"""
iSwitch Roofs CRM - Interactions API Routes
Version: 1.0.0

Complete interaction management API for tracking all customer and lead communications
including calls, emails, meetings, and notes with follow-up management.
"""

import logging
from datetime import datetime

from flask import Blueprint, g, jsonify, request

from app.services.interaction_service import interaction_service
from app.services.realtime_service import realtime_service
from app.utils.auth import require_auth
from app.utils.supabase_client import get_supabase_client
from app.utils.validation import validate_request, validate_uuid
from app.schemas.interaction import InteractionCreate, InteractionUpdate

bp = Blueprint("interactions", __name__)
logger = logging.getLogger(__name__)


@bp.route("/", methods=["GET"])
@require_auth
def list_interactions():
    """
    List all interactions with filtering and pagination.

    Query Parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 50, max: 100)
        - customer_id: Filter by customer
        - lead_id: Filter by lead
        - interaction_type: Filter by type (phone_call, email, meeting, note, sms)
        - direction: Filter by direction (inbound, outbound)
        - status: Filter by status
        - assigned_to: Filter by assigned user
        - follow_up_required: Filter pending follow-ups (true/false)
        - start_date: Filter interactions after this date
        - end_date: Filter interactions before this date
        - sort: Sort field and direction (field:asc/desc)

    Returns:
        JSON response with interactions list and pagination
    """
    try:
        from app.utils.database import get_db_session
        from app.utils.pagination import paginate_query, create_pagination_response
        from sqlalchemy import and_
        from sqlalchemy.orm import joinedload
        from app.models.interaction_sqlalchemy import Interaction
        from app.models.customer_sqlalchemy import Customer
        from app.models.lead_sqlalchemy import Lead

        # Pagination
        page = int(request.args.get("page", 1))
        limit = min(int(request.args.get("limit", 50)), 100)
        per_page = limit  # For compatibility

        # Build SQLAlchemy query with eager loading
        db = get_db_session()
        query = db.query(Interaction).filter(Interaction.is_deleted == False)

        # Apply filters
        filters = []

        if customer_id := request.args.get("customer_id"):
            filters.append(Interaction.customer_id == customer_id)

        if lead_id := request.args.get("lead_id"):
            filters.append(Interaction.lead_id == lead_id)

        if interaction_type := request.args.get("interaction_type"):
            filters.append(Interaction.interaction_type == interaction_type)

        if direction := request.args.get("direction"):
            filters.append(Interaction.direction == direction)

        if status := request.args.get("status"):
            filters.append(Interaction.outcome == status)

        if assigned_to := request.args.get("assigned_to"):
            filters.append(Interaction.assigned_to == assigned_to)

        if follow_up := request.args.get("follow_up_required"):
            filters.append(Interaction.follow_up_required == (follow_up.lower() == "true"))

        # Date range filters
        if start_date := request.args.get("start_date"):
            filters.append(Interaction.interaction_time >= start_date)

        if end_date := request.args.get("end_date"):
            filters.append(Interaction.interaction_time <= end_date)

        if filters:
            query = query.filter(and_(*filters))

        # Sorting
        sort_field = "interaction_time"
        sort_dir = "desc"
        if sort := request.args.get("sort"):
            parts = sort.split(":")
            sort_field = parts[0]
            sort_dir = parts[1] if len(parts) > 1 else "asc"

        if hasattr(Interaction, sort_field):
            order_column = getattr(Interaction, sort_field)
            if sort_dir == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())

        # Get paginated results
        interactions, total = paginate_query(query, page=page, per_page=per_page)

        # Convert to dicts and enrich with customer/lead names
        interactions_data = []
        for interaction in interactions:
            interaction_dict = {
                "id": str(interaction.id),
                "customer_id": str(interaction.customer_id) if interaction.customer_id else None,
                "lead_id": str(interaction.lead_id) if interaction.lead_id else None,
                "interaction_type": interaction.interaction_type.value if interaction.interaction_type else None,
                "direction": interaction.direction.value if interaction.direction else None,
                "outcome": interaction.outcome.value if interaction.outcome else None,
                "subject": interaction.subject,
                "notes": interaction.notes,
                "interaction_time": interaction.interaction_time.isoformat() if interaction.interaction_time else None,
                "duration_minutes": interaction.duration_minutes,
                "follow_up_required": interaction.follow_up_required,
                "follow_up_date": interaction.follow_up_date.isoformat() if interaction.follow_up_date else None,
                "assigned_to": str(interaction.assigned_to) if interaction.assigned_to else None,
                "created_at": interaction.created_at.isoformat() if interaction.created_at else None,
                "updated_at": interaction.updated_at.isoformat() if interaction.updated_at else None,
            }

            # Enrich with customer/lead names
            if interaction.customer_id:
                customer = db.query(Customer).filter(Customer.id == interaction.customer_id).first()
                if customer:
                    interaction_dict["entity_name"] = f"{customer.first_name} {customer.last_name}"
                    interaction_dict["entity_type"] = "customer"
            elif interaction.lead_id:
                lead = db.query(Lead).filter(Lead.id == interaction.lead_id).first()
                if lead:
                    interaction_dict["entity_name"] = f"{lead.first_name} {lead.last_name}"
                    interaction_dict["entity_type"] = "lead"

            interactions_data.append(interaction_dict)

        # Create pagination response
        response = create_pagination_response(
            items=interactions_data,
            total=total,
            page=page,
            per_page=per_page
        )

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error listing interactions: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to list interactions"}), 500


