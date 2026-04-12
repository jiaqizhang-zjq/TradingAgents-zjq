"""
木头姐创新颠覆研究员 (Cathie Wood Disruptive Innovation Researcher)

以凯茜·伍德 / ARK Invest 的投资哲学进行分析：
- 颠覆性创新潜力（AI、机器人、基因组学、区块链、能源存储）
- 指数级增长曲线和 TAM 扩张
- 技术采用 S 曲线分析
- Wright's Law 成本下降曲线
"""

from tradingagents.agents.prompt_templates import build_researcher_prompt
from tradingagents.agents.prompts.perspectives import (
    CATHIE_WOOD_PERSPECTIVE_ZH,
    CATHIE_WOOD_PERSPECTIVE_EN,
)
from tradingagents.agents.researchers.base_researcher import BaseResearcher
from tradingagents.constants import DEFAULT_NEUTRAL_WIN_RATE


SYSTEM_PROMPTS = {
    "zh": build_researcher_prompt(
        role_name_zh="木头姐创新颠覆分析师",
        role_name_en="Cathie Wood Disruptive Innovation Analyst",
        perspective_zh=CATHIE_WOOD_PERSPECTIVE_ZH,
        perspective_en=CATHIE_WOOD_PERSPECTIVE_EN,
        language="zh",
        analyst_level="senior",
    ),
    "en": build_researcher_prompt(
        role_name_zh="木头姐创新颠覆分析师",
        role_name_en="Cathie Wood Disruptive Innovation Analyst",
        perspective_zh=CATHIE_WOOD_PERSPECTIVE_ZH,
        perspective_en=CATHIE_WOOD_PERSPECTIVE_EN,
        language="en",
        analyst_level="senior",
    ),
}


def create_cathie_wood_researcher(llm, memory):
    """
    创建木头姐创新颠覆研究员节点
    
    Args:
        llm: LLM 客户端
        memory: 记忆存储
        
    Returns:
        节点函数
    """
    researcher = BaseResearcher(
        researcher_type="cathie_wood_researcher",
        system_prompts=SYSTEM_PROMPTS,
        llm=llm,
        memory=memory,
        default_win_rate=DEFAULT_NEUTRAL_WIN_RATE,
        stance_zh="创新颠覆投资",
        stance_en="disruptive innovation investing",
        speaker_label="CathieWood",
    )
    return researcher.create_node()
