"""
Appointments Service for iSwitch Roofs CRM
Version: 1.0.0
Date: 2025-01-04

Comprehensive appointment scheduling system with Google Calendar integration,
smart scheduling, buffer time management, and automated reminders.

Features:
- Google Calendar OAuth2 integration
- Two-way sync with conflict detection
- Availability management
- Buffer and travel time calculations
- Automated SMS/email reminders
- Rescheduling and cancellation workflows
- Team calendar coordination
"""

import json
import logging
import os
from datetime import datetime, timedelta
from enum import Enum

# Redis for caching
# Background tasks
# Google Calendar imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.config import get_redis_client, get_supabase_client
from app.services.alert_service import alert_service

logger = logging.getLogger(__name__)


class AppointmentStatus(str, Enum):
    """Appointment status enumeration"""

    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"
    NO_SHOW = "no_show"


class AppointmentType(str, Enum):
    """Appointment type enumeration"""

    INITIAL_CONSULTATION = "initial_consultation"
    INSPECTION = "inspection"
    ESTIMATE = "estimate"
    PROJECT_START = "project_start"
    PROJECT_REVIEW = "project_review"
    FINAL_WALKTHROUGH = "final_walkthrough"
    FOLLOW_UP = "follow_up"
    MAINTENANCE = "maintenance"


class ReminderType(str, Enum):
    """Reminder type enumeration"""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    CALL = "call"