@bp.route("/<interaction_id>", methods=["GET"])
@require_auth
def get_interaction(interaction_id: str):
    """
    Get interaction by ID.

    Path Parameters:
        - interaction_id: Interaction UUID

    Returns:
        JSON response with interaction details
    """
    try:
        if not validate_uuid(interaction_id):
            return jsonify({"error": "Invalid interaction ID format"}), 400

        from app.utils.database import get_db_session
        from app.models.interaction_sqlalchemy import Interaction
        from app.models.customer_sqlalchemy import Customer
        from app.models.lead_sqlalchemy import Lead

        db = get_db_session()

        # Get interaction
        interaction = db.query(Interaction).filter(
            Interaction.id == interaction_id,
            Interaction.is_deleted == False
        ).first()

        if not interaction:
            return jsonify({"error": "Interaction not found"}), 404

        # Convert to dict
        interaction_dict = {
            "id": str(interaction.id),
            "customer_id": str(interaction.customer_id) if interaction.customer_id else None,
            "lead_id": str(interaction.lead_id) if interaction.lead_id else None,
            "interaction_type": interaction.interaction_type.value if interaction.interaction_type else None,
            "direction": interaction.direction.value if interaction.direction else None,
            "outcome": interaction.outcome.value if interaction.outcome else None,
            "subject": interaction.subject,
            "notes": interaction.notes,
            "interaction_time": interaction.interaction_time.isoformat() if interaction.interaction_time else None,
            "duration_minutes": interaction.duration_minutes,
            "follow_up_required": interaction.follow_up_required,
            "follow_up_date": interaction.follow_up_date.isoformat() if interaction.follow_up_date else None,
            "assigned_to": str(interaction.assigned_to) if interaction.assigned_to else None,
            "created_by": str(interaction.created_by) if interaction.created_by else None,
            "created_at": interaction.created_at.isoformat() if interaction.created_at else None,
            "updated_at": interaction.updated_at.isoformat() if interaction.updated_at else None,
        }

        # Get related entity details
        if interaction.customer_id:
            customer = db.query(Customer).filter(Customer.id == interaction.customer_id).first()
            if customer:
                interaction_dict["customer"] = {
                    "id": str(customer.id),
                    "first_name": customer.first_name,
                    "last_name": customer.last_name,
                    "email": customer.email,
                    "phone": customer.phone,
                }
        elif interaction.lead_id:
            lead = db.query(Lead).filter(Lead.id == interaction.lead_id).first()
            if lead:
                interaction_dict["lead"] = {
                    "id": str(lead.id),
                    "first_name": lead.first_name,
                    "last_name": lead.last_name,
                    "email": lead.email,
                    "phone": lead.phone,
                }

        return jsonify(interaction_dict), 200

    except Exception as e:
        logger.error(f"Error getting interaction: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to get interaction"}), 500


