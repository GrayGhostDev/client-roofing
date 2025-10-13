"""
Live Data Collection API Routes
Real-time lead generation and data extraction
"""

import asyncio
from flask import Blueprint, jsonify, request
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.auth import require_auth
from app.services.intelligence.live_data_collector import LiveDataCollector, run_live_collection

bp = Blueprint("live_data", __name__)


@bp.route("/generate", methods=["POST"])
@require_auth
def generate_leads():
    """
    Generate realistic leads from public data sources

    POST /api/live-data/generate
    Body: {
        "count": 50,  // Number of leads to generate
        "filters": {
            "min_value": 500000,
            "cities": ["Bloomfield Hills", "Birmingham"]
        }
    }

    Returns: Generation results with statistics
    """
    try:
        data = request.get_json() or {}
        count = data.get("count", 50)

        if count < 1 or count > 500:
            return jsonify({
                "error": "Count must be between 1 and 500"
            }), 400

        # Get database session
        db = next(get_db())

        # Run async collection
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(run_live_collection(db, count))
        loop.close()

        return jsonify({
            "success": results["success"],
            "message": f"Generated and ingested {results.get('ingested', 0)} leads",
            "statistics": {
                "total_generated": results.get("total", 0),
                "successfully_ingested": results.get("ingested", 0),
                "duplicates_skipped": results.get("skipped", 0)
            }
        }), 200

    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Failed to generate leads"
        }), 500


@bp.route("/preview", methods=["POST"])
@require_auth
def preview_leads():
    """
    Preview lead generation without database insertion

    POST /api/live-data/preview
    Body: {
        "count": 10
    }

    Returns: Sample leads with scores
    """
    try:
        data = request.get_json() or {}
        count = min(data.get("count", 10), 50)  # Max 50 for preview

        db = next(get_db())
        collector = LiveDataCollector(db)

        # Generate leads
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        leads = loop.run_until_complete(collector.collect_sample_leads(count))
        loop.close()

        # Convert datetime objects to strings
        for lead in leads:
            if "created_at" in lead:
                lead["created_at"] = lead["created_at"].isoformat()
            # Convert enums to values
            if "source" in lead:
                lead["source"] = lead["source"].value
            if "status" in lead:
                lead["status"] = lead["status"].value
            if "temperature" in lead:
                lead["temperature"] = lead["temperature"].value

        return jsonify({
            "success": True,
            "leads": leads,
            "count": len(leads),
            "statistics": {
                "hot_leads": len([l for l in leads if l.get("lead_score", 0) >= 80]),
                "warm_leads": len([l for l in leads if 60 <= l.get("lead_score", 0) < 80]),
                "cool_leads": len([l for l in leads if 40 <= l.get("lead_score", 0) < 60]),
                "cold_leads": len([l for l in leads if l.get("lead_score", 0) < 40]),
                "avg_score": sum(l.get("lead_score", 0) for l in leads) / len(leads) if leads else 0
            }
        }), 200

    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Failed to preview leads"
        }), 500


@bp.route("/stats", methods=["GET"])
@require_auth
def get_collection_stats():
    """
    Get statistics about live data collection

    GET /api/live-data/stats

    Returns: Collection statistics
    """
    try:
        db = next(get_db())

        from app.models.lead_sqlalchemy import Lead
        from sqlalchemy import func
        from datetime import datetime, timedelta

        # Get leads from last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        total_leads = db.query(func.count(Lead.id)).scalar() or 0
        recent_leads = db.query(func.count(Lead.id)).filter(
            Lead.created_at >= thirty_days_ago
        ).scalar() or 0

        # Temperature distribution
        hot_leads = db.query(func.count(Lead.id)).filter(Lead.lead_score >= 80).scalar() or 0
        warm_leads = db.query(func.count(Lead.id)).filter(
            Lead.lead_score >= 60,
            Lead.lead_score < 80
        ).scalar() or 0
        cool_leads = db.query(func.count(Lead.id)).filter(
            Lead.lead_score >= 40,
            Lead.lead_score < 60
        ).scalar() or 0
        cold_leads = db.query(func.count(Lead.id)).filter(Lead.lead_score < 40).scalar() or 0

        # Average score
        avg_score = db.query(func.avg(Lead.lead_score)).scalar() or 0

        return jsonify({
            "success": True,
            "statistics": {
                "total_leads": total_leads,
                "recent_leads_30d": recent_leads,
                "temperature_distribution": {
                    "hot": hot_leads,
                    "warm": warm_leads,
                    "cool": cool_leads,
                    "cold": cold_leads
                },
                "average_score": round(float(avg_score), 2)
            }
        }), 200

    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Failed to get statistics"
        }), 500


@bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint

    GET /api/live-data/health
    """
    return jsonify({
        "status": "healthy",
        "service": "live_data_collector",
        "version": "1.0.0"
    }), 200
