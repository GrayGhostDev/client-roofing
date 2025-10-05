"""
Reviews API Routes

Endpoints for multi-platform review management:
- Fetch reviews from Google, Yelp, Facebook, BirdEye
- Review aggregation and metrics
- Sentiment analysis
- Response management
- Review campaigns
"""

import logging
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

# Local imports
from app.services.reviews_service import reviews_service
from app.utils.decorators import require_auth, require_roles
from app.utils.validators import validate_request

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
reviews_bp = Blueprint("reviews", __name__, url_prefix="/api/reviews")


@reviews_bp.route("/platforms/gmb/auth/init", methods=["POST"])
@require_auth
@require_roles(["admin", "manager"])
def init_gmb_auth():
    """
    Initialize Google My Business OAuth flow

    Returns:
        - 200: OAuth URL generated
        - 400: Invalid request
        - 500: Server error
    """
    try:
        data = request.get_json()
        redirect_uri = data.get("redirect_uri")

        if not redirect_uri:
            return jsonify({"success": False, "error": "redirect_uri is required"}), 400

        auth_url = reviews_service.init_gmb_oauth(redirect_uri)

        if auth_url:
            return jsonify({"success": True, "auth_url": auth_url}), 200
        else:
            return jsonify({"success": False, "error": "Failed to generate OAuth URL"}), 500

    except Exception as e:
        logger.error(f"GMB auth init error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@reviews_bp.route("/platforms/gmb/auth/callback", methods=["POST"])
@require_auth
@require_roles(["admin", "manager"])
def complete_gmb_auth():
    """
    Complete Google My Business OAuth flow

    Returns:
        - 200: OAuth completed successfully
        - 400: Invalid request
        - 500: Server error
    """
    try:
        data = request.get_json()
        auth_code = data.get("code")
        redirect_uri = data.get("redirect_uri")

        if not auth_code or not redirect_uri:
            return jsonify({"success": False, "error": "code and redirect_uri are required"}), 400

        success, error = reviews_service.complete_gmb_oauth(auth_code, redirect_uri)

        if success:
            return jsonify({"success": True, "message": "GMB authentication completed"}), 200
        else:
            return jsonify({"success": False, "error": error or "OAuth completion failed"}), 400

    except Exception as e:
        logger.error(f"GMB auth callback error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@reviews_bp.route("/fetch", methods=["POST"])
@require_auth
def fetch_reviews():
    """
    Fetch reviews from all configured platforms

    Returns:
        - 200: Reviews fetched successfully
        - 500: Server error
    """
    try:
        data = request.get_json() or {}
        refresh = data.get("refresh", False)

        success, result, error = reviews_service.fetch_all_reviews(refresh=refresh)

        if success:
            return jsonify({"success": True, "data": result}), 200
        else:
            return jsonify({"success": False, "error": error or "Failed to fetch reviews"}), 500

    except Exception as e:
        logger.error(f"Fetch reviews error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@reviews_bp.route("/platforms/<platform>/fetch", methods=["POST"])
@require_auth
def fetch_platform_reviews(platform):
    """
    Fetch reviews from a specific platform

    Args:
        platform: Platform name (google, yelp, facebook, birdeye)

    Returns:
        - 200: Reviews fetched successfully
        - 400: Invalid platform
        - 500: Server error
    """
    try:
        data = request.get_json() or {}

        if platform == "google":
            location_name = data.get("location_name")
            success, reviews, error = reviews_service.fetch_gmb_reviews(location_name)
        elif platform == "yelp":
            business_alias = data.get("business_alias")
            success, reviews, error = reviews_service.fetch_yelp_reviews(business_alias)
        elif platform == "facebook":
            success, reviews, error = reviews_service.fetch_facebook_reviews()
        elif platform == "birdeye":
            success, reviews, error = reviews_service.fetch_birdeye_reviews()
        else:
            return jsonify({"success": False, "error": f"Invalid platform: {platform}"}), 400

        if success:
            return jsonify({"success": True, "reviews": reviews}), 200
        else:
            return (
                jsonify(
                    {"success": False, "error": error or f"Failed to fetch {platform} reviews"}
                ),
                500,
            )

    except Exception as e:
        logger.error(f"Fetch {platform} reviews error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@reviews_bp.route("/<review_id>/analyze", methods=["GET"])
@require_auth
def analyze_review(review_id):
    """
    Analyze sentiment of a specific review

    Args:
        review_id: Review ID

    Returns:
        - 200: Analysis complete
        - 404: Review not found
        - 500: Server error
    """
    try:
        # Get review from database
        review = (
            reviews_service.supabase.client.table("reviews")
            .select("*")
            .eq("id", review_id)
            .single()
            .execute()
        )

        if not review.data:
            return jsonify({"success": False, "error": "Review not found"}), 404

        # Analyze sentiment
        sentiment = reviews_service.analyze_sentiment(review.data.get("comment", ""))

        # Update review with sentiment
        reviews_service.supabase.client.table("reviews").update(
            {"sentiment_score": sentiment["score"], "sentiment_label": sentiment["label"]}
        ).eq("id", review_id).execute()

        return jsonify({"success": True, "sentiment": sentiment}), 200

    except Exception as e:
        logger.error(f"Analyze review error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@reviews_bp.route("/<review_id>/response/suggest", methods=["GET"])
@require_auth
def suggest_response(review_id):
    """
    Generate suggested response for a review

    Args:
        review_id: Review ID

    Returns:
        - 200: Suggestion generated
        - 404: Review not found
        - 500: Server error
    """
    try:
        # Get review from database
        review = (
            reviews_service.supabase.client.table("reviews")
            .select("*")
            .eq("id", review_id)
            .single()
            .execute()
        )

        if not review.data:
            return jsonify({"success": False, "error": "Review not found"}), 404

        # Generate suggestion
        success, suggestion, error = reviews_service.generate_response_suggestion(review.data)

        if success:
            return jsonify({"success": True, "suggestion": suggestion}), 200
        else:
            return (
                jsonify({"success": False, "error": error or "Failed to generate suggestion"}),
                500,
            )

    except Exception as e:
        logger.error(f"Suggest response error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@reviews_bp.route("/<review_id>/response", methods=["POST"])
@require_auth
@require_roles(["admin", "manager"])
def post_response(review_id):
    """
    Post response to a review

    Args:
        review_id: Review ID

    Returns:
        - 200: Response posted successfully
        - 400: Invalid request
        - 404: Review not found
        - 500: Server error
    """
    try:
        data = request.get_json()
        response_text = data.get("response")

        if not response_text:
            return jsonify({"success": False, "error": "response text is required"}), 400

        # Get review from database
        review = (
            reviews_service.supabase.client.table("reviews")
            .select("*")
            .eq("id", review_id)
            .single()
            .execute()
        )

        if not review.data:
            return jsonify({"success": False, "error": "Review not found"}), 404

        # Post response
        platform = review.data.get("platform")
        platform_review_id = review.data.get("platform_review_id")

        success, error = reviews_service.post_review_response(
            platform_review_id, response_text, platform
        )

        if success:
            # Log activity
            reviews_service.supabase.client.table("activity_logs").insert(
                {
                    "user_id": request.user["id"],
                    "action": "review_response_posted",
                    "entity_type": "review",
                    "entity_id": review_id,
                    "metadata": {"platform": platform, "response_length": len(response_text)},
                    "created_at": datetime.utcnow().isoformat(),
                }
            ).execute()

            return jsonify({"success": True, "message": "Response posted successfully"}), 200
        else:
            return jsonify({"success": False, "error": error or "Failed to post response"}), 400

    except Exception as e:
        logger.error(f"Post response error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@reviews_bp.route("/campaigns", methods=["GET"])
@require_auth
def list_campaigns():
    """
    List review campaigns

    Returns:
        - 200: Campaigns retrieved
        - 500: Server error
    """
    try:
        # Get query parameters
        status = request.args.get("status")
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))

        # Build query
        query = reviews_service.supabase.client.table("review_campaigns").select("*")

        if status:
            query = query.eq("status", status)

        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

        result = query.execute()

        return jsonify({"success": True, "campaigns": result.data, "total": len(result.data)}), 200

    except Exception as e:
        logger.error(f"List campaigns error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@reviews_bp.route("/campaigns", methods=["POST"])
@require_auth
@require_roles(["admin", "manager"])
def create_campaign():
    """
    Create review request campaign

    Returns:
        - 201: Campaign created
        - 400: Invalid request
        - 500: Server error
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["customer_ids", "campaign_name"]
        errors = validate_request(data, required_fields)
        if errors:
            return jsonify({"success": False, "errors": errors}), 400

        customer_ids = data["customer_ids"]
        campaign_name = data["campaign_name"]
        template_id = data.get("template_id")

        # Create campaign
        success, result, error = reviews_service.create_review_campaign(
            customer_ids, campaign_name, template_id
        )

        if success:
            return jsonify({"success": True, "campaign": result}), 201
        else:
            return jsonify({"success": False, "error": error or "Failed to create campaign"}), 500

    except Exception as e:
        logger.error(f"Create campaign error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@reviews_bp.route("/request", methods=["POST"])
@require_auth
def send_review_request():
    """
    Send review request to customer

    Returns:
        - 200: Request sent
        - 400: Invalid request
        - 500: Server error
    """
    try:
        data = request.get_json()

        customer_id = data.get("customer_id")
        method = data.get("method", "email")

        if not customer_id:
            return jsonify({"success": False, "error": "customer_id is required"}), 400

        if method not in ["email", "sms"]:
            return jsonify({"success": False, "error": "Invalid method. Use email or sms"}), 400

        # Send request
        success, error = reviews_service.send_review_request(customer_id, method)

        if success:
            # Log activity
            reviews_service.supabase.client.table("activity_logs").insert(
                {
                    "user_id": request.user["id"],
                    "action": "review_request_sent",
                    "entity_type": "customer",
                    "entity_id": customer_id,
                    "metadata": {"method": method},
                    "created_at": datetime.utcnow().isoformat(),
                }
            ).execute()

            return jsonify({"success": True, "message": f"Review request sent via {method}"}), 200
        else:
            return jsonify({"success": False, "error": error or "Failed to send request"}), 500

    except Exception as e:
        logger.error(f"Send review request error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@reviews_bp.route("/metrics", methods=["GET"])
@require_auth
def get_review_metrics():
    """
    Get aggregated review metrics

    Returns:
        - 200: Metrics calculated
        - 500: Server error
    """
    try:
        # Fetch all reviews
        success, result, error = reviews_service.fetch_all_reviews(refresh=False)

        if success and result:
            metrics = result.get("metrics", {})
            return jsonify({"success": True, "metrics": metrics}), 200
        else:
            # Calculate from database
            reviews = reviews_service.supabase.client.table("reviews").select("*").execute()
            metrics = reviews_service.calculate_review_metrics(reviews.data)

            return jsonify({"success": True, "metrics": metrics}), 200

    except Exception as e:
        logger.error(f"Get metrics error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@reviews_bp.route("/insights", methods=["GET"])
@require_auth
def get_insights():
    """
    Get review insights and recommendations

    Returns:
        - 200: Insights generated
        - 500: Server error
    """
    try:
        days = int(request.args.get("days", 30))

        success, insights, error = reviews_service.get_review_insights(days)

        if success:
            return jsonify({"success": True, "insights": insights}), 200
        else:
            return jsonify({"success": False, "error": error or "Failed to generate insights"}), 500

    except Exception as e:
        logger.error(f"Get insights error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@reviews_bp.route("/alerts", methods=["GET"])
@require_auth
def get_review_alerts():
    """
    Get alerts for reviews needing attention

    Returns:
        - 200: Alerts retrieved
        - 500: Server error
    """
    try:
        alerts = []

        # Check for unanswered negative reviews
        negative_reviews = (
            reviews_service.supabase.client.table("reviews")
            .select("*")
            .lte("rating", 3)
            .is_("reply", None)
            .execute()
        )

        for review in negative_reviews.data:
            alerts.append(
                {
                    "type": "negative_review_unanswered",
                    "severity": "high",
                    "review_id": review["id"],
                    "platform": review.get("platform"),
                    "rating": review.get("rating"),
                    "created_at": review.get("created_at"),
                    "message": f"Negative {review.get('rating')}-star review needs response",
                }
            )

        # Check for old unanswered reviews
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        old_reviews = (
            reviews_service.supabase.client.table("reviews")
            .select("*")
            .is_("reply", None)
            .lte("created_at", week_ago)
            .execute()
        )

        for review in old_reviews.data:
            if review["id"] not in [a["review_id"] for a in alerts]:
                alerts.append(
                    {
                        "type": "old_review_unanswered",
                        "severity": "medium",
                        "review_id": review["id"],
                        "platform": review.get("platform"),
                        "rating": review.get("rating"),
                        "created_at": review.get("created_at"),
                        "message": "Review over 7 days old needs response",
                    }
                )

        return jsonify({"success": True, "alerts": alerts, "total": len(alerts)}), 200

    except Exception as e:
        logger.error(f"Get alerts error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@reviews_bp.route("/templates", methods=["GET"])
@require_auth
def get_response_templates():
    """
    Get review response templates

    Returns:
        - 200: Templates retrieved
        - 500: Server error
    """
    try:
        templates = (
            reviews_service.supabase.client.table("response_templates").select("*").execute()
        )

        return jsonify({"success": True, "templates": templates.data}), 200

    except Exception as e:
        logger.error(f"Get templates error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@reviews_bp.route("/templates", methods=["POST"])
@require_auth
@require_roles(["admin", "manager"])
def create_response_template():
    """
    Create review response template

    Returns:
        - 201: Template created
        - 400: Invalid request
        - 500: Server error
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["name", "template", "rating_range"]
        errors = validate_request(data, required_fields)
        if errors:
            return jsonify({"success": False, "errors": errors}), 400

        # Create template
        template = {
            "name": data["name"],
            "template": data["template"],
            "rating_range": data["rating_range"],
            "platform": data.get("platform"),
            "tags": data.get("tags", []),
            "created_by": request.user["id"],
            "created_at": datetime.utcnow().isoformat(),
        }

        result = (
            reviews_service.supabase.client.table("response_templates").insert(template).execute()
        )

        return jsonify({"success": True, "template": result.data[0]}), 201

    except Exception as e:
        logger.error(f"Create template error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


# Error handlers
@reviews_bp.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Resource not found"}), 404


@reviews_bp.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {error}")
    return jsonify({"success": False, "error": "Internal server error"}), 500