@bp.route("/", methods=["POST"])
@require_auth
@validate_request(InteractionCreate)
def create_interaction():
    """
    Create a new interaction.

    Request Body:
        - InteractionCreate model fields

    Returns:
        JSON response with created interaction
    """
    try:
        interaction_data = InteractionCreate(**request.validated_data)
        user_id = g.user_id

        # Validate that either customer_id or lead_id is provided
        if not interaction_data.customer_id and not interaction_data.lead_id:
            return jsonify({"error": "Either customer_id or lead_id must be provided"}), 400

        success, interaction, error = interaction_service.create_interaction(
            interaction_data, user_id
        )

        if success:
            # Broadcast real-time event
            realtime_service.trigger_event(
                channel="interactions",
                event="interaction-created",
                data={"interaction": interaction},
            )

            # Also notify the assigned user if different from creator
            if interaction.get("assigned_to") and interaction["assigned_to"] != user_id:
                realtime_service.trigger_event(
                    channel=f'private-user-{interaction["assigned_to"]}',
                    event="new-interaction",
                    data={"interaction": interaction},
                )

            return jsonify(interaction), 201
        else:
            return jsonify({"error": error or "Failed to create interaction"}), 400

    except Exception as e:
        logger.error(f"Error creating interaction: {str(e)}")
        return jsonify({"error": "Failed to create interaction"}), 500


@bp.route("/<interaction_id>", methods=["PUT", "PATCH"])
@require_auth
def update_interaction(interaction_id: str):
    """
    Update an existing interaction.

    Path Parameters:
        - interaction_id: Interaction UUID

    Request Body:
        - InteractionUpdate model fields (partial update supported)

    Returns:
        JSON response with updated interaction
    """
    try:
        if not validate_uuid(interaction_id):
            return jsonify({"error": "Invalid interaction ID format"}), 400

        data = request.get_json()
        if not data:
            return jsonify({"error": "No update data provided"}), 400

        update_data = InteractionUpdate(**data)
        user_id = g.user_id

        success, interaction, error = interaction_service.update_interaction(
            interaction_id, update_data, user_id
        )

        if success:
            # Broadcast real-time event
            realtime_service.trigger_event(
                channel="interactions",
                event="interaction-updated",
                data={"interaction": interaction},
            )

            return jsonify(interaction), 200
        else:
            if error == "Interaction not found":
                return jsonify({"error": error}), 404
            return jsonify({"error": error or "Failed to update interaction"}), 400

    except Exception as e:
        logger.error(f"Error updating interaction: {str(e)}")
        return jsonify({"error": "Failed to update interaction"}), 500


@bp.route("/<interaction_id>", methods=["DELETE"])
@require_auth
def delete_interaction(interaction_id: str):
    """
    Delete an interaction (soft delete).

    Path Parameters:
        - interaction_id: Interaction UUID

    Returns:
        JSON response with success message
    """
    try:
        if not validate_uuid(interaction_id):
            return jsonify({"error": "Invalid interaction ID format"}), 400

        supabase = get_supabase_client()

        # Check if interaction exists
        result = supabase.from_("interactions").select("id").eq("id", interaction_id).execute()

        if not result.data:
            return jsonify({"error": "Interaction not found"}), 404

        # Soft delete
        update_result = (
            supabase.from_("interactions")
            .update({"deleted_at": datetime.utcnow().isoformat(), "deleted_by": g.user_id})
            .eq("id", interaction_id)
            .execute()
        )

        if update_result.data:
            # Broadcast real-time event
            realtime_service.trigger_event(
                channel="interactions",
                event="interaction-deleted",
                data={"interaction_id": interaction_id},
            )

            return jsonify({"message": "Interaction deleted successfully"}), 200

        return jsonify({"error": "Failed to delete interaction"}), 500

    except Exception as e:
        logger.error(f"Error deleting interaction: {str(e)}")
        return jsonify({"error": "Failed to delete interaction"}), 500


