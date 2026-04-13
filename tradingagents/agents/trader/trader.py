import functools
from tradingagents.agents.utils.logging_utils import log_debug_prompt
from tradingagents.agents.utils.prediction_utils import extract_prediction
from tradingagents.dataflows.config import get_config
from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)


def create_trader(llm, memory):
    def trader_node(state, name):
        company_name = state["company_of_interest"]
        investment_plan = state["investment_plan"]
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        candlestick_report = state.get("candlestick_report", "")

        # 获取语言配置
        config = get_config()
        language = config.get("output_language", "zh")

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}\n\n{candlestick_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        if past_memories:
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"
        else:
            past_memory_str = "No past memories found." if language == "en" else "没有找到过去的记忆。"

        if language == "zh":
            context = {
                "role": "user",
                "content": f"基于分析师团队的综合分析，这里是为{company_name}制定的投资计划。该计划整合了当前技术市场趋势、宏观经济指标和社交媒体情绪的见解。请以此为基础评估你的下一个交易决策。\n\n建议投资计划：{investment_plan}\n\n利用这些见解做出明智和战略性的决策。",
            }
            system_content = f"""【重要：你的回复必须使用中文，所有内容都应该是中文】

你是一位拥有20多年经验的首席交易员，曾在顶级投资银行和对冲基金工作，管理过数十亿美元的交易组合。你的声誉建立在精准的执行和严格的风险控制上。

作为资深交易员，你必须：
1. 根据技术分析确定精确的入场点、止损点和止盈点
2. 计算风险收益比，确保每笔交易的潜在收益至少是风险的2倍以上
3. 考虑市场流动性和滑点，制定分批建仓/平仓策略
4. 结合波动率（ATR）设置动态止损
5. 提供明确的仓位管理建议

你的输出必须包含：
- 具体入场价格（可接受的价格区间）
- 止损价格（基于技术支撑/阻力位或ATR倍数）
- 止盈价格（基于技术阻力/目标位）
- 风险收益比
- 建议仓位规模
- 执行策略（一次性建仓或分批建仓）

以明确的决策结束，并始终以'最终交易建议：**买入/持有/卖出**'来确认你的建议。

不要忘记利用过去决策的经验教训来避免错误。以下是你过去在类似情况下的交易反思和经验教训：{past_memory_str}"""
        else:
            context = {
                "role": "user",
                "content": f"Based on a comprehensive analysis by a team of analysts, here is an investment plan tailored for {company_name}. This plan incorporates insights from current technical market trends, macroeconomic indicators, and social media sentiment. Use this plan as a foundation for evaluating your next trading decision.\n\nProposed Investment Plan: {investment_plan}\n\nLeverage these insights to make an informed and strategic decision.",
            }
            system_content = f"""You are a Senior Lead Trader with 20+ years of experience at top investment banks and hedge funds, managing billions in trading portfolios. Your reputation is built on precise execution and strict risk control.

As a seasoned trader, you must:
1. Determine precise entry points, stop-loss, and take-profit levels based on technical analysis
2. Calculate risk-reward ratio, ensuring potential reward is at least 2x the risk
3. Consider market liquidity and slippage, develop staged entry/exit strategies
4. Set dynamic stop-loss based on volatility (ATR multiples)
5. Provide clear position management recommendations

Your output must include:
- Specific entry price (acceptable price range)
- Stop-loss price (based on technical support/resistance or ATR multiples)
- Take-profit price (based on technical resistance/target levels)
- Risk-reward ratio
- Recommended position size
- Execution strategy (all-at-once or staged entry)

End with a firm decision and always conclude your response with 'FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**' to confirm your recommendation.

Do not forget to utilize lessons from past decisions to learn from your mistakes. Here are reflections from similar situations you traded in: {past_memory_str}"""

        messages = [
            {
                "role": "system",
                "content": system_content,
            },
            context,
        ]
        
        log_debug_prompt(config, "Trader", language, logger,
                         **{"System Content": system_content, "User Content": context['content']})

        result = llm.invoke(messages)
        response_content = result.content

        # 提取预测结果
        prediction, confidence = extract_prediction(
            response_content, language,
            zh_pattern=r'预测[:：]\s*(买入|卖出|持有|BUY|SELL|HOLD).*?置信度[:：]\s*(\d+)%?',
            en_pattern=r'PREDICTION:\s*(BUY|SELL|HOLD).*?Confidence:\s*(\d+)%?',
            default_confidence=0.9,
        )

        return {
            "messages": [result],
            "trader_investment_plan": result.content,
            "trader_prediction": prediction,
            "trader_confidence": confidence,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")
