"""
Analytics API Routes for iSwitch Roofs CRM

Provides REST endpoints for KPI calculations, metrics, forecasting,
and real-time dashboard updates via Pusher.

Features:
- KPI snapshots and historical trends
- Revenue forecasting
- Lead funnel analytics
- Team performance metrics
- Real-time metrics streaming
- Custom report generation

Author: iSwitch Roofs Development Team
Date: 2025-01-04
"""

import json
import logging
from datetime import datetime, timedelta

from flask import Blueprint, g, jsonify, request

from app.services.analytics_service import TimeFrame, analytics_service
from app.utils.auth import require_auth, require_role
from app.utils.pusher_client import get_pusher_service

logger = logging.getLogger(__name__)
bp = Blueprint("analytics", __name__)


@bp.route("/kpis", methods=["GET"])
@require_auth
def get_kpis():
    """
    Get comprehensive KPI snapshot

    Query Parameters:
        - timeframe: Time period (daily, weekly, monthly, quarterly, yearly, mtd, qtd, ytd)
                    Default: mtd (month-to-date)

    Returns:
        200: KPI metrics
        401: Unauthorized
        500: Server error

    Example:
        GET /api/analytics/kpis?timeframe=mtd
    """
    try:
        # Get timeframe parameter
        timeframe_str = request.args.get("timeframe", "mtd")

        # Validate timeframe
        valid_timeframes = [t.value for t in TimeFrame]
        if timeframe_str not in valid_timeframes:
            return (
                jsonify(
                    {"error": f'Invalid timeframe. Must be one of: {", ".join(valid_timeframes)}'}
                ),
                400,
            )

        timeframe = TimeFrame(timeframe_str)

        # Get KPIs
        kpis = analytics_service.calculate_kpis(timeframe)

        if not kpis:
            return jsonify({"error": "Failed to calculate KPIs"}), 500

        return (
            jsonify({"success": True, "kpis": kpis, "generated_at": datetime.utcnow().isoformat()}),
            200,
        )

    except Exception as e:
        logger.error(f"Error fetching KPIs: {str(e)}")
        return jsonify({"error": "Failed to fetch KPIs"}), 500


