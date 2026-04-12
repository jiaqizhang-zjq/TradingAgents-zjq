# TradingAgents 数据库文档

## 概述

本文档描述 TradingAgents 系统中使用的 SQLite 数据库 `research_tracker.db` 的结构和内容。

## 数据库文件

### 1. research_tracker.db
- **文件名**: `research_tracker.db`
- **位置**: 项目根目录
- **用途**: 存储研究员预测、回测结果和内存记录

### 2. trading_analysis.db
- **文件名**: `trading_analysis.db`
- **位置**: `tradingagents/db/`
- **用途**: 存储完整的分析报告和工具调用数据

---

## 数据表结构

### 1. research_records (研究记录表)

**用途**: 存储所有研究员/Agent 的分析决策记录

**表结构**:

| 字段 | 类型 | 描述 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| researcher_name | TEXT | 研究员名称 (如 bull_researcher, bear_researcher, research_manager, trader) |
| researcher_type | TEXT | 研究员类型 (bull/bear/manager/trader/aggressive/conservative/neutral) |
| symbol | TEXT | 股票代码 (如 LMND, RKLB, TSLA, NVDA 等) |
| trade_date | TEXT | 交易日期 (格式: YYYY-MM-DD) |
| prediction | TEXT | 预测结果 (BUY/SELL/HOLD) |
| confidence | REAL | 置信度 (0.0-1.0) |
| reasoning | TEXT | 推理过程/报告内容 |
| outcome | TEXT | 结果状态 (pending/correct/incorrect/partial) |
| verified_date | TEXT | 验证日期 |
| actual_return | REAL | 实际收益率 (百分比，如 0.05 表示 5%) |
| total_return | REAL | 总收益金额 (如 $500 表示盈利 500 美元) |
| holding_days | INTEGER | 持有天数 (默认5天) |
| created_at | TEXT | 创建时间 |
| metadata | TEXT | 额外元数据 (JSON格式，包含头寸变化详情) |
| buy_price | REAL | 买入价格 (交易当天收盘价) |
| initial_capital | REAL | 初始资金 (默认 10000 美元) |
| shares | REAL | 头寸数量 (股数) |

**metadata JSON 结构示例**:
```json
{
  "position_change": {
    "action": "BUY",
    "shares": 100.5,
    "buy_price": 99.5,
    "current_price": 105.2,
    "total_return": 573.85,
    "verified_date": "2026-02-25"
  }
}
```

**索引**:
- `idx_research_records_symbol_date`: (symbol, trade_date)
- `idx_research_records_researcher`: (researcher_name)
- `idx_research_records_outcome`: (outcome)

---

### 2. researcher_configs (研究员配置表)

**用途**: 存储研究员的配置信息

**表结构**:

| 字段 | 类型 | 描述 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| researcher_name | TEXT | 研究员名称 (唯一) |
| researcher_type | TEXT | 研究员类型 |
| description | TEXT | 描述 |
| is_active | BOOLEAN | 是否激活 |
| created_at | TEXT | 创建时间 |
| config_json | TEXT | 配置 JSON |

**当前状态**: 表为空

---

### 3. stock_returns (股票收益表)

**用途**: 存储股票的历史收益数据

**表结构**:

| 字段 | 类型 | 描述 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| symbol | TEXT | 股票代码 |
| trade_date | TEXT | 交易日期 |
| holding_days | INTEGER | 持有天数 |
| return_rate | REAL | 收益率 |
| close_price | REAL | 收盘价 |
| future_price | REAL | 未来价格 |
| created_at | TEXT | 创建时间 |

**索引**:
- `idx_stock_returns_symbol_date`: (symbol, trade_date)

**当前状态**: 表为空

---

### 4. memory_records (内存记录表)

**用途**: 存储各角色的历史经验和记忆，用于BM25相似性匹配

**表结构**:

| 字段 | 类型 | 描述 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| memory_name | TEXT | 内存实例名称 (如 bull_researcher, bear_researcher, trader) |
| situation | TEXT | 完整的市场情境描述 (包含5份专家报告) |
| recommendation | TEXT | 建议内容 (包含角色、预测、推理和收益) |
| actual_return | REAL | 实际收益率 |
| symbol | TEXT | 股票代码 |
| trade_date | TEXT | 交易日期 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

**索引**:
- `idx_memory_records_memory_name`: (memory_name)

**数据来源**:
- 从 `research_records` 表获取已验证的预测记录
- 从 `analysis_reports` 表获取完整的市场报告
- 自动在回测后生成

---

## trading_analysis.db 表结构

### 1. analysis_reports (分析报告表)

**用途**: 存储完整的5份专家报告和交易决策

**表结构**:

| 字段 | 类型 | 描述 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| symbol | TEXT | 股票代码 |
| trade_date | TEXT | 交易日期 |
| created_at | TEXT | 创建时间 |
| market_report | TEXT | 市场分析师报告 (Markdown格式) |
| fundamentals_report | TEXT | 基本面分析师报告 (Markdown格式) |
| candlestick_report | TEXT | 蜡烛图分析师报告 (Markdown格式) |
| sentiment_report | TEXT | 情绪分析师报告 (Markdown格式) |
| news_report | TEXT | 新闻分析师报告 (Markdown格式) |
| investment_plan | TEXT | 投资计划 |
| trader_investment_plan | TEXT | 交易员投资计划 |
| final_trade_decision | TEXT | 最终交易决策 |
| tool_calls_jsonl | TEXT | 工具调用原始数据 (JSONL格式) |
| metadata | TEXT | 元数据 (JSON格式) |

