from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.agent_utils import get_fundamentals, get_balance_sheet, get_cashflow, get_income_statement
from tradingagents.agents.utils.logging_utils import log_debug_prompt
from tradingagents.dataflows.config import get_config
from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)


# 中英双语系统提示词
SYSTEM_PROMPTS = {
    "en": """You are a researcher tasked with analyzing fundamental information about a company. Based on the provided fundamental data, balance sheet, cashflow statement, and income statement, please write a comprehensive report of the company's fundamental information such as financial documents, company profile, basic company financials, and company financial history to gain a full view of the company's fundamental information to inform traders. Make sure to include as much detail as possible. Do not simply state the trends are mixed, provide detailed and finegrained analysis and insights that may help traders make decisions. Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read.""",

    "zh": """你是一位研究员，负责分析公司的基本面信息。基于提供的基本面数据、资产负债表、现金流量表和利润表，请撰写一份全面的报告，涵盖公司的基本面信息，如财务文件、公司简介、基本公司财务和公司财务历史，以全面了解公司的基本面信息，为交易员提供参考。

【重要：你的回复必须使用中文，所有内容都应该是中文】

确保包含尽可能多的细节。不要简单地说明趋势混杂，要提供详细且精细的分析和见解，帮助交易员做出决策。确保在报告末尾添加一个Markdown表格，整理报告中的关键点，使其有条理且易于阅读。你的整个回复必须使用中文，包括标题、表格、分析内容。"""
}


def create_fundamentals_analyst(llm):
    def fundamentals_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        
        # 获取语言配置
        config = get_config()
        language = config.get("output_language", "zh")
        
        fundamentals_data = ""
        try:
            fundamentals_data = get_fundamentals.invoke({"ticker": ticker, "curr_date": current_date})
        except (ConnectionError, ValueError, TimeoutError, OSError) as e:
            fundamentals_data = f"Error fetching fundamentals: {str(e)}"
        
        balance_sheet_data = ""
        try:
            balance_sheet_data = get_balance_sheet.invoke({"ticker": ticker, "freq": "quarterly", "curr_date": current_date})
        except (ConnectionError, ValueError, TimeoutError, OSError) as e:
            balance_sheet_data = f"Error fetching balance sheet: {str(e)}"
        
        cashflow_data = ""
        try:
            cashflow_data = get_cashflow.invoke({"ticker": ticker, "freq": "quarterly", "curr_date": current_date})
        except (ConnectionError, ValueError, TimeoutError, OSError) as e:
            cashflow_data = f"Error fetching cashflow: {str(e)}"
        
        income_statement_data = ""
        try:
            income_statement_data = get_income_statement.invoke({"ticker": ticker, "freq": "quarterly", "curr_date": current_date})
        except (ConnectionError, ValueError, TimeoutError, OSError) as e:
            income_statement_data = f"Error fetching income statement: {str(e)}"
        
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
                "\n\n基本面数据：\n{fundamentals_data}"
                "\n\n资产负债表：\n{balance_sheet_data}"
                "\n\n现金流量表：\n{cashflow_data}"
                "\n\n利润表：\n{income_statement_data}"
            )
        else:
            assistant_prompt = (
                "You are a helpful AI assistant, collaborating with other assistants."
                " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                "{system_message}"
                "\nFor your reference, the current date is {current_date}. The company we want to look at is {ticker}."
                "\n\nFundamentals Data:\n{fundamentals_data}"
                "\n\nBalance Sheet:\n{balance_sheet_data}"
                "\n\nCashflow Statement:\n{cashflow_data}"
                "\n\nIncome Statement:\n{income_statement_data}"
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
        prompt = prompt.partial(fundamentals_data=fundamentals_data)
        prompt = prompt.partial(balance_sheet_data=balance_sheet_data)
        prompt = prompt.partial(cashflow_data=cashflow_data)
        prompt = prompt.partial(income_statement_data=income_statement_data)

        chain = prompt | llm
        
        log_debug_prompt(config, "Fundamentals Analyst", language, logger,
                         **{"System Message": system_message, "Assistant Prompt": assistant_prompt})
        
        result = chain.invoke(state["messages"])
        report = result.content

        return {
            "messages": [result],
            "fundamentals_report": report,
        }

    return fundamentals_analyst_node
