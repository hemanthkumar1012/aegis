import redis
import time
import os
import logging
from typing import Tuple
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseRateLimiter(ABC):
    @abstractmethod
    def check_limit(self, identity_name: str, limit: int = 60, window: int = 60) -> Tuple[bool, int]:
        pass
        
    @abstractmethod
    def get_health(self) -> dict:
        pass

import threading

class MockRateLimiter(BaseRateLimiter):
    def __init__(self):
        self._store = {}
        self._lock = threading.Lock()
        
    def check_limit(self, identity_name: str, limit: int = 60, window: int = 60) -> Tuple[bool, int]:
        now = time.time()
        key = f"rate_limit:{identity_name}"
        
        with self._lock:
            if key not in self._store:
                self._store[key] = []
            
            self._store[key] = [t for t in self._store[key] if now - t < window]
            
            if len(self._store[key]) >= limit:
                return False, 0
                
            self._store[key].append(now)
            return True, limit - len(self._store[key])
        
    def get_health(self) -> dict:
        return {"status": "DEGRADED", "backend": "in-memory-mock", "message": "Using development fallback for rate limiting."}

class RedisRateLimiter(BaseRateLimiter):
    def __init__(self, redis_url: str):
        self.r = redis.Redis.from_url(redis_url, socket_connect_timeout=2)
        
    def check_limit(self, identity_name: str, limit: int = 60, window: int = 60) -> Tuple[bool, int]:
        key = f"rate_limit:{identity_name}"
        try:
            # Atomic check-and-increment
            pipeline = self.r.pipeline()
            pipeline.incr(key, 1)
            pipeline.ttl(key)
            result = pipeline.execute()
            
            current = result[0]
            ttl = result[1]
            
            if current == 1 or ttl == -1:
                self.r.expire(key, window)
                
            if current > limit:
                return False, 0
                
            return True, limit - current
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.error(f"Redis rate limiting failed: {e}")
            # Security gateways usually fail open for rate limits to prevent DOSing the service itself, 
            # unless under strict denial rules.
            return True, limit
            
    def get_health(self) -> dict:
        try:
            self.r.ping()
            return {"status": "HEALTHY", "backend": "redis"}
        except Exception as e:
            return {"status": "UNHEALTHY", "backend": "redis", "message": str(e)}

def get_rate_limiter() -> BaseRateLimiter:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    if os.getenv("ENVIRONMENT") == "production":
        return RedisRateLimiter(redis_url)
        
    # In dev, attempt Redis but fallback to Mock
    try:
        client = redis.Redis.from_url(redis_url, socket_connect_timeout=1)
        client.ping()
        return RedisRateLimiter(redis_url)
    except Exception:
        return MockRateLimiter()
