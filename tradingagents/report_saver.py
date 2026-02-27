"""
报告保存模块
用于将所有分析报告保存到文件系统，按股票名/日期/报告类型组织
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# 导入依赖注入容器
from tradingagents.core.container import get_container


class ReportSaver:
    """
    报告保存器
    
    目录结构：
    reports/
    ├── LMND/
    │   ├── 2026-02-20/
    │   │   ├── 01_market_analysis.md
    │   │   ├── 02_sentiment_analysis.md
    │   │   ├── 03_news_analysis.md
    │   │   ├── 04_fundamentals_analysis.md
    │   │   ├── 05_candlestick_analysis.md
    │   │   ├── 06_research_debate.md
    │   │   ├── 07_research_manager_decision.md
    │   │   ├── 08_risk_debate.md
    │   │   ├── 09_risk_manager_decision.md
    │   │   └── 10_final_decision.md
    │   └── 2026-02-19/
    │       └── ...
    └── NVDA/
        └── ...
    """
    
    def __init__(self, base_dir: str = "reports"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    def _get_report_dir(self, symbol: str, trade_date: str) -> Path:
        """获取报告目录路径"""
        report_dir = self.base_dir / symbol / trade_date
        report_dir.mkdir(parents=True, exist_ok=True)
        return report_dir
    
    def _save_report(self, report_dir: Path, filename: str, content: str, metadata: Dict = None):
        """保存单个报告文件"""
        filepath = report_dir / filename
        
        # 构建文件内容
        file_content = f"""# {filename.replace('.md', '').replace('_', ' ').title()}

**股票代码**: {report_dir.parent.name}  
**日期**: {report_dir.name}  
**生成时间**: {datetime.now().isoformat()}

---

{content}

"""
        
        # 如果有元数据，添加到文件末尾
        if metadata:
            file_content += "\n---\n\n## 元数据\n\n```json\n"
            file_content += json.dumps(metadata, indent=2, ensure_ascii=False)
            file_content += "\n```\n"
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        print(f"✅ 报告已保存: {filepath}")
        return filepath
    
    def save_analysis_reports(
        self,
        symbol: str,
        trade_date: str,
        market_report: str = "",
        sentiment_report: str = "",
        news_report: str = "",
        fundamentals_report: str = "",
        candlestick_report: str = "",
        investment_debate_state: Dict = None,
        risk_debate_state: Dict = None,
        trader_report: str = "",
        investment_plan: str = "",
        final_trade_decision: str = ""
    ):
        """
        保存所有分析报告
        
        Args:
            symbol: 股票代码
            trade_date: 交易日期
            market_report: 市场分析报告
            sentiment_report: 情绪分析报告
            news_report: 新闻分析报告
            fundamentals_report: 基本面分析报告
            candlestick_report: 蜡烛图分析报告
            investment_debate_state: 投资辩论状态
            risk_debate_state: 风险辩论状态
            trader_report: 交易员报告
            investment_plan: 投资计划
            final_trade_decision: 最终交易决策
        """
        report_dir = self._get_report_dir(symbol, trade_date)
        saved_files = []
        
        # 1. 市场分析报告
        if market_report:
            saved_files.append(self._save_report(
                report_dir, "01_market_analysis.md", market_report,
                {"type": "market_analysis", "symbol": symbol, "date": trade_date}
            ))
        
        # 2. 情绪分析报告
        if sentiment_report:
            saved_files.append(self._save_report(
                report_dir, "02_sentiment_analysis.md", sentiment_report,
                {"type": "sentiment_analysis", "symbol": symbol, "date": trade_date}
            ))
        
        # 3. 新闻分析报告
        if news_report:
            saved_files.append(self._save_report(
                report_dir, "03_news_analysis.md", news_report,
                {"type": "news_analysis", "symbol": symbol, "date": trade_date}
            ))
        
        # 4. 基本面分析报告
        if fundamentals_report:
            saved_files.append(self._save_report(
                report_dir, "04_fundamentals_analysis.md", fundamentals_report,
                {"type": "fundamentals_analysis", "symbol": symbol, "date": trade_date}
            ))
        
        # 5. 蜡烛图分析报告
        if candlestick_report:
            saved_files.append(self._save_report(
                report_dir, "05_candlestick_analysis.md", candlestick_report,
                {"type": "candlestick_analysis", "symbol": symbol, "date": trade_date}
            ))
        
        # 6. 研究员辩论过程
        if investment_debate_state:
            debate_content = self._format_debate_state(investment_debate_state, "研究员辩论")
            if debate_content:
                saved_files.append(self._save_report(
                    report_dir, "06_research_debate.md", debate_content,
                    {"type": "research_debate", "symbol": symbol, "date": trade_date}
                ))
        
        # 7. 研究经理决策
        if investment_debate_state and investment_debate_state.get("judge_decision"):
            saved_files.append(self._save_report(
                report_dir, "07_research_manager_decision.md", 
                investment_debate_state["judge_decision"],
                {"type": "research_manager_decision", "symbol": symbol, "date": trade_date}
            ))
        
        # 8. 风险辩论过程
        if risk_debate_state:
            risk_debate_content = self._format_debate_state(risk_debate_state, "风险辩论")
            if risk_debate_content:
                saved_files.append(self._save_report(
                    report_dir, "08_risk_debate.md", risk_debate_content,
                    {"type": "risk_debate", "symbol": symbol, "date": trade_date}
                ))
        
        # 9. 风险经理决策
        if risk_debate_state and risk_debate_state.get("judge_decision"):
            saved_files.append(self._save_report(
                report_dir, "09_risk_manager_decision.md",
                risk_debate_state["judge_decision"],
                {"type": "risk_manager_decision", "symbol": symbol, "date": trade_date}
            ))
        
        # 10. 交易员报告
        if trader_report:
            saved_files.append(self._save_report(
                report_dir, "10_trader_report.md", trader_report,
                {"type": "trader_report", "symbol": symbol, "date": trade_date}
            ))
        
        # 11. 最终决策
        if final_trade_decision:
            saved_files.append(self._save_report(
                report_dir, "11_final_decision.md", final_trade_decision,
                {"type": "final_decision", "symbol": symbol, "date": trade_date}
            ))
        
        # 保存索引文件
        self._save_index_file(report_dir, symbol, trade_date, saved_files)
        
        print(f"\n✅ 所有报告已保存到: {report_dir}")
        print(f"   共保存 {len(saved_files)} 个文件\n")
        
        return saved_files
    
    def _format_debate_state(self, debate_state: Dict, title: str) -> str:
        """格式化辩论状态为可读文本"""
        if not debate_state:
            return ""
        
        content = f"# {title}\n\n"
        
        # 添加历史记录
        if debate_state.get("history"):
            content += "## 辩论历史\n\n"
            content += debate_state["history"]
            content += "\n\n"
        
        # 添加当前响应
        if debate_state.get("current_response"):
            content += "## 最新观点\n\n"
            content += debate_state["current_response"]
            content += "\n\n"
        
        return content
    
    def _save_index_file(self, report_dir: Path, symbol: str, trade_date: str, saved_files: list):
        """保存索引文件"""
        index_content = f"""# 报告索引

