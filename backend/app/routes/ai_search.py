"""
AI-Powered Search API Routes
Natural language search interface for querying CRM data
"""

import logging
from typing import List
from flask import Blueprint, jsonify, request
from app.database import get_db
from app.services.ai_search_service import AISearchService
from app.utils.auth import require_auth
import asyncio

logger = logging.getLogger(__name__)
bp = Blueprint("ai_search", __name__)


@bp.route("/search", methods=["POST"])
@require_auth
def ai_search():
    """
    AI-powered search endpoint

    Request Body:
        {
            "query": "Find all hot leads from this week",
            "context": {
                "filters": {...},
                "user_preferences": {...}
            }
        }

    Returns:
        200: Search results with AI-interpreted intent
        400: Invalid request
        500: Server error
    """
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        context = data.get('context', {})

        if not query:
            return jsonify({
                "error": "Query is required",
                "message": "Please provide a search query"
            }), 400

        if len(query) < 3:
            return jsonify({
                "error": "Query too short",
                "message": "Search query must be at least 3 characters"
            }), 400

        # Initialize service
        db = next(get_db())
        service = AISearchService(db)

        # Process search query using GPT-4o
        try:
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(
                service.process_search_query(query, context)
            )
            loop.close()
        finally:
            db.close()

        return jsonify(results), 200

    except Exception as e:
        logger.error(f"AI search error: {str(e)}")
        return jsonify({
            "error": "Search failed",
            "details": str(e)
        }), 500


@bp.route("/suggest", methods=["POST"])
@require_auth
def suggest_queries():
    """
    Suggest search queries based on partial input

    Request Body:
        {
            "partial_query": "show me leads",
            "limit": 5
        }

    Returns:
        200: List of suggested queries
        400: Invalid request
        500: Server error
    """
    try:
        data = request.get_json()
        partial_query = data.get('partial_query', '').strip()
        limit = data.get('limit', 5)

        if not partial_query:
            return jsonify({
                "error": "Partial query is required"
            }), 400

        # Common search patterns
        suggestions = _generate_suggestions(partial_query, limit)

        return jsonify({
            "success": True,
            "partial_query": partial_query,
            "suggestions": suggestions,
            "count": len(suggestions)
        }), 200

    except Exception as e:
        logger.error(f"Suggestion error: {str(e)}")
        return jsonify({
            "error": "Suggestion generation failed",
            "details": str(e)
        }), 500


@bp.route("/examples", methods=["GET"])
def get_search_examples():
    """
    Get example search queries to help users

    Returns:
        200: List of example queries by category
    """
    examples = {
        "success": True,
        "categories": [
            {
                "category": "Leads",
                "icon": "👥",
                "examples": [
                    "Show me all hot leads from this week",
                    "Find new leads that haven't been contacted",
                    "Get qualified leads with high scores",
                    "List all leads from Google Ads",
                    "Show leads created today"
                ]
            },
            {
                "category": "Customers",
                "icon": "🏠",
                "examples": [
                    "Find all premium tier customers",
                    "Show customers with projects over $50k",
                    "List recent customers from this month",
                    "Get customers in Bloomfield Hills",
                    "Find customers who need follow-up"
                ]
            },
            {
                "category": "Projects",
                "icon": "🏗️",
                "examples": [
                    "Show active projects",
                    "Find projects starting this week",
                    "List completed projects from last month",
                    "Get high-value projects over $100k",
                    "Show projects by status"
                ]
            },
            {
                "category": "Voice Calls",
                "icon": "📞",
                "examples": [
                    "Find calls with negative sentiment",
                    "Show today's voice interactions",
                    "List calls that were escalated to human",
                    "Get calls with appointment scheduled",
                    "Find calls about roof repairs"
                ]
            },
            {
                "category": "Appointments",
                "icon": "📅",
                "examples": [
                    "Show appointments for today",
                    "Find scheduled inspections this week",
                    "List upcoming appointments",
                    "Get cancelled appointments",
                    "Show appointments that need confirmation"
                ]
            }
        ]
    }

    return jsonify(examples), 200


@bp.route("/quick-actions", methods=["GET"])
def get_quick_actions():
    """
    Get predefined quick action searches

    Returns:
        200: List of quick action buttons
    """
    actions = {
        "success": True,
        "quick_actions": [
            {
                "id": "hot_leads_today",
                "label": "🔥 Hot Leads Today",
                "query": "Show me all hot leads created today",
                "color": "red"
            },
            {
                "id": "new_leads_week",
                "label": "📬 New Leads This Week",
                "query": "Find all new leads from this week",
                "color": "blue"
            },
            {
                "id": "active_projects",
                "label": "🏗️ Active Projects",
                "query": "Show all active projects",
                "color": "orange"
            },
            {
                "id": "today_appointments",
                "label": "📅 Today's Appointments",
                "query": "Show appointments for today",
                "color": "green"
            },
            {
                "id": "negative_sentiment_calls",
                "label": "⚠️ Negative Sentiment Calls",
                "query": "Find calls with negative sentiment from this week",
                "color": "yellow"
            },
            {
                "id": "premium_customers",
                "label": "⭐ Premium Customers",
                "query": "Show all premium tier customers",
                "color": "purple"
            },
            {
                "id": "follow_up_needed",
                "label": "🔔 Follow-ups Needed",
                "query": "Find leads that need follow-up",
                "color": "pink"
            },
            {
                "id": "high_value_opportunities",
                "label": "💰 High Value Opportunities",
                "query": "Show leads and projects with high values",
                "color": "gold"
            }
        ]
    }

    return jsonify(actions), 200


@bp.route("/health", methods=["GET"])
def ai_search_health():
    """Health check for AI search service"""
    try:
        from app.services.call_transcription import get_openai_client
        has_openai = get_openai_client() is not None

        return jsonify({
            "status": "healthy",
            "service": "ai-search",
            "openai_configured": has_openai,
            "model": "gpt-4o",
            "features": [
                "natural_language_search",
                "query_suggestions",
                "intent_analysis",
                "multi_entity_search"
            ]
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "service": "ai-search",
            "error": str(e)
        }), 503


def _generate_suggestions(partial: str, limit: int) -> List[str]:
    """Generate search query suggestions"""
    partial_lower = partial.lower()

    # Common search patterns
    patterns = [
        # Leads
        "Show me all hot leads from this week",
        "Find new leads that haven't been contacted",
        "Get qualified leads with high scores",
        "List all leads from Google Ads",
        "Show leads created today",
        "Find leads in Bloomfield Hills",

        # Customers
        "Find all premium tier customers",
        "Show customers with projects over $50k",
        "List recent customers from this month",
        "Get customers who need follow-up",

        # Projects
        "Show active projects",
        "Find projects starting this week",
        "List completed projects from last month",
        "Get high-value projects over $100k",

        # Voice Calls
        "Find calls with negative sentiment",
        "Show today's voice interactions",
        "List calls that were escalated",
        "Get calls with appointments scheduled",

        # Appointments
        "Show appointments for today",
        "Find scheduled inspections this week",
        "List upcoming appointments",
        "Get appointments that need confirmation"
    ]

    # Filter patterns that match partial query
    suggestions = [
        pattern for pattern in patterns
        if partial_lower in pattern.lower()
    ]

    return suggestions[:limit]
