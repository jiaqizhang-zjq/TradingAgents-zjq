#!/usr/bin/env python3
"""图表形态识别模块
包含头肩顶/底、双顶/底、三角形等西方技术分析形态
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple

from tradingagents.constants import (
    PEAK_TROUGH_WINDOW,
    HEAD_SHOULDERS_TOLERANCE,
    DOUBLE_TOP_BOTTOM_TOLERANCE,
    TRIANGLE_FLAT_TOLERANCE,
    FLAG_TREND_THRESHOLD,
    FLAG_RANGE_THRESHOLD,
)


def _find_peaks_and_troughs(df: pd.DataFrame, window: int = PEAK_TROUGH_WINDOW) -> Tuple[List[int], List[int]]:
    """找出价格的峰值和谷值索引"""
    highs = df["high"].values
    lows = df["low"].values
    peaks: List[int] = []
    troughs: List[int] = []

    for i in range(window, len(df) - window):
        if all(highs[i] > highs[i - j] for j in range(1, window + 1)) and \
           all(highs[i] > highs[i + j] for j in range(1, window + 1)):
            peaks.append(i)
        if all(lows[i] < lows[i - j] for j in range(1, window + 1)) and \
           all(lows[i] < lows[i + j] for j in range(1, window + 1)):
            troughs.append(i)

    return peaks, troughs


class ChartPatterns:
    """
    图表形态识别器 (西方技术分析)
    识别基于价格走势的几何形态，如头肩顶/底、双顶/底、三角形等
    """

    @staticmethod
    def identify_all_patterns(df: pd.DataFrame, lookback: int = 60) -> Dict[str, Any]:
        """识别所有图表形态"""
        if df is None or len(df) < lookback:
            return {"patterns_found": False, "patterns": {}}

        df_slice = df.tail(lookback).copy()
        patterns: Dict[str, Any] = {}

        for name, func in [
            ("head_and_shoulders", ChartPatterns._identify_head_and_shoulders),
            ("double_top", ChartPatterns._identify_double_top),
            ("double_bottom", ChartPatterns._identify_double_bottom),
            ("ascending_triangle", ChartPatterns._identify_ascending_triangle),
            ("descending_triangle", ChartPatterns._identify_descending_triangle),
            ("symmetrical_triangle", ChartPatterns._identify_symmetrical_triangle),
            ("flag", ChartPatterns._identify_flag),
            ("wedge", ChartPatterns._identify_wedge),
            ("rounding_top", ChartPatterns._identify_rounding_top),
            ("rounding_bottom", ChartPatterns._identify_rounding_bottom),
            ("rectangle", ChartPatterns._identify_rectangle),
        ]:
            try:
                result = func(df_slice)
                if result.get("detected"):
                    patterns[name] = result
            except (ValueError, TypeError, KeyError, IndexError):
                continue

        return {
            "patterns_found": bool(patterns),
            "patterns": patterns,
        }

    @staticmethod
    def _find_peaks_and_troughs(df: pd.DataFrame, window: int = PEAK_TROUGH_WINDOW) -> Tuple[List[int], List[int]]:
        return _find_peaks_and_troughs(df, window)

    # =====================================================================
    # 各形态检测方法
    # =====================================================================

    @staticmethod
    def _identify_head_and_shoulders(df: pd.DataFrame) -> Dict[str, Any]:
        """检测头肩顶/底"""
        result: Dict[str, Any] = {"detected": False}
        peaks, troughs = _find_peaks_and_troughs(df)

        # 头肩顶：需要至少3个峰值，中间最高
        if len(peaks) >= 3:
            highs = df["high"].values
            for i in range(len(peaks) - 2):
                left, head, right = peaks[i], peaks[i + 1], peaks[i + 2]
                if highs[head] > highs[left] and highs[head] > highs[right]:
                    shoulder_diff = abs(highs[left] - highs[right]) / highs[head]
                    if shoulder_diff < HEAD_SHOULDERS_TOLERANCE:  # 两肩高度差 < 5%
                        result = {
                            "detected": True,
                            "type": "head_and_shoulders_top",
                            "signal": "bearish",
                            "confidence": round(min(0.9, 0.6 + (1 - shoulder_diff) * 0.3), 2),
                        }
                        break

        # 头肩底（逆向）
        if not result["detected"] and len(troughs) >= 3:
            lows = df["low"].values
            for i in range(len(troughs) - 2):
                left, head, right = troughs[i], troughs[i + 1], troughs[i + 2]
                if lows[head] < lows[left] and lows[head] < lows[right]:
                    shoulder_diff = abs(lows[left] - lows[right]) / abs(lows[head]) if lows[head] != 0 else 1
                    if shoulder_diff < HEAD_SHOULDERS_TOLERANCE:
                        result = {
                            "detected": True,
                            "type": "head_and_shoulders_bottom",
                            "signal": "bullish",
                            "confidence": round(min(0.9, 0.6 + (1 - shoulder_diff) * 0.3), 2),
                        }
                        break
        return result

    @staticmethod
    def _identify_double_extreme(
        df: pd.DataFrame, use_peaks: bool = True
    ) -> Dict[str, Any]:
        """检测双顶或双底（参数化方法）
        
        Args:
            df: 价格数据
            use_peaks: True=检测双顶(peaks/highs/bearish), False=检测双底(troughs/lows/bullish)
        """
        peaks, troughs = _find_peaks_and_troughs(df)
        points = peaks if use_peaks else troughs
        values = df["high"].values if use_peaks else df["low"].values
        pattern_type = "double_top" if use_peaks else "double_bottom"
        signal = "bearish" if use_peaks else "bullish"

        if len(points) >= 2:
            p1, p2 = points[-2], points[-1]
            divisor = max(abs(values[p1]), abs(values[p2])) if not use_peaks else max(values[p1], values[p2])
            if divisor == 0:
                divisor = 1
            diff = abs(values[p1] - values[p2]) / divisor
            if diff < DOUBLE_TOP_BOTTOM_TOLERANCE:
                return {
                    "detected": True,
                    "type": pattern_type,
                    "signal": signal,
                    "confidence": round(min(0.85, 0.5 + (1 - diff) * 0.35), 2),
                }
        return {"detected": False}

    @staticmethod
    def _identify_double_top(df: pd.DataFrame) -> Dict[str, Any]:
        """检测双顶"""
        return ChartPatterns._identify_double_extreme(df, use_peaks=True)

    @staticmethod
    def _identify_double_bottom(df: pd.DataFrame) -> Dict[str, Any]:
        """检测双底"""
        return ChartPatterns._identify_double_extreme(df, use_peaks=False)

    @staticmethod
    def _identify_ascending_triangle(df: pd.DataFrame) -> Dict[str, Any]:
        """检测上升三角形：水平阻力线 + 上升支撑线"""
        peaks, troughs = _find_peaks_and_troughs(df)
        if len(peaks) >= 2 and len(troughs) >= 2:
            highs = df["high"].values
            lows = df["low"].values
            resistance_flat = abs(highs[peaks[-1]] - highs[peaks[-2]]) / highs[peaks[-1]] < TRIANGLE_FLAT_TOLERANCE
            support_rising = lows[troughs[-1]] > lows[troughs[-2]]
            if resistance_flat and support_rising:
                return {"detected": True, "type": "ascending_triangle", "signal": "bullish", "confidence": 0.65}
        return {"detected": False}

    @staticmethod
    def _identify_descending_triangle(df: pd.DataFrame) -> Dict[str, Any]:
        """检测下降三角形：水平支撑线 + 下降阻力线"""
        peaks, troughs = _find_peaks_and_troughs(df)
        if len(peaks) >= 2 and len(troughs) >= 2:
            highs = df["high"].values
            lows = df["low"].values
            support_flat = abs(lows[troughs[-1]] - lows[troughs[-2]]) / max(abs(lows[troughs[-1]]), 1e-9) < TRIANGLE_FLAT_TOLERANCE
            resistance_falling = highs[peaks[-1]] < highs[peaks[-2]]
            if support_flat and resistance_falling:
                return {"detected": True, "type": "descending_triangle", "signal": "bearish", "confidence": 0.65}
        return {"detected": False}

    @staticmethod
    def _identify_symmetrical_triangle(df: pd.DataFrame) -> Dict[str, Any]:
        """检测对称三角形：阻力下降 + 支撑上升"""
        peaks, troughs = _find_peaks_and_troughs(df)
        if len(peaks) >= 2 and len(troughs) >= 2:
            highs = df["high"].values
            lows = df["low"].values
            resistance_falling = highs[peaks[-1]] < highs[peaks[-2]]
            support_rising = lows[troughs[-1]] > lows[troughs[-2]]
            if resistance_falling and support_rising:
                return {"detected": True, "type": "symmetrical_triangle", "signal": "neutral", "confidence": 0.55}
        return {"detected": False}

    @staticmethod
    def _identify_flag(df: pd.DataFrame) -> Dict[str, Any]:
        """检测旗形：强趋势后的平行通道整理"""
        closes = df["close"].values
        if len(closes) < 20:
            return {"detected": False}

        # 前半段趋势
        half = len(closes) // 2
        trend_pct = (closes[half] - closes[0]) / closes[0] if closes[0] != 0 else 0

        # 后半段振幅
        flag_range = (max(closes[half:]) - min(closes[half:])) / closes[half] if closes[half] != 0 else 1

        if abs(trend_pct) > FLAG_TREND_THRESHOLD and flag_range < FLAG_RANGE_THRESHOLD:
            signal = "bullish" if trend_pct > 0 else "bearish"
            return {"detected": True, "type": "flag", "signal": signal, "confidence": 0.60}
        return {"detected": False}

    @staticmethod
    def _identify_wedge(df: pd.DataFrame) -> Dict[str, Any]:
        """检测楔形：收敛趋势线（均向上或均向下）"""
        peaks, troughs = _find_peaks_and_troughs(df)
        if len(peaks) >= 2 and len(troughs) >= 2:
            highs = df["high"].values
            lows = df["low"].values
            resistance_rising = highs[peaks[-1]] > highs[peaks[-2]]
            support_rising = lows[troughs[-1]] > lows[troughs[-2]]
            resistance_falling = highs[peaks[-1]] < highs[peaks[-2]]
            support_falling = lows[troughs[-1]] < lows[troughs[-2]]

            if resistance_rising and support_rising:
                return {"detected": True, "type": "rising_wedge", "signal": "bearish", "confidence": 0.60}
            if resistance_falling and support_falling:
                return {"detected": True, "type": "falling_wedge", "signal": "bullish", "confidence": 0.60}
        return {"detected": False}

    @staticmethod
    def _identify_rounding(df: pd.DataFrame, is_top: bool = True) -> Dict[str, Any]:
        """检测圆弧顶或圆弧底（参数化方法）
        
        Args:
            df: 价格数据
            is_top: True=圆弧顶(先升后降/bearish), False=圆弧底(先降后升/bullish)
        """
        closes = df["close"].values
        if len(closes) < 20:
            return {"detected": False}

        mid = len(closes) // 2
        first_half_slope = (closes[mid] - closes[0]) / max(mid, 1)
        second_half_slope = (closes[-1] - closes[mid]) / max(len(closes) - mid, 1)

        if is_top and first_half_slope > 0 and second_half_slope < 0:
            return {"detected": True, "type": "rounding_top", "signal": "bearish", "confidence": 0.55}
        if not is_top and first_half_slope < 0 and second_half_slope > 0:
            return {"detected": True, "type": "rounding_bottom", "signal": "bullish", "confidence": 0.55}
        return {"detected": False}

    @staticmethod
    def _identify_rounding_top(df: pd.DataFrame) -> Dict[str, Any]:
        """检测圆弧顶"""
        return ChartPatterns._identify_rounding(df, is_top=True)

    @staticmethod
    def _identify_rounding_bottom(df: pd.DataFrame) -> Dict[str, Any]:
        """检测圆弧底"""
        return ChartPatterns._identify_rounding(df, is_top=False)

    @staticmethod
    def _identify_rectangle(df: pd.DataFrame) -> Dict[str, Any]:
        """检测矩形整理：水平阻力 + 水平支撑"""
        peaks, troughs = _find_peaks_and_troughs(df)
        if len(peaks) >= 2 and len(troughs) >= 2:
            highs = df["high"].values
            lows = df["low"].values
            resistance_flat = abs(highs[peaks[-1]] - highs[peaks[-2]]) / max(highs[peaks[-1]], 1e-9) < 0.02
            support_flat = abs(lows[troughs[-1]] - lows[troughs[-2]]) / max(abs(lows[troughs[-1]]), 1e-9) < 0.02
            if resistance_flat and support_flat:
                return {"detected": True, "type": "rectangle", "signal": "neutral", "confidence": 0.50}
        return {"detected": False}
