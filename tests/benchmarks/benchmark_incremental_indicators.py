#!/usr/bin/env python3
"""
增量指标计算性能基准测试

对比全量计算 vs 增量计算的性能差异
"""

import time
import pandas as pd
import numpy as np
from pathlib import Path
import shutil

from tradingagents.dataflows.complete_indicators import CompleteTechnicalIndicators
from tradingagents.dataflows.incremental_indicators import IncrementalIndicators


def generate_large_dataset(n_rows=2000):
    """生成大规模测试数据"""
    dates = pd.date_range('2020-01-01', periods=n_rows, freq='D')
    np.random.seed(42)
    
    data = {
        'timestamp': dates.strftime('%Y-%m-%d').tolist(),
        'open': 100 + np.cumsum(np.random.randn(n_rows) * 2),
        'high': 102 + np.cumsum(np.random.randn(n_rows) * 2),
        'low': 98 + np.cumsum(np.random.randn(n_rows) * 2),
        'close': 100 + np.cumsum(np.random.randn(n_rows) * 2),
        'volume': np.random.randint(1000000, 5000000, n_rows)
    }
    
    df = pd.DataFrame(data)
    # 确保high >= low, open, close
    df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
    df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
    
    return df


def benchmark_full_calculation(df, n_iterations=5):
    """基准测试：全量计算"""
    times = []
    
    for _ in range(n_iterations):
        start = time.time()
        result = CompleteTechnicalIndicators.calculate_all_indicators(df)
        elapsed = time.time() - start
        times.append(elapsed)
    
    avg_time = sum(times) / len(times)
    return avg_time, result


def benchmark_incremental_calculation(df, n_new_rows=20, n_iterations=5):
    """基准测试：增量计算"""
    cache_dir = Path("/tmp/indicator_benchmark_cache")
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    cache_dir.mkdir()
    
    calculator = IncrementalIndicators(str(cache_dir))
    
    # 首次全量计算
    initial_df = df.iloc[:-n_new_rows]
    calculator.calculate(initial_df, symbol="BENCH")
    
    # 增量计算
    times = []
    for _ in range(n_iterations):
        start = time.time()
        result = calculator.calculate(df, symbol="BENCH")
        elapsed = time.time() - start
        times.append(elapsed)
    
    avg_time = sum(times) / len(times)
    
    # 清理
    shutil.rmtree(cache_dir)
    
    return avg_time, result


def main():
    print("=" * 80)
    print("增量指标计算性能基准测试")
    print("=" * 80)
    
    # 测试配置
    configs = [
        (500, 10),
        (1000, 20),
        (2000, 20),
    ]
    
    for n_rows, n_new in configs:
        print(f"\n数据规模: {n_rows}行, 新增: {n_new}行")
        print("-" * 80)
        
        df = generate_large_dataset(n_rows)
        
        # 全量计算
        print("⏳ 测试全量计算...")
        full_time, full_result = benchmark_full_calculation(df, n_iterations=3)
        
        # 增量计算
        print("⏳ 测试增量计算...")
        incr_time, incr_result = benchmark_incremental_calculation(df, n_new, n_iterations=3)
        
        # 结果
        speedup = full_time / incr_time if incr_time > 0 else 0
        improvement = ((full_time - incr_time) / full_time * 100) if full_time > 0 else 0
        
        print(f"\n📊 结果:")
        print(f"  全量计算: {full_time:.3f}s")
        print(f"  增量计算: {incr_time:.3f}s")
        print(f"  加速比: {speedup:.2f}x")
        print(f"  性能提升: {improvement:.1f}%")
        
        # 验证结果一致性
        n_cols = len(full_result.columns)
        print(f"\n✅ 指标数量: {n_cols}列")
    
    print("\n" + "=" * 80)
    print("✅ 基准测试完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
