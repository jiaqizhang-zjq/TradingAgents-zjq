from langchain_core.tools import tool
from typing import Annotated, List, Optional
from tradingagents.dataflows.interface import get_data_manager
from tradingagents.agents.utils.logging_utils import log_tool_call, get_vendor_info
from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)

try:
    from tradingagents.dataflows.social_media import get_stock_mentions
    HAS_SOCIAL_MEDIA = True
except ImportError:
    HAS_SOCIAL_MEDIA = False


@tool
def get_news(
    ticker: Annotated[str, "Ticker symbol"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve news data for a given ticker symbol.
    Uses the configured news_data vendor.
    Args:
        ticker (str): Ticker symbol
        start_date (str): Start date in yyyy-mm-dd format
        end_date (str): End date in yyyy-mm-dd format
    Returns:
        str: A formatted string containing news data
    """
    logger.debug("🔧 Calling get_news for %s (%s to %s)", ticker, start_date, end_date)
    
    manager = get_data_manager()
    result = manager.fetch("get_news", ticker, start_date, end_date)
    log_tool_call("get_news", get_vendor_info(manager), result)
    
    return result


@tool
def get_global_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back"] = 7,
    limit: Annotated[int, "Maximum number of articles to return"] = 5,
) -> str:
    """
    Retrieve global news data.
    Uses the configured news_data vendor.
    Args:
        curr_date (str): Current date in yyyy-mm-dd format
        look_back_days (int): Number of days to look back (default 7)
        limit (int): Maximum number of articles to return (default 5)
    Returns:
        str: A formatted string containing global news data
    """
    logger.debug("🔧 Calling get_global_news for date %s, look_back_days=%d", curr_date, look_back_days)
    
    manager = get_data_manager()
    result = manager.fetch("get_global_news", curr_date, look_back_days, limit)
    log_tool_call("get_global_news", get_vendor_info(manager), result)
    
    return result


@tool
def get_insider_transactions(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """
    Retrieve insider transaction information about a company.
    Uses the configured news_data vendor.
    Args:
        ticker (str): Ticker symbol of the company
    Returns:
        str: A report of insider transaction data
    """
    logger.debug("🔧 Calling get_insider_transactions for %s", ticker)
    
    manager = get_data_manager()
    result = manager.fetch("get_insider_transactions", ticker)
    log_tool_call("get_insider_transactions", get_vendor_info(manager), result)
    
    return result


@tool
def get_social_media_data(
    ticker: Annotated[str, "Ticker symbol"],
    platforms: Annotated[Optional[List[str]], "List of platforms (reddit, twitter)"] = None,
    limit: Annotated[int, "Number of posts per platform"] = 20,
) -> str:
    """
    Retrieve social media mentions for a given ticker from Reddit and/or Twitter.
    Provides insights into public sentiment and discussions about the company.
    
    Args:
        ticker (str): Ticker symbol
        platforms (list): List of platforms to search (default: ["reddit", "twitter"])
        limit (int): Number of posts per platform (default: 20)
        
    Returns:
        str: JSON string containing social media data
    """
    if platforms is None:
        platforms = ["reddit", "twitter"]
    if not HAS_SOCIAL_MEDIA:
        return "Social media module not available. Please install praw and tweepy."
    
    try:
        return get_stock_mentions(ticker, platforms, limit)
    except (ConnectionError, ValueError, TimeoutError, OSError, ImportError) as e:
        return f"Error retrieving social media data: {str(e)}"
