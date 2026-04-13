import pandas as pd
from typing import Any, Dict

from tradingagents.utils.logger import get_logger
from tradingagents.constants import MIN_STOCK_DATA_DAYS

logger = get_logger(__name__)

# Import from vendor-specific modules
from .y_finance import (
    get_YFin_data_online,
    get_stock_stats_indicators_window,
    get_fundamentals as get_yfinance_fundamentals,
    get_balance_sheet as get_yfinance_balance_sheet,
    get_cashflow as get_yfinance_cashflow,
    get_income_statement as get_yfinance_income_statement,
    get_insider_transactions as get_yfinance_insider_transactions,
)
from .yfinance_news import get_news_yfinance, get_global_news_yfinance
from .alpha_vantage import (
    get_stock as get_alpha_vantage_stock,
    get_indicator as get_alpha_vantage_indicator,
    get_fundamentals as get_alpha_vantage_fundamentals,
    get_balance_sheet as get_alpha_vantage_balance_sheet,
    get_cashflow as get_alpha_vantage_cashflow,
    get_income_statement as get_alpha_vantage_income_statement,
    get_insider_transactions as get_alpha_vantage_insider_transactions,
    get_news as get_alpha_vantage_news,
    get_global_news as get_alpha_vantage_global_news,
)

# 长桥API模块（默认选项）
from .longbridge import (
    get_stock as get_longbridge_stock,
    get_indicator as get_longbridge_indicator,
    get_fundamentals as get_longbridge_fundamentals,
    get_balance_sheet as get_longbridge_balance_sheet,
    get_cashflow as get_longbridge_cashflow,
    get_income_statement as get_longbridge_income_statement,
    get_insider_transactions as get_longbridge_insider_transactions,
    get_news as get_longbridge_news,
    get_global_news as get_longbridge_global_news,
    get_candlestick_patterns as get_longbridge_candlestick_patterns,
)

# 导入本地计算模块
from .complete_indicators import (
    CompleteTechnicalIndicators,
    CompleteCandlestickPatterns,
    ChartPatterns
)

# 导入统一数据管理器
from .unified_data_manager import (
    UnifiedDataManager,
    VendorPriority,
    DataFetchError,
)

# Configuration and routing logic
from .config import get_config

# 导入核心工具模块
from .core import (
    parse_stock_data as _core_parse_stock_data,
    prepare_clean_dataframe as _core_prepare_clean_dataframe,
    collect_all_needed_indicators as _core_collect_all_needed_indicators,
    build_grouped_results as _core_build_grouped_results,
)

# 导入依赖注入容器
from tradingagents.core.container import get_container

# ========== LOCAL VENDOR 实现 ==========
def _parse_stock_data(stock_data_str: str) -> pd.DataFrame:
    """解析股票数据字符串为DataFrame（委托给core模块）"""
    return _core_parse_stock_data(stock_data_str)

def _local_get_indicators(symbol, indicator, curr_date, look_back_days, *args, **kwargs):
    """本地计算技术指标（使用惰性计算优化）"""
    from datetime import datetime, timedelta
    from .lazy_indicators import get_lazy_calculator
    from .indicator_groups import get_indicator_columns
    
    stock_data = kwargs.get('stock_data', '')
    manager = get_data_manager()
    
    if not stock_data:
        end_date = curr_date
        start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=look_back_days + 60)).strftime("%Y-%m-%d")
        stock_data = manager.fetch("get_stock_data", symbol, start_date, end_date)
    
    df = _parse_stock_data(stock_data)
    
    if df is None:
        raise DataFetchError("Failed to parse stock data")
    
    df_clean = _prepare_clean_dataframe(df)
    
    # 使用惰性计算器 - 只计算需要的指标
    lazy_calc = get_lazy_calculator(df_clean)
    
    # 获取该指标组需要的列
    all_columns = BASE_COLUMNS + lazy_calc.get_available_indicators()
    needed_indicators = get_indicator_columns(indicator, all_columns)
    
    # 只计算需要的指标（不是全部100+个）
    needed_indicators = [col for col in needed_indicators if col not in BASE_COLUMNS]
    result_df = lazy_calc.get_indicators(needed_indicators)
    
    # 只返回最近需要的天数
    result_df = result_df.tail(look_back_days + 10)
    
    return result_df.to_csv(index=False)


