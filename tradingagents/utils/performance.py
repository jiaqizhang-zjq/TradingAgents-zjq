#!/usr/bin/env python3
"""
性能监控工具
提供装饰器和统计收集功能
"""

import time
from functools import wraps
from typing import Dict, Any, Callable
from collections import defaultdict


class PerformanceTracker:
    """性能追踪器"""
    
    def __init__(self) -> None:
        self._stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "total_time": 0.0,
            "min_time": float('inf'),
            "max_time": 0.0,
            "avg_time": 0.0,
            "last_time": 0.0
        })
    
    def record(self, func_name: str, elapsed: float) -> None:
        """记录一次执行"""
        stats = self._stats[func_name]
        stats["count"] += 1
        stats["total_time"] += elapsed
        stats["min_time"] = min(stats["min_time"], elapsed)
        stats["max_time"] = max(stats["max_time"], elapsed)
        stats["avg_time"] = stats["total_time"] / stats["count"]
        stats["last_time"] = elapsed
    
    def get_stats(self, func_name: str = None) -> Dict[str, Any]:
        """获取统计信息"""
        if func_name:
            return dict(self._stats.get(func_name, {}))
        return {k: dict(v) for k, v in self._stats.items()}
    
    def get_report(self) -> str:
        """生成性能报告"""
        if not self._stats:
            return "No performance data recorded."
        
        lines = ["Performance Statistics:", "=" * 80]
        
        # 按总耗时排序
        sorted_stats = sorted(
            self._stats.items(),
            key=lambda x: x[1]["total_time"],
            reverse=True
        )
        
        for func_name, stats in sorted_stats:
            lines.append(
                f"{func_name:40} | "
                f"Calls: {stats['count']:4} | "
                f"Avg: {stats['avg_time']:6.3f}s | "
                f"Total: {stats['total_time']:7.2f}s | "
                f"Min: {stats['min_time']:6.3f}s | "
                f"Max: {stats['max_time']:6.3f}s"
            )
        
        lines.append("=" * 80)
        return "\n".join(lines)
    
    def reset(self) -> None:
        """重置所有统计"""
        self._stats.clear()


# 全局性能追踪器（使用依赖注入容器管理）
def get_performance_tracker() -> PerformanceTracker:
    """获取性能追踪器实例（通过依赖注入容器）"""
    from tradingagents.core.container import get_container
    container = get_container()
    
    if not container.has('performance_tracker'):
        container.register('performance_tracker', lambda: PerformanceTracker(), singleton=True)
    
    return container.get('performance_tracker')


def track_performance(func_type: str = None):
    """
    性能监控装饰器
    
    Args:
        func_type: 函数类型标签（可选，默认使用函数名）
    
    用法:
        @track_performance("llm_call")
        def call_llm(...):
            ...
        
        @track_performance()
        def fetch_data(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                name = func_type or f"{func.__module__}.{func.__name__}"
                _tracker.record(name, elapsed)
        
        return wrapper
    
    return decorator


def get_performance_stats(func_name: str = None) -> Dict[str, Any]:
    """
    获取性能统计
    
    Args:
        func_name: 函数名（可选，None返回所有统计）
    
    Returns:
        统计字典
    """
    return _tracker.get_stats(func_name)


def get_performance_report() -> str:
    """
    生成性能报告
    
    Returns:
        格式化的报告字符串
    """
    return _tracker.get_report()


def reset_performance_stats() -> None:
    """重置所有性能统计"""
    _tracker.reset()


# 便捷装饰器别名
track_llm = track_performance("llm_call")
track_data_fetch = track_performance("data_fetch")
track_indicator = track_performance("indicator_calculation")
track_agent = track_performance("agent_execution")


if __name__ == "__main__":
    # 测试代码
    @track_performance("test_function")
    def slow_function(n: int) -> int:
        time.sleep(0.1)
        return n * 2
    
    # 执行多次
    for i in range(5):
        slow_function(i)
    
    # 打印报告
    print(get_performance_report())
