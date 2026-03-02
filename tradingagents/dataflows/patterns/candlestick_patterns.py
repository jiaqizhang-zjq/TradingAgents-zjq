#!/usr/bin/env python3
"""
蜡烛图形态识别模块
包含常见的单根、两根、三根K线形态识别
"""

import pandas as pd
from typing import Dict, List, Any


class CandlestickPatternRecognizer:
    """蜡烛图形态识别器"""
    
    @staticmethod
    def identify_patterns(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        识别蜡烛图形态
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame
            
        Returns:
            识别到的形态列表
        """
        patterns = []
        avg_volume = df['volume'].mean() if 'volume' in df.columns else 0
        
        for i in range(3, len(df)):
            prev3 = df.iloc[i-3] if i >= 3 else None
            prev2 = df.iloc[i-2]
            prev1 = df.iloc[i-1]
            curr = df.iloc[i]
            
            pattern_info = {
                "timestamp": curr.get("timestamp", curr.get("date", i)),
                "open": curr["open"],
                "high": curr["high"],
                "low": curr["low"],
                "close": curr["close"],
                "volume": curr.get("volume", 0),
                "volume_confirmed": False,
                "patterns": []
            }
            
            # 计算当前K线特征
            curr_body = abs(curr["close"] - curr["open"])
            curr_range = curr["high"] - curr["low"]
            curr_upper_shadow = curr["high"] - max(curr["open"], curr["close"])
            curr_lower_shadow = min(curr["open"], curr["close"]) - curr["low"]
            curr_is_bullish = curr["close"] > curr["open"]
            curr_is_bearish = curr["close"] < curr["open"]
            curr_vol = curr.get("volume", avg_volume)
            
            # 计算前一根K线特征
            prev1_body = abs(prev1["close"] - prev1["open"])
            prev1_range = prev1["high"] - prev1["low"]
            prev1_is_bullish = prev1["close"] > prev1["open"]
            prev1_is_bearish = prev1["close"] < prev1["open"]
            prev1_vol = prev1.get("volume", avg_volume)
            
            prev2_body = abs(prev2["close"] - prev2["open"])
            prev2_is_bullish = prev2["close"] > prev2["open"]
            prev2_is_bearish = prev2["close"] < prev2["open"]
            prev2_vol = prev2.get("volume", avg_volume)
            
            # ==================== 单根K线形态 ====================
            # DOJI系列
            if curr_body < curr_range * 0.1:
                if curr_upper_shadow > curr_body * 3 and curr_lower_shadow > curr_body * 3:
                    pattern_info["patterns"].append("DOJI_LONG_LEGGED")
                elif curr_upper_shadow > curr_lower_shadow * 2:
                    pattern_info["patterns"].append("DOJI_GRAVESTONE")
                elif curr_lower_shadow > curr_upper_shadow * 2:
                    pattern_info["patterns"].append("DOJI_DRAGONFLY")
                else:
                    pattern_info["patterns"].append("DOJI")
            
            # 锤子线/上吊线
            if (curr_body < curr_range * 0.35 and
                curr_lower_shadow > curr_body * 2 and
                curr_upper_shadow < curr_body * 0.5):
                if curr_is_bullish:
                    pattern_info["patterns"].append("HAMMER")
                    if curr_vol > avg_volume * 1.2:
                        pattern_info["volume_confirmed"] = True
                else:
                    pattern_info["patterns"].append("HANGING_MAN")
                    if curr_vol > avg_volume * 1.2:
                        pattern_info["volume_confirmed"] = True
            
            # 倒锤子/流星线
            if (curr_body < curr_range * 0.35 and
                curr_upper_shadow > curr_body * 2 and
                curr_lower_shadow < curr_body * 0.5):
                if curr_is_bearish:
                    pattern_info["patterns"].append("INVERTED_HAMMER")
                    if curr_vol > avg_volume * 1.2:
                        pattern_info["volume_confirmed"] = True
                else:
                    pattern_info["patterns"].append("SHOOTING_STAR")
                    if curr_vol > avg_volume * 1.2:
                        pattern_info["volume_confirmed"] = True
            
            # 陀螺线
            if (curr_body < curr_range * 0.5 and
                curr_body > curr_range * 0.2 and
                curr_upper_shadow > curr_body * 0.5 and
                curr_lower_shadow > curr_body * 0.5):
                pattern_info["patterns"].append("SPINNING_TOP")
            
            # 光头光脚阳线/阴线
            if curr_body > curr_range * 0.8:
                if curr_is_bullish:
                    pattern_info["patterns"].append("MARUBOZU_BULLISH")
                    if curr_vol > avg_volume * 1.5:
                        pattern_info["volume_confirmed"] = True
                else:
                    pattern_info["patterns"].append("MARUBOZU_BEARISH")
                    if curr_vol > avg_volume * 1.5:
                        pattern_info["volume_confirmed"] = True
            
            # ==================== 两根K线形态 ====================
            # 吞没形态
            if curr_body > prev1_body * 1.5:
                if curr_is_bullish and prev1_is_bearish and curr["close"] > prev1["open"] and curr["open"] < prev1["close"]:
                    pattern_info["patterns"].append("BULLISH_ENGULFING")
                    if curr_vol > prev1_vol * 1.2:
                        pattern_info["volume_confirmed"] = True
                elif curr_is_bearish and prev1_is_bullish and curr["close"] < prev1["open"] and curr["open"] > prev1["close"]:
                    pattern_info["patterns"].append("BEARISH_ENGULFING")
                    if curr_vol > prev1_vol * 1.2:
                        pattern_info["volume_confirmed"] = True
            
            # 孕线形态
            if curr_body < prev1_body * 0.7:
                if curr["high"] < prev1["high"] and curr["low"] > prev1["low"]:
                    if prev1_is_bullish and curr_is_bearish:
                        pattern_info["patterns"].append("BEARISH_HARAMI")
                    elif prev1_is_bearish and curr_is_bullish:
                        pattern_info["patterns"].append("BULLISH_HARAMI")
            
            # 乌云盖顶/曙光初现
            if curr_body > prev1_body * 0.5 and prev1_body > 0:
                if prev1_is_bullish and curr_is_bearish:
                    if curr["open"] > prev1["high"] and curr["close"] < (prev1["open"] + prev1["close"]) / 2:
                        pattern_info["patterns"].append("DARK_CLOUD_COVER")
                        if curr_vol > prev1_vol * 1.2:
                            pattern_info["volume_confirmed"] = True
                elif prev1_is_bearish and curr_is_bullish:
                    if curr["open"] < prev1["low"] and curr["close"] > (prev1["open"] + prev1["close"]) / 2:
                        pattern_info["patterns"].append("PIERCING_PATTERN")
                        if curr_vol > prev1_vol * 1.2:
                            pattern_info["volume_confirmed"] = True
            
            # ==================== 三根K线形态 ====================
            # 晨星/暮星
            if i >= 2:
                if prev2_body > 0 and prev1_body < prev2_body * 0.3 and curr_body > prev2_body * 0.5:
                    # 晨星形态
                    if prev2_is_bearish and curr_is_bullish and prev1["high"] < prev2["low"]:
                        pattern_info["patterns"].append("MORNING_STAR")
                        if curr_vol > (prev1_vol + prev2_vol) / 2 * 1.2:
                            pattern_info["volume_confirmed"] = True
                    # 暮星形态
                    elif prev2_is_bullish and curr_is_bearish and prev1["low"] > prev2["high"]:
                        pattern_info["patterns"].append("EVENING_STAR")
                        if curr_vol > (prev1_vol + prev2_vol) / 2 * 1.2:
                            pattern_info["volume_confirmed"] = True
                
                # 三白兵/三黑鸦
                if prev2_is_bullish and prev1_is_bullish and curr_is_bullish:
                    if (curr["close"] > prev1["close"] > prev2["close"] and
                        curr_body > prev2_body * 0.5 and prev1_body > prev2_body * 0.5):
                        pattern_info["patterns"].append("THREE_WHITE_SOLDIERS")
                        if curr_vol > avg_volume * 1.3:
                            pattern_info["volume_confirmed"] = True
                elif prev2_is_bearish and prev1_is_bearish and curr_is_bearish:
                    if (curr["close"] < prev1["close"] < prev2["close"] and
                        curr_body > prev2_body * 0.5 and prev1_body > prev2_body * 0.5):
                        pattern_info["patterns"].append("THREE_BLACK_CROWS")
                        if curr_vol > avg_volume * 1.3:
                            pattern_info["volume_confirmed"] = True
            
            # 只保留有识别到形态的记录
            if pattern_info["patterns"]:
                patterns.append(pattern_info)
        
        return patterns
    
    @staticmethod
    def format_patterns(patterns: List[Dict[str, Any]], max_count: int = 5) -> str:
        """
        格式化形态识别结果
        
        Args:
            patterns: 识别到的形态列表
            max_count: 最多显示的形态数量
            
        Returns:
            格式化的字符串
        """
        if not patterns:
            return "未识别到明显的蜡烛图形态"
        
        result = []
        result.append("## 蜡烛图形态识别\n")
        
        # 只显示最近的几个形态
        recent_patterns = patterns[-max_count:]
        
        for i, pattern in enumerate(recent_patterns, 1):
            result.append(f"### {i}. {pattern['timestamp']}")
            result.append(f"- 识别形态: {', '.join(pattern['patterns'])}")
            result.append(f"- 价格: Open=${pattern['open']:.2f}, Close=${pattern['close']:.2f}")
            result.append(f"- 成交量确认: {'✅' if pattern['volume_confirmed'] else '❌'}")
            result.append("")
        
        return "\n".join(result)
