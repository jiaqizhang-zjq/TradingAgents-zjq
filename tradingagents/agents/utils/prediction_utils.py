"""通用的预测结果提取工具函数。"""

import re
from typing import Tuple

# 中文到英文的预测映射
ZH_PREDICTION_MAP = {"买入": "BUY", "卖出": "SELL", "持有": "HOLD"}


def extract_prediction(
    response_content: str,
    language: str,
    zh_pattern: str,
    en_pattern: str,
    default_confidence: float = 0.8,
) -> Tuple[str, float]:
    """从 LLM 响应文本中提取预测结果和置信度。

    Args:
        response_content: LLM 返回的响应文本
        language: 当前语言 ("zh" / "en")
        zh_pattern: 中文正则表达式模式（group 1=预测, group 2=置信度百分比）
        en_pattern: 英文正则表达式模式（group 1=预测, group 2=置信度百分比）
        default_confidence: 默认置信度（未匹配时使用）

    Returns:
        (prediction, confidence) 元组
    """
    prediction = "HOLD"
    confidence = default_confidence

    pattern = zh_pattern if language == "zh" else en_pattern
    match = re.search(pattern, response_content, re.IGNORECASE)

    if match:
        prediction = match.group(1).upper()
        prediction = ZH_PREDICTION_MAP.get(prediction, prediction)
        confidence = int(match.group(2)) / 100.0

    return prediction, confidence
