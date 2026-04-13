from datetime import datetime
from typing import Dict, Any

from tradingagents.constants import TOOL_CALL_LOG_PATH
from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)


def log_tool_call(tool_name: str, vendor_used: str, result: str) -> None:
    """记录工具调用信息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = TOOL_CALL_LOG_PATH
    
    log_entry = f"\n{'='*100}\n"
    log_entry += f"[{timestamp}] 🔧 Tool: {tool_name}\n"
    log_entry += f"          📊 Vendor Used: {vendor_used}\n"
    log_entry += f"          📄 Result Preview:\n"
    log_entry += f"{result[:500]}{'...' if len(result) > 500 else ''}\n"
    log_entry += f"{'='*100}\n"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)
    
    logger.debug("🔧 [TOOL CALL] %s (Vendor: %s)", tool_name, vendor_used)


def log_debug_prompt(
    config: Dict[str, Any],
    agent_name: str,
    language: str,
    caller_logger: Any = None,
    **text_fields: str,
) -> None:
    """统一的 debug prompt 日志输出（由 debug 开关控制）。
    
    Args:
        config: 全局配置字典（需含 debug.enabled / debug.show_prompts）
        agent_name: 代理名称，用于日志标题
        language: 当前语言设置
        caller_logger: 调用方的 logger（可选，默认使用本模块 logger）
        **text_fields: 需要打印的文本字段（key=标签, value=内容），超过 500 字符自动截断
    """
    debug_config = config.get("debug", {})
    if not (debug_config.get("enabled", False) and debug_config.get("show_prompts", False)):
        return
    
    log = caller_logger or logger
    log.debug("=" * 80)
    log.debug("DEBUG: %s Prompt Before LLM Call:", agent_name)
    log.debug("=" * 80)
    log.debug("Language: %s", language)
    for label, text in text_fields.items():
        display = text[:500] + "..." if len(text) > 500 else text
        log.debug("%s: %s", label, display)
    log.debug("=" * 80)


def get_vendor_info(manager: Any) -> str:
    """从 UnifiedDataManager 中提取上次使用的 vendor 信息。
    
    Args:
        manager: UnifiedDataManager 实例
        
    Returns:
        vendor 名称字符串
    """
    if hasattr(manager, 'get_stats'):
        stats = manager.get_stats()
        return stats.get('last_vendor_used', 'unknown')
    return "unknown"


def build_situation_string(state: dict) -> str:
    """从 state 中构建当前市场情况的汇总字符串。
    
    将 5 份报告拼接为单一字符串，供 memory 查询和 prompt 使用。
    
    Args:
        state: 图状态字典，需包含 market_report / sentiment_report /
               news_report / fundamentals_report 以及可选的 candlestick_report
    
    Returns:
        拼接后的情况字符串
    """
    return (
        f"{state['market_report']}\n\n"
        f"{state['sentiment_report']}\n\n"
        f"{state['news_report']}\n\n"
        f"{state['fundamentals_report']}\n\n"
        f"{state.get('candlestick_report', '')}"
    )


def format_past_memories(past_memories: list, language: str = "zh") -> str:
    """将历史记忆列表格式化为字符串。
    
    Args:
        past_memories: memory.get_memories() 返回的记录列表
        language: 当前语言 ("zh" / "en")
    
    Returns:
        格式化后的历史记忆字符串
    """
    if not past_memories:
        return "没有找到过去的记忆。" if language == "zh" else "No past memories found."
    
    past_memory_str = ""
    for i, rec in enumerate(past_memories, 1):
        past_memory_str += rec["recommendation"] + "\n\n"
    return past_memory_str
