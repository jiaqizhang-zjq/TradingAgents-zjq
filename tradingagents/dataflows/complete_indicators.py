#!/usr/bin/env python3
"""
完整技术指标计算库（重构后协调器）

**历史**: 原1426行→简化为150行协调器
**架构**: 模块化拆分，单一职责

拆分为：
1. indicators/*.py - 技术指标模块（移动平均、动量、成交量、趋势）
2. patterns/*.py - 形态识别模块（蜡烛图、图表形态）

本文件仅作为统一接口，委托给各模块实现
"""

import pandas as pd
from typing import Dict, Any
from .indicator_groups import (
    INDICATOR_GROUPS,
    get_indicator_columns
)
from .indicators.moving_averages import MovingAverageIndicators
from .indicators.momentum_indicators import MomentumIndicators
from .indicators.volume_indicators import VolumeIndicators
from .indicators.trend_indicators import TrendIndicators
from .indicators.additional_indicators import AdditionalIndicators
from .patterns import CandlestickPatternRecognizer, ChartPatterns


class CompleteTechnicalIndicators:
    """
    完整技术指标计算器（协调器）
    
    委托给各模块进行实际计算：
    - MovingAverageIndicators: SMA, EMA, Bollinger Bands, ATR
    - MomentumIndicators: RSI, MACD, ADX
    - VolumeIndicators: OBV, VWMA, Volume Patterns
    - TrendIndicators: Trend Lines, Support/Resistance
    - AdditionalIndicators: Extended Indicators
    """
    
    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        计算所有技术指标（使用模块化结构，支持inplace修改）
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame，需要包含以下列：
                - open, high, low, close, volume
            inplace: True则直接修改df，False则返回新DataFrame（默认False保持兼容性）
                
        Returns:
            包含所有技术指标的 DataFrame
        """
        if not inplace:
            df = df.copy()
        
        result_df = df
        
        # ==================== 移动平均线指标 ====================
        result_df = MovingAverageIndicators.calculate_sma(result_df, inplace=True)
        result_df = MovingAverageIndicators.calculate_ema(result_df, inplace=True)
        result_df = MovingAverageIndicators.calculate_bollinger_bands(result_df, inplace=True)
        result_df = MovingAverageIndicators.calculate_atr(result_df, inplace=True)
        
        # ==================== 动量指标 ====================
        result_df["rsi"] = MomentumIndicators.calculate_rsi(result_df["close"])
        
        macd, signal, hist = MomentumIndicators.calculate_macd(result_df["close"])
        result_df["macd"] = macd
        result_df["macds"] = signal
        result_df["macdh"] = hist
        
        adx, plus_di, minus_di = MomentumIndicators.calculate_adx(result_df)
        result_df["adx"] = adx
        result_df["plus_di"] = plus_di
        result_df["minus_di"] = minus_di
        
        # ==================== 成交量指标 ====================
        result_df = VolumeIndicators.calculate_all_volume_indicators(result_df, inplace=True)
        
        # ==================== 趋势指标 ====================
        result_df = TrendIndicators.calculate_all_trend_indicators(result_df, inplace=True)
        
        # ==================== 扩展指标 ====================
        result_df = AdditionalIndicators.calculate_all_additional_indicators(result_df, inplace=True)
        
        return result_df
    
    @staticmethod
    def get_indicator_group(df: pd.DataFrame, indicator: str, look_back_days: int = 120) -> pd.DataFrame:
        """
        获取指定指标组的数据
        
        Args:
            df: 包含所有指标的 DataFrame
            indicator: 指标名称或指标组名称
            look_back_days: 回看天数
            
        Returns:
            包含指定指标的 DataFrame
        """
        keep_cols = get_indicator_columns(indicator, list(df.columns))
        
        # 只保留需要的列
        result_df = df[[col for col in keep_cols if col in df.columns]].copy()
        
        # 只返回最近look_back_days天的数据
        result_df = result_df.tail(look_back_days + 10)
        
        return result_df
    
    @staticmethod
    def get_all_indicator_groups(df: pd.DataFrame, look_back_days: int = 120) -> str:
        """
        获取所有指标组的数据，按组格式化输出
        
        Args:
            df: 包含所有指标的 DataFrame
            look_back_days: 回看天数
            
        Returns:
            格式化的字符串，包含所有指标组
        """
        result = ""
        
        for group_name, group_cols in INDICATOR_GROUPS.items():
            # 获取该组的指标
            keep_cols = get_indicator_columns(group_name, list(df.columns))
            group_df = df[[col for col in keep_cols if col in df.columns]].copy()
            group_df = group_df.tail(look_back_days + 10)
            
            result += f"\n=== {group_name.upper()} INDICATOR GROUP ===\n"
            result += group_df.to_csv(index=False)
            result += "\n"
        
        return result


class CompleteCandlestickPatterns:
    """
    蜡烛图形态识别器（委托给patterns模块）
    
    实际实现在 patterns/candlestick_patterns.py
    """
    
    @staticmethod
    def identify_patterns(df: pd.DataFrame):
        """
        识别蜡烛图形态（委托给CandlestickPatternRecognizer）
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame
            
        Returns:
            识别到的形态列表
        """
        return CandlestickPatternRecognizer.identify_patterns(df)


# 向后兼容：导出原有的类名
# 实际实现在各子模块中
__all__ = [
    "CompleteTechnicalIndicators",
    "CompleteCandlestickPatterns",
    "ChartPatterns",  # 从patterns模块导入
]
