"""
看跌研究员 (Bear Researcher) - 使用基类重构
"""

from tradingagents.agents.prompt_templates import STANDARD_BEAR_PROMPT_EN, STANDARD_BEAR_PROMPT_ZH
from tradingagents.agents.researchers.base_researcher import BaseResearcher
from tradingagents.constants import DEFAULT_BEAR_WIN_RATE


# 使用模板中的提示词
SYSTEM_PROMPTS = {
    "en": STANDARD_BEAR_PROMPT_EN,
    "zh": STANDARD_BEAR_PROMPT_ZH
}


def create_bear_researcher(llm, memory):
    """
    创建看跌研究员节点
    
    Args:
        llm: LLM 客户端
        memory: 记忆存储
        
    Returns:
        节点函数
    """
    researcher = BaseResearcher(
        researcher_type="bear_researcher",
        system_prompts=SYSTEM_PROMPTS,
        llm=llm,
        memory=memory,
        default_win_rate=DEFAULT_BEAR_WIN_RATE
    )
    return researcher.create_node()
