"""
查理·芒格多元思维研究员 (Charlie Munger Multi-Disciplinary Researcher)

以查理·芒格的投资哲学进行分析：
- 逆向思维（Inversion）
- 多元思维模型（心理学、经济学、物理学等多学科）
- 检查清单思维
- 机会成本思维
- 耐心等待"肥球"
"""

from tradingagents.agents.prompt_templates import build_researcher_prompt
from tradingagents.agents.prompts.perspectives import (
    CHARLIE_MUNGER_PERSPECTIVE_ZH,
    CHARLIE_MUNGER_PERSPECTIVE_EN,
)
from tradingagents.agents.researchers.base_researcher import BaseResearcher
from tradingagents.constants import DEFAULT_NEUTRAL_WIN_RATE


SYSTEM_PROMPTS = {
    "zh": build_researcher_prompt(
        role_name_zh="查理·芒格多元思维分析师",
        role_name_en="Charlie Munger Multi-Disciplinary Analyst",
        perspective_zh=CHARLIE_MUNGER_PERSPECTIVE_ZH,
        perspective_en=CHARLIE_MUNGER_PERSPECTIVE_EN,
        language="zh",
        analyst_level="senior",
    ),
    "en": build_researcher_prompt(
        role_name_zh="查理·芒格多元思维分析师",
        role_name_en="Charlie Munger Multi-Disciplinary Analyst",
        perspective_zh=CHARLIE_MUNGER_PERSPECTIVE_ZH,
        perspective_en=CHARLIE_MUNGER_PERSPECTIVE_EN,
        language="en",
        analyst_level="senior",
    ),
}


def create_charlie_munger_researcher(llm, memory):
    """
    创建查理·芒格多元思维研究员节点
    
    Args:
        llm: LLM 客户端
        memory: 记忆存储
        
    Returns:
        节点函数
    """
    researcher = BaseResearcher(
        researcher_type="charlie_munger_researcher",
        system_prompts=SYSTEM_PROMPTS,
        llm=llm,
        memory=memory,
        default_win_rate=DEFAULT_NEUTRAL_WIN_RATE,
        stance_zh="芒格多元思维",
        stance_en="Munger multi-disciplinary thinking",
        speaker_label="Munger",
    )
    return researcher.create_node()
