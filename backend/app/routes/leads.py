"""
iSwitch Roofs CRM - Leads API Routes
Version: 1.0.0

Complete REST API for lead management with pagination, filtering, sorting,
and automatic lead scoring.
"""

from flask import Blueprint, request, jsonify
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from backend.app.models.lead import (
    Lead,
    LeadCreate,
    LeadUpdate,
    LeadListFilters,
    LeadStatus,
    LeadTemperature
)
from backend.app.models.base import PaginationParams, SortParams, PaginatedResponse
from backend.app.services.lead_scoring import lead_scoring_engine
from backend.app.config import get_supabase_client
from backend.app.utils.validators import validate_uuid

logger = logging.getLogger(__name__)
bp = Blueprint('leads', __name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_supabase():
    """Get Supabase client"""
    return get_supabase_client()


def parse_filters(params: Dict[str, Any]) -> Dict[str, Any]:
    """Parse query parameters into Supabase filters"""
    filters = {}

    # Status filter (comma-separated)
    if params.get('status'):
        statuses = params['status'].split(',')
        filters['status'] = {'in': statuses}

    # Temperature filter (comma-separated)
    if params.get('temperature'):
        temps = params['temperature'].split(',')
        filters['temperature'] = {'in': temps}

    # Source filter (comma-separated)
    if params.get('source'):
        sources = params['source'].split(',')
        filters['source'] = {'in': sources}

    # Assigned to
    if params.get('assigned_to'):
        filters['assigned_to'] = params['assigned_to']

    # Created after
    if params.get('created_after'):
        filters['created_at'] = {'gte': params['created_after']}

    # Score range
    if params.get('min_score'):
        filters['lead_score'] = {'gte': int(params['min_score'])}
    if params.get('max_score'):
        if 'lead_score' not in filters:
            filters['lead_score'] = {}
        filters['lead_score']['lte'] = int(params['max_score'])

    # ZIP code
    if params.get('zip_code'):
        filters['zip_code'] = params['zip_code']

    # Converted
    if params.get('converted') is not None:
        filters['converted_to_customer'] = params['converted'] == 'true'

    return filters


def apply_sorting(query, sort_param: str):
    """Apply sorting to Supabase query"""
    if ':' not in sort_param:
        sort_param = f"{sort_param}:desc"

    field, direction = sort_param.split(':')
    ascending = direction.lower() == 'asc'

    return query.order(field, desc=not ascending)


# ============================================================================
# CRUD ENDPOINTS
# ============================================================================

@bp.route('/', methods=['GET'])
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
        supabase = get_supabase()

        # Parse pagination parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
        offset = (page - 1) * per_page

        # Parse sorting
        sort = request.args.get('sort', 'created_at:desc')

        # Build query
        query = supabase.table('leads').select('*', count='exact')

        # Apply filters
        filters = parse_filters(request.args)
        for field, condition in filters.items():
            if isinstance(condition, dict):
                for op, value in condition.items():
                    if op == 'in':
                        query = query.in_(field, value)
                    elif op == 'gte':
                        query = query.gte(field, value)
                    elif op == 'lte':
                        query = query.lte(field, value)
            else:
                query = query.eq(field, condition)

        # Get total count
        count_result = query

        # Apply sorting and pagination
        query = apply_sorting(query, sort)
        query = query.range(offset, offset + per_page - 1)

        # Execute query
        result = query.execute()

        # Get total count
        total = result.count if hasattr(result, 'count') else len(result.data)

        # Return paginated response
        return jsonify(PaginatedResponse.create(
            data=result.data,
            page=page,
            per_page=per_page,
            total=total
        )), 200

    except Exception as e:
        logger.error(f"Error fetching leads: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to fetch leads", "details": str(e)}), 500


@bp.route('/<lead_id>', methods=['GET'])
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

        supabase = get_supabase()

        # Fetch lead
        result = supabase.table('leads').select('*').eq('id', lead_id).execute()

        if not result.data:
            return jsonify({"error": "Lead not found"}), 404

        lead_data = result.data[0]

        # Parse lead into Pydantic model
        lead = Lead(**lead_data)

        # Calculate score breakdown
        score_breakdown = lead_scoring_engine.calculate_score(
            lead,
            interaction_count=lead.interaction_count,
            response_time_minutes=lead.response_time_minutes
        )

        return jsonify({
            "data": lead_data,
            "score_breakdown": score_breakdown.model_dump()
        }), 200

    except Exception as e:
        logger.error(f"Error fetching lead {lead_id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to fetch lead", "details": str(e)}), 500


