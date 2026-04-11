"""
回测统计报告
============
提供回测结果的统计分析和打印功能。
"""

import sqlite3
from typing import Optional


def print_records(cursor, symbol: Optional[str], target_date: str, title: str):
    """打印记录列表"""
    print(f"\n=== {title} {symbol or '全部'} {target_date} 的记录 ===")
    
    if symbol:
        cursor.execute("""
            SELECT id, researcher_name, researcher_type, symbol, trade_date, prediction, confidence, 
                   reasoning, outcome, verified_date, actual_return, holding_days, created_at, 
                   metadata, buy_price, initial_capital, shares, total_return, backtest_date, backtest_price
            FROM research_records 
            WHERE trade_date <= ? 
            AND prediction IN ('BUY', 'SELL', 'HOLD')
            AND symbol = ?
            ORDER BY symbol, trade_date, researcher_name
        """, (target_date, symbol))
    else:
        cursor.execute("""
            SELECT id, researcher_name, researcher_type, symbol, trade_date, prediction, confidence, 
                   reasoning, outcome, verified_date, actual_return, holding_days, created_at, 
                   metadata, buy_price, initial_capital, shares, total_return, backtest_date, backtest_price
            FROM research_records 
            WHERE trade_date <= ? 
            AND prediction IN ('BUY', 'SELL', 'HOLD')
            ORDER BY symbol, trade_date, researcher_name
        """, (target_date,))
    
    all_records = cursor.fetchall()
    for r in all_records:
        print(f"ID:{r[0]} | {r[3]} | {r[4]} | {r[1]} | {r[5]} | conf:{r[6]} | outcome:{r[8]} | "
              f"buy_price:{r[14]} | shares:{r[16]} | total_return:{r[17]} | "
              f"backtest_date:{r[18]} | backtest_price:{r[19]}")
    print("-" * 130)


def print_backtest_stats(db_path: str):
    """打印回测统计报告"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 按研究员类型统计
    cursor.execute("""
        SELECT 
            researcher_type,
            COUNT(*) as total,
            SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct,
            SUM(CASE WHEN outcome = 'incorrect' THEN 1 ELSE 0 END) as incorrect,
            SUM(CASE WHEN outcome = 'partial' THEN 1 ELSE 0 END) as partial,
            AVG(actual_return) as avg_return,
            SUM(total_return) as total_profit
        FROM research_records 
        WHERE outcome != 'pending'
        GROUP BY researcher_type
    """)
    
    print("\n按研究员类型:")
    print(f"{'类型':15s} | {'总数':5s} | {'正确':5s} | {'错误':5s} | {'部分':5s} | "
          f"{'胜率':8s} | {'平均收益率':12s} | {'总收益':14s}")
    print("-" * 100)
    
    for row in cursor.fetchall():
        researcher_type, total, correct, incorrect, partial, avg_return, total_profit = row
        if total and total > 0:
            win_rate = (correct / total * 100)
            avg_return_str = f"{avg_return*100:+.2f}%" if avg_return else "N/A"
            profit_str = f"${total_profit:+.2f}" if total_profit else "N/A"
            print(f"{researcher_type:15s} | {total:5d} | {correct:5d} | {incorrect:5d} | "
                  f"{partial:5d} | {win_rate:7.1f}% | {avg_return_str:12s} | {profit_str:14s}")
    
    # 按股票统计
    cursor.execute("""
        SELECT 
            symbol,
            COUNT(*) as total,
            SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct,
            AVG(actual_return) as avg_return,
            SUM(total_return) as total_profit
        FROM research_records 
        WHERE outcome != 'pending'
        GROUP BY symbol
    """)
    
    print("\n按股票:")
    print(f"{'股票':8s} | {'总数':5s} | {'正确':5s} | {'胜率':8s} | {'平均收益率':12s} | {'总收益':14s}")
    print("-" * 70)
    
    for row in cursor.fetchall():
        symbol_name, total, correct, avg_return, total_profit = row
        if total and total > 0:
            win_rate = (correct / total * 100)
            avg_return_str = f"{avg_return*100:+.2f}%" if avg_return else "N/A"
            profit_str = f"${total_profit:+.2f}" if total_profit else "N/A"
            print(f"{symbol_name:8s} | {total:5d} | {correct:5d} | {win_rate:7.1f}% | "
                  f"{avg_return_str:12s} | {profit_str:14s}")
    
    # 总利润统计
    cursor.execute("""
        SELECT 
            SUM(total_return) as total_profit,
            AVG(actual_return) as avg_return
        FROM research_records 
        WHERE outcome != 'pending'
    """)
    
    row = cursor.fetchone()
    if row:
        total_profit, avg_return = row
        print(f"\n总收益: ${total_profit:+.2f}" if total_profit else "\n总收益: N/A")
        print(f"平均收益率: {avg_return*100:+.2f}%" if avg_return else "平均收益率: N/A")
    
    conn.close()
