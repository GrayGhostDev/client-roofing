"""
Redis Caching Utilities
Production-ready caching for ML predictions with TTL and invalidation
"""

import redis
import json
import hashlib
from functools import wraps
from typing import Optional, Any, Callable
import os
import logging
from datetime import timedelta
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis client configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB_ML", 1))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Cache TTL settings
DEFAULT_TTL = int(os.getenv("ML_CACHE_TTL", 3600))
ENABLED = os.getenv("ML_CACHE_ENABLED", "true").lower() == "true"

# Initialize Redis client
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True
    )
    redis_client.ping()
    logger.info(f"✅ Redis connected: {REDIS_HOST}:{REDIS_PORT} (DB {REDIS_DB})")
except (redis.ConnectionError, redis.TimeoutError) as e:
    logger.warning(f"⚠️  Redis connection failed: {e}. Caching disabled.")
    redis_client = None


def _create_cache_key(prefix: str, *args, **kwargs) -> str:
    """Create deterministic cache key from function arguments"""
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    key_hash = hashlib.md5(
        json.dumps(key_data, sort_keys=True, default=str).encode()
    ).hexdigest()
    return f"{prefix}:{key_hash}"


def cache_prediction(ttl: int = DEFAULT_TTL, key_prefix: str = "ml") -> Callable:
    """Decorator for caching ML prediction results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not ENABLED or redis_client is None:
                logger.debug(f"Cache disabled or unavailable, executing {func.__name__}")
                return await func(*args, **kwargs)

            cache_key = _create_cache_key(key_prefix, *args, **kwargs)

            try:
                cached_value = redis_client.get(cache_key)
                if cached_value:
                    logger.info(f"✅ Cache HIT: {cache_key[:50]}...")
                    return json.loads(cached_value)

                logger.info(f"⚠️  Cache MISS: {cache_key[:50]}...")
                result = await func(*args, **kwargs)

                redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(result, default=str)
                )

                logger.info(f"💾 Cached result with TTL={ttl}s")
                return result

            except redis.RedisError as e:
                logger.error(f"❌ Redis error: {e}. Executing without cache.")
                return await func(*args, **kwargs)

        return wrapper
    return decorator


def invalidate_cache(key_pattern: str) -> int:
    """Invalidate cache entries matching pattern"""
    if not ENABLED or redis_client is None:
        logger.warning("Cache not available for invalidation")
        return 0

    try:
        keys = redis_client.keys(key_pattern)
        if not keys:
            logger.info(f"No cache keys found matching: {key_pattern}")
            return 0

        count = redis_client.delete(*keys)
        logger.info(f"✅ Invalidated {count} cache entries matching: {key_pattern}")
        return count

    except redis.RedisError as e:
        logger.error(f"❌ Cache invalidation failed: {e}")
        return 0


def get_cache_stats() -> dict:
    """Get cache statistics"""
    if not ENABLED or redis_client is None:
        return {"status": "disabled", "enabled": False}

    try:
        info = redis_client.info("stats")
        keyspace = redis_client.info("keyspace")

        db_keys = keyspace.get(f'db{REDIS_DB}', {})
        keys_count = db_keys.get('keys', 0)

        return {
            "status": "healthy",
            "enabled": True,
            "keys": keys_count,
            "keyspace_hits": info.get('keyspace_hits', 0),
            "keyspace_misses": info.get('keyspace_misses', 0),
            "hit_rate": info.get('keyspace_hits', 0) / max(1, info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0)),
            "total_commands": info.get('total_commands_processed', 0),
            "connected_clients": info.get('connected_clients', 0)
        }

    except redis.RedisError as e:
        logger.error(f"❌ Failed to get cache stats: {e}")
        return {"status": "error", "enabled": True, "error": str(e)}


def check_redis_health() -> bool:
    """Check if Redis is healthy"""
    if redis_client is None:
        return False
    try:
        redis_client.ping()
        return True
    except (redis.ConnectionError, redis.TimeoutError):
        return False