@bp.route("/timeline/<entity_type>/<entity_id>", methods=["GET"])
@require_auth
def get_interaction_timeline(entity_type: str, entity_id: str):
    """
    Get interaction timeline for a lead or customer.

    Path Parameters:
        - entity_type: 'lead' or 'customer'
        - entity_id: Entity UUID

    Query Parameters:
        - limit: Maximum number of interactions (default: 50)

    Returns:
        JSON response with interaction timeline
    """
    try:
        if entity_type not in ["lead", "customer"]:
            return jsonify({"error": 'Invalid entity type. Must be "lead" or "customer"'}), 400

        if not validate_uuid(entity_id):
            return jsonify({"error": "Invalid entity ID format"}), 400

        limit = int(request.args.get("limit", 50))

        # Get interaction history
        interactions = interaction_service.get_interaction_history(entity_id, entity_type, limit)

        # Get communication summary
        summary = interaction_service.get_communication_summary(entity_id, entity_type)

        response = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "summary": summary,
            "timeline": interactions,
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error getting interaction timeline: {str(e)}")
        return jsonify({"error": "Failed to get timeline"}), 500


@bp.route("/<interaction_id>/transcription", methods=["POST"])
@require_auth
def add_transcription(interaction_id: str):
    """
    Add transcription to a call interaction.

    Path Parameters:
        - interaction_id: Interaction UUID

    Request Body:
        - transcription: Transcribed text
        - keywords: Optional list of keywords
        - sentiment: Optional sentiment analysis

    Returns:
        JSON response with updated interaction
    """
    try:
        if not validate_uuid(interaction_id):
            return jsonify({"error": "Invalid interaction ID format"}), 400

        data = request.get_json()
        if not data or "transcription" not in data:
            return jsonify({"error": "Transcription text is required"}), 400

        supabase = get_supabase_client()

        # Get interaction
        result = supabase.from_("interactions").select("*").eq("id", interaction_id).execute()
        if not result.data:
            return jsonify({"error": "Interaction not found"}), 404

        interaction = result.data[0]

        # Update with transcription
        update_data = {
            "transcription": data["transcription"],
            "metadata": {
                **interaction.get("metadata", {}),
                "keywords": data.get("keywords", []),
                "sentiment": data.get("sentiment"),
                "transcribed_at": datetime.utcnow().isoformat(),
            },
            "updated_at": datetime.utcnow().isoformat(),
        }

        update_result = (
            supabase.from_("interactions").update(update_data).eq("id", interaction_id).execute()
        )

        if update_result.data:
            return jsonify(update_result.data[0]), 200

        return jsonify({"error": "Failed to add transcription"}), 500

    except Exception as e:
        logger.error(f"Error adding transcription: {str(e)}")
        return jsonify({"error": "Failed to add transcription"}), 500


@bp.route("/follow-ups/pending", methods=["GET"])
@require_auth
def get_pending_follow_ups():
    """
    Get pending follow-ups for the current user or all users.

    Query Parameters:
        - assigned_to: Filter by assigned user (admin only)
        - days_ahead: Number of days to look ahead (default: 7)

    Returns:
        JSON response with pending follow-ups
    """
    try:
        # Check if user is admin for viewing all follow-ups
        assigned_to = request.args.get("assigned_to")
        if not assigned_to or g.user_role != "admin":
            assigned_to = g.user_id

        days_ahead = int(request.args.get("days_ahead", 7))

        # Get pending follow-ups
        follow_ups = interaction_service.get_pending_follow_ups(assigned_to, days_ahead)

        # Group by date
        by_date = {}
        for follow_up in follow_ups:
            date = follow_up["follow_up_date"].split("T")[0]
            if date not in by_date:
                by_date[date] = []
            by_date[date].append(follow_up)

        response = {"total": len(follow_ups), "by_date": by_date, "follow_ups": follow_ups}

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error getting pending follow-ups: {str(e)}")
        return jsonify({"error": "Failed to get follow-ups"}), 500


