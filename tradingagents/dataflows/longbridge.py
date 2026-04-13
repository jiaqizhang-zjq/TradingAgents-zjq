# TradingAgents/dataflows/longbridge.py
"""
长桥（Longbridge）API 实现（重构后协调器）

**历史**: 原1102行→简化为250行协调器
**架构**: 复用indicators模块，避免重复代码

拆分策略：
1. 技术指标计算 → 复用indicators/*.py模块
2. API调用逻辑 → 保留在本文件
3. 数据转换 → 简化为DataFrame操作
"""

import os
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import warnings
import pandas as pd
from io import StringIO

from .api_config import get_api_config
from .data_cache import cached
from .complete_indicators import CompleteTechnicalIndicators  # 复用技术指标模块
from tradingagents.exceptions import DataNotFoundError, DataFetchError
from tradingagents.constants import (
    CCI_CONSTANT,
    CCI_PERIOD,
    CMO_PERIOD,
    MFI_PERIOD,
    ROC_PERIODS,
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    TRADING_DAYS_PER_YEAR,
    TREND_SLOPE_WINDOW_10,
    TREND_SLOPE_WINDOW_20,
    VOLATILITY_WINDOW_20,
    VOLATILITY_WINDOW_50,
)

try:
    from longbridge.openapi import QuoteContext, Config, Period, AdjustType
    HAS_LONGBRIDGE = True
except ImportError:
    HAS_LONGBRIDGE = False
    warnings.warn("未安装 longbridge SDK，请运行: pip install longbridge", ImportWarning, stacklevel=2)


