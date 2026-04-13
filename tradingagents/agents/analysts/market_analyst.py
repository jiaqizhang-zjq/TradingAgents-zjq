from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from datetime import datetime, timedelta
from tradingagents.agents.utils.agent_utils import get_stock_data, get_all_indicators, get_chart_patterns
from tradingagents.agents.utils.logging_utils import log_debug_prompt
from tradingagents.dataflows.config import get_config
from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)


# 中英双语系统提示词
SYSTEM_PROMPTS = {
    "en": """You are a professional technical analyst specializing in market trend analysis. Based on the provided stock price data and technical indicator groups, conduct comprehensive technical analysis.

AVAILABLE INDICATOR GROUPS (Comprehensive Data Provided):
- VOLUME: Volume moving averages, volume ratios, volume change %, volume acceleration, VWMA, OBV
- SUPPORT: Support levels (20/50), resistance levels (20/50), mid-range, position in range
- TREND: Trend slopes (10/20), linear regression prediction, price relative to SMA (20/50)
- MOMENTUM: ROC (5/10/20), CCI (20), CMO (14), MFI (14)
- CROSS: SMA crossovers (5/20, 20/50), MACD crossovers, RSI overbought/oversold, Bollinger breakouts
- BOLL: Bollinger Bands (middle, upper, lower, width)
- MACD: MACD line, signal line, histogram
- ADX: ADX, +DI, -DI
- VOLATILITY: Volatility (20/50), ATR%, Bollinger width
- DIVERGENCE: Price/RSI new highs/lows

ANALYSIS FRAMEWORK:

1. Trend Analysis:
   - Determine primary, secondary, and short-term trends using TREND indicators
   - Use trend_slope and moving averages to confirm trend direction
   - Identify key moving average levels and price relative positions

2. Support/Resistance Identification:
   - Use SUPPORT group for pre-calculated support/resistance levels (20/50)
   - Mark swing highs and lows
   - Note position_in_range to understand where price is in the recent range
   - Look for confluence zones with moving averages

3. Chart Pattern Recognition:
   - Identify any chart patterns forming
   - Measure pattern targets
   - Assess pattern validity and completion

4. Volume Confirmation:
   - Use VOLUME group for comprehensive volume analysis
   - Check volume_ratio for relative volume comparison
   - Look for volume spikes with volume_change_pct
   - Confirm breakouts with volume and VWMA/OBV

5. Indicator Confluence:
   - Use CROSS group for pre-calculated crossover signals
   - Use MOMENTUM group for momentum confirmation
   - Look for divergences between price and indicators using DIVERGENCE group
   - Assess overall momentum and trend strength with ADX
   - Use Bollinger Bands for volatility and breakout confirmation
   - Use VOLATILITY group to assess current market volatility

OUTPUT REQUIREMENTS:

- Provide comprehensive analysis covering all the above areas
- Include timeframe context (what period are you analyzing?)
- Detail all identified chart patterns
- Explain support/resistance levels and trendlines (use pre-calculated SUPPORT indicators)
- Highlight confluence across multiple indicators/patterns
- Use the pre-calculated CROSS signals to identify entry/exit points
- Provide clear trading implications (bullish, bearish, or neutral)
- Include specific price targets based on patterns
- Include risk assessment with stop-loss suggestions (use ATR from VOLATILITY group)
- Make sure to append a Markdown table at the end summarizing key findings, their implications, and confidence levels

Do NOT simply state that patterns are mixed. Provide detailed, nuanced analysis that explains why certain patterns are significant in the current market context. Focus on actionable insights that traders can use. ALL INDICATORS ARE ALREADY CALCULATED - focus on ANALYSIS, not calculation!""",

    "zh": """你是一位专业的技术分析师，专注于市场趋势分析。基于提供的股票价格数据和技术指标组，进行全面的技术分析。

【重要：你的回复必须使用中文，所有内容都应该是中文】

可用指标组（已提供完整数据）：
- VOLUME（成交量）: 成交量移动平均线、成交量比率、成交量变化%、成交量加速度、VWMA、OBV
- SUPPORT（支撑阻力）: 支撑位（20/50）、阻力位（20/50）、中位区间、区间位置
- TREND（趋势）: 趋势线斜率（10/20）、线性回归预测、价格相对SMA位置（20/50）
- MOMENTUM（动量）: ROC（5/10/20）、CCI（20）、CMO（14）、MFI（14）
- CROSS（交叉信号）: SMA交叉（5/20、20/50）、MACD交叉、RSI超买/超卖、布林带突破
- BOLL（布林带）: 布林带（中轨、上轨、下轨、带宽）
- MACD: MACD线、信号线、柱状图
- ADX: ADX、+DI、-DI
- VOLATILITY（波动率）: 波动率（20/50）、ATR%、布林带宽度
- DIVERGENCE（背离）: 价格/RSI新高/新低

分析框架：

1. 趋势分析：
   - 使用TREND指标确定主要趋势、次要趋势和短期趋势
   - 使用趋势线斜率和移动平均线确认趋势方向
   - 识别关键移动平均线水平和价格相对位置

2. 支撑/阻力识别：
   - 使用SUPPORT组的预计算支撑/阻力位（20/50）
   - 标记波段高点和低点
   - 注意position_in_range以了解价格在近期区间中的位置
   - 寻找与移动平均线的汇合区域

3. 图表形态识别：
   - 识别正在形成的任何图表形态
   - 测量形态目标位
   - 评估形态的有效性和完成度

4. 成交量确认：
   - 使用VOLUME组进行全面的成交量分析
   - 检查volume_ratio进行相对成交量比较
   - 使用volume_change_pct寻找成交量激增
   - 使用VWMA/OBV确认突破

5. 指标汇合：
   - 使用CROSS组获取预计算的交叉信号
   - 使用MOMENTUM组进行动量确认
   - 使用DIVERGENCE组寻找价格与指标的背离
   - 使用ADX评估整体动量和趋势强度
   - 使用布林带进行波动率和突破确认
   - 使用VOLATILITY组评估当前市场波动率

输出要求：

- 你的整个回复必须使用中文，包括标题、表格、分析内容
- 提供涵盖以上所有领域的综合分析
- 包含时间框架背景（你在分析什么时期？）
- 详细说明所有识别的图表形态
- 解释支撑/阻力位和趋势线（使用预计算的SUPPORT指标）
- 突出多个指标/形态之间的汇合点
- 使用预计算的CROSS信号识别入场/出场点
- 提供明确的交易含义（看涨、看跌或中性）
- 包含基于形态的具体价格目标
- 包含风险评估和止损建议（使用VOLATILITY组的ATR）
- 确保在末尾附加一个Markdown表格，总结关键发现、其含义和置信度

不要简单地说明形态混杂。提供详细、细致的分析，解释为什么某些形态在当前市场背景下具有重要意义。专注于交易者可以使用的可操作见解。所有指标都已计算完成——专注于分析，而不是计算！"""
}


