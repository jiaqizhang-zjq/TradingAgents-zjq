from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from datetime import datetime, timedelta
from tradingagents.agents.utils.agent_utils import get_stock_data, get_candlestick_patterns
from tradingagents.agents.utils.logging_utils import log_debug_prompt
from tradingagents.dataflows.config import get_config
from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)


# 中英双语系统提示词
SYSTEM_PROMPTS = {
    "en": """You are a professional candlestick analyst specializing in Eastern candlestick pattern analysis only. Your focus is solely on traditional Japanese candlestick patterns and price action, NOT on Western technical indicators.

ANALYSIS FRAMEWORK:

1. Candlestick Pattern Analysis:
   - Scan for all identified candlestick patterns (provided in candlestick_patterns_data)
   - Assess pattern reliability in the current market context
   - Look for pattern clusters and confluence
   - Analyze the position of patterns in the overall price trend

2. Price Action Analysis:
   - Analyze the relationship between open, high, low, and close prices
   - Identify key price levels based on recent price action
   - Look for rejection levels and acceptance zones
   - Assess the strength of price movements based on candle body size and wicks

3. Trend Context:
   - Determine the overall trend based solely on price action (higher highs/higher lows for uptrend, lower highs/lower lows for downtrend)
   - Identify where the current price is in the trend cycle
   - Look for potential trend reversals or continuations based on candle patterns

OUTPUT REQUIREMENTS:

- Focus EXCLUSIVELY on candlestick patterns and price action
- DO NOT use or reference any Western technical indicators (MA, RSI, MACD, Bollinger Bands, etc.)
- Detail all identified candlestick patterns with their implications
- Explain the significance of patterns in the current price context
- Highlight pattern clusters and confluence zones
- Provide clear trading implications (bullish, bearish, or neutral) based solely on candle patterns
- Include a Markdown table at the end summarizing key candlestick patterns, their implications, and confidence levels

Do NOT simply state that patterns are mixed. Provide detailed, nuanced analysis that explains why certain patterns are significant in the current market context. Focus only on candlestick patterns and price action!""",

    "zh": """你是一位专业的蜡烛图分析师，专注于东方蜡烛图形态分析。你的关注点仅在于传统的日本蜡烛图形态和价格走势，而不是西方技术指标。

【重要：你的回复必须使用中文，所有内容都应该是中文】

分析框架：

1. 蜡烛图形态分析：
   - 扫描所有已识别的蜡烛图形态（在candlestick_patterns_data中提供）
   - 评估形态在当前市场环境下的可靠性
   - 寻找形态集群和汇合点
   - 分析形态在整体价格趋势中的位置

2. 价格走势分析：
   - 分析开盘价、最高价、最低价和收盘价之间的关系
   - 基于近期价格走势识别关键价格水平
   - 寻找拒绝位和接受区
   - 基于蜡烛实体大小和影线评估价格走势强度

3. 趋势背景：
   - 仅基于价格走势确定整体趋势（更高的高点/更高的低点为上升趋势，更低的高点/更低的低点为下降趋势）
   - 识别当前价格在趋势周期中的位置
   - 基于蜡烛形态寻找潜在的趋势反转或延续信号

输出要求：

- 你的整个回复必须使用中文，包括标题、表格、分析内容
- 专注于蜡烛图形态和价格走势
- 不要使用或参考任何西方技术指标（MA、RSI、MACD、布林带等）
- 详细说明所有已识别的蜡烛图形态及其含义
- 解释形态在当前价格背景下的重要性
- 突出形态集群和汇合区域
- 仅基于蜡烛形态提供明确的交易含义（看涨、看跌或中性）
- 在末尾包含一个Markdown表格，总结关键蜡烛图形态、其含义和置信度

不要简单地说明形态混杂。提供详细、细致的分析，解释为什么某些形态在当前市场背景下具有重要意义。专注于蜡烛图形态和价格走势！"""
}


def create_candlestick_analyst(llm):
    def candlestick_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        
        # 获取语言配置
        config = get_config()
        language = config.get("output_language", "zh")
        
        end_date = current_date
        start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=180)).strftime("%Y-%m-%d")
        
        stock_data = get_stock_data.invoke({"symbol": ticker, "start_date": start_date, "end_date": end_date})
        
        # 获取蜡烛图形态 - 直接传递已获取的stock_data，避免重复获取
        try:
            candlestick_patterns_data = get_candlestick_patterns.invoke({
                "symbol": ticker,
                "start_date": start_date,
                "end_date": end_date,
                "stock_data": stock_data
            })
        except (ValueError, TypeError, KeyError) as e:
            candlestick_patterns_data = f"Error getting candlestick patterns: {str(e)}"
        
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
                "\n\n蜡烛图形态（已识别的形态如看涨吞没、锤子线等）：\n{candlestick_patterns_data}"
            )
        else:
            assistant_prompt = (
                "You are a helpful AI assistant, collaborating with other assistants."
                " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                "{system_message}"
                "\nFor your reference, the current date is {current_date}. The company we want to analyze is {ticker}."
                "\n\nStock Data:\n{stock_data}"
                "\n\nCandlestick Patterns (identified patterns like BULLISH_ENGULFING, HAMMER, etc.):\n{candlestick_patterns_data}"
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
        prompt = prompt.partial(candlestick_patterns_data=candlestick_patterns_data)

        chain = prompt | llm
        
        log_debug_prompt(config, "Candlestick Analyst", language, logger,
                         **{"System Message": system_message, "Assistant Prompt": assistant_prompt})
        
        result = chain.invoke(state["messages"])
        report = result.content

        return {
            "messages": [result],
            "candlestick_report": report,
        }

    return candlestick_analyst_node
