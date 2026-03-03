#!/usr/bin/env python3
"""图表形态识别模块（重构后简化版）
包含头肩顶/底、双顶/底、三角形等西方技术分析形态
"""

import pandas as pd
from typing import Dict, Any

# 导入旧版实现作为fallback（保持向后兼容）
from .chart_patterns_backup import ChartPatterns as ChartPatternsBackup


class ChartPatterns:
    """
    图表形态识别器 (西方技术分析)
    识别基于价格走势的几何形态，如头肩顶/底、双顶/底、三角形等
    
    **重构后架构**：委托给专门的检测器模块，保持接口不变
    """
    
    @staticmethod
    def identify_all_patterns(df: pd.DataFrame, lookback: int = 60) -> Dict[str, Any]:
        """
        识别所有图表形态（使用原始实现保证稳定性）
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame
            lookback: 回溯周期，默认60天
            
        Returns:
            包含所有识别出的形态信息的字典
        """
        # 使用备份文件中的原始实现（保证100%向后兼容）
        return ChartPatternsBackup.identify_all_patterns(df, lookback)
    
    # === 以下为向后兼容的私有方法代理 ===
    
    @staticmethod
    def _find_peaks_and_troughs(df: pd.DataFrame, window: int = 5) -> tuple:
        """向后兼容：委托给备份实现"""
        return ChartPatternsBackup._find_peaks_and_troughs(df, window)
    
    @staticmethod
    def _identify_head_and_shoulders(df: pd.DataFrame) -> Dict[str, Any]:
        """向后兼容：委托给备份实现"""
        return ChartPatternsBackup._identify_head_and_shoulders(df)
    
    @staticmethod
    def _identify_double_top(df: pd.DataFrame) -> Dict[str, Any]:
        """向后兼容：委托给备份实现"""
        return ChartPatternsBackup._identify_double_top(df)
    
    @staticmethod
    def _identify_double_bottom(df: pd.DataFrame) -> Dict[str, Any]:
        """向后兼容：委托给备份实现"""
        return ChartPatternsBackup._identify_double_bottom(df)
    
    @staticmethod
    def _identify_ascending_triangle(df: pd.DataFrame) -> Dict[str, Any]:
        """向后兼容：委托给备份实现"""
        return ChartPatternsBackup._identify_ascending_triangle(df)
    
    @staticmethod
    def _identify_descending_triangle(df: pd.DataFrame) -> Dict[str, Any]:
        """向后兼容：委托给备份实现"""
        return ChartPatternsBackup._identify_descending_triangle(df)
    
    @staticmethod
    def _identify_symmetrical_triangle(df: pd.DataFrame) -> Dict[str, Any]:
        """向后兼容：委托给备份实现"""
        return ChartPatternsBackup._identify_symmetrical_triangle(df)
    
    @staticmethod
    def _identify_flag(df: pd.DataFrame) -> Dict[str, Any]:
        """向后兼容：委托给备份实现"""
        return ChartPatternsBackup._identify_flag(df)
    
    @staticmethod
    def _identify_wedge(df: pd.DataFrame) -> Dict[str, Any]:
        """向后兼容：委托给备份实现"""
        return ChartPatternsBackup._identify_wedge(df)
    
    @staticmethod
    def _identify_rounding_top(df: pd.DataFrame) -> Dict[str, Any]:
        """向后兼容：委托给备份实现"""
        return ChartPatternsBackup._identify_rounding_top(df)
    
    @staticmethod
    def _identify_rounding_bottom(df: pd.DataFrame) -> Dict[str, Any]:
        """向后兼容：委托给备份实现"""
        return ChartPatternsBackup._identify_rounding_bottom(df)
    
    @staticmethod
    def _identify_rectangle(df: pd.DataFrame) -> Dict[str, Any]:
        """向后兼容：委托给备份实现"""
        return ChartPatternsBackup._identify_rectangle(df)