@bp.route("/dashboard", methods=["GET"])
@require_auth
def get_dashboard():
    """
    Get dashboard analytics with all metrics

    Query Parameters:
        - timeframe: Time period (default: mtd)
        - include_forecast: Include revenue forecast (default: true)
        - include_funnel: Include lead funnel (default: true)

    Returns:
        200: Complete dashboard data
        401: Unauthorized
        500: Server error

    Example:
        GET /api/analytics/dashboard?timeframe=mtd&include_forecast=true
    """
    try:
        timeframe_str = request.args.get("timeframe", "mtd")
        include_forecast = request.args.get("include_forecast", "true").lower() == "true"
        include_funnel = request.args.get("include_funnel", "true").lower() == "true"

        # Validate timeframe
        valid_timeframes = [t.value for t in TimeFrame]
        if timeframe_str not in valid_timeframes:
            return (
                jsonify(
                    {"error": f'Invalid timeframe. Must be one of: {", ".join(valid_timeframes)}'}
                ),
                400,
            )

        timeframe = TimeFrame(timeframe_str)

        # Get all dashboard components
        dashboard_data = {
            "kpis": analytics_service.calculate_kpis(timeframe),
            "realtime": analytics_service.get_realtime_metrics(),
        }

        if include_forecast:
            dashboard_data["forecast"] = analytics_service.forecast_revenue(months_ahead=3)

        if include_funnel:
            dashboard_data["funnel"] = analytics_service.get_lead_funnel(timeframe)

        return (
            jsonify(
                {
                    "success": True,
                    "dashboard": dashboard_data,
                    "timeframe": timeframe_str,
                    "generated_at": datetime.utcnow().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error fetching dashboard: {str(e)}")
        return jsonify({"error": "Failed to fetch dashboard data"}), 500


@bp.route("/trends", methods=["GET"])
@require_auth
def get_trends():
    """
    Get historical trend data for metrics

    Query Parameters:
        - metric: Metric type to trend (leads, revenue, conversion)
        - period: Number of periods to include (default: 12)
        - interval: Interval type (daily, weekly, monthly) (default: monthly)

    Returns:
        200: Trend data with time series
        401: Unauthorized
        500: Server error

    Example:
        GET /api/analytics/trends?metric=revenue&period=12&interval=monthly
    """
    try:
        metric = request.args.get("metric", "revenue")
        period = int(request.args.get("period", 12))
        interval = request.args.get("interval", "monthly")

        # Validate parameters
        valid_metrics = ["leads", "revenue", "conversion", "customers"]
        if metric not in valid_metrics:
            return (
                jsonify({"error": f'Invalid metric. Must be one of: {", ".join(valid_metrics)}'}),
                400,
            )

        valid_intervals = ["daily", "weekly", "monthly"]
        if interval not in valid_intervals:
            return (
                jsonify(
                    {"error": f'Invalid interval. Must be one of: {", ".join(valid_intervals)}'}
                ),
                400,
            )

        # Calculate date range
        end_date = datetime.utcnow()
        if interval == "daily":
            start_date = end_date - timedelta(days=period)
            delta = timedelta(days=1)
        elif interval == "weekly":
            start_date = end_date - timedelta(weeks=period)
            delta = timedelta(weeks=1)
        else:  # monthly
            start_date = end_date - timedelta(days=period * 30)
            delta = timedelta(days=30)

        # Get trend data
        from app.config import get_supabase_client

        supabase = get_supabase_client()

        trend_data = []
        current_date = start_date

        while current_date < end_date:
            next_date = current_date + delta

            if metric == "leads":
                result = (
                    supabase.table("leads")
                    .select("id")
                    .gte("created_at", current_date.isoformat())
                    .lt("created_at", next_date.isoformat())
                    .execute()
                )
                value = len(result.data) if result.data else 0
            elif metric == "revenue":
                result = (
                    supabase.table("projects")
                    .select("actual_amount")
                    .eq("status", "completed")
                    .gte("completed_at", current_date.isoformat())
                    .lt("completed_at", next_date.isoformat())
                    .execute()
                )
                value = sum(
                    float(p.get("actual_amount", 0)) for p in (result.data if result.data else [])
                )
            elif metric == "conversion":
                leads_result = (
                    supabase.table("leads")
                    .select("id")
                    .gte("created_at", current_date.isoformat())
                    .lt("created_at", next_date.isoformat())
                    .execute()
                )
                converted_result = (
                    supabase.table("leads")
                    .select("id")
                    .eq("status", "converted")
                    .gte("created_at", current_date.isoformat())
                    .lt("created_at", next_date.isoformat())
                    .execute()
                )

                total_leads = len(leads_result.data) if leads_result.data else 0
                converted = len(converted_result.data) if converted_result.data else 0
                value = (converted / max(total_leads, 1)) * 100
            else:  # customers
                result = (
                    supabase.table("customers")
                    .select("id")
                    .gte("created_at", current_date.isoformat())
                    .lt("created_at", next_date.isoformat())
                    .execute()
                )
                value = len(result.data) if result.data else 0

            trend_data.append(
                {
                    "date": current_date.isoformat(),
                    "value": round(value, 2),
                }
            )

            current_date = next_date

        # Calculate trend direction
        if len(trend_data) >= 2:
            recent_avg = sum(d["value"] for d in trend_data[-3:]) / min(3, len(trend_data))
            older_avg = sum(d["value"] for d in trend_data[:3]) / min(3, len(trend_data))
            trend_direction = (
                "increasing"
                if recent_avg > older_avg
                else "decreasing" if recent_avg < older_avg else "stable"
            )
        else:
            trend_direction = "insufficient_data"

        return (
            jsonify(
                {
                    "success": True,
                    "metric": metric,
                    "interval": interval,
                    "trend_data": trend_data,
                    "trend_direction": trend_direction,
                    "period_count": len(trend_data),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error fetching trends: {str(e)}")
        return jsonify({"error": "Failed to fetch trend data"}), 500


@bp.route("/forecasts", methods=["GET"])
@require_auth
def get_forecasts():
    """
    Get revenue and metric forecasts

    Query Parameters:
        - months_ahead: Number of months to forecast (default: 3, max: 12)

    Returns:
        200: Forecast data with confidence intervals
        401: Unauthorized
        500: Server error

    Example:
        GET /api/analytics/forecasts?months_ahead=6
    """
    try:
        months_ahead = int(request.args.get("months_ahead", 3))

        # Validate parameters
        if months_ahead < 1 or months_ahead > 12:
            return jsonify({"error": "months_ahead must be between 1 and 12"}), 400

        # Get revenue forecast
        forecast = analytics_service.forecast_revenue(months_ahead)

        if "error" in forecast:
            return jsonify({"error": forecast["error"]}), 500

        return (
            jsonify(
                {
                    "success": True,
                    "forecast": forecast,
                    "generated_at": datetime.utcnow().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error generating forecast: {str(e)}")
        return jsonify({"error": "Failed to generate forecast"}), 500


@bp.route("/team-performance", methods=["GET"])
@require_auth
def get_team_performance():
    """
    Get team performance metrics

    Query Parameters:
        - team_member_id: Specific team member ID (optional)
        - timeframe: Time period (default: mtd)

    Returns:
        200: Team performance metrics
        401: Unauthorized
        500: Server error

    Example:
        GET /api/analytics/team-performance?timeframe=mtd
        GET /api/analytics/team-performance?team_member_id=uuid&timeframe=qtd
    """
    try:
        team_member_id = request.args.get("team_member_id")
        timeframe_str = request.args.get("timeframe", "mtd")

        # Validate timeframe
        valid_timeframes = [t.value for t in TimeFrame]
        if timeframe_str not in valid_timeframes:
            return (
                jsonify(
                    {"error": f'Invalid timeframe. Must be one of: {", ".join(valid_timeframes)}'}
                ),
                400,
            )

        timeframe = TimeFrame(timeframe_str)

        if team_member_id:
            # Get individual performance
            performance = analytics_service.calculate_team_performance(team_member_id, timeframe)

            if not performance:
                return jsonify({"error": "Failed to calculate performance"}), 500

            return (
                jsonify(
                    {
                        "success": True,
                        "performance": performance,
                    }
                ),
                200,
            )
        else:
            # Get all team members' performance
            from app.config import get_supabase_client

            supabase = get_supabase_client()

            team_result = (
                supabase.table("team_members")
                .select("id", "name", "role")
                .eq("is_active", True)
                .execute()
            )

            team_members = team_result.data if team_result.data else []
            performances = []

            for member in team_members:
                perf = analytics_service.calculate_team_performance(member["id"], timeframe)
                if perf:
                    perf["name"] = member["name"]
                    perf["role"] = member["role"]
                    performances.append(perf)

            # Sort by performance score
            performances.sort(key=lambda x: x.get("performance_score", 0), reverse=True)

            # Add rankings
            for i, perf in enumerate(performances):
                perf["rank"] = i + 1

            return (
                jsonify(
                    {
                        "success": True,
                        "team_performance": performances,
                        "team_count": len(performances),
                        "timeframe": timeframe_str,
                    }
                ),
                200,
            )

    except Exception as e:
        logger.error(f"Error fetching team performance: {str(e)}")
        return jsonify({"error": "Failed to fetch team performance"}), 500


@bp.route("/lead-funnel", methods=["GET"])
@require_auth
def get_lead_funnel():
    """
    Get lead funnel analytics

    Query Parameters:
        - timeframe: Time period (default: mtd)

    Returns:
        200: Funnel metrics with conversion rates
        401: Unauthorized
        500: Server error

    Example:
        GET /api/analytics/lead-funnel?timeframe=mtd
    """
    try:
        timeframe_str = request.args.get("timeframe", "mtd")

        # Validate timeframe
        valid_timeframes = [t.value for t in TimeFrame]
        if timeframe_str not in valid_timeframes:
            return (
                jsonify(
                    {"error": f'Invalid timeframe. Must be one of: {", ".join(valid_timeframes)}'}
                ),
                400,
            )

        timeframe = TimeFrame(timeframe_str)

        # Get funnel data
        funnel = analytics_service.get_lead_funnel(timeframe)

        if not funnel:
            return jsonify({"error": "Failed to get funnel data"}), 500

        return (
            jsonify(
                {
                    "success": True,
                    "funnel": funnel,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error fetching lead funnel: {str(e)}")
        return jsonify({"error": "Failed to fetch lead funnel"}), 500


@bp.route("/custom-report", methods=["POST"])
@require_auth
@require_role("manager")  # Only managers and above can run custom reports
def create_custom_report():
    """
    Generate a custom analytics report

    Request Body:
        {
            "name": "Report name",
            "metrics": ["leads", "revenue", "conversion"],
            "timeframe": "mtd",
            "filters": {
                "source": "google",
                "team_member_id": "uuid"
            },
            "group_by": "source"  // optional
        }

    Returns:
        201: Custom report data
        400: Invalid parameters
        401: Unauthorized
        403: Insufficient permissions
        500: Server error

    Example:
        POST /api/analytics/custom-report
        {
            "name": "Q4 Google Leads Report",
            "metrics": ["leads", "conversion"],
            "timeframe": "qtd",
            "filters": {"source": "google"}
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Validate required fields
        required_fields = ["name", "metrics", "timeframe"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400

        # Get timeframe
        timeframe_str = data["timeframe"]
        valid_timeframes = [t.value for t in TimeFrame]
        if timeframe_str not in valid_timeframes:
            return (
                jsonify(
                    {"error": f'Invalid timeframe. Must be one of: {", ".join(valid_timeframes)}'}
                ),
                400,
            )

        timeframe = TimeFrame(timeframe_str)
        start_date, end_date = analytics_service._get_date_range(timeframe)

        # Build custom report
        from app.config import get_supabase_client

        supabase = get_supabase_client()

        report_data = {
            "name": data["name"],
            "timeframe": timeframe_str,
            "generated_at": datetime.utcnow().isoformat(),
            "metrics": {},
        }

        # Process each requested metric
        for metric in data["metrics"]:
            if metric == "leads":
                query = (
                    supabase.table("leads")
                    .select("*")
                    .gte("created_at", start_date.isoformat())
                    .lte("created_at", end_date.isoformat())
                )

                # Apply filters
                if "filters" in data:
                    if "source" in data["filters"]:
                        query = query.eq("source", data["filters"]["source"])
                    if "team_member_id" in data["filters"]:
                        query = query.eq("assigned_to", data["filters"]["team_member_id"])

                result = query.execute()
                leads = result.data if result.data else []

                report_data["metrics"]["leads"] = {
                    "total": len(leads),
                    "hot": len([l for l in leads if l.get("temperature") == "hot"]),
                    "warm": len([l for l in leads if l.get("temperature") == "warm"]),
                    "cold": len([l for l in leads if l.get("temperature") == "cold"]),
                }

            elif metric == "revenue":
                query = (
                    supabase.table("projects")
                    .select("*")
                    .gte("created_at", start_date.isoformat())
                    .lte("created_at", end_date.isoformat())
                )

                # Apply filters
                if "filters" in data and "team_member_id" in data["filters"]:
                    query = query.eq("sales_rep_id", data["filters"]["team_member_id"])

                result = query.execute()
                projects = result.data if result.data else []

                report_data["metrics"]["revenue"] = {
                    "total_quoted": sum(float(p.get("quoted_amount", 0)) for p in projects),
                    "total_actual": sum(
                        float(p.get("actual_amount", 0))
                        for p in projects
                        if p.get("status") == "completed"
                    ),
                    "project_count": len(projects),
                }

            elif metric == "conversion":
                # Get conversion data with filters
                query = (
                    supabase.table("leads")
                    .select("*")
                    .gte("created_at", start_date.isoformat())
                    .lte("created_at", end_date.isoformat())
                )

                if "filters" in data:
                    if "source" in data["filters"]:
                        query = query.eq("source", data["filters"]["source"])
                    if "team_member_id" in data["filters"]:
                        query = query.eq("assigned_to", data["filters"]["team_member_id"])

                result = query.execute()
                leads = result.data if result.data else []

                total = len(leads)
                converted = len([l for l in leads if l.get("status") == "converted"])

                report_data["metrics"]["conversion"] = {
                    "total_leads": total,
                    "converted": converted,
                    "rate": round((converted / max(total, 1)) * 100, 2),
                }

        # Apply grouping if requested
        if "group_by" in data:
            # This would implement grouping logic
            pass

        # Store report for later retrieval (optional)
        report_record = {
            "name": data["name"],
            "created_by": g.get("user", {}).get("user_id"),
            "parameters": json.dumps(data),
            "results": json.dumps(report_data),
            "created_at": datetime.utcnow().isoformat(),
        }

        supabase.table("analytics_reports").insert(report_record).execute()

        return (
            jsonify(
                {
                    "success": True,
                    "report": report_data,
                }
            ),
            201,
        )

    except Exception as e:
        logger.error(f"Error creating custom report: {str(e)}")
        return jsonify({"error": "Failed to create custom report"}), 500


@bp.route("/realtime", methods=["GET"])
@require_auth
def get_realtime_metrics():
    """
    Get real-time metrics for live dashboard

    Returns:
        200: Current real-time metrics
        401: Unauthorized
        500: Server error

    Example:
        GET /api/analytics/realtime
    """
    try:
        # Get real-time metrics
        metrics = analytics_service.get_realtime_metrics()

        if not metrics:
            return jsonify({"error": "Failed to get realtime metrics"}), 500

        return (
            jsonify(
                {
                    "success": True,
                    "metrics": metrics,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error fetching realtime metrics: {str(e)}")
        return jsonify({"error": "Failed to fetch realtime metrics"}), 500


@bp.route("/stream/auth", methods=["POST"])
@require_auth
def pusher_auth():
    """
    Authenticate Pusher channel subscription

    Request Body:
        {
            "channel_name": "private-analytics",
            "socket_id": "socket_id_from_pusher"
        }

    Returns:
        200: Authentication signature
        400: Invalid request
        401: Unauthorized
        500: Server error

    Example:
        POST /api/analytics/stream/auth
        {
            "channel_name": "private-analytics",
            "socket_id": "12345.67890"
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        channel_name = data.get("channel_name")
        socket_id = data.get("socket_id")

        if not channel_name or not socket_id:
            return jsonify({"error": "channel_name and socket_id are required"}), 400

        # Get user info
        user = g.get("user")
        user_id = user.get("user_id") if user else None

        # Authenticate with Pusher
        pusher_service = get_pusher_service()
        auth_data = pusher_service.authenticate_channel(socket_id, channel_name, user_id)

        if "error" in auth_data:
            return jsonify({"error": auth_data["error"]}), 500

        return jsonify(auth_data), 200

    except Exception as e:
        logger.error(f"Error authenticating Pusher channel: {str(e)}")
        return jsonify({"error": "Failed to authenticate channel"}), 500


@bp.route("/export", methods=["GET"])
@require_auth
@require_role("manager")
def export_analytics():
    """
    Export analytics data to CSV or JSON

    Query Parameters:
        - format: Export format (csv, json) (default: json)
        - timeframe: Time period (default: mtd)
        - metrics: Comma-separated metrics to include

    Returns:
        200: Exported data
        401: Unauthorized
        403: Insufficient permissions
        500: Server error

    Example:
        GET /api/analytics/export?format=csv&timeframe=mtd&metrics=leads,revenue
    """
    try:
        export_format = request.args.get("format", "json")
        timeframe_str = request.args.get("timeframe", "mtd")
        metrics_str = request.args.get("metrics", "all")

        # Validate format
        if export_format not in ["csv", "json"]:
            return jsonify({"error": "Format must be csv or json"}), 400

        # Validate timeframe
        valid_timeframes = [t.value for t in TimeFrame]
        if timeframe_str not in valid_timeframes:
            return (
                jsonify(
                    {"error": f'Invalid timeframe. Must be one of: {", ".join(valid_timeframes)}'}
                ),
                400,
            )

        timeframe = TimeFrame(timeframe_str)

        # Get data
        export_data = analytics_service.calculate_kpis(timeframe)

        # Filter metrics if specified
        if metrics_str != "all":
            requested_metrics = metrics_str.split(",")
            filtered_data = {}
            for metric in requested_metrics:
                if metric in export_data:
                    filtered_data[metric] = export_data[metric]
            export_data = filtered_data

        if export_format == "json":
            return (
                jsonify(
                    {
                        "success": True,
                        "data": export_data,
                        "exported_at": datetime.utcnow().isoformat(),
                    }
                ),
                200,
            )
        else:
            # Convert to CSV format
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Flatten the nested structure for CSV
            rows = []
            for category, metrics in export_data.items():
                if isinstance(metrics, dict):
                    for key, value in metrics.items():
                        if not isinstance(value, (dict, list)):
                            rows.append([category, key, value])

            # Write CSV
            writer.writerow(["Category", "Metric", "Value"])
            writer.writerows(rows)

            from flask import Response

            return Response(
                output.getvalue(),
                mimetype="text/csv",
                headers={
                    "Content-Disposition": f"attachment;filename=analytics_{timeframe_str}.csv"
                },
            )

    except Exception as e:
        logger.error(f"Error exporting analytics: {str(e)}")
        return jsonify({"error": "Failed to export analytics"}), 500


# Health check endpoint
@bp.route("/health", methods=["GET"])
def health_check():
    """
    Check analytics service health

    Returns:
        200: Service is healthy
    """
    return (
        jsonify(
            {
                "success": True,
                "service": "analytics",
                "status": "healthy",
                "features": {
                    "kpis": True,
                    "forecasting": True,
                    "realtime": True,
                    "pusher": get_pusher_service().is_available(),
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
        ),
        200,
    )


# Error handlers
@bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Analytics endpoint not found"}), 404


@bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error in analytics API: {error}")
    return jsonify({"error": "Internal server error"}), 500
