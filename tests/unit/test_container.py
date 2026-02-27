"""单元测试: 依赖注入容器"""
import pytest
from tradingagents.core.container import DependencyContainer


class TestContainer:
    """测试依赖注入容器"""
    
    @pytest.fixture
    def container(self):
        """创建测试用容器"""
        return DependencyContainer()
        
    def test_initialization(self, container):
        """测试初始化"""
        assert container._singletons == {}
        assert container._factories == {}
        
    def test_register_factory(self, container):
        """测试注册工厂函数"""
        def create_service():
            return "test_service"
            
        container.register("service", create_service)
        assert "service" in container._factories
        
    def test_get_creates_singleton(self, container):
        """测试获取单例实例"""
        counter = {"value": 0}
        
        def create_service():
            counter["value"] += 1
            return f"service_{counter['value']}"
            
        container.register("service", create_service)
        
        # 多次获取应返回同一实例
        service1 = container.get("service")
        service2 = container.get("service")
        
        assert service1 == service2
        assert counter["value"] == 1  # 工厂函数只调用一次
        
    def test_get_unregistered_raises_error(self, container):
        """测试获取未注册服务抛出异常"""
        with pytest.raises(KeyError):
            container.get("nonexistent")
            
    def test_reset(self, container):
        """测试重置单例实例"""
        def create_service():
            return "test_service"
            
        container.register("service", create_service, singleton=True)
        container.get("service")  # 创建实例
        
        container.reset_singletons()
        
        assert container._singletons == {}
        # 工厂函数仍然保留
        assert "service" in container._factories
        
    def test_has_service(self, container):
        """测试检查服务是否已注册"""
        def create_service():
            return "test_service"
            
        container.register("service", create_service)
        
        assert container.has("service") is True
        assert container.has("nonexistent") is False
