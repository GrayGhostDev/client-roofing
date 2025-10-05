"""
Appointments API Routes for iSwitch Roofs CRM

Provides REST endpoints for appointment scheduling, management, and Google Calendar
integration. Includes availability checking, smart scheduling, and reminder management.

Features:
- CRUD operations for appointments
- Google Calendar OAuth2 and sync
- Availability checking and slot management
- Team schedule views
- Automated reminders
- Rescheduling and cancellation workflows

Author: iSwitch Roofs Development Team
Date: 2025-01-04
"""

import logging
from datetime import datetime

from flask import Blueprint, g, jsonify, redirect, request, session

from app.services.appointments_service import (
    AppointmentStatus,
    AppointmentType,
    ReminderType,
    appointments_service,
)
from app.utils.auth import require_auth, require_role

logger = logging.getLogger(__name__)
bp = Blueprint("appointments", __name__)


@bp.route("/", methods=["GET"])
@require_auth
def get_appointments():
    """
    Get appointments with filtering and pagination

    Query Parameters:
        - customer_id: Filter by customer
        - team_member_id: Filter by team member
        - status: Filter by status
        - appointment_type: Filter by type
        - start_date: Filter appointments after this date
        - end_date: Filter appointments before this date
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20)

    Returns:
        200: List of appointments
        401: Unauthorized
        500: Server error

    Example:
        GET /api/appointments?team_member_id=uuid&start_date=2025-01-01
    """
    try:
        # Get user context
        user = g.get("user")

        # Build query
        from app.config import get_supabase_client

        supabase = get_supabase_client()
        query = supabase.table("appointments").select(
            "*, customers!inner(name, email, phone), team_members!inner(name, email)"
        )

        # Apply filters
        customer_id = request.args.get("customer_id")
        if customer_id:
            query = query.eq("customer_id", customer_id)

        team_member_id = request.args.get("team_member_id")
        if team_member_id:
            query = query.eq("team_member_id", team_member_id)

        status = request.args.get("status")
        if status:
            query = query.eq("status", status)

        appointment_type = request.args.get("appointment_type")
        if appointment_type:
            query = query.eq("appointment_type", appointment_type)

        start_date = request.args.get("start_date")
        if start_date:
            query = query.gte("scheduled_start", start_date)

        end_date = request.args.get("end_date")
        if end_date:
            query = query.lte("scheduled_start", end_date)

        # Pagination
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))

        # Apply sorting
        query = query.order("scheduled_start", desc=False)

        # Execute query with pagination
        start_index = (page - 1) * per_page
        end_index = start_index + per_page - 1
        query = query.range(start_index, end_index)

        result = query.execute()

        # Get total count for pagination
        count_query = supabase.table("appointments").select("id", count="exact")

        if customer_id:
            count_query = count_query.eq("customer_id", customer_id)
        if team_member_id:
            count_query = count_query.eq("team_member_id", team_member_id)
        if status:
            count_query = count_query.eq("status", status)
        if appointment_type:
            count_query = count_query.eq("appointment_type", appointment_type)
        if start_date:
            count_query = count_query.gte("scheduled_start", start_date)
        if end_date:
            count_query = count_query.lte("scheduled_start", end_date)

        count_result = count_query.execute()
        total_count = count_result.count if hasattr(count_result, "count") else len(result.data)

        return (
            jsonify(
                {
                    "success": True,
                    "appointments": result.data,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": total_count,
                        "pages": (total_count + per_page - 1) // per_page,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error fetching appointments: {str(e)}")
        return jsonify({"error": "Failed to fetch appointments"}), 500


@bp.route("/<appointment_id>", methods=["GET"])
@require_auth
def get_appointment(appointment_id: str):
    """
    Get a specific appointment by ID

    Path Parameters:
        appointment_id: Appointment UUID

    Returns:
        200: Appointment details
        401: Unauthorized
        404: Appointment not found
        500: Server error

    Example:
        GET /api/appointments/123e4567-e89b-12d3-a456-426614174000
    """
    try:
        from app.config import get_supabase_client

        supabase = get_supabase_client()

        result = (
            supabase.table("appointments")
            .select(
                "*, customers!inner(name, email, phone, address), "
                "team_members!inner(name, email, phone), "
                "projects(id, status, total_value)"
            )
            .eq("id", appointment_id)
            .execute()
        )

        if not result.data:
            return jsonify({"error": "Appointment not found"}), 404

        return jsonify({"success": True, "appointment": result.data[0]}), 200

    except Exception as e:
        logger.error(f"Error fetching appointment: {str(e)}")
        return jsonify({"error": "Failed to fetch appointment"}), 500


@bp.route("/", methods=["POST"])
@require_auth
def create_appointment():
    """
    Create a new appointment

    Request Body:
        {
            "customer_id": "uuid",
            "appointment_type": "inspection",
            "scheduled_time": "2025-01-15T10:00:00",
            "team_member_id": "uuid",
            "duration": 60,  // minutes, optional
            "location": "123 Main St",  // optional
            "notes": "Customer prefers morning",  // optional
            "send_reminders": true,  // optional, default true
            "sync_to_calendar": true  // optional, default true
        }

    Returns:
        201: Appointment created successfully
        400: Validation error or time slot unavailable
        401: Unauthorized
        500: Server error

    Example:
        POST /api/appointments
        {
            "customer_id": "cust-uuid",
            "appointment_type": "initial_consultation",
            "scheduled_time": "2025-01-15T14:00:00",
            "team_member_id": "team-uuid",
            "duration": 90,
            "location": "Customer residence"
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Validate required fields
        required_fields = ["customer_id", "appointment_type", "scheduled_time", "team_member_id"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400

        # Validate appointment type
        valid_types = [t.value for t in AppointmentType]
        if data["appointment_type"] not in valid_types:
            return (
                jsonify(
                    {"error": f'Invalid appointment type. Must be one of: {", ".join(valid_types)}'}
                ),
                400,
            )

        # Parse scheduled time
        try:
            scheduled_time = datetime.fromisoformat(data["scheduled_time"])
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid scheduled_time format. Use ISO 8601 format"}), 400

        # Check if scheduled time is in the future
        if scheduled_time <= datetime.now():
            return jsonify({"error": "Scheduled time must be in the future"}), 400

        # Create appointment
        success, appointment, error = appointments_service.create_appointment(
            customer_id=data["customer_id"],
            appointment_type=data["appointment_type"],
            scheduled_time=scheduled_time,
            team_member_id=data["team_member_id"],
            duration=data.get("duration"),
            location=data.get("location"),
            notes=data.get("notes"),
            send_reminders=data.get("send_reminders", True),
            sync_to_calendar=data.get("sync_to_calendar", True),
        )

        if not success:
            return jsonify({"error": error}), 400

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Appointment created successfully",
                    "appointment": appointment,
                }
            ),
            201,
        )

    except Exception as e:
        logger.error(f"Error creating appointment: {str(e)}")
        return jsonify({"error": "Failed to create appointment"}), 500


@bp.route("/<appointment_id>", methods=["PUT"])
@require_auth
def update_appointment(appointment_id: str):
    """
    Update an existing appointment

    Path Parameters:
        appointment_id: Appointment UUID

    Request Body:
        {
            "scheduled_time": "2025-01-16T10:00:00",  // optional
            "duration": 90,  // optional
            "location": "Updated location",  // optional
            "notes": "Updated notes",  // optional
            "status": "confirmed"  // optional
        }

    Returns:
        200: Appointment updated successfully
        400: Validation error or time slot unavailable
        401: Unauthorized
        404: Appointment not found
        500: Server error

    Example:
        PUT /api/appointments/123e4567-e89b-12d3-a456-426614174000
        {
            "scheduled_time": "2025-01-16T14:00:00",
            "status": "confirmed"
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Parse scheduled time if provided
        if "scheduled_time" in data:
            try:
                data["scheduled_start"] = datetime.fromisoformat(
                    data.pop("scheduled_time")
                ).isoformat()
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid scheduled_time format"}), 400

        # Validate status if provided
        if "status" in data:
            valid_statuses = [s.value for s in AppointmentStatus]
            if data["status"] not in valid_statuses:
                return (
                    jsonify(
                        {"error": f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}
                    ),
                    400,
                )

        # Update appointment
        success, updated_appointment, error = appointments_service.update_appointment(
            appointment_id=appointment_id, updates=data
        )

        if not success:
            if "not found" in error.lower():
                return jsonify({"error": error}), 404
            return jsonify({"error": error}), 400

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Appointment updated successfully",
                    "appointment": updated_appointment,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error updating appointment: {str(e)}")
        return jsonify({"error": "Failed to update appointment"}), 500


@bp.route("/<appointment_id>", methods=["DELETE"])
@require_auth
def cancel_appointment(appointment_id: str):
    """
    Cancel an appointment

    Path Parameters:
        appointment_id: Appointment UUID

    Request Body (optional):
        {
            "reason": "Customer requested cancellation",
            "cancelled_by": "user_id"
        }

    Returns:
        200: Appointment cancelled successfully
        401: Unauthorized
        404: Appointment not found
        500: Server error

    Example:
        DELETE /api/appointments/123e4567-e89b-12d3-a456-426614174000
        {
            "reason": "Weather conditions"
        }
    """
    try:
        data = request.get_json() or {}
        user = g.get("user")

        # Cancel appointment
        success, error = appointments_service.cancel_appointment(
            appointment_id=appointment_id,
            reason=data.get("reason"),
            cancelled_by=data.get("cancelled_by", user.get("user_id")),
        )

        if not success:
            if "not found" in error.lower():
                return jsonify({"error": error}), 404
            return jsonify({"error": error}), 400

        return jsonify({"success": True, "message": "Appointment cancelled successfully"}), 200

    except Exception as e:
        logger.error(f"Error cancelling appointment: {str(e)}")
        return jsonify({"error": "Failed to cancel appointment"}), 500


@bp.route("/availability/check", methods=["POST"])
@require_auth
def check_availability():
    """
    Check if a time slot is available

    Request Body:
        {
            "team_member_id": "uuid",
            "start_time": "2025-01-15T10:00:00",
            "duration": 60,  // minutes
            "exclude_appointment_id": "uuid"  // optional, for rescheduling
        }

    Returns:
        200: Availability status
        400: Validation error
        401: Unauthorized
        500: Server error

    Example:
        POST /api/appointments/availability/check
        {
            "team_member_id": "team-uuid",
            "start_time": "2025-01-15T10:00:00",
            "duration": 60
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Validate required fields
        required_fields = ["team_member_id", "start_time", "duration"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400

        # Parse start time
        try:
            start_time = datetime.fromisoformat(data["start_time"])
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid start_time format"}), 400

        # Check availability
        is_available, conflict = appointments_service.check_availability(
            team_member_id=data["team_member_id"],
            start_time=start_time,
            duration=int(data["duration"]),
            exclude_appointment_id=data.get("exclude_appointment_id"),
        )

        return jsonify({"success": True, "available": is_available, "conflict": conflict}), 200

    except Exception as e:
        logger.error(f"Error checking availability: {str(e)}")
        return jsonify({"error": "Failed to check availability"}), 500


@bp.route("/availability/slots", methods=["GET"])
@require_auth
def get_available_slots():
    """
    Get available time slots for a specific date

    Query Parameters:
        - team_member_id: Team member UUID (required)
        - date: Date to check (required, format: YYYY-MM-DD)
        - appointment_type: Type of appointment (optional)
        - duration: Duration in minutes (optional, default: 60)

    Returns:
        200: List of available time slots
        400: Validation error
        401: Unauthorized
        500: Server error

    Example:
        GET /api/appointments/availability/slots?team_member_id=uuid&date=2025-01-15&duration=60
    """
    try:
        # Validate required parameters
        team_member_id = request.args.get("team_member_id")
        date_str = request.args.get("date")

        if not team_member_id:
            return jsonify({"error": "team_member_id is required"}), 400

        if not date_str:
            return jsonify({"error": "date is required"}), 400

        # Parse date
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        # Get optional parameters
        appointment_type = request.args.get("appointment_type")
        duration = request.args.get("duration", type=int)

        # Get available slots
        slots = appointments_service.get_available_slots(
            team_member_id=team_member_id,
            date=date,
            appointment_type=appointment_type,
            duration=duration,
        )

        return (
            jsonify(
                {
                    "success": True,
                    "date": date_str,
                    "team_member_id": team_member_id,
                    "available_slots": slots,
                    "total_slots": len(slots),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting available slots: {str(e)}")
        return jsonify({"error": "Failed to get available slots"}), 500


@bp.route("/schedule/<team_member_id>", methods=["GET"])
@require_auth
def get_team_schedule(team_member_id: str):
    """
    Get team member's schedule for a date range

    Path Parameters:
        team_member_id: Team member UUID

    Query Parameters:
        - start_date: Start date (required, format: YYYY-MM-DD)
        - end_date: End date (required, format: YYYY-MM-DD)

    Returns:
        200: Team member's schedule
        400: Validation error
        401: Unauthorized
        500: Server error

    Example:
        GET /api/appointments/schedule/team-uuid?start_date=2025-01-01&end_date=2025-01-31
    """
    try:
        # Get date range
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")

        if not start_date_str or not end_date_str:
            return jsonify({"error": "start_date and end_date are required"}), 400

        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        # Validate date range
        if end_date < start_date:
            return jsonify({"error": "end_date must be after start_date"}), 400

        if (end_date - start_date).days > 90:
            return jsonify({"error": "Date range cannot exceed 90 days"}), 400

        # Get schedule
        schedule = appointments_service.get_team_schedule(
            team_member_id=team_member_id, start_date=start_date, end_date=end_date
        )

        return (
            jsonify(
                {
                    "success": True,
                    "team_member_id": team_member_id,
                    "start_date": start_date_str,
                    "end_date": end_date_str,
                    "appointments": schedule,
                    "total": len(schedule),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting team schedule: {str(e)}")
        return jsonify({"error": "Failed to get team schedule"}), 500


@bp.route("/<appointment_id>/complete", methods=["POST"])
@require_auth
def complete_appointment(appointment_id: str):
    """
    Mark appointment as completed

    Path Parameters:
        appointment_id: Appointment UUID

    Request Body (optional):
        {
            "notes": "Completion notes",
            "follow_up_required": false
        }

    Returns:
        200: Appointment completed successfully
        401: Unauthorized
        404: Appointment not found
        500: Server error

    Example:
        POST /api/appointments/123e4567-e89b-12d3-a456-426614174000/complete
        {
            "notes": "Inspection completed, quote provided",
            "follow_up_required": true
        }
    """
    try:
        data = request.get_json() or {}

        # Complete appointment
        success, error = appointments_service.complete_appointment(
            appointment_id=appointment_id,
            notes=data.get("notes"),
            follow_up_required=data.get("follow_up_required", False),
        )

        if not success:
            if "not found" in error.lower():
                return jsonify({"error": error}), 404
            return jsonify({"error": error}), 400

        return jsonify({"success": True, "message": "Appointment completed successfully"}), 200

    except Exception as e:
        logger.error(f"Error completing appointment: {str(e)}")
        return jsonify({"error": "Failed to complete appointment"}), 500


@bp.route("/<appointment_id>/reminder", methods=["POST"])
@require_auth
def send_reminder(appointment_id: str):
    """
    Send appointment reminder

    Path Parameters:
        appointment_id: Appointment UUID

    Request Body (optional):
        {
            "reminder_type": "email"  // or "sms", default: "email"
        }

    Returns:
        200: Reminder sent successfully
        400: Validation error
        401: Unauthorized
        404: Appointment not found
        500: Server error

    Example:
        POST /api/appointments/123e4567-e89b-12d3-a456-426614174000/reminder
        {
            "reminder_type": "sms"
        }
    """
    try:
        data = request.get_json() or {}

        # Validate reminder type
        reminder_type = data.get("reminder_type", ReminderType.EMAIL)
        valid_types = [t.value for t in ReminderType]

        if reminder_type not in valid_types:
            return (
                jsonify(
                    {"error": f'Invalid reminder type. Must be one of: {", ".join(valid_types)}'}
                ),
                400,
            )

        # Send reminder
        success, error = appointments_service.send_reminder(
            appointment_id=appointment_id, reminder_type=reminder_type
        )

        if not success:
            if "not found" in error.lower():
                return jsonify({"error": error}), 404
            return jsonify({"error": error}), 400

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"{reminder_type.capitalize()} reminder sent successfully",
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error sending reminder: {str(e)}")
        return jsonify({"error": "Failed to send reminder"}), 500


@bp.route("/oauth2/authorize", methods=["GET"])
@require_auth
@require_role("manager")  # Only managers and above can set up calendar sync
def google_calendar_authorize():
    """
    Initiate Google Calendar OAuth2 authorization flow

    Returns:
        302: Redirect to Google OAuth consent screen
        401: Unauthorized
        500: Server error

    Example:
        GET /api/appointments/oauth2/authorize
    """
    try:
        flow = appointments_service.get_oauth_flow()

        if not flow:
            return jsonify({"error": "OAuth configuration not available"}), 500

        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type="offline", include_granted_scopes="true"
        )

        # Store state in session for security
        session["oauth_state"] = state
        session["user_id"] = g.get("user", {}).get("user_id")

        # Redirect to Google OAuth
        return redirect(authorization_url)

    except Exception as e:
        logger.error(f"Error initiating OAuth flow: {str(e)}")
        return jsonify({"error": "Failed to initiate authorization"}), 500


@bp.route("/oauth2/callback", methods=["GET"])
def google_calendar_callback():
    """
    Handle Google Calendar OAuth2 callback

    Query Parameters:
        - code: Authorization code from Google
        - state: Security state parameter

    Returns:
        200: Authorization successful
        400: Authorization failed
        500: Server error

    Example:
        GET /api/appointments/oauth2/callback?code=...&state=...
    """
    try:
        # Verify state parameter
        if "state" not in request.args or request.args["state"] != session.get("oauth_state"):
            return jsonify({"error": "Invalid state parameter"}), 400

        # Get authorization code
        code = request.args.get("code")
        if not code:
            return jsonify({"error": "Authorization code not provided"}), 400

        # Get OAuth flow
        flow = appointments_service.get_oauth_flow()
        if not flow:
            return jsonify({"error": "OAuth configuration not available"}), 500

        # Exchange code for tokens
        flow.fetch_token(code=code)

        # Store credentials
        credentials = flow.credentials
        user_id = session.get("user_id")

        if user_id:
            # Store credentials in database (encrypted)
            from app.config import get_supabase_client

            supabase = get_supabase_client()

            supabase.table("google_calendar_credentials").upsert(
                {
                    "user_id": user_id,
                    "credentials": credentials.to_json(),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            ).execute()

            # Initialize calendar service
            appointments_service.init_google_calendar_service(credentials)

        # Clear session
        session.pop("oauth_state", None)
        session.pop("user_id", None)

        return (
            jsonify({"success": True, "message": "Google Calendar authorization successful"}),
            200,
        )

    except Exception as e:
        logger.error(f"Error in OAuth callback: {str(e)}")
        return jsonify({"error": "Authorization failed"}), 500


@bp.route("/stats", methods=["GET"])
@require_auth
def get_appointment_stats():
    """
    Get appointment statistics

    Query Parameters:
        - team_member_id: Filter by team member (optional)
        - start_date: Start date for stats (optional)
        - end_date: End date for stats (optional)

    Returns:
        200: Appointment statistics
        401: Unauthorized
        500: Server error

    Example:
        GET /api/appointments/stats?start_date=2025-01-01&end_date=2025-01-31
    """
    try:
        from app.config import get_supabase_client

        supabase = get_supabase_client()

        # Build base query
        query = supabase.table("appointments").select("status", count="exact")

        # Apply filters
        team_member_id = request.args.get("team_member_id")
        if team_member_id:
            query = query.eq("team_member_id", team_member_id)

        start_date = request.args.get("start_date")
        if start_date:
            query = query.gte("scheduled_start", start_date)

        end_date = request.args.get("end_date")
        if end_date:
            query = query.lte("scheduled_start", end_date)

        # Get counts by status
        stats = {
            "total": 0,
            "by_status": {},
            "completion_rate": 0,
            "no_show_rate": 0,
            "cancellation_rate": 0,
        }

        for status in AppointmentStatus:
            status_query = query.eq("status", status.value)
            result = status_query.execute()
            count = result.count if hasattr(result, "count") else 0
            stats["by_status"][status.value] = count
            stats["total"] += count

        # Calculate rates
        if stats["total"] > 0:
            completed = stats["by_status"].get(AppointmentStatus.COMPLETED, 0)
            no_shows = stats["by_status"].get(AppointmentStatus.NO_SHOW, 0)
            cancelled = stats["by_status"].get(AppointmentStatus.CANCELLED, 0)

            stats["completion_rate"] = round((completed / stats["total"]) * 100, 2)
            stats["no_show_rate"] = round((no_shows / stats["total"]) * 100, 2)
            stats["cancellation_rate"] = round((cancelled / stats["total"]) * 100, 2)

        return jsonify({"success": True, "stats": stats}), 200

    except Exception as e:
        logger.error(f"Error getting appointment stats: {str(e)}")
        return jsonify({"error": "Failed to get statistics"}), 500


# Health check endpoint
@bp.route("/health", methods=["GET"])
def health_check():
    """
    Check appointments service health

    Returns:
        200: Service is healthy
    """
    return (
        jsonify(
            {
                "success": True,
                "service": "appointments",
                "status": "healthy",
                "features": {
                    "google_calendar": bool(appointments_service.google_client_id),
                    "reminders": True,
                    "availability_checking": True,
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
        ),
        200,
    )


# Error handlers
@bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Appointment endpoint not found"}), 404


@bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error in appointments API: {error}")
    return jsonify({"error": "Internal server error"}), 500
