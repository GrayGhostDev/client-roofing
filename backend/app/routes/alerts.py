"""
iSwitch Roofs CRM - Alert System API Routes

REST API endpoints for managing the critical 2-minute lead response alert system.
Provides endpoints for acknowledging, responding, and tracking alert metrics.

Author: iSwitch Roofs Development Team
Date: 2025-01-04
"""

import logging
from datetime import datetime

from flask import Blueprint, jsonify, request

from app.services.alert_service import (
    acknowledge_alert,
    get_response_metrics,
    mark_responded,
)
from app.utils.auth import get_current_user, require_auth
from app.utils.validators import validate_uuid

logger = logging.getLogger(__name__)
bp = Blueprint("alerts", __name__)


@bp.route("/<alert_id>/acknowledge", methods=["POST"])
@require_auth
def acknowledge_alert_endpoint(alert_id: str):
    """
    Acknowledge receipt of an alert

    This endpoint marks an alert as acknowledged by the assigned team member,
    indicating they have seen the notification and are working on it.

    Path Parameters:
        alert_id: Unique identifier of the alert

    Returns:
        200: Alert acknowledged successfully
        400: Invalid alert ID
        404: Alert not found
        500: Server error

    Example:
        POST /api/alerts/alert-123/acknowledge
    """
    try:
        # Validate UUID format
        if not validate_uuid(alert_id):
            return jsonify({"error": "Invalid alert ID format"}), 400

        # Get current user
        user = get_current_user()
        if not user:
            return jsonify({"error": "User not authenticated"}), 401

        # Acknowledge the alert
        success = acknowledge_alert(alert_id, user["id"])

        if not success:
            return jsonify({"error": "Alert not found or already acknowledged"}), 404

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Alert acknowledged successfully",
                    "alert_id": alert_id,
                    "acknowledged_by": user["id"],
                    "acknowledged_at": datetime.utcnow().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error acknowledging alert {alert_id}: {str(e)}")
        return jsonify({"error": "Failed to acknowledge alert", "details": str(e)}), 500


@bp.route("/<alert_id>/respond", methods=["POST"])
@require_auth
def respond_to_alert_endpoint(alert_id: str):
    """
    Mark alert as responded with action taken

    This endpoint marks an alert as fully responded to, indicating the team member
    has made contact with the lead and taken appropriate action.

    Path Parameters:
        alert_id: Unique identifier of the alert

    Request Body:
        {
            "action": "called|emailed|texted|visited",
            "outcome": "interested|not_interested|callback_scheduled|quote_sent",
            "notes": "Optional notes about the interaction",
            "next_steps": "Optional next steps planned"
        }

    Returns:
        200: Alert response recorded successfully
        400: Invalid request data
        404: Alert not found
        500: Server error

    Example:
        POST /api/alerts/alert-123/respond
        {
            "action": "called",
            "outcome": "interested",
            "notes": "Customer wants quote for full roof replacement",
            "next_steps": "Schedule inspection tomorrow"
        }
    """
    try:
        # Validate UUID format
        if not validate_uuid(alert_id):
            return jsonify({"error": "Invalid alert ID format"}), 400

        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Validate required fields
        if "action" not in data:
            return jsonify({"error": "Action is required"}), 400

        # Get current user
        user = get_current_user()
        if not user:
            return jsonify({"error": "User not authenticated"}), 401

        # Mark as responded
        response_data = {
            "action": data.get("action"),
            "outcome": data.get("outcome"),
            "notes": data.get("notes"),
            "next_steps": data.get("next_steps"),
            "responded_at": datetime.utcnow().isoformat(),
        }

        success = mark_responded(alert_id, user["id"], response_data)

        if not success:
            return jsonify({"error": "Alert not found or already responded"}), 404

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Response recorded successfully",
                    "alert_id": alert_id,
                    "responded_by": user["id"],
                    "response_data": response_data,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error responding to alert {alert_id}: {str(e)}")
        return jsonify({"error": "Failed to record response", "details": str(e)}), 500


