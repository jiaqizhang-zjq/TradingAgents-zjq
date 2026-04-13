from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.agent_utils import get_news, get_global_news
from tradingagents.agents.utils.logging_utils import log_debug_prompt
from tradingagents.dataflows.config import get_config
from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)


def create_news_analyst(llm):
    def news_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        tools = [
            get_news,
            get_global_news,
        ]

        config = get_config()
        language = config.get("output_language", "zh")

        if language == "zh":
            system_message = (
                "【重要：你的回复必须使用中文，所有内容都应该是中文】\n\n"
                "你是一位新闻研究员，负责分析过去一周的最新新闻和趋势。请撰写一份全面的报告，分析与交易和宏观经济学相关的当前世界状态。"
                "使用可用工具：get_news(query, start_date, end_date) 用于公司特定或目标新闻搜索，"
                "get_global_news(curr_date, look_back_days, limit) 用于更广泛的宏观经济新闻。"
                "不要简单地说明趋势混合，要提供详细且精细的分析和见解，帮助交易员做出决策。"
                + " 确保在报告末尾添加一个Markdown表格，整理报告中的关键点，使其有条理且易于阅读。"
            )
        else:
            system_message = (
                "You are a news researcher tasked with analyzing recent news and trends over the past week. Please write a comprehensive report of the current state of the world that is relevant for trading and macroeconomics. Use the available tools: get_news(query, start_date, end_date) for company-specific or targeted news searches, and get_global_news(curr_date, look_back_days, limit) for broader macroeconomic news. Do not simply state the trends are mixed, provide detailed and finegrained analysis and insights that may help traders make decisions."
                + """ Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."""
            )

        if language == "zh":
            assistant_prompt = (
                "你是一个有用的AI助手，与其他助手合作。使用提供的工具来推进问题的回答。"
                "如果你无法完全回答，没关系；另一个拥有不同工具的助手会在你离开的地方继续。"
                "执行你能做的来取得进展。如果你或任何其他助手有最终交易建议：**买入/持有/卖出**或可交付成果，"
                "请在你的回复前加上'最终交易建议：**买入/持有/卖出**'，这样团队就知道要停止了。"
                "你可以使用以下工具：{tool_names}。\n{system_message}"
                "参考信息：当前日期是{current_date}。我们正在分析公司{ticker}"
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
                "For your reference, the current date is {current_date}. We are looking at the company {ticker}"
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
        
        log_debug_prompt(config, "News Analyst", language, logger,
                         **{"System Message": system_message, "Assistant Prompt": assistant_prompt})
        
        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "news_report": report,
        }

    return news_analyst_node
