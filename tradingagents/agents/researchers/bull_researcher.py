"""
看涨研究员 (Bull Researcher) - 使用基类重构
"""

from tradingagents.agents.prompt_templates import STANDARD_BULL_PROMPT_EN, STANDARD_BULL_PROMPT_ZH
from tradingagents.agents.researchers.base_researcher import BaseResearcher
from tradingagents.constants import DEFAULT_BULL_WIN_RATE


# 使用模板中的提示词
SYSTEM_PROMPTS = {
    "en": STANDARD_BULL_PROMPT_EN,
    "zh": STANDARD_BULL_PROMPT_ZH
}


def create_bull_researcher(llm, memory):
    """
    创建看涨研究员节点
    
    Args:
        llm: LLM 客户端
        memory: 记忆存储
        
    Returns:
        节点函数
    """
    researcher = BaseResearcher(
        researcher_type="bull_researcher",
        system_prompts=SYSTEM_PROMPTS,
        llm=llm,
        memory=memory,
        default_win_rate=DEFAULT_BULL_WIN_RATE
    )
    return researcher.create_node()
