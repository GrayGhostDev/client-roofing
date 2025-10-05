"""
Redis Client Configuration for iSwitch Roofs CRM

Provides Redis connection and utility functions for caching,
session management, and real-time data operations.

Author: iSwitch Roofs Development Team
Date: 2025-01-04
"""

import os
import json
import logging
from typing import Optional, Any, Dict, List
import redis
from redis.exceptions import ConnectionError, TimeoutError

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis client wrapper with connection pooling and error handling

    Features:
    - Connection pooling for performance
    - Automatic reconnection on failure
    - JSON serialization/deserialization
    - Key expiration management
    - Pub/Sub support
    """

    def __init__(self):
        """Initialize Redis connection with configuration from environment"""
        self.host = os.getenv('REDIS_HOST', 'localhost')
        self.port = int(os.getenv('REDIS_PORT', 6379))
        self.db = int(os.getenv('REDIS_DB', 0))
        self.password = os.getenv('REDIS_PASSWORD', None)
        self.max_connections = int(os.getenv('REDIS_MAX_CONNECTIONS', 50))
        self.socket_timeout = int(os.getenv('REDIS_SOCKET_TIMEOUT', 5))
        self.connection_pool = None
        self.client = None
        self.is_connected = False

        # Initialize connection
        self._connect()

    def _connect(self):
        """Establish Redis connection with pooling"""
        try:
            # Create connection pool
            self.connection_pool = redis.ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                max_connections=self.max_connections,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_timeout,
                decode_responses=True
            )

            # Create Redis client
            self.client = redis.Redis(connection_pool=self.connection_pool)

            # Test connection
            self.client.ping()
            self.is_connected = True

            logger.info(f"Redis connected successfully to {self.host}:{self.port}")

        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            self.is_connected = False

            # Create mock client for development
            self.client = MockRedisClient()
            logger.warning("Using mock Redis client for development")

    def _ensure_connected(self):
        """Ensure Redis connection is active"""
        if not self.is_connected:
            self._connect()

    def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        try:
            self._ensure_connected()
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {str(e)}")
            return None

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """
        Set key-value pair

        Args:
            key: Redis key
            value: Value to store
            ex: Optional expiration in seconds

        Returns:
            Success boolean
        """
        try:
            self._ensure_connected()
            return self.client.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {str(e)}")
            return False

    def setex(self, key: str, seconds: int, value: str) -> bool:
        """Set key with expiration"""
        try:
            self._ensure_connected()
            return self.client.setex(key, seconds, value)
        except Exception as e:
            logger.error(f"Redis SETEX error for key {key}: {str(e)}")
            return False

    def delete(self, *keys: str) -> int:
        """Delete one or more keys"""
        try:
            self._ensure_connected()
            return self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis DELETE error: {str(e)}")
            return 0

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            self._ensure_connected()
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {str(e)}")
            return False

    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on existing key"""
        try:
            self._ensure_connected()
            return self.client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key {key}: {str(e)}")
            return False

    def ttl(self, key: str) -> int:
        """Get time to live for key"""
        try:
            self._ensure_connected()
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error for key {key}: {str(e)}")
            return -2

    def incr(self, key: str) -> int:
        """Increment integer value"""
        try:
            self._ensure_connected()
            return self.client.incr(key)
        except Exception as e:
            logger.error(f"Redis INCR error for key {key}: {str(e)}")
            return 0

    def decr(self, key: str) -> int:
        """Decrement integer value"""
        try:
            self._ensure_connected()
            return self.client.decr(key)
        except Exception as e:
            logger.error(f"Redis DECR error for key {key}: {str(e)}")
            return 0

    def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field value"""
        try:
            self._ensure_connected()
            return self.client.hget(name, key)
        except Exception as e:
            logger.error(f"Redis HGET error for {name}:{key}: {str(e)}")
            return None

    def hset(self, name: str, key: str, value: str) -> bool:
        """Set hash field value"""
        try:
            self._ensure_connected()
            return bool(self.client.hset(name, key, value))
        except Exception as e:
            logger.error(f"Redis HSET error for {name}:{key}: {str(e)}")
            return False

    def hgetall(self, name: str) -> Dict[str, str]:
        """Get all hash fields and values"""
        try:
            self._ensure_connected()
            return self.client.hgetall(name) or {}
        except Exception as e:
            logger.error(f"Redis HGETALL error for {name}: {str(e)}")
            return {}

    def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields"""
        try:
            self._ensure_connected()
            return self.client.hdel(name, *keys)
        except Exception as e:
            logger.error(f"Redis HDEL error for {name}: {str(e)}")
            return 0

    def lpush(self, key: str, *values: str) -> int:
        """Push values to list head"""
        try:
            self._ensure_connected()
            return self.client.lpush(key, *values)
        except Exception as e:
            logger.error(f"Redis LPUSH error for key {key}: {str(e)}")
            return 0

    def rpush(self, key: str, *values: str) -> int:
        """Push values to list tail"""
        try:
            self._ensure_connected()
            return self.client.rpush(key, *values)
        except Exception as e:
            logger.error(f"Redis RPUSH error for key {key}: {str(e)}")
            return 0

    def lpop(self, key: str) -> Optional[str]:
        """Pop value from list head"""
        try:
            self._ensure_connected()
            return self.client.lpop(key)
        except Exception as e:
            logger.error(f"Redis LPOP error for key {key}: {str(e)}")
            return None

    def rpop(self, key: str) -> Optional[str]:
        """Pop value from list tail"""
        try:
            self._ensure_connected()
            return self.client.rpop(key)
        except Exception as e:
            logger.error(f"Redis RPOP error for key {key}: {str(e)}")
            return None

    def lrange(self, key: str, start: int, stop: int) -> List[str]:
        """Get list range"""
        try:
            self._ensure_connected()
            return self.client.lrange(key, start, stop) or []
        except Exception as e:
            logger.error(f"Redis LRANGE error for key {key}: {str(e)}")
            return []

    def sadd(self, key: str, *values: str) -> int:
        """Add members to set"""
        try:
            self._ensure_connected()
            return self.client.sadd(key, *values)
        except Exception as e:
            logger.error(f"Redis SADD error for key {key}: {str(e)}")
            return 0

    def srem(self, key: str, *values: str) -> int:
        """Remove members from set"""
        try:
            self._ensure_connected()
            return self.client.srem(key, *values)
        except Exception as e:
            logger.error(f"Redis SREM error for key {key}: {str(e)}")
            return 0

    def smembers(self, key: str) -> set:
        """Get all set members"""
        try:
            self._ensure_connected()
            return self.client.smembers(key) or set()
        except Exception as e:
            logger.error(f"Redis SMEMBERS error for key {key}: {str(e)}")
            return set()

    def sismember(self, key: str, value: str) -> bool:
        """Check if value is in set"""
        try:
            self._ensure_connected()
            return bool(self.client.sismember(key, value))
        except Exception as e:
            logger.error(f"Redis SISMEMBER error for key {key}: {str(e)}")
            return False

    def publish(self, channel: str, message: str) -> int:
        """Publish message to channel"""
        try:
            self._ensure_connected()
            return self.client.publish(channel, message)
        except Exception as e:
            logger.error(f"Redis PUBLISH error for channel {channel}: {str(e)}")
            return 0

    def subscribe(self, *channels: str):
        """Subscribe to channels"""
        try:
            self._ensure_connected()
            pubsub = self.client.pubsub()
            pubsub.subscribe(*channels)
            return pubsub
        except Exception as e:
            logger.error(f"Redis SUBSCRIBE error: {str(e)}")
            return None

    def scan_keys(self, pattern: str = '*', count: int = 100) -> List[str]:
        """Scan for keys matching pattern"""
        try:
            self._ensure_connected()
            keys = []
            cursor = 0

            while True:
                cursor, partial_keys = self.client.scan(cursor, match=pattern, count=count)
                keys.extend(partial_keys)

                if cursor == 0:
                    break

            return keys

        except Exception as e:
            logger.error(f"Redis SCAN error for pattern {pattern}: {str(e)}")
            return []

    def pipeline(self):
        """Create pipeline for batch operations"""
        try:
            self._ensure_connected()
            return self.client.pipeline()
        except Exception as e:
            logger.error(f"Redis PIPELINE error: {str(e)}")
            return None

    def close(self):
        """Close Redis connection"""
        try:
            if self.connection_pool:
                self.connection_pool.disconnect()
            self.is_connected = False
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {str(e)}")


