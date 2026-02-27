"""
测试 validators 模块
"""

import pytest
from tradingagents.utils.validators import (
    validate_symbol,
    validate_date,
    validate_date_range,
    validate_confidence,
    validate_prediction,
    sanitize_string,
    validate_trading_params
)


class TestValidateSymbol:
    """测试股票代码验证"""
    
    def test_valid_symbols(self):
        """测试有效的股票代码"""
        assert validate_symbol("AAPL") == "AAPL"
        assert validate_symbol("TSLA") == "TSLA"
        assert validate_symbol("NVDA") == "NVDA"
        assert validate_symbol("MSFT.US") == "MSFT.US"
        assert validate_symbol("0700.HK") == "0700.HK"
    
    def test_invalid_symbols(self):
        """测试无效的股票代码"""
        with pytest.raises(ValueError, match="股票代码不能为空"):
            validate_symbol("")
        
        with pytest.raises(ValueError, match="股票代码不能为空"):
            validate_symbol("   ")
        
        with pytest.raises(ValueError, match="股票代码过长"):
            validate_symbol("A" * 21)
        
        with pytest.raises(ValueError, match="股票代码只能包含"):
            validate_symbol("AAPL@123")
    
    def test_symbol_normalization(self):
        """测试股票代码规范化"""
        assert validate_symbol("  aapl  ") == "AAPL"
        assert validate_symbol("tsla") == "TSLA"


class TestValidateDate:
    """测试日期验证"""
    
    def test_valid_dates(self):
        """测试有效日期"""
        assert validate_date("2024-01-15") == "2024-01-15"
        assert validate_date("2023-12-31") == "2023-12-31"
    
    def test_invalid_dates(self):
        """测试无效日期"""
        with pytest.raises(ValueError, match="日期不能为空"):
            validate_date("")
        
        with pytest.raises(ValueError, match="日期格式必须为 YYYY-MM-DD"):
            validate_date("2024/01/15")
        
        with pytest.raises(ValueError, match="无效的日期"):
            validate_date("2024-13-01")
        
        with pytest.raises(ValueError, match="无效的日期"):
            validate_date("2024-02-30")


class TestValidateDateRange:
    """测试日期范围验证"""
    
    def test_valid_date_ranges(self):
        """测试有效日期范围"""
        start, end = validate_date_range("2024-01-01", "2024-12-31")
        assert start == "2024-01-01"
        assert end == "2024-12-31"
    
    def test_invalid_date_ranges(self):
        """测试无效日期范围"""
        with pytest.raises(ValueError, match="开始日期必须早于或等于结束日期"):
            validate_date_range("2024-12-31", "2024-01-01")


class TestValidateConfidence:
    """测试置信度验证"""
    
    def test_valid_confidence(self):
        """测试有效置信度"""
        assert validate_confidence(0.0) == 0.0
        assert validate_confidence(0.5) == 0.5
        assert validate_confidence(1.0) == 1.0
        assert validate_confidence(0.75) == 0.75
    
    def test_invalid_confidence(self):
        """测试无效置信度"""
        with pytest.raises(ValueError, match="置信度必须在 0-1 之间"):
            validate_confidence(-0.1)
        
        with pytest.raises(ValueError, match="置信度必须在 0-1 之间"):
            validate_confidence(1.1)


class TestValidatePrediction:
    """测试预测类型验证"""
    
    def test_valid_predictions(self):
        """测试有效预测类型"""
        assert validate_prediction("BUY") == "BUY"
        assert validate_prediction("SELL") == "SELL"
        assert validate_prediction("HOLD") == "HOLD"
        assert validate_prediction("buy") == "BUY"
    
    def test_invalid_predictions(self):
        """测试无效预测类型"""
        with pytest.raises(ValueError, match="预测类型必须是"):
            validate_prediction("UNKNOWN")
        
        with pytest.raises(ValueError, match="预测类型不能为空"):
            validate_prediction("")


class TestSanitizeString:
    """测试字符串清理"""
    
    def test_normal_strings(self):
        """测试正常字符串"""
        assert sanitize_string("Hello World") == "Hello World"
        assert sanitize_string("AAPL") == "AAPL"
    
    def test_sql_injection_prevention(self):
        """测试SQL注入防护"""
        dangerous = "'; DROP TABLE users; --"
        cleaned = sanitize_string(dangerous)
        assert "DROP" not in cleaned
        assert ";" not in cleaned
    
    def test_length_limit(self):
        """测试长度限制"""
        long_text = "A" * 2000
        cleaned = sanitize_string(long_text, max_length=100)
        assert len(cleaned) <= 100


class TestValidateTradingParams:
    """测试交易参数一键验证"""
    
    def test_valid_params(self):
        """测试有效参数"""
        params = validate_trading_params(
            symbol="AAPL",
            start_date="2024-01-01",
            end_date="2024-12-31",
            confidence=0.8,
            prediction="BUY"
        )
        assert params["symbol"] == "AAPL"
        assert params["confidence"] == 0.8
        assert params["prediction"] == "BUY"
    
    def test_invalid_params(self):
        """测试无效参数"""
        with pytest.raises(ValueError):
            validate_trading_params(
                symbol="",
                start_date="2024-01-01",
                end_date="2024-12-31"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