@bp.route('/', methods=['POST'])
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

        # Create Lead object for scoring
        lead = Lead(
            **lead_create.model_dump(exclude={'budget_confirmed', 'is_decision_maker'}),
            lead_score=0,  # Will be calculated
            temperature=None  # Will be calculated
        )

        # Calculate lead score
        score_breakdown = lead_scoring_engine.calculate_score(
            lead,
            interaction_count=0,
            response_time_minutes=None,
            budget_confirmed=lead_create.budget_confirmed,
            is_decision_maker=lead_create.is_decision_maker
        )

        # Update lead with score and temperature
        lead.lead_score = score_breakdown.total_score
        lead.temperature = score_breakdown.temperature

        # Prepare data for insert (exclude None values)
        insert_data = lead.model_dump(exclude_none=True, exclude={'id', 'created_at', 'updated_at'})

        # Insert into Supabase
        supabase = get_supabase()
        result = supabase.table('leads').insert(insert_data).execute()

        if not result.data:
            return jsonify({"error": "Failed to create lead"}), 500

        created_lead = result.data[0]

        logger.info(f"Lead created: {created_lead['id']} with score {score_breakdown.total_score}")

        return jsonify({
            "data": created_lead,
            "score_breakdown": score_breakdown.model_dump()
        }), 201

    except ValueError as e:
        logger.warning(f"Validation error creating lead: {str(e)}")
        return jsonify({"error": "Validation error", "details": str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating lead: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to create lead", "details": str(e)}), 500


@bp.route('/<lead_id>', methods=['PUT'])
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

        supabase = get_supabase()

        # Fetch existing lead
        result = supabase.table('leads').select('*').eq('id', lead_id).execute()

        if not result.data:
            return jsonify({"error": "Lead not found"}), 404

        existing_lead = Lead(**result.data[0])

        # Apply updates
        update_data = lead_update.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(existing_lead, field, value)

        # Recalculate score
        score_breakdown = lead_scoring_engine.recalculate_lead_score(
            existing_lead,
            interaction_count=existing_lead.interaction_count
        )

        # Update score and temperature
        update_data['lead_score'] = score_breakdown.total_score
        update_data['temperature'] = score_breakdown.temperature.value
        update_data['updated_at'] = datetime.utcnow().isoformat()

        # Update in Supabase
        result = supabase.table('leads').update(update_data).eq('id', lead_id).execute()

        if not result.data:
            return jsonify({"error": "Failed to update lead"}), 500

        updated_lead = result.data[0]

        logger.info(f"Lead updated: {lead_id} with new score {score_breakdown.total_score}")

        return jsonify({
            "data": updated_lead,
            "score_breakdown": score_breakdown.model_dump()
        }), 200

    except ValueError as e:
        logger.warning(f"Validation error updating lead {lead_id}: {str(e)}")
        return jsonify({"error": "Validation error", "details": str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating lead {lead_id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to update lead", "details": str(e)}), 500


@bp.route('/<lead_id>', methods=['DELETE'])
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

        supabase = get_supabase()

        # Check if lead exists
        result = supabase.table('leads').select('id').eq('id', lead_id).execute()

        if not result.data:
            return jsonify({"error": "Lead not found"}), 404

        # Soft delete by updating status to LOST
        update_data = {
            'status': LeadStatus.LOST.value,
            'updated_at': datetime.utcnow().isoformat()
        }

        supabase.table('leads').update(update_data).eq('id', lead_id).execute()

        logger.info(f"Lead soft deleted: {lead_id}")

        return jsonify({"message": f"Lead {lead_id} deleted successfully"}), 200

    except Exception as e:
        logger.error(f"Error deleting lead {lead_id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to delete lead", "details": str(e)}), 500


# ============================================================================
# SPECIALIZED ENDPOINTS
# ============================================================================

@bp.route('/<lead_id>/score', methods=['POST'])
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
        result = supabase.table('leads').select('*').eq('id', lead_id).execute()

        if not result.data:
            return jsonify({"error": "Lead not found"}), 404

        lead = Lead(**result.data[0])

        # Get optional scoring parameters
        data = request.get_json() or {}
        interaction_count = data.get('interaction_count', lead.interaction_count)
        response_time_minutes = data.get('response_time_minutes', lead.response_time_minutes)
        budget_confirmed = data.get('budget_confirmed', False)
        is_decision_maker = data.get('is_decision_maker', False)

        # Recalculate score
        score_breakdown = lead_scoring_engine.calculate_score(
            lead,
            interaction_count=interaction_count,
            response_time_minutes=response_time_minutes,
            budget_confirmed=budget_confirmed,
            is_decision_maker=is_decision_maker
        )

        # Update lead
        update_data = {
            'lead_score': score_breakdown.total_score,
            'temperature': score_breakdown.temperature.value,
            'updated_at': datetime.utcnow().isoformat()
        }

        result = supabase.table('leads').update(update_data).eq('id', lead_id).execute()

        logger.info(f"Lead score recalculated: {lead_id} - Score: {score_breakdown.total_score}")

        return jsonify({
            "data": result.data[0],
            "score_breakdown": score_breakdown.model_dump()
        }), 200

    except Exception as e:
        logger.error(f"Error recalculating score for lead {lead_id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to recalculate score", "details": str(e)}), 500


@bp.route('/hot', methods=['GET'])
def get_hot_leads():
    """
    Get all hot leads (score >= 80) requiring immediate action.

    Returns:
        200: List of hot leads
        500: Server error
    """
    try:
        supabase = get_supabase()

        result = supabase.table('leads')\
            .select('*')\
            .gte('lead_score', 80)\
            .eq('temperature', LeadTemperature.HOT.value)\
            .order('lead_score', desc=True)\
            .execute()

        return jsonify({
            "data": result.data,
            "count": len(result.data)
        }), 200

    except Exception as e:
        logger.error(f"Error fetching hot leads: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to fetch hot leads", "details": str(e)}), 500


@bp.route('/<lead_id>/convert', methods=['POST'])
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

        supabase = get_supabase()

        # Fetch lead
        result = supabase.table('leads').select('*').eq('id', lead_id).execute()

        if not result.data:
            return jsonify({"error": "Lead not found"}), 404

        lead_data = result.data[0]

        # Get customer ID from request or generate new
        data = request.get_json() or {}
        customer_id = data.get('customer_id')

        # Update lead
        update_data = {
            'converted_to_customer': True,
            'customer_id': customer_id,
            'status': LeadStatus.WON.value,
            'updated_at': datetime.utcnow().isoformat()
        }

        supabase.table('leads').update(update_data).eq('id', lead_id).execute()

        logger.info(f"Lead converted to customer: {lead_id} -> {customer_id}")

        return jsonify({
            "message": "Lead converted to customer successfully",
            "lead_id": lead_id,
            "customer_id": customer_id
        }), 200

    except Exception as e:
        logger.error(f"Error converting lead {lead_id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to convert lead", "details": str(e)}), 500


@bp.route('/stats', methods=['GET'])
def get_lead_stats():
    """
    Get lead statistics and KPIs.

    Returns:
        200: Lead statistics
        500: Server error
    """
    try:
        supabase = get_supabase()

        # Get counts by temperature
        hot_count = supabase.table('leads').select('id', count='exact')\
            .eq('temperature', LeadTemperature.HOT.value).execute().count
        warm_count = supabase.table('leads').select('id', count='exact')\
            .eq('temperature', LeadTemperature.WARM.value).execute().count
        cool_count = supabase.table('leads').select('id', count='exact')\
            .eq('temperature', LeadTemperature.COOL.value).execute().count
        cold_count = supabase.table('leads').select('id', count='exact')\
            .eq('temperature', LeadTemperature.COLD.value).execute().count

        # Get counts by status
        new_count = supabase.table('leads').select('id', count='exact')\
            .eq('status', LeadStatus.NEW.value).execute().count
        qualified_count = supabase.table('leads').select('id', count='exact')\
            .eq('status', LeadStatus.QUALIFIED.value).execute().count

        # Get conversion metrics
        total_leads = supabase.table('leads').select('id', count='exact').execute().count
        converted_count = supabase.table('leads').select('id', count='exact')\
            .eq('converted_to_customer', True).execute().count

        conversion_rate = (converted_count / total_leads * 100) if total_leads > 0 else 0

        return jsonify({
            "total_leads": total_leads,
            "by_temperature": {
                "hot": hot_count,
                "warm": warm_count,
                "cool": cool_count,
                "cold": cold_count
            },
            "by_status": {
                "new": new_count,
                "qualified": qualified_count
            },
            "conversion": {
                "converted_count": converted_count,
                "conversion_rate": round(conversion_rate, 2)
            }
        }), 200

    except Exception as e:
        logger.error(f"Error fetching lead stats: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to fetch stats", "details": str(e)}), 500
