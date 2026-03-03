"""
研究追踪器主协调器（重构后简化版）

原research_tracker.py (818行) → tracker.py (150行)
策略：保持公共API不变，简化内部实现
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import contextmanager

from .models import ResearchOutcome, ResearchRecord, ResearcherStats


class ResearchTracker:
    """
    Research Team 胜率追踪器（重构后）
    
    功能：
    1. 记录每个研究员的每次预测
    2. 验证预测结果（对比实际收益）
    3. 统计胜率、收益率等指标
    """
    
    def __init__(self, db_path: str = "tradingagents/db/research_tracker.db"):
        self.db_path = db_path
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """初始化数据库表结构（简化版）"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 研究记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS research_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    researcher_name TEXT NOT NULL,
                    researcher_type TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    trade_date TEXT NOT NULL,
                    prediction TEXT NOT NULL,
                    confidence REAL DEFAULT 0.0,
                    reasoning TEXT,
                    outcome TEXT DEFAULT 'pending',
                    verified_date TEXT,
                    actual_return REAL,
                    holding_days INTEGER DEFAULT 5,
                    created_at TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    buy_price REAL,
                    initial_capital REAL DEFAULT 10000,
                    shares REAL,
                    total_return REAL,
                    backtest_date TEXT,
                    backtest_price REAL,
                    UNIQUE(researcher_name, symbol, trade_date)
                )
            ''')
            
            # 研究员配置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS researcher_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    researcher_name TEXT UNIQUE NOT NULL,
                    researcher_type TEXT NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT NOT NULL,
                    config_json TEXT DEFAULT '{}'
                )
            ''')
            
            # 股票收益记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_returns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    trade_date TEXT NOT NULL,
                    holding_days INTEGER NOT NULL,
                    return_rate REAL NOT NULL,
                    close_price REAL,
                    future_price REAL,
                    created_at TEXT NOT NULL,
                    UNIQUE(symbol, trade_date, holding_days)
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_research_records_symbol_date ON research_records(symbol, trade_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_research_records_researcher ON research_records(researcher_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_research_records_outcome ON research_records(outcome)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_returns_symbol_date ON stock_returns(symbol, trade_date)')
            
            conn.commit()
    
    def record_research(self, researcher_name: str, researcher_type: str, symbol: str, 
                       trade_date: str, prediction: str, confidence: float = 0.0,
                       reasoning: str = "", holding_days: int = 5, metadata: Dict = None,
                       buy_price: float = None, initial_capital: float = 10000.0,
                       shares: float = None, total_return: float = None) -> bool:
        """记录一次研究预测"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                created_at = datetime.now().isoformat()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO research_records (
                        researcher_name, researcher_type, symbol, trade_date,
                        prediction, confidence, reasoning, outcome,
                        holding_days, created_at, metadata,
                        buy_price, initial_capital, shares, total_return
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (researcher_name, researcher_type, symbol, trade_date,
                      prediction.upper(), confidence, reasoning, ResearchOutcome.PENDING.value,
                      holding_days, created_at, json.dumps(metadata or {}),
                      buy_price, initial_capital, shares, total_return))
                
                return True
        except Exception as e:
            print(f"❌ 记录研究预测失败: {e}")
            return False
    
    def verify_prediction(self, researcher_name: str, symbol: str, trade_date: str,
                         actual_return: float, outcome: str = None) -> bool:
        """验证一次预测结果"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT prediction FROM research_records WHERE researcher_name = ? AND symbol = ? AND trade_date = ?',
                             (researcher_name, symbol, trade_date))
                row = cursor.fetchone()
                if not row:
                    return False
                
                prediction = row['prediction']
                if outcome is None:
                    outcome = self._auto_judge_outcome(prediction, actual_return)
                
                verified_date = datetime.now().isoformat()
                cursor.execute('UPDATE research_records SET outcome = ?, actual_return = ?, verified_date = ? WHERE researcher_name = ? AND symbol = ? AND trade_date = ?',
                             (outcome, actual_return, verified_date, researcher_name, symbol, trade_date))
                
                return True
        except Exception as e:
            print(f"❌ 验证预测失败: {e}")
            return False
    
    def _auto_judge_outcome(self, prediction: str, actual_return: float) -> str:
        """自动判断预测结果"""
        prediction = prediction.upper()
        if prediction == "BUY":
            return ResearchOutcome.CORRECT.value if actual_return > 0.02 else ResearchOutcome.INCORRECT.value
        elif prediction == "SELL":
            return ResearchOutcome.CORRECT.value if actual_return < -0.02 else ResearchOutcome.INCORRECT.value
        else:  # HOLD
            return ResearchOutcome.CORRECT.value if abs(actual_return) <= 0.02 else ResearchOutcome.PARTIAL.value
    
    def get_researcher_stats(self, researcher_name: str, symbol: str = None, 
                            start_date: str = None, end_date: str = None) -> Optional[ResearcherStats]:
        """获取研究员统计数据（委托给原实现）"""
        # 为简化重构，直接导入原实现
        from ..research_tracker import ResearchTracker as OriginalTracker
        original = OriginalTracker(self.db_path)
        return original.get_researcher_stats(researcher_name, symbol, start_date, end_date)
    
    def get_symbol_stats(self, symbol: str, start_date: str = None, end_date: str = None) -> Dict:
        """获取股票统计数据"""
        from ..research_tracker import ResearchTracker as OriginalTracker
        original = OriginalTracker(self.db_path)
        return original.get_symbol_stats(symbol, start_date, end_date)
    
    def register_researcher(self, researcher_name: str, researcher_type: str, 
                           description: str = "", config: Dict = None) -> bool:
        """注册新研究员"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                created_at = datetime.now().isoformat()
                
                cursor.execute('INSERT OR REPLACE INTO researcher_configs (researcher_name, researcher_type, description, created_at, config_json) VALUES (?, ?, ?, ?, ?)',
                             (researcher_name, researcher_type, description, created_at, json.dumps(config or {})))
                return True
        except Exception as e:
            print(f"❌ 注册研究员失败: {e}")
            return False
    
    def get_registered_researchers(self, researcher_type: str = None, is_active: bool = True) -> List[Dict]:
        """获取已注册的研究员列表"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT * FROM researcher_configs WHERE 1=1'
                params = []
                
                if researcher_type:
                    query += ' AND researcher_type = ?'
                    params.append(researcher_type)
                if is_active is not None:
                    query += ' AND is_active = ?'
                    params.append(1 if is_active else 0)
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ 获取研究员列表失败: {e}")
            return []
    
    def batch_verify_pending_predictions(self, get_actual_return_func) -> int:
        """批量验证待验证的预测"""
        from ..research_tracker import ResearchTracker as OriginalTracker
        original = OriginalTracker(self.db_path)
        return original.batch_verify_pending_predictions(get_actual_return_func)
    
    def get_researcher_win_rate(self, researcher_name: str, symbol: str = None, 
                               days: int = 30) -> float:
        """获取研究员胜率"""
        from ..research_tracker import ResearchTracker as OriginalTracker
        original = OriginalTracker(self.db_path)
        return original.get_researcher_win_rate(researcher_name, symbol, days)


# 全局实例（向后兼容）
_tracker_instance: Optional[ResearchTracker] = None


def get_research_tracker(db_path: str = "tradingagents/db/research_tracker.db") -> ResearchTracker:
    """获取全局 ResearchTracker 实例（单例模式）"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = ResearchTracker(db_path)
    return _tracker_instance
