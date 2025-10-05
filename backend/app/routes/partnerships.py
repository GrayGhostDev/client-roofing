"""
Partnerships API Routes

Endpoints for partner relationship management:
- Partner onboarding and management
- Referral tracking
- Commission processing
- Partner portal access
"""

import logging
from datetime import datetime

from flask import Blueprint, jsonify, request

# Local imports
from app.services.partnerships_service import partnerships_service
from app.utils.decorators import require_auth, require_roles
from app.utils.validators import validate_request

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint (module exports alias `bp` for app factory consistency)
partnerships_bp = Blueprint("partnerships", __name__, url_prefix="/api/partnerships")
# Alias expected by app.register_blueprint(...)
bp = partnerships_bp


@partnerships_bp.route("/", methods=["GET"])
@require_auth
@require_roles(["admin", "manager"])
def list_partners():
    """
    List all partners with filtering

    Query Parameters:
        - status: Filter by status (active, inactive, pending_approval)
        - category: Filter by category (insurance_agent, real_estate_agent, etc.)
        - tier: Filter by tier (bronze, silver, gold, platinum)
        - limit: Number of results (default 50)
        - offset: Skip results (default 0)

    Returns:
        - 200: Partners list retrieved
        - 500: Server error
    """
    try:
        # Get query parameters
        status = request.args.get("status")
        category = request.args.get("category")
        tier = request.args.get("tier")
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))

        # Build query
        query = partnerships_service.supabase.client.table("partners").select("*")

        if status:
            query = query.eq("status", status)
        if category:
            query = query.eq("category", category)
        if tier:
            query = query.eq("tier", tier)

        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

        result = query.execute()

        # Get metrics for each partner
        partners_with_metrics = []
        for partner in result.data:
            metrics = partnerships_service._calculate_partner_metrics(partner["id"])
            partner["metrics"] = metrics
            partners_with_metrics.append(partner)

        return (
            jsonify(
                {"success": True, "partners": partners_with_metrics, "total": len(result.data)}
            ),
            200,
        )

    except Exception as e:
        logger.error(f"List partners error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@partnerships_bp.route("/", methods=["POST"])
@require_auth
@require_roles(["admin"])
def create_partner():
    """
    Create a new partner

    Request Body:
        - company_name: Company name (required)
        - contact_name: Primary contact name (required)
        - email: Contact email (required)
        - phone: Contact phone (required)
        - category: Partner category (required)
        - address: Company address
        - website: Company website
        - license_number: Business license
        - tax_id: Tax identification
        - payment_method: Payment preference
        - password: Portal access password

    Returns:
        - 201: Partner created successfully
        - 400: Invalid request
        - 500: Server error
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["company_name", "contact_name", "email", "phone", "category"]
        errors = validate_request(data, required_fields)
        if errors:
            return jsonify({"success": False, "errors": errors}), 400

        # Create partner
        success, result, error = partnerships_service.create_partner(data)

        if success:
            # Log activity
            partnerships_service.supabase.client.table("activity_logs").insert(
                {
                    "user_id": request.user["id"],
                    "action": "partner_created",
                    "entity_type": "partner",
                    "entity_id": result["partner_id"],
                    "metadata": {
                        "company_name": data["company_name"],
                        "category": data["category"],
                    },
                    "created_at": datetime.utcnow().isoformat(),
                }
            ).execute()

            return jsonify({"success": True, "partner": result}), 201
        else:
            return jsonify({"success": False, "error": error or "Failed to create partner"}), 400

    except Exception as e:
        logger.error(f"Create partner error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@partnerships_bp.route("/<partner_id>", methods=["GET"])
@require_auth
def get_partner(partner_id):
    """
    Get partner details

    Args:
        partner_id: Partner UUID

    Returns:
        - 200: Partner details retrieved
        - 404: Partner not found
        - 500: Server error
    """
    try:
        success, partner, error = partnerships_service.get_partner(partner_id=partner_id)

        if success:
            return jsonify({"success": True, "partner": partner}), 200
        else:
            return jsonify({"success": False, "error": error or "Partner not found"}), 404

    except Exception as e:
        logger.error(f"Get partner error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@partnerships_bp.route("/<partner_id>", methods=["PUT"])
@require_auth
@require_roles(["admin", "manager"])
def update_partner(partner_id):
    """
    Update partner information

    Args:
        partner_id: Partner UUID

    Request Body:
        Any partner fields to update

    Returns:
        - 200: Partner updated successfully
        - 400: Invalid request
        - 404: Partner not found
        - 500: Server error
    """
    try:
        data = request.get_json()

        success, error = partnerships_service.update_partner(partner_id, data)

        if success:
            # Log activity
            partnerships_service.supabase.client.table("activity_logs").insert(
                {
                    "user_id": request.user["id"],
                    "action": "partner_updated",
                    "entity_type": "partner",
                    "entity_id": partner_id,
                    "metadata": {"updated_fields": list(data.keys())},
                    "created_at": datetime.utcnow().isoformat(),
                }
            ).execute()

            return jsonify({"success": True, "message": "Partner updated successfully"}), 200
        else:
            return jsonify({"success": False, "error": error or "Failed to update partner"}), 404

    except Exception as e:
        logger.error(f"Update partner error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@partnerships_bp.route("/<partner_id>", methods=["DELETE"])
@require_auth
@require_roles(["admin"])
def deactivate_partner(partner_id):
    """
    Deactivate a partner

    Args:
        partner_id: Partner UUID

    Returns:
        - 200: Partner deactivated
        - 404: Partner not found
        - 500: Server error
    """
    try:
        success, error = partnerships_service.update_partner(
            partner_id, {"status": "inactive", "deactivated_at": datetime.utcnow().isoformat()}
        )

        if success:
            return jsonify({"success": True, "message": "Partner deactivated successfully"}), 200
        else:
            return jsonify({"success": False, "error": error or "Partner not found"}), 404

    except Exception as e:
        logger.error(f"Deactivate partner error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@partnerships_bp.route("/referrals", methods=["GET"])
@require_auth
def list_referrals():
    """
    List referrals with filtering

    Query Parameters:
        - partner_id: Filter by partner
        - status: Filter by status
        - date_from: Start date
        - date_to: End date
        - limit: Number of results
        - offset: Skip results

    Returns:
        - 200: Referrals list retrieved
        - 500: Server error
    """
    try:
        # Get query parameters
        partner_id = request.args.get("partner_id")
        status = request.args.get("status")
        date_from = request.args.get("date_from")
        date_to = request.args.get("date_to")
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))

        # Build query
        query = partnerships_service.supabase.client.table("referrals").select("*")

        if partner_id:
            query = query.eq("partner_id", partner_id)
        if status:
            query = query.eq("status", status)
        if date_from:
            query = query.gte("created_at", date_from)
        if date_to:
            query = query.lte("created_at", date_to)

        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

        result = query.execute()

        return jsonify({"success": True, "referrals": result.data, "total": len(result.data)}), 200

    except Exception as e:
        logger.error(f"List referrals error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@partnerships_bp.route("/<partner_id>/referrals", methods=["GET"])
@require_auth
@require_roles(["admin", "manager", "sales"])
def get_partner_referrals(partner_id: str):
    """
    Get referral history for a specific partner (convenience endpoint).

    Query Parameters (optional):
        - status, date_from, date_to, limit, offset
    """
    try:
        status = request.args.get("status")
        date_from = request.args.get("date_from")
        date_to = request.args.get("date_to")
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))

        query = partnerships_service.supabase.client.table("referrals").select("*")
        query = query.eq("partner_id", partner_id)
        if status:
            query = query.eq("status", status)
        if date_from:
            query = query.gte("created_at", date_from)
        if date_to:
            query = query.lte("created_at", date_to)

        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        result = query.execute()
        return jsonify({"success": True, "referrals": result.data, "total": len(result.data)}), 200
    except Exception as e:
        logger.error(f"Get partner referrals error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@partnerships_bp.route("/<partner_id>/referral", methods=["POST"])
@require_auth
@require_roles(["admin", "manager", "sales"])
def create_partner_referral(partner_id: str):
    """
    Log a referral for a specific partner (convenience endpoint).
    """
    try:
        data = request.get_json() or {}
        data["partner_id"] = partner_id

        # Validate and create
        required_fields = ["partner_id", "customer_name", "customer_email", "customer_phone"]
        errors = validate_request(data, required_fields)
        if errors:
            return jsonify({"success": False, "errors": errors}), 400

        success, result, error = partnerships_service.create_referral(data)
        if success:
            return jsonify({"success": True, "referral": result}), 201
        else:
            return jsonify({"success": False, "error": error or "Failed to create referral"}), 400
    except Exception as e:
        logger.error(f"Create partner referral error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@partnerships_bp.route("/<partner_id>/commission", methods=["GET"])
@require_auth
@require_roles(["admin", "manager", "finance"])
def get_partner_commission(partner_id: str):
    """
    Calculate and return commission metrics for a specific partner.
    """
    try:
        # Leverage existing metrics calculator
        metrics = partnerships_service._calculate_partner_metrics(partner_id)
        if not metrics:
            return jsonify({"success": False, "error": "Partner not found or no data"}), 404

        return jsonify({"success": True, "commission": {
            "total_commission": metrics.get("total_commission", 0),
            "pending_commission": metrics.get("pending_commission", 0),
            "total_revenue": metrics.get("total_revenue", 0),
            "completed_referrals": metrics.get("completed_referrals", 0),
            "won_referrals": metrics.get("won_referrals", 0),
        }}), 200
    except Exception as e:
        logger.error(f"Get partner commission error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@partnerships_bp.route("/referrals", methods=["POST"])
@require_auth
def create_referral():
    """
    Create a new referral

    Request Body:
        - partner_id: Partner UUID (required)
        - customer_name: Customer name (required)
        - customer_email: Customer email (required)
        - customer_phone: Customer phone (required)
        - customer_address: Customer address
        - service_type: Service requested
        - urgency: Urgency level
        - notes: Additional notes

    Returns:
        - 201: Referral created successfully
        - 400: Invalid request
        - 500: Server error
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["partner_id", "customer_name", "customer_email", "customer_phone"]
        errors = validate_request(data, required_fields)
        if errors:
            return jsonify({"success": False, "errors": errors}), 400

        # Create referral
        success, result, error = partnerships_service.create_referral(data)

        if success:
            return jsonify({"success": True, "referral": result}), 201
        else:
            return jsonify({"success": False, "error": error or "Failed to create referral"}), 400

    except Exception as e:
        logger.error(f"Create referral error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@partnerships_bp.route("/referrals/<referral_id>/status", methods=["PUT"])
@require_auth
@require_roles(["admin", "manager", "sales"])
def update_referral_status(referral_id):
    """
    Update referral status

    Args:
        referral_id: Referral UUID

    Request Body:
        - status: New status (required)
        - project_value: Project value for won/completed status

    Returns:
        - 200: Status updated successfully
        - 400: Invalid request
        - 404: Referral not found
        - 500: Server error
    """
    try:
        data = request.get_json()
        status = data.get("status")
        project_value = data.get("project_value")

        if not status:
            return jsonify({"success": False, "error": "status is required"}), 400

        success, error = partnerships_service.update_referral_status(
            referral_id, status, project_value
        )

        if success:
            return (
                jsonify({"success": True, "message": "Referral status updated successfully"}),
                200,
            )
        else:
            return jsonify({"success": False, "error": error or "Failed to update referral"}), 400

    except Exception as e:
        logger.error(f"Update referral status error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@partnerships_bp.route("/commission/process", methods=["POST"])
@require_auth
@require_roles(["admin", "finance"])
def process_commission():
    """
    Process commission payment for partner

    Request Body:
        - partner_id: Partner UUID (required)
        - referral_ids: List of referral IDs to process

    Returns:
        - 200: Commission processed successfully
        - 400: Invalid request
        - 500: Server error
    """
    try:
        data = request.get_json()
        partner_id = data.get("partner_id")
        referral_ids = data.get("referral_ids")

        if not partner_id:
            return jsonify({"success": False, "error": "partner_id is required"}), 400

        success, result, error = partnerships_service.process_commission_payment(
            partner_id, referral_ids
        )

        if success:
            return jsonify({"success": True, "payment": result}), 200
        else:
            return (
                jsonify({"success": False, "error": error or "Failed to process commission"}),
                400,
            )

    except Exception as e:
        logger.error(f"Process commission error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@partnerships_bp.route("/commission/<payment_id>/complete", methods=["PUT"])
@require_auth
@require_roles(["admin", "finance"])
def complete_payment(payment_id):
    """
    Mark commission payment as complete

    Args:
        payment_id: Payment UUID

    Request Body:
        - transaction_id: Payment transaction ID

    Returns:
        - 200: Payment marked as complete
        - 404: Payment not found
        - 500: Server error
    """
    try:
        data = request.get_json()
        transaction_id = data.get("transaction_id")

        success, error = partnerships_service.mark_payment_complete(payment_id, transaction_id)

        if success:
            return jsonify({"success": True, "message": "Payment marked as complete"}), 200
        else:
            return jsonify({"success": False, "error": error or "Payment not found"}), 404

    except Exception as e:
        logger.error(f"Complete payment error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@partnerships_bp.route("/portal/auth", methods=["POST"])
def partner_portal_login():
    """
    Partner portal authentication

    Request Body:
        - email: Partner email (required)
        - password: Partner password (required)

    Returns:
        - 200: Authentication successful
        - 401: Invalid credentials
        - 500: Server error
    """
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"success": False, "error": "Email and password are required"}), 400

        success, result, error = partnerships_service.authenticate_partner(email, password)

        if success:
            return jsonify({"success": True, "data": result}), 200
        else:
            return jsonify({"success": False, "error": error or "Invalid credentials"}), 401

    except Exception as e:
        logger.error(f"Partner portal login error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@partnerships_bp.route("/portal/validate", methods=["POST"])
def validate_portal_session():
    """
    Validate partner portal session

    Request Body:
        - session_token: Session token (required)

    Returns:
        - 200: Session valid
        - 401: Invalid or expired session
        - 500: Server error
    """
    try:
        data = request.get_json()
        session_token = data.get("session_token")

        if not session_token:
            return jsonify({"success": False, "error": "session_token is required"}), 400

        success, partner, error = partnerships_service.validate_partner_session(session_token)

        if success:
            return jsonify({"success": True, "partner": partner}), 200
        else:
            return jsonify({"success": False, "error": error or "Invalid session"}), 401

    except Exception as e:
        logger.error(f"Validate session error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@partnerships_bp.route("/portal/dashboard/<partner_id>", methods=["GET"])
def get_partner_dashboard(partner_id):
    """
    Get partner dashboard data

    Args:
        partner_id: Partner UUID

    Headers:
        - Authorization: Bearer {session_token}

    Returns:
        - 200: Dashboard data retrieved
        - 401: Unauthorized
        - 404: Partner not found
        - 500: Server error
    """
    try:
        # Validate session from header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "error": "Authorization required"}), 401

        session_token = auth_header.replace("Bearer ", "")
        valid, partner, error = partnerships_service.validate_partner_session(session_token)

        if not valid:
            return jsonify({"success": False, "error": "Invalid session"}), 401

        # Verify partner accessing own dashboard
        if partner["id"] != partner_id:
            return jsonify({"success": False, "error": "Unauthorized access"}), 403

        # Get dashboard data
        success, dashboard, error = partnerships_service.get_partner_dashboard(partner_id)

        if success:
            return jsonify({"success": True, "dashboard": dashboard}), 200
        else:
            return jsonify({"success": False, "error": error or "Dashboard not available"}), 404

    except Exception as e:
        logger.error(f"Get partner dashboard error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@partnerships_bp.route("/analytics", methods=["GET"])
@require_auth
@require_roles(["admin", "manager"])
def get_partnerships_analytics():
    """
    Get comprehensive partnership program analytics

    Returns:
        - 200: Analytics retrieved
        - 500: Server error
    """
    try:
        success, analytics, error = partnerships_service.get_partnerships_analytics()

        if success:
            return jsonify({"success": True, "analytics": analytics}), 200
        else:
            return (
                jsonify({"success": False, "error": error or "Failed to generate analytics"}),
                500,
            )

    except Exception as e:
        logger.error(f"Get analytics error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@partnerships_bp.route("/categories", methods=["GET"])
@require_auth
def get_partner_categories():
    """
    Get available partner categories and commission structures

    Returns:
        - 200: Categories retrieved
    """
    try:
        return (
            jsonify({"success": True, "categories": partnerships_service.partner_categories}),
            200,
        )

    except Exception as e:
        logger.error(f"Get categories error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


# Error handlers
@partnerships_bp.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Resource not found"}), 404


@partnerships_bp.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {error}")
    return jsonify({"success": False, "error": "Internal server error"}), 500
