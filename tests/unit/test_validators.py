"""单元测试: 输入验证器模块"""
import pytest
from datetime import datetime, timedelta
from tradingagents.utils.validators import (
    validate_symbol,
    validate_date,
    validate_date_range,
)
from tradingagents.exceptions import ValidationError


class TestValidateSymbol:
    """测试股票代码验证"""
    
    def test_valid_symbols(self):
        """测试有效股票代码"""
        assert validate_symbol("AAPL") == "AAPL"
        assert validate_symbol("TSLA") == "TSLA"
        assert validate_symbol("600519") == "600519"
        
    def test_invalid_symbols(self):
        """测试无效股票代码"""
        with pytest.raises(ValidationError, match="Symbol cannot be empty"):
            validate_symbol("")
        with pytest.raises(ValidationError, match="Symbol cannot be empty"):
            validate_symbol("   ")
        with pytest.raises(ValidationError):
            validate_symbol("A" * 21)
        with pytest.raises(ValidationError):
            validate_symbol("AA@PL")
        with pytest.raises(ValidationError):
            validate_symbol("AA PL")


class TestValidateDate:
    """测试日期验证"""
    
    def test_valid_dates(self):
        """测试有效日期"""
        assert validate_date("2024-01-01") == "2024-01-01"
        assert validate_date("2023-12-31") == "2023-12-31"
        
    def test_invalid_date_format(self):
        """测试无效日期格式"""
        with pytest.raises(ValidationError, match="Invalid date format"):
            validate_date("2024/01/01")
        with pytest.raises(ValidationError, match="Invalid date format"):
            validate_date("01-01-2024")
        with pytest.raises(ValidationError):
            validate_date("")
            
    def test_invalid_date_value(self):
        """测试无效日期值"""
        with pytest.raises(ValidationError, match="Invalid date format"):
            validate_date("2024-02-30")
        with pytest.raises(ValidationError, match="Invalid date format"):
            validate_date("2024-13-01")


class TestValidateDateRange:
    """测试日期范围验证"""
    
    def test_valid_date_range(self):
        """测试有效日期范围"""
        start, end = validate_date_range("2024-01-01", "2024-12-31")
        assert start == "2024-01-01"
        assert end == "2024-12-31"
        
    def test_invalid_date_range(self):
        """测试无效日期范围 - 开始日期晚于结束日期"""
        with pytest.raises(ValidationError, match="Start date .* is after end date"):
            validate_date_range("2024-12-31", "2024-01-01")
            
    def test_date_range_too_long(self):
        """测试日期范围过长"""
        start = "2020-01-01"
        end = "2025-01-01"
        with pytest.raises(ValidationError):
            validate_date_range(start, end)