**股票代码**: {symbol}  
**日期**: {trade_date}  
**生成时间**: {datetime.now().isoformat()}

## 报告列表

| 序号 | 报告名称 | 文件路径 |
|------|----------|----------|
"""
        
        for i, filepath in enumerate(saved_files, 1):
            filename = filepath.name
            report_name = filename.replace('.md', '').replace('_', ' ').title()
            index_content += f"| {i} | {report_name} | `{filename}` |\n"
        
        index_content += f"""

## 目录结构

```
{symbol}/
└── {trade_date}/
"""
        
        for filepath in saved_files:
            index_content += f"    ├── {filepath.name}\n"
        
        index_content += "```\n"
        
        # 写入索引文件
        index_path = report_dir / "00_index.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        print(f"✅ 索引文件已保存: {index_path}")
    
    def get_report_history(self, symbol: str = None, limit: int = 100) -> list:
        """
        获取历史报告列表
        
        Args:
            symbol: 按股票筛选，为None则返回所有
            limit: 返回数量限制
            
        Returns:
            报告历史列表
        """
        history = []
        
        if symbol:
            # 获取特定股票的报告
            symbol_dir = self.base_dir / symbol
            if symbol_dir.exists():
                for date_dir in sorted(symbol_dir.iterdir(), reverse=True):
                    if date_dir.is_dir():
                        history.append({
                            "symbol": symbol,
                            "date": date_dir.name,
                            "path": str(date_dir),
                            "reports": [f.name for f in date_dir.glob("*.md")]
                        })
        else:
            # 获取所有股票的报告
            for symbol_dir in self.base_dir.iterdir():
                if symbol_dir.is_dir():
                    for date_dir in sorted(symbol_dir.iterdir(), reverse=True):
                        if date_dir.is_dir():
                            history.append({
                                "symbol": symbol_dir.name,
                                "date": date_dir.name,
                                "path": str(date_dir),
                                "reports": [f.name for f in date_dir.glob("*.md")]
                            })
        
        # 按日期排序并限制数量
        history.sort(key=lambda x: x["date"], reverse=True)
        return history[:limit]


def get_report_saver(base_dir: str = "reports") -> ReportSaver:
    """
    获取 ReportSaver 实例（通过依赖注入容器）
    
    使用依赖注入容器管理单例，支持测试和多实例场景
    """
    container = get_container()
    
    # 如果未注册，则注册并初始化
    if not container.has('report_saver'):
        container.register('report_saver', lambda: ReportSaver(base_dir), singleton=True)
    
    return container.get('report_saver')
