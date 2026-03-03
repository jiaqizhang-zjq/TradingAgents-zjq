#!/usr/bin/env python3
"""图表形态识别模块
包含头肩顶/底、双顶/底、三角形等西方技术分析形态
"""

import numpy as np
import pandas as pd
from typing import Dict, Any


class ChartPatterns:
    """
    图表形态识别器 (西方技术分析)
    识别基于价格走势的几何形态，如头肩顶/底、双顶/底、三角形等
    """
    
    @staticmethod
    def identify_all_patterns(df: pd.DataFrame, lookback: int = 60) -> Dict[str, Any]:
        """
        识别所有图表形态
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame
            lookback: 回溯周期，默认60天
            
        Returns:
            包含所有识别出的形态信息的字典
        """
        if len(df) < lookback:
            lookback = len(df)
        
        recent_df = df.tail(lookback).copy()
        
        patterns = {
            "head_and_shoulders": ChartPatterns._identify_head_and_shoulders(recent_df),
            "double_top": ChartPatterns._identify_double_top(recent_df),
            "double_bottom": ChartPatterns._identify_double_bottom(recent_df),
            "ascending_triangle": ChartPatterns._identify_ascending_triangle(recent_df),
            "descending_triangle": ChartPatterns._identify_descending_triangle(recent_df),
            "symmetrical_triangle": ChartPatterns._identify_symmetrical_triangle(recent_df),
            "flag": ChartPatterns._identify_flag(recent_df),
            "wedge": ChartPatterns._identify_wedge(recent_df),
            "rounding_top": ChartPatterns._identify_rounding_top(recent_df),
            "rounding_bottom": ChartPatterns._identify_rounding_bottom(recent_df),
            "rectangle": ChartPatterns._identify_rectangle(recent_df),
        }
        
        return patterns
    
    @staticmethod
    def _find_peaks_and_troughs(df: pd.DataFrame, window: int = 5) -> tuple:
        """
        找出价格的峰值和谷值
        
        Args:
            df: DataFrame with 'high' and 'low' columns
            window: 窗口大小用于确认峰值/谷值
            
        Returns:
            (peaks, troughs) - 峰值和谷值的索引列表
        """
        highs = df['high'].values
        lows = df['low'].values
        
        peaks = []
        troughs = []
        
        for i in range(window, len(df) - window):
            # 峰值：比前后window个数据点都高
            if all(highs[i] > highs[i-j] for j in range(1, window+1)) and \
               all(highs[i] > highs[i+j] for j in range(1, window+1)):
                peaks.append(i)
            
            # 谷值：比前后window个数据点都低
            if all(lows[i] < lows[i-j] for j in range(1, window+1)) and \
               all(lows[i] < lows[i+j] for j in range(1, window+1)):
                troughs.append(i)
        
        return peaks, troughs
    
    @staticmethod
    def _identify_head_and_shoulders(df: pd.DataFrame) -> Dict[str, Any]:
        """识别头肩顶/底形态"""
        peaks, troughs = ChartPatterns._find_peaks_and_troughs(df)
        
        if len(peaks) < 3:
            return {"detected": False, "type": None, "confidence": 0}
        
        # 计算平均成交量用于比较
        avg_volume = df['volume'].mean()
        
        # 检查头肩顶 (三个峰值，中间最高)
        avg_volume = df['volume'].mean()
        
        for i in range(len(peaks) - 2):
            left_shoulder = df.iloc[peaks[i]]['high']
            head = df.iloc[peaks[i+1]]['high']
            right_shoulder = df.iloc[peaks[i+2]]['high']
            
            # 头肩顶条件：中间峰值最高，左右肩大致相等
            if (head > left_shoulder and head > right_shoulder and
                abs(left_shoulder - right_shoulder) / head < 0.05):  # 5%容差
                
                # 计算颈线
                left_trough_idx = [t for t in troughs if peaks[i] < t < peaks[i+1]]
                right_trough_idx = [t for t in troughs if peaks[i+1] < t < peaks[i+2]]
                
                if left_trough_idx and right_trough_idx:
                    neckline = (df.iloc[left_trough_idx[0]]['low'] + 
                               df.iloc[right_trough_idx[0]]['low']) / 2
                    
                    # 成交量验证：头部成交量应小于左肩，右肩成交量应更小
                    left_shoulder_vol = df.iloc[peaks[i]]['volume']
                    head_vol = df.iloc[peaks[i+1]]['volume']
                    right_shoulder_vol = df.iloc[peaks[i+2]]['volume']
                    
                    volume_confirmed = head_vol < left_shoulder_vol * 0.8 and right_shoulder_vol < head_vol * 0.8
                    
                    # 突破验证：价格应跌破颈线
                    breakout_confirmed = df['close'].iloc[-1] < neckline * 0.995
                    
                    confidence = 0.75
                    if volume_confirmed:
                        confidence += 0.10
                    if breakout_confirmed:
                        confidence += 0.10
                    
                    return {
                        "detected": True,
                        "type": "HEAD_AND_SHOULDERS_TOP",
                        "confidence": min(confidence, 0.95),
                        "head_price": head,
                        "shoulder_prices": [left_shoulder, right_shoulder],
                        "neckline": neckline,
                        "target_price": neckline - (head - neckline),
                        "volume_confirmed": volume_confirmed,
                        "breakout_confirmed": breakout_confirmed,
                        "volume_analysis": f"左肩成交量: {left_shoulder_vol:.0f}, 头部成交量: {head_vol:.0f}, 右肩成交量: {right_shoulder_vol:.0f}, 平均: {avg_volume:.0f}",
                        "description": "头肩顶形态，看跌信号" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                    }
        
        # 检查头肩底 (三个谷值，中间最低)
        if len(troughs) >= 3:
            for i in range(len(troughs) - 2):
                left_shoulder = df.iloc[troughs[i]]['low']
                head = df.iloc[troughs[i+1]]['low']
                right_shoulder = df.iloc[troughs[i+2]]['low']
                
                if (head < left_shoulder and head < right_shoulder and
                    abs(left_shoulder - right_shoulder) / head < 0.05):
                    
                    left_peak_idx = [p for p in peaks if troughs[i] < p < troughs[i+1]]
                    right_peak_idx = [p for p in peaks if troughs[i+1] < p < troughs[i+2]]
                    
                    if left_peak_idx and right_peak_idx:
                        neckline = (df.iloc[left_peak_idx[0]]['high'] + 
                                   df.iloc[right_peak_idx[0]]['high']) / 2
                        
                        # 成交量验证：头部成交量应大于左肩（恐慌性抛盘）
                        left_shoulder_vol = df.iloc[troughs[i]]['volume']
                        head_vol = df.iloc[troughs[i+1]]['volume']
                        right_shoulder_vol = df.iloc[troughs[i+2]]['volume']
                        
                        volume_confirmed = head_vol > left_shoulder_vol * 1.3  # 头部放量30%以上
                        
                        # 突破验证：价格应突破颈线
                        breakout_confirmed = df['close'].iloc[-1] > neckline * 1.005
                        
                        confidence = 0.75
                        if volume_confirmed:
                            confidence += 0.10
                        if breakout_confirmed:
                            confidence += 0.10
                        
                        return {
                            "detected": True,
                            "type": "HEAD_AND_SHOULDERS_BOTTOM",
                            "confidence": min(confidence, 0.95),
                            "head_price": head,
                            "shoulder_prices": [left_shoulder, right_shoulder],
                            "neckline": neckline,
                            "target_price": neckline + (neckline - head),
                            "volume_confirmed": volume_confirmed,
                            "breakout_confirmed": breakout_confirmed,
                            "volume_analysis": f"左肩成交量: {left_shoulder_vol:.0f}, 头部成交量: {head_vol:.0f}, 右肩成交量: {right_shoulder_vol:.0f}, 平均: {avg_volume:.0f}",
                            "description": "头肩底形态，看涨信号" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                        }
        
        return {"detected": False, "type": None, "confidence": 0}
    
    @staticmethod
    def _identify_double_top(df: pd.DataFrame) -> Dict[str, Any]:
        """识别双顶形态 (M顶)"""
        peaks, _ = ChartPatterns._find_peaks_and_troughs(df)
        
        avg_volume = df['volume'].mean()
        
        if len(peaks) < 2:
            return {"detected": False, "type": None, "confidence": 0}
        
        for i in range(len(peaks) - 1):
            first_peak = df.iloc[peaks[i]]['high']
            second_peak = df.iloc[peaks[i+1]]['high']
            
            # 两个峰值相近 (5%容差)
            if abs(first_peak - second_peak) / first_peak < 0.05:
                # 中间有回调
                trough_between = df.iloc[peaks[i]:peaks[i+1]]['low'].min()
                
                if trough_between < first_peak * 0.95:  # 至少回调5%
                    # 成交量验证：第二个峰成交量应小于第一个峰
                    first_peak_vol = df.iloc[peaks[i]]['volume']
                    second_peak_vol = df.iloc[peaks[i+1]]['volume']
                    
                    volume_confirmed = second_peak_vol < first_peak_vol * 0.85  # 第二个峰放量小于第一个峰15%以上
                    
                    # 突破验证：价格跌破颈线
                    neckline = trough_between
                    breakout_confirmed = df['close'].iloc[-1] < neckline * 0.995
                    
                    confidence = 0.70
                    if volume_confirmed:
                        confidence += 0.10
                    if breakout_confirmed:
                        confidence += 0.10
                    
                    return {
                        "detected": True,
                        "type": "DOUBLE_TOP",
                        "confidence": min(confidence, 0.95),
                        "peak_prices": [first_peak, second_peak],
                        "trough_between": trough_between,
                        "target_price": trough_between - (first_peak - trough_between),
                        "volume_confirmed": volume_confirmed,
                        "breakout_confirmed": breakout_confirmed,
                        "volume_analysis": f"第一峰成交量: {first_peak_vol:.0f}, 第二峰成交量: {second_peak_vol:.0f}, 平均: {avg_volume:.0f}",
                        "description": "双顶形态(M顶)，看跌反转信号" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                    }
        
        return {"detected": False, "type": None, "confidence": 0}
    
    @staticmethod
    def _identify_double_bottom(df: pd.DataFrame) -> Dict[str, Any]:
        """识别双底形态 (W底)"""
        _, troughs = ChartPatterns._find_peaks_and_troughs(df)
        
        if len(troughs) < 2:
            return {"detected": False, "type": None, "confidence": 0}
        
        avg_volume = df['volume'].mean()
        
        for i in range(len(troughs) - 1):
            first_trough = df.iloc[troughs[i]]['low']
            second_trough = df.iloc[troughs[i+1]]['low']
            
            # 两个谷值相近 (5%容差)
            if abs(first_trough - second_trough) / first_trough < 0.05:
                # 中间有反弹
                peak_between = df.iloc[troughs[i]:troughs[i+1]]['high'].max()
                
                if peak_between > first_trough * 1.05:  # 至少反弹5%
                    # 成交量验证：第二个底成交量应大于第一个底（恐慌性抛盘后萎缩）
                    first_trough_vol = df.iloc[troughs[i]]['volume']
                    second_trough_vol = df.iloc[troughs[i+1]]['volume']
                    
                    volume_confirmed = second_trough_vol < first_trough_vol * 0.85  # 第二个底成交量小于第一个底15%以上
                    
                    # 突破验证：价格突破颈线
                    neckline = peak_between
                    breakout_confirmed = df['close'].iloc[-1] > neckline * 1.005
                    
                    confidence = 0.70
                    if volume_confirmed:
                        confidence += 0.10
                    if breakout_confirmed:
                        confidence += 0.10
                    
                    return {
                        "detected": True,
                        "type": "DOUBLE_BOTTOM",
                        "confidence": min(confidence, 0.95),
                        "trough_prices": [first_trough, second_trough],
                        "peak_between": peak_between,
                        "target_price": peak_between + (peak_between - first_trough),
                        "volume_confirmed": volume_confirmed,
                        "breakout_confirmed": breakout_confirmed,
                        "volume_analysis": f"第一底成交量: {first_trough_vol:.0f}, 第二底成交量: {second_trough_vol:.0f}, 平均: {avg_volume:.0f}",
                        "description": "双底形态(W底)，看涨反转信号" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                    }
        
        return {"detected": False, "type": None, "confidence": 0}
    
    @staticmethod
    def _identify_ascending_triangle(df: pd.DataFrame) -> Dict[str, Any]:
        """识别上升三角形"""
        peaks, troughs = ChartPatterns._find_peaks_and_troughs(df, window=3)
        
        if len(peaks) < 2 or len(troughs) < 2:
            return {"detected": False, "type": None, "confidence": 0}
        
        avg_volume = df['volume'].mean()
        
        # 检查最近的高点是否大致相同（水平阻力线）
        recent_peaks = [df.iloc[p]['high'] for p in peaks[-3:]]
        recent_troughs = [df.iloc[t]['low'] for t in troughs[-3:]]
        
        # 高点水平，低点上升
        high_variance = max(recent_peaks) - min(recent_peaks)
        avg_high = sum(recent_peaks) / len(recent_peaks)
        
        if high_variance / avg_high < 0.03:  # 高点变化小于3%
            # 检查低点是否上升
            if len(recent_troughs) >= 2 and recent_troughs[-1] > recent_troughs[0]:
                # 成交量验证：整理期间成交量应递减，突破时放量
                
                # 简单验证：最近成交量低于平均
                recent_vol = df['volume'].iloc[-5:].mean()
                volume_confirmed = recent_vol < avg_volume * 0.9  # 整理期成交量萎缩
                
                # 突破验证：价格接近或突破阻力线
                breakout_confirmed = df['close'].iloc[-1] > avg_high * 0.995
                
                confidence = 0.65
                if volume_confirmed:
                    confidence += 0.10
                if breakout_confirmed:
                    confidence += 0.10
                
                return {
                    "detected": True,
                    "type": "ASCENDING_TRIANGLE",
                    "confidence": min(confidence, 0.95),
                    "resistance_level": avg_high,
                    "trend_line_start": recent_troughs[0],
                    "trend_line_end": recent_troughs[-1],
                    "target_price": avg_high + (avg_high - recent_troughs[0]),
                    "volume_confirmed": volume_confirmed,
                    "breakout_confirmed": breakout_confirmed,
                    "volume_analysis": f"最近5日平均成交量: {recent_vol:.0f}, 总体平均: {avg_volume:.0f}",
                    "description": "上升三角形，看涨持续形态" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                }
        
        return {"detected": False, "type": None, "confidence": 0}
    
    @staticmethod
    def _identify_descending_triangle(df: pd.DataFrame) -> Dict[str, Any]:
        """识别下降三角形"""
        peaks, troughs = ChartPatterns._find_peaks_and_troughs(df, window=3)
        
        if len(peaks) < 2 or len(troughs) < 2:
            return {"detected": False, "type": None, "confidence": 0}
        
        avg_volume = df['volume'].mean()
        
        recent_peaks = [df.iloc[p]['high'] for p in peaks[-3:]]
        recent_troughs = [df.iloc[t]['low'] for t in troughs[-3:]]
        
        # 低点水平，高点下降
        low_variance = max(recent_troughs) - min(recent_troughs)
        avg_low = sum(recent_troughs) / len(recent_troughs)
        
        if low_variance / avg_low < 0.03:  # 低点变化小于3%
            # 检查高点是否下降
            if len(recent_peaks) >= 2 and recent_peaks[-1] < recent_peaks[0]:
                # 成交量验证：整理期间成交量递减，突破时放量
                recent_vol = df['volume'].iloc[-5:].mean()
                volume_confirmed = recent_vol < avg_volume * 0.9
                
                # 突破验证：价格跌破支撑线
                breakout_confirmed = df['close'].iloc[-1] < avg_low * 0.995
                
                confidence = 0.65
                if volume_confirmed:
                    confidence += 0.10
                if breakout_confirmed:
                    confidence += 0.10
                
                return {
                    "detected": True,
                    "type": "DESCENDING_TRIANGLE",
                    "confidence": min(confidence, 0.95),
                    "support_level": avg_low,
                    "trend_line_start": recent_peaks[0],
                    "trend_line_end": recent_peaks[-1],
                    "target_price": avg_low - (recent_peaks[0] - avg_low),
                    "volume_confirmed": volume_confirmed,
                    "breakout_confirmed": breakout_confirmed,
                    "volume_analysis": f"最近5日平均成交量: {recent_vol:.0f}, 总体平均: {avg_volume:.0f}",
                    "description": "下降三角形，看跌持续形态" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                }
        
        return {"detected": False, "type": None, "confidence": 0}
    
    @staticmethod
    def _identify_symmetrical_triangle(df: pd.DataFrame) -> Dict[str, Any]:
        """识别对称三角形"""
        peaks, troughs = ChartPatterns._find_peaks_and_troughs(df, window=3)
        
        if len(peaks) < 3 or len(troughs) < 3:
            return {"detected": False, "type": None, "confidence": 0}
        
        avg_volume = df['volume'].mean()
        
        recent_peaks = [df.iloc[p]['high'] for p in peaks[-4:]]
        recent_troughs = [df.iloc[t]['low'] for t in troughs[-4:]]
        
        # 高点下降，低点上升
        if (len(recent_peaks) >= 3 and len(recent_troughs) >= 3 and
            recent_peaks[-1] < recent_peaks[0] and
            recent_troughs[-1] > recent_troughs[0]):
            
            # 计算收敛程度
            high_slope = (recent_peaks[-1] - recent_peaks[0]) / len(recent_peaks)
            low_slope = (recent_troughs[-1] - recent_troughs[0]) / len(recent_troughs)
            
            # 高点下降，低点上升（斜率相反）
            if high_slope < 0 and low_slope > 0:
                apex = (recent_peaks[-1] + recent_troughs[-1]) / 2
                
                # 成交量验证：整理期间成交量递减
                recent_vol = df['volume'].iloc[-5:].mean()
                volume_confirmed = recent_vol < avg_volume * 0.9
                
                # 突破验证：价格接近上沿或下沿
                current_close = df['close'].iloc[-1]
                breakout_up = current_close > recent_peaks[-1] * 0.995
                breakout_down = current_close < recent_troughs[-1] * 1.005
                breakout_confirmed = breakout_up or breakout_down
                
                confidence = 0.60
                if volume_confirmed:
                    confidence += 0.10
                if breakout_confirmed:
                    confidence += 0.10
                
                return {
                    "detected": True,
                    "type": "SYMMETRICAL_TRIANGLE",
                    "confidence": min(confidence, 0.95),
                    "upper_trendline": recent_peaks,
                    "lower_trendline": recent_troughs,
                    "apex_price": apex,
                    "volume_confirmed": volume_confirmed,
                    "breakout_confirmed": breakout_confirmed,
                    "breakout_direction": "up" if breakout_up else "down" if breakout_down else None,
                    "volume_analysis": f"最近5日平均成交量: {recent_vol:.0f}, 总体平均: {avg_volume:.0f}",
                    "description": "对称三角形，中性整理形态，突破方向决定趋势" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                }
        
        return {"detected": False, "type": None, "confidence": 0}
    
    @staticmethod
    def _identify_flag(df: pd.DataFrame) -> Dict[str, Any]:
        """识别旗形/旗杆形态"""
        if len(df) < 20:
            return {"detected": False, "type": None, "confidence": 0}
        
        avg_volume = df['volume'].mean()
        
        # 检查是否有急剧的价格变动（旗杆）
        price_change_5d = (df['close'].iloc[-5] - df['close'].iloc[-20]) / df['close'].iloc[-20]
        
        if abs(price_change_5d) > 0.15:  # 15%以上的变动
            # 检查随后的整理（旗形）
            recent_range = (df['high'].iloc[-5:].max() - df['low'].iloc[-5:].min()) / df['close'].iloc[-5]
            
            if recent_range < 0.05:  # 整理区间小于5%
                direction = "BULL_FLAG" if price_change_5d > 0 else "BEAR_FLAG"
                
                # 成交量验证：旗杆期间放量，整理期间萎缩
                pole_vol = df['volume'].iloc[-20:-5].mean()
                flag_vol = df['volume'].iloc[-5:].mean()
                volume_confirmed = pole_vol > avg_volume * 1.2 and flag_vol < avg_volume * 0.8
                
                # 突破验证：价格突破整理区间
                current_close = df['close'].iloc[-1]
                recent_high = df['high'].iloc[-5:].max()
                recent_low = df['low'].iloc[-5:].min()
                breakout_confirmed = (direction == "BULL_FLAG" and current_close > recent_high * 1.005) or \
                                    (direction == "BEAR_FLAG" and current_close < recent_low * 0.995)
                
                confidence = 0.60
                if volume_confirmed:
                    confidence += 0.10
                if breakout_confirmed:
                    confidence += 0.10
                
                return {
                    "detected": True,
                    "type": direction,
                    "confidence": min(confidence, 0.95),
                    "pole_height": abs(price_change_5d),
                    "consolidation_range": recent_range,
                    "target_price": (df['close'].iloc[-5:].max() + abs(price_change_5d) * df['close'].iloc[-5]) 
                                    if direction == "BULL_FLAG" else
                                    (df['close'].iloc[-5:].min() - abs(price_change_5d) * df['close'].iloc[-5]),
                    "volume_confirmed": volume_confirmed,
                    "breakout_confirmed": breakout_confirmed,
                    "volume_analysis": f"旗杆期平均成交量: {pole_vol:.0f}, 旗形期平均成交量: {flag_vol:.0f}, 总体平均: {avg_volume:.0f}",
                    "description": f"{'看涨' if direction == 'BULL_FLAG' else '看跌'}旗形，持续形态" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                }
        
        return {"detected": False, "type": None, "confidence": 0}
    
    @staticmethod
    def _identify_wedge(df: pd.DataFrame) -> Dict[str, Any]:
        """识别楔形形态"""
        peaks, troughs = ChartPatterns._find_peaks_and_troughs(df, window=3)
        
        if len(peaks) < 3 or len(troughs) < 3:
            return {"detected": False, "type": None, "confidence": 0}
        
        avg_volume = df['volume'].mean()
        
        recent_peaks = [df.iloc[p]['high'] for p in peaks[-4:]]
        recent_troughs = [df.iloc[t]['low'] for t in troughs[-4:]]
        
        # 上升楔形：高点和低点都上升，但高点斜率小于低点斜率
        if (recent_peaks[-1] > recent_peaks[0] and recent_troughs[-1] > recent_troughs[0]):
            high_slope = (recent_peaks[-1] - recent_peaks[0]) / len(recent_peaks)
            low_slope = (recent_troughs[-1] - recent_troughs[0]) / len(recent_troughs)
            
            if high_slope < low_slope:  # 收敛
                # 成交量验证：上升楔形通常伴随着成交量递减
                recent_vol = df['volume'].iloc[-5:].mean()
                volume_confirmed = recent_vol < avg_volume * 0.9
                
                # 突破验证：价格跌破下轨
                breakout_confirmed = df['close'].iloc[-1] < recent_troughs[-1] * 0.995
                
                confidence = 0.60
                if volume_confirmed:
                    confidence += 0.10
                if breakout_confirmed:
                    confidence += 0.10
                
                return {
                    "detected": True,
                    "type": "RISING_WEDGE",
                    "confidence": min(confidence, 0.95),
                    "upper_trendline": recent_peaks,
                    "lower_trendline": recent_troughs,
                    "volume_confirmed": volume_confirmed,
                    "breakout_confirmed": breakout_confirmed,
                    "volume_analysis": f"最近5日平均成交量: {recent_vol:.0f}, 总体平均: {avg_volume:.0f}",
                    "description": "上升楔形，看跌反转形态" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                }
        
        # 下降楔形：高点和低点都下降，但高点斜率小于低点斜率（更平缓）
        if (recent_peaks[-1] < recent_peaks[0] and recent_troughs[-1] < recent_troughs[0]):
            high_slope = (recent_peaks[-1] - recent_peaks[0]) / len(recent_peaks)
            low_slope = (recent_troughs[-1] - recent_troughs[0]) / len(recent_troughs)
            
            if abs(high_slope) < abs(low_slope):  # 收敛
                # 成交量验证：下降楔形通常伴随着成交量递减
                recent_vol = df['volume'].iloc[-5:].mean()
                volume_confirmed = recent_vol < avg_volume * 0.9
                
                # 突破验证：价格突破上轨
                breakout_confirmed = df['close'].iloc[-1] > recent_peaks[-1] * 1.005
                
                confidence = 0.60
                if volume_confirmed:
                    confidence += 0.10
                if breakout_confirmed:
                    confidence += 0.10
                
                return {
                    "detected": True,
                    "type": "FALLING_WEDGE",
                    "confidence": min(confidence, 0.95),
                    "upper_trendline": recent_peaks,
                    "lower_trendline": recent_troughs,
                    "volume_confirmed": volume_confirmed,
                    "breakout_confirmed": breakout_confirmed,
                    "volume_analysis": f"最近5日平均成交量: {recent_vol:.0f}, 总体平均: {avg_volume:.0f}",
                    "description": "下降楔形，看涨反转形态" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                }
        
        return {"detected": False, "type": None, "confidence": 0}
    
    @staticmethod
    def _identify_rounding_top(df: pd.DataFrame) -> Dict[str, Any]:
        """识别圆形顶"""
        if len(df) < 30:
            return {"detected": False, "type": None, "confidence": 0}
        
        avg_volume = df['volume'].mean()
        
        # 检查价格是否呈现弧形顶部
        highs = df['high'].values[-30:]
        mid = len(highs) // 2
        
        # 中间高，两边低，形成弧形
        if (highs[mid] > highs[0] and highs[mid] > highs[-1] and
            highs[mid-5:mid+5].mean() > highs[:5].mean() and
            highs[mid-5:mid+5].mean() > highs[-5:].mean()):
            
            # 检查是否平滑（没有尖锐的峰）
            if np.std(highs[mid-5:mid+5]) < np.std(highs[:5]) * 0.5:
                # 成交量验证：左侧上升时放量，右侧下跌时缩量
                left_vol = df['volume'].iloc[-30:-15].mean()
                right_vol = df['volume'].iloc[-15:].mean()
                volume_confirmed = left_vol > avg_volume * 1.1 and right_vol < avg_volume * 0.9
                
                # 突破验证：价格跌破颈线（左侧起点）
                neckline = df['close'].iloc[-30]
                breakout_confirmed = df['close'].iloc[-1] < neckline * 0.995
                
                confidence = 0.55
                if volume_confirmed:
                    confidence += 0.10
                if breakout_confirmed:
                    confidence += 0.10
                
                return {
                    "detected": True,
                    "type": "ROUNDING_TOP",
                    "confidence": min(confidence, 0.95),
                    "top_price": highs[mid],
                    "start_price": highs[0],
                    "end_price": highs[-1],
                    "volume_confirmed": volume_confirmed,
                    "breakout_confirmed": breakout_confirmed,
                    "volume_analysis": f"左侧平均成交量: {left_vol:.0f}, 右侧平均成交量: {right_vol:.0f}, 总体平均: {avg_volume:.0f}",
                    "description": "圆形顶，看跌反转形态" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                }
        
        return {"detected": False, "type": None, "confidence": 0}
    
    @staticmethod
    def _identify_rounding_bottom(df: pd.DataFrame) -> Dict[str, Any]:
        """识别圆形底"""
        if len(df) < 30:
            return {"detected": False, "type": None, "confidence": 0}
        
        avg_volume = df['volume'].mean()
        
        # 检查价格是否呈现弧形底部
        lows = df['low'].values[-30:]
        mid = len(lows) // 2
        
        # 中间低，两边高，形成弧形
        if (lows[mid] < lows[0] and lows[mid] < lows[-1] and
            lows[mid-5:mid+5].mean() < lows[:5].mean() and
            lows[mid-5:mid+5].mean() < lows[-5:].mean()):
            
            # 检查是否平滑
            if np.std(lows[mid-5:mid+5]) < np.std(lows[:5]) * 0.5:
                # 成交量验证：左侧下跌时缩量，右侧上升时放量
                left_vol = df['volume'].iloc[-30:-15].mean()
                right_vol = df['volume'].iloc[-15:].mean()
                volume_confirmed = right_vol > left_vol * 1.3  # 右侧放量30%以上
                
                # 突破验证：价格突破颈线（左侧起点）
                neckline = df['close'].iloc[-30]
                breakout_confirmed = df['close'].iloc[-1] > neckline * 1.005
                
                confidence = 0.55
                if volume_confirmed:
                    confidence += 0.10
                if breakout_confirmed:
                    confidence += 0.10
                
                return {
                    "detected": True,
                    "type": "ROUNDING_BOTTOM",
                    "confidence": min(confidence, 0.95),
                    "bottom_price": lows[mid],
                    "start_price": lows[0],
                    "end_price": lows[-1],
                    "volume_confirmed": volume_confirmed,
                    "breakout_confirmed": breakout_confirmed,
                    "volume_analysis": f"左侧平均成交量: {left_vol:.0f}, 右侧平均成交量: {right_vol:.0f}, 总体平均: {avg_volume:.0f}",
                    "description": "圆形底，看涨反转形态" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                }
        
        return {"detected": False, "type": None, "confidence": 0}
    
    @staticmethod
    def _identify_rectangle(df: pd.DataFrame) -> Dict[str, Any]:
        """识别矩形整理形态"""
        if len(df) < 20:
            return {"detected": False, "type": None, "confidence": 0}
        
        avg_volume = df['volume'].mean()
        recent_df = df.tail(20)
        
        # 检查是否在一定区间内震荡
        high_range = recent_df['high'].max() - recent_df['high'].min()
        low_range = recent_df['low'].max() - recent_df['low'].min()
        avg_price = recent_df['close'].mean()
        
        # 高点和低点都在较窄的区间内
        if high_range / avg_price < 0.05 and low_range / avg_price < 0.05:
            resistance = recent_df['high'].max()
            support = recent_df['low'].min()
            
            # 检查是否有多次触及上下边界
            high_touches = sum(1 for h in recent_df['high'] if h > resistance * 0.98)
            low_touches = sum(1 for l in recent_df['low'] if l < support * 1.02)
            
            if high_touches >= 2 and low_touches >= 2:
                # 成交量验证：整理期间成交量应递减
                recent_vol = df['volume'].iloc[-5:].mean()
                volume_confirmed = recent_vol < avg_volume * 0.9
                
                # 突破验证：价格接近或突破上沿或下沿
                current_close = df['close'].iloc[-1]
                breakout_up = current_close > resistance * 0.995
                breakout_down = current_close < support * 1.005
                breakout_confirmed = breakout_up or breakout_down
                
                confidence = 0.60
                if volume_confirmed:
                    confidence += 0.10
                if breakout_confirmed:
                    confidence += 0.10
                
                return {
                    "detected": True,
                    "type": "RECTANGLE",
                    "confidence": min(confidence, 0.95),
                    "resistance": resistance,
                    "support": support,
                    "range_height": resistance - support,
                    "volume_confirmed": volume_confirmed,
                    "breakout_confirmed": breakout_confirmed,
                    "breakout_direction": "up" if breakout_up else "down" if breakout_down else None,
                    "volume_analysis": f"最近5日平均成交量: {recent_vol:.0f}, 总体平均: {avg_volume:.0f}",
                    "description": "矩形整理形态，突破方向决定趋势" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                }
        
        return {"detected": False, "type": None, "confidence": 0}
    
    @staticmethod
    def format_patterns_for_display(patterns: Dict[str, Any]) -> str:
        """
        将识别的形态格式化为可读的字符串
        
        Args:
            patterns: identify_all_patterns 返回的字典
            
        Returns:
            格式化的形态描述字符串
        """
        detected_patterns = []
        
        for pattern_name, pattern_info in patterns.items():
            if pattern_info.get("detected"):
                detected_patterns.append(pattern_info)
        
        if not detected_patterns:
            return "未识别到明显的图表形态"
        
        # 按置信度排序
        detected_patterns.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        
        result = []
        result.append("## 图表形态识别结果\n")
        
        for i, pattern in enumerate(detected_patterns[:3], 1):  # 只显示前3个
            result.append(f"### {i}. {pattern.get('description', '')}")
            result.append(f"- 形态类型: {pattern.get('type', 'Unknown')}")
            result.append(f"- 置信度: {pattern.get('confidence', 0):.0%}")
            
            if 'target_price' in pattern:
                result.append(f"- 目标价格: ${pattern['target_price']:.2f}")
            if 'neckline' in pattern:
                result.append(f"- 颈线位: ${pattern['neckline']:.2f}")
            if 'resistance_level' in pattern:
                result.append(f"- 阻力位: ${pattern['resistance_level']:.2f}")
            if 'support_level' in pattern:
                result.append(f"- 支撑位: ${pattern['support_level']:.2f}")
            
            result.append("")
        
        return "\n".join(result)
