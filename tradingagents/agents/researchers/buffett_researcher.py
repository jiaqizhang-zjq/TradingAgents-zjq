"""
巴菲特价值投资研究员 (Buffett Value Researcher)

以沃伦·巴菲特的投资哲学进行分析：
- 护城河、安全边际、管理层质量
- 长期可持续竞争优势
- 内在价值 vs 市场价格
- 自由现金流和股东回报
"""

from tradingagents.agents.prompt_templates import build_researcher_prompt
from tradingagents.agents.prompts.perspectives import (
    BUFFETT_PERSPECTIVE_ZH,
    BUFFETT_PERSPECTIVE_EN,
)
from tradingagents.agents.researchers.base_researcher import BaseResearcher
from tradingagents.constants import DEFAULT_NEUTRAL_WIN_RATE


SYSTEM_PROMPTS = {
    "zh": build_researcher_prompt(
        role_name_zh="巴菲特价值投资分析师",
        role_name_en="Buffett Value Analyst",
        perspective_zh=BUFFETT_PERSPECTIVE_ZH,
        perspective_en=BUFFETT_PERSPECTIVE_EN,
        language="zh",
        analyst_level="senior",
    ),
    "en": build_researcher_prompt(
        role_name_zh="巴菲特价值投资分析师",
        role_name_en="Buffett Value Analyst",
        perspective_zh=BUFFETT_PERSPECTIVE_ZH,
        perspective_en=BUFFETT_PERSPECTIVE_EN,
        language="en",
        analyst_level="senior",
    ),
}


def create_buffett_researcher(llm, memory):
    """
    创建巴菲特价值投资研究员节点
    
    Args:
        llm: LLM 客户端
        memory: 记忆存储
        
    Returns:
        节点函数
    """
    researcher = BaseResearcher(
        researcher_type="buffett_researcher",
        system_prompts=SYSTEM_PROMPTS,
        llm=llm,
        memory=memory,
        default_win_rate=DEFAULT_NEUTRAL_WIN_RATE,
        stance_zh="巴菲特价值投资",
        stance_en="Buffett value investing",
        speaker_label="Buffett",
    )
    return researcher.create_node()
