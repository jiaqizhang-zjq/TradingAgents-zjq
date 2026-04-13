from tradingagents.agents.utils.logging_utils import log_debug_prompt, build_situation_string, format_past_memories
from tradingagents.agents.utils.prediction_utils import extract_prediction
from tradingagents.dataflows.config import get_config
from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)


def create_risk_manager(llm, memory):
    def risk_manager_node(state) -> dict:

        company_name = state["company_of_interest"]

        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        market_research_report = state["market_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        sentiment_report = state["sentiment_report"]
        candlestick_report = state.get("candlestick_report", "")
        trader_plan = state["investment_plan"]

        curr_situation = build_situation_string(state)
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = format_past_memories(past_memories, language)

        config = get_config()
        language = config.get("output_language", "zh")
        
        if language == "zh":
            prompt = f"""作为风险管理评委和辩论主持人，你的目标是评估三位风险分析师——激进、中性和保守——之间的辩论，并确定交易员的最佳行动方案。

【重要：你的回复必须使用中文，所有内容都应该是中文】

你的决定必须导致明确的建议：买入、卖出或持有。只有在特定论点充分支持的情况下才选择持有，而不是在所有方面似乎都有效时作为退路。努力做到清晰和果断。

决策指南：
1. **总结关键论点**：从每位分析师中提取最强的观点，专注于与上下文的相关性。
2. **提供理由**：用辩论中的直接引语和反驳论点支持你的建议。
3. **完善交易员计划**：从交易员的原始计划 **{trader_plan}** 开始，并根据分析师的见解进行调整。
4. **从过去的错误中学习**：使用 **{past_memory_str}** 中的教训来解决先前的错误判断，并改进你现在做出的决定，以确保你不会做出错误的买入/卖出/持有的决定而赔钱。

交付物：
- 清晰且可操作的建议：买入、卖出或持有。
- 基于辩论和过去反思的详细推理。
- 你的整个回复必须使用中文，包括标题、表格、分析内容。

---

**分析师辩论历史：**  
{history}

---

专注于可操作的见解和持续改进。建立在过去的教训之上，批判性地评估所有观点，并确保每个决定都推动更好的结果。"""
        else:
            prompt = f"""As the Risk Management Judge and Debate Facilitator, your goal is to evaluate the debate between three risk analysts—Aggressive, Neutral, and Conservative—and determine the best course of action for the trader. Your decision must result in a clear recommendation: Buy, Sell, or Hold. Choose Hold only if strongly justified by specific arguments, not as a fallback when all sides seem valid. Strive for clarity and decisiveness.

Guidelines for Decision-Making:
1. **Summarize Key Arguments**: Extract the strongest points from each analyst, focusing on relevance to the context.
2. **Provide Rationale**: Support your recommendation with direct quotes and counterarguments from the debate.
3. **Refine the Trader's Plan**: Start with the trader's original plan, **{trader_plan}**, and adjust it based on the analysts' insights.
4. **Learn from Past Mistakes**: Use lessons from **{past_memory_str}** to address prior misjudgments and improve the decision you are making now to make sure you don't make a wrong BUY/SELL/HOLD call that loses money.

Deliverables:
- A clear and actionable recommendation: Buy, Sell, or Hold.
- Detailed reasoning anchored in the debate and past reflections.

---

**Analysts Debate History:**  
{history}

---

Focus on actionable insights and continuous improvement. Build on past lessons, critically evaluate all perspectives, and ensure each decision advances better outcomes."""

        log_debug_prompt(config, "Risk Manager", language, logger, Prompt=prompt)
        
        response = llm.invoke(prompt)
        response_content = response.content

        # 提取预测结果
        prediction, confidence = extract_prediction(
            response_content, language,
            zh_pattern=r'预测[:：]\s*(买入|卖出|持有|BUY|SELL|HOLD).*?置信度[:：]\s*(\d+)%?',
            en_pattern=r'PREDICTION:\s*(BUY|SELL|HOLD).*?Confidence:\s*(\d+)%?',
            default_confidence=0.8,
        )

        new_risk_debate_state = {
            "judge_decision": response_content,
            "history": risk_debate_state["history"],
            "aggressive_history": risk_debate_state["aggressive_history"],
            "conservative_history": risk_debate_state["conservative_history"],
            "neutral_history": risk_debate_state["neutral_history"],
            "latest_speaker": "Judge",
            "current_aggressive_response": risk_debate_state["current_aggressive_response"],
            "current_conservative_response": risk_debate_state["current_conservative_response"],
            "current_neutral_response": risk_debate_state["current_neutral_response"],
            "current_response": response_content,  # 添加 current_response 用于打印
            "count": risk_debate_state["count"],
            "risk_manager_prediction": prediction,
            "risk_manager_confidence": confidence,
        }

        return {
            "risk_debate_state": new_risk_debate_state,
            "final_trade_decision": response.content,
            "risk_manager_prediction": prediction,
            "risk_manager_confidence": confidence,
        }

    return risk_manager_node