@bp.route("/metrics", methods=["GET"])
@require_auth
def get_alert_metrics():
    """
    Get alert response metrics for the team

    Query Parameters:
        team_id: Optional team filter (UUID)
        period_days: Number of days to analyze (default: 30, max: 365)
        group_by: Optional grouping (team_member|hour|day|week)

    Returns:
        200: Metrics data
        500: Server error

    Example:
        GET /api/alerts/metrics?period_days=7&group_by=team_member
    """
    try:
        # Parse query parameters
        team_id = request.args.get("team_id")
        period_days = min(int(request.args.get("period_days", 30)), 365)
        group_by = request.args.get("group_by")

        # Get metrics
        metrics = get_response_metrics(team_id, period_days)

        # Add grouping if requested
        if group_by and metrics.get("data"):
            if group_by == "team_member":
                metrics["grouped_data"] = metrics.get("team_leaderboard", [])
            elif group_by == "hour":
                metrics["grouped_data"] = metrics.get("hourly_distribution", {})
            # Add more grouping options as needed

        return (
            jsonify(
                {
                    "success": True,
                    "metrics": metrics,
                    "query": {"team_id": team_id, "period_days": period_days, "group_by": group_by},
                }
            ),
            200,
        )

    except ValueError as e:
        return jsonify({"error": "Invalid parameter value", "details": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting alert metrics: {str(e)}")
        return jsonify({"error": "Failed to get metrics", "details": str(e)}), 500


@bp.route("/active", methods=["GET"])
@require_auth
def get_active_alerts():
    """
    Get all active alerts for the current user or team

    Query Parameters:
        status: Filter by status (pending|acknowledged|escalated)
        assigned_to: Filter by assigned user ID (admin only)
        priority: Filter by priority (critical|high|normal|low)

    Returns:
        200: List of active alerts
        500: Server error

    Example:
        GET /api/alerts/active?status=pending&priority=critical
    """
    try:
        # Get current user
        user = get_current_user()
        if not user:
            return jsonify({"error": "User not authenticated"}), 401

        # Parse filters
        status = request.args.get("status")
        assigned_to = request.args.get("assigned_to")
        priority = request.args.get("priority")

        # Only admins can view other users' alerts
        if assigned_to and user.get("role") != "admin" or not assigned_to:
            assigned_to = user["id"]

        # Get active alerts from Redis
        import json

        from app.utils.redis_client import redis_client

        alert_keys = redis_client.scan_keys("alert:*")
        active_alerts = []

        for key in alert_keys:
            alert_data = redis_client.get(key)
            if alert_data:
                alert = json.loads(alert_data)

                # Apply filters
                if status and alert.get("status") != status:
                    continue
                if assigned_to and alert.get("assigned_to") != assigned_to:
                    continue
                if priority and alert.get("priority") != priority:
                    continue

                # Check if not expired
                if alert.get("status") not in ["responded", "expired"]:
                    active_alerts.append(alert)

        # Sort by created_at (newest first)
        active_alerts.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return jsonify({"success": True, "alerts": active_alerts, "total": len(active_alerts)}), 200

    except Exception as e:
        logger.error(f"Error getting active alerts: {str(e)}")
        return jsonify({"error": "Failed to get active alerts", "details": str(e)}), 500


@bp.route("/test-alert", methods=["POST"])
@require_auth
def create_test_alert():
    """
    Create a test alert for training or testing purposes

    This endpoint creates a simulated lead alert for testing the alert system
    without creating an actual lead.

    Request Body:
        {
            "lead_name": "Test Lead Name",
            "lead_score": 85,
            "priority": "critical|high|normal|low"
        }

    Returns:
        201: Test alert created
        400: Invalid request data
        500: Server error

    Example:
        POST /api/alerts/test-alert
        {
            "lead_name": "John Test",
            "lead_score": 90,
            "priority": "critical"
        }
    """
    try:
        # Get current user (must be admin or manager)
        user = get_current_user()
        if not user or user.get("role") not in ["admin", "manager"]:
            return jsonify({"error": "Insufficient permissions"}), 403

        # Get request data
        data = request.get_json()
        if not data:
            data = {}

        # Create test lead data
        from uuid import uuid4

        test_lead_id = str(uuid4())
        test_lead_data = {
            "id": test_lead_id,
            "name": data.get("lead_name", "Test Lead"),
            "email": "test@example.com",
            "phone": "+1 (248) 555-0100",
            "score": data.get("lead_score", 75),
            "source": "test",
            "address": "123 Test Street, Birmingham, MI 48009",
            "project_type": "Test Project",
            "urgency": "Test Alert - No Action Required",
            "is_test": True,
        }

        # Trigger test alert
        from app.services.alert_service import trigger_lead_alert

        success, alert_id = trigger_lead_alert(test_lead_id, test_lead_data)

        if not success:
            return jsonify({"error": "Failed to create test alert", "details": alert_id}), 500

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Test alert created successfully",
                    "alert_id": alert_id,
                    "test_lead_id": test_lead_id,
                    "note": "This is a test alert - no actual lead was created",
                }
            ),
            201,
        )

    except Exception as e:
        logger.error(f"Error creating test alert: {str(e)}")
        return jsonify({"error": "Failed to create test alert", "details": str(e)}), 500


