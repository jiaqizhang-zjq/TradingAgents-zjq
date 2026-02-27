"""
Research Team 胜率追踪系统
用于记录和统计每个研究员在不同股票上的预测准确率
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

from contextlib import contextmanager
from enum import Enum

# 导入依赖注入容器
from tradingagents.core.container import get_container


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
    """研究员统计信息"""
    researcher_name: str
    researcher_type: str
    total_predictions: int = 0
    correct_predictions: int = 0
    incorrect_predictions: int = 0
    partial_predictions: int = 0
    pending_predictions: int = 0
    
    # 胜率统计
    win_rate: float = 0.0               # 总胜率
    win_rate_bull: float = 0.0          # 看多胜率
    win_rate_bear: float = 0.0          # 看空胜率
    
    # 收益统计
    avg_return: float = 0.0             # 平均收益
    max_return: float = 0.0             # 最大收益
    min_return: float = 0.0             # 最小收益
    
    # 股票维度统计
    symbols_traded: List[str] = None
    best_symbol: str = ""               # 表现最好的股票
    worst_symbol: str = ""              # 表现最差的股票
    
    def __post_init__(self):
        if self.symbols_traded is None:
            self.symbols_traded = []


class ResearchTracker:
    """
    Research Team 胜率追踪器
    
    功能：
    1. 记录每个研究员的每次预测
    2. 验证预测结果（对比实际收益）
    3. 统计胜率、收益率等指标
    4. 支持按股票、时间、研究员类型筛选
    5. 预留扩展接口，方便添加新的研究员类型
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
        """初始化数据库表结构"""
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
                    prediction TEXT NOT NULL,  -- BUY, SELL, HOLD
                    confidence REAL DEFAULT 0.0,
                    reasoning TEXT,
                    outcome TEXT DEFAULT 'pending',  -- pending, correct, incorrect, partial
                    verified_date TEXT,
                    actual_return REAL,
                    holding_days INTEGER DEFAULT 5,
                    created_at TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    buy_price REAL,  -- 买入价格（交易当天收盘价）
                    initial_capital REAL DEFAULT 10000,  -- 初始资金，默认1万美元
                    shares REAL,  -- 头寸数量
                    total_return REAL,  -- 总收益（金额）
                    backtest_date TEXT,  -- 回测日期
                    backtest_price REAL,  -- 回测价格
                    
                    -- 复合索引
                    UNIQUE(researcher_name, symbol, trade_date)
                )
            ''')
            
            # 研究员配置表 (用于扩展新的研究员类型)
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
            
            # 股票收益记录表 (用于验证预测)
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
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_research_records_symbol_date 
                ON research_records(symbol, trade_date)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_research_records_researcher 
                ON research_records(researcher_name)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_research_records_outcome 
                ON research_records(outcome)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_stock_returns_symbol_date 
                ON stock_returns(symbol, trade_date)
            ''')
            
            conn.commit()
            print(f"✅ Research Tracker 数据库初始化完成: {self.db_path}")
    
    # ==================== 记录管理 ====================
    
    def record_research(
        self,
        researcher_name: str,
        researcher_type: str,
        symbol: str,
        trade_date: str,
        prediction: str,  # BUY, SELL, HOLD
        confidence: float = 0.0,
        reasoning: str = "",
        holding_days: int = 5,
        metadata: Dict = None,
        buy_price: float = None,
        initial_capital: float = 10000.0,
        shares: float = None,
        total_return: float = None
    ) -> bool:
        """
        记录一次研究预测
        
        Args:
            researcher_name: 研究员名称 (如 "bull_001", "aggressive_001")
            researcher_type: 研究员类型 (bull/bear/neutral/aggressive/conservative)
            symbol: 股票代码
            trade_date: 交易日期
            prediction: 预测结果 (BUY/SELL/HOLD)
            confidence: 置信度 0-1
            reasoning: 推理过程
            holding_days: 持仓天数
            metadata: 额外元数据
            buy_price: 买入价格
            initial_capital: 初始资金
            shares: 头寸数量
            total_return: 总收益
            
        Returns:
            bool: 是否记录成功
        """
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
                ''', (
                    researcher_name,
                    researcher_type,
                    symbol,
                    trade_date,
                    prediction.upper(),
                    confidence,
                    reasoning,
                    ResearchOutcome.PENDING.value,
                    holding_days,
                    created_at,
                    json.dumps(metadata or {}),
                    buy_price,  # 买入价格
                    initial_capital,  # 初始资金
                    shares,  # 头寸数量
                    total_return  # 总收益
                ))
                
                print(f"✅ 记录研究预测: {researcher_name} -> {symbol} {prediction}")
                return True
                
        except Exception as e:
            print(f"❌ 记录研究预测失败: {e}")
            return False
    
    def verify_prediction(
        self,
        researcher_name: str,
        symbol: str,
        trade_date: str,
        actual_return: float,
        outcome: str = None
    ) -> bool:
        """
        验证一次预测结果
        
        Args:
            researcher_name: 研究员名称
            symbol: 股票代码
            trade_date: 交易日期
            actual_return: 实际收益率 (如 0.05 表示 5%)
            outcome: 验证结果 (correct/incorrect/partial)，为None则自动判断
            
        Returns:
            bool: 是否验证成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取原预测
                cursor.execute('''
                    SELECT prediction FROM research_records 
                    WHERE researcher_name = ? AND symbol = ? AND trade_date = ?
                ''', (researcher_name, symbol, trade_date))
                
                row = cursor.fetchone()
                if not row:
                    print(f"❌ 未找到预测记录: {researcher_name} {symbol} {trade_date}")
                    return False
                
                prediction = row['prediction']
                
                # 自动判断结果
                if outcome is None:
                    outcome = self._auto_judge_outcome(prediction, actual_return)
                
                verified_date = datetime.now().isoformat()
                
                cursor.execute('''
                    UPDATE research_records 
                    SET outcome = ?, actual_return = ?, verified_date = ?
                    WHERE researcher_name = ? AND symbol = ? AND trade_date = ?
                ''', (outcome, actual_return, verified_date, 
                      researcher_name, symbol, trade_date))
                
                # 同时记录到股票收益表
                cursor.execute('''
                    INSERT OR REPLACE INTO stock_returns (
                        symbol, trade_date, holding_days, return_rate, created_at
                    ) SELECT symbol, trade_date, holding_days, ?, ?
                    FROM research_records 
                    WHERE researcher_name = ? AND symbol = ? AND trade_date = ?
                ''', (actual_return, verified_date, researcher_name, symbol, trade_date))
                
                print(f"✅ 验证预测: {researcher_name} {symbol} -> {outcome} (收益: {actual_return:.2%})")
                return True
                
        except Exception as e:
            print(f"❌ 验证预测失败: {e}")
            return False
    
    def _auto_judge_outcome(self, prediction: str, actual_return: float) -> str:
        """自动判断预测结果"""
        prediction = prediction.upper()
        
        if prediction == "BUY":
            if actual_return > 0.02:  # 涨超过2%
                return ResearchOutcome.CORRECT.value
            elif actual_return < -0.02:  # 跌超过2%
                return ResearchOutcome.INCORRECT.value
            else:
                return ResearchOutcome.PARTIAL.value
                
        elif prediction == "SELL":
            if actual_return < -0.02:  # 跌超过2%
                return ResearchOutcome.CORRECT.value
            elif actual_return > 0.02:  # 涨超过2%
                return ResearchOutcome.INCORRECT.value
            else:
                return ResearchOutcome.PARTIAL.value
                
        else:  # HOLD
            if abs(actual_return) < 0.02:  # 波动小于2%
                return ResearchOutcome.CORRECT.value
            else:
                return ResearchOutcome.INCORRECT.value
    
    # ==================== 统计查询 ====================
    
    def get_researcher_stats(
        self,
        researcher_name: str = None,
        researcher_type: str = None,
        symbol: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> List[ResearcherStats]:
        """
        获取研究员统计信息
        
        Args:
            researcher_name: 按研究员名称筛选
            researcher_type: 按研究员类型筛选
            symbol: 按股票筛选
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            ResearcherStats 列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 构建查询条件
                conditions = ["1=1"]
                params = []
                
                if researcher_name:
                    conditions.append("researcher_name = ?")
                    params.append(researcher_name)
                if researcher_type:
                    conditions.append("researcher_type = ?")
                    params.append(researcher_type)
                if symbol:
                    conditions.append("symbol = ?")
                    params.append(symbol)
                if start_date:
                    conditions.append("trade_date >= ?")
                    params.append(start_date)
                if end_date:
                    conditions.append("trade_date <= ?")
                    params.append(end_date)
                
                where_clause = " AND ".join(conditions)
                
                # 获取每个研究员的统计
                cursor.execute(f'''
                    SELECT 
                        researcher_name,
                        researcher_type,
                        COUNT(*) as total,
                        SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct,
                        SUM(CASE WHEN outcome = 'incorrect' THEN 1 ELSE 0 END) as incorrect,
                        SUM(CASE WHEN outcome = 'partial' THEN 1 ELSE 0 END) as partial,
                        SUM(CASE WHEN outcome = 'pending' THEN 1 ELSE 0 END) as pending,
                        AVG(CASE WHEN outcome != 'pending' THEN actual_return END) as avg_return,
                        MAX(CASE WHEN outcome != 'pending' THEN actual_return END) as max_return,
                        MIN(CASE WHEN outcome != 'pending' THEN actual_return END) as min_return,
                        GROUP_CONCAT(DISTINCT symbol) as symbols
                    FROM research_records
                    WHERE {where_clause}
                    GROUP BY researcher_name, researcher_type
                ''', params)
                
                rows = cursor.fetchall()
                
                stats_list = []
                for row in rows:
                    total = row['total'] or 0
                    correct = row['correct'] or 0
                    incorrect = row['incorrect'] or 0
                    partial = row['partial'] or 0
                    
                    # 计算胜率
                    verified = correct + incorrect + partial
                    win_rate = correct / verified if verified > 0 else 0
                    
                    stats = ResearcherStats(
                        researcher_name=row['researcher_name'],
                        researcher_type=row['researcher_type'],
                        total_predictions=total,
                        correct_predictions=correct,
                        incorrect_predictions=incorrect,
                        partial_predictions=partial,
                        pending_predictions=row['pending'] or 0,
                        win_rate=win_rate,
                        avg_return=row['avg_return'] or 0,
                        max_return=row['max_return'] or 0,
                        min_return=row['min_return'] or 0,
                        symbols_traded=row['symbols'].split(',') if row['symbols'] else []
                    )
                    stats_list.append(stats)
                
                return stats_list
                
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
            return []
    
    def get_symbol_stats(
        self,
        symbol: str,
        researcher_type: str = None
    ) -> Dict:
        """
        获取特定股票的预测统计
        
        Args:
            symbol: 股票代码
            researcher_type: 研究员类型筛选
            
        Returns:
            统计字典
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                conditions = ["symbol = ?"]
                params = [symbol]
                
                if researcher_type:
                    conditions.append("researcher_type = ?")
                    params.append(researcher_type)
                
                where_clause = " AND ".join(conditions)
                
                cursor.execute(f'''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct,
                        AVG(actual_return) as avg_return
                    FROM research_records
                    WHERE {where_clause}
                ''', params)
                
                row = cursor.fetchone()
                
                total = row['total'] or 0
                correct = row['correct'] or 0
                
                return {
                    'symbol': symbol,
                    'total_predictions': total,
                    'correct_predictions': correct,
                    'win_rate': correct / total if total > 0 else 0,
                    'avg_return': row['avg_return'] or 0
                }
                
        except Exception as e:
            print(f"❌ 获取股票统计失败: {e}")
            return {}
    
    # ==================== 扩展接口 ====================
    
    def register_researcher(
        self,
        researcher_name: str,
        researcher_type: str,
        description: str = "",
        config: Dict = None
    ) -> bool:
        """
        注册新的研究员类型 (扩展接口)
        
        Args:
            researcher_name: 研究员唯一名称
            researcher_type: 研究员类型 (可自定义)
            description: 描述
            config: 配置参数
            
        Returns:
            bool: 是否注册成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                created_at = datetime.now().isoformat()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO researcher_configs (
                        researcher_name, researcher_type, description,
                        created_at, config_json
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    researcher_name,
                    researcher_type,
                    description,
                    created_at,
                    json.dumps(config or {})
                ))
                
                print(f"✅ 注册研究员: {researcher_name} ({researcher_type})")
                return True
                
        except Exception as e:
            print(f"❌ 注册研究员失败: {e}")
            return False
    
    def get_registered_researchers(
        self,
        researcher_type: str = None,
        active_only: bool = True
    ) -> List[Dict]:
        """
        获取已注册的研究员列表
        
        Args:
            researcher_type: 按类型筛选
            active_only: 只返回活跃的研究员
            
        Returns:
            研究员列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                conditions = ["1=1"]
                params = []
                
                if researcher_type:
                    conditions.append("researcher_type = ?")
                    params.append(researcher_type)
                if active_only:
                    conditions.append("is_active = 1")
                
                where_clause = " AND ".join(conditions)
                
                cursor.execute(f'''
                    SELECT * FROM researcher_configs
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                ''', params)
                
                rows = cursor.fetchall()
                
                return [
                    {
                        'researcher_name': row['researcher_name'],
                        'researcher_type': row['researcher_type'],
                        'description': row['description'],
                        'is_active': bool(row['is_active']),
                        'config': json.loads(row['config_json'])
                    }
                    for row in rows
                ]
                
        except Exception as e:
            print(f"❌ 获取研究员列表失败: {e}")
            return []
    
    def batch_verify_pending_predictions(
        self,
        symbol: str = None,
        date_range: int = 7
    ) -> int:
        """
        批量验证待验证的预测
        
        Args:
            symbol: 按股票筛选
            date_range: 验证多少天前的预测
            
        Returns:
            验证的记录数
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取待验证的记录
                conditions = ["outcome = 'pending'"]
                params = []
                
                if symbol:
                    conditions.append("symbol = ?")
                    params.append(symbol)
                
                where_clause = " AND ".join(conditions)
                
                cursor.execute(f'''
                    SELECT * FROM research_records
                    WHERE {where_clause}
                ''', params)
                
                rows = cursor.fetchall()
                verified_count = 0
                
                for row in rows:
                    # 这里需要从外部获取实际收益数据
                    # 简化示例：假设收益为0
                    actual_return = 0.0  # 实际应从数据源获取
                    
                    self.verify_prediction(
                        row['researcher_name'],
                        row['symbol'],
                        row['trade_date'],
                        actual_return
                    )
                    verified_count += 1
                
                return verified_count
                
        except Exception as e:
            print(f"❌ 批量验证失败: {e}")
            return 0
    
    def get_researcher_win_rate(
        self,
        researcher_name: str,
        symbol: str = None,
        default_win_rate: float = 0.5
    ) -> Dict:
        """
        获取研究员的胜率统计
        
        优先返回特定股票的胜率，如果没有则返回该研究员的平均胜率，
        如果仍然没有则返回默认胜率（行业均值）
        
        Args:
            researcher_name: 研究员名称
            symbol: 股票代码（可选）
            default_win_rate: 默认胜率（行业均值，默认0.5）
            
        Returns:
            {
                'win_rate': 胜率,
                'total_predictions': 总预测数,
                'correct_predictions': 正确预测数,
                'source': 'symbol_specific'/'researcher_average'/'default',
                'symbol': 股票代码（如果是特定股票）
            }
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. 首先尝试获取特定股票的胜率
                if symbol:
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct
                        FROM research_records
                        WHERE researcher_name = ? 
                        AND symbol = ?
                        AND outcome != 'pending'
                    ''', (researcher_name, symbol))
                    
                    row = cursor.fetchone()
                    total = row['total'] or 0
                    correct = row['correct'] or 0
                    
                    if total >= 1:  # 至少有1次预测就返回数据
                        return {
                            'win_rate': correct / total if total > 0 else default_win_rate,
                            'total_predictions': total,
                            'correct_predictions': correct,
                            'source': 'symbol_specific',
                            'symbol': symbol
                        }
                
                # 2. 如果没有特定股票数据或数据不足，获取该研究员的平均胜率
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct
                    FROM research_records
                    WHERE researcher_name = ?
                    AND outcome != 'pending'
                ''', (researcher_name,))
                
                row = cursor.fetchone()
                total = row['total'] or 0
                correct = row['correct'] or 0
                
                if total >= 1:  # 至少有1次预测就返回数据
                    return {
                        'win_rate': correct / total if total > 0 else default_win_rate,
                        'total_predictions': total,
                        'correct_predictions': correct,
                        'source': 'researcher_average',
                        'symbol': symbol
                    }
                
                # 3. 如果该研究员没有足够数据，获取同类型研究员的平均胜率
                researcher_type = researcher_name.split('_')[0] if '_' in researcher_name else researcher_name
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct
                    FROM research_records
                    WHERE researcher_type = ?
                    AND outcome != 'pending'
                ''', (researcher_type,))
                
                row = cursor.fetchone()
                total = row['total'] or 0
                correct = row['correct'] or 0
                
                if total >= 1:  # 至少有1次预测就返回数据
                    return {
                        'win_rate': correct / total if total > 0 else default_win_rate,
                        'total_predictions': total,
                        'correct_predictions': correct,
                        'source': 'type_average',
                        'symbol': symbol
                    }
                
                # 4. 返回默认胜率（行业均值）
                return {
                    'win_rate': default_win_rate,
                    'total_predictions': 0,
                    'correct_predictions': 0,
                    'source': 'default',
                    'symbol': symbol
                }
                
        except Exception as e:
            print(f"❌ 获取胜率失败: {e}")
            return {
                'win_rate': default_win_rate,
                'total_predictions': 0,
                'correct_predictions': 0,
                'source': 'default',
                'symbol': symbol
            }


def get_research_tracker(db_path: str = "tradingagents/db/research_tracker.db") -> ResearchTracker:
    """
    获取 ResearchTracker 实例（通过依赖注入容器）
    
    使用依赖注入容器管理单例，支持测试和多实例场景
    
    Args:
        db_path: 数据库路径
        
    Returns:
        ResearchTracker 实例
    """
    container = get_container()
    
    # 如果未注册，则注册并初始化
    if not container.has('research_tracker'):
        container.register('research_tracker', lambda: ResearchTracker(db_path), singleton=True)
    
    return container.get('research_tracker')
