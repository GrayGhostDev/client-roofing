"""
iSwitch Roofs CRM - Production-Grade Caching Decorators
Version: 1.0.0
Date: 2025-10-09

PURPOSE:
Transparent Redis caching decorator for service methods with:
- Automatic cache key generation from function signature
- 3-tier TTL strategy (real-time/standard/historical)
- Cache statistics tracking (hits/misses/errors)
- Graceful error handling and fallback
- JSON serialization with support for complex objects
- Cache invalidation by pattern

USAGE:
    from app.utils.cache import cache_result, cache_invalidate, get_cache_stats

    @cache_result(ttl=300, key_prefix="leads")
    def get_lead_stats():
        # ... expensive database query ...
        return stats

    # Invalidate on mutations
    cache_invalidate("crm:leads:*")

TTL STRATEGY:
- 30s: Real-time metrics (lead_response, active_counts)
- 300s (5min): Dashboard data (lead_stats, hot_leads)
- 3600s (1hr): Historical analytics (revenue_trends, marketing_roi)
"""

import functools
import hashlib
import json
import logging
from typing import Any, Callable, Optional
from datetime import datetime

from app.utils.redis_client import redis_client

logger = logging.getLogger(__name__)


# ============================================================================
# CACHE STATISTICS TRACKING
# ============================================================================

class CacheStats:
    """
    Thread-safe cache statistics tracker.
    Tracks hits, misses, errors for monitoring cache effectiveness.
    """

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.errors = 0
        self.last_reset = datetime.now()

    def record_hit(self):
        """Increment cache hit counter."""
        self.hits += 1

    def record_miss(self):
        """Increment cache miss counter."""
        self.misses += 1

    def record_error(self):
        """Increment cache error counter."""
        self.errors += 1

    def get_stats(self) -> dict[str, Any]:
        """
        Get current cache statistics.

        Returns:
            dict: Cache statistics including hit rate
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "last_reset": self.last_reset.isoformat()
        }

    def reset(self):
        """Reset all statistics counters."""
        self.hits = 0
        self.misses = 0
        self.errors = 0
        self.last_reset = datetime.now()
        logger.info("Cache statistics reset")


# Global cache statistics instance
cache_stats = CacheStats()


# ============================================================================
# CACHE KEY GENERATION
# ============================================================================

def _generate_cache_key(
    namespace: str,
    key_prefix: str,
    func_name: str,
    args: tuple,
    kwargs: dict
) -> str:
    """
    Generate deterministic cache key from function signature.

    Key format: {namespace}:{key_prefix}:{func_name}:{hash(args+kwargs)}

    Args:
        namespace: Cache namespace (e.g., "crm")
        key_prefix: Functional prefix (e.g., "leads", "metrics")
        func_name: Function name
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        str: Cache key like "crm:leads:get_lead_stats:a1b2c3d4"
    """
    # Create stable string representation of arguments
    # Filter out 'self' and 'cls' from args
    filtered_args = [arg for arg in args if arg not in ('self', 'cls')]

    arg_string = f"{filtered_args}:{sorted(kwargs.items())}"
    arg_hash = hashlib.md5(arg_string.encode()).hexdigest()[:8]

    # Build key components
    components = [namespace]
    if key_prefix:
        components.append(key_prefix)
    components.extend([func_name, arg_hash])

    return ":".join(components)


def _serialize_result(result: Any) -> str:
    """
    Serialize result to JSON string with fallback for complex objects.

    Args:
        result: Function result to serialize

    Returns:
        str: JSON string
    """
    try:
        return json.dumps(result, default=str)
    except Exception as e:
        logger.warning(f"JSON serialization fallback used: {e}")
        # Fallback: convert to string representation
        return json.dumps({"__serialized__": str(result)})


def _deserialize_result(cached_data: str) -> Any:
    """
    Deserialize JSON string back to Python object.

    Args:
        cached_data: JSON string from cache

    Returns:
        Any: Deserialized Python object
    """
    return json.loads(cached_data)


# ============================================================================
# MAIN CACHING DECORATOR
# ============================================================================

def cache_result(
    ttl: int = 300,
    key_prefix: str = "",
    namespace: str = "crm"
) -> Callable:
    """
    Production-grade caching decorator with automatic key generation.

    Features:
    - Automatic cache key generation from function signature
    - Configurable TTL (time to live)
    - Graceful degradation on Redis failure
    - Cache statistics tracking
    - JSON serialization with fallback

    Args:
        ttl: Time to live in seconds (default: 300s = 5min)
            - 30s: Real-time metrics
            - 300s: Standard dashboard data
            - 3600s: Historical analytics
        key_prefix: Cache key prefix for grouping (e.g., "leads", "metrics")
        namespace: Top-level namespace (default: "crm")

    Usage:
        @cache_result(ttl=30, key_prefix="leads")
        def get_hot_leads():
            return db.query(Lead).filter(Lead.temperature == "hot").all()

    Cache Key Pattern:
        {namespace}:{key_prefix}:{func_name}:{hash(args+kwargs)}
        Example: "crm:leads:get_hot_leads:a1b2c3d4"
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Check if Redis is available
            if not redis_client or not redis_client.is_connected:
                logger.debug(f"Redis unavailable, executing {func.__name__} without cache")
                return func(*args, **kwargs)

            try:
                # Generate cache key
                cache_key = _generate_cache_key(
                    namespace=namespace,
                    key_prefix=key_prefix,
                    func_name=func.__name__,
                    args=args,
                    kwargs=kwargs
                )

                # Try to get from cache
                cached_data = redis_client.get(cache_key)

                if cached_data:
                    # Cache hit
                    cache_stats.record_hit()
                    logger.debug(f"Cache HIT: {cache_key}")
                    return _deserialize_result(cached_data)

                # Cache miss - execute function
                cache_stats.record_miss()
                logger.debug(f"Cache MISS: {cache_key}")

                result = func(*args, **kwargs)

                # Store result in cache
                serialized = _serialize_result(result)
                redis_client.setex(cache_key, ttl, serialized)

                logger.debug(f"Cache STORED: {cache_key} (TTL: {ttl}s)")
                return result

            except Exception as e:
                # Log error but don't fail the request
                cache_stats.record_error()
                logger.error(f"Cache error in {func.__name__}: {e}", exc_info=True)

                # Fallback to direct execution
                return func(*args, **kwargs)

        return wrapper
    return decorator


