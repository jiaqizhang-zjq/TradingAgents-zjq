import re

from tradingagents.agents.utils.logging_utils import log_debug_prompt
from tradingagents.dataflows.research_tracker import get_research_tracker
from tradingagents.dataflows.config import get_config
from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)


def create_research_manager(llm, memory):
    def research_manager_node(state) -> dict:
        history = state["investment_debate_state"].get("history", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        candlestick_report = state.get("candlestick_report", "")

        investment_debate_state = state["investment_debate_state"]
        
        # 获取股票和日期信息
        symbol = state.get("company_of_interest", "UNKNOWN")
        trade_date = state.get("trade_date", "")
        
        # 获取语言配置
        config = get_config()
        language = config.get("output_language", "zh")

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}\n\n{candlestick_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        if language == "zh":
            prompt = f"""你是一位拥有20多年经验的资深投资组合经理，曾在顶级对冲基金工作，管理过数十亿美元资产。你的声誉建立在卓越的业绩和严谨的风险管理上。

作为辩论主持人，你的角色是批判性地评估本轮辩论并做出明确的决定。你必须展现出资深专家的专业水准。

【重要：你的回复必须使用中文，所有内容都应该是中文】

评估要求：
1. 分析双方的概率分布和预期收益
2. 计算凯利公式最优仓位（f* = (bp - q) / b，其中b是赔率，p是胜率，q是败率）
3. 考虑风险调整后的收益（夏普比率、最大回撤）
4. 结合技术分析确定入场点和出场点

你必须提供：
- 明确的建议：买入、卖出或持有
- 凯利公式计算的最优仓位比例
- 风险调整后的预期收益
- 具体的入场价格区间
- 止损价格和止盈价格
- 持仓时间建议

考虑你在类似情况下的过去错误。利用这些见解来完善你的决策。

重要：在你的回复末尾，你必须包含：
最终决定：[买入/卖出/持有]（置信度：[0-100]%）
凯利公式仓位：X%
入场价格区间：$X - $Y
止损价格：$X
止盈价格：$X
预期持有时间：X天
风险收益比：1:X

以下是你在过去错误上的反思：
"{past_memory_str}"

以下是辩论内容：
辩论历史：
{history}"""
        else:
            prompt = f"""You are a Senior Portfolio Manager with 20+ years of experience at top hedge funds, managing billions in assets. Your reputation is built on exceptional performance and rigorous risk management.

As the debate facilitator, your role is to critically evaluate this round of debate and make a definitive decision. You must demonstrate the professional standards of a seasoned expert.

Evaluation Requirements:
1. Analyze both sides' probability distributions and expected returns
2. Calculate Kelly Criterion optimal position size (f* = (bp - q) / b, where b is odds, p is win probability, q is loss probability)
3. Consider risk-adjusted returns (Sharpe ratio, max drawdown)
4. Combine technical analysis to determine entry and exit points

You must provide:
- Clear recommendation: Buy, Sell, or Hold
- Kelly Criterion optimal position size
- Risk-adjusted expected return
- Specific entry price range
- Stop-loss price
- Take-profit price
- Recommended holding period

Take into account your past mistakes on similar situations.

IMPORTANT: At the end of your response, you MUST include:
FINAL DECISION: [BUY/SELL/HOLD] (Confidence: [0-100]%)
KELLY CRITERION POSITION SIZE: X%
ENTRY PRICE RANGE: $X - $Y
STOP-LOSS PRICE: $X
TAKE-PROFIT PRICE: $X
EXPECTED HOLDING PERIOD: X days
RISK-REWARD RATIO: 1:X

Here are your past reflections on mistakes:
"{past_memory_str}"

Here is the debate:
Debate History:
{history}"""
        log_debug_prompt(config, "Research Manager", language, logger, Prompt=prompt)
        
        response = llm.invoke(prompt)
        response_content = response.content

        # 默认值
        prediction = "HOLD"
        confidence = 0.85

        new_investment_debate_state = {
            "judge_decision": response_content,
            "history": investment_debate_state.get("history", ""),
            "researcher_histories": investment_debate_state.get("researcher_histories", {}),
            "current_response": response_content,
            "latest_speaker": investment_debate_state.get("latest_speaker", ""),
            "count": investment_debate_state["count"],
            "research_manager_prediction": prediction,
            "research_manager_confidence": confidence,
        }
        
        # 解析最终决策并记录到数据库
        try:
            tracker = get_research_tracker()
            
            # 提取最终决策 - 支持中英文格式
            if language == "zh":
                decision_match = re.search(r'最终决定[:：]\s*(买入|卖出|持有|BUY|SELL|HOLD).*?置信度[:：]\s*(\d+)%?', response_content, re.IGNORECASE)
            else:
                decision_match = re.search(r'FINAL\s*DECISION:\s*(BUY|SELL|HOLD).*?Confidence:\s*(\d+)%?', response_content, re.IGNORECASE)
            
            if decision_match:
                prediction = decision_match.group(1).upper()
                # 转换中文预测为英文
                prediction_map = {"买入": "BUY", "卖出": "SELL", "持有": "HOLD"}
                prediction = prediction_map.get(prediction, prediction)
                confidence = int(decision_match.group(2)) / 100.0
            else:
                # 尝试从内容推断
                content_upper = response_content.upper()
                if language == "zh":
                    if "买入" in response_content or ("BUY" in content_upper and "SELL" not in content_upper):
                        prediction = "BUY"
                    elif "卖出" in response_content or "SELL" in content_upper:
                        prediction = "SELL"
                    else:
                        prediction = "HOLD"
                else:
                    if "BUY" in content_upper and "SELL" not in content_upper:
                        prediction = "BUY"
                    elif "SELL" in content_upper:
                        prediction = "SELL"
                    else:
                        prediction = "HOLD"
                # 基于预测类型和文本内容调整置信度
                if prediction in ["BUY", "SELL"]:
                    # 检查文本中的强弱信号词
                    has_strong_words = any(word in response_content.lower() for word in ['strong', 'confident', 'clear', 'convincing', '明显', '强烈', '确定', '有说服力'])
                    has_weak_words = any(word in response_content.lower() for word in ['uncertain', 'unclear', 'mixed', 'weak', '模糊', '不确定', '混杂', '弱'])
                    
                    if has_strong_words and not has_weak_words:
                        confidence = 0.72
                    elif has_weak_words and not has_strong_words:
                        confidence = 0.58
                    else:
                        confidence = 0.65
                else:
                    confidence = 0.55
            
            # 记录到数据库
            tracker.record_research(
                researcher_name="research_manager",
                researcher_type="manager",
                symbol=symbol,
                trade_date=trade_date,
                prediction=prediction,
                confidence=confidence,
                reasoning=response_content,
                holding_days=5,
                metadata={
                    "role": "research_manager",
                    "full_response": response_content
                }
            )
        except Exception as e:
            logger.warning("记录Research Manager决策失败: %s", e)

        return {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": response_content,
        }

    return research_manager_node
