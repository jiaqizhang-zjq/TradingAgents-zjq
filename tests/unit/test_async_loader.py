"""
异步数据加载器单元测试
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from tradingagents.dataflows.async_data_loader import AsyncDataLoader


class TestAsyncDataLoader:
    """测试异步数据加载器"""
    
    def test_init(self):
        """测试初始化"""
        loader = AsyncDataLoader("AAPL", "2024-01-01", lookback_days=180, max_workers=4)
        
        assert loader.ticker == "AAPL"
        assert loader.end_date == "2024-01-01"
        assert loader.lookback_days == 180
        assert loader.max_workers == 4
        assert loader.start_date == "2023-07-05"
    
    @patch('tradingagents.dataflows.async_data_loader.route_to_vendor')
    def test_load_stock_data(self, mock_route):
        """测试加载股票数据"""
        mock_route.return_value = "date,open,high,low,close,volume\n2024-01-01,100,105,95,102,1000000"
        
        loader = AsyncDataLoader("AAPL", "2024-01-01")
        loader._load_stock_data()
        
        assert loader.stock_data_str != ""
        assert "2024-01-01" in loader.stock_data_str
        mock_route.assert_called_once()
    
    @patch('tradingagents.dataflows.async_data_loader.route_to_vendor')
    def test_load_fundamentals_data(self, mock_route):
        """测试加载基本面数据"""
        mock_route.return_value = "PE Ratio: 25.5"
        
        loader = AsyncDataLoader("AAPL", "2024-01-01")
        loader._load_fundamentals_data()
        
        assert loader.fundamentals == "PE Ratio: 25.5"
        mock_route.assert_called_once_with("get_fundamentals", "AAPL")
    
    @patch('tradingagents.dataflows.async_data_loader.route_to_vendor')
    def test_load_balance_sheet_data(self, mock_route):
        """测试加载资产负债表"""
        mock_route.return_value = "Total Assets: 1000000"
        
        loader = AsyncDataLoader("AAPL", "2024-01-01")
        loader._load_balance_sheet_data()
        
        assert loader.balance_sheet == "Total Assets: 1000000"
        mock_route.assert_called_once_with("get_balance_sheet", "AAPL")
    
    @patch('tradingagents.dataflows.async_data_loader.route_to_vendor')
    def test_error_handling(self, mock_route):
        """测试错误处理"""
        mock_route.side_effect = Exception("API Error")
        
        loader = AsyncDataLoader("AAPL", "2024-01-01")
        loader._load_fundamentals_data()
        
        assert "Error loading fundamentals" in loader.fundamentals
    
    def test_getter_methods(self):
        """测试getter方法"""
        loader = AsyncDataLoader("AAPL", "2024-01-01")
        loader.stock_data_str = "test_data"
        loader.fundamentals = "test_fundamentals"
        loader.indicators = {"rsi": "test_rsi"}
        
        assert loader.get_stock_data() == "test_data"
        assert loader.get_fundamentals() == "test_fundamentals"
        assert loader.get_indicator("rsi") == "test_rsi"
        assert "not available" in loader.get_indicator("unknown")
    
    @patch('tradingagents.dataflows.async_data_loader.route_to_vendor')
    def test_async_load_all_data(self, mock_route):
        """测试异步加载所有数据"""
        mock_route.return_value = "mock_data"
        
        loader = AsyncDataLoader("AAPL", "2024-01-01", max_workers=2)
        asyncio.run(loader.load_all_data_async())
        
        # 验证多个数据源被调用
        assert mock_route.call_count >= 6  # 至少6个数据源
    
    @patch('tradingagents.dataflows.async_data_loader.route_to_vendor')
    def test_sync_load_wrapper(self, mock_route):
        """测试同步包装器"""
        mock_route.return_value = "mock_data"
        
        loader = AsyncDataLoader("AAPL", "2024-01-01", max_workers=2)
        loader.load_all_data_sync()
        
        # 验证同步调用也能工作
        assert mock_route.call_count >= 6
