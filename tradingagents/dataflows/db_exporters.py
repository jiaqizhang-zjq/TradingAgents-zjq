"""
数据库导出工具
=============
提供分析报告和工具调用记录的导出功能。
从 database.py 中拆分出来以实现单一职责。
"""

import os
import json
from typing import Optional

from .database import TradingDatabase, AnalysisReport


def export_report_to_markdown(
    db: TradingDatabase,
    symbol: str,
    trade_date: str,
    output_dir: str = "reports"
) -> str:
    """
    将报告导出为 Markdown 文件
    
    Args:
        db: 数据库实例
        symbol: 股票代码
        trade_date: 交易日期
        output_dir: 输出目录
        
    Returns:
        导出的文件路径
    """
    report = db.get_report(symbol, trade_date)
    
    if not report:
        print(f"❌ 未找到报告: {symbol} @ {trade_date}")
        return ""
    
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{symbol}_{trade_date}_report.md"
    filepath = os.path.join(output_dir, filename)
    
    content = f"""# 股票分析报告: {symbol}

**分析日期**: {trade_date}  
**生成时间**: {report.created_at}

---

## 📊 市场分析报告

{report.market_report}

---

## 📈 基本面分析报告

{report.fundamentals_report}

---

## 🕯️ 蜡烛图分析报告

{report.candlestick_report}

---

## 😊 情绪分析报告

{report.sentiment_report}

---

## 📰 新闻分析报告

{report.news_report}

---

## 💼 投资计划

{report.investment_plan}

---

## 🎯 交易员计划

{report.trader_investment_plan}

---

## ✅ 最终交易决策

{report.final_trade_decision}

---

*报告由 TradingAgents 系统自动生成*
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Markdown 报告已导出: {filepath}")
    return filepath


def export_tool_calls_to_jsonl(
    db: TradingDatabase,
    symbol: str,
    trade_date: str,
    output_dir: str = "reports"
) -> str:
    """
    将工具调用记录导出为 JSONL 文件
    
    Args:
        db: 数据库实例
        symbol: 股票代码
        trade_date: 交易日期
        output_dir: 输出目录
        
    Returns:
        导出的文件路径
    """
    tool_calls = db.get_tool_calls(symbol, trade_date)
    
    if not tool_calls:
        print(f"⚠️ 未找到工具调用记录: {symbol} @ {trade_date}")
        return ""
    
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{symbol}_{trade_date}_tool_calls.jsonl"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        for call in tool_calls:
            f.write(json.dumps(call, ensure_ascii=False) + '\n')
    
    print(f"✅ JSONL 工具调用记录已导出: {filepath}")
    return filepath
