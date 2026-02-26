"""输入验证模块

提供统一的输入验证函数，防止无效输入和潜在安全风险
"""
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class ValidationError(Exception):
    """验证错误异常"""
    pass


def validate_symbol(symbol: str) -> str:
    """验证股票代码格式
    
    Args:
        symbol: 股票代码，如 'AAPL', 'TSLA'
        
    Returns:
        str: 清理后的大写股票代码
        
    Raises:
        ValidationError: 股票代码格式不正确
    """
    if not symbol or not isinstance(symbol, str):
        raise ValidationError("股票代码不能为空")
    
    symbol = symbol.strip().upper()
    
    # 验证格式：1-10个字母或字母+数字，可能包含点或短横线（如 BRK.B）
    pattern = r'^[A-Z][A-Z0-9\.\-]{0,9}$'
    if not re.match(pattern, symbol):
        raise ValidationError(
            f"股票代码格式不正确: '{symbol}'. "
            f"应为1-10个大写字母/数字组合，可包含点或短横线"
        )
    
    return symbol


def validate_date(date_str: str, date_name: str = "日期") -> str:
    """验证日期格式 (YYYY-MM-DD)
    
    Args:
        date_str: 日期字符串
        date_name: 日期字段名称（用于错误消息）
        
    Returns:
        str: 验证后的日期字符串
        
    Raises:
        ValidationError: 日期格式不正确或日期无效
    """
    if not date_str or not isinstance(date_str, str):
        raise ValidationError(f"{date_name}不能为空")
    
    # 验证格式
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(pattern, date_str):
        raise ValidationError(
            f"{date_name}格式不正确: '{date_str}'. "
            f"应为 YYYY-MM-DD 格式"
        )
    
    # 验证日期有效性
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError as e:
        raise ValidationError(f"{date_name}无效: '{date_str}'. {str(e)}")
    
    return date_str


def validate_date_range(
    start_date: str, 
    end_date: str, 
    max_days: Optional[int] = None,
    allow_future: bool = False
) -> tuple:
    """验证日期范围
    
    Args:
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        max_days: 最大允许天数差，None表示不限制
        allow_future: 是否允许未来日期
        
    Returns:
        tuple: 验证后的 (start_date, end_date)
        
    Raises:
        ValidationError: 日期范围不正确
    """
    start_date = validate_date(start_date, "开始日期")
    end_date = validate_date(end_date, "结束日期")
    
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    if start_dt > end_dt:
        raise ValidationError(
            f"开始日期 ({start_date}) 不能晚于结束日期 ({end_date})"
        )
    
    if not allow_future:
        if start_dt > today:
            raise ValidationError(f"开始日期 ({start_date}) 不能是未来日期")
        if end_dt > today:
            raise ValidationError(f"结束日期 ({end_date}) 不能是未来日期")
    
    if max_days is not None:
        days_diff = (end_dt - start_dt).days
        if days_diff > max_days:
            raise ValidationError(
                f"日期范围过大: {days_diff}天 (最大允许: {max_days}天)"
            )
    
    return start_date, end_date


def validate_confidence(confidence: float) -> float:
    """验证置信度值
    
    Args:
        confidence: 置信度值
        
    Returns:
        float: 验证后的置信度
        
    Raises:
        ValidationError: 置信度不在有效范围内
    """
    if not isinstance(confidence, (int, float)):
        raise ValidationError(f"置信度必须是数字，实际类型: {type(confidence)}")
    
    if not 0.0 <= confidence <= 1.0:
        raise ValidationError(
            f"置信度必须在 [0.0, 1.0] 范围内，实际值: {confidence}"
        )
    
    return float(confidence)


def validate_prediction(prediction: str) -> str:
    """验证预测类型
    
    Args:
        prediction: 预测类型字符串
        
    Returns:
        str: 标准化的预测类型 ('BUY', 'SELL', 'HOLD')
        
    Raises:
        ValidationError: 预测类型无效
    """
    if not prediction or not isinstance(prediction, str):
        raise ValidationError("预测类型不能为空")
    
    prediction = prediction.strip().upper()
    
    # 中英文映射
    prediction_map = {
        '买入': 'BUY',
        '卖出': 'SELL', 
        '持有': 'HOLD',
    }
    
    if prediction in prediction_map:
        prediction = prediction_map[prediction]
    
    if prediction not in {'BUY', 'SELL', 'HOLD'}:
        raise ValidationError(
            f"预测类型无效: '{prediction}'. "
            f"必须是 BUY/SELL/HOLD 或 买入/卖出/持有"
        )
    
    return prediction


def sanitize_string(text: str, max_length: int = 1000) -> str:
    """清理和限制字符串长度（防止注入攻击）
    
    Args:
        text: 输入文本
        max_length: 最大允许长度
        
    Returns:
        str: 清理后的文本
        
    Raises:
        ValidationError: 文本过长
    """
    if not isinstance(text, str):
        raise ValidationError(f"输入必须是字符串，实际类型: {type(text)}")
    
    # 移除控制字符
    text = ''.join(char for char in text if char.isprintable() or char in '\n\t')
    
    if len(text) > max_length:
        raise ValidationError(
            f"文本过长: {len(text)}字符 (最大允许: {max_length}字符)"
        )
    
    return text.strip()


def validate_trading_params(
    symbol: str,
    trade_date: str,
    prediction: Optional[str] = None,
    confidence: Optional[float] = None
) -> Dict[str, Any]:
    """一次性验证交易参数
    
    Args:
        symbol: 股票代码
        trade_date: 交易日期
        prediction: 预测类型（可选）
        confidence: 置信度（可选）
        
    Returns:
        dict: 验证后的参数字典
        
    Raises:
        ValidationError: 任何参数验证失败
    """
    result = {
        'symbol': validate_symbol(symbol),
        'trade_date': validate_date(trade_date, "交易日期")
    }
    
    if prediction is not None:
        result['prediction'] = validate_prediction(prediction)
    
    if confidence is not None:
        result['confidence'] = validate_confidence(confidence)
    
    return result
