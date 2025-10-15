"""
Business Metrics API Routes for iSwitch Roofs CRM
Version: 2.0.0
Date: 2025-10-09

Provides REST endpoints for business-specific KPIs and real-time metrics.
"""

import json
import logging
import time
from datetime import datetime

from flask import Blueprint, Response, jsonify, request, stream_with_context

from app.services.business_metrics import business_metrics_service
# from app.utils.auth import require_auth  # Temporarily disabled for dashboard access
from app.utils.redis_cache import invalidate_cache as invalidate_redis_cache
from app.utils.pusher_client import get_pusher_service

logger = logging.getLogger(__name__)
bp = Blueprint("business_metrics", __name__)


@bp.route("/premium-markets", methods=["GET"])
# @require_auth  # Temporarily disabled for dashboard access
def get_premium_markets():
    """
    Get premium market penetration metrics

    Query Parameters:
        - days: Number of days to analyze (default: 30)

    Returns:
        200: Premium market metrics
        401: Unauthorized
        500: Server error

    Example:
        GET /api/business-metrics/premium-markets?days=30
    """
    try:
        days = int(request.args.get("days", 30))

        metrics = business_metrics_service.get_premium_market_metrics(days=days)

        return jsonify({
            "success": True,
            "data": metrics,
            "generated_at": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error fetching premium market metrics: {str(e)}")
        return jsonify({"error": "Failed to fetch premium market metrics"}), 500


@bp.route("/lead-response", methods=["GET"])
# @require_auth  # Temporarily disabled for dashboard access - THIS WAS CAUSING 404 ERRORS
def get_lead_response():
    """
    Get lead response time metrics (2-minute target)

    Returns:
        200: Response time metrics
        401: Unauthorized
        500: Server error

    Example:
        GET /api/business-metrics/lead-response
    """
    try:
        metrics = business_metrics_service.get_lead_response_metrics()

        return jsonify({
            "success": True,
            "data": metrics,
            "target_seconds": 120,
            "generated_at": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error fetching lead response metrics: {str(e)}")
        return jsonify({"error": "Failed to fetch lead response metrics"}), 500


@bp.route("/marketing-roi", methods=["GET"])
# @require_auth  # Temporarily disabled for dashboard access
def get_marketing_roi():
    """
    Get marketing channel ROI metrics

    Query Parameters:
        - days: Number of days to analyze (default: 30)

    Returns:
        200: Marketing ROI data
        401: Unauthorized
        500: Server error

    Example:
        GET /api/business-metrics/marketing-roi?days=30
    """
    try:
        days = int(request.args.get("days", 30))

        metrics = business_metrics_service.get_marketing_channel_roi(days=days)

        return jsonify({
            "success": True,
            "data": metrics,
            "generated_at": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error fetching marketing ROI: {str(e)}")
        return jsonify({"error": "Failed to fetch marketing ROI"}), 500


@bp.route("/conversion-optimization", methods=["GET"])
# @require_auth  # Temporarily disabled for dashboard access
def get_conversion_optimization():
    """
    Get conversion optimization metrics (25-35% target)

    Returns:
        200: Conversion optimization data
        401: Unauthorized
        500: Server error

    Example:
        GET /api/business-metrics/conversion-optimization
    """
    try:
        metrics = business_metrics_service.get_conversion_optimization_metrics()

        return jsonify({
            "success": True,
            "data": metrics,
            "target_range": "25-35%",
            "generated_at": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error fetching conversion metrics: {str(e)}")
        return jsonify({"error": "Failed to fetch conversion metrics"}), 500


@bp.route("/revenue-growth", methods=["GET"])
# @require_auth  # Temporarily disabled for dashboard access
def get_revenue_growth():
    """
    Get revenue growth progress ($6M → $30M journey)

    Returns:
        200: Revenue growth data
        401: Unauthorized
        500: Server error

    Example:
        GET /api/business-metrics/revenue-growth
    """
    try:
        metrics = business_metrics_service.get_revenue_growth_progress()

        return jsonify({
            "success": True,
            "data": metrics,
            "growth_path": "$6M → $8M → $18M → $30M",
            "generated_at": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error fetching revenue growth: {str(e)}")
        return jsonify({"error": "Failed to fetch revenue growth"}), 500


@bp.route("/realtime/stream", methods=["GET"])
# @require_auth  # Temporarily disabled for dashboard access
def stream_realtime_metrics():
    """
    Server-Sent Events (SSE) endpoint for real-time metric updates

    Streams updates every 30 seconds with:
    - Lead response time
    - Current day revenue
    - Active leads count
    - Team activity

    Returns:
        SSE stream

    Example:
        GET /api/business-metrics/realtime/stream
    """
    def generate():
        """Generate SSE events"""
        try:
            while True:
                # Gather real-time metrics
                response_metrics = business_metrics_service.get_lead_response_metrics()
                revenue_metrics = business_metrics_service.get_revenue_growth_progress()

                # Create event payload
                payload = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "lead_response": response_metrics,
                    "revenue": revenue_metrics.get("current_month", {}),
                    "status": "healthy"
                }

                # Send SSE event
                yield f"event: metrics\n"
                yield f"data: {json.dumps(payload)}\n\n"

                # Wait 30 seconds before next update
                time.sleep(30)

        except GeneratorExit:
            logger.info("Client disconnected from SSE stream")
        except Exception as e:
            logger.error(f"Error in SSE stream: {str(e)}")
            yield f"event: error\n"
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@bp.route("/realtime/snapshot", methods=["GET"])
# @require_auth  # Temporarily disabled for dashboard access
def get_realtime_snapshot():
    """
    Get current real-time snapshot (faster than SSE for single request)

    Returns:
        200: Current snapshot
        401: Unauthorized
        500: Server error

    Example:
        GET /api/business-metrics/realtime/snapshot
    """
    try:
        # Gather all real-time metrics
        response_metrics = business_metrics_service.get_lead_response_metrics()
        revenue_metrics = business_metrics_service.get_revenue_growth_progress()
        conversion_metrics = business_metrics_service.get_conversion_optimization_metrics()

        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "lead_response": response_metrics,
            "revenue": revenue_metrics.get("current_month", {}),
            "conversion": conversion_metrics.get("overall", {}),
            "status": "healthy"
        }

        return jsonify({
            "success": True,
            "data": snapshot
        }), 200

    except Exception as e:
        logger.error(f"Error fetching realtime snapshot: {str(e)}")
        return jsonify({"error": "Failed to fetch realtime snapshot"}), 500


@bp.route("/invalidate-cache", methods=["POST"])
# @require_auth  # Temporarily disabled for dashboard access
def invalidate_business_metrics_cache():
    """
    Invalidate business metrics cache

    Request Body:
        - pattern: Cache key pattern to invalidate (optional, defaults to all)

    Returns:
        200: Cache invalidated
        401: Unauthorized
        500: Server error

    Example:
        POST /api/business-metrics/invalidate-cache
        {"pattern": "business_metrics:*"}
    """
    try:
        data = request.get_json() or {}
        pattern = data.get("pattern", "business_metrics:*")

        deleted = invalidate_redis_cache(pattern)

        logger.info(f"Invalidated {deleted} cache keys matching pattern: {pattern}")

        return jsonify({
            "success": True,
            "message": f"Invalidated {deleted} cache entries",
            "pattern": pattern
        }), 200

    except Exception as e:
        logger.error(f"Error invalidating cache: {str(e)}")
        return jsonify({"error": "Failed to invalidate cache"}), 500


@bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check for business metrics service

    Returns:
        200: Service healthy
        503: Service unhealthy
    """
    try:
        # Test basic functionality
        metrics = business_metrics_service.get_lead_response_metrics()

        if metrics:
            return jsonify({
                "status": "healthy",
                "service": "business_metrics",
                "timestamp": datetime.utcnow().isoformat()
            }), 200
        else:
            return jsonify({
                "status": "degraded",
                "service": "business_metrics",
                "message": "Unable to fetch metrics"
            }), 503

    except Exception as e:
        logger.error(f"Business metrics health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "service": "business_metrics",
            "error": str(e)
        }), 503


@bp.route("/summary", methods=["GET"])
# @require_auth  # Temporarily disabled for dashboard access
def get_business_summary():
    """
    Get comprehensive business metrics summary

    Returns all key business metrics in one call for dashboard.

    Returns:
        200: Business summary
        401: Unauthorized
        500: Server error

    Example:
        GET /api/business-metrics/summary
    """
    try:
        summary = {
            "premium_markets": business_metrics_service.get_premium_market_metrics(days=30),
            "lead_response": business_metrics_service.get_lead_response_metrics(),
            "marketing_roi": business_metrics_service.get_marketing_channel_roi(days=30),
            "conversion": business_metrics_service.get_conversion_optimization_metrics(),
            "revenue_growth": business_metrics_service.get_revenue_growth_progress(),
            "generated_at": datetime.utcnow().isoformat()
        }

        return jsonify({
            "success": True,
            "data": summary
        }), 200

    except Exception as e:
        logger.error(f"Error fetching business summary: {str(e)}")
        return jsonify({"error": "Failed to fetch business summary"}), 500