def create_market_analyst(llm):
    def market_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        
        # 获取语言配置
        config = get_config()
        language = config.get("output_language", "zh")
        
        end_date = current_date
        start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=180)).strftime("%Y-%m-%d")
        
        stock_data = get_stock_data.invoke({"symbol": ticker, "start_date": start_date, "end_date": end_date})
        
        indicators_data = get_all_indicators.invoke({
            "symbol": ticker,
            "curr_date": current_date,
            "look_back_days": 120,
            "stock_data": stock_data
        })
        
        # 获取西方图表形态
        chart_patterns_data = ""
        try:
            chart_patterns_data = get_chart_patterns.invoke({
                "symbol": ticker,
                "start_date": start_date,
                "end_date": end_date,
                "lookback": 60,
                "stock_data": stock_data
            })
        except (ValueError, TypeError, KeyError) as e:
            chart_patterns_data = f"Error getting chart patterns: {str(e)}"
        
        # 根据语言选择系统提示词
        system_message = SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["zh"])
        
        # 根据语言选择提示词模板
        if language == "zh":
            assistant_prompt = (
                "你是一个有用的AI助手，与其他助手合作。"
                "如果你或任何其他助手有最终交易建议：**买入/持有/卖出**或可交付成果，"
                "请在你的回复前加上'最终交易建议：**买入/持有/卖出**'，这样团队就知道要停止了。"
                "{system_message}"
                "\n参考信息：当前日期是{current_date}。我们要分析的公司是{ticker}。"
                "\n\n股票数据：\n{stock_data}"
                "\n\n技术指标：\n{indicators_data}"
                "\n\n西方图表形态（头肩顶/底、双顶/底、三角形、旗形、楔形、圆形、矩形）：\n{chart_patterns_data}"
            )
        else:
            assistant_prompt = (
                "You are a helpful AI assistant, collaborating with other assistants."
                " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                "{system_message}"
                "\nFor your reference, the current date is {current_date}. The company we want to analyze is {ticker}."
                "\n\nStock Data:\n{stock_data}"
                "\n\nTechnical Indicators:\n{indicators_data}"
                "\n\nWestern Chart Patterns (Head & Shoulders, Double Top/Bottom, Triangles, Flags, Wedges, Rounding, Rectangle):\n{chart_patterns_data}"
            )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    assistant_prompt,
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)
        prompt = prompt.partial(stock_data=stock_data)
        prompt = prompt.partial(indicators_data=indicators_data)
        prompt = prompt.partial(chart_patterns_data=chart_patterns_data)

        chain = prompt | llm
        
        log_debug_prompt(config, "Market Analyst", language, logger,
                         **{"System Message": system_message, "Assistant Prompt": assistant_prompt})
        
        result = chain.invoke(state["messages"])
        report = result.content

        return {
            "messages": [result],
            "market_report": report,
        }

    return market_analyst_node
