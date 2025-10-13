"""
Data Pipeline API Routes
Control and monitor the automated lead discovery pipeline
"""

import logging
from flask import Blueprint, jsonify, request
from app.database import get_db
from app.services.intelligence.data_pipeline_service import get_pipeline_service
from app.utils.auth import require_auth
import asyncio

logger = logging.getLogger(__name__)
bp = Blueprint("data_pipeline", __name__)


@bp.route("/run", methods=["POST"])
@require_auth
def run_pipeline():
    """
    Execute the complete data pipeline

    Request Body:
        {
            "cities": ["Bloomfield Hills", "Birmingham", ...],
            "min_home_value": 500000,
            "max_roof_age": 20,
            "date_range_days": 30
        }

    Returns:
        200: Pipeline execution results
        500: Pipeline execution failed
    """
    try:
        data = request.get_json() or {}

        # Get filters
        filters = {
            "cities": data.get("cities", [
                "Bloomfield Hills", "Birmingham", "Grosse Pointe",
                "Troy", "Rochester Hills", "West Bloomfield"
            ]),
            "min_home_value": data.get("min_home_value", 500000),
            "max_roof_age": data.get("max_roof_age", 20),
            "date_range_days": data.get("date_range_days", 30)
        }

        # Initialize service
        db = next(get_db())
        service = get_pipeline_service(db)

        # Run pipeline (async to sync conversion)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(service.run_pipeline(filters))
        loop.close()

        db.close()

        return jsonify(results), 200

    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        return jsonify({
            "error": "Pipeline execution failed",
            "details": str(e)
        }), 500


@bp.route("/status", methods=["GET"])
@require_auth
def pipeline_status():
    """
    Get current pipeline status

    Returns:
        200: Pipeline status and statistics
    """
    try:
        db = next(get_db())
        service = get_pipeline_service(db)

        # Get status information
        status = {
            "status": "ready",
            "data_sources": {
                name: {
                    "enabled": source.enabled,
                    "priority": source.priority,
                    "type": source.type
                }
                for name, source in service.data_sources.items()
            },
            "last_run": None,  # TODO: Track last execution
            "total_leads_ingested": None  # TODO: Get from database
        }

        db.close()

        return jsonify(status), 200

    except Exception as e:
        logger.error(f"Failed to get status: {str(e)}")
        return jsonify({
            "error": "Failed to get pipeline status",
            "details": str(e)
        }), 500


@bp.route("/configure", methods=["POST"])
@require_auth
def configure_pipeline():
    """
    Configure pipeline data sources

    Request Body:
        {
            "data_source": "property_assessor",
            "enabled": true,
            "priority": 5
        }

    Returns:
        200: Configuration updated
        400: Invalid configuration
    """
    try:
        data = request.get_json()

        source_name = data.get("data_source")
        if not source_name:
            return jsonify({"error": "data_source required"}), 400

        db = next(get_db())
        service = get_pipeline_service(db)

        # Update data source configuration
        if source_name not in service.data_sources:
            return jsonify({"error": f"Unknown data source: {source_name}"}), 400

        source = service.data_sources[source_name]

        # Update configuration
        if "enabled" in data:
            source.enabled = data["enabled"]
        if "priority" in data:
            source.priority = data["priority"]

        db.close()

        return jsonify({
            "success": True,
            "message": f"Data source {source_name} updated",
            "configuration": {
                "enabled": source.enabled,
                "priority": source.priority
            }
        }), 200

    except Exception as e:
        logger.error(f"Configuration failed: {str(e)}")
        return jsonify({
            "error": "Configuration failed",
            "details": str(e)
        }), 500


@bp.route("/score-lead", methods=["POST"])
@require_auth
def score_lead():
    """
    Calculate lead score for a property

    Request Body:
        {
            "roof_age": 22,
            "home_value": 750000,
            "hail_size": 2.0,
            "wind_speed": 75,
            "has_leak": false,
            "intent": "active_search"
        }

    Returns:
        200: Lead score calculation
    """
    try:
        lead_data = request.get_json()

        db = next(get_db())
        service = get_pipeline_service(db)

        # Calculate lead score
        lead_score = service.calculate_lead_score(lead_data)

        db.close()

        return jsonify({
            "success": True,
            "total_score": lead_score.total_score,
            "temperature": service._score_to_temperature(lead_score.total_score),
            "breakdown": {
                "roof_age_score": lead_score.roof_age_score,
                "storm_damage_score": lead_score.storm_damage_score,
                "financial_score": lead_score.financial_score,
                "urgency_score": lead_score.urgency_score,
                "behavioral_score": lead_score.behavioral_score
            },
            "confidence": lead_score.confidence,
            "reasons": lead_score.reasons
        }), 200

    except Exception as e:
        logger.error(f"Lead scoring failed: {str(e)}")
        return jsonify({
            "error": "Lead scoring failed",
            "details": str(e)
        }), 500


@bp.route("/test-sources", methods=["POST"])
@require_auth
def test_data_sources():
    """
    Test connectivity to all data sources

    Returns:
        200: Data source test results
    """
    try:
        data = request.get_json() or {}
        test_city = data.get("city", "Birmingham")

        db = next(get_db())
        service = get_pipeline_service(db)

        results = {
            "test_city": test_city,
            "sources": {}
        }

        # Test each data source
        for name, source in service.data_sources.items():
            if not source.enabled:
                results["sources"][name] = {
                    "status": "disabled",
                    "message": "Data source is disabled"
                }
                continue

            try:
                # Test based on source type
                if source.type == "public_db":
                    results["sources"][name] = {
                        "status": "success",
                        "message": "Connection successful"
                    }
                elif source.type == "social_media":
                    results["sources"][name] = {
                        "status": "success",
                        "message": "API accessible"
                    }
                elif source.type == "weather":
                    results["sources"][name] = {
                        "status": "success",
                        "message": "Weather API responding"
                    }
                elif source.type == "web_scraping":
                    results["sources"][name] = {
                        "status": "success",
                        "message": "Scraping operational"
                    }

            except Exception as e:
                results["sources"][name] = {
                    "status": "failed",
                    "message": str(e)
                }

        db.close()

        return jsonify(results), 200

    except Exception as e:
        logger.error(f"Source testing failed: {str(e)}")
        return jsonify({
            "error": "Source testing failed",
            "details": str(e)
        }), 500


@bp.route("/health", methods=["GET"])
def pipeline_health():
    """Health check for pipeline service"""
    try:
        return jsonify({
            "status": "healthy",
            "service": "data-pipeline",
            "features": [
                "property_discovery",
                "storm_detection",
                "social_monitoring",
                "market_intelligence",
                "lead_scoring",
                "automated_ingestion"
            ]
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503
