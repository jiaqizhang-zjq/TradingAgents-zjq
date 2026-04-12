"""
达利奥全天候/债务周期研究员 (Dalio All-Weather/Debt Cycle Researcher)

以雷·达利奥（Bridgewater）的投资哲学进行分析：
- 债务周期分析
- "经济机器"框架
- 风险平价思维
- 四象限分析（增长/通胀）
- 原则化决策和压力测试
"""

from tradingagents.agents.prompt_templates import build_researcher_prompt
from tradingagents.agents.prompts.perspectives import (
    DALIO_PERSPECTIVE_ZH,
    DALIO_PERSPECTIVE_EN,
)
from tradingagents.agents.researchers.base_researcher import BaseResearcher
from tradingagents.constants import DEFAULT_NEUTRAL_WIN_RATE


SYSTEM_PROMPTS = {
    "zh": build_researcher_prompt(
        role_name_zh="达利奥全天候/债务周期分析师",
        role_name_en="Dalio All-Weather / Debt Cycle Analyst",
        perspective_zh=DALIO_PERSPECTIVE_ZH,
        perspective_en=DALIO_PERSPECTIVE_EN,
        language="zh",
        analyst_level="senior",
    ),
    "en": build_researcher_prompt(
        role_name_zh="达利奥全天候/债务周期分析师",
        role_name_en="Dalio All-Weather / Debt Cycle Analyst",
        perspective_zh=DALIO_PERSPECTIVE_ZH,
        perspective_en=DALIO_PERSPECTIVE_EN,
        language="en",
        analyst_level="senior",
    ),
}


def create_dalio_researcher(llm, memory):
    """
    创建达利奥全天候/债务周期研究员节点
    
    Args:
        llm: LLM 客户端
        memory: 记忆存储
        
    Returns:
        节点函数
    """
    researcher = BaseResearcher(
        researcher_type="dalio_researcher",
        system_prompts=SYSTEM_PROMPTS,
        llm=llm,
        memory=memory,
        default_win_rate=DEFAULT_NEUTRAL_WIN_RATE,
        stance_zh="达利奥全天候分析",
        stance_en="Dalio all-weather analysis",
        speaker_label="Dalio",
    )
    return researcher.create_node()