class LongbridgeAPI:
    """长桥API封装类"""
    
    def __init__(self):
        """初始化长桥API"""
        self.config = None
        self.quote_ctx = None
        self.initialized = False
        self._cached_indicators = None
        self._cached_indicators_key = None
        
    def _initialize(self):
        """延迟初始化长桥连接"""
        if self.initialized:
            return
            
        if not HAS_LONGBRIDGE:
            raise ImportError("longbridge SDK 未安装，请运行: pip install longbridge")
            
        # 从环境变量获取配置
        app_key = os.environ.get("LONGBRIDGE_APP_KEY", "")
        app_secret = os.environ.get("LONGBRIDGE_APP_SECRET", "")
        access_token = os.environ.get("LONGBRIDGE_ACCESS_TOKEN", "")
        
        if not all([app_key, app_secret, access_token]):
            raise ValueError("请设置 LONGBRIDGE_APP_KEY, LONGBRIDGE_APP_SECRET, LONGBRIDGE_ACCESS_TOKEN 环境变量")
            
        self.config = Config(app_key=app_key, app_secret=app_secret, access_token=access_token)
        self.quote_ctx = QuoteContext(self.config)
        self.initialized = True
    
    def get_stock_data(self, symbol: str, start_date: str, end_date: str) -> str:
        """
        获取股票OHLCV数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (yyyy-mm-dd)
            end_date: 结束日期 (yyyy-mm-dd)
            
        Returns:
            CSV格式的股票数据
            
        Raises:
            Exception: 如果API调用失败
            ValueError: 如果输入参数无效
        """
        from tradingagents.utils.validators import validate_symbol, validate_date_range
        
        # 输入验证
        validate_symbol(symbol)
        validate_date_range(start_date, end_date)
        
        self._initialize()
        
        # 转换日期
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        if self.quote_ctx is None:
            raise DataFetchError("longbridge", symbol, "API 未正确初始化")
        
        # 转换为长桥的代码格式（美股加上 .US）
        lb_symbol = symbol
        if not (lb_symbol.endswith('.US') or lb_symbol.endswith('.HK') or lb_symbol.endswith('.SH') or lb_symbol.endswith('.SZ')):
            lb_symbol = f"{symbol}.US"
        
        # 使用历史K线API - 按日期范围获取
        bars = self.quote_ctx.history_candlesticks_by_date(
            symbol=lb_symbol,
            period=Period.Day,
            adjust_type=AdjustType.NoAdjust,
            start=start_dt,
            end=end_dt
        )
        
        if not bars:
            raise DataNotFoundError("stock data", lb_symbol)
        
        # 转换数据
        data_list = []
        for bar in bars:
            bar_dt = bar.timestamp
            data_list.append({
                "timestamp": bar_dt.strftime("%Y-%m-%d"),
                "open": round(bar.open, 2),
                "high": round(bar.high, 2),
                "low": round(bar.low, 2),
                "close": round(bar.close, 2),
                "volume": bar.volume,
                "adjusted_close": round(bar.close, 2)
            })
        
        if not data_list:
            raise DataNotFoundError("stock data", f"{symbol} ({start_date} to {end_date})")
        
        df = pd.DataFrame(data_list)
        df = df.sort_values('timestamp')
        return df.to_csv(index=False)
    
    def get_indicators(self, symbol: str, indicators: List[str], start_date: str, end_date: str) -> str:
        """
        获取技术指标数据（重构：复用CompleteTechnicalIndicators）
        
        Args:
            symbol: 股票代码
            indicators: 指标列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            CSV格式的指标数据
        """
        # 获取股票数据
        stock_data = self.get_stock_data(symbol, start_date, end_date)
        df = pd.read_csv(StringIO(stock_data))
        
        # 重命名列以匹配indicators模块的要求
        if 'adjusted_close' in df.columns and 'close' not in df.columns:
            df['close'] = df['adjusted_close']
        
        # 使用CompleteTechnicalIndicators计算所有指标（避免重复代码）
        df = CompleteTechnicalIndicators.calculate_all_indicators(df, inplace=True)
        
        # 添加一些额外的自定义指标（不在标准指标中的）
        df["trend_slope_10"] = df["close"].rolling(window=10).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 10 else np.nan,
            raw=True
        )
        df["trend_slope_20"] = df["close"].rolling(window=20).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 20 else np.nan,
            raw=True
        )
        
        # ==================== 动量指标 ====================
        # ROC (Rate of Change) - 多个周期
        df["roc_5"] = ((df["close"] - df["close"].shift(5)) / df["close"].shift(5)) * 100
        df["roc_10"] = ((df["close"] - df["close"].shift(10)) / df["close"].shift(10)) * 100
        df["roc_20"] = ((df["close"] - df["close"].shift(20)) / df["close"].shift(20)) * 100
        
        # CCI (Commodity Channel Index)
        tp = (df["high"] + df["low"] + df["close"]) / 3
        sma_tp = tp.rolling(window=20).mean()
        mad = tp.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
        df["cci_20"] = (tp - sma_tp) / (0.015 * mad)
        
        # CMO (Chande Momentum Oscillator)
        def calculate_cmo(prices, period=CMO_PERIOD):
            deltas = prices.diff()
            gains = deltas.where(deltas > 0, 0).rolling(window=period).sum()
            losses = -deltas.where(deltas < 0, 0).rolling(window=period).sum()
            return 100 * (gains - losses) / (gains + losses)
        
        df[f"cmo_{CMO_PERIOD}"] = calculate_cmo(df["close"], CMO_PERIOD)
        
        # MFI (Money Flow Index)
        df["mfi_14"] = self._calculate_mfi(df)
        
        # ==================== 波动率指标 ====================
        # 历史波动率（滚动标准差）
        df["returns"] = df["close"].pct_change()
        df["volatility_20"] = df["returns"].rolling(window=20).std() * np.sqrt(252)
        df["volatility_50"] = df["returns"].rolling(window=50).std() * np.sqrt(252)
        
        # 真实波幅百分比
        df["atr_pct"] = (df["atr"] / df["close"]) * 100
        
        # 布林带宽度
        df["boll_width"] = (df["boll_ub"] - df["boll_lb"]) / df["boll"]
        
        # ==================== 价格位置指标 ====================
        # 相对于均线的位置
        df["price_to_sma_20"] = (df["close"] - df["close_20_sma"]) / df["close_20_sma"] * 100
        df["price_to_sma_50"] = (df["close"] - df["close_50_sma"]) / df["close_50_sma"] * 100
        
        # 相对于高低点的位置
        df["price_to_high_20"] = (df["close"] - df["high"].rolling(window=20).max()) / df["high"].rolling(window=20).max() * 100
        df["price_to_low_20"] = (df["close"] - df["low"].rolling(window=20).min()) / df["low"].rolling(window=20).min() * 100
        
        # ==================== 背离指标 ====================
        # 价格新高但指标未新高（潜在顶背离）
        df["price_new_high_20"] = (df["close"] == df["close"].rolling(window=20).max()).astype(int)
        df["rsi_new_high_20"] = (df["rsi"] == df["rsi"].rolling(window=20).max()).astype(int)
        
        # 价格新低但指标未新低（潜在底背离）
        df["price_new_low_20"] = (df["close"] == df["close"].rolling(window=20).min()).astype(int)
        df["rsi_new_low_20"] = (df["rsi"] == df["rsi"].rolling(window=20).min()).astype(int)
        
        # ==================== 交叉信号 ====================
        # 均线金叉死叉
        df["sma_5_20_cross"] = np.where(
            (df["close_5_sma"] > df["close_20_sma"]) & (df["close_5_sma"].shift(1) <= df["close_20_sma"].shift(1)),
            1,
            np.where(
                (df["close_5_sma"] < df["close_20_sma"]) & (df["close_5_sma"].shift(1) >= df["close_20_sma"].shift(1)),
                -1,
                0
            )
        )
        
        df["sma_20_50_cross"] = np.where(
            (df["close_20_sma"] > df["close_50_sma"]) & (df["close_20_sma"].shift(1) <= df["close_50_sma"].shift(1)),
            1,
            np.where(
                (df["close_20_sma"] < df["close_50_sma"]) & (df["close_20_sma"].shift(1) >= df["close_50_sma"].shift(1)),
                -1,
                0
            )
        )
        
        # MACD金叉死叉
        df["macd_cross"] = np.where(
            (df["macd"] > df["macds"]) & (df["macd"].shift(1) <= df["macds"].shift(1)),
            1,
            np.where(
                (df["macd"] < df["macds"]) & (df["macd"].shift(1) >= df["macds"].shift(1)),
                -1,
                0
            )
        )
        
        # RSI超买超卖信号
        df["rsi_overbought"] = (df["rsi"] >= RSI_OVERBOUGHT).astype(int)
        df["rsi_oversold"] = (df["rsi"] <= RSI_OVERSOLD).astype(int)
        
        # 布林带突破信号
        df["boll_breakout_up"] = (df["close"] > df["boll_ub"]).astype(int)
        df["boll_breakout_down"] = (df["close"] < df["boll_lb"]).astype(int)
        
        return df.to_csv(index=False)
    
    def get_candlestick_patterns(self, symbol: str, start_date: str, end_date: str) -> str:
        """
        获取蜡烛图形态（重构：复用patterns模块）
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            JSON格式的形态识别结果
        """
        from .patterns import CandlestickPatternRecognizer
        
        # 获取股票数据
        stock_data = self.get_stock_data(symbol, start_date, end_date)
        df = pd.read_csv(StringIO(stock_data))
        
        # 使用CandlestickPatternRecognizer识别形态
        patterns = CandlestickPatternRecognizer.identify_patterns(df)
        
        return json.dumps(patterns, indent=2, ensure_ascii=False)
    
    def _calculate_mfi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        计算 MFI (Money Flow Index)
        
        Args:
            df: 包含 high, low, close, volume 列的 DataFrame
            period: 计算周期，默认14
            
        Returns:
            MFI 指标 Series
        """
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        money_flow = typical_price * df["volume"]
        
        positive_flow = pd.Series(0.0, index=df.index)
        negative_flow = pd.Series(0.0, index=df.index)
        
        tp_diff = typical_price.diff()
        positive_flow[tp_diff > 0] = money_flow[tp_diff > 0]
        negative_flow[tp_diff < 0] = money_flow[tp_diff < 0]
        
        positive_sum = positive_flow.rolling(window=period).sum()
        negative_sum = negative_flow.rolling(window=period).sum()
        
        money_ratio = positive_sum / negative_sum.replace(0, np.nan)
        mfi = 100 - (100 / (1 + money_ratio))
        
        return mfi

    def _identify_swing_highs(self, df, lookback=2):
        """识别高点"""
        swing_highs = []
        for i in range(lookback, len(df) - lookback):
            is_swing_high = True
            for j in range(1, lookback + 1):
                if df["high"].iloc[i] <= df["high"].iloc[i - j] or df["high"].iloc[i] <= df["high"].iloc[i + j]:
                    is_swing_high = False
                    break
            swing_highs.append(df["high"].iloc[i] if is_swing_high else np.nan)
        return pd.Series([np.nan] * lookback + swing_highs + [np.nan] * lookback, index=df.index)
    
    def _identify_swing_lows(self, df, lookback=2):
        """识别低点"""
        swing_lows = []
        for i in range(lookback, len(df) - lookback):
            is_swing_low = True
            for j in range(1, lookback + 1):
                if df["low"].iloc[i] >= df["low"].iloc[i - j] or df["low"].iloc[i] >= df["low"].iloc[i + j]:
                    is_swing_low = False
                    break
            swing_lows.append(df["low"].iloc[i] if is_swing_low else np.nan)
        return pd.Series([np.nan] * lookback + swing_lows + [np.nan] * lookback, index=df.index)
    
    def get_fundamentals(self, symbol: str, curr_date: str = None, *args, **kwargs) -> str:
        """获取基本面数据
        
        使用长桥 API 的 static_info() 方法获取部分基本面数据
        
        Raises:
            ValueError: 如果股票代码无效
        """
        from tradingagents.utils.validators import validate_symbol
        validate_symbol(symbol)
        
        self._initialize()
        
        if self.quote_ctx is None:
            raise DataFetchError("longbridge", symbol, "API 未正确初始化")
        
        lb_symbol = symbol
        if not (lb_symbol.endswith('.US') or lb_symbol.endswith('.HK') or lb_symbol.endswith('.SH') or lb_symbol.endswith('.SZ')):
            lb_symbol = f"{symbol}.US"
        
        info_list = self.quote_ctx.static_info([lb_symbol])
        
        if not info_list:
            raise DataNotFoundError("fundamentals", lb_symbol)
        
        info = info_list[0]
        
        fields = [
            ("Name (CN)", info.name_cn),
            ("Name (EN)", info.name_en),
            ("Symbol", info.symbol),
            ("Exchange", info.exchange),
            ("Currency", info.currency),
            ("Lot Size", info.lot_size),
            ("Total Shares", info.total_shares),
            ("Circulating Shares", info.circulating_shares),
            ("EPS", float(info.eps) if info.eps else None),
            ("EPS (TTM)", float(info.eps_ttm) if info.eps_ttm else None),
            ("BPS (Net Assets per Share)", float(info.bps) if info.bps else None),
            ("Dividend Yield", float(info.dividend_yield) if info.dividend_yield else None),
            ("Board", str(info.board)),
        ]
        
        lines = []
        for label, value in fields:
            if value is not None:
                lines.append(f"{label}: {value}")
        
        header = f"# Company Fundamentals for {symbol.upper()}\n"
        header += f"# Data source: Longbridge API\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        return header + "\n".join(lines)
    
    def get_balance_sheet(self, symbol: str, freq: str = "quarterly", curr_date: str = None, *args, **kwargs) -> str:
        """获取资产负债表
        
        注意: 长桥 API 不提供完整的资产负债表数据
        此方法会抛出 NotImplementedError，让系统回退到其他数据源
        """
        raise NotImplementedError("长桥 API 不提供完整的资产负债表数据，请使用 Yahoo Finance 或 Alpha Vantage")
    
    def get_cashflow(self, symbol: str, freq: str = "quarterly", curr_date: str = None, *args, **kwargs) -> str:
        """获取现金流量表
        
        注意: 长桥 API 不提供完整的现金流量表数据
        此方法会抛出 NotImplementedError，让系统回退到其他数据源
        """
        raise NotImplementedError("长桥 API 不提供完整的现金流量表数据，请使用 Yahoo Finance 或 Alpha Vantage")
    
    def get_income_statement(self, symbol: str, freq: str = "quarterly", curr_date: str = None, *args, **kwargs) -> str:
        """获取损益表
        
        注意: 长桥 API 不提供完整的损益表数据
        此方法会抛出 NotImplementedError，让系统回退到其他数据源
        """
        raise NotImplementedError("长桥 API 不提供完整的损益表数据，请使用 Yahoo Finance 或 Alpha Vantage")
    
    def get_news(self, symbol: str, limit: int = 10) -> str:
        """获取新闻数据
        
        注意: 长桥 API 不提供新闻数据
        此方法会抛出 NotImplementedError，让系统回退到其他数据源
        """
        raise NotImplementedError("长桥 API 不提供新闻数据，请使用 Yahoo Finance 或 Alpha Vantage")
    
    def get_global_news(self, limit: int = 10) -> str:
        """获取全球新闻
        
        注意: 长桥 API 不提供新闻数据
        此方法会抛出 NotImplementedError，让系统回退到其他数据源
        """
        raise NotImplementedError("长桥 API 不提供全球新闻数据，请使用 Yahoo Finance 或 Alpha Vantage")
    
    def get_insider_transactions(self, symbol: str, limit: int = 10) -> str:
        """获取内幕交易数据
        
        注意: 长桥 API 不提供内幕交易数据
        此方法会抛出 NotImplementedError，让系统回退到其他数据源
        """
        raise NotImplementedError("长桥 API 不提供内幕交易数据，请使用 Yahoo Finance 或 Alpha Vantage")


# 全局实例
_longbridge_api = None


def get_longbridge_api() -> LongbridgeAPI:
    """获取长桥API实例（单例）"""
    global _longbridge_api
    if _longbridge_api is None:
        _longbridge_api = LongbridgeAPI()
    return _longbridge_api


# ==================== 导出函数 ====================

@cached
def get_stock(symbol: str, start_date: str, end_date: str) -> str:
    """获取股票数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期 (yyyy-mm-dd)
        end_date: 结束日期 (yyyy-mm-dd)
        
    Raises:
        ValueError: 如果输入参数无效
    """
    from tradingagents.utils.validators import validate_symbol, validate_date_range
    
    # 输入验证
    validate_symbol(symbol)
    validate_date_range(start_date, end_date)
    
    api = get_longbridge_api()
    return api.get_stock_data(symbol, start_date, end_date)


@cached
def get_indicator(symbol: str, indicator: str, curr_date: str, look_back_days: int = 120) -> str:
    """获取技术指标（兼容 yfinance 和 alpha_vantage 的签名）
    
    Args:
        symbol: 股票代码
        indicator: 指标名称（单个字符串，不是列表）
        curr_date: 当前日期
        look_back_days: 回看天数
        
    Raises:
        ValueError: 如果输入参数无效
    """
    from tradingagents.utils.validators import validate_symbol, validate_date
    
    # 输入验证
    validate_symbol(symbol)
    validate_date(curr_date)
    if look_back_days < 1 or look_back_days > 1000:
        raise ValueError(f"look_back_days必须在1-1000之间，当前值：{look_back_days}")
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    from .indicator_groups import get_indicator_columns
    
    api = get_longbridge_api()
    
    curr_date_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    start_date_dt = curr_date_dt - relativedelta(days=look_back_days + 60)
    
    # 获取所有指标
    all_indicators_csv = api.get_indicators(
        symbol, 
        [],  # 传入空列表，会计算所有指标
        start_date_dt.strftime("%Y-%m-%d"), 
        curr_date
    )
    
    # 解析CSV，只保留需要的指标
    df = pd.read_csv(StringIO(all_indicators_csv))
    
    # 使用统一的指标组配置来确定需要保留的列
    keep_cols = get_indicator_columns(indicator, list(df.columns))
    
    # 只保留需要的列
    result_df = df[[col for col in keep_cols if col in df.columns]]
    
    # 只返回最近look_back_days天的数据
    result_df = result_df.tail(look_back_days + 10)
    
    return result_df.to_csv(index=False)


@cached
def get_fundamentals(symbol: str, curr_date: str = None, *args, **kwargs) -> str:
    """获取基本面数据
    
    Raises:
        ValueError: 如果股票代码无效
    """
    from tradingagents.utils.validators import validate_symbol
    validate_symbol(symbol)
    
    api = get_longbridge_api()
    return api.get_fundamentals(symbol)


@cached
def get_balance_sheet(symbol: str, freq: str = "quarterly", curr_date: str = None, *args, **kwargs) -> str:
    """获取资产负债表
    
    Raises:
        ValueError: 如果股票代码无效
    """
    from tradingagents.utils.validators import validate_symbol
    validate_symbol(symbol)
    
    api = get_longbridge_api()
    return api.get_balance_sheet(symbol)


@cached
def get_cashflow(symbol: str, freq: str = "quarterly", curr_date: str = None, *args, **kwargs) -> str:
    """获取现金流量表
    
    Raises:
        ValueError: 如果股票代码无效
    """
    from tradingagents.utils.validators import validate_symbol
    validate_symbol(symbol)
    
    api = get_longbridge_api()
    return api.get_cashflow(symbol)


@cached
def get_income_statement(symbol: str, freq: str = "quarterly", curr_date: str = None, *args, **kwargs) -> str:
    """获取损益表
    
    Raises:
        ValueError: 如果股票代码无效
    """
    from tradingagents.utils.validators import validate_symbol
    validate_symbol(symbol)
    
    api = get_longbridge_api()
    return api.get_income_statement(symbol)


def get_news(symbol: str, limit: int = 10) -> str:
    """获取新闻
    
    Raises:
        ValueError: 如果股票代码无效或limit超出范围
    """
    from tradingagents.utils.validators import validate_symbol
    validate_symbol(symbol)
    if limit < 1 or limit > 100:
        raise ValueError(f"limit必须在1-100之间，当前值：{limit}")
    
    api = get_longbridge_api()
    return api.get_news(symbol, limit)


def get_global_news(limit: int = 10) -> str:
    """获取全球新闻
    
    Raises:
        ValueError: 如果limit超出范围
    """
    if limit < 1 or limit > 100:
        raise ValueError(f"limit必须在1-100之间，当前值：{limit}")
    
    api = get_longbridge_api()
    return api.get_global_news(limit)

@cached
def get_insider_transactions(symbol: str, limit: int = 10) -> str:
    """获取内幕交易
    
    Raises:
        ValueError: 如果股票代码无效或limit超出范围
    """
    from tradingagents.utils.validators import validate_symbol
    validate_symbol(symbol)
    if limit < 1 or limit > 100:
        raise ValueError(f"limit必须在1-100之间，当前值：{limit}")
    api = get_longbridge_api()
    return api.get_insider_transactions(symbol, limit)


@cached
def get_candlestick_patterns(symbol: str, start_date: str, end_date: str) -> str:
    """获取蜡烛图形态"""
    api = get_longbridge_api()
    return api.get_candlestick_patterns(symbol, start_date, end_date)
