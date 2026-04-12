"""
索罗斯宏观/反身性研究员 (Soros Macro/Reflexivity Researcher)

以乔治·索罗斯的投资哲学进行分析：
- 反身性理论（Reflexivity）
- 宏观经济趋势分析
- 市场情绪极端值识别
- 不对称风险回报
- 政策博弈
"""

from tradingagents.agents.prompt_templates import build_researcher_prompt
from tradingagents.agents.prompts.perspectives import (
    SOROS_PERSPECTIVE_ZH,
    SOROS_PERSPECTIVE_EN,
)
from tradingagents.agents.researchers.base_researcher import BaseResearcher
from tradingagents.constants import DEFAULT_NEUTRAL_WIN_RATE


SYSTEM_PROMPTS = {
    "zh": build_researcher_prompt(
        role_name_zh="索罗斯宏观/反身性分析师",
        role_name_en="Soros Macro/Reflexivity Analyst",
        perspective_zh=SOROS_PERSPECTIVE_ZH,
        perspective_en=SOROS_PERSPECTIVE_EN,
        language="zh",
        analyst_level="senior",
    ),
    "en": build_researcher_prompt(
        role_name_zh="索罗斯宏观/反身性分析师",
        role_name_en="Soros Macro/Reflexivity Analyst",
        perspective_zh=SOROS_PERSPECTIVE_ZH,
        perspective_en=SOROS_PERSPECTIVE_EN,
        language="en",
        analyst_level="senior",
    ),
}


def create_soros_researcher(llm, memory):
    """
    创建索罗斯宏观/反身性研究员节点
    
    Args:
        llm: LLM 客户端
        memory: 记忆存储
        
    Returns:
        节点函数
    """
    researcher = BaseResearcher(
        researcher_type="soros_researcher",
        system_prompts=SYSTEM_PROMPTS,
        llm=llm,
        memory=memory,
        default_win_rate=DEFAULT_NEUTRAL_WIN_RATE,
        stance_zh="索罗斯宏观反身性",
        stance_en="Soros macro reflexivity",
        speaker_label="Soros",
    )
    return researcher.create_node()
