"""单元测试: 数据统计收集器"""
import pytest
from tradingagents.dataflows.core.statistics_collector import StatisticsCollector


class TestStatisticsCollector:
    """测试统计收集器"""
    
    @pytest.fixture
    def collector(self):
        """创建测试用收集器"""
        return StatisticsCollector()
        
    def test_initialization(self, collector):
        """测试初始化"""
        assert collector._api_calls == {}
        assert collector._cache_hits == {}
        assert collector._cache_misses == {}
        assert collector._errors == {}
        
    def test_record_api_call(self, collector):
        """测试记录API调用"""
        collector.record_api_call("yfinance", "AAPL")
        collector.record_api_call("yfinance", "AAPL")
        collector.record_api_call("yfinance", "TSLA")
        
        stats = collector.get_statistics()
        assert stats["api_calls"]["yfinance"] == 3
        
    def test_record_cache_hit(self, collector):
        """测试记录缓存命中"""
        collector.record_cache_hit("yfinance", "AAPL")
        collector.record_cache_hit("yfinance", "AAPL")
        
        stats = collector.get_statistics()
        assert stats["cache_hits"]["yfinance"] == 2
        
    def test_record_cache_miss(self, collector):
        """测试记录缓存未命中"""
        collector.record_cache_miss("yfinance", "AAPL")
        
        stats = collector.get_statistics()
        assert stats["cache_misses"]["yfinance"] == 1
        
    def test_record_error(self, collector):
        """测试记录错误"""
        collector.record_error("yfinance", "AAPL", "Timeout")
        collector.record_error("yfinance", "TSLA", "Timeout")
        collector.record_error("akshare", "600519", "NotFound")
        
        stats = collector.get_statistics()
        assert stats["errors"]["yfinance"] == 2
        assert stats["errors"]["akshare"] == 1
        
    def test_get_statistics_comprehensive(self, collector):
        """测试获取完整统计数据"""
        # 模拟一系列操作
        collector.record_api_call("yfinance", "AAPL")
        collector.record_api_call("yfinance", "AAPL")
        collector.record_cache_hit("yfinance", "AAPL")
        collector.record_cache_miss("yfinance", "TSLA")
        collector.record_error("yfinance", "MSFT", "Timeout")
        
        stats = collector.get_statistics()
        
        assert stats["api_calls"]["yfinance"] == 2
        assert stats["cache_hits"]["yfinance"] == 1
        assert stats["cache_misses"]["yfinance"] == 1
        assert stats["errors"]["yfinance"] == 1
        
    def test_reset(self, collector):
        """测试重置统计"""
        collector.record_api_call("yfinance", "AAPL")
        collector.record_cache_hit("yfinance", "AAPL")
        collector.reset()
        
        stats = collector.get_statistics()
        assert stats["api_calls"] == {}
        assert stats["cache_hits"] == {}
        assert stats["cache_misses"] == {}
        assert stats["errors"] == {}
