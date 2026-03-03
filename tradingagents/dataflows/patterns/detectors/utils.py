"""形态识别工具函数"""

import pandas as pd


def find_peaks_and_troughs(df: pd.DataFrame, window: int = 5) -> tuple:
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
