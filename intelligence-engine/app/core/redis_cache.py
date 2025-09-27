"""
Redis Cache Integration for Milhena
====================================
Simple Redis caching with 60s TTL
"""

import json
import redis
from typing import Optional, Any
from datetime import timedelta


class RedisCache:
    """Simple Redis cache for Milhena responses"""

    def __init__(self, host: str = "localhost", port: int = 6379, ttl_seconds: int = 60):
        """
        Initialize Redis cache

        Args:
            host: Redis host
            port: Redis port
            ttl_seconds: Time to live for cache entries
        """
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=0,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        self.ttl = timedelta(seconds=ttl_seconds)

    def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        try:
            return self.redis_client.get(key)
        except:
            return None

    def set(self, key: str, value: str) -> bool:
        """Set value in cache with TTL"""
        try:
            self.redis_client.setex(key, self.ttl, value)
            return True
        except:
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            self.redis_client.delete(key)
            return True
        except:
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return bool(self.redis_client.exists(key))
        except:
            return False

    def get_json(self, key: str) -> Optional[dict]:
        """Get JSON value from cache"""
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except:
                return None
        return None

    def set_json(self, key: str, value: dict) -> bool:
        """Set JSON value in cache"""
        try:
            json_str = json.dumps(value)
            return self.set(key, json_str)
        except:
            return False

    def ping(self) -> bool:
        """Check Redis connection"""
        try:
            return self.redis_client.ping()
        except:
            return False


# Singleton instance
_instance = None

def get_cache(host: str = "localhost", port: int = 6379) -> RedisCache:
    """Get or create singleton cache instance"""
    global _instance
    if _instance is None:
        _instance = RedisCache(host, port)
    return _instance