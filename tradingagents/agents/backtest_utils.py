"""
回测工具函数
============
提供回测相关的计算和数据获取工具。
"""

from datetime import datetime, timedelta
from typing import Optional

from tradingagents.utils.validators import validate_symbol, validate_date


def get_price_on_date(symbol: str, target_date: str) -> Optional[float]:
    """
    获取指定日期的股票价格
    
    Args:
        symbol: 股票代码
        target_date: 目标日期 (YYYY-MM-DD)
    
    Returns:
        股票价格或None
    """
    validate_symbol(symbol)
    validate_date(target_date)
    
    try:
        from tradingagents.dataflows.interface import get_data_manager
        
        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
        start_date = target_date
        end_date = target_date
        
        print(f"Fetching price for {symbol} on {target_date}")
        
        manager = get_data_manager()
        stock_data = manager.fetch("get_stock_data", symbol, start_date, end_date)
        
        if not stock_data or stock_data == "N/A" or (isinstance(stock_data, str) and stock_data.strip() == ""):
            print(f"No data returned for {symbol}")
            return None
        
        print(f"Data type: {type(stock_data)}, length: {len(stock_data) if isinstance(stock_data, str) else 'N/A'}")
        
        # 尝试解析JSON格式
        import json
        try:
            data = json.loads(stock_data) if isinstance(stock_data, str) else stock_data
            if isinstance(data, dict):
                if 'close' in data:
                    return float(data['close'])
                if 'Close' in data:
                    return float(data['Close'])
        except (json.JSONDecodeError, TypeError):
            pass
        
        # 尝试解析CSV格式
        import io
        import pandas as pd
        if isinstance(stock_data, str) and ('close' in stock_data.lower() or 'Close' in stock_data):
            try:
                df = pd.read_csv(io.StringIO(stock_data))
                if 'close' in df.columns:
                    return float(df['close'].iloc[-1])
                if 'Close' in df.columns:
                    return float(df['Close'].iloc[-1])
                if 'adjusted_close' in df.columns:
                    return float(df['adjusted_close'].iloc[-1])
            except Exception:
                pass
        
        # 尝试直接转换为浮点数
        try:
            return float(stock_data)
        except (ValueError, TypeError):
            pass
            
        print(f"无法解析 {symbol} 的价格数据")
        return None
        
    except Exception as e:
        print(f"获取 {symbol} 在 {target_date} 的价格失败: {e}")
        return None


def calculate_return(buy_price: float, current_price: float) -> Optional[float]:
    """计算收益率"""
    if buy_price is None or current_price is None:
        return None
    return (current_price - buy_price) / buy_price


def calculate_profit(buy_price: float, current_price: float, initial_capital: float = 10000) -> Optional[float]:
    """计算总收益"""
    if buy_price is None or current_price is None:
        return None
    shares = initial_capital / buy_price
    return (current_price - buy_price) * shares


def calculate_shares(buy_price: float, initial_capital: float = 10000) -> float:
    """计算持股数量"""
    if buy_price is None or buy_price <= 0:
        return 0
    return initial_capital / buy_price


def is_market_open(symbol: str, target_date: str = None) -> bool:
    """通过获取股票数据判断是否开盘"""
    from tradingagents.agents.utils.agent_utils import is_market_open as check_market
    return check_market(symbol, target_date)


def determine_outcome(prediction: str, actual_return: float, buy_price: float, current_price: float) -> str:
    """
    判断预测是否正确
    
    Args:
        prediction: 预测方向 (BUY/SELL/HOLD)
        actual_return: 实际收益率
        buy_price: 买入价格
        current_price: 当前价格
    
    Returns:
        outcome: 'correct', 'incorrect', 或 'partial'
    """
    if prediction == "HOLD":
        if -0.02 <= actual_return <= 0.02:
            return "correct"
        elif abs(actual_return) > 0.05:
            return "incorrect"
        else:
            return "partial"
    elif prediction == "BUY":
        if actual_return > 0:
            return "correct"
        elif actual_return < 0:
            return "incorrect"
        else:
            return "partial"
    elif prediction == "SELL":
        short_return = (buy_price - current_price) / buy_price
        if short_return > 0:
            return "correct"
        elif short_return < 0:
            return "incorrect"
        else:
            return "partial"
    else:
        if -0.02 <= actual_return <= 0.02:
            return "correct"
        else:
            return "partial"
