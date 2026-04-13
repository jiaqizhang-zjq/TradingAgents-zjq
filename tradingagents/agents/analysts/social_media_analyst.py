from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.agent_utils import get_news, get_social_media_data
from tradingagents.agents.utils.logging_utils import log_debug_prompt
from tradingagents.dataflows.config import get_config
from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)


def create_social_media_analyst(llm):
    def social_media_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        tools = [
            get_news,
            get_social_media_data,
        ]

        config = get_config()
        language = config.get("output_language", "zh")

        if language == "zh":
            system_message = (
                "【重要：你的回复必须使用中文，所有内容都应该是中文】\n\n"
                "你是一位社交媒体和公司特定新闻研究员/分析师，负责分析过去一周特定公司的社交媒体帖子、最新公司新闻和公众情绪。"
                "你将获得一家公司的名称，你的目标是撰写一份全面的长篇报告，详细说明你的分析、见解以及对交易员和投资者关于这家公司当前状态的影响，"
                "在查看社交媒体和人们对该公司的评价后，分析人们每天对公司的情绪数据，并查看最新的公司新闻。\n\n"
                "可用工具:\n"
                "1. get_news(query, start_date, end_date): 检索有关公司的传统新闻文章\n"
                "2. get_social_media_data(ticker, platforms, limit): 从Reddit和/或Twitter检索社交媒体提及。"
                "此工具提供来自社交平台的实时公众情绪和讨论。\n\n"
                "分析指南:\n"
                "- 首先，使用 get_social_media_data 收集来自 Reddit 和 Twitter 的社交媒体情绪\n"
                "- 然后，使用 get_news 收集传统新闻文章\n"
                "- 分析两个来源的情绪和主题\n"
                "- 寻找社交媒体和传统新闻之间的模式、趋势和差异\n"
                "- 关注可能影响市场的高影响力帖子或文章\n"
                "- 不要简单地说明趋势混合，要提供详细且精细的分析和见解，帮助交易员做出决策。\n\n"
                "- 不要简单地说明趋势混合，要提供详细且精细的分析和见解，帮助交易员做出决策。\n\n"
                "确保在报告末尾添加一个Markdown表格，整理报告中的关键点，使其有条理且易于阅读。"
            )
        else:
            system_message = (
                "You are a social media and company specific news researcher/analyst tasked with analyzing social media posts, recent company news, and public sentiment for a specific company over the past week. You will be given a company's name your objective is to write a comprehensive long report detailing your analysis, insights, and implications for traders and investors on this company's current state after looking at social media and what people are saying about that company, analyzing sentiment data of what people feel each day about the company, and looking at recent company news.\n\n"
                "AVAILABLE TOOLS:\n"
                "1. get_news(query, start_date, end_date): Retrieve traditional news articles about the company\n"
                "2. get_social_media_data(ticker, platforms, limit): Retrieve social media mentions from Reddit and/or Twitter. "
                "This tool provides real-time public sentiment and discussions from social platforms.\n\n"
                "ANALYSIS GUIDELINES:\n"
                "- First, use get_social_media_data to gather social media sentiment from Reddit and Twitter\n"
                "- Then, use get_news to gather traditional news articles\n"
                "- Analyze the sentiment and themes from both sources\n"
                "- Look for patterns, trends, and divergences between social media and traditional news\n"
                "- Pay attention to high-impact posts or articles that could move the market\n"
                "- Do not simply state the trends are mixed, provide detailed and finegrained analysis and insights that may help traders make decisions.\n\n"
                "- Do not simply state the trends are mixed, provide detailed and finegrained analysis and insights that may help traders make decisions.\n\n"
                "Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."
            )

        if language == "zh":
            assistant_prompt = (
                "你是一个有用的AI助手，与其他助手合作。使用提供的工具来推进问题的回答。"
                "如果你无法完全回答，没关系；另一个拥有不同工具的助手会在你离开的地方继续。"
                "执行你能做的来取得进展。如果你或任何其他助手有最终交易建议：**买入/持有/卖出**或可交付成果，"
                "请在你的回复前加上'最终交易建议：**买入/持有/卖出**'，这样团队就知道要停止了。"
                "你可以使用以下工具：{tool_names}。\n{system_message}"
                "参考信息：当前日期是{current_date}。我们要分析的当前公司是{ticker}"
            )
        else:
            assistant_prompt = (
                "You are a helpful AI assistant, collaborating with other assistants."
                " Use the provided tools to progress towards answering the question."
                " If you are unable to fully answer, that's OK; another assistant with different tools"
                " will help where you left off. Execute what you can to make progress."
                " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                " You have access to the following tools: {tool_names}.\n{system_message}"
                "For your reference, the current date is {current_date}. The current company we want to analyze is {ticker}"
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
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)
        
        log_debug_prompt(config, "Social Media Analyst", language, logger,
                         **{"System Message": system_message, "Assistant Prompt": assistant_prompt})
        
        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "sentiment_report": report,
        }

    return social_media_analyst_node
