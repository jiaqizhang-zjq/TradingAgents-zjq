"""
专家提示词模板系统
==================

本模块提供标准化的专家提示词模板，确保所有研究员和风险分析师都遵循20+年资深专家的标准。

使用说明：
1. 所有研究员（Researcher）必须继承 RESEARCHER_BASE_TEMPLATE
2. 所有风险分析师（Risk Analyst）必须继承 RISK_ANALYST_BASE_TEMPLATE
3. 新增角色时，只需定义角色的特定视角，基础要求会自动包含

模板结构：
- 角色定义（20+年资深专家）
- 基础要求（概率分布、预期收益、仓位管理等）
- 输出格式（标准化的结尾格式）
- 角色特定要求（看涨/看跌/激进/保守等）

架构说明（v2.0 模块化重构）：
- prompts/base_templates.py: 基础模板（身份、要求、输出格式）
- prompts/perspectives.py: 角色视角定义
- 本文件: 组合函数 + 预定义常量 + 向后兼容导出
"""

from typing import Dict, List

# 从子模块导入基础模板
from .prompts.base_templates import (
    EXPERT_IDENTITY_ZH,
    EXPERT_IDENTITY_EN,
    JUNIOR_ANALYST_IDENTITY_ZH,
    JUNIOR_ANALYST_IDENTITY_EN,
    SENIOR_MASTER_IDENTITY_ZH,
    SENIOR_MASTER_IDENTITY_EN,
    RESEARCHER_BASE_REQUIREMENTS_ZH,
    RESEARCHER_BASE_REQUIREMENTS_EN,
    RESEARCHER_OUTPUT_FORMAT_ZH,
    RESEARCHER_OUTPUT_FORMAT_EN,
    RISK_ANALYST_BASE_REQUIREMENTS_ZH,
    RISK_ANALYST_BASE_REQUIREMENTS_EN,
    RISK_ANALYST_OUTPUT_FORMAT_ZH,
    RISK_ANALYST_OUTPUT_FORMAT_EN,
)

# 从子模块导入角色视角
from .prompts.perspectives import (
    BULL_PERSPECTIVE_ZH,
    BULL_PERSPECTIVE_EN,
    BEAR_PERSPECTIVE_ZH,
    BEAR_PERSPECTIVE_EN,
    BUFFETT_PERSPECTIVE_ZH,
    BUFFETT_PERSPECTIVE_EN,
    CATHIE_WOOD_PERSPECTIVE_ZH,
    CATHIE_WOOD_PERSPECTIVE_EN,
    PETER_LYNCH_PERSPECTIVE_ZH,
    PETER_LYNCH_PERSPECTIVE_EN,
    CHARLIE_MUNGER_PERSPECTIVE_ZH,
    CHARLIE_MUNGER_PERSPECTIVE_EN,
    SOROS_PERSPECTIVE_ZH,
    SOROS_PERSPECTIVE_EN,
    DALIO_PERSPECTIVE_ZH,
    DALIO_PERSPECTIVE_EN,
    LIVERMORE_PERSPECTIVE_ZH,
    LIVERMORE_PERSPECTIVE_EN,
    AGGRESSIVE_PERSPECTIVE_ZH,
    CONSERVATIVE_PERSPECTIVE_ZH,
    NEUTRAL_PERSPECTIVE_ZH,
)


# =============================================================================
# 模板组合函数
# =============================================================================

def build_researcher_prompt(
    role_name_zh: str,
    role_name_en: str,
    perspective_zh: str,
    perspective_en: str = "",
    language: str = "zh",
    analyst_level: str = "default",
) -> str:
    """
    构建研究员提示词

    Args:
        role_name_zh: 中文角色名称（如"看涨分析师"）
        role_name_en: 英文角色名称（如"Bull Analyst"）
        perspective_zh: 中文角色特定视角
        perspective_en: 英文角色特定视角（可选）
        language: 语言（"zh"或"en"）
        analyst_level: 分析师级别
            - "junior": 初阶分析师（Bull/Bear），使用 JUNIOR_ANALYST_IDENTITY
            - "senior": 高级分析师（投资大师），使用 SENIOR_MASTER_IDENTITY
            - "default": 通用模板，使用 EXPERT_IDENTITY（向后兼容）

    Returns:
        完整的提示词
    """
    # 根据 analyst_level 选择身份模板
    if analyst_level == "junior":
        identity_zh = JUNIOR_ANALYST_IDENTITY_ZH.format(role_name=role_name_zh)
        identity_en = JUNIOR_ANALYST_IDENTITY_EN.format(role_name=role_name_en)
    elif analyst_level == "senior":
        identity_zh = SENIOR_MASTER_IDENTITY_ZH
        identity_en = SENIOR_MASTER_IDENTITY_EN
    else:
        identity_zh = EXPERT_IDENTITY_ZH.format(role_name=role_name_zh)
        identity_en = EXPERT_IDENTITY_EN.format(role_name=role_name_en)

    if language == "zh":
        return f"""{identity_zh}

{RESEARCHER_BASE_REQUIREMENTS_ZH}

{perspective_zh}

{RESEARCHER_OUTPUT_FORMAT_ZH}
"""
    else:
        return f"""{identity_en}

{RESEARCHER_BASE_REQUIREMENTS_EN}

{perspective_en if perspective_en else perspective_zh}

{RESEARCHER_OUTPUT_FORMAT_EN}
"""


