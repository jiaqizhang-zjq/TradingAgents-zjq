"""
数据源模型定义
=============
定义数据源管理相关的异常类、配置类和统计类。
从 unified_data_manager.py 中拆分出来以实现单一职责。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime


# =============================================================================
# 异常类
# =============================================================================

class RateLimitError(Exception):
    """限流错误"""
    pass


class DataFetchError(Exception):
    """数据获取错误"""
    pass


class VendorNotFoundError(Exception):
    """数据源未找到错误"""
    pass


# =============================================================================
# 枚举类
# =============================================================================

class VendorPriority(Enum):
    """数据源优先级"""
    PRIMARY = 1
    SECONDARY = 2
    FALLBACK = 3


# =============================================================================
# 数据类
# =============================================================================

@dataclass
class VendorConfig:
    """数据源配置"""
    name: str
    priority: VendorPriority = VendorPriority.SECONDARY
    max_retries: int = 3
    retry_delay_base: float = 1.0
    retry_delay_max: float = 10.0
    rate_limit_wait: float = 5.0
    rate_limit_max_retries: int = 5
    enabled: bool = True


@dataclass
class FetchStats:
    """获取统计"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rate_limit_hits: int = 0
    total_wait_time: float = 0.0


@dataclass
class VendorStats:
    """数据源统计"""
    name: str
    stats: FetchStats = field(default_factory=FetchStats)
    last_error: Optional[str] = None
    last_success: Optional[datetime] = None
