from app.core.rate_limit import get_rate_limiter, MockRateLimiter
import time

def test_rate_limiter_mock():
    # In a test environment without redis, it returns MockRateLimiter
    limiter = get_rate_limiter()
    assert isinstance(limiter, MockRateLimiter)
    
    allowed, remaining = limiter.check_limit("test-id", limit=2, window=10)
    assert allowed == True
    
    allowed, remaining = limiter.check_limit("test-id", limit=2, window=10)
    assert allowed == True
    
    # Third request should be blocked
    allowed, remaining = limiter.check_limit("test-id", limit=2, window=10)
    assert allowed == False
