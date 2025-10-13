"""
iSwitch Roofs CRM - Cache Monitoring Endpoints
Version: 1.0.0
Date: 2025-10-09

PURPOSE:
Cache monitoring and management endpoints for production debugging and optimization.

ENDPOINTS:
- GET  /api/cache/stats      - Get cache statistics
- POST /api/cache/clear      - Clear all cache
- POST /api/cache/clear/:key - Clear specific cache key pattern
- POST /api/cache/warm       - Trigger cache warming

SECURITY:
These endpoints should be restricted to admin users in production.
"""

import logging
from flask import Blueprint, jsonify, request
from typing import Any, Dict

from app.utils.cache import (
    get_cache_stats,
    reset_cache_stats,
    clear_all_cache,
    cache_invalidate,
)
from app.scripts.warm_cache import warm_all_caches, warm_specific_cache

logger = logging.getLogger(__name__)

# Create blueprint
cache_monitor_bp = Blueprint("cache_monitor", __name__, url_prefix="/api/cache")


@cache_monitor_bp.route("/stats", methods=["GET"])
def get_stats() -> tuple[Dict[str, Any], int]:
    """
    Get current cache statistics.

    Returns:
        200: Cache statistics
        {
            "success": true,
            "data": {
                "hits": 1250,
                "misses": 350,
                "errors": 5,
                "total_requests": 1600,
                "hit_rate_percent": 78.13,
                "last_reset": "2025-10-09T10:00:00"
            }
        }

    Usage:
        curl http://localhost:8000/api/cache/stats
    """
    try:
        stats = get_cache_stats()

        return jsonify({"success": True, "data": stats}), 200

    except Exception as e:
        logger.error(f"Error getting cache stats: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@cache_monitor_bp.route("/stats/reset", methods=["POST"])
def reset_stats() -> tuple[Dict[str, Any], int]:
    """
    Reset cache statistics counters.

    Returns:
        200: Success confirmation
        {
            "success": true,
            "message": "Cache statistics reset successfully"
        }

    Usage:
        curl -X POST http://localhost:8000/api/cache/stats/reset
    """
    try:
        reset_cache_stats()

        return (
            jsonify({"success": True, "message": "Cache statistics reset successfully"}),
            200,
        )

    except Exception as e:
        logger.error(f"Error resetting cache stats: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@cache_monitor_bp.route("/clear", methods=["POST"])
def clear_cache() -> tuple[Dict[str, Any], int]:
    """
    Clear all cache entries.

    WARNING: This clears ALL cached data. Use with caution in production.

    Request Body (optional):
        {
            "namespace": "crm"  // Optional: specify namespace to clear
        }

    Returns:
        200: Success with count of deleted keys
        {
            "success": true,
            "message": "Cache cleared successfully",
            "keys_deleted": 1234
        }

    Usage:
        curl -X POST http://localhost:8000/api/cache/clear
        curl -X POST http://localhost:8000/api/cache/clear -H "Content-Type: application/json" -d '{"namespace":"crm"}'
    """
    try:
        data = request.get_json() or {}
        namespace = data.get("namespace", "crm")

        keys_deleted = clear_all_cache(namespace=namespace)

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Cache cleared successfully",
                    "keys_deleted": keys_deleted,
                    "namespace": namespace,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@cache_monitor_bp.route("/clear/<path:pattern>", methods=["POST"])
def clear_cache_pattern(pattern: str) -> tuple[Dict[str, Any], int]:
    """
    Clear cache entries matching a pattern.

    Args:
        pattern: Redis key pattern (e.g., "crm:leads:*")

    Returns:
        200: Success with count of deleted keys
        {
            "success": true,
            "message": "Cache pattern cleared",
            "pattern": "crm:leads:*",
            "keys_deleted": 42
        }

    Usage:
        curl -X POST http://localhost:8000/api/cache/clear/crm:leads:*
        curl -X POST http://localhost:8000/api/cache/clear/crm:metrics:*
    """
    try:
        keys_deleted = cache_invalidate(pattern)

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Cache pattern cleared successfully",
                    "pattern": pattern,
                    "keys_deleted": keys_deleted,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error clearing cache pattern: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@cache_monitor_bp.route("/warm", methods=["POST"])
def warm_cache() -> tuple[Dict[str, Any], int]:
    """
    Trigger cache warming process.

    Request Body (optional):
        {
            "type": "all"  // Options: "all", "leads", "metrics"
        }

    Returns:
        200: Success confirmation
        {
            "success": true,
            "message": "Cache warming completed",
            "type": "all"
        }

    Usage:
        curl -X POST http://localhost:8000/api/cache/warm
        curl -X POST http://localhost:8000/api/cache/warm -H "Content-Type: application/json" -d '{"type":"leads"}'
    """
    try:
        data = request.get_json() or {}
        cache_type = data.get("type", "all")

        if cache_type not in ["all", "leads", "metrics"]:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Invalid cache type. Valid options: all, leads, metrics",
                    }
                ),
                400,
            )

        # Trigger warming
        if cache_type == "all":
            warm_all_caches()
        else:
            warm_specific_cache(cache_type)

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Cache warming completed for {cache_type}",
                    "type": cache_type,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error warming cache: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@cache_monitor_bp.route("/health", methods=["GET"])
def cache_health() -> tuple[Dict[str, Any], int]:
    """
    Check cache health status.

    Returns:
        200: Health status
        {
            "success": true,
            "data": {
                "redis_connected": true,
                "hit_rate": 78.5,
                "total_requests": 1500,
                "status": "healthy"  // "healthy", "degraded", "down"
            }
        }

    Usage:
        curl http://localhost:8000/api/cache/health
    """
    try:
        from app.utils.cache import redis_client

        stats = get_cache_stats()

        # Determine health status
        is_connected = redis_client and redis_client.is_connected
        hit_rate = stats.get("hit_rate_percent", 0)

        if not is_connected:
            status = "down"
        elif hit_rate < 50:
            status = "degraded"
        else:
            status = "healthy"

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "redis_connected": is_connected,
                        "hit_rate": hit_rate,
                        "total_requests": stats.get("total_requests", 0),
                        "status": status,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error checking cache health: {e}", exc_info=True)
        return (
            jsonify(
                {
                    "success": False,
                    "error": str(e),
                    "data": {"status": "error", "redis_connected": False},
                }
            ),
            500,
        )


# Export blueprint
__all__ = ["cache_monitor_bp"]
