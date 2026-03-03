"""
数据模型定义
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class ResearchOutcome(Enum):
    """研究结果 outcomes"""
    CORRECT = "correct"      # 预测正确
    INCORRECT = "incorrect"  # 预测错误
    PENDING = "pending"      # 待验证
    PARTIAL = "partial"      # 部分正确


@dataclass
class ResearchRecord:
    """单次研究记录"""
    id: Optional[int] = None
    researcher_name: str = ""           # 研究员名称 (bull/bear/自定义)
    researcher_type: str = ""           # 类型 (bull/bear/neutral/aggressive/conservative)
    symbol: str = ""                    # 股票代码
    trade_date: str = ""                # 交易日期
    prediction: str = ""                # 预测结果 (BUY/SELL/HOLD)
    confidence: float = 0.0             # 置信度 0-1
    reasoning: str = ""                 # 推理过程
    
    # 验证相关
    outcome: str = "pending"            # 验证结果
    verified_date: Optional[str] = None # 验证日期
    actual_return: Optional[float] = None  # 实际收益率
    holding_days: int = 5               # 持仓天数 (默认5天)
    
    # 元数据
    created_at: str = ""
    metadata: str = "{}"


@dataclass
class ResearcherStats:
    """研究员统计数据"""
    researcher_name: str
    researcher_type: str
    total_predictions: int = 0
    correct_predictions: int = 0
    incorrect_predictions: int = 0
    pending_predictions: int = 0
    win_rate: float = 0.0
    avg_confidence: float = 0.0
    avg_return: float = 0.0
    best_return: float = 0.0
    worst_return: float = 0.0
    
    # 按预测类型分组
    buy_predictions: int = 0
    sell_predictions: int = 0
    hold_predictions: int = 0
    
    buy_win_rate: float = 0.0
    sell_win_rate: float = 0.0
    hold_win_rate: float = 0.0
    
    # 时间范围
    first_prediction_date: Optional[str] = None
    last_prediction_date: Optional[str] = None
    
    def __post_init__(self):
        """计算胜率"""
        total_verified = self.correct_predictions + self.incorrect_predictions
        if total_verified > 0:
            self.win_rate = self.correct_predictions / total_verified