def build_risk_analyst_prompt(
    role_name_zh: str,
    role_name_en: str,
    perspective_zh: str,
    perspective_en: str = "",
    language: str = "zh"
) -> str:
    """
    构建风险分析师提示词
    
    Args:
        role_name_zh: 中文角色名称（如"激进型风险分析师"）
        role_name_en: 英文角色名称（如"Aggressive Risk Analyst"）
        perspective_zh: 中文角色特定视角
        perspective_en: 英文角色特定视角（可选）
        language: 语言（"zh"或"en"）
    
    Returns:
        完整的提示词
    """
    if language == "zh":
        return f"""{EXPERT_IDENTITY_ZH.format(role_name=role_name_zh)}

{RISK_ANALYST_BASE_REQUIREMENTS_ZH}

{perspective_zh}

{RISK_ANALYST_OUTPUT_FORMAT_ZH}
"""
    else:
        return f"""{EXPERT_IDENTITY_EN.format(role_name=role_name_en)}

{RISK_ANALYST_BASE_REQUIREMENTS_EN}

{perspective_en if perspective_en else perspective_zh}

{RISK_ANALYST_OUTPUT_FORMAT_EN}
"""


# =============================================================================
# 预定义的标准角色提示词
# =============================================================================

# 标准研究员提示词 - 中文
# Bull/Bear 使用初阶分析师身份（analyst_level="junior"）
STANDARD_BULL_PROMPT_ZH = build_researcher_prompt(
    role_name_zh="看涨分析师",
    role_name_en="Bull Analyst",
    perspective_zh=BULL_PERSPECTIVE_ZH,
    perspective_en=BULL_PERSPECTIVE_EN,
    language="zh",
    analyst_level="junior",
)

STANDARD_BEAR_PROMPT_ZH = build_researcher_prompt(
    role_name_zh="看跌分析师",
    role_name_en="Bear Analyst",
    perspective_zh=BEAR_PERSPECTIVE_ZH,
    perspective_en=BEAR_PERSPECTIVE_EN,
    language="zh",
    analyst_level="junior",
)

# 标准研究员提示词 - 英文（使用模板生成）
STANDARD_BULL_PROMPT_EN = build_researcher_prompt(
    role_name_zh="看涨分析师",
    role_name_en="Bull Analyst",
    perspective_zh=BULL_PERSPECTIVE_ZH,
    perspective_en=BULL_PERSPECTIVE_EN,
    language="en",
    analyst_level="junior",
)

STANDARD_BEAR_PROMPT_EN = build_researcher_prompt(
    role_name_zh="看跌分析师",
    role_name_en="Bear Analyst",
    perspective_zh=BEAR_PERSPECTIVE_ZH,
    perspective_en=BEAR_PERSPECTIVE_EN,
    language="en",
    analyst_level="junior",
)

# 标准风险分析师提示词 - 中文
STANDARD_AGGRESSIVE_PROMPT_ZH = build_risk_analyst_prompt(
    role_name_zh="激进型风险分析师",
    role_name_en="Aggressive Risk Analyst",
    perspective_zh=AGGRESSIVE_PERSPECTIVE_ZH,
    language="zh"
)

STANDARD_CONSERVATIVE_PROMPT_ZH = build_risk_analyst_prompt(
    role_name_zh="保守型风险分析师",
    role_name_en="Conservative Risk Analyst",
    perspective_zh=CONSERVATIVE_PERSPECTIVE_ZH,
    language="zh"
)

STANDARD_NEUTRAL_PROMPT_ZH = build_risk_analyst_prompt(
    role_name_zh="中立型风险分析师",
    role_name_en="Neutral Risk Analyst",
    perspective_zh=NEUTRAL_PERSPECTIVE_ZH,
    language="zh"
)
