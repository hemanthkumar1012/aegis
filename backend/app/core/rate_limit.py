import redis
import time
from typing import Tuple

# Simple mocked fallback if redis isn't available
_mock_store = {}

class RateLimiter:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.use_mock = False
        try:
            self.r = redis.Redis.from_url(redis_url, socket_connect_timeout=1)
            self.r.ping()
        except (redis.ConnectionError, redis.TimeoutError):
            print("Redis not available, using mock rate limiter.")
            self.use_mock = True

    def check_limit(self, identity_name: str, limit: int = 60, window: int = 60) -> Tuple[bool, int]:
        """Returns (is_allowed, requests_remaining)"""
        key = f"rate_limit:{identity_name}"
        
        if self.use_mock:
            now = time.time()
            if key not in _mock_store:
                _mock_store[key] = []
            
            # clean up old
            _mock_store[key] = [t for t in _mock_store[key] if now - t < window]
            
            if len(_mock_store[key]) >= limit:
                return False, 0
                
            _mock_store[key].append(now)
            return True, limit - len(_mock_store[key])
            
        else:
            current = self.r.get(key)
            if current and int(current) >= limit:
                return False, 0
            
            pipeline = self.r.pipeline()
            pipeline.incr(key, 1)
            pipeline.expire(key, window)
            result = pipeline.execute()
            
            requests = result[0]
            return True, limit - requests