**唯一约束**:
- `UNIQUE(symbol, trade_date)`

**数据来源**:
- 股票分析完成时自动生成
- 包含完整的5份专家报告

### 2. tool_calls (工具调用表)

**用途**: 存储详细的工具调用记录

**表结构**:
| 字段 | 类型 | 描述 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| report_id | INTEGER | 关联 analysis_reports.id |
| tool_name | TEXT | 工具名称 |
| input_params | TEXT | 输入参数 (JSON格式) |
| output_result | TEXT | 输出结果 (JSON格式) |
| timestamp | TEXT | 调用时间戳 |
| duration_ms | INTEGER | 执行时长 (毫秒) |

**索引**:
- 关联 analysis_reports 表

---

## 数据统计

### 已分析的股票

| 股票代码 | 分析日期 | 记录数 |
|----------|----------|--------|
| LMND | 2026-02-20 | 9条 |
| LMND | 2026-02-23 | 9条 |
| RKLB | 2026-02-20 | 9条 |
| RKLB | 2026-02-23 | 9条 |
| AAPL | 2026-02-20 | 1条 |
| APLD | 2026-02-20 | 9条 |
| APLD | 2026-02-23 | 9条 |
| TSLA | 2026-02-23 | 9条 |
| NVDA | 2026-02-23 | 9条 |
| INTC | 2026-02-23 | 9条 |
| IREN | 2026-02-23 | 9条 |
| KTOS | 2026-02-23 | 9条 |

### 研究员类型分布

| 研究员类型 | 说明 |
|------------|------|
| bull_0 | 初级看涨分析师 |
| bear_0 | 初级看跌分析师 |
| bull_researcher | 高级看涨研究员 |
| bear_researcher | 高级看跌研究员 |
| research_manager | 研究经理 |
| aggressive_risk | 激进型风控 |
| conservative_risk | 保守型风控 |
| neutral_risk | 中性风控 |
| trader | 交易员 |

### 预测结果分布

所有记录的预测结果和置信度:

| researcher_name | type | symbol | date | prediction | confidence | outcome |
|-----------------|------|--------|------|------------|------------|---------|
| bull_0 | bull | LMND | 2026-02-20 | BUY | 0.75 | pending |
| bear_0 | bear | LMND | 2026-02-20 | SELL | 0.78 | pending |
| bull_researcher | bull | LMND | 2026-02-20 | HOLD | 0.80 | pending |
| bear_researcher | bear | LMND | 2026-02-20 | HOLD | 0.80 | pending |
| research_manager | manager | LMND | 2026-02-20 | HOLD | 0.85 | pending |
| bull_0 | bull | RKLB | 2026-02-20 | BUY | 0.65 | pending |
| bear_0 | bear | RKLB | 2026-02-20 | SELL | 0.65 | pending |
| bull_researcher | bull | RKLB | 2026-02-20 | HOLD | 0.80 | pending |
| bear_researcher | bear | RKLB | 2026-02-20 | HOLD | 0.80 | pending |
| research_manager | manager | RKLB | 2026-02-20 | HOLD | 0.85 | pending |
| bull_researcher | bull | RKLB | 2026-02-23 | BUY | 0.80 | pending |
| bear_researcher | bear | RKLB | 2026-02-23 | HOLD | 0.80 | pending |
| research_manager | manager | RKLB | 2026-02-23 | HOLD | 0.85 | pending |
| bull_researcher | bull | NVDA | 2026-02-23 | BUY | 0.80 | pending |
| bear_researcher | bear | NVDA | 2026-02-23 | HOLD | 0.80 | pending |
| research_manager | manager | NVDA | 2026-02-23 | HOLD | 0.85 | pending |
| trader | trader | RKLB | all | HOLD | 0.90 | pending |

---

## 数据流程

```
1. 运行 TradingAgentsGraph.propagate(ticker, date)
   ↓
2. 各 Agent 执行分析 (bull_0, bear_0, analysts...)
   ↓
3. 保存分析报告到 research_records 表
   ↓
4. 等待 holding_days (默认5天)
   ↓
5. 获取实际股价，计算 return_rate
   ↓
6. 更新 outcome (correct/incorrect/partial)
```

---

## 胜率计算

胜率计算逻辑:

```sql
-- 计算每个研究员的胜率
SELECT 
    researcher_name,
    researcher_type,
    COUNT(*) as total_predictions,
    SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct_count,
    ROUND(1.0 * SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate
FROM research_records
WHERE outcome != 'pending'
GROUP BY researcher_name
ORDER BY win_rate DESC;
```

---

## 更新日志

- 2026-02-24: 添加 memory_records 表，用于存储各角色的历史经验和记忆
- 2026-02-23: 初始化数据库，创建 research_records 表
- 记录了多个股票 (LMND, RKLB, TSLA, NVDA, AAPL, APLD, INTC, IREN, KTOS) 的分析结果
- 所有记录当前状态为 pending，等待未来验证