def _ensure_stock_data(symbol: str, curr_date: str, look_back_days: int, stock_data: str = '') -> str:
    """确保有股票数据，如果没有则获取"""
    if stock_data:
        return stock_data
    
    from datetime import datetime, timedelta
    manager = get_data_manager()
    end_date = curr_date
    start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=look_back_days + 60)).strftime("%Y-%m-%d")
    return manager.fetch("get_stock_data", symbol, start_date, end_date)


def _prepare_clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """准备干净的DataFrame用于指标计算"""
    df.reset_index(inplace=True)
    
    # 优化：避免创建新 DataFrame，使用 rename
    df_clean = df.rename(columns={
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    })[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    
    return df_clean


def _collect_all_needed_indicators() -> set:
    """收集所有分组需要的指标（去重）"""
    from .indicator_groups import INDICATOR_GROUPS, BASE_COLUMNS
    
    all_needed_indicators = set()
    for group_name, indicators in INDICATOR_GROUPS.items():
        for ind in indicators:
            if ind not in BASE_COLUMNS:
                all_needed_indicators.add(ind)
    return all_needed_indicators


def _build_grouped_results(df_with_indicators: pd.DataFrame, look_back_days: int) -> dict:
    """按分组构建结果字典（委托给core模块）"""
    return _core_build_grouped_results(df_with_indicators, look_back_days)


def _local_get_all_indicators(symbol: str, curr_date: str, look_back_days: int, stock_data: str = '', *args, **kwargs) -> str:
    """本地计算所有技术指标，一次性返回所有分组（使用惰性计算优化）"""
    from .lazy_indicators import get_lazy_calculator
    import traceback
    
    try:
        logger.debug("_local_get_all_indicators: symbol=%s, curr_date=%s, look_back_days=%s", symbol, curr_date, look_back_days)
        logger.debug("_local_get_all_indicators: stock_data length=%d", len(stock_data) if stock_data else 0)
        
        # 1. 确保有股票数据
        stock_data = _ensure_stock_data(symbol, curr_date, look_back_days, stock_data)
        
        # 2. 解析并验证数据
        df = _parse_stock_data(stock_data)
        if df is None:
            raise DataFetchError("Failed to parse stock data")
        logger.debug("_local_get_all_indicators: df parsed, shape=%s", df.shape)
        
        # 3. 准备干净的 DataFrame
        df_clean = _prepare_clean_dataframe(df)
        logger.debug("_local_get_all_indicators: df_clean shape=%s", df_clean.shape)
        
        # 4. 收集所有需要的指标
        all_needed_indicators = _collect_all_needed_indicators()
        logger.debug("_local_get_all_indicators: calculating %d unique indicators...", len(all_needed_indicators))
        
        # 5. 批量计算指标
        lazy_calc = get_lazy_calculator(df_clean)
        df_with_indicators = lazy_calc.get_indicators(list(all_needed_indicators))
        
        # 6. 构建分组结果
        logger.debug("_local_get_all_indicators: building result groups...")
        result = _build_grouped_results(df_with_indicators, look_back_days)
        
        logger.debug("_local_get_all_indicators: done, result has %d groups", len(result))
        return result
        
    except Exception as e:
        logger.error("_local_get_all_indicators ERROR: %s", e)
        logger.debug("_local_get_all_indicators Traceback:\n%s", traceback.format_exc())
        raise DataFetchError(f"_local_get_all_indicators failed: {e}")

def _local_get_candlestick_patterns(symbol, start_date, end_date, *args, **kwargs):
    """本地识别蜡烛图形态"""
    from datetime import datetime, timedelta
    
    stock_data = kwargs.get('stock_data', '')
    manager = get_data_manager()
    
    if not stock_data:
        stock_data = manager.fetch("get_stock_data", symbol, start_date, end_date)
    
    df = _parse_stock_data(stock_data)
    
    if df is None:
        raise DataFetchError("Failed to parse stock data")
    
    df.reset_index(inplace=True)
    
    df_clean = pd.DataFrame()
    df_clean['timestamp'] = df['timestamp']
    df_clean['open'] = df['Open']
    df_clean['high'] = df['High']
    df_clean['low'] = df['Low']
    df_clean['close'] = df['Close']
    df_clean['volume'] = df['Volume']
    
    result_df = CompleteCandlestickPatterns.identify_patterns(df_clean)
    
    if len(result_df) == 0:
        return f"No candlestick patterns identified for {symbol} in the date range {start_date} to {end_date}"
    
    patterns_result = []
    for _, row in result_df.iterrows():
        date_str = row.get('timestamp', '')
        patterns_str = row.get('patterns', '')
        volume_confirmed = row.get('volume_confirmed', False)
        
        if volume_confirmed and patterns_str:
            patterns_list = patterns_str.split('|')
            patterns_with_confirmation = [f"{p}(VOL_CONFIRMED)" for p in patterns_list]
            patterns_str = '|'.join(patterns_with_confirmation)
        elif volume_confirmed:
            patterns_str = "(VOL_CONFIRMED)"
        
        patterns_result.append({
            'Date': date_str,
            'Patterns': patterns_str.replace('|', ', '),
            'Open': round(row.get('open', 0), 2),
            'High': round(row.get('high', 0), 2),
            'Low': round(row.get('low', 0), 2),
            'Close': round(row.get('close', 0), 2)
        })
    
    result = f"# Candlestick Patterns for {symbol} ({start_date} to {end_date})\n\n"
    result += "| Date       | Patterns                                      | Open   | High   | Low    | Close  |\n"
    result += "|------------|-----------------------------------------------|--------|--------|--------|--------|\n"
    
    for p in patterns_result:
        patterns_str = p['Patterns']
        if len(patterns_str) > 45:
            patterns_str = patterns_str[:42] + "..."
        result += f"| {p['Date']} | {patterns_str:<45} | {p['Open']:>6} | {p['High']:>6} | {p['Low']:>6} | {p['Close']:>6} |\n"
    
    all_patterns = []
    for p in patterns_result:
        all_patterns.extend(p['Patterns'].split(', '))
    
    pattern_counts = {}
    for pat in all_patterns:
        pattern_counts[pat] = pattern_counts.get(pat, 0) + 1
    
    result += f"\n## Pattern Summary\n"
    result += "| Pattern                | Count |\n"
    result += "|------------------------|-------|\n"
    for pat, cnt in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        result += f"| {pat:<22} | {cnt:>5} |\n"
    
    return result

def _local_get_chart_patterns(symbol, start_date, end_date, lookback=60, *args, **kwargs):
    """本地识别西方图表形态"""
    from datetime import datetime, timedelta
    import traceback
    
    try:
        logger.debug("_local_get_chart_patterns: symbol=%s, start_date=%s, end_date=%s", symbol, start_date, end_date)
        
        stock_data = kwargs.get('stock_data', '')
        manager = get_data_manager()
        
        if not stock_data:
            logger.debug("_local_get_chart_patterns: fetching stock data...")
            stock_data = manager.fetch("get_stock_data", symbol, start_date, end_date)
        
        logger.debug("_local_get_chart_patterns: parsing stock data...")
        df = _parse_stock_data(stock_data)
        
        if df is None:
            raise DataFetchError("Failed to parse stock data")
        
        logger.debug("_local_get_chart_patterns: df parsed, shape=%s", df.shape)
        logger.debug("_local_get_chart_patterns: df columns=%s", list(df.columns))
        
        df_clean = _prepare_clean_dataframe(df)
        
        logger.debug("_local_get_chart_patterns: calling identify_all_patterns...")
        patterns = ChartPatterns.identify_all_patterns(df_clean, lookback)
        logger.debug("_local_get_chart_patterns: identify_all_patterns done")
        
        result_lines = [
            f"# Chart Patterns for {symbol}",
            "",
            "| Pattern Type | Detected | Confidence | Volume Confirmed | Breakout Confirmed | Description |",
            "|--------------|----------|------------|------------------|-------------------|-------------|"
        ]
        
        for pattern_name, pattern_info in patterns.items():
            detected = "✅" if pattern_info.get("detected", False) else "❌"
            confidence = f"{pattern_info.get('confidence', 0):.2%}"
            volume_confirmed = "✅" if pattern_info.get("volume_confirmed", False) else "❌"
            breakout_confirmed = "✅" if pattern_info.get("breakout_confirmed", False) else "❌"
            description = pattern_info.get("description", "")
            result_lines.append(f"| {pattern_name:<12} | {detected:<8} | {confidence:<10} | {volume_confirmed:<16} | {breakout_confirmed:<17} | {description} |")
        
        result_lines.extend(["", "## Detailed Pattern Information", ""])
        for pattern_name, pattern_info in patterns.items():
            if pattern_info.get("detected", False):
                result_lines.append(f"### {pattern_name}")
                for key, value in pattern_info.items():
                    if key not in ["detected", "description"]:
                        result_lines.append(f"- {key}: {value}")
                result_lines.append("")
        
        return "\n".join(result_lines)
    except Exception as e:
        logger.error("_local_get_chart_patterns ERROR: %s", e)
        logger.debug("_local_get_chart_patterns Traceback:\n%s", traceback.format_exc())
        raise DataFetchError(f"_local_get_chart_patterns failed: {e}")

# ========== 数据管理器初始化 ==========
def get_data_manager() -> UnifiedDataManager:
    """
    获取数据管理器实例（通过依赖注入容器）
    
    使用依赖注入容器管理单例，支持测试和多实例场景
    """
    container = get_container()
    
    # 如果未注册，则注册并初始化
    if not container.has('data_manager'):
        container.register('data_manager', _init_data_manager, singleton=True)
    
    return container.get('data_manager')

def _init_data_manager() -> UnifiedDataManager:
    """初始化数据管理器"""
    manager = UnifiedDataManager(
        default_max_retries=3,
        default_retry_delay_base=1.0,
        default_retry_delay_max=10.0,
        default_rate_limit_wait=5.0,
        default_rate_limit_max_retries=5,
    )
    
    config = get_config()
    
    manager.register_vendor(
        "local",
        priority=VendorPriority.PRIMARY,
        max_retries=1,
        rate_limit_wait=0.0,
    )
    
    manager.register_vendor(
        "longbridge",
        priority=VendorPriority.SECONDARY,
        max_retries=3,
        rate_limit_wait=2.0,
    )
    
    manager.register_vendor(
        "yfinance",
        priority=VendorPriority.FALLBACK,
        max_retries=3,
        rate_limit_wait=1.0,
    )
    
    manager.register_vendor(
        "alpha_vantage",
        priority=VendorPriority.FALLBACK,
        max_retries=2,
        rate_limit_wait=12.0,
    )
    
    # ========== 声明式方法注册表 ==========
    # 每项格式: (method_name, {vendor: impl}, [priority_order])
    method_registry = [
        ("get_stock_data", {
            "longbridge": get_longbridge_stock,
            "yfinance": get_YFin_data_online,
            "alpha_vantage": get_alpha_vantage_stock,
        }, ["longbridge", "yfinance", "alpha_vantage"]),

        ("get_indicators", {
            "local": _local_get_indicators,
            "longbridge": get_longbridge_indicator,
            "yfinance": get_stock_stats_indicators_window,
            "alpha_vantage": get_alpha_vantage_indicator,
        }, ["local", "longbridge", "yfinance", "alpha_vantage"]),

        ("get_all_indicators", {
            "local": _local_get_all_indicators,
        }, ["local"]),

        ("get_fundamentals", {
            "longbridge": get_longbridge_fundamentals,
            "yfinance": get_yfinance_fundamentals,
            "alpha_vantage": get_alpha_vantage_fundamentals,
        }, ["longbridge", "yfinance", "alpha_vantage"]),

        ("get_balance_sheet", {
            "alpha_vantage": get_alpha_vantage_balance_sheet,
            "yfinance": get_yfinance_balance_sheet,
            "longbridge": get_longbridge_balance_sheet,
        }, ["alpha_vantage", "yfinance", "longbridge"]),

        ("get_cashflow", {
            "alpha_vantage": get_alpha_vantage_cashflow,
            "yfinance": get_yfinance_cashflow,
            "longbridge": get_longbridge_cashflow,
        }, ["alpha_vantage", "yfinance", "longbridge"]),

        ("get_income_statement", {
            "alpha_vantage": get_alpha_vantage_income_statement,
            "yfinance": get_yfinance_income_statement,
            "longbridge": get_longbridge_income_statement,
        }, ["alpha_vantage", "yfinance", "longbridge"]),

        ("get_news", {
            "alpha_vantage": get_alpha_vantage_news,
            "yfinance": get_news_yfinance,
        }, ["alpha_vantage", "yfinance"]),

        ("get_global_news", {
            "alpha_vantage": get_alpha_vantage_global_news,
            "yfinance": get_global_news_yfinance,
        }, ["alpha_vantage", "yfinance"]),

        ("get_insider_transactions", {
            "alpha_vantage": get_alpha_vantage_insider_transactions,
            "yfinance": get_yfinance_insider_transactions,
        }, ["alpha_vantage", "yfinance"]),

        ("get_candlestick_patterns", {
            "local": _local_get_candlestick_patterns,
            "longbridge": get_longbridge_candlestick_patterns,
        }, ["local", "longbridge"]),

        ("get_chart_patterns", {
            "local": _local_get_chart_patterns,
        }, ["local"]),
    ]

    for method_name, impls, priority_order in method_registry:
        manager.register_method(method_name, impls, priority_order)
    
    return manager

def route_to_vendor(method: str, *args, **kwargs) -> str:
    """路由方法调用到统一数据管理器
    
    这是兼容旧代码的接口，新代码应该直接使用 get_data_manager()
    
    Args:
        method: 方法名称
        *args: 位置参数
        **kwargs: 关键字参数
    
    Returns:
        获取的数据
    """
    from datetime import datetime, timedelta
    
    manager = get_data_manager()
    
    if method == "get_stock_data":
        args_list = list(args)
        if len(args_list) >= 3:
            symbol, start_date, end_date = args_list[:3]
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                days_diff = (end_dt - start_dt).days
                
                if days_diff < MIN_STOCK_DATA_DAYS:
                    new_start_dt = end_dt - timedelta(days=MIN_STOCK_DATA_DAYS)
                    new_start_date = new_start_dt.strftime("%Y-%m-%d")
                    args_list[1] = new_start_date
                    args = tuple(args_list)
            except (ValueError, TypeError):
                pass
    
    return manager.fetch(method, *args, **kwargs)

def get_fetch_stats() -> Dict:
    """获取数据获取统计信息"""
    manager = get_data_manager()
    return manager.get_stats()

def reset_fetch_stats() -> None:
    """重置数据获取统计信息"""
    manager = get_data_manager()
    manager.reset_stats()
