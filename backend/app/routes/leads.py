"""
iSwitch Roofs CRM - Leads API Routes
Version: 1.0.0

Complete REST API for lead management with pagination, filtering, sorting,
and automatic lead scoring.
"""

import io
import json
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

import pandas as pd
from flask import Blueprint, jsonify, request

from app.config import get_supabase_client

# Database session and services
# SQLAlchemy model
from app.models.lead_sqlalchemy import Lead
from app.models.lead_sqlalchemy import LeadStatusEnum as LeadStatus

# Pydantic schemas
from app.schemas.lead import (
    LeadCreate,
    LeadListFilters,
    LeadListResponse,
    LeadUpdate,
)
from app.services.lead_scoring import lead_scoring_engine
from app.services.lead_service import lead_service
from app.utils.validators import validate_uuid

logger = logging.getLogger(__name__)
bp = Blueprint("leads", __name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_supabase():
    """Get Supabase client"""
    return get_supabase_client()


def parse_filters(params: dict[str, Any]) -> dict[str, Any]:
    """Parse query parameters into Supabase filters"""
    filters = {}

    # Status filter (comma-separated)
    if params.get("status"):
        statuses = params["status"].split(",")
        filters["status"] = {"in": statuses}

    # Temperature filter (comma-separated)
    if params.get("temperature"):
        temps = params["temperature"].split(",")
        filters["temperature"] = {"in": temps}

    # Source filter (comma-separated)
    if params.get("source"):
        sources = params["source"].split(",")
        filters["source"] = {"in": sources}

    # Assigned to
    if params.get("assigned_to"):
        filters["assigned_to"] = params["assigned_to"]

    # Created after
    if params.get("created_after"):
        filters["created_at"] = {"gte": params["created_after"]}

    # Score range
    if params.get("min_score"):
        filters["lead_score"] = {"gte": int(params["min_score"])}
    if params.get("max_score"):
        if "lead_score" not in filters:
            filters["lead_score"] = {}
        filters["lead_score"]["lte"] = int(params["max_score"])

    # ZIP code
    if params.get("zip_code"):
        filters["zip_code"] = params["zip_code"]

    # Converted
    if params.get("converted") is not None:
        filters["converted_to_customer"] = params["converted"] == "true"

    return filters


def apply_sorting(query, sort_param: str):
    """Apply sorting to Supabase query"""
    if ":" not in sort_param:
        sort_param = f"{sort_param}:desc"

    field, direction = sort_param.split(":")
    ascending = direction.lower() == "asc"

    return query.order(field, desc=not ascending)


# ============================================================================
# CRUD ENDPOINTS
# ============================================================================


@bp.route("/", methods=["GET"])
def get_leads():
    """
    Get all leads with filtering, pagination, and sorting.

    Query Parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 50, max: 100)
        - sort: Sort field:direction (e.g., lead_score:desc, created_at:asc)
        - status: Comma-separated status values
        - temperature: Comma-separated temperature values
        - source: Comma-separated source values
        - assigned_to: Filter by assigned team member UUID
        - created_after: Filter by creation date (ISO format)
        - min_score: Minimum lead score
        - max_score: Maximum lead score
        - zip_code: Filter by ZIP code
        - converted: Filter by conversion status (true/false)

    Returns:
        200: Paginated list of leads with metadata
        500: Server error
    """
    try:
        # Parse pagination parameters
        page = int(request.args.get("page", 1))
        per_page = min(int(request.args.get("per_page", 50)), 100)

        # Parse sorting
        sort = request.args.get("sort", "created_at:desc")

        # Parse filters
        filters = LeadListFilters(
            status=request.args.get("status"),
            temperature=request.args.get("temperature"),
            source=request.args.get("source"),
            assigned_to=request.args.get("assigned_to"),
            created_after=request.args.get("created_after"),
            min_score=request.args.get("min_score"),
            max_score=request.args.get("max_score"),
            zip_code=request.args.get("zip_code"),
            converted=request.args.get("converted"),
        )

        # Get leads from service
        leads, total = lead_service.get_leads_with_filters(filters, page, per_page, sort)

        # Convert to response format
        lead_data = [lead.to_dict() for lead in leads]

        # Create paginated response
        response = LeadListResponse.create(
            data=lead_data, page=page, per_page=per_page, total=total
        )

        return jsonify(response.model_dump()), 200

    except Exception as e:
        logger.error(f"Error fetching leads: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to fetch leads", "details": str(e)}), 500


