"""单元测试: 重试策略模块"""
import pytest
from tradingagents.dataflows.core.retry_policy import RetryPolicy


class TestRetryPolicy:
    """测试重试策略"""
    
    def test_initialization(self):
        """测试初始化"""
        policy = RetryPolicy(max_attempts=5, delay_seconds=2, backoff_multiplier=2.0)
        assert policy.max_attempts == 5
        assert policy.delay_seconds == 2
        assert policy.backoff_multiplier == 2.0
        
    def test_execute_success_first_try(self):
        """测试首次执行成功"""
        call_count = {"value": 0}
        
        def successful_func():
            call_count["value"] += 1
            return "success"
            
        policy = RetryPolicy(max_attempts=3)
        result = policy.execute(successful_func)
        
        assert result == "success"
        assert call_count["value"] == 1
        
    def test_execute_retries_on_failure(self):
        """测试失败后重试"""
        call_count = {"value": 0}
        
        def failing_func():
            call_count["value"] += 1
            if call_count["value"] < 3:
                raise ValueError("Test error")
            return "success"
            
        policy = RetryPolicy(max_attempts=3, delay_seconds=0)
        result = policy.execute(failing_func)
        
        assert result == "success"
        assert call_count["value"] == 3
        
    def test_execute_gives_up_after_max_attempts(self):
        """测试达到最大重试次数后放弃"""
        call_count = {"value": 0}
        
        def always_failing_func():
            call_count["value"] += 1
            raise ValueError("Always fails")
            
        policy = RetryPolicy(max_attempts=3, delay_seconds=0)
        
        with pytest.raises(ValueError, match="Always fails"):
            policy.execute(always_failing_func)
            
        assert call_count["value"] == 3
