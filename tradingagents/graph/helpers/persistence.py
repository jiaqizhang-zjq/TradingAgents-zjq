"""
状态持久化模块（从trading_graph.py提取）

负责：
- 保存状态到数据库
- 保存状态到文件
- 记录研究员预测
"""

import json
from datetime import datetime
from typing import Dict, Any

from tradingagents.dataflows.database import AnalysisReport, get_db
from tradingagents.dataflows.research_tracker import get_research_tracker
from tradingagents.report_saver import get_report_saver
from tradingagents.agents.utils.agent_utils import is_market_open


class StatePersistence:
    """状态持久化管理器"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    def save_all(self, final_state: Dict[str, Any]):
        """保存所有状态（数据库+文件+追踪）"""
        self._save_to_database(final_state)
        self._record_research_predictions(final_state)
    
    def _save_to_database(self, final_state: Dict[str, Any]):
        """保存分析结果到数据库"""
        symbol = final_state["company_of_interest"]
        trade_date = final_state["trade_date"]
        
        # 检查指定日期是否开盘
        if not is_market_open(symbol, trade_date):
            if self.debug:
                print(f"⏰ {trade_date} 非开盘时间，跳过保存数据库")
            return
        
        try:
            db = get_db()
            
            # Create report object
            report = AnalysisReport(
                symbol=symbol,
                trade_date=trade_date,
                created_at=datetime.now().isoformat(),
                market_report=final_state.get("market_report", ""),
                fundamentals_report=final_state.get("fundamentals_report", ""),
                candlestick_report=final_state.get("candlestick_report", ""),
                sentiment_report=final_state.get("sentiment_report", ""),
                news_report=final_state.get("news_report", ""),
                investment_plan=final_state.get("investment_plan", ""),
                trader_investment_plan=final_state.get("trader_investment_plan", ""),
                final_trade_decision=final_state.get("final_trade_decision", ""),
                tool_calls_jsonl="",
                metadata=json.dumps({
                    "source": "TradingAgentsGraph",
                    "saved_at": datetime.now().isoformat()
                })
            )
            
            # Save to database
            success = db.save_analysis_report(report)
            
            if success:
                print(f"✅ 分析结果已保存到数据库: {symbol} @ {trade_date}")
                self._save_to_files(final_state)
            else:
                print(f"❌ 保存到数据库失败")
                
        except Exception as e:
            print(f"❌ 数据库保存错误: {e}")
    
    def _save_to_files(self, final_state: Dict[str, Any]):
        """保存分析结果到文件"""
        try:
            saver = get_report_saver()
            
            symbol = final_state["company_of_interest"]
            trade_date = final_state["trade_date"]
            
            # Get debate states
            investment_debate_state = final_state.get("investment_debate_state", {})
            risk_debate_state = final_state.get("risk_debate_state", {})
            
            # Save all reports
            saver.save_analysis_reports(
                symbol=symbol,
                trade_date=trade_date,
                market_report=final_state.get("market_report", ""),
                sentiment_report=final_state.get("sentiment_report", ""),
                news_report=final_state.get("news_report", ""),
                fundamentals_report=final_state.get("fundamentals_report", ""),
                candlestick_report=final_state.get("candlestick_report", ""),
                investment_debate_state=investment_debate_state,
                risk_debate_state=risk_debate_state,
                trader_report=final_state.get("trader_investment_plan", ""),
                investment_plan=final_state.get("investment_plan", ""),
                final_trade_decision=final_state.get("final_trade_decision", "")
            )
                
        except Exception as e:
            print(f"❌ 文件保存错误: {e}")
    
    def _record_research_predictions(self, final_state: Dict[str, Any]):
        """记录研究员预测（用于胜率追踪）"""
        symbol = final_state["company_of_interest"]
        trade_date = final_state["trade_date"]
        
        # 检查指定日期是否开盘
        if not is_market_open(symbol, trade_date):
            if self.debug:
                print(f"⏰ {trade_date} 非开盘时间，跳过记录预测")
            return
        
        try:
            tracker = get_research_tracker()
            
            # Extract investment debate state
            invest_debate = final_state.get("investment_debate_state", {})
            risk_debate = final_state.get("risk_debate_state", {})
            
            # Record all researchers
            self._record_bull_bear(tracker, symbol, trade_date, invest_debate)
            self._record_risk_analysts(tracker, symbol, trade_date, risk_debate)
            self._record_trader(tracker, symbol, trade_date, final_state)
            
            print(f"✅ 研究员预测已记录到胜率追踪器")
            
        except Exception as e:
            print(f"❌ 记录研究员预测失败: {e}")
    
    def _record_bull_bear(self, tracker, symbol: str, trade_date: str, invest_debate: Dict):
        """记录多空研究员"""
        # Bull
        bull_prediction = invest_debate.get("bull_prediction", "HOLD")
        bull_confidence = invest_debate.get("bull_confidence", 0.8)
        if bull_prediction:
            tracker.record_research(
                researcher_name="bull_researcher",
                researcher_type="bull",
                symbol=symbol,
                trade_date=trade_date,
                prediction=bull_prediction,
                confidence=bull_confidence,
                reasoning=invest_debate.get("bull_history", "")
            )
        
        # Bear
        bear_prediction = invest_debate.get("bear_prediction", "HOLD")
        bear_confidence = invest_debate.get("bear_confidence", 0.8)
        if bear_prediction:
            tracker.record_research(
                researcher_name="bear_researcher",
                researcher_type="bear",
                symbol=symbol,
                trade_date=trade_date,
                prediction=bear_prediction,
                confidence=bear_confidence,
                reasoning=invest_debate.get("bear_history", "")
            )
        
        # Research Manager
        manager_prediction = invest_debate.get("research_manager_prediction", "HOLD")
        manager_confidence = invest_debate.get("research_manager_confidence", 0.85)
        if manager_prediction:
            tracker.record_research(
                researcher_name="research_manager",
                researcher_type="manager",
                symbol=symbol,
                trade_date=trade_date,
                prediction=manager_prediction,
                confidence=manager_confidence,
                reasoning=invest_debate.get("judge_decision", "")
            )
    
    def _record_risk_analysts(self, tracker, symbol: str, trade_date: str, risk_debate: Dict):
        """记录风险分析师"""
        analysts = [
            ("aggressive_risk", "aggressive", "aggressive_prediction", "aggressive_confidence", "aggressive_history"),
            ("conservative_risk", "conservative", "conservative_prediction", "conservative_confidence", "conservative_history"),
            ("neutral_risk", "neutral", "neutral_prediction", "neutral_confidence", "neutral_history"),
            ("risk_manager", "risk_manager", "risk_manager_prediction", "risk_manager_confidence", "judge_decision"),
        ]
        
        for name, type_, pred_key, conf_key, reason_key in analysts:
            prediction = risk_debate.get(pred_key, "HOLD")
            confidence = risk_debate.get(conf_key, 0.75)
            if prediction:
                tracker.record_research(
                    researcher_name=name,
                    researcher_type=type_,
                    symbol=symbol,
                    trade_date=trade_date,
                    prediction=prediction,
                    confidence=confidence,
                    reasoning=risk_debate.get(reason_key, "")
                )
    
    def _record_trader(self, tracker, symbol: str, trade_date: str, final_state: Dict):
        """记录交易员决策"""
        trader_prediction = final_state.get("trader_prediction", "HOLD")
        trader_confidence = final_state.get("trader_confidence", 0.9)
        tracker.record_research(
            researcher_name="trader",
            researcher_type="trader",
            symbol=symbol,
            trade_date=trade_date,
            prediction=trader_prediction,
            confidence=trader_confidence,
            reasoning=final_state.get("final_trade_decision", "")
        )
