from .alpha_vantage_common import _make_api_request, format_datetime_for_api

def get_news(ticker, start_date, end_date, limit: int = 10) -> dict[str, str] | str:
    """Returns live and historical market news & sentiment data from premier news outlets worldwide.

    Covers stocks, cryptocurrencies, forex, and topics like fiscal policy, mergers & acquisitions, IPOs.

    Args:
        ticker: Stock symbol for news articles.
        start_date: Start date for news search.
        end_date: End date for news search.
        limit: Maximum number of articles (default 10).

    Returns:
        Dictionary containing news sentiment data or JSON string.
        
    Raises:
        ValueError: 如果输入参数无效
    """
    from tradingagents.utils.validators import validate_symbol, validate_date_range
    
    validate_symbol(ticker)
    validate_date_range(start_date, end_date)
    if limit < 1 or limit > 100:
        raise ValueError(f"limit必须在1-100之间，当前值：{limit}")

    params = {
        "tickers": ticker,
        "time_from": format_datetime_for_api(start_date),
        "time_to": format_datetime_for_api(end_date),
        "limit": str(limit),
    }

    return _make_api_request("NEWS_SENTIMENT", params)

def get_global_news(curr_date, look_back_days: int = 7, limit: int = 20) -> dict[str, str] | str:
    """Returns global market news & sentiment data without ticker-specific filtering.

    Covers broad market topics like financial markets, economy, and more.

    Args:
        curr_date: Current date in yyyy-mm-dd format.
        look_back_days: Number of days to look back (default 7).
        limit: Maximum number of articles (default 50).

    Returns:
        Dictionary containing global news sentiment data or JSON string.
        
    Raises:
        ValueError: 如果输入参数无效
    """
    from datetime import datetime, timedelta
    from tradingagents.utils.validators import validate_date
    
    validate_date(curr_date)
    if look_back_days < 1 or look_back_days > 365:
        raise ValueError(f"look_back_days必须在1-365之间，当前值：{look_back_days}")
    if limit < 1 or limit > 100:
        raise ValueError(f"limit必须在1-100之间，当前值：{limit}")

    # Calculate start date
    curr_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    start_dt = curr_dt - timedelta(days=look_back_days)
    start_date = start_dt.strftime("%Y-%m-%d")

    params = {
        "topics": "financial_markets,economy_macro,economy_monetary",
        "time_from": format_datetime_for_api(start_date),
        "time_to": format_datetime_for_api(curr_date),
        "limit": str(limit),
    }

    return _make_api_request("NEWS_SENTIMENT", params)


def get_insider_transactions(symbol: str) -> dict[str, str] | str:
    """Returns latest and historical insider transactions by key stakeholders.

    Covers transactions by founders, executives, board members, etc.

    Args:
        symbol: Ticker symbol. Example: "IBM".

    Returns:
        Dictionary containing insider transaction data or JSON string.
        
    Raises:
        ValueError: 如果股票代码无效
    """
    from tradingagents.utils.validators import validate_symbol
    validate_symbol(symbol)

    params = {
        "symbol": symbol,
    }

    return _make_api_request("INSIDER_TRANSACTIONS", params)