class MockRedisClient:
    """
    Mock Redis client for development/testing when Redis is not available

    Implements basic in-memory storage with Redis-like interface
    """

    def __init__(self):
        self.storage = {}
        self.expiry = {}
        logger.info("Initialized mock Redis client")

    def get(self, key: str) -> Optional[str]:
        return self.storage.get(key)

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        self.storage[key] = value
        if ex:
            import time
            self.expiry[key] = time.time() + ex
        return True

    def setex(self, key: str, seconds: int, value: str) -> bool:
        import time
        self.storage[key] = value
        self.expiry[key] = time.time() + seconds
        return True

    def delete(self, *keys: str) -> int:
        count = 0
        for key in keys:
            if key in self.storage:
                del self.storage[key]
                count += 1
        return count

    def exists(self, key: str) -> bool:
        return key in self.storage

    def expire(self, key: str, seconds: int) -> bool:
        if key in self.storage:
            import time
            self.expiry[key] = time.time() + seconds
            return True
        return False

    def ttl(self, key: str) -> int:
        if key in self.expiry:
            import time
            remaining = self.expiry[key] - time.time()
            return int(remaining) if remaining > 0 else -2
        return -1 if key in self.storage else -2

    def incr(self, key: str) -> int:
        val = int(self.storage.get(key, 0)) + 1
        self.storage[key] = str(val)
        return val

    def decr(self, key: str) -> int:
        val = int(self.storage.get(key, 0)) - 1
        self.storage[key] = str(val)
        return val

    def ping(self) -> bool:
        return True

    # Add other methods as needed with basic implementations
    def hget(self, name: str, key: str) -> Optional[str]:
        hash_key = f"{name}:{key}"
        return self.storage.get(hash_key)

    def hset(self, name: str, key: str, value: str) -> bool:
        hash_key = f"{name}:{key}"
        self.storage[hash_key] = value
        return True

    def hgetall(self, name: str) -> Dict[str, str]:
        prefix = f"{name}:"
        result = {}
        for k, v in self.storage.items():
            if k.startswith(prefix):
                field = k[len(prefix):]
                result[field] = v
        return result

    def hdel(self, name: str, *keys: str) -> int:
        count = 0
        for key in keys:
            hash_key = f"{name}:{key}"
            if hash_key in self.storage:
                del self.storage[hash_key]
                count += 1
        return count

    def lpush(self, key: str, *values: str) -> int:
        lst = json.loads(self.storage.get(key, '[]'))
        for value in values:
            lst.insert(0, value)
        self.storage[key] = json.dumps(lst)
        return len(lst)

    def rpush(self, key: str, *values: str) -> int:
        lst = json.loads(self.storage.get(key, '[]'))
        lst.extend(values)
        self.storage[key] = json.dumps(lst)
        return len(lst)

    def lpop(self, key: str) -> Optional[str]:
        lst = json.loads(self.storage.get(key, '[]'))
        if lst:
            val = lst.pop(0)
            self.storage[key] = json.dumps(lst)
            return val
        return None

    def rpop(self, key: str) -> Optional[str]:
        lst = json.loads(self.storage.get(key, '[]'))
        if lst:
            val = lst.pop()
            self.storage[key] = json.dumps(lst)
            return val
        return None

    def lrange(self, key: str, start: int, stop: int) -> List[str]:
        lst = json.loads(self.storage.get(key, '[]'))
        return lst[start:stop+1] if stop >= 0 else lst[start:]

    def sadd(self, key: str, *values: str) -> int:
        s = set(json.loads(self.storage.get(key, '[]')))
        orig_len = len(s)
        s.update(values)
        self.storage[key] = json.dumps(list(s))
        return len(s) - orig_len

    def srem(self, key: str, *values: str) -> int:
        s = set(json.loads(self.storage.get(key, '[]')))
        orig_len = len(s)
        s.difference_update(values)
        self.storage[key] = json.dumps(list(s))
        return orig_len - len(s)

    def smembers(self, key: str) -> set:
        return set(json.loads(self.storage.get(key, '[]')))

    def sismember(self, key: str, value: str) -> bool:
        s = set(json.loads(self.storage.get(key, '[]')))
        return value in s

    def publish(self, channel: str, message: str) -> int:
        # Mock publish, just log
        logger.debug(f"Mock publish to {channel}: {message}")
        return 1

    def subscribe(self, *channels: str):
        # Mock subscribe
        logger.debug(f"Mock subscribe to channels: {channels}")
        return None

    def scan(self, cursor: int, match: str = '*', count: int = 100):
        # Mock scan
        import fnmatch
        matching_keys = [k for k in self.storage.keys() if fnmatch.fnmatch(k, match)]

        # Simple pagination
        start = cursor
        end = min(cursor + count, len(matching_keys))

        next_cursor = 0 if end >= len(matching_keys) else end

        return next_cursor, matching_keys[start:end]

    def pipeline(self):
        # Return self for basic chaining
        return self


# Create singleton instance
redis_client = RedisClient()


# Export convenience functions
def cache_get(key: str) -> Optional[Any]:
    """Get cached value with JSON deserialization"""
    value = redis_client.get(key)
    if value:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return None


def cache_set(key: str, value: Any, ttl: int = 3600) -> bool:
    """Set cached value with JSON serialization"""
    try:
        json_value = json.dumps(value) if not isinstance(value, str) else value
        return redis_client.setex(key, ttl, json_value)
    except Exception as e:
        logger.error(f"Cache set error: {str(e)}")
        return False


def cache_delete(pattern: str) -> int:
    """Delete cached keys by pattern"""
    keys = redis_client.scan_keys(pattern)
    if keys:
        return redis_client.delete(*keys)
    return 0