@bp.route("/<lead_id>", methods=["GET"])
def get_lead(lead_id: str):
    """
    Get a specific lead by ID with score breakdown.

    Path Parameters:
        lead_id: UUID of the lead

    Returns:
        200: Lead data with score breakdown
        404: Lead not found
        500: Server error
    """
    try:
        # Validate UUID
        if not validate_uuid(lead_id):
            return jsonify({"error": "Invalid lead ID format"}), 400

        # Get lead from service
        lead = lead_service.get_lead_by_id(lead_id)

        if not lead:
            return jsonify({"error": "Lead not found"}), 404

        # Calculate score breakdown
        score_breakdown = lead_scoring_engine.calculate_score(
            lead,
            interaction_count=lead.interaction_count,
            response_time_minutes=lead.response_time_minutes,
        )

        return (
            jsonify({"data": lead.to_dict(), "score_breakdown": score_breakdown.model_dump()}),
            200,
        )

    except Exception as e:
        logger.error(f"Error fetching lead {lead_id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to fetch lead", "details": str(e)}), 500


@bp.route("/", methods=["POST"])
def create_lead():
    """
    Create a new lead with automatic lead scoring.

    Request Body:
        LeadCreate schema (JSON)

    Returns:
        201: Created lead with score
        400: Validation error
        500: Server error
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Validate with Pydantic
        lead_create = LeadCreate(**data)

        # Create lead using service
        lead = lead_service.create_lead(lead_create)

        logger.info(f"Lead created: {lead.id} with score {lead.lead_score}")

        # Calculate score breakdown for response
        score_breakdown = lead_scoring_engine.calculate_score(
            lead,
            interaction_count=0,
            response_time_minutes=None,
            budget_confirmed=lead_create.budget_confirmed,
            is_decision_maker=lead_create.is_decision_maker,
        )

        # Trigger 2-minute alert for new lead
        try:
            from app.services.alert_service import trigger_lead_alert

            alert_success, alert_result = trigger_lead_alert(
                lead_id=str(lead.id),
                lead_data={
                    **lead.to_dict(),
                    "score": lead.lead_score,
                    "temperature": lead.temperature.value if lead.temperature else None,
                },
            )
        except ImportError:
            # Alert service not available, continue without alerts
            alert_success = False
            alert_result = "Alert service not available"
            logger.warning("Alert service not available for new lead notification")

        if not alert_success:
            logger.warning(f"Failed to trigger alert for lead {lead.id}: {alert_result}")

        return (
            jsonify(
                {
                    "data": lead.to_dict(),
                    "score_breakdown": score_breakdown.model_dump(),
                    "alert_triggered": alert_success,
                    "alert_id": alert_result if alert_success else None,
                }
            ),
            201,
        )

    except ValueError as e:
        logger.warning(f"Validation error creating lead: {str(e)}")
        return jsonify({"error": "Validation error", "details": str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating lead: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to create lead", "details": str(e)}), 500


@bp.route("/<lead_id>", methods=["PUT"])
def update_lead(lead_id: str):
    """
    Update a lead and recalculate score.

    Path Parameters:
        lead_id: UUID of the lead

    Request Body:
        LeadUpdate schema (JSON)

    Returns:
        200: Updated lead with new score
        400: Validation error
        404: Lead not found
        500: Server error
    """
    try:
        # Validate UUID
        if not validate_uuid(lead_id):
            return jsonify({"error": "Invalid lead ID format"}), 400

        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Validate with Pydantic
        lead_update = LeadUpdate(**data)

        # Update lead using service
        updated_lead = lead_service.update_lead(lead_id, lead_update)

        if not updated_lead:
            return jsonify({"error": "Lead not found"}), 404

        # Calculate score breakdown for response
        score_breakdown = lead_scoring_engine.recalculate_lead_score(
            updated_lead, interaction_count=updated_lead.interaction_count
        )

        logger.info(f"Lead updated: {lead_id} with new score {updated_lead.lead_score}")

        return (
            jsonify(
                {"data": updated_lead.to_dict(), "score_breakdown": score_breakdown.model_dump()}
            ),
            200,
        )

    except ValueError as e:
        logger.warning(f"Validation error updating lead {lead_id}: {str(e)}")
        return jsonify({"error": "Validation error", "details": str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating lead {lead_id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to update lead", "details": str(e)}), 500


@bp.route("/<lead_id>", methods=["DELETE"])
def delete_lead(lead_id: str):
    """
    Soft delete a lead (marks as deleted, doesn't remove from database).

    Path Parameters:
        lead_id: UUID of the lead

    Returns:
        200: Success message
        404: Lead not found
        500: Server error
    """
    try:
        # Validate UUID
        if not validate_uuid(lead_id):
            return jsonify({"error": "Invalid lead ID format"}), 400

        # Delete lead using service
        success = lead_service.delete_lead(lead_id)

        if not success:
            return jsonify({"error": "Lead not found"}), 404

        logger.info(f"Lead soft deleted: {lead_id}")

        return jsonify({"message": f"Lead {lead_id} deleted successfully"}), 200

    except Exception as e:
        logger.error(f"Error deleting lead {lead_id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to delete lead", "details": str(e)}), 500


# ============================================================================
# SPECIALIZED ENDPOINTS
# ============================================================================


@bp.route("/<lead_id>/score", methods=["POST"])
def recalculate_lead_score(lead_id: str):
    """
    Manually recalculate lead score.

    Path Parameters:
        lead_id: UUID of the lead

    Request Body (optional):
        {
            "interaction_count": int,
            "response_time_minutes": int,
            "budget_confirmed": bool,
            "is_decision_maker": bool
        }

    Returns:
        200: Updated lead with new score breakdown
        404: Lead not found
        500: Server error
    """
    try:
        # Validate UUID
        if not validate_uuid(lead_id):
            return jsonify({"error": "Invalid lead ID format"}), 400

        supabase = get_supabase()

        # Fetch lead
        result = supabase.table("leads").select("*").eq("id", lead_id).execute()

        if not result.data:
            return jsonify({"error": "Lead not found"}), 404

        lead = Lead(**result.data[0])

        # Get optional scoring parameters
        data = request.get_json() or {}
        interaction_count = data.get("interaction_count", lead.interaction_count)
        response_time_minutes = data.get("response_time_minutes", lead.response_time_minutes)
        budget_confirmed = data.get("budget_confirmed", False)
        is_decision_maker = data.get("is_decision_maker", False)

        # Recalculate score
        score_breakdown = lead_scoring_engine.calculate_score(
            lead,
            interaction_count=interaction_count,
            response_time_minutes=response_time_minutes,
            budget_confirmed=budget_confirmed,
            is_decision_maker=is_decision_maker,
        )

        # Update lead
        update_data = {
            "lead_score": score_breakdown.total_score,
            "temperature": score_breakdown.temperature.value,
            "updated_at": datetime.utcnow().isoformat(),
        }

        result = supabase.table("leads").update(update_data).eq("id", lead_id).execute()

        logger.info(f"Lead score recalculated: {lead_id} - Score: {score_breakdown.total_score}")

        return (
            jsonify({"data": result.data[0], "score_breakdown": score_breakdown.model_dump()}),
            200,
        )

    except Exception as e:
        logger.error(f"Error recalculating score for lead {lead_id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to recalculate score", "details": str(e)}), 500


@bp.route("/hot", methods=["GET"])
def get_hot_leads():
    """
    Get all hot leads (score >= 80) requiring immediate action.

    Returns:
        200: List of hot leads
        500: Server error
    """
    try:
        # Get hot leads from service
        hot_leads = lead_service.get_hot_leads()

        return (
            jsonify({"data": [lead.to_dict() for lead in hot_leads], "count": len(hot_leads)}),
            200,
        )

    except Exception as e:
        logger.error(f"Error fetching hot leads: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to fetch hot leads", "details": str(e)}), 500


@bp.route("/<lead_id>/convert", methods=["POST"])
def convert_lead_to_customer(lead_id: str):
    """
    Convert a lead to a customer.

    Path Parameters:
        lead_id: UUID of the lead

    Request Body:
        {
            "customer_id": UUID (optional, if customer already created)
        }

    Returns:
        200: Success message with customer ID
        404: Lead not found
        500: Server error
    """
    try:
        # Validate UUID
        if not validate_uuid(lead_id):
            return jsonify({"error": "Invalid lead ID format"}), 400

        # Get customer ID from request or generate new
        data = request.get_json() or {}
        customer_id = data.get("customer_id")

        # Convert lead using service
        converted_lead = lead_service.convert_lead_to_customer(lead_id, customer_id)

        if not converted_lead:
            return jsonify({"error": "Lead not found"}), 404

        logger.info(f"Lead converted to customer: {lead_id} -> {customer_id}")

        return (
            jsonify(
                {
                    "message": "Lead converted to customer successfully",
                    "lead_id": lead_id,
                    "customer_id": customer_id,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error converting lead {lead_id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to convert lead", "details": str(e)}), 500


@bp.route("/<lead_id>/assign", methods=["POST"])
def assign_lead(lead_id: str):
    """
    Assign a lead to a team member.

    Path Parameters:
        lead_id: UUID of the lead

    Request Body:
        {
            "team_member_id": UUID (required unless auto_assign is true),
            "auto_assign": bool (optional, use automatic assignment),
            "strategy": str (optional, "round_robin" or "load_balanced"),
            "force_reassign": bool (optional, force reassignment if already assigned),
            "notes": str (optional, assignment notes),
            "send_notification": bool (optional, send real-time notification)
        }

    Returns:
        200: Success message with assignment details
        400: Validation error
        404: Lead or team member not found
        500: Server error
    """
    try:
        # Validate UUID
        if not validate_uuid(lead_id):
            return jsonify({"error": "Invalid lead ID format"}), 400

        data = request.get_json() or {}
        supabase = get_supabase()

        # Fetch the lead
        result = supabase.table("leads").select("*").eq("id", lead_id).execute()

        if not result.data:
            return jsonify({"error": "Lead not found"}), 404

        lead = result.data[0]

        # Check if already assigned
        if lead.get("assigned_to") and not data.get("force_reassign"):
            return (
                jsonify(
                    {
                        "error": "Lead is already assigned",
                        "current_assignee": lead.get("assigned_to"),
                        "hint": "Use force_reassign=true to reassign",
                    }
                ),
                400,
            )

        # Determine team member ID
        team_member_id = None

        if data.get("auto_assign"):
            # Automatic assignment logic
            strategy = data.get("strategy", "round_robin")

            # Get available team members
            team_result = (
                supabase.table("team_members")
                .select("id, name, role, status")
                .eq("status", "active")
                .eq("role", "sales_rep")
                .execute()
            )

            if not team_result.data:
                return jsonify({"error": "No available team members for auto-assignment"}), 400

            if strategy == "round_robin":
                # Simple round-robin: assign to team member with least recent assignment
                # For now, just pick the first available
                team_member_id = team_result.data[0]["id"]
            elif strategy == "load_balanced":
                # Assign to team member with fewest active leads
                # This would require counting leads per team member
                # For now, use first available
                team_member_id = team_result.data[0]["id"]
            else:
                team_member_id = team_result.data[0]["id"]

        else:
            # Manual assignment
            team_member_id = data.get("team_member_id")

            if not team_member_id:
                return (
                    jsonify({"error": "team_member_id is required when auto_assign is not true"}),
                    400,
                )

            if not validate_uuid(team_member_id):
                return jsonify({"error": "Invalid team member ID format"}), 400

            # Verify team member exists
            team_result = (
                supabase.table("team_members").select("id, name").eq("id", team_member_id).execute()
            )

            if not team_result.data:
                return jsonify({"error": "Team member not found"}), 400

        # Update the lead with assignment
        update_data = {
            "assigned_to": team_member_id,
            "assigned_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Update status to contacted if it's still new
        if lead.get("status") == LeadStatus.NEW.value:
            update_data["status"] = LeadStatus.CONTACTED.value

        # Add assignment notes if provided
        if data.get("notes"):
            # Store notes in interactions or a separate field
            update_data["assignment_notes"] = data.get("notes")

        # Perform the update
        update_result = supabase.table("leads").update(update_data).eq("id", lead_id).execute()

        if not update_result.data:
            return jsonify({"error": "Failed to assign lead"}), 500

        # Send real-time notification if requested
        if data.get("send_notification"):
            from app.utils.pusher_client import get_pusher_client

            pusher = get_pusher_client()
            pusher.trigger(
                f"team-{team_member_id}",
                "lead-assigned",
                {
                    "lead_id": lead_id,
                    "lead_name": f"{lead.get('first_name')} {lead.get('last_name')}",
                    "assigned_at": update_data["assigned_at"],
                },
            )

        # Log the assignment in interactions
        interaction_data = {
            "entity_type": "lead",
            "entity_id": lead_id,
            "type": "assignment",
            "direction": "internal",
            "subject": f"Lead assigned to team member {team_member_id}",
            "description": data.get("notes", "Lead assignment"),
            "created_at": datetime.utcnow().isoformat(),
        }

        supabase.table("interactions").insert(interaction_data).execute()

        message = (
            "Lead reassigned successfully"
            if lead.get("assigned_to")
            else "Lead assigned successfully"
        )

        logger.info(f"Lead {lead_id} assigned to team member {team_member_id}")

        return (
            jsonify(
                {
                    "message": message,
                    "lead_id": lead_id,
                    "assigned_to": team_member_id,
                    "assigned_at": update_data["assigned_at"],
                    "status": update_data.get("status", lead.get("status")),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error assigning lead {lead_id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to assign lead", "details": str(e)}), 500


@bp.route("/stats", methods=["GET"])
def get_lead_stats():
    """
    Get lead statistics and KPIs.

    Returns:
        200: Lead statistics
        500: Server error
    """
    try:
        # Get stats from service
        stats = lead_service.get_lead_stats()
        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"Error fetching lead stats: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to fetch stats", "details": str(e)}), 500


@bp.route("/bulk-import", methods=["POST"])
def bulk_import_leads():
    """
    Bulk import leads from CSV or Excel file.

    Form Data:
        file: CSV or Excel file (required)
        skip_duplicates: bool (optional, skip duplicate emails)
        auto_score: bool (optional, automatically calculate lead scores)
        validate_strict: bool (optional, strict validation mode)
        field_mapping: JSON string (optional, custom field mapping)
        max_rows: int (optional, maximum rows to import, default 10000)

    Returns:
        201: Import summary with success/failure counts
        207: Partial success with errors
        400: Validation error or invalid file
        413: File too large
        500: Server error
    """
    try:
        # Check if file is present
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Check file extension
        filename = file.filename.lower()
        if not (
            filename.endswith(".csv") or filename.endswith(".xlsx") or filename.endswith(".xls")
        ):
            return (
                jsonify({"error": "Invalid file format. Only CSV and Excel files are supported"}),
                400,
            )

        # Parse form parameters
        skip_duplicates = request.form.get("skip_duplicates", "true").lower() == "true"
        auto_score = request.form.get("auto_score", "true").lower() == "true"
        validate_strict = request.form.get("validate_strict", "false").lower() == "true"
        max_rows = int(request.form.get("max_rows", 10000))

        # Parse field mapping if provided
        field_mapping = {}
        if "field_mapping" in request.form:
            try:
                field_mapping = json.loads(request.form["field_mapping"])
            except json.JSONDecodeError:
                return jsonify({"error": "Invalid field_mapping JSON"}), 400

        # Read the file into a DataFrame
        try:
            if filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(file.read()))
            else:
                df = pd.read_excel(io.BytesIO(file.read()))
        except Exception as e:
            return jsonify({"error": f"Failed to read file: {str(e)}"}), 400

        # Check file size limits
        if len(df) > max_rows:
            return (
                jsonify(
                    {
                        "error": f"File contains {len(df)} rows, which exceeds the limit of {max_rows} rows"
                    }
                ),
                400,
            )

        # Apply field mapping if provided
        if field_mapping:
            df = df.rename(columns=field_mapping)

        # Check for required fields
        required_fields = ["first_name", "last_name", "phone", "source"]

        # Handle full_name if present
        if "full_name" in df.columns and (
            "first_name" not in df.columns or "last_name" not in df.columns
        ):
            # Split full name into first and last
            df[["first_name", "last_name"]] = df["full_name"].str.split(" ", n=1, expand=True)
            df["last_name"] = df["last_name"].fillna("")

        missing_fields = [field for field in required_fields if field not in df.columns]
        if missing_fields:
            return (
                jsonify(
                    {
                        "error": f"Missing required fields: {', '.join(missing_fields)}",
                        "required_fields": required_fields,
                        "found_fields": list(df.columns),
                    }
                ),
                400,
            )

        # Initialize counters
        total_rows = len(df)
        success_count = 0
        failed_count = 0
        duplicate_count = 0
        errors = []
        imported_leads = []

        supabase = get_supabase()

        # Process each row
        for index, row in df.iterrows():
            try:
                # Convert row to dict and remove NaN values
                lead_data = row.to_dict()
                lead_data = {k: v for k, v in lead_data.items() if pd.notna(v)}

                # Clean phone number
                if "phone" in lead_data:
                    lead_data["phone"] = (
                        str(lead_data["phone"])
                        .replace("-", "")
                        .replace(" ", "")
                        .replace("(", "")
                        .replace(")", "")[:15]
                    )

                # Validate email if present
                if "email" in lead_data:
                    email = lead_data["email"]

                    # Check for duplicates if enabled
                    if skip_duplicates:
                        existing = supabase.table("leads").select("id").eq("email", email).execute()
                        if existing.data:
                            duplicate_count += 1
                            continue

                # Map source values if needed
                if "source" in lead_data:
                    source_mapping = {
                        "website": "website_form",
                        "google": "google_ads",
                        "facebook": "facebook_ads",
                        "referral": "referral",
                    }
                    source = str(lead_data["source"]).lower()
                    lead_data["source"] = source_mapping.get(source, source)

                # Create Lead object for validation
                try:
                    lead = LeadCreate(**lead_data)
                    lead_dict = lead.model_dump(exclude_none=True)
                except Exception as e:
                    if validate_strict:
                        errors.append(
                            {
                                "row": index + 2,  # +2 for header and 0-index
                                "error": str(e),
                                "data": lead_data,
                            }
                        )
                        failed_count += 1
                        continue
                    else:
                        # Use partial data
                        lead_dict = lead_data

                # Calculate lead score if enabled
                if auto_score:
                    lead_obj = Lead(**lead_dict, lead_score=0, temperature=None)
                    score_breakdown = lead_scoring_engine.calculate_score(lead_obj)
                    lead_dict["lead_score"] = score_breakdown.total_score
                    lead_dict["temperature"] = score_breakdown.temperature.value

                # Add metadata
                lead_dict["id"] = str(uuid4())
                lead_dict["created_at"] = datetime.utcnow().isoformat()
                lead_dict["updated_at"] = datetime.utcnow().isoformat()
                lead_dict["import_batch_id"] = request.form.get("import_id", str(uuid4()))

                # Add audit fields
                from app.middleware.audit_middleware import get_current_user

                user = get_current_user()
                if user:
                    lead_dict["created_by"] = user.get("id")
                    lead_dict["created_by_email"] = user.get("email")
                    lead_dict["updated_by"] = user.get("id")
                    lead_dict["updated_by_email"] = user.get("email")

                # Insert lead
                result = supabase.table("leads").insert(lead_dict).execute()

                if result.data:
                    success_count += 1
                    imported_leads.append(
                        {
                            "id": lead_dict["id"],
                            "name": f"{lead_dict.get('first_name', '')} {lead_dict.get('last_name', '')}",
                            "score": lead_dict.get("lead_score"),
                        }
                    )
                else:
                    failed_count += 1
                    errors.append(
                        {"row": index + 2, "error": "Failed to insert", "data": lead_data}
                    )

            except Exception as e:
                failed_count += 1
                errors.append(
                    {
                        "row": index + 2,
                        "error": str(e),
                        "data": lead_data if "lead_data" in locals() else row.to_dict(),
                    }
                )

        # Prepare response
        import_id = request.form.get("import_id", str(uuid4()))
        status_code = 201 if failed_count == 0 else 207  # 207 for partial success

        response_data = {
            "import_id": import_id,
            "total_imported": total_rows,
            "success": success_count,
            "failed": failed_count,
            "duplicates": duplicate_count,
            "imported_leads": (
                imported_leads[:10] if len(imported_leads) > 10 else imported_leads
            ),  # Limit response size
        }

        if errors and (validate_strict or len(errors) <= 10):
            response_data["errors"] = errors[:10]  # Limit errors in response

        if success_count > 0:
            # Send real-time notification
            from app.utils.pusher_client import get_pusher_client

            pusher = get_pusher_client()
            pusher.trigger(
                "leads",
                "bulk-import-complete",
                {
                    "import_id": import_id,
                    "success_count": success_count,
                    "failed_count": failed_count,
                },
            )

        logger.info(
            f"Bulk import completed: {success_count} success, {failed_count} failed, {duplicate_count} duplicates"
        )

        return jsonify(response_data), status_code

    except Exception as e:
        logger.error(f"Error in bulk import: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to import leads", "details": str(e)}), 500
