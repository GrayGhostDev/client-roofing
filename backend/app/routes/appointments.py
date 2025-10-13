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
from app.utils.pusher_client import get_pusher_service

logger = logging.getLogger(__name__)
bp = Blueprint("appointments", __name__)

# Initialize Pusher service for real-time updates
pusher_service = get_pusher_service()


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
        - limit: Items per page (default: 20)

    Returns:
        200: List of appointments
        401: Unauthorized
        500: Server error

    Example:
        GET /api/appointments?team_member_id=uuid&start_date=2025-01-01
    """
    try:
        from app.utils.database import get_db_session
        from app.utils.pagination import paginate_query, create_pagination_response
        from sqlalchemy import and_
        from app.models.appointment_sqlalchemy import Appointment
        from app.models.customer_sqlalchemy import Customer
        from app.models.team_sqlalchemy import TeamMember

        # Pagination parameters
        page = int(request.args.get("page", 1))
        limit = min(int(request.args.get("limit", 20)), 100)

        # Build query using SQLAlchemy
        db = get_db_session()
        query = db.query(Appointment).filter(Appointment.is_deleted == False)

        # Apply filters
        filters = []

        customer_id = request.args.get("customer_id")
        if customer_id:
            filters.append(Appointment.customer_id == customer_id)

        team_member_id = request.args.get("team_member_id")
        if team_member_id:
            filters.append(Appointment.assigned_to == team_member_id)

        status = request.args.get("status")
        if status:
            filters.append(Appointment.status == status)

        appointment_type = request.args.get("appointment_type")
        if appointment_type:
            filters.append(Appointment.appointment_type == appointment_type)

        start_date = request.args.get("start_date")
        if start_date:
            filters.append(Appointment.scheduled_date >= start_date)

        end_date = request.args.get("end_date")
        if end_date:
            filters.append(Appointment.scheduled_date <= end_date)

        if filters:
            query = query.filter(and_(*filters))

        # Apply sorting
        query = query.order_by(Appointment.scheduled_date.asc())

        # Get paginated results
        appointments, total = paginate_query(query, page=page, per_page=limit)

        # Convert SQLAlchemy models to dicts
        appointments_data = []
        for appointment in appointments:
            appointment_dict = {
                "id": str(appointment.id),
                "entity_type": appointment.entity_type,
                "entity_id": str(appointment.entity_id),
                "appointment_type": appointment.appointment_type.value if appointment.appointment_type else None,
                "status": appointment.status.value if appointment.status else None,
                "title": appointment.title,
                "scheduled_date": appointment.scheduled_date.isoformat() if appointment.scheduled_date else None,
                "duration_minutes": appointment.duration_minutes,
                "end_time": appointment.end_time.isoformat() if appointment.end_time else None,
                "location": appointment.location,
                "is_virtual": appointment.is_virtual,
                "meeting_url": appointment.meeting_url,
                "assigned_to": str(appointment.assigned_to) if appointment.assigned_to else None,
                "customer_id": str(appointment.customer_id) if appointment.customer_id else None,
                "description": appointment.description,
                "created_at": appointment.created_at.isoformat() if appointment.created_at else None,
                "updated_at": appointment.updated_at.isoformat() if appointment.updated_at else None,
            }

            # Enrich with customer name if available
            if appointment.customer_id:
                customer = db.query(Customer).filter(Customer.id == appointment.customer_id).first()
                if customer:
                    appointment_dict["customer_name"] = f"{customer.first_name} {customer.last_name}"
                    appointment_dict["customer_email"] = customer.email
                    appointment_dict["customer_phone"] = customer.phone

            # Enrich with team member name if available
            if appointment.assigned_to:
                team_member = db.query(TeamMember).filter(TeamMember.id == appointment.assigned_to).first()
                if team_member:
                    appointment_dict["team_member_name"] = team_member.name
                    appointment_dict["team_member_email"] = team_member.email

            appointments_data.append(appointment_dict)

        # Create pagination response
        response = create_pagination_response(
            items=appointments_data,
            total=total,
            page=page,
            per_page=limit
        )

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error fetching appointments: {str(e)}", exc_info=True)
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
        from app.utils.database import get_db_session
        from app.models.appointment_sqlalchemy import Appointment
        from app.models.customer_sqlalchemy import Customer
        from app.models.team_sqlalchemy import TeamMember
        from app.models.project_sqlalchemy import Project

        db = get_db_session()

        # Get appointment
        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.is_deleted == False
        ).first()

        if not appointment:
            return jsonify({"error": "Appointment not found"}), 404

        # Build appointment dict
        appointment_dict = {
            "id": str(appointment.id),
            "entity_type": appointment.entity_type,
            "entity_id": str(appointment.entity_id),
            "appointment_type": appointment.appointment_type.value if appointment.appointment_type else None,
            "status": appointment.status.value if appointment.status else None,
            "title": appointment.title,
            "scheduled_date": appointment.scheduled_date.isoformat() if appointment.scheduled_date else None,
            "duration_minutes": appointment.duration_minutes,
            "end_time": appointment.end_time.isoformat() if appointment.end_time else None,
            "location": appointment.location,
            "is_virtual": appointment.is_virtual,
            "meeting_url": appointment.meeting_url,
            "assigned_to": str(appointment.assigned_to) if appointment.assigned_to else None,
            "customer_id": str(appointment.customer_id) if appointment.customer_id else None,
            "description": appointment.description,
            "preparation_notes": appointment.preparation_notes,
            "outcome_notes": appointment.outcome_notes,
            "created_at": appointment.created_at.isoformat() if appointment.created_at else None,
            "updated_at": appointment.updated_at.isoformat() if appointment.updated_at else None,
        }

        # Enrich with customer details if available
        if appointment.customer_id:
            customer = db.query(Customer).filter(Customer.id == appointment.customer_id).first()
            if customer:
                appointment_dict["customer"] = {
                    "id": str(customer.id),
                    "name": f"{customer.first_name} {customer.last_name}",
                    "email": customer.email,
                    "phone": customer.phone,
                    "address": customer.street_address
                }

        # Enrich with team member details if available
        if appointment.assigned_to:
            team_member = db.query(TeamMember).filter(TeamMember.id == appointment.assigned_to).first()
            if team_member:
                appointment_dict["team_member"] = {
                    "id": str(team_member.id),
                    "name": team_member.name,
                    "email": team_member.email,
                    "phone": team_member.phone
                }

        # Enrich with project details if entity is a project
        if appointment.entity_type == "project":
            project = db.query(Project).filter(Project.id == appointment.entity_id).first()
            if project:
                appointment_dict["project"] = {
                    "id": str(project.id),
                    "status": project.status.value if project.status else None,
                    "total_value": float(project.estimated_value) if project.estimated_value else None
                }

        return jsonify({"success": True, "appointment": appointment_dict}), 200

    except Exception as e:
        logger.error(f"Error fetching appointment: {str(e)}", exc_info=True)
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

        # Broadcast appointment creation event
        try:
            pusher_service.broadcast_appointment_created(appointment)
            logger.debug(f"Broadcasted appointment:created event for appointment {appointment.get('id')}")
        except Exception as pusher_error:
            logger.warning(f"Failed to broadcast appointment creation event: {str(pusher_error)}")

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
        from app.utils.database import get_db_session
        from sqlalchemy import func, and_
        from app.models.appointment_sqlalchemy import Appointment, AppointmentStatus

        db = get_db_session()

        # Build base query
        query = db.query(Appointment).filter(Appointment.is_deleted == False)

        # Apply filters
        filters = []
        team_member_id = request.args.get("team_member_id")
        if team_member_id:
            filters.append(Appointment.assigned_to == team_member_id)

        start_date = request.args.get("start_date")
        if start_date:
            filters.append(Appointment.scheduled_date >= start_date)

        end_date = request.args.get("end_date")
        if end_date:
            filters.append(Appointment.scheduled_date <= end_date)

        if filters:
            query = query.filter(and_(*filters))

        # Get counts by status
        stats = {
            "total": 0,
            "by_status": {},
            "completion_rate": 0,
            "no_show_rate": 0,
            "cancellation_rate": 0,
        }

        for status in AppointmentStatus:
            count = query.filter(Appointment.status == status).count()
            stats["by_status"][status.value] = count
            stats["total"] += count

        # Calculate rates
        if stats["total"] > 0:
            completed = stats["by_status"].get(AppointmentStatus.COMPLETED.value, 0)
            no_shows = stats["by_status"].get(AppointmentStatus.NO_SHOW.value, 0)
            cancelled = stats["by_status"].get(AppointmentStatus.CANCELLED.value, 0)

            stats["completion_rate"] = round((completed / stats["total"]) * 100, 2)
            stats["no_show_rate"] = round((no_shows / stats["total"]) * 100, 2)
            stats["cancellation_rate"] = round((cancelled / stats["total"]) * 100, 2)

        return jsonify({"success": True, "stats": stats}), 200

    except Exception as e:
        logger.error(f"Error getting appointment stats: {str(e)}", exc_info=True)
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
