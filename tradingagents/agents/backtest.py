#!/usr/bin/env python3
"""
回测脚本 - 使用最新股价验证研究员的预测收益
使用项目中已配置的数据源

架构说明（v2.0 模块化重构）：
- backtest_utils.py: 计算工具（价格获取、收益计算、预测判断）
- backtest_stats.py: 统计报告（打印统计分析）
- 本文件: 主回测逻辑
"""

import os
import sqlite3
from datetime import datetime
import sys
import json
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from tradingagents.constants import DEFAULT_DB_PATH  # noqa: E402

DB_PATH = os.path.join(PROJECT_ROOT, DEFAULT_DB_PATH)

# 加载环境变量
load_dotenv()

# 从工具模块导入
from tradingagents.agents.backtest_utils import (
    get_price_on_date,
    calculate_return,
    calculate_profit,
    calculate_shares,
    is_market_open,
    determine_outcome,
)
from tradingagents.agents.backtest_stats import (
    print_records,
    print_backtest_stats,
)
from tradingagents.utils.logger import get_logger
from tradingagents.constants import DEFAULT_INITIAL_CAPITAL, MIN_STOCK_DATA_DAYS

logger = get_logger(__name__)


def _ensure_table_schema(cursor, conn):
    """确保表结构正确"""
    try:
        cursor.execute("ALTER TABLE research_records ADD COLUMN buy_price REAL")
        cursor.execute(f"ALTER TABLE research_records ADD COLUMN initial_capital REAL DEFAULT {DEFAULT_INITIAL_CAPITAL}")
        cursor.execute("ALTER TABLE research_records ADD COLUMN shares REAL")
        cursor.execute("ALTER TABLE research_records ADD COLUMN total_return REAL")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # 列已存在，忽略


def _get_last_trade_date(cursor, target_date: str, symbol: str = None) -> str:
    """找出目标日期的前一个有记录的trade_date"""
    if symbol:
        cursor.execute("""
            SELECT DISTINCT trade_date FROM research_records 
            WHERE trade_date < ? 
            AND prediction IN ('BUY', 'SELL', 'HOLD')
            AND symbol = ?
            ORDER BY trade_date DESC
            LIMIT 1
        """, (target_date, symbol))
    else:
        cursor.execute("""
            SELECT DISTINCT trade_date FROM research_records 
            WHERE trade_date < ? 
            AND prediction IN ('BUY', 'SELL', 'HOLD')
            ORDER BY trade_date DESC
            LIMIT 1
        """, (target_date,))
    
    row = cursor.fetchone()
    return row[0] if row else None


def _fetch_pending_records(cursor, last_date: str, symbol: str = None):
    """获取待回测记录"""
    if symbol:
        cursor.execute("""
            SELECT id, researcher_name, researcher_type, symbol, trade_date, prediction, 
                   confidence, holding_days, buy_price, initial_capital, shares, metadata
            FROM research_records
            WHERE trade_date = ? AND prediction IN ('BUY', 'SELL', 'HOLD') AND symbol = ?
            ORDER BY researcher_name
        """, (last_date, symbol))
    else:
        cursor.execute("""
            SELECT id, researcher_name, researcher_type, symbol, trade_date, prediction, 
                   confidence, holding_days, buy_price, initial_capital, shares, metadata
            FROM research_records
            WHERE trade_date = ? AND prediction IN ('BUY', 'SELL', 'HOLD')
            ORDER BY researcher_name
        """, (last_date,))
    
    return cursor.fetchall()


def _backfill_buy_prices(cursor, conn, records):
    """回填空的买入价格"""
    unique_symbols = set()
    for record in records:
        record_id, _, _, sym, trade_date, _, _, _, buy_price, _, _, _ = record
        if buy_price is None or buy_price == 0:
            unique_symbols.add((sym, trade_date))

    price_cache = {}
    for sym, trade_date in unique_symbols:
        price = get_price_on_date(sym, trade_date)
        if price and price > 0:
            price_cache[(sym, trade_date)] = price
            logger.info("获取价格 %s @ %s: $%.2f", sym, trade_date, price)
        else:
            logger.warning("%s %s: 无法获取买入价格", sym, trade_date)

    logger.info("-" * 130)

    for record in records:
        record_id, _, _, sym, trade_date, _, _, _, buy_price, initial_capital, shares, _ = record

        if buy_price is None or buy_price == 0:
            buy_price = price_cache.get((sym, trade_date))
            if buy_price is None or buy_price == 0:
                logger.warning("%s %s: 无法获取买入价格，跳过", sym, trade_date)
                continue

            if initial_capital is None:
                initial_capital = DEFAULT_INITIAL_CAPITAL
            if shares is None or shares == 0:
                shares = calculate_shares(buy_price, initial_capital)

            cursor.execute("""
                UPDATE research_records
                SET buy_price = ?, initial_capital = ?, shares = ?
                WHERE id = ?
            """, (buy_price, initial_capital, shares, record_id))

            logger.info("回填 %s %s: 买入价格 $%.2f, 股数 %.2f", sym, trade_date, buy_price, shares)

    conn.commit()


