# TradingAgents/graph/reflection.py

from typing import Dict, Any
from langchain_openai import ChatOpenAI


class Reflector:
    """Handles reflection on decisions and updating memory."""

    def __init__(self, quick_thinking_llm: ChatOpenAI):
        """Initialize the reflector with an LLM."""
        self.quick_thinking_llm = quick_thinking_llm
        self.reflection_system_prompt = self._get_reflection_prompt()

    def _get_reflection_prompt(self) -> str:
        """Get the system prompt for reflection."""
        return """
You are an expert financial analyst tasked with reviewing trading decisions/analysis and providing a comprehensive, step-by-step analysis. 
Your goal is to deliver detailed insights into investment decisions and highlight opportunities for improvement, adhering strictly to the following guidelines:

1. Reasoning:
   - For each trading decision, determine whether it was correct or incorrect. A correct decision results in an increase in returns, while an incorrect decision does the opposite.
   - Analyze the contributing factors to each success or mistake. Consider:
     - Market intelligence.
     - Technical indicators.
     - Technical signals.
     - Price movement analysis.
     - Overall market data analysis 
     - News analysis.
     - Social media and sentiment analysis.
     - Fundamental data analysis.
     - Weight the importance of each factor in the decision-making process.

2. Improvement:
   - For any incorrect decisions, propose revisions to maximize returns.
   - Provide a detailed list of corrective actions or improvements, including specific recommendations (e.g., changing a decision from HOLD to BUY on a particular date).

3. Summary:
   - Summarize the lessons learned from the successes and mistakes.
   - Highlight how these lessons can be adapted for future trading scenarios and draw connections between similar situations to apply the knowledge gained.

4. Query:
   - Extract key insights from the summary into a concise sentence of no more than 1000 tokens.
   - Ensure the condensed sentence captures the essence of the lessons and reasoning for easy reference.

Adhere strictly to these instructions, and ensure your output is detailed, accurate, and actionable. You will also be given objective descriptions of the market from a price movements, technical indicator, news, and sentiment perspective to provide more context for your analysis.
"""

    def _extract_current_situation(self, current_state: Dict[str, Any]) -> str:
        """Extract the current market situation from the state."""
        curr_market_report = current_state["market_report"]
        curr_sentiment_report = current_state["sentiment_report"]
        curr_news_report = current_state["news_report"]
        curr_fundamentals_report = current_state["fundamentals_report"]
        curr_candlestick_report = current_state.get("candlestick_report", "")

        return f"{curr_market_report}\n\n{curr_sentiment_report}\n\n{curr_news_report}\n\n{curr_fundamentals_report}\n\n{curr_candlestick_report}"

    def _reflect_on_component(
        self, component_type: str, report: str, situation: str, returns_losses
    ) -> str:
        """Generate reflection for a component."""
        messages = [
            ("system", self.reflection_system_prompt),
            (
                "human",
                f"Returns: {returns_losses}\n\nAnalysis/Decision: {report}\n\nObjective Market Reports for Reference: {situation}",
            ),
        ]

        result = self.quick_thinking_llm.invoke(messages).content
        return result

    def reflect_researcher(self, current_state, returns_losses, memory, researcher_type: str):
        """Reflect on a researcher's analysis and update memory.
        
        通用方法，替代原来的 reflect_bull_researcher / reflect_bear_researcher。
        从 researcher_histories Dict 中读取对应 researcher 的历史。
        
        Args:
            current_state: 当前状态
            returns_losses: 收益/亏损数据
            memory: 该 researcher 的记忆
            researcher_type: researcher 类型标识（如 "bull_researcher", "buffett_researcher"）
        """
        situation = self._extract_current_situation(current_state)
        researcher_histories = current_state["investment_debate_state"].get("researcher_histories", {})
        debate_history = researcher_histories.get(researcher_type, "")
        
        actual_return = returns_losses.get(researcher_type, 0.0) if isinstance(returns_losses, dict) else 0.0

        result = self._reflect_on_component(
            researcher_type.upper(), debate_history, situation, returns_losses
        )
        memory.add_situations([(situation, result, actual_return)])

    def _reflect_role(
        self,
        current_state,
        returns_losses,
        memory,
        role_key: str,
        state_path: str,
        label: str,
    ):
        """通用的角色反思方法。

        Args:
            current_state: 当前状态
            returns_losses: 收益/亏损数据
            memory: 角色对应的记忆
            role_key: 在 returns_losses 中的 key（如 "trader"、"invest_judge"）
            state_path: 状态路径，用 '.' 分隔（如 "trader_investment_plan" 或 "investment_debate_state.judge_decision"）
            label: 用于日志的标签名称（如 "TRADER"、"INVEST JUDGE"）
        """
        situation = self._extract_current_situation(current_state)

        # 按路径获取决策内容
        parts = state_path.split(".")
        decision = current_state
        for part in parts:
            decision = decision[part]

        actual_return = returns_losses.get(role_key, 0.0) if isinstance(returns_losses, dict) else 0.0

        result = self._reflect_on_component(label, decision, situation, returns_losses)
        memory.add_situations([(situation, result, actual_return)])

    def reflect_trader(self, current_state, returns_losses, trader_memory):
        """Reflect on trader's decision and update memory."""
        self._reflect_role(
            current_state, returns_losses, trader_memory,
            role_key="trader",
            state_path="trader_investment_plan",
            label="TRADER",
        )

    def reflect_invest_judge(self, current_state, returns_losses, invest_judge_memory):
        """Reflect on investment judge's decision and update memory."""
        self._reflect_role(
            current_state, returns_losses, invest_judge_memory,
            role_key="invest_judge",
            state_path="investment_debate_state.judge_decision",
            label="INVEST JUDGE",
        )

    def reflect_risk_manager(self, current_state, returns_losses, risk_manager_memory):
        """Reflect on risk manager's decision and update memory."""
        self._reflect_role(
            current_state, returns_losses, risk_manager_memory,
            role_key="risk_manager",
            state_path="risk_debate_state.judge_decision",
            label="RISK JUDGE",
        )
