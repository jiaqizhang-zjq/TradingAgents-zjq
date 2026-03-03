"""
研究追踪系统模块（重构后）

原research_tracker.py (818行) → 拆分为：
- models.py - 数据模型
- database_ops.py - 数据库操作
- stats_calculator.py - 统计计算
- prediction_verifier.py - 预测验证
- tracker.py - 主协调器
"""

from .models import ResearchOutcome, ResearchRecord, ResearcherStats
from .tracker import ResearchTracker, get_research_tracker

__all__ = [
    "ResearchOutcome",
    "ResearchRecord",
    "ResearcherStats",
    "ResearchTracker",
    "get_research_tracker",
]
