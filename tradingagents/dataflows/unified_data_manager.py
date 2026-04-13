import time
import random
import pandas as pd
import numpy as np
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from .data_cache import get_data_cache
from tradingagents.utils.logger import get_logger
from tradingagents.constants import MIN_STOCK_DATA_DAYS

logger = get_logger(__name__)

# 从模型模块导入（v2.0 模块化拆分）
from .vendor_models import (
    RateLimitError,
    DataFetchError,
    VendorPriority,
    VendorConfig,
    FetchStats,
    VendorStats,
)

# 向后兼容：保留VendorNotFoundError导出（从vendor_models中导入）
from .vendor_models import VendorNotFoundError


class UnifiedDataManager:
    """统一数据获取管理器
    
    特性:
    - 多数据源优先级支持
    - 自动降级和重试
    - 限流检测和等待
    - 最大访问次数限制
    - 详细的统计信息
    """
    
    def __init__(
        self,
        default_max_retries: int = 3,
        default_retry_delay_base: float = 1.0,
        default_retry_delay_max: float = 10.0,
        default_rate_limit_wait: float = 5.0,
        default_rate_limit_max_retries: int = 5,
    ):
        """
        初始化统一数据管理器
        
        Args:
            default_max_retries: 默认最大重试次数
            default_retry_delay_base: 默认重试延迟基数（指数退避）
            default_retry_delay_max: 默认最大重试延迟
            default_rate_limit_wait: 默认限流等待时间
            default_rate_limit_max_retries: 默认限流最大重试次数
        """
        self.default_max_retries = default_max_retries
        self.default_retry_delay_base = default_retry_delay_base
        self.default_retry_delay_max = default_retry_delay_max
        self.default_rate_limit_wait = default_rate_limit_wait
        self.default_rate_limit_max_retries = default_rate_limit_max_retries
        
        self.vendor_configs: Dict[str, VendorConfig] = {}
        self.vendor_stats: Dict[str, VendorStats] = {}
        self.global_stats: FetchStats = FetchStats()
        
        self.method_vendors: Dict[str, List[str]] = {}
        self.method_implementations: Dict[str, Dict[str, Callable]] = {}
        
        self.cache = get_data_cache()
        self.last_vendor_used: Optional[str] = None
        
    def register_vendor(
        self,
        name: str,
        priority: VendorPriority = VendorPriority.SECONDARY,
        **kwargs
    ) -> "UnifiedDataManager":
        """
        注册数据源
        
        Args:
            name: 数据源名称
            priority: 优先级
            **kwargs: 其他配置参数
        
        Returns:
            self，支持链式调用
        """
        config = VendorConfig(
            name=name,
            priority=priority,
            max_retries=kwargs.get("max_retries", self.default_max_retries),
            retry_delay_base=kwargs.get("retry_delay_base", self.default_retry_delay_base),
            retry_delay_max=kwargs.get("retry_delay_max", self.default_retry_delay_max),
            rate_limit_wait=kwargs.get("rate_limit_wait", self.default_rate_limit_wait),
            rate_limit_max_retries=kwargs.get("rate_limit_max_retries", self.default_rate_limit_max_retries),
            enabled=kwargs.get("enabled", True),
        )
        self.vendor_configs[name] = config
        self.vendor_stats[name] = VendorStats(name=name)
        return self
    
    def register_method(
        self,
        method_name: str,
        vendor_implementations: Dict[str, Callable],
        vendor_priority_order: Optional[List[str]] = None
    ) -> "UnifiedDataManager":
        """
        注册方法
        
        Args:
            method_name: 方法名称
            vendor_implementations: 数据源实现字典 {vendor_name: implementation}
            vendor_priority_order: 可选的数据源优先级顺序
        
        Returns:
            self，支持链式调用
        """
        self.method_implementations[method_name] = vendor_implementations
        
        if vendor_priority_order:
            self.method_vendors[method_name] = vendor_priority_order
        else:
            vendors = list(vendor_implementations.keys())
            vendors.sort(key=lambda v: self.vendor_configs.get(v, VendorConfig(name=v)).priority.value)
            self.method_vendors[method_name] = vendors
        
        return self
    
    def _get_sorted_vendors(self, method_name: str) -> List[str]:
        """
        获取排序后的数据源列表
        
        Args:
            method_name: 方法名称
        
        Returns:
            排序后的数据源列表
        """
        if method_name not in self.method_vendors:
            return []
        
        vendors = self.method_vendors[method_name]
        
        enabled_vendors = [
            v for v in vendors
            if self.vendor_configs.get(v, VendorConfig(name=v)).enabled
        ]
        
        return enabled_vendors
    
    def _parse_stock_data(self, stock_data_str: str) -> Optional[pd.DataFrame]:
        """
        解析股票数据字符串为 DataFrame
        
        Args:
            stock_data_str: CSV格式的股票数据字符串
        
        Returns:
            DataFrame 或 None
        """
        try:
            lines = stock_data_str.strip().split('\n')
            if len(lines) < 2:
                return None
            
            header = [col.strip() for col in lines[0].split(',')]
            data = []
            
            for line in lines[1:]:
                if line.strip():
                    row = [col.strip() for col in line.split(',')]
                    if len(row) == len(header):
                        data.append(row)
            
            if not data:
                return None
            
            df = pd.DataFrame(data, columns=header)
            
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date').sort_index()
            
            return df
        except (ValueError, KeyError, pd.errors.ParserError):
            return None
    
    def _exponential_backoff(
        self,
        attempt: int,
        base_delay: float,
        max_delay: float
    ) -> float:
        """
        计算指数退避延迟时间
        
        Args:
            attempt: 重试次数
            base_delay: 基础延迟
            max_delay: 最大延迟
        
        Returns:
            延迟时间（秒）
        """
        delay = min(base_delay * (2 ** attempt), max_delay)
        jitter = random.uniform(0, delay * 0.1)
        return delay + jitter
    
    def _is_rate_limit_error(self, error: Exception) -> bool:
        """
        判断是否是限流错误
        
        Args:
            error: 异常
        
        Returns:
            是否是限流错误
        """
        error_str = str(error).lower()
        
        rate_limit_keywords = [
            "rate limit", "ratelimit", "too many requests",
            "429", "quota", "exceeded", "throttle"
        ]
        
        for keyword in rate_limit_keywords:
            if keyword in error_str:
                return True
        
        from .alpha_vantage_common import AlphaVantageRateLimitError
        if isinstance(error, (RateLimitError, AlphaVantageRateLimitError)):
            return True
        
        return False
    
    def _log_tool_call(
        self,
        method_name: str,
        vendor: str,
        args: tuple,
        kwargs: dict,
        result: str,
    ) -> None:
        """记录工具调用信息到数据库（统一日志逻辑）"""
        try:
            from tradingagents.dataflows.database import get_db
            db = get_db()
            symbol = args[0] if args else "unknown"
            trade_date = args[2] if len(args) >= 3 else datetime.now().strftime("%Y-%m-%d")
            input_params = {
                "args": args,
                "kwargs": kwargs
            }
            db.save_tool_call(
                symbol=symbol,
                trade_date=trade_date,
                tool_name=method_name,
                vendor_used=vendor,
                input_params=input_params,
                result=str(result)
            )
            logger.debug("%s工具调用已记录到数据库", "缓存" if vendor == "cache" else "")
        except Exception as e:
            logger.warning("记录%s工具调用失败: %s", "缓存" if vendor == "cache" else "", e)
    
    def fetch(
        self,
        method_name: str,
        *args,
        no_cache: bool = False,
        **kwargs
    ) -> Any:
        """
        获取数据
        
        Args:
            method_name: 方法名称
            *args: 位置参数
            **kwargs: 关键字参数
        
        Returns:
            获取的数据
        
        Raises:
            DataFetchError: 所有数据源都失败时抛出
        """
        from datetime import datetime, timedelta
        
        logger.debug("调用方法: %s", method_name)
        logger.debug("参数: args=%s, kwargs=%s", args, kwargs)

        self.global_stats.total_calls += 1
        
        processed_args = args
        if method_name == "get_stock_data":
            args_list = list(args)
            if len(args_list) >= 3:
                try:
                    symbol, start_date, end_date = args_list[:3]
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                    days_diff = (end_dt - start_dt).days
                    
                    if days_diff < MIN_STOCK_DATA_DAYS:
                        new_start_dt = end_dt - timedelta(days=MIN_STOCK_DATA_DAYS)
                        new_start_date = new_start_dt.strftime("%Y-%m-%d")
                        args_list[1] = new_start_date
                        processed_args = tuple(args_list)
                        logger.debug("调整日期范围: %s -> %s", start_date, new_start_date)
                except (ValueError, TypeError):
                    pass
        
        cached_result = self.cache.get(method_name, *processed_args, **kwargs)
        if cached_result is not None:
            logger.debug("使用缓存数据")
            self.global_stats.successful_calls += 1
            # 按日期逆序排列输出
            cached_lines = str(cached_result).split('\n')
            if len(cached_lines) > 2:
                header = cached_lines[0]
                data_lines = cached_lines[1:]
                data_lines.reverse()
                sorted_data = header + '\n' + '\n'.join(data_lines[:20])
                logger.debug("缓存数据输出 (最新20条):\n%s", sorted_data)
            else:
                logger.debug("缓存数据输出:\n%s", str(cached_result)[:500])
            if len(str(cached_result)) > 500:
                logger.debug("... (截断，总长度: %d)", len(str(cached_result)))
            
            # 记录工具调用信息（缓存数据）
            self._log_tool_call(method_name, "cache", args, kwargs, cached_result)
            
            return cached_result
        
        vendors = self._get_sorted_vendors(method_name)
        logger.debug("可用数据源: %s", vendors)
        
        if not vendors:
            raise DataFetchError(f"No vendors available for method '{method_name}'")
        
        last_error = None
        
        for vendor in vendors:
            logger.debug("尝试使用数据源: %s", vendor)
            config = self.vendor_configs.get(vendor, VendorConfig(name=vendor))
            stats = self.vendor_stats.get(vendor, VendorStats(name=vendor))
            
            if not config.enabled:
                logger.debug("数据源 %s 已禁用", vendor)
                continue
            
            if vendor not in self.method_implementations.get(method_name, {}):
                logger.debug("数据源 %s 不支持方法 %s", vendor, method_name)
                continue
            
            impl = self.method_implementations[method_name][vendor]
            
            result = self._try_vendor(
                vendor=vendor,
                config=config,
                stats=stats,
                impl=impl,
                args=processed_args,
                kwargs=kwargs
            )
            
            if result is not None:
                self.global_stats.successful_calls += 1
                self.last_vendor_used = vendor
                
                # 检查是否写入缓存
                should_cache = not no_cache
                if should_cache and method_name == "get_stock_data" and len(args) >= 3:
                    try:
                        from datetime import datetime
                        end_date = args[2]
                        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                        # 简单判断：周末不缓存 (5=周六, 6=周日)
                        if end_dt.weekday() >= 5:
                            logger.debug("结束日期 %s 是周末，不写入缓存", end_date)
                            should_cache = False
                    except (ValueError, TypeError):
                        pass
                
                if should_cache:
                    self.cache.set(method_name, result, *processed_args, **kwargs)
                
                # 按日期倒序输出
                result_lines = str(result).split('\n')
                if len(result_lines) > 2:
                    header = result_lines[0]
                    data_lines = result_lines[1:]
                    data_lines.reverse()
                    sorted_result = header + '\n' + '\n'.join(data_lines[:20])
                    logger.debug("数据输出 (最新20条):\n%s", sorted_result)
                else:
                    logger.debug("数据输出 (前500字符):\n%s", str(result)[:500])
                
                if len(str(result)) > 500:
                    logger.debug("... (截断，总长度: %d)", len(str(result)))
                
                # 记录工具调用信息
                self._log_tool_call(method_name, vendor, args, kwargs, result)
                
                return result
            else:
                logger.warning("数据源 %s 失败", vendor)
            
            last_error = result
        
        self.global_stats.failed_calls += 1
        logger.error("所有数据源都失败, method=%s", method_name)
        raise DataFetchError(
            f"All vendors failed for method '{method_name}'. Last error: {last_error}")
    
    def _try_vendor(
        self,
        vendor: str,
        config: VendorConfig,
        stats: VendorStats,
        impl: Callable,
        args: tuple,
        kwargs: dict
    ) -> Any:
        """
        尝试使用某个数据源获取数据
        
        Args:
            vendor: 数据源名称
            config: 数据源配置
            stats: 数据源统计
            impl: 实现函数
            args: 位置参数
            kwargs: 关键字参数
        
        Returns:
            成功返回数据，失败返回None
        """
        rate_limit_retries = 0
        
        for attempt in range(config.max_retries):
            try:
                stats.stats.total_calls += 1
                
                result = impl(*args, **kwargs)
                
                stats.stats.successful_calls += 1
                stats.last_success = datetime.now()
                
                return result
                
            except Exception as e:
                stats.stats.failed_calls += 1
                stats.last_error = str(e)
                
                if self._is_rate_limit_error(e):
                    stats.stats.rate_limit_hits += 1
                    self.global_stats.rate_limit_hits += 1
                    rate_limit_retries += 1
                    
                    if rate_limit_retries > config.rate_limit_max_retries:
                        break
                    
                    wait_time = config.rate_limit_wait * rate_limit_retries
                    stats.stats.total_wait_time += wait_time
                    self.global_stats.total_wait_time += wait_time
                    
                    time.sleep(wait_time)
                    continue
                
                if attempt < config.max_retries - 1:
                    delay = self._exponential_backoff(
                        attempt,
                        config.retry_delay_base,
                        config.retry_delay_max
                    )
                    stats.stats.total_wait_time += delay
                    self.global_stats.total_wait_time += delay
                    
                    time.sleep(delay)
                    continue
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "last_vendor_used": self.last_vendor_used,
            "global": {
                "total_calls": self.global_stats.total_calls,
                "successful_calls": self.global_stats.successful_calls,
                "failed_calls": self.global_stats.failed_calls,
                "rate_limit_hits": self.global_stats.rate_limit_hits,
                "total_wait_time": self.global_stats.total_wait_time,
            },
            "vendors": {
                name: {
                    "total_calls": v.stats.total_calls,
                    "successful_calls": v.stats.successful_calls,
                    "failed_calls": v.stats.failed_calls,
                    "rate_limit_hits": v.stats.rate_limit_hits,
                    "total_wait_time": v.stats.total_wait_time,
                    "last_success": v.last_success.isoformat() if v.last_success else None,
                    "last_error": v.last_error,
                }
                for name, v in self.vendor_stats.items()
            }
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.global_stats = FetchStats()
        for vendor in self.vendor_stats:
            self.vendor_stats[vendor] = VendorStats(name=vendor)