class AppointmentsService:
    """
    Service for managing appointments with Google Calendar integration.

    Implements smart scheduling, availability management, and automated
    reminders for the roofing CRM system.
    """

    def __init__(self):
        """Initialize appointments service"""
        self._supabase = None
        self._redis = None
        self._calendar_service = None

        # Google Calendar configuration
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.google_redirect_uri = os.getenv(
            "GOOGLE_REDIRECT_URI", "http://localhost:5000/api/appointments/oauth2callback"
        )
        self.google_scopes = ["https://www.googleapis.com/auth/calendar"]

        # Appointment settings
        self.default_duration = 60  # minutes
        self.buffer_time = 15  # minutes between appointments
        self.travel_time = 30  # default travel time
        self.reminder_times = [24 * 60, 2 * 60]  # 24 hours and 2 hours before
        self.business_hours = {
            "monday": {"start": "08:00", "end": "18:00"},
            "tuesday": {"start": "08:00", "end": "18:00"},
            "wednesday": {"start": "08:00", "end": "18:00"},
            "thursday": {"start": "08:00", "end": "18:00"},
            "friday": {"start": "08:00", "end": "18:00"},
            "saturday": {"start": "09:00", "end": "14:00"},
            "sunday": None,  # Closed
        }

        # Cache settings
        self.cache_ttl = 300  # 5 minutes

    @property
    def supabase(self):
        """Lazy load Supabase client"""
        if self._supabase is None:
            self._supabase = get_supabase_client()
        return self._supabase

    @property
    def redis_client(self):
        """Lazy load Redis client"""
        if self._redis is None:
            self._redis = get_redis_client()
        return self._redis

    def create_appointment(
        self,
        customer_id: str,
        appointment_type: str,
        scheduled_time: datetime,
        team_member_id: str,
        duration: int = None,
        location: str = None,
        notes: str = None,
        send_reminders: bool = True,
        sync_to_calendar: bool = True,
    ) -> tuple[bool, dict | None, str | None]:
        """
        Create a new appointment

        Args:
            customer_id: Customer ID
            appointment_type: Type of appointment
            scheduled_time: Scheduled datetime
            team_member_id: Assigned team member
            duration: Duration in minutes
            location: Appointment location
            notes: Additional notes
            send_reminders: Whether to send reminders
            sync_to_calendar: Whether to sync with Google Calendar

        Returns:
            Tuple of (success, appointment_data, error_message)
        """
        try:
            # Validate appointment type
            if appointment_type not in [t.value for t in AppointmentType]:
                return False, None, f"Invalid appointment type: {appointment_type}"

            # Use default duration if not specified
            if duration is None:
                duration = self.default_duration

            # Check availability
            is_available, conflict = self.check_availability(
                team_member_id, scheduled_time, duration
            )

            if not is_available:
                return False, None, f"Time slot not available: {conflict}"

            # Calculate end time
            end_time = scheduled_time + timedelta(minutes=duration + self.buffer_time)

            # Create appointment record
            appointment_data = {
                "customer_id": customer_id,
                "team_member_id": team_member_id,
                "appointment_type": appointment_type,
                "scheduled_start": scheduled_time.isoformat(),
                "scheduled_end": end_time.isoformat(),
                "duration": duration,
                "buffer_time": self.buffer_time,
                "location": location,
                "notes": notes,
                "status": AppointmentStatus.SCHEDULED,
                "send_reminders": send_reminders,
                "created_at": datetime.utcnow().isoformat(),
            }

            result = self.supabase.table("appointments").insert(appointment_data).execute()

            if not result.data:
                return False, None, "Failed to create appointment"

            appointment = result.data[0]

            # Sync with Google Calendar
            if sync_to_calendar and self.google_client_id:
                calendar_event_id = self._sync_to_google_calendar(appointment)
                if calendar_event_id:
                    # Update appointment with calendar event ID
                    self.supabase.table("appointments").update(
                        {"google_calendar_event_id": calendar_event_id}
                    ).eq("id", appointment["id"]).execute()
                    appointment["google_calendar_event_id"] = calendar_event_id

            # Schedule reminders
            if send_reminders:
                self._schedule_reminders(appointment)

            # Send confirmation
            self._send_confirmation(appointment)

            # Clear availability cache
            self._clear_availability_cache(team_member_id, scheduled_time)

            logger.info(f"Appointment created: {appointment['id']}")
            return True, appointment, None

        except Exception as e:
            logger.error(f"Error creating appointment: {str(e)}")
            return False, None, str(e)

    def update_appointment(
        self, appointment_id: str, updates: dict
    ) -> tuple[bool, dict | None, str | None]:
        """
        Update an existing appointment

        Args:
            appointment_id: Appointment ID
            updates: Dictionary of updates

        Returns:
            Tuple of (success, updated_appointment, error_message)
        """
        try:
            # Get existing appointment
            result = (
                self.supabase.table("appointments").select("*").eq("id", appointment_id).execute()
            )

            if not result.data:
                return False, None, "Appointment not found"

            appointment = result.data[0]

            # Check if rescheduling
            if "scheduled_start" in updates:
                # Check new availability
                new_start = datetime.fromisoformat(updates["scheduled_start"])
                duration = updates.get("duration", appointment["duration"])

                is_available, conflict = self.check_availability(
                    appointment["team_member_id"],
                    new_start,
                    duration,
                    exclude_appointment_id=appointment_id,
                )

                if not is_available:
                    return False, None, f"New time slot not available: {conflict}"

                # Calculate new end time
                updates["scheduled_end"] = (
                    new_start + timedelta(minutes=duration + self.buffer_time)
                ).isoformat()
                updates["status"] = AppointmentStatus.RESCHEDULED

                # Track rescheduling history
                self._track_reschedule(appointment, updates)

            # Update appointment
            updates["updated_at"] = datetime.utcnow().isoformat()

            result = (
                self.supabase.table("appointments")
                .update(updates)
                .eq("id", appointment_id)
                .execute()
            )

            if not result.data:
                return False, None, "Failed to update appointment"

            updated_appointment = result.data[0]

            # Update Google Calendar if needed
            if updated_appointment.get("google_calendar_event_id"):
                self._update_google_calendar_event(updated_appointment)

            # Reschedule reminders if time changed
            if "scheduled_start" in updates:
                self._reschedule_reminders(updated_appointment)
                self._send_reschedule_notification(updated_appointment)

            # Clear caches
            self._clear_availability_cache(
                updated_appointment["team_member_id"],
                datetime.fromisoformat(updated_appointment["scheduled_start"]),
            )

            logger.info(f"Appointment updated: {appointment_id}")
            return True, updated_appointment, None

        except Exception as e:
            logger.error(f"Error updating appointment: {str(e)}")
            return False, None, str(e)

    def cancel_appointment(
        self, appointment_id: str, reason: str = None, cancelled_by: str = None
    ) -> tuple[bool, str | None]:
        """
        Cancel an appointment

        Args:
            appointment_id: Appointment ID
            reason: Cancellation reason
            cancelled_by: User who cancelled

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get appointment
            result = (
                self.supabase.table("appointments").select("*").eq("id", appointment_id).execute()
            )

            if not result.data:
                return False, "Appointment not found"

            appointment = result.data[0]

            # Update appointment status
            updates = {
                "status": AppointmentStatus.CANCELLED,
                "cancellation_reason": reason,
                "cancelled_by": cancelled_by,
                "cancelled_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            result = (
                self.supabase.table("appointments")
                .update(updates)
                .eq("id", appointment_id)
                .execute()
            )

            if not result.data:
                return False, "Failed to cancel appointment"

            # Cancel in Google Calendar
            if appointment.get("google_calendar_event_id"):
                self._cancel_google_calendar_event(appointment["google_calendar_event_id"])

            # Cancel reminders
            self._cancel_reminders(appointment_id)

            # Send cancellation notification
            self._send_cancellation_notification(appointment, reason)

            # Clear cache
            self._clear_availability_cache(
                appointment["team_member_id"],
                datetime.fromisoformat(appointment["scheduled_start"]),
            )

            logger.info(f"Appointment cancelled: {appointment_id}")
            return True, None

        except Exception as e:
            logger.error(f"Error cancelling appointment: {str(e)}")
            return False, str(e)

    def check_availability(
        self,
        team_member_id: str,
        start_time: datetime,
        duration: int,
        exclude_appointment_id: str = None,
    ) -> tuple[bool, str | None]:
        """
        Check if a time slot is available

        Args:
            team_member_id: Team member ID
            start_time: Start time to check
            duration: Duration in minutes
            exclude_appointment_id: Appointment ID to exclude

        Returns:
            Tuple of (is_available, conflict_description)
        """
        try:
            # Check cache first
            cache_key = f"availability:{team_member_id}:{start_time.date()}"
            cached_slots = self.redis_client.get(cache_key)

            if cached_slots:
                slots = json.loads(cached_slots)
                # Check if requested time conflicts with booked slots
                for slot in slots:
                    if exclude_appointment_id and slot["id"] == exclude_appointment_id:
                        continue

                    slot_start = datetime.fromisoformat(slot["start"])
                    slot_end = datetime.fromisoformat(slot["end"])
                    end_time = start_time + timedelta(minutes=duration)

                    if start_time < slot_end and end_time > slot_start:
                        return (
                            False,
                            f"Conflicts with existing appointment at {slot_start.strftime('%I:%M %p')}",
                        )

            # Check business hours
            day_name = start_time.strftime("%A").lower()
            business_hours = self.business_hours.get(day_name)

            if not business_hours:
                return False, f"No availability on {day_name.capitalize()}"

            # Parse business hours
            bh_start = datetime.combine(
                start_time.date(), datetime.strptime(business_hours["start"], "%H:%M").time()
            )
            bh_end = datetime.combine(
                start_time.date(), datetime.strptime(business_hours["end"], "%H:%M").time()
            )

            end_time = start_time + timedelta(minutes=duration)

            if start_time < bh_start or end_time > bh_end:
                return (
                    False,
                    f"Outside business hours ({business_hours['start']} - {business_hours['end']})",
                )

            # Query database for conflicts
            query = (
                self.supabase.table("appointments")
                .select("*")
                .eq("team_member_id", team_member_id)
                .in_("status", [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
            )

            if exclude_appointment_id:
                query = query.neq("id", exclude_appointment_id)

            # Get appointments for the date range
            date_start = start_time.replace(hour=0, minute=0, second=0).isoformat()
            date_end = (
                (start_time + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat()
            )

            query = query.gte("scheduled_start", date_start).lt("scheduled_start", date_end)

            result = query.execute()

            # Check for conflicts
            for appointment in result.data:
                apt_start = datetime.fromisoformat(appointment["scheduled_start"])
                apt_end = datetime.fromisoformat(appointment["scheduled_end"])

                if start_time < apt_end and end_time > apt_start:
                    return False, f"Conflicts with appointment at {apt_start.strftime('%I:%M %p')}"

            # Update cache
            self._update_availability_cache(team_member_id, start_time.date())

            return True, None

        except Exception as e:
            logger.error(f"Error checking availability: {str(e)}")
            return False, "Error checking availability"

    def get_available_slots(
        self,
        team_member_id: str,
        date: datetime,
        appointment_type: str = None,
        duration: int = None,
    ) -> list[dict]:
        """
        Get available time slots for a specific date

        Args:
            team_member_id: Team member ID
            date: Date to check
            appointment_type: Type of appointment
            duration: Duration in minutes

        Returns:
            List of available time slots
        """
        try:
            if duration is None:
                duration = self.default_duration

            available_slots = []

            # Get business hours for the day
            day_name = date.strftime("%A").lower()
            business_hours = self.business_hours.get(day_name)

            if not business_hours:
                return []

            # Parse business hours
            start_time = datetime.combine(
                date.date(), datetime.strptime(business_hours["start"], "%H:%M").time()
            )
            end_time = datetime.combine(
                date.date(), datetime.strptime(business_hours["end"], "%H:%M").time()
            )

            # Get existing appointments
            result = (
                self.supabase.table("appointments")
                .select("scheduled_start", "scheduled_end")
                .eq("team_member_id", team_member_id)
                .in_("status", [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
                .gte("scheduled_start", date.replace(hour=0, minute=0).isoformat())
                .lt(
                    "scheduled_start",
                    (date + timedelta(days=1)).replace(hour=0, minute=0).isoformat(),
                )
                .execute()
            )

            booked_slots = []
            for apt in result.data:
                booked_slots.append(
                    {
                        "start": datetime.fromisoformat(apt["scheduled_start"]),
                        "end": datetime.fromisoformat(apt["scheduled_end"]),
                    }
                )

            # Sort booked slots
            booked_slots.sort(key=lambda x: x["start"])

            # Find available slots
            current_time = start_time
            slot_duration = timedelta(minutes=duration + self.buffer_time)

            for booked in booked_slots:
                # Check if there's space before this appointment
                if current_time + slot_duration <= booked["start"]:
                    available_slots.append(
                        {
                            "start": current_time.isoformat(),
                            "end": (current_time + timedelta(minutes=duration)).isoformat(),
                            "duration": duration,
                        }
                    )

                # Move current time to after this appointment
                current_time = max(current_time, booked["end"])

            # Check if there's space after the last appointment
            while current_time + slot_duration <= end_time:
                available_slots.append(
                    {
                        "start": current_time.isoformat(),
                        "end": (current_time + timedelta(minutes=duration)).isoformat(),
                        "duration": duration,
                    }
                )
                current_time += slot_duration

            return available_slots

        except Exception as e:
            logger.error(f"Error getting available slots: {str(e)}")
            return []

    def get_team_schedule(
        self, team_member_id: str, start_date: datetime, end_date: datetime
    ) -> list[dict]:
        """
        Get team member's schedule for a date range

        Args:
            team_member_id: Team member ID
            start_date: Start date
            end_date: End date

        Returns:
            List of appointments
        """
        try:
            result = (
                self.supabase.table("appointments")
                .select("*, customers!inner(name, email, phone)")
                .eq("team_member_id", team_member_id)
                .gte("scheduled_start", start_date.isoformat())
                .lte("scheduled_start", end_date.isoformat())
                .order("scheduled_start")
                .execute()
            )

            return result.data

        except Exception as e:
            logger.error(f"Error getting team schedule: {str(e)}")
            return []

    def send_reminder(
        self, appointment_id: str, reminder_type: str = ReminderType.EMAIL
    ) -> tuple[bool, str | None]:
        """
        Send appointment reminder

        Args:
            appointment_id: Appointment ID
            reminder_type: Type of reminder

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get appointment with customer info
            result = (
                self.supabase.table("appointments")
                .select("*, customers!inner(name, email, phone), team_members!inner(name)")
                .eq("id", appointment_id)
                .execute()
            )

            if not result.data:
                return False, "Appointment not found"

            appointment = result.data[0]
            customer = appointment["customers"]
            team_member = appointment["team_members"]

            # Format appointment time
            apt_time = datetime.fromisoformat(appointment["scheduled_start"])
            formatted_time = apt_time.strftime("%B %d, %Y at %I:%M %p")

            # Prepare reminder message
            message = f"""
            Reminder: You have an appointment scheduled with {team_member['name']}
            for {appointment['appointment_type'].replace('_', ' ').title()}
            on {formatted_time}.

            Location: {appointment.get('location', 'To be confirmed')}

            Please confirm your attendance or contact us if you need to reschedule.
            """

            # Send based on reminder type
            if reminder_type == ReminderType.EMAIL and customer.get("email"):
                # Send email reminder
                alert_service.send_email_notification(
                    to_email=customer["email"],
                    subject=f"Appointment Reminder - {formatted_time}",
                    body=message,
                    notification_type="appointment_reminder",
                )

            elif reminder_type == ReminderType.SMS and customer.get("phone"):
                # Send SMS reminder
                alert_service.send_sms_notification(
                    to_phone=customer["phone"],
                    message=message,
                    notification_type="appointment_reminder",
                )
            else:
                return False, f"Cannot send {reminder_type} reminder - missing contact info"

            # Log reminder sent
            self.supabase.table("appointment_reminders").insert(
                {
                    "appointment_id": appointment_id,
                    "reminder_type": reminder_type,
                    "sent_at": datetime.utcnow().isoformat(),
                }
            ).execute()

            logger.info(f"Reminder sent for appointment {appointment_id}")
            return True, None

        except Exception as e:
            logger.error(f"Error sending reminder: {str(e)}")
            return False, str(e)

    def complete_appointment(
        self, appointment_id: str, notes: str = None, follow_up_required: bool = False
    ) -> tuple[bool, str | None]:
        """
        Mark appointment as completed

        Args:
            appointment_id: Appointment ID
            notes: Completion notes
            follow_up_required: Whether follow-up is needed

        Returns:
            Tuple of (success, error_message)
        """
        try:
            updates = {
                "status": AppointmentStatus.COMPLETED,
                "completion_notes": notes,
                "completed_at": datetime.utcnow().isoformat(),
                "follow_up_required": follow_up_required,
                "updated_at": datetime.utcnow().isoformat(),
            }

            result = (
                self.supabase.table("appointments")
                .update(updates)
                .eq("id", appointment_id)
                .execute()
            )

            if not result.data:
                return False, "Failed to complete appointment"

            appointment = result.data[0]

            # Create follow-up task if needed
            if follow_up_required:
                self._create_follow_up_task(appointment)

            # Update Google Calendar
            if appointment.get("google_calendar_event_id"):
                self._update_google_calendar_event(appointment)

            logger.info(f"Appointment completed: {appointment_id}")
            return True, None

        except Exception as e:
            logger.error(f"Error completing appointment: {str(e)}")
            return False, str(e)

    # Private helper methods
    def _sync_to_google_calendar(self, appointment: dict) -> str | None:
        """Sync appointment to Google Calendar"""
        try:
            if not self._calendar_service:
                return None

            # Get customer info
            customer_result = (
                self.supabase.table("customers")
                .select("name", "email", "phone")
                .eq("id", appointment["customer_id"])
                .execute()
            )

            customer = customer_result.data[0] if customer_result.data else {}

            # Create calendar event
            event = {
                "summary": f"{appointment['appointment_type'].replace('_', ' ').title()} - {customer.get('name', 'Customer')}",
                "location": appointment.get("location", ""),
                "description": f"Customer: {customer.get('name', '')}\nPhone: {customer.get('phone', '')}\n\n{appointment.get('notes', '')}",
                "start": {
                    "dateTime": appointment["scheduled_start"],
                    "timeZone": "America/Detroit",
                },
                "end": {
                    "dateTime": appointment["scheduled_end"],
                    "timeZone": "America/Detroit",
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": 60},
                        {"method": "email", "minutes": 24 * 60},
                    ],
                },
            }

            # Add customer as attendee if email exists
            if customer.get("email"):
                event["attendees"] = [{"email": customer["email"]}]

            # Insert event
            result = (
                self._calendar_service.events()
                .insert(calendarId="primary", body=event, sendUpdates="all")
                .execute()
            )

            return result.get("id")

        except Exception as e:
            logger.error(f"Error syncing to Google Calendar: {str(e)}")
            return None

    def _update_google_calendar_event(self, appointment: dict):
        """Update Google Calendar event"""
        try:
            if not self._calendar_service or not appointment.get("google_calendar_event_id"):
                return

            # Update event details
            event = (
                self._calendar_service.events()
                .get(calendarId="primary", eventId=appointment["google_calendar_event_id"])
                .execute()
            )

            event["start"] = {
                "dateTime": appointment["scheduled_start"],
                "timeZone": "America/Detroit",
            }
            event["end"] = {
                "dateTime": appointment["scheduled_end"],
                "timeZone": "America/Detroit",
            }

            if appointment["status"] == AppointmentStatus.COMPLETED:
                event["summary"] = f"[COMPLETED] {event.get('summary', '')}"
            elif appointment["status"] == AppointmentStatus.CANCELLED:
                event["summary"] = f"[CANCELLED] {event.get('summary', '')}"

            self._calendar_service.events().update(
                calendarId="primary",
                eventId=appointment["google_calendar_event_id"],
                body=event,
                sendUpdates="all",
            ).execute()

        except Exception as e:
            logger.error(f"Error updating Google Calendar event: {str(e)}")

    def _cancel_google_calendar_event(self, event_id: str):
        """Cancel Google Calendar event"""
        try:
            if not self._calendar_service:
                return

            self._calendar_service.events().delete(
                calendarId="primary", eventId=event_id, sendUpdates="all"
            ).execute()

        except Exception as e:
            logger.error(f"Error cancelling Google Calendar event: {str(e)}")

    def _schedule_reminders(self, appointment: dict):
        """Schedule appointment reminders"""
        try:
            scheduled_time = datetime.fromisoformat(appointment["scheduled_start"])

            for minutes_before in self.reminder_times:
                reminder_time = scheduled_time - timedelta(minutes=minutes_before)

                # Only schedule if in the future
                if reminder_time > datetime.now():
                    # Schedule with Celery or your task queue
                    task_data = {
                        "appointment_id": appointment["id"],
                        "reminder_type": (
                            ReminderType.EMAIL if minutes_before >= 60 else ReminderType.SMS
                        ),
                        "scheduled_for": reminder_time.isoformat(),
                    }

                    # Store in database for tracking
                    self.supabase.table("scheduled_reminders").insert(task_data).execute()

        except Exception as e:
            logger.error(f"Error scheduling reminders: {str(e)}")

    def _reschedule_reminders(self, appointment: dict):
        """Reschedule reminders for updated appointment"""
        try:
            # Cancel existing reminders
            self._cancel_reminders(appointment["id"])

            # Schedule new reminders
            self._schedule_reminders(appointment)

        except Exception as e:
            logger.error(f"Error rescheduling reminders: {str(e)}")

    def _cancel_reminders(self, appointment_id: str):
        """Cancel scheduled reminders"""
        try:
            # Update scheduled reminders as cancelled
            self.supabase.table("scheduled_reminders").update(
                {"status": "cancelled", "cancelled_at": datetime.utcnow().isoformat()}
            ).eq("appointment_id", appointment_id).eq("status", "pending").execute()

        except Exception as e:
            logger.error(f"Error cancelling reminders: {str(e)}")

    def _send_confirmation(self, appointment: dict):
        """Send appointment confirmation"""
        try:
            # Get customer info
            customer_result = (
                self.supabase.table("customers")
                .select("name", "email", "phone")
                .eq("id", appointment["customer_id"])
                .execute()
            )

            if not customer_result.data:
                return

            customer = customer_result.data[0]
            apt_time = datetime.fromisoformat(appointment["scheduled_start"])
            formatted_time = apt_time.strftime("%B %d, %Y at %I:%M %p")

            message = f"""
            Your appointment has been confirmed for {formatted_time}.

            Type: {appointment['appointment_type'].replace('_', ' ').title()}
            Location: {appointment.get('location', 'To be confirmed')}

            We'll send you a reminder before your appointment.
            If you need to reschedule, please contact us.
            """

            # Send confirmation
            if customer.get("email"):
                alert_service.send_email_notification(
                    to_email=customer["email"],
                    subject=f"Appointment Confirmed - {formatted_time}",
                    body=message,
                    notification_type="appointment_confirmation",
                )

        except Exception as e:
            logger.error(f"Error sending confirmation: {str(e)}")

    def _send_reschedule_notification(self, appointment: dict):
        """Send rescheduling notification"""
        try:
            # Get customer info
            customer_result = (
                self.supabase.table("customers")
                .select("name", "email", "phone")
                .eq("id", appointment["customer_id"])
                .execute()
            )

            if not customer_result.data:
                return

            customer = customer_result.data[0]
            apt_time = datetime.fromisoformat(appointment["scheduled_start"])
            formatted_time = apt_time.strftime("%B %d, %Y at %I:%M %p")

            message = f"""
            Your appointment has been rescheduled to {formatted_time}.

            Type: {appointment['appointment_type'].replace('_', ' ').title()}
            Location: {appointment.get('location', 'To be confirmed')}

            We'll send you a reminder before your appointment.
            """

            # Send notification
            if customer.get("email"):
                alert_service.send_email_notification(
                    to_email=customer["email"],
                    subject=f"Appointment Rescheduled - {formatted_time}",
                    body=message,
                    notification_type="appointment_reschedule",
                )

        except Exception as e:
            logger.error(f"Error sending reschedule notification: {str(e)}")

    def _send_cancellation_notification(self, appointment: dict, reason: str = None):
        """Send cancellation notification"""
        try:
            # Get customer info
            customer_result = (
                self.supabase.table("customers")
                .select("name", "email", "phone")
                .eq("id", appointment["customer_id"])
                .execute()
            )

            if not customer_result.data:
                return

            customer = customer_result.data[0]

            message = f"""
            Your appointment has been cancelled.

            Type: {appointment['appointment_type'].replace('_', ' ').title()}
            Original Time: {datetime.fromisoformat(appointment['scheduled_start']).strftime('%B %d, %Y at %I:%M %p')}
            {f"Reason: {reason}" if reason else ""}

            Please contact us to reschedule at your convenience.
            """

            # Send notification
            if customer.get("email"):
                alert_service.send_email_notification(
                    to_email=customer["email"],
                    subject="Appointment Cancelled",
                    body=message,
                    notification_type="appointment_cancellation",
                )

        except Exception as e:
            logger.error(f"Error sending cancellation notification: {str(e)}")

    def _track_reschedule(self, original: dict, updates: dict):
        """Track appointment reschedule history"""
        try:
            history_data = {
                "appointment_id": original["id"],
                "original_start": original["scheduled_start"],
                "original_end": original["scheduled_end"],
                "new_start": updates.get("scheduled_start"),
                "new_end": updates.get("scheduled_end"),
                "rescheduled_at": datetime.utcnow().isoformat(),
            }

            self.supabase.table("appointment_history").insert(history_data).execute()

        except Exception as e:
            logger.error(f"Error tracking reschedule: {str(e)}")

    def _create_follow_up_task(self, appointment: dict):
        """Create follow-up task for completed appointment"""
        try:
            follow_up_data = {
                "appointment_id": appointment["id"],
                "customer_id": appointment["customer_id"],
                "team_member_id": appointment["team_member_id"],
                "task_type": "appointment_follow_up",
                "due_date": (datetime.utcnow() + timedelta(days=3)).isoformat(),
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
            }

            self.supabase.table("tasks").insert(follow_up_data).execute()

        except Exception as e:
            logger.error(f"Error creating follow-up task: {str(e)}")

    def _update_availability_cache(self, team_member_id: str, date: datetime.date):
        """Update availability cache for a team member"""
        try:
            # Get all appointments for the date
            start_of_day = datetime.combine(date, datetime.min.time())
            end_of_day = datetime.combine(date, datetime.max.time())

            result = (
                self.supabase.table("appointments")
                .select("id", "scheduled_start", "scheduled_end")
                .eq("team_member_id", team_member_id)
                .in_("status", [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
                .gte("scheduled_start", start_of_day.isoformat())
                .lte("scheduled_start", end_of_day.isoformat())
                .execute()
            )

            # Format for cache
            slots = []
            for apt in result.data:
                slots.append(
                    {"id": apt["id"], "start": apt["scheduled_start"], "end": apt["scheduled_end"]}
                )

            # Store in cache
            cache_key = f"availability:{team_member_id}:{date}"
            self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(slots))

        except Exception as e:
            logger.error(f"Error updating availability cache: {str(e)}")

    def _clear_availability_cache(self, team_member_id: str, date: datetime):
        """Clear availability cache"""
        try:
            cache_key = f"availability:{team_member_id}:{date.date()}"
            self.redis_client.delete(cache_key)

        except Exception as e:
            logger.error(f"Error clearing availability cache: {str(e)}")

    def init_google_calendar_service(self, credentials: Credentials):
        """Initialize Google Calendar service with credentials"""
        try:
            self._calendar_service = build("calendar", "v3", credentials=credentials)
            return True
        except Exception as e:
            logger.error(f"Error initializing Google Calendar service: {str(e)}")
            return False

    def get_oauth_flow(self) -> Flow:
        """Get Google OAuth flow for calendar access"""
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.google_client_id,
                        "client_secret": self.google_client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.google_redirect_uri],
                    }
                },
                scopes=self.google_scopes,
            )
            flow.redirect_uri = self.google_redirect_uri
            return flow
        except Exception as e:
            logger.error(f"Error creating OAuth flow: {str(e)}")
            return None


# Create singleton instance
appointments_service = AppointmentsService()
