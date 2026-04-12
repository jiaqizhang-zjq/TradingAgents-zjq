"""
利弗莫尔趋势/动量交易研究员 (Livermore Trend/Momentum Researcher)

以杰西·利弗莫尔的交易哲学进行分析：
- 趋势跟踪
- 关键价位分析（支撑/阻力/突破）
- 成交量确认
- 金字塔加仓法
- 严格止损纪律
"""

from tradingagents.agents.prompt_templates import build_researcher_prompt
from tradingagents.agents.prompts.perspectives import (
    LIVERMORE_PERSPECTIVE_ZH,
    LIVERMORE_PERSPECTIVE_EN,
)
from tradingagents.agents.researchers.base_researcher import BaseResearcher
from tradingagents.constants import DEFAULT_NEUTRAL_WIN_RATE


SYSTEM_PROMPTS = {
    "zh": build_researcher_prompt(
        role_name_zh="利弗莫尔趋势/动量交易分析师",
        role_name_en="Livermore Trend/Momentum Trading Analyst",
        perspective_zh=LIVERMORE_PERSPECTIVE_ZH,
        perspective_en=LIVERMORE_PERSPECTIVE_EN,
        language="zh",
        analyst_level="senior",
    ),
    "en": build_researcher_prompt(
        role_name_zh="利弗莫尔趋势/动量交易分析师",
        role_name_en="Livermore Trend/Momentum Trading Analyst",
        perspective_zh=LIVERMORE_PERSPECTIVE_ZH,
        perspective_en=LIVERMORE_PERSPECTIVE_EN,
        language="en",
        analyst_level="senior",
    ),
}


def create_livermore_researcher(llm, memory):
    """
    创建利弗莫尔趋势/动量交易研究员节点
    
    Args:
        llm: LLM 客户端
        memory: 记忆存储
        
    Returns:
        节点函数
    """
    researcher = BaseResearcher(
        researcher_type="livermore_researcher",
        system_prompts=SYSTEM_PROMPTS,
        llm=llm,
        memory=memory,
        default_win_rate=DEFAULT_NEUTRAL_WIN_RATE,
        stance_zh="利弗莫尔趋势交易",
        stance_en="Livermore trend trading",
        speaker_label="Livermore",
    )
    return researcher.create_node()
