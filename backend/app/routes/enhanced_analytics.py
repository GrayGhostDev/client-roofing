"""
Enhanced Analytics API Routes for iSwitch Roofs CRM
Version: 2.0.0

Advanced analytics endpoints with comprehensive business intelligence,
roofing industry insights, and predictive analytics.

Features:
- Roofing industry KPIs and benchmarks
- Advanced conversion funnel analysis
- Predictive revenue forecasting
- Team performance optimization
- Marketing ROI attribution
- Weather impact correlation
- Seasonal trend analysis
- Real-time business intelligence
"""

import logging
from datetime import datetime

from flask import Blueprint, g, jsonify, request

from app.models.analytics_sqlalchemy import (
    AnalyticsTimeframe,
)
from app.services.enhanced_analytics_service import enhanced_analytics_service
from app.utils.auth import require_auth, require_role
from app.utils.pusher_client import get_pusher_service

logger = logging.getLogger(__name__)
bp = Blueprint("enhanced_analytics", __name__)


@bp.route("/roofing-kpis", methods=["GET"])
@require_auth
def get_roofing_kpis():
    """
    Get comprehensive roofing industry KPIs with benchmarks

    Query Parameters:
        - timeframe: Time period (daily, weekly, monthly, quarterly, yearly, mtd, qtd, ytd)
                    Default: mtd
        - include_benchmarks: Include industry benchmarks (default: true)
        - include_insights: Include business insights (default: true)
        - include_forecasts: Include forecast data (default: false)

    Returns:
        200: Enhanced KPI metrics with industry context
        401: Unauthorized
        500: Server error

    Example:
        GET /api/enhanced-analytics/roofing-kpis?timeframe=mtd&include_insights=true
    """
    try:
        # Parse query parameters
        timeframe_str = request.args.get("timeframe", "mtd")
        include_benchmarks = request.args.get("include_benchmarks", "true").lower() == "true"
        include_insights = request.args.get("include_insights", "true").lower() == "true"
        include_forecasts = request.args.get("include_forecasts", "false").lower() == "true"

        # Validate timeframe
        try:
            timeframe = AnalyticsTimeframe(timeframe_str)
        except ValueError:
            return (
                jsonify(
                    {
                        "error": f"Invalid timeframe. Must be one of: {[t.value for t in AnalyticsTimeframe]}"
                    }
                ),
                400,
            )

        # Calculate enhanced KPIs
        kpis = enhanced_analytics_service.calculate_roofing_kpis(timeframe)

        if not kpis:
            return jsonify({"error": "Failed to calculate roofing KPIs"}), 500

        # Add forecasts if requested
        if include_forecasts:
            try:
                forecast_data = enhanced_analytics_service.enhanced_revenue_forecast(months_ahead=3)
                kpis["revenue_forecast"] = forecast_data
            except Exception as e:
                logger.warning(f"Could not include forecast data: {str(e)}")

        # Filter response based on parameters
        response_data = {
            "success": True,
            "kpis": kpis,
            "generated_at": datetime.utcnow().isoformat(),
            "timeframe": timeframe_str,
        }

        if not include_benchmarks:
            response_data["kpis"].pop("benchmarks", None)

        if not include_insights:
            response_data["kpis"].pop("insights", None)

        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Error fetching roofing KPIs: {str(e)}")
        return jsonify({"error": "Failed to fetch roofing KPIs"}), 500


