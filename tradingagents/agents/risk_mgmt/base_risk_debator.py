"""
风险辩论者基类 — 消除 aggressive/conservative/neutral debator 的代码重复。

三个子角色仅在以下方面不同：
  1. 角色名称 / prompt 文本
  2. 自身历史 state key（如 aggressive_history）
  3. 对手 response 的 state key
  4. 默认置信度
  5. 预测/置信度在 state 中的 key 前缀
  6. 轮次标记文本
"""

import re
from dataclasses import dataclass
from typing import Callable, Dict

from tradingagents.dataflows.config import get_config
from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class RiskDebatorConfig:
    """角色差异化配置"""

    role_name: str  # "Aggressive" / "Conservative" / "Neutral"
    state_key_prefix: str  # "aggressive" / "conservative" / "neutral"
    own_history_key: str  # "aggressive_history" / "conservative_history" / "neutral_history"
    opponent_response_keys: tuple  # 对手两个 response 的 state key
    default_confidence: float  # 默认置信度
    round_label_zh: str  # "激进风险观点" / "保守风险观点" / "中性风险观点"
    debug_label: str  # "Aggressive Risk Debator" / ...
    prompt_zh: str  # 中文 prompt 模板（含 {placeholders}）
    prompt_en: str  # 英文 prompt 模板


def create_risk_debator(llm, config: RiskDebatorConfig) -> Callable:
    """通用风险辩论者工厂函数。

    Args:
        llm: LLM 实例
        config: 角色差异化配置

    Returns:
        状态图节点函数
    """

    def risk_debator_node(state: dict) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        own_history = risk_debate_state.get(config.own_history_key, "")

        # 对手观点
        opponent_responses: Dict[str, str] = {}
        for key in config.opponent_response_keys:
            opponent_responses[key] = risk_debate_state.get(key, "")

        # 公共报告
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        candlestick_report = state.get("candlestick_report", "")
        trader_decision = state["trader_investment_plan"]

        # 语言配置
        app_config = get_config()
        language = app_config.get("output_language", "zh")

        # 构造 prompt 的公共变量
        fmt_vars = {
            "trader_decision": trader_decision,
            "market_research_report": market_research_report,
            "sentiment_report": sentiment_report,
            "news_report": news_report,
            "fundamentals_report": fundamentals_report,
            "candlestick_report": candlestick_report,
            "history": history,
        }
        # 加入对手 response
        for key in config.opponent_response_keys:
            fmt_vars[key] = opponent_responses[key]

        prompt = (config.prompt_zh if language == "zh" else config.prompt_en).format(**fmt_vars)

        # Debug 日志
        debug_cfg = app_config.get("debug", {})
        if debug_cfg.get("enabled", False) and debug_cfg.get("show_prompts", False):
            logger.debug("=" * 80)
            logger.debug("DEBUG: %s Prompt Before LLM Call:", config.debug_label)
            logger.debug("=" * 80)
            logger.debug("Language: %s", language)
            logger.debug("Prompt: %s", prompt[:800] + "..." if len(prompt) > 800 else prompt)
            logger.debug("=" * 80)

        response = llm.invoke(prompt)
        response_content = response.content

        # 提取预测
        prediction = "HOLD"
        confidence = config.default_confidence
        if language == "zh":
            pred_match = re.search(
                r'预测[:：]\s*(买入|卖出|持有|BUY|SELL|HOLD).*?置信度[:：]\s*(\d+)%?',
                response_content,
                re.IGNORECASE,
            )
        else:
            pred_match = re.search(
                r'PREDICTION:\s*(BUY|SELL|HOLD).*?Confidence:\s*(\d+)%?',
                response_content,
                re.IGNORECASE,
            )

        if pred_match:
            prediction = pred_match.group(1).upper()
            pred_map = {"买入": "BUY", "卖出": "SELL", "持有": "HOLD"}
            prediction = pred_map.get(prediction, prediction)
            confidence = int(pred_match.group(2)) / 100.0

        # 轮次标记
        current_round = risk_debate_state["count"] + 1
        argument = (
            f"## 第 {current_round} 轮 - {config.round_label_zh}\n"
            f"{config.role_name} Analyst: {response_content}"
        )

        # 构建新状态 — 保留所有字段，只更新自身部分
        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "aggressive_history": risk_debate_state.get("aggressive_history", ""),
            "conservative_history": risk_debate_state.get("conservative_history", ""),
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": config.role_name,
            "current_aggressive_response": risk_debate_state.get("current_aggressive_response", ""),
            "current_conservative_response": risk_debate_state.get("current_conservative_response", ""),
            "current_neutral_response": risk_debate_state.get("current_neutral_response", ""),
            "count": current_round,
        }

        # 更新自身的 history 和 response
        new_risk_debate_state[config.own_history_key] = own_history + "\n" + argument
        current_response_key = f"current_{config.state_key_prefix}_response"
        new_risk_debate_state[current_response_key] = argument

        # 写入预测结果
        new_risk_debate_state[f"{config.state_key_prefix}_prediction"] = prediction
        new_risk_debate_state[f"{config.state_key_prefix}_confidence"] = confidence

        return {"risk_debate_state": new_risk_debate_state}

    return risk_debator_node
