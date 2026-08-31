from app.core.rate_limit import RateLimiter
import time

def test_rate_limiter_mock():
    # Will use mock if redis is unavailable
    limiter = RateLimiter(redis_url="redis://invalid:6379/0")
    assert limiter.use_mock == True
    
    allowed, remaining = limiter.check_limit("test-id", limit=2, window=10)
    assert allowed == True
    
    allowed, remaining = limiter.check_limit("test-id", limit=2, window=10)
    assert allowed == True
    
    # Third request should be blocked
    allowed, remaining = limiter.check_limit("test-id", limit=2, window=10)
    assert allowed == False
