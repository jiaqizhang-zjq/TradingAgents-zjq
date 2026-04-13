from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import get_data_manager
from tradingagents.agents.utils.logging_utils import log_tool_call, get_vendor_info
from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)


@tool
def get_indicators(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[str, "The current trading date you are trading on, YYYY-mm-dd"],
    look_back_days: Annotated[int, "how many days to look back"] = 30,
    stock_data: Annotated[str, "Optional: pre-fetched stock data in table format"] = "",
) -> str:
    """
    Retrieve technical indicators for a given ticker symbol.
    Uses UnifiedDataManager for consistent data management.
    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        indicator (str): Technical indicator to get the analysis and report of
        curr_date (str): The current trading date you are trading on, YYYY-mm-dd
        look_back_days (int): How many days to look back, default is 30
        stock_data (str): Optional: pre-fetched stock data in table format
    Returns:
        str: A formatted dataframe containing the technical indicators for the specified ticker symbol and indicator.
    """
    logger.debug("🔧 Calling get_indicators for %s, indicator=%s, date=%s", symbol, indicator, curr_date)
    
    manager = get_data_manager()
    result = manager.fetch("get_indicators", symbol, indicator, curr_date, look_back_days, stock_data)
    log_tool_call("get_indicators", get_vendor_info(manager), result)
    
    return result


@tool
def get_all_indicators(
    symbol: Annotated[str, "ticker symbol of the company"],
    curr_date: Annotated[str, "The current trading date you are trading on, YYYY-mm-dd"],
    look_back_days: Annotated[int, "how many days to look back"] = 120,
    stock_data: Annotated[str, "Optional: pre-fetched stock data in table format"] = "",
) -> str:
    """
    Retrieve all technical indicator groups for a given ticker symbol.
    Uses UnifiedDataManager for consistent data management.
    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        curr_date (str): The current trading date you are trading on, YYYY-mm-dd
        look_back_days (int): How many days to look back, default is 120
        stock_data (str): Optional: pre-fetched stock data in table format
    Returns:
        str: A formatted string containing all technical indicator groups
    """
    logger.debug("🔧 Calling get_all_indicators for %s, date=%s", symbol, curr_date)
    
    manager = get_data_manager()
    result = manager.fetch("get_all_indicators", symbol, curr_date, look_back_days, stock_data)
    log_tool_call("get_all_indicators", get_vendor_info(manager), result)
    
    return result