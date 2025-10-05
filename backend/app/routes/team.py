"""
Team Management API Routes for iSwitch Roofs CRM

Provides REST endpoints for team member management, performance tracking,
territory assignment, and commission calculations.

Features:
- Team member CRUD operations
- Performance metrics and scoring
- Territory and skill management
- Lead assignment automation
- Commission calculations
- Real-time availability tracking

Author: iSwitch Roofs Development Team
Date: 2025-01-04
"""

import logging
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from app.services.team_service import SkillType, TeamRole, team_service
from app.utils.auth import require_auth, require_role
from app.utils.validators import validate_email_format, validate_phone_format

logger = logging.getLogger(__name__)
bp = Blueprint("team", __name__)


@bp.route("/members", methods=["GET"])
@require_auth
def get_team_members():
    """
    Get all team members with filtering

    Query Parameters:
        - role: Filter by role (admin, manager, sales_rep, etc.)
        - is_active: Filter by active status (true/false)
        - territory: Filter by territory (zip code)
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20)

    Returns:
        200: List of team members
        401: Unauthorized
        500: Server error

    Example:
        GET /api/team/members?role=sales_rep&is_active=true
    """
    try:
        # Get filter parameters
        role = request.args.get("role")
        is_active = request.args.get("is_active")
        territory = request.args.get("territory")
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))

        # Validate role if provided
        if role and role not in [r.value for r in TeamRole]:
            return (
                jsonify(
                    {
                        "error": f'Invalid role. Must be one of: {", ".join([r.value for r in TeamRole])}'
                    }
                ),
                400,
            )

        # Convert is_active to boolean
        if is_active is not None:
            is_active = is_active.lower() == "true"

        # Get team members
        team_members = team_service.get_team_members(
            role=role, is_active=is_active, territory=territory
        )

        # Apply pagination
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_members = team_members[start_index:end_index]

        return (
            jsonify(
                {
                    "success": True,
                    "team_members": paginated_members,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": len(team_members),
                        "pages": (len(team_members) + per_page - 1) // per_page,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error fetching team members: {str(e)}")
        return jsonify({"error": "Failed to fetch team members"}), 500


@bp.route("/members/<member_id>", methods=["GET"])
@require_auth
def get_team_member(member_id: str):
    """
    Get a specific team member by ID

    Path Parameters:
        member_id: Team member UUID

    Returns:
        200: Team member details
        401: Unauthorized
        404: Team member not found
        500: Server error

    Example:
        GET /api/team/members/123e4567-e89b-12d3-a456-426614174000
    """
    try:
        from app.config import get_supabase_client

        supabase = get_supabase_client()

        result = supabase.table("team_members").select("*").eq("id", member_id).execute()

        if not result.data:
            return jsonify({"error": "Team member not found"}), 404

        member = result.data[0]

        # Add performance metrics
        performance = team_service.calculate_performance(
            member_id, datetime.utcnow() - timedelta(days=30), datetime.utcnow()
        )

        member["performance"] = performance

        return jsonify({"success": True, "team_member": member}), 200

    except Exception as e:
        logger.error(f"Error fetching team member: {str(e)}")
        return jsonify({"error": "Failed to fetch team member"}), 500


@bp.route("/members", methods=["POST"])
@require_auth
@require_role("manager")  # Only managers and above can add team members
def create_team_member():
    """
    Create a new team member

    Request Body:
        {
            "name": "John Smith",
            "email": "john@iswitchroofs.com",
            "role": "sales_rep",
            "phone": "+12485551234",  // optional
            "skills": ["roofing_shingle", "sales"],  // optional
            "territories": ["48033", "48034"],  // optional
            "hire_date": "2025-01-01"  // optional
        }

    Returns:
        201: Team member created successfully
        400: Validation error
        401: Unauthorized
        403: Insufficient permissions
        409: Email already exists
        500: Server error

    Example:
        POST /api/team/members
        {
            "name": "John Smith",
            "email": "john@iswitchroofs.com",
            "role": "sales_rep",
            "phone": "+12485551234"
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Validate required fields
        required_fields = ["name", "email", "role"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400

        # Validate email
        if not validate_email_format(data["email"]):
            return jsonify({"error": "Invalid email format"}), 400

        # Validate phone if provided
        if "phone" in data and data["phone"]:
            if not validate_phone_format(data["phone"]):
                return jsonify({"error": "Invalid phone format"}), 400

        # Validate role
        if data["role"] not in [r.value for r in TeamRole]:
            return (
                jsonify(
                    {
                        "error": f'Invalid role. Must be one of: {", ".join([r.value for r in TeamRole])}'
                    }
                ),
                400,
            )

        # Validate skills if provided
        if "skills" in data:
            valid_skills = [s.value for s in SkillType]
            for skill in data["skills"]:
                if skill not in valid_skills:
                    return (
                        jsonify(
                            {
                                "error": f'Invalid skill: {skill}. Must be one of: {", ".join(valid_skills)}'
                            }
                        ),
                        400,
                    )

        # Parse hire date if provided
        hire_date = None
        if "hire_date" in data:
            try:
                hire_date = datetime.fromisoformat(data["hire_date"])
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid hire_date format. Use ISO 8601"}), 400

        # Create team member
        success, member, error = team_service.create_team_member(
            name=data["name"],
            email=data["email"],
            role=data["role"],
            phone=data.get("phone"),
            skills=data.get("skills"),
            territories=data.get("territories"),
            hire_date=hire_date,
        )

        if not success:
            if "already exists" in str(error):
                return jsonify({"error": error}), 409
            return jsonify({"error": error}), 400

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Team member created successfully",
                    "team_member": member,
                }
            ),
            201,
        )

    except Exception as e:
        logger.error(f"Error creating team member: {str(e)}")
        return jsonify({"error": "Failed to create team member"}), 500


@bp.route("/members/<member_id>", methods=["PUT"])
@require_auth
@require_role("manager")
def update_team_member(member_id: str):
    """
    Update team member information

    Path Parameters:
        member_id: Team member UUID

    Request Body:
        {
            "name": "Updated Name",  // optional
            "role": "manager",  // optional
            "skills": ["roofing_metal", "estimation"],  // optional
            "territories": ["48033", "48034", "48035"],  // optional
            "is_active": true  // optional
        }

    Returns:
        200: Team member updated successfully
        400: Validation error
        401: Unauthorized
        403: Insufficient permissions
        404: Team member not found
        500: Server error

    Example:
        PUT /api/team/members/123e4567-e89b-12d3-a456-426614174000
        {
            "role": "manager",
            "skills": ["roofing_metal", "estimation", "project_management"]
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Validate role if being updated
        if "role" in data:
            if data["role"] not in [r.value for r in TeamRole]:
                return (
                    jsonify(
                        {
                            "error": f'Invalid role. Must be one of: {", ".join([r.value for r in TeamRole])}'
                        }
                    ),
                    400,
                )

        # Validate skills if being updated
        if "skills" in data:
            valid_skills = [s.value for s in SkillType]
            for skill in data["skills"]:
                if skill not in valid_skills:
                    return (
                        jsonify(
                            {
                                "error": f'Invalid skill: {skill}. Must be one of: {", ".join(valid_skills)}'
                            }
                        ),
                        400,
                    )

        # Update team member
        success, updated_member, error = team_service.update_team_member(member_id, data)

        if not success:
            if "not found" in str(error).lower():
                return jsonify({"error": error}), 404
            return jsonify({"error": error}), 400

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Team member updated successfully",
                    "team_member": updated_member,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error updating team member: {str(e)}")
        return jsonify({"error": "Failed to update team member"}), 500


@bp.route("/members/<member_id>", methods=["DELETE"])
@require_auth
@require_role("admin")  # Only admins can delete team members
def deactivate_team_member(member_id: str):
    """
    Deactivate a team member (soft delete)

    Path Parameters:
        member_id: Team member UUID

    Returns:
        200: Team member deactivated successfully
        401: Unauthorized
        403: Insufficient permissions
        404: Team member not found
        500: Server error

    Example:
        DELETE /api/team/members/123e4567-e89b-12d3-a456-426614174000
    """
    try:
        # Deactivate rather than delete
        success, _, error = team_service.update_team_member(
            member_id, {"is_active": False, "deactivated_at": datetime.utcnow().isoformat()}
        )

        if not success:
            if "not found" in str(error).lower():
                return jsonify({"error": error}), 404
            return jsonify({"error": error}), 400

        return jsonify({"success": True, "message": "Team member deactivated successfully"}), 200

    except Exception as e:
        logger.error(f"Error deactivating team member: {str(e)}")
        return jsonify({"error": "Failed to deactivate team member"}), 500


@bp.route("/performance/<member_id>", methods=["GET"])
@require_auth
def get_member_performance(member_id: str):
    """
    Get performance metrics for a team member

    Path Parameters:
        member_id: Team member UUID

    Query Parameters:
        - days: Number of days to look back (default: 30, max: 365)

    Returns:
        200: Performance metrics
        401: Unauthorized
        404: Team member not found
        500: Server error

    Example:
        GET /api/team/performance/123e4567-e89b-12d3-a456-426614174000?days=90
    """
    try:
        # Get time period
        days = int(request.args.get("days", 30))
        if days < 1 or days > 365:
            return jsonify({"error": "Days must be between 1 and 365"}), 400

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get performance metrics
        performance = team_service.calculate_performance(member_id, start_date, end_date)

        if not performance:
            return jsonify({"error": "Team member not found or no data available"}), 404

        return jsonify({"success": True, "performance": performance}), 200

    except Exception as e:
        logger.error(f"Error fetching performance: {str(e)}")
        return jsonify({"error": "Failed to fetch performance metrics"}), 500


@bp.route("/assign-lead", methods=["POST"])
@require_auth
def assign_lead():
    """
    Automatically assign lead to best available team member

    Request Body:
        {
            "lead_id": "uuid",
            "zip_code": "48033",
            "required_skills": ["roofing_shingle"],  // optional
            "priority": "high"  // optional
        }

    Returns:
        200: Lead assigned successfully
        400: No available team members
        401: Unauthorized
        500: Server error

    Example:
        POST /api/team/assign-lead
        {
            "lead_id": "lead-uuid",
            "zip_code": "48033",
            "required_skills": ["roofing_metal", "language_spanish"]
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Validate required fields
        if "lead_id" not in data:
            return jsonify({"error": "lead_id is required"}), 400

        # Assign lead
        success, assigned_to, error = team_service.assign_lead_to_member(data["lead_id"], data)

        if not success:
            return jsonify({"error": error}), 400

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Lead assigned successfully",
                    "assigned_to": assigned_to,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error assigning lead: {str(e)}")
        return jsonify({"error": "Failed to assign lead"}), 500


@bp.route("/territories", methods=["GET"])
@require_auth
def get_territories():
    """
    Get territory assignments for all team members

    Returns:
        200: Territory assignments
        401: Unauthorized
        500: Server error

    Example:
        GET /api/team/territories
    """
    try:
        territories = team_service.get_team_territories()

        return jsonify({"success": True, "territories": territories}), 200

    except Exception as e:
        logger.error(f"Error fetching territories: {str(e)}")
        return jsonify({"error": "Failed to fetch territories"}), 500


@bp.route("/availability/<member_id>", methods=["PUT"])
@require_auth
def update_availability(member_id: str):
    """
    Update team member availability

    Path Parameters:
        member_id: Team member UUID

    Request Body:
        {
            "is_available": true,
            "reason": "In meeting"  // optional, for unavailability
        }

    Returns:
        200: Availability updated successfully
        400: Validation error
        401: Unauthorized
        404: Team member not found
        500: Server error

    Example:
        PUT /api/team/availability/123e4567-e89b-12d3-a456-426614174000
        {
            "is_available": false,
            "reason": "Lunch break"
        }
    """
    try:
        data = request.get_json()

        if not data or "is_available" not in data:
            return jsonify({"error": "is_available is required"}), 400

        # Update availability
        success, error = team_service.update_availability(
            member_id, data["is_available"], data.get("reason")
        )

        if not success:
            if "not found" in str(error).lower():
                return jsonify({"error": error}), 404
            return jsonify({"error": error}), 400

        return jsonify({"success": True, "message": "Availability updated successfully"}), 200

    except Exception as e:
        logger.error(f"Error updating availability: {str(e)}")
        return jsonify({"error": "Failed to update availability"}), 500


@bp.route("/commissions/<member_id>", methods=["GET"])
@require_auth
def calculate_commission(member_id: str):
    """
    Calculate commission for a team member

    Path Parameters:
        member_id: Team member UUID

    Query Parameters:
        - month: Month to calculate (format: YYYY-MM, default: current month)

    Returns:
        200: Commission calculation
        401: Unauthorized
        404: Team member not found
        500: Server error

    Example:
        GET /api/team/commissions/123e4567-e89b-12d3-a456-426614174000?month=2025-01
    """
    try:
        # Get month parameter
        month_str = request.args.get("month")

        if month_str:
            try:
                # Parse month
                month_date = datetime.strptime(month_str, "%Y-%m")
                start_date = month_date.replace(day=1)
                # Get last day of month
                if month_date.month == 12:
                    end_date = month_date.replace(
                        year=month_date.year + 1, month=1, day=1
                    ) - timedelta(days=1)
                else:
                    end_date = month_date.replace(month=month_date.month + 1, day=1) - timedelta(
                        days=1
                    )
            except ValueError:
                return jsonify({"error": "Invalid month format. Use YYYY-MM"}), 400
        else:
            # Current month
            now = datetime.utcnow()
            start_date = now.replace(day=1, hour=0, minute=0, second=0)
            end_date = now

        # Calculate commission
        commission = team_service.calculate_commission(member_id, start_date, end_date)

        if "error" in commission:
            return jsonify({"error": commission["error"]}), 404

        return jsonify({"success": True, "commission": commission}), 200

    except Exception as e:
        logger.error(f"Error calculating commission: {str(e)}")
        return jsonify({"error": "Failed to calculate commission"}), 500


@bp.route("/schedule", methods=["GET"])
@require_auth
def get_team_schedule():
    """
    Get team schedule overview

    Query Parameters:
        - date: Date to view (format: YYYY-MM-DD, default: today)

    Returns:
        200: Team schedule
        401: Unauthorized
        500: Server error

    Example:
        GET /api/team/schedule?date=2025-01-15
    """
    try:
        # Get date parameter
        date_str = request.args.get("date")

        if date_str:
            try:
                schedule_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        else:
            schedule_date = datetime.utcnow()

        # Get all active team members
        team_members = team_service.get_team_members(is_active=True)

        # Get appointments for each member
        from app.config import get_supabase_client

        supabase = get_supabase_client()

        schedule = []
        for member in team_members:
            # Get member's appointments for the day
            start_of_day = schedule_date.replace(hour=0, minute=0, second=0)
            end_of_day = schedule_date.replace(hour=23, minute=59, second=59)

            appointments = (
                supabase.table("appointments")
                .select("id", "scheduled_start", "scheduled_end", "appointment_type", "status")
                .eq("team_member_id", member["id"])
                .gte("scheduled_start", start_of_day.isoformat())
                .lte("scheduled_start", end_of_day.isoformat())
                .execute()
            )

            schedule.append(
                {
                    "member_id": member["id"],
                    "member_name": member["name"],
                    "role": member["role"],
                    "is_available": member["is_available"],
                    "appointments": appointments.data if appointments.data else [],
                    "appointment_count": len(appointments.data) if appointments.data else 0,
                }
            )

        return (
            jsonify(
                {
                    "success": True,
                    "date": date_str or schedule_date.strftime("%Y-%m-%d"),
                    "schedule": schedule,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error fetching team schedule: {str(e)}")
        return jsonify({"error": "Failed to fetch team schedule"}), 500


# Health check endpoint
@bp.route("/health", methods=["GET"])
def health_check():
    """
    Check team service health

    Returns:
        200: Service is healthy
    """
    return (
        jsonify(
            {
                "success": True,
                "service": "team",
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
            }
        ),
        200,
    )


# Error handlers
@bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Team endpoint not found"}), 404


@bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error in team API: {error}")
    return jsonify({"error": "Internal server error"}), 500
