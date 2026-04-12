"""
彼得·林奇成长投资研究员 (Peter Lynch Growth Researcher)

以彼得·林奇的投资哲学进行分析：
- PEG 比率分析
- 六种股票分类法
- "翻石头" 深入研究策略
- 内部人买入信号
- 寻找被忽视的好公司
"""

from tradingagents.agents.prompt_templates import build_researcher_prompt
from tradingagents.agents.prompts.perspectives import (
    PETER_LYNCH_PERSPECTIVE_ZH,
    PETER_LYNCH_PERSPECTIVE_EN,
)
from tradingagents.agents.researchers.base_researcher import BaseResearcher
from tradingagents.constants import DEFAULT_NEUTRAL_WIN_RATE


SYSTEM_PROMPTS = {
    "zh": build_researcher_prompt(
        role_name_zh="彼得·林奇成长投资分析师",
        role_name_en="Peter Lynch Growth Analyst",
        perspective_zh=PETER_LYNCH_PERSPECTIVE_ZH,
        perspective_en=PETER_LYNCH_PERSPECTIVE_EN,
        language="zh",
        analyst_level="senior",
    ),
    "en": build_researcher_prompt(
        role_name_zh="彼得·林奇成长投资分析师",
        role_name_en="Peter Lynch Growth Analyst",
        perspective_zh=PETER_LYNCH_PERSPECTIVE_ZH,
        perspective_en=PETER_LYNCH_PERSPECTIVE_EN,
        language="en",
        analyst_level="senior",
    ),
}


def create_peter_lynch_researcher(llm, memory):
    """
    创建彼得·林奇成长投资研究员节点
    
    Args:
        llm: LLM 客户端
        memory: 记忆存储
        
    Returns:
        节点函数
    """
    researcher = BaseResearcher(
        researcher_type="peter_lynch_researcher",
        system_prompts=SYSTEM_PROMPTS,
        llm=llm,
        memory=memory,
        default_win_rate=DEFAULT_NEUTRAL_WIN_RATE,
        stance_zh="林奇成长投资",
        stance_en="Peter Lynch growth investing",
        speaker_label="PeterLynch",
    )
    return researcher.create_node()