@bp.route("/settings", methods=["GET", "PUT"])
@require_auth
def alert_settings():
    """
    Get or update alert settings for the current user

    GET: Returns current alert settings
    PUT: Updates alert settings

    Request Body (PUT):
        {
            "channels": ["email", "sms", "push"],
            "quiet_hours": {
                "enabled": true,
                "start": 22,
                "end": 8
            },
            "escalation_enabled": true,
            "auto_acknowledge": false
        }

    Returns:
        200: Settings retrieved or updated
        400: Invalid settings data
        500: Server error
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({"error": "User not authenticated"}), 401

        if request.method == "GET":
            # Get current settings from database
            from app.config import get_supabase_client

            supabase = get_supabase_client()
            result = (
                supabase.table("alert_settings").select("*").eq("user_id", user["id"]).execute()
            )

            settings = (
                result.data[0]
                if result.data
                else {
                    "user_id": user["id"],
                    "channels": ["email", "sms", "push"],
                    "quiet_hours": {"enabled": True, "start": 22, "end": 8},
                    "escalation_enabled": True,
                    "auto_acknowledge": False,
                }
            )

            return jsonify({"success": True, "settings": settings}), 200

        else:  # PUT
            data = request.get_json()
            if not data:
                return jsonify({"error": "Settings data required"}), 400

            # Update settings
            settings_data = {
                "user_id": user["id"],
                "channels": data.get("channels", ["email", "sms", "push"]),
                "quiet_hours": data.get("quiet_hours", {"enabled": True, "start": 22, "end": 8}),
                "escalation_enabled": data.get("escalation_enabled", True),
                "auto_acknowledge": data.get("auto_acknowledge", False),
                "updated_at": datetime.utcnow().isoformat(),
            }

            # Upsert settings
            result = supabase.table("alert_settings").upsert(settings_data).execute()

            return (
                jsonify(
                    {
                        "success": True,
                        "message": "Settings updated successfully",
                        "settings": settings_data,
                    }
                ),
                200,
            )

    except Exception as e:
        logger.error(f"Error managing alert settings: {str(e)}")
        return jsonify({"error": "Failed to manage settings", "details": str(e)}), 500


@bp.route("/performance/dashboard", methods=["GET"])
@require_auth
def alert_performance_dashboard():
    """
    Get comprehensive alert performance dashboard data

    Returns aggregated metrics for display in a dashboard view.

    Query Parameters:
        period: today|week|month|quarter (default: week)

    Returns:
        200: Dashboard data
        500: Server error

    Example:
        GET /api/alerts/performance/dashboard?period=week
    """
    try:
        period = request.args.get("period", "week")

        # Calculate period in days
        period_days = {"today": 1, "week": 7, "month": 30, "quarter": 90}.get(period, 7)

        # Get comprehensive metrics
        metrics = get_response_metrics(None, period_days)

        # Calculate additional KPIs
        dashboard_data = {
            "period": period,
            "summary": {
                "total_alerts": metrics.get("total_responses", 0),
                "avg_response_time_seconds": metrics.get("avg_response_time", 0),
                "within_target_rate": metrics.get("within_target_rate", 0),
                "alerts_today": 0,  # Would need additional query
                "active_alerts": 0,  # Would need Redis scan
            },
            "trends": {
                "hourly_distribution": metrics.get("hourly_distribution", {}),
                "daily_trend": [],  # Would need additional processing
            },
            "leaderboard": metrics.get("team_leaderboard", [])[:5],
            "alerts_by_priority": {
                "critical": 0,  # Would need additional queries
                "high": 0,
                "normal": 0,
                "low": 0,
            },
            "best_performer": (
                metrics.get("team_leaderboard", [{}])[0]
                if metrics.get("team_leaderboard")
                else None
            ),
            "needs_attention": [],  # Team members below target rate
        }

        # Find team members needing attention (below 80% target rate)
        for member in metrics.get("team_leaderboard", []):
            if member.get("target_rate", 100) < 80:
                dashboard_data["needs_attention"].append(
                    {
                        "member_id": member.get("member_id"),
                        "target_rate": member.get("target_rate"),
                        "avg_response_time": member.get("avg_response_time"),
                    }
                )

        return (
            jsonify(
                {
                    "success": True,
                    "dashboard": dashboard_data,
                    "generated_at": datetime.utcnow().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting performance dashboard: {str(e)}")
        return jsonify({"error": "Failed to get dashboard data", "details": str(e)}), 500


# Register error handlers
@bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Alert endpoint not found"}), 404


@bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error in alerts API: {error}")
    return jsonify({"error": "Internal server error"}), 500