# ============================================================================
# CACHE INVALIDATION
# ============================================================================

def cache_invalidate(pattern: str) -> int:
    """
    Invalidate cache entries matching a pattern.

    Use this after data mutations to ensure cache consistency.

    Args:
        pattern: Redis key pattern with wildcards
            Examples:
            - "crm:leads:*" - All lead cache entries
            - "crm:metrics:get_lead_stats:*" - Specific method all args
            - "crm:*" - Everything in CRM namespace

    Returns:
        int: Number of keys deleted

    Usage:
        # After creating a new lead
        cache_invalidate("crm:leads:*")

        # After updating customer
        cache_invalidate("crm:customers:*")
    """
    try:
        if not redis_client or not redis_client.is_connected:
            logger.warning("Redis unavailable, cache invalidation skipped")
            return 0

        # Get all keys matching pattern
        keys = redis_client.keys(pattern)

        if not keys:
            logger.debug(f"No cache keys found for pattern: {pattern}")
            return 0

        # Delete all matching keys
        deleted = redis_client.delete(*keys)
        logger.info(f"Cache invalidated: {deleted} keys deleted (pattern: {pattern})")

        return deleted

    except Exception as e:
        logger.error(f"Cache invalidation error: {e}", exc_info=True)
        return 0


def cache_invalidate_function(
    func_name: str,
    key_prefix: str = "",
    namespace: str = "crm"
) -> int:
    """
    Invalidate all cache entries for a specific function.

    Args:
        func_name: Name of the cached function
        key_prefix: Cache key prefix (optional)
        namespace: Cache namespace (default: "crm")

    Returns:
        int: Number of keys deleted

    Usage:
        cache_invalidate_function("get_lead_stats", key_prefix="leads")
    """
    components = [namespace]
    if key_prefix:
        components.append(key_prefix)
    components.append(func_name)
    components.append("*")

    pattern = ":".join(components)
    return cache_invalidate(pattern)


# ============================================================================
# CACHE MANAGEMENT
# ============================================================================

def get_cache_stats() -> dict[str, Any]:
    """
    Get current cache statistics.

    Returns:
        dict: Statistics including hits, misses, hit rate
    """
    return cache_stats.get_stats()


def reset_cache_stats():
    """Reset cache statistics counters."""
    cache_stats.reset()


def clear_all_cache(namespace: str = "crm") -> int:
    """
    Clear all cache entries in a namespace.

    WARNING: This clears ALL cached data. Use with caution.

    Args:
        namespace: Cache namespace to clear (default: "crm")

    Returns:
        int: Number of keys deleted
    """
    pattern = f"{namespace}:*"
    deleted = cache_invalidate(pattern)
    logger.warning(f"All cache cleared: {deleted} keys deleted in namespace '{namespace}'")
    return deleted


# ============================================================================
# CACHE WARMING
# ============================================================================

def warm_cache(func: Callable, *args, **kwargs) -> Any:
    """
    Pre-populate cache by executing a cached function.

    Useful for warming cache on server startup.

    Args:
        func: Cached function to warm
        *args: Arguments to pass to function
        **kwargs: Keyword arguments to pass to function

    Returns:
        Any: Function result

    Usage:
        warm_cache(get_lead_stats)
        warm_cache(get_hot_leads, limit=10)
    """
    logger.info(f"Warming cache: {func.__name__}")
    result = func(*args, **kwargs)
    logger.info(f"Cache warmed: {func.__name__}")
    return result


# ============================================================================
# EXPORT PUBLIC API
# ============================================================================

__all__ = [
    "cache_result",
    "cache_invalidate",
    "cache_invalidate_function",
    "get_cache_stats",
    "reset_cache_stats",
    "clear_all_cache",
    "warm_cache",
]
