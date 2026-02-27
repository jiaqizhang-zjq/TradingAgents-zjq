"""单元测试: 数据供应商注册表"""
import pytest
from tradingagents.dataflows.core.vendor_registry import VendorRegistry


class TestVendorRegistry:
    """测试供应商注册表"""
    
    @pytest.fixture
    def registry(self):
        """创建测试用注册表"""
        return VendorRegistry()
        
    def test_initialization(self, registry):
        """测试初始化 - 应包含默认供应商"""
        assert len(registry._vendors) > 0
        assert "yfinance" in registry._vendors
        assert "akshare" in registry._vendors
        
    def test_get_vendor_priority(self, registry):
        """测试按优先级获取供应商"""
        vendors = registry.get_vendor_priority()
        assert isinstance(vendors, list)
        assert len(vendors) > 0
        # 应按优先级降序排列
        priorities = [v["priority"] for v in vendors]
        assert priorities == sorted(priorities, reverse=True)
        
    def test_get_vendor_info(self, registry):
        """测试获取供应商信息"""
        info = registry.get_vendor_info("yfinance")
        assert info is not None
        assert "name" in info
        assert "priority" in info
        assert info["name"] == "yfinance"
        
    def test_get_vendor_info_not_found(self, registry):
        """测试获取不存在的供应商"""
        info = registry.get_vendor_info("nonexistent")
        assert info is None
        
    def test_is_vendor_available(self, registry):
        """测试检查供应商是否可用"""
        assert registry.is_vendor_available("yfinance") is True
        assert registry.is_vendor_available("nonexistent") is False
        
    def test_get_all_vendors(self, registry):
        """测试获取所有供应商"""
        vendors = registry.get_all_vendors()
        assert isinstance(vendors, list)
        assert len(vendors) > 0
        assert all("name" in v for v in vendors)