def _calculate_and_update_returns(cursor, conn, records, verify_date: str) -> int:
    """计算收益并更新数据库"""
    logger.info("开始计算收益...")
    logger.info("-" * 130)

    # 批量获取验证日期价格
    verify_prices = {}
    for record in records:
        _, _, _, sym, _, _, _, _, _, _, _, _ = record
        if (sym, verify_date) not in verify_prices:
            price = get_price_on_date(sym, verify_date)
            if price:
                verify_prices[(sym, verify_date)] = price

    updated_count = 0
    for record in records:
        record_id, researcher_name, _, sym, trade_date, prediction, _, holding_days, buy_price, initial_capital, shares, metadata = record

        current_price = verify_prices.get((sym, verify_date))
        if current_price is None:
            logger.warning("%s %s: 无法获取验证价格，跳过", sym, verify_date)
            continue

        actual_return = calculate_return(buy_price, current_price)

        if prediction == "SELL":
            short_return = (buy_price - current_price) / buy_price
            total_return = initial_capital * short_return
        else:
            total_return = calculate_profit(buy_price, current_price, initial_capital)

        if prediction == "HOLD":
            total_return = calculate_profit(buy_price, current_price, initial_capital)

        outcome = determine_outcome(prediction, actual_return, buy_price, current_price)

        # 更新metadata
        meta = {}
        if metadata:
            try:
                meta = json.loads(metadata) if isinstance(metadata, str) else metadata
            except (json.JSONDecodeError, TypeError):
                logger.warning("记录 %s metadata 解析失败，使用空字典", record_id)

        meta["position_change"] = {
            "action": prediction,
            "shares": shares,
            "buy_price": buy_price,
            "current_price": current_price,
            "total_return": total_return,
            "verified_date": verify_date
        }

        cursor.execute("""
            UPDATE research_records
            SET outcome = ?, actual_return = ?, total_return = ?,
                verified_date = ?, holding_days = ?, buy_price = ?,
                shares = ?, metadata = ?, backtest_date = ?, backtest_price = ?
            WHERE id = ?
        """, (outcome, actual_return, total_return, verify_date, holding_days,
              buy_price, shares, json.dumps(meta), verify_date, current_price, record_id))

        return_str = f"{actual_return*100:+.2f}%" if actual_return is not None else "N/A"
        profit_str = f"${total_return:+.2f}" if total_return is not None else "N/A"
        shares_str = f"{shares:.2f}" if shares else "0.00"

        logger.info("%6s | %s | %4s | 买入: $%.2f | 股数: %8s | 当前: $%.2f | 收益率: %10s | 总收益: %12s | %s",
                    sym, trade_date, prediction, buy_price, shares_str, current_price, return_str, profit_str, outcome)

        updated_count += 1

    conn.commit()
    return updated_count


def _update_memory_system(db_path: str):
    """更新内存系统"""
    logger.info("=" * 50)
    logger.info("🧠 更新内存系统...")
    logger.info("=" * 50)

    try:
        from tradingagents.agents.utils.memory import FinancialSituationMemory
        from tradingagents.constants import RESEARCHER_REGISTRY

        # 从注册表动态获取所有 researcher type + 固定角色
        memory_names = [info["type"] for info in RESEARCHER_REGISTRY.values()]
        memory_names.extend(["trader", "research_manager", "risk_manager"])

        for name in memory_names:
            memory = FinancialSituationMemory(name, {"db_path": db_path})
            memory.learn_from_research_records()
            logger.info("✅ %s 内存已更新", name)
    except Exception as e:
        logger.error("更新内存系统失败: %s", e)
        import traceback
        logger.debug("错误详情: %s", traceback.format_exc())


def run_backtest(symbol: str = None, target_date: str = None, db_path: str = DB_PATH, debug: bool = False):
    """
    执行回测
    
    Args:
        symbol: 股票代码（可选，None表示全部）
        target_date: 目标日期（可选，None表示今天）
        db_path: 数据库路径
        debug: 是否输出调试信息
    """
    # 检查指定日期是否开盘
    if not is_market_open(symbol, target_date):
        if debug:
            logger.info("⏰ %s 非开盘时间，跳过回测", target_date or '当前')
        return

    if not target_date:
        target_date = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    _ensure_table_schema(cursor, conn)

    # 回测前输出记录
    print_records(cursor, symbol, target_date, "回测前")

    # 找出前一个交易日期
    last_date = _get_last_trade_date(cursor, target_date, symbol)
    if not last_date:
        logger.info("没有可回测的历史记录")
        conn.close()
        return

    logger.info("回测日期: %s", last_date)
    logger.info("-" * 130)

    # 获取待回测记录
    pending_records = _fetch_pending_records(cursor, last_date, symbol)
    logger.info("找到 %d 条待回测记录 (BUY/SELL/HOLD)", len(pending_records))

    # 第一步：回填买入价格
    _backfill_buy_prices(cursor, conn, pending_records)

    # 重新获取记录（买入价格可能已更新）
    records = _fetch_pending_records(cursor, last_date, symbol)

    # 第二步：计算收益
    updated_count = _calculate_and_update_returns(cursor, conn, records, target_date)

    conn.close()

    # 回测后输出记录
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print_records(cursor, symbol, target_date, "回测后")
    conn.close()

    logger.info("-" * 130)
    logger.info("回测完成！更新了 %d 条记录", updated_count)

    # 更新内存系统
    _update_memory_system(db_path)

    # 打印统计
    logger.info("=== 回测统计 ===")
    print_backtest_stats(db_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="回测研究员的预测收益")
    parser.add_argument("--db", default="research_tracker.db", help="数据库路径")

    args = parser.parse_args()

    run_backtest(args.db)
