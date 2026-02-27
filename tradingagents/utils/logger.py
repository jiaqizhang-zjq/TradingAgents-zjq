"""
TradingAgents 统一日志系统

提供结构化日志记录、敏感信息脱敏、日志轮转等功能。
替换项目中的所有 print() 语句。
"""

import logging
import os
import re
from logging.handlers import RotatingFileHandler
from typing import Optional


class SensitiveDataFilter(logging.Filter):
    """敏感数据过滤器 - 脱敏 API keys 等信息"""
    
    SENSITIVE_PATTERNS = [
        (r'api_key=\S+', 'api_key=***'),
        (r'api_secret=\S+', 'api_secret=***'),
        (r'token=\S+', 'token=***'),
        (r'password=\S+', 'password=***'),
        (r'Authorization:\s*Bearer\s+\S+', 'Authorization: Bearer ***'),
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """过滤日志记录中的敏感信息"""
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                record.msg = re.sub(pattern, replacement, record.msg, flags=re.IGNORECASE)
        return True


def setup_logger(
    name: str,
    level: str = "INFO",
    log_dir: str = "logs",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_console: bool = True,
    enable_file: bool = True
) -> logging.Logger:
    """
    设置并返回配置好的 logger
    
    Args:
        name: Logger 名称（通常使用 __name__）
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 日志文件存储目录
        max_bytes: 单个日志文件最大大小（字节）
        backup_count: 保留的备份日志文件数量
        enable_console: 是否启用控制台输出
        enable_file: 是否启用文件输出
        
    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)
    
    # 如果 logger 已有 handlers，说明已配置过，直接返回
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, level.upper()))
    logger.propagate = False  # 防止日志传播到父 logger
    
    # 添加敏感数据过滤器
    sensitive_filter = SensitiveDataFilter()
    logger.addFilter(sensitive_filter)
    
    # 格式器
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台 Handler
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(sensitive_filter)
        logger.addHandler(console_handler)
    
    # 文件 Handler
    if enable_file:
        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)
        
        log_file_path = os.path.join(log_dir, f'{name.replace(".", "_")}.log')
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(sensitive_filter)
        logger.addHandler(file_handler)
    
    return logger


# 全局默认 logger（用于快速导入）
default_logger = setup_logger("tradingagents")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取 logger 实例
    
    Args:
        name: Logger 名称，如果为 None 则返回默认 logger
        
    Returns:
        Logger 实例
    """
    if name is None:
        return default_logger
    return setup_logger(name)


# 便捷函数（向后兼容 print()）
def log_info(msg: str, logger_name: Optional[str] = None):
    """记录 INFO 级别日志"""
    logger = get_logger(logger_name)
    logger.info(msg)


def log_debug(msg: str, logger_name: Optional[str] = None):
    """记录 DEBUG 级别日志"""
    logger = get_logger(logger_name)
    logger.debug(msg)


def log_warning(msg: str, logger_name: Optional[str] = None):
    """记录 WARNING 级别日志"""
    logger = get_logger(logger_name)
    logger.warning(msg)


def log_error(msg: str, logger_name: Optional[str] = None, exc_info: bool = False):
    """记录 ERROR 级别日志"""
    logger = get_logger(logger_name)
    logger.error(msg, exc_info=exc_info)


def log_critical(msg: str, logger_name: Optional[str] = None, exc_info: bool = False):
    """记录 CRITICAL 级别日志"""
    logger = get_logger(logger_name)
    logger.critical(msg, exc_info=exc_info)
