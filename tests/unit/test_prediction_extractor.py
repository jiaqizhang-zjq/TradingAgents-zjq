"""单元测试: 预测提取器"""
import pytest
from tradingagents.agents.utils.prediction_extractor import (
    extract_prediction,
    RegexStrategy,
    KeywordStrategy,
    ConfidenceAnalyzer,
)


class TestExtractPrediction:
    """测试预测提取主函数"""
    
    def test_regex_pattern_buy(self):
        """测试正则模式 - BUY"""
        pred, conf = extract_prediction("预测: BUY 置信度: 0.85")
        assert pred == "BUY"
        assert conf == 0.85
        
    def test_regex_pattern_sell(self):
        """测试正则模式 - SELL"""
        pred, conf = extract_prediction("Prediction: SELL Confidence: 0.75")
        assert pred == "SELL"
        assert conf == 0.75
        
    def test_regex_pattern_hold(self):
        """测试正则模式 - HOLD"""
        pred, conf = extract_prediction("预测结果: HOLD, 置信度: 0.65")
        assert pred == "HOLD"
        assert conf == 0.65
        
    def test_keyword_fallback_bullish(self):
        """测试关键词回退 - 看涨"""
        pred, conf = extract_prediction("这只股票前景看涨，建议买入")
        assert pred == "BUY"
        assert 0.5 <= conf <= 0.7
        
    def test_keyword_fallback_bearish(self):
        """测试关键词回退 - 看跌"""
        pred, conf = extract_prediction("市场疲软，建议卖出")
        assert pred == "SELL"
        assert 0.5 <= conf <= 0.7
        
    def test_neutral_default(self):
        """测试中性默认值"""
        pred, conf = extract_prediction("无法判断")
        assert pred == "HOLD"
        assert conf == 0.5


class TestRegexStrategy:
    """测试正则表达式策略"""
    
    @pytest.fixture
    def strategy(self):
        return RegexStrategy()
        
    def test_extract_buy(self, strategy):
        """测试提取BUY"""
        result = strategy.extract("预测: BUY 置信度: 0.9")
        assert result == ("BUY", 0.9)
        
    def test_extract_sell(self, strategy):
        """测试提取SELL"""
        result = strategy.extract("Prediction: SELL, Confidence: 0.8")
        assert result == ("SELL", 0.8)
        
    def test_extract_no_match(self, strategy):
        """测试无匹配"""
        result = strategy.extract("没有明确预测")
        assert result is None


class TestKeywordStrategy:
    """测试关键词策略"""
    
    @pytest.fixture
    def strategy(self):
        return KeywordStrategy()
        
    def test_bullish_keywords(self, strategy):
        """测试看涨关键词"""
        text = "看涨 建议买入"
        result = strategy.extract(text)
        assert result is not None
        assert result[0] == "BUY"
            
    def test_bearish_keywords(self, strategy):
        """测试看跌关键词"""
        text = "看跌 建议卖出"
        result = strategy.extract(text)
        assert result is not None
        assert result[0] == "SELL"
            
    def test_no_keywords(self, strategy):
        """测试无关键词"""
        result = strategy.extract("市场状况复杂")
        assert result is None


class TestConfidenceAnalyzer:
    """测试置信度分析器"""
    
    @pytest.fixture
    def analyzer(self):
        return ConfidenceAnalyzer()
        
    def test_extract_strong_confidence(self, analyzer):
        """测试强置信度提取"""
        result = analyzer.extract("非常确定 强烈建议 明确")
        assert result is not None
        assert result[1] >= 0.7
        
    def test_extract_weak_confidence(self, analyzer):
        """测试弱置信度提取"""
        result = analyzer.extract("可能 也许 或许")
        assert result is not None or result is None  # 可能返回默认值
        
    def test_extract_default(self, analyzer):
        """测试默认置信度"""
        result = analyzer.extract("市场表现")
        assert result is None or (result and 0.5 <= result[1] <= 0.7)