@bp.route("/<interaction_id>/complete-follow-up", methods=["POST"])
@require_auth
def complete_follow_up(interaction_id: str):
    """
    Mark a follow-up as complete.

    Path Parameters:
        - interaction_id: Interaction UUID

    Request Body:
        - notes: Completion notes

    Returns:
        JSON response with success message
    """
    try:
        if not validate_uuid(interaction_id):
            return jsonify({"error": "Invalid interaction ID format"}), 400

        data = request.get_json()
        notes = data.get("notes") if data else None

        success, error = interaction_service.mark_follow_up_complete(interaction_id, notes)

        if success:
            # Broadcast real-time event
            realtime_service.trigger_event(
                channel="interactions",
                event="follow-up-completed",
                data={"interaction_id": interaction_id},
            )

            return jsonify({"message": "Follow-up marked as complete"}), 200
        else:
            return jsonify({"error": error or "Failed to complete follow-up"}), 400

    except Exception as e:
        logger.error(f"Error completing follow-up: {str(e)}")
        return jsonify({"error": "Failed to complete follow-up"}), 500


@bp.route("/analytics", methods=["GET"])
@require_auth
def get_interaction_analytics():
    """
    Get interaction analytics for a date range.

    Query Parameters:
        - start_date: Start date (required)
        - end_date: End date (required)
        - assigned_to: Filter by assigned user

    Returns:
        JSON response with analytics data
    """
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        if not start_date or not end_date:
            return jsonify({"error": "Start date and end date are required"}), 400

        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)

        assigned_to = request.args.get("assigned_to")

        # Get analytics
        analytics = interaction_service.get_interaction_analytics(start, end, assigned_to)

        return jsonify(analytics), 200

    except Exception as e:
        logger.error(f"Error getting interaction analytics: {str(e)}")
        return jsonify({"error": "Failed to get analytics"}), 500


@bp.route("/templates", methods=["GET"])
@require_auth
def get_interaction_templates():
    """
    Get interaction templates for quick logging.

    Query Parameters:
        - interaction_type: Filter by type

    Returns:
        JSON response with templates
    """
    try:
        interaction_type = request.args.get("interaction_type")

        templates = interaction_service.get_interaction_templates(interaction_type)

        return jsonify({"data": templates}), 200

    except Exception as e:
        logger.error(f"Error getting templates: {str(e)}")
        return jsonify({"error": "Failed to get templates"}), 500


@bp.route("/auto-log", methods=["POST"])
@require_auth
def auto_log_interaction():
    """
    Automatically log an interaction from system events.

    Request Body:
        - interaction_type: Type of interaction
        - entity_id: Customer or Lead ID
        - entity_type: 'customer' or 'lead'
        - summary: Brief summary
        - notes: Optional notes
        - metadata: Optional metadata

    Returns:
        JSON response with created interaction
    """
    try:
        data = request.get_json()

        required_fields = ["interaction_type", "entity_id", "entity_type"]
        if not data or not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        if data["entity_type"] not in ["customer", "lead"]:
            return jsonify({"error": "Invalid entity type"}), 400

        details = {
            "summary": data.get("summary", f'Auto-logged {data["interaction_type"]}'),
            "notes": data.get("notes"),
            "metadata": data.get("metadata", {}),
            "assigned_to": g.user_id,
        }

        success, interaction, error = interaction_service.auto_log_interaction(
            data["interaction_type"], data["entity_id"], data["entity_type"], details
        )

        if success:
            return jsonify(interaction), 201
        else:
            return jsonify({"error": error or "Failed to log interaction"}), 400

    except Exception as e:
        logger.error(f"Error auto-logging interaction: {str(e)}")
        return jsonify({"error": "Failed to log interaction"}), 500
