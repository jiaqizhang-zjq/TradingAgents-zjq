"""
异步数据加载器性能基准测试
对比同步vs异步加载时间
"""
import time
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tradingagents.dataflows.data_preloader import DataPreloader
from tradingagents.dataflows.async_data_loader import AsyncDataLoader


def benchmark_sync_loader():
    """基准测试：同步加载"""
    print("=" * 60)
    print("📊 同步数据加载基准测试")
    print("=" * 60)
    
    ticker = "AAPL"
    end_date = "2024-01-01"
    
    start = time.time()
    loader = DataPreloader(ticker, end_date, lookback_days=180)
    loader.load_all_data()
    elapsed = time.time() - start
    
    print(f"✅ 同步加载完成")
    print(f"   耗时: {elapsed:.2f}秒")
    print(f"   股票数据: {'有' if loader.stock_data_str else '无'}")
    print(f"   指标数量: {len(loader.indicators)}")
    print(f"   基本面: {'有' if loader.fundamentals else '无'}")
    
    return elapsed


def benchmark_async_loader():
    """基准测试：异步加载"""
    print("\n" + "=" * 60)
    print("⚡ 异步数据加载基准测试")
    print("=" * 60)
    
    ticker = "AAPL"
    end_date = "2024-01-01"
    
    start = time.time()
    loader = AsyncDataLoader(ticker, end_date, lookback_days=180, max_workers=8)
    loader.load_all_data_sync()
    elapsed = time.time() - start
    
    print(f"✅ 异步加载完成")
    print(f"   耗时: {elapsed:.2f}秒")
    print(f"   股票数据: {'有' if loader.stock_data_str else '无'}")
    print(f"   指标数量: {len(loader.indicators)}")
    print(f"   基本面: {'有' if loader.fundamentals else '无'}")
    
    return elapsed


def main():
    print("\n🚀 异步数据加载性能对比测试\n")
    
    # 运行同步版本
    sync_time = benchmark_sync_loader()
    
    # 运行异步版本
    async_time = benchmark_async_loader()
    
    # 对比分析
    print("\n" + "=" * 60)
    print("📈 性能对比分析")
    print("=" * 60)
    
    speedup = sync_time / async_time if async_time > 0 else 0
    improvement = ((sync_time - async_time) / sync_time * 100) if sync_time > 0 else 0
    
    print(f"同步加载时间: {sync_time:.2f}秒")
    print(f"异步加载时间: {async_time:.2f}秒")
    print(f"加速比: {speedup:.2f}x")
    print(f"性能提升: {improvement:.1f}%")
    print(f"节省时间: {sync_time - async_time:.2f}秒")
    
    if speedup > 2:
        print("\n🎉 异步加载实现显著性能提升！")
    elif speedup > 1.5:
        print("\n✅ 异步加载实现良好性能提升！")
    else:
        print("\n⚠️  性能提升有限，可能受限于网络或API限流")


if __name__ == "__main__":
    main()