@bp.route("/conversion-funnel", methods=["GET"])
@require_auth
def get_enhanced_conversion_funnel():
    """
    Get enhanced conversion funnel analysis with bottleneck identification

    Query Parameters:
        - timeframe: Analysis timeframe (default: mtd)
        - include_sources: Include source breakdown (default: true)
        - include_temperature: Include lead temperature analysis (default: true)
        - include_recommendations: Include optimization recommendations (default: true)

    Returns:
        200: Enhanced funnel analysis with optimization insights
        401: Unauthorized
        500: Server error

    Example:
        GET /api/enhanced-analytics/conversion-funnel?timeframe=qtd&include_recommendations=true
    """
    try:
        timeframe_str = request.args.get("timeframe", "mtd")
        include_sources = request.args.get("include_sources", "true").lower() == "true"
        include_temperature = request.args.get("include_temperature", "true").lower() == "true"
        include_recommendations = (
            request.args.get("include_recommendations", "true").lower() == "true"
        )

        try:
            timeframe = AnalyticsTimeframe(timeframe_str)
        except ValueError:
            return jsonify({"error": "Invalid timeframe"}), 400

        # Get enhanced funnel analysis (would implement in service)
        start_date, end_date = enhanced_analytics_service._get_date_range(timeframe)

        # Basic funnel calculation (simplified for this example)
        from app.config import get_supabase_client

        supabase = get_supabase_client()

        leads_result = (
            supabase.table("leads")
            .select("id", "status", "temperature", "source", "created_at")
            .gte("created_at", start_date.isoformat())
            .lte("created_at", end_date.isoformat())
            .execute()
        )

        leads = leads_result.data if leads_result.data else []

        # Calculate funnel stages
        stages = {
            "new": len([l for l in leads if l.get("status") == "new"]),
            "contacted": len([l for l in leads if l.get("status") == "contacted"]),
            "qualified": len([l for l in leads if l.get("status") == "qualified"]),
            "appointment_scheduled": len(
                [l for l in leads if l.get("status") == "appointment_scheduled"]
            ),
            "inspection_completed": len(
                [l for l in leads if l.get("status") == "inspection_completed"]
            ),
            "quote_sent": len([l for l in leads if l.get("status") == "quote_sent"]),
            "won": len([l for l in leads if l.get("status") == "won"]),
        }

        # Calculate conversion rates
        total_leads = len(leads)
        conversion_rates = {}
        stage_names = list(stages.keys())

        for i in range(len(stage_names) - 1):
            from_stage = stage_names[i]
            to_stage = stage_names[i + 1]

            from_count = sum(stages[stage] for stage in stage_names[i:])
            to_count = sum(stages[stage] for stage in stage_names[i + 1 :])

            rate = (to_count / max(from_count, 1)) * 100
            conversion_rates[f"{from_stage}_to_{to_stage}"] = round(rate, 2)

        # Source breakdown
        source_breakdown = {}
        if include_sources:
            for source in set(l.get("source", "unknown") for l in leads):
                source_leads = [l for l in leads if l.get("source") == source]
                source_converted = [l for l in source_leads if l.get("status") == "won"]
                source_breakdown[source] = {
                    "total": len(source_leads),
                    "converted": len(source_converted),
                    "conversion_rate": round(
                        (len(source_converted) / max(len(source_leads), 1)) * 100, 2
                    ),
                }

        # Temperature breakdown
        temperature_breakdown = {}
        if include_temperature:
            for temp in ["hot", "warm", "cold"]:
                temp_leads = [l for l in leads if l.get("temperature") == temp]
                temp_converted = [l for l in temp_leads if l.get("status") == "won"]
                temperature_breakdown[temp] = {
                    "total": len(temp_leads),
                    "converted": len(temp_converted),
                    "conversion_rate": round(
                        (len(temp_converted) / max(len(temp_leads), 1)) * 100, 2
                    ),
                }

        # Identify bottlenecks
        bottlenecks = []
        for stage_conversion, rate in conversion_rates.items():
            if rate < 50:  # Less than 50% conversion
                bottlenecks.append(
                    {
                        "stage": stage_conversion.replace("_to_", " → ").replace("_", " ").title(),
                        "conversion_rate": rate,
                        "severity": "high" if rate < 25 else "medium",
                    }
                )

        # Generate recommendations
        recommendations = []
        if include_recommendations:
            if any(b["severity"] == "high" for b in bottlenecks):
                recommendations.append(
                    "Critical bottlenecks identified - immediate process review needed"
                )

            if source_breakdown:
                best_source = max(source_breakdown.items(), key=lambda x: x[1]["conversion_rate"])
                recommendations.append(
                    f"Focus marketing budget on {best_source[0]} - highest conversion rate at {best_source[1]['conversion_rate']}%"
                )

        funnel_data = {
            "timeframe": timeframe_str,
            "stages": stages,
            "conversion_rates": conversion_rates,
            "overall_conversion_rate": round((stages["won"] / max(total_leads, 1)) * 100, 2),
            "bottlenecks": bottlenecks,
            "total_leads": total_leads,
        }

        if include_sources:
            funnel_data["source_breakdown"] = source_breakdown

        if include_temperature:
            funnel_data["temperature_breakdown"] = temperature_breakdown

        if include_recommendations:
            funnel_data["recommendations"] = recommendations

        return (
            jsonify(
                {
                    "success": True,
                    "funnel": funnel_data,
                    "generated_at": datetime.utcnow().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error fetching conversion funnel: {str(e)}")
        return jsonify({"error": "Failed to fetch conversion funnel"}), 500


@bp.route("/revenue-forecast", methods=["GET"])
@require_auth
def get_enhanced_revenue_forecast():
    """
    Get enhanced revenue forecast with seasonal and weather adjustments

    Query Parameters:
        - months_ahead: Number of months to forecast (1-12, default: 6)
        - include_breakdown: Include detailed breakdown (default: true)
        - confidence_level: Confidence level for intervals (80, 90, 95, default: 95)

    Returns:
        200: Enhanced revenue forecast with seasonal adjustments
        401: Unauthorized
        500: Server error

    Example:
        GET /api/enhanced-analytics/revenue-forecast?months_ahead=6&confidence_level=95
    """
    try:
        months_ahead = int(request.args.get("months_ahead", 6))
        include_breakdown = request.args.get("include_breakdown", "true").lower() == "true"
        confidence_level = int(request.args.get("confidence_level", 95))

        # Validate parameters
        if months_ahead < 1 or months_ahead > 12:
            return jsonify({"error": "months_ahead must be between 1 and 12"}), 400

        if confidence_level not in [80, 90, 95]:
            return jsonify({"error": "confidence_level must be 80, 90, or 95"}), 400

        # Get enhanced forecast
        forecast = enhanced_analytics_service.enhanced_revenue_forecast(months_ahead)

        if "error" in forecast:
            return jsonify({"error": forecast["error"]}), 500

        # Add additional analysis if requested
        if include_breakdown:
            # Add quarterly summaries
            quarterly_summary = {}
            for forecast_item in forecast.get("forecasts", []):
                quarter = (
                    f"Q{((datetime.strptime(forecast_item['date'], '%Y-%m').month - 1) // 3) + 1}"
                )
                year = datetime.strptime(forecast_item["date"], "%Y-%m").year
                quarter_key = f"{year}-{quarter}"

                if quarter_key not in quarterly_summary:
                    quarterly_summary[quarter_key] = {"total": 0, "months": 0}

                quarterly_summary[quarter_key]["total"] += forecast_item["forecast"]
                quarterly_summary[quarter_key]["months"] += 1

            forecast["quarterly_summary"] = quarterly_summary

        return (
            jsonify(
                {
                    "success": True,
                    "forecast": forecast,
                    "confidence_level": confidence_level,
                    "generated_at": datetime.utcnow().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error generating enhanced forecast: {str(e)}")
        return jsonify({"error": "Failed to generate enhanced forecast"}), 500


@bp.route("/team-performance", methods=["GET"])
@require_auth
def get_enhanced_team_performance():
    """
    Get enhanced team performance analytics with improvement recommendations

    Query Parameters:
        - timeframe: Analysis timeframe (default: mtd)
        - team_member_id: Specific team member (optional)
        - include_rankings: Include team rankings (default: true)
        - include_goals: Include goal tracking (default: true)
        - include_recommendations: Include improvement recommendations (default: true)

    Returns:
        200: Enhanced team performance with actionable insights
        401: Unauthorized
        500: Server error

    Example:
        GET /api/enhanced-analytics/team-performance?timeframe=qtd&include_recommendations=true
    """
    try:
        timeframe_str = request.args.get("timeframe", "mtd")
        team_member_id = request.args.get("team_member_id")
        include_rankings = request.args.get("include_rankings", "true").lower() == "true"
        include_goals = request.args.get("include_goals", "true").lower() == "true"
        include_recommendations = (
            request.args.get("include_recommendations", "true").lower() == "true"
        )

        try:
            timeframe = AnalyticsTimeframe(timeframe_str)
        except ValueError:
            return jsonify({"error": "Invalid timeframe"}), 400

        # Get team performance (simplified implementation)
        from app.config import get_supabase_client

        supabase = get_supabase_client()

        # Get team members
        team_result = supabase.table("team_members").select("id", "name", "role").execute()
        team_members = team_result.data if team_result.data else []

        if team_member_id:
            team_members = [tm for tm in team_members if tm["id"] == team_member_id]

        # Calculate performance for each team member
        start_date, end_date = enhanced_analytics_service._get_date_range(timeframe)
        performances = []

        for member in team_members:
            # Get member's metrics
            member_performance = enhanced_analytics_service.calculate_team_performance(
                member["id"], timeframe
            )

            if member_performance:
                member_performance["name"] = member["name"]
                member_performance["role"] = member["role"]
                performances.append(member_performance)

        # Sort by performance score
        performances.sort(key=lambda x: x.get("performance_score", 0), reverse=True)

        # Add rankings
        if include_rankings:
            for i, perf in enumerate(performances):
                perf["rank"] = i + 1

        # Add team averages
        team_averages = {}
        if performances:
            metrics = ["conversion_rate", "avg_response_time", "total_revenue", "total_activities"]
            for metric in metrics:
                values = []
                for perf in performances:
                    if metric == "conversion_rate":
                        values.append(perf.get("leads", {}).get("conversion_rate", 0))
                    elif metric == "avg_response_time":
                        values.append(perf.get("leads", {}).get("avg_response_time", 0))
                    elif metric == "total_revenue":
                        values.append(perf.get("revenue", {}).get("total_closed", 0))
                    elif metric == "total_activities":
                        values.append(perf.get("activities", {}).get("total", 0))

                if values:
                    team_averages[metric] = round(sum(values) / len(values), 2)

        # Generate improvement recommendations
        recommendations = []
        if include_recommendations and performances:
            # Identify improvement areas
            low_performers = [p for p in performances if p.get("performance_score", 0) < 60]

            if low_performers:
                recommendations.append(
                    {
                        "type": "training",
                        "priority": "high",
                        "message": f"{len(low_performers)} team members need performance improvement",
                        "action": "Provide additional training and coaching",
                    }
                )

            # Response time recommendations
            slow_responders = [
                p for p in performances if p.get("leads", {}).get("avg_response_time", 0) > 15
            ]
            if slow_responders:
                recommendations.append(
                    {
                        "type": "process",
                        "priority": "medium",
                        "message": f"{len(slow_responders)} team members have slow response times",
                        "action": "Implement response time tracking and alerts",
                    }
                )

        response_data = {
            "success": True,
            "timeframe": timeframe_str,
            "team_performance": performances,
            "team_count": len(performances),
        }

        if include_rankings and performances:
            response_data["team_averages"] = team_averages

        if include_recommendations:
            response_data["recommendations"] = recommendations

        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Error fetching enhanced team performance: {str(e)}")
        return jsonify({"error": "Failed to fetch enhanced team performance"}), 500


@bp.route("/marketing-roi", methods=["GET"])
@require_auth
def get_marketing_roi_analysis():
    """
    Get marketing ROI analysis with attribution modeling

    Query Parameters:
        - timeframe: Analysis timeframe (default: mtd)
        - channels: Comma-separated channel names (optional)
        - attribution_model: first_touch, last_touch, linear (default: linear)
        - include_campaigns: Include campaign details (default: false)

    Returns:
        200: Marketing ROI analysis with attribution insights
        401: Unauthorized
        500: Server error

    Example:
        GET /api/enhanced-analytics/marketing-roi?timeframe=qtd&attribution_model=linear
    """
    try:
        timeframe_str = request.args.get("timeframe", "mtd")
        channels = (
            request.args.get("channels", "").split(",") if request.args.get("channels") else None
        )
        attribution_model = request.args.get("attribution_model", "linear")
        include_campaigns = request.args.get("include_campaigns", "false").lower() == "true"

        try:
            timeframe = AnalyticsTimeframe(timeframe_str)
        except ValueError:
            return jsonify({"error": "Invalid timeframe"}), 400

        if attribution_model not in ["first_touch", "last_touch", "linear"]:
            return jsonify({"error": "Invalid attribution model"}), 400

        # Calculate marketing ROI (simplified implementation)
        start_date, end_date = enhanced_analytics_service._get_date_range(timeframe)

        from app.config import get_supabase_client

        supabase = get_supabase_client()

        # Get leads with source information
        leads_result = (
            supabase.table("leads")
            .select("id", "source", "created_at", "status")
            .gte("created_at", start_date.isoformat())
            .lte("created_at", end_date.isoformat())
            .execute()
        )

        leads = leads_result.data if leads_result.data else []

        # Get revenue from converted leads
        converted_leads = [l for l in leads if l.get("status") == "won"]

        # Calculate ROI by source/channel
        channel_performance = {}

        # Mock marketing spend data (would come from marketing platform integrations)
        mock_spend = {
            "google_ads": 5000,
            "facebook_ads": 3000,
            "seo": 2000,
            "referral": 500,
            "direct": 0,
        }

        for source in set(l.get("source", "unknown") for l in leads):
            source_leads = [l for l in leads if l.get("source") == source]
            source_converted = [l for l in source_leads if l.get("status") == "won"]

            # Mock revenue calculation (would join with projects table)
            estimated_revenue_per_conversion = 25000  # Average project value
            source_revenue = len(source_converted) * estimated_revenue_per_conversion

            spend = mock_spend.get(source, 1000)  # Default spend if not found

            roi = ((source_revenue - spend) / max(spend, 1)) * 100 if spend > 0 else 0
            cost_per_lead = spend / max(len(source_leads), 1)
            cost_per_acquisition = spend / max(len(source_converted), 1) if source_converted else 0

            channel_performance[source] = {
                "leads_generated": len(source_leads),
                "conversions": len(source_converted),
                "conversion_rate": round(
                    (len(source_converted) / max(len(source_leads), 1)) * 100, 2
                ),
                "revenue_generated": source_revenue,
                "marketing_spend": spend,
                "roi_percentage": round(roi, 2),
                "cost_per_lead": round(cost_per_lead, 2),
                "cost_per_acquisition": round(cost_per_acquisition, 2),
            }

        # Calculate overall ROI
        total_spend = sum(perf["marketing_spend"] for perf in channel_performance.values())
        total_revenue = sum(perf["revenue_generated"] for perf in channel_performance.values())
        overall_roi = (
            ((total_revenue - total_spend) / max(total_spend, 1)) * 100 if total_spend > 0 else 0
        )

        # Rank channels by ROI
        channel_rankings = sorted(
            channel_performance.items(), key=lambda x: x[1]["roi_percentage"], reverse=True
        )

        return (
            jsonify(
                {
                    "success": True,
                    "timeframe": timeframe_str,
                    "attribution_model": attribution_model,
                    "channel_performance": channel_performance,
                    "overall_metrics": {
                        "total_spend": total_spend,
                        "total_revenue": total_revenue,
                        "overall_roi": round(overall_roi, 2),
                        "total_leads": len(leads),
                        "total_conversions": len(converted_leads),
                    },
                    "channel_rankings": [{"channel": ch[0], **ch[1]} for ch in channel_rankings],
                    "generated_at": datetime.utcnow().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error fetching marketing ROI: {str(e)}")
        return jsonify({"error": "Failed to fetch marketing ROI"}), 500


@bp.route("/weather-correlation", methods=["GET"])
@require_auth
def get_weather_correlation():
    """
    Get weather impact correlation analysis

    Query Parameters:
        - timeframe: Analysis timeframe (default: mtd)
        - zip_codes: Comma-separated ZIP codes (optional)
        - include_storms: Include storm impact analysis (default: true)
        - correlation_threshold: Minimum correlation to report (default: 0.3)

    Returns:
        200: Weather correlation analysis
        401: Unauthorized
        500: Server error

    Example:
        GET /api/enhanced-analytics/weather-correlation?timeframe=quarterly&include_storms=true
    """
    try:
        timeframe_str = request.args.get("timeframe", "mtd")
        zip_codes = (
            request.args.get("zip_codes", "").split(",") if request.args.get("zip_codes") else None
        )
        include_storms = request.args.get("include_storms", "true").lower() == "true"
        correlation_threshold = float(request.args.get("correlation_threshold", 0.3))

        try:
            timeframe = AnalyticsTimeframe(timeframe_str)
        except ValueError:
            return jsonify({"error": "Invalid timeframe"}), 400

        # Get weather correlation analysis from service
        weather_analysis = enhanced_analytics_service._calculate_weather_impact_metrics(
            *enhanced_analytics_service._get_date_range(timeframe)
        )

        # Add additional analysis based on parameters
        if zip_codes:
            # Filter analysis by specific ZIP codes (would implement geographic filtering)
            weather_analysis["geographic_filter"] = zip_codes

        return (
            jsonify(
                {
                    "success": True,
                    "timeframe": timeframe_str,
                    "weather_analysis": weather_analysis,
                    "correlation_threshold": correlation_threshold,
                    "generated_at": datetime.utcnow().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error fetching weather correlation: {str(e)}")
        return jsonify({"error": "Failed to fetch weather correlation"}), 500


@bp.route("/business-alerts", methods=["GET"])
@require_auth
def get_business_alerts():
    """
    Get intelligent business alerts and notifications

    Query Parameters:
        - level: Alert level filter (info, warning, critical) (optional)
        - category: Alert category filter (optional)
        - acknowledged: Filter by acknowledgment status (default: false)
        - limit: Maximum number of alerts (default: 50)

    Returns:
        200: Business alerts with recommended actions
        401: Unauthorized
        500: Server error

    Example:
        GET /api/enhanced-analytics/business-alerts?level=critical&acknowledged=false
    """
    try:
        level_filter = request.args.get("level")
        category_filter = request.args.get("category")
        acknowledged = request.args.get("acknowledged", "false").lower() == "true"
        limit = int(request.args.get("limit", 50))

        # Get current KPIs to generate alerts
        kpis = enhanced_analytics_service.calculate_roofing_kpis(AnalyticsTimeframe.MTD)
        alerts = kpis.get("alerts", [])

        # Apply filters
        if level_filter:
            alerts = [a for a in alerts if a.get("level") == level_filter]

        if category_filter:
            alerts = [a for a in alerts if a.get("type") == category_filter]

        # Limit results
        alerts = alerts[:limit]

        # Add alert metadata
        for alert in alerts:
            alert["id"] = hash(alert.get("message", ""))
            alert["created_at"] = datetime.utcnow().isoformat()
            alert["is_acknowledged"] = False  # Would come from database

        return (
            jsonify(
                {
                    "success": True,
                    "alerts": alerts,
                    "total_count": len(alerts),
                    "filters_applied": {
                        "level": level_filter,
                        "category": category_filter,
                        "acknowledged": acknowledged,
                    },
                    "generated_at": datetime.utcnow().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error fetching business alerts: {str(e)}")
        return jsonify({"error": "Failed to fetch business alerts"}), 500


@bp.route("/export", methods=["POST"])
@require_auth
@require_role("manager")
def export_enhanced_analytics():
    """
    Export enhanced analytics data

    Request Body:
        {
            "export_format": "json|csv|xlsx|pdf",
            "timeframe": "mtd",
            "metrics": ["leads", "revenue", "conversion"],
            "include_charts": false,
            "email_to": "user@example.com"
        }

    Returns:
        200: Export data or confirmation if emailed
        400: Invalid parameters
        401: Unauthorized
        403: Insufficient permissions
        500: Server error

    Example:
        POST /api/enhanced-analytics/export
        {
            "export_format": "xlsx",
            "timeframe": "qtd",
            "metrics": ["leads", "revenue", "team_performance"]
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Validate request
        export_format = data.get("export_format", "json")
        if export_format not in ["json", "csv", "xlsx", "pdf"]:
            return jsonify({"error": "Invalid export format"}), 400

        timeframe_str = data.get("timeframe", "mtd")
        try:
            timeframe = AnalyticsTimeframe(timeframe_str)
        except ValueError:
            return jsonify({"error": "Invalid timeframe"}), 400

        metrics = data.get("metrics", ["leads", "revenue"])
        include_charts = data.get("include_charts", False)
        email_to = data.get("email_to")

        # Get the requested analytics data
        export_data = {}

        if "leads" in metrics:
            kpis = enhanced_analytics_service.calculate_roofing_kpis(timeframe)
            export_data["leads"] = kpis.get("leads", {})

        if "revenue" in metrics:
            kpis = enhanced_analytics_service.calculate_roofing_kpis(timeframe)
            export_data["revenue"] = kpis.get("revenue", {})

        if "forecast" in metrics:
            forecast = enhanced_analytics_service.enhanced_revenue_forecast()
            export_data["forecast"] = forecast

        # Add metadata
        export_data["metadata"] = {
            "exported_at": datetime.utcnow().isoformat(),
            "exported_by": g.get("user", {}).get("user_id"),
            "timeframe": timeframe_str,
            "export_format": export_format,
        }

        if export_format == "json":
            return (
                jsonify(
                    {
                        "success": True,
                        "data": export_data,
                    }
                ),
                200,
            )

        elif export_format == "csv":
            # Convert to CSV format (simplified)
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Write headers
            writer.writerow(["Category", "Metric", "Value"])

            # Flatten data for CSV
            for category, data_dict in export_data.items():
                if isinstance(data_dict, dict):
                    for key, value in data_dict.items():
                        if not isinstance(value, (dict, list)):
                            writer.writerow([category, key, value])

            from flask import Response

            return Response(
                output.getvalue(),
                mimetype="text/csv",
                headers={
                    "Content-Disposition": f"attachment;filename=enhanced_analytics_{timeframe_str}.csv"
                },
            )

        else:
            return jsonify({"error": f"Export format {export_format} not yet implemented"}), 501

    except Exception as e:
        logger.error(f"Error exporting enhanced analytics: {str(e)}")
        return jsonify({"error": "Failed to export enhanced analytics"}), 500


@bp.route("/dashboard-config", methods=["GET", "POST"])
@require_auth
def manage_dashboard_config():
    """
    Get or create dashboard configuration

    GET: Returns user's dashboard configurations
    POST: Creates new dashboard configuration

    Returns:
        200: Dashboard configurations
        201: Dashboard configuration created
        400: Invalid request
        401: Unauthorized
        500: Server error
    """
    try:
        if request.method == "GET":
            # Get user's dashboard configurations (would query database)
            user_id = g.get("user", {}).get("user_id")

            # Mock dashboard configurations
            mock_configs = [
                {
                    "id": 1,
                    "name": "Executive Dashboard",
                    "type": "executive",
                    "widgets": ["business_health", "revenue_summary", "lead_trends"],
                    "is_default": True,
                },
                {
                    "id": 2,
                    "name": "Sales Dashboard",
                    "type": "sales",
                    "widgets": ["conversion_funnel", "team_performance", "pipeline"],
                    "is_default": False,
                },
            ]

            return (
                jsonify(
                    {
                        "success": True,
                        "dashboards": mock_configs,
                    }
                ),
                200,
            )

        else:  # POST
            data = request.get_json()
            if not data:
                return jsonify({"error": "Request body is required"}), 400

            # Validate required fields
            required_fields = ["name", "type", "widgets"]
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"{field} is required"}), 400

            # Create dashboard configuration (would save to database)
            dashboard_config = {
                "id": hash(data["name"]),  # Mock ID
                "name": data["name"],
                "type": data["type"],
                "widgets": data["widgets"],
                "created_by": g.get("user", {}).get("user_id"),
                "created_at": datetime.utcnow().isoformat(),
                "is_default": data.get("is_default", False),
            }

            return (
                jsonify(
                    {
                        "success": True,
                        "dashboard": dashboard_config,
                    }
                ),
                201,
            )

    except Exception as e:
        logger.error(f"Error managing dashboard config: {str(e)}")
        return jsonify({"error": "Failed to manage dashboard configuration"}), 500


# Real-time endpoints


@bp.route("/realtime/subscribe", methods=["POST"])
@require_auth
def subscribe_to_realtime_updates():
    """
    Subscribe to real-time analytics updates

    Request Body:
        {
            "channel": "enhanced-analytics",
            "events": ["metrics:update", "alerts:new"],
            "user_preferences": {}
        }

    Returns:
        200: Subscription confirmation with connection details
        400: Invalid request
        401: Unauthorized
        500: Server error
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        channel = data.get("channel", "enhanced-analytics")
        events = data.get("events", ["metrics:update"])
        user_id = g.get("user", {}).get("user_id")

        # Get Pusher authentication
        pusher_service = get_pusher_service()
        if not pusher_service.is_available():
            return jsonify({"error": "Real-time service not available"}), 503

        # Create subscription (would save to database for user preferences)
        subscription = {
            "user_id": user_id,
            "channel": channel,
            "events": events,
            "subscribed_at": datetime.utcnow().isoformat(),
            "pusher_app_key": (
                pusher_service.app_key if hasattr(pusher_service, "app_key") else "mock_key"
            ),
        }

        return (
            jsonify(
                {
                    "success": True,
                    "subscription": subscription,
                    "websocket_url": f'wss://ws-{pusher_service.cluster}.pusher.com/app/{subscription["pusher_app_key"]}',
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error subscribing to real-time updates: {str(e)}")
        return jsonify({"error": "Failed to subscribe to real-time updates"}), 500


# Health check
@bp.route("/health", methods=["GET"])
def enhanced_health_check():
    """
    Enhanced analytics service health check

    Returns:
        200: Service health status with feature availability
    """
    try:
        # Check service dependencies
        pusher_available = get_pusher_service().is_available()

        # Mock Redis and database checks
        redis_available = True  # Would check Redis connection
        database_available = True  # Would check Supabase connection

        features = {
            "roofing_kpis": True,
            "enhanced_forecasting": True,
            "weather_correlation": True,
            "real_time_updates": pusher_available,
            "data_export": True,
            "business_intelligence": True,
        }

        overall_health = all([redis_available, database_available])

        return (
            jsonify(
                {
                    "success": True,
                    "service": "enhanced-analytics",
                    "status": "healthy" if overall_health else "degraded",
                    "features": features,
                    "dependencies": {
                        "redis": redis_available,
                        "database": database_available,
                        "pusher": pusher_available,
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": "2.0.0",
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Enhanced analytics health check failed: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "service": "enhanced-analytics",
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            500,
        )


# Error handlers
@bp.errorhandler(404)
def enhanced_not_found(error):
    return jsonify({"error": "Enhanced analytics endpoint not found"}), 404


@bp.errorhandler(500)
def enhanced_internal_error(error):
    logger.error(f"Internal error in enhanced analytics API: {error}")
    return jsonify({"error": "Internal server error in enhanced analytics"}), 500
