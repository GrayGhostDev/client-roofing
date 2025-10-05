"""
iSwitch Roofs CRM - Appointment Model
Version: 1.0.0

Appointment data model for scheduling inspections, consultations, and follow-ups.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from enum import Enum

from app.models.base import BaseDBModel


class AppointmentType(str, Enum):
    """Appointment type enumeration"""
    INITIAL_CONSULTATION = "initial_consultation"
    ROOF_INSPECTION = "roof_inspection"
    QUOTE_PRESENTATION = "quote_presentation"
    CONTRACT_SIGNING = "contract_signing"
    PROJECT_KICKOFF = "project_kickoff"
    SITE_VISIT = "site_visit"
    PROGRESS_CHECK = "progress_check"
    FINAL_WALKTHROUGH = "final_walkthrough"
    FOLLOW_UP_MEETING = "follow_up_meeting"
    EMERGENCY_INSPECTION = "emergency_inspection"


class AppointmentStatus(str, Enum):
    """Appointment status"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class ReminderStatus(str, Enum):
    """Reminder status"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class Appointment(BaseDBModel):
    """
    Appointment data model for scheduling and managing customer appointments.

    Supports scheduling, reminders, calendar integration, and completion tracking.
    """

    # Association (Required)
    entity_type: str = Field(..., description="lead or customer or project")
    entity_id: UUID = Field(..., description="ID of associated lead/customer/project")

    # Appointment Details (Required)
    appointment_type: AppointmentType = Field(..., description="Type of appointment")
    status: AppointmentStatus = Field(default=AppointmentStatus.SCHEDULED, description="Current status")
    title: str = Field(..., min_length=1, max_length=200, description="Appointment title")

    # Scheduling
    scheduled_date: datetime = Field(..., description="Scheduled date and time")
    duration_minutes: int = Field(..., ge=15, le=480, description="Duration in minutes")
    end_time: Optional[datetime] = Field(None, description="Calculated end time")

    # Location
    location: Optional[str] = Field(None, max_length=500, description="Meeting location or address")
    is_virtual: bool = Field(default=False, description="Is this a virtual meeting?")
    meeting_url: Optional[str] = Field(None, description="Virtual meeting URL (Zoom, Teams, etc.)")

    # Participants
    assigned_to: UUID = Field(..., description="Assigned team member")
    customer_id: Optional[UUID] = Field(None, description="Customer/lead attending")
    additional_attendees: Optional[str] = Field(None, description="Additional attendees (comma-separated names)")

    # Description & Notes
    description: Optional[str] = Field(None, max_length=2000, description="Appointment description")
    preparation_notes: Optional[str] = Field(None, max_length=1000, description="Preparation requirements")
    outcome_notes: Optional[str] = Field(None, max_length=2000, description="Notes after completion")

    # Reminders
    send_reminder: bool = Field(default=True, description="Send reminder notifications")
    reminder_hours_before: int = Field(default=24, ge=1, le=168, description="Hours before to send reminder")
    reminder_sent: bool = Field(default=False, description="Has reminder been sent?")
    reminder_sent_at: Optional[datetime] = Field(None, description="When reminder was sent")
    reminder_status: ReminderStatus = Field(default=ReminderStatus.PENDING, description="Reminder status")

    # Confirmation
    confirmation_requested: bool = Field(default=False, description="Confirmation requested from customer")
    confirmed_by_customer: bool = Field(default=False, description="Has customer confirmed?")
    confirmed_at: Optional[datetime] = Field(None, description="When customer confirmed")

    # Completion
    actual_start_time: Optional[datetime] = Field(None, description="Actual start time")
    actual_end_time: Optional[datetime] = Field(None, description="Actual end time")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")

    # Cancellation/Rescheduling
    cancelled_at: Optional[datetime] = Field(None, description="Cancellation timestamp")
    cancellation_reason: Optional[str] = Field(None, max_length=500, description="Reason for cancellation")
    rescheduled_from: Optional[UUID] = Field(None, description="Original appointment ID if rescheduled")
    rescheduled_to: Optional[UUID] = Field(None, description="New appointment ID if rescheduled")

    # Calendar Integration
    google_calendar_event_id: Optional[str] = Field(None, description="Google Calendar event ID")
    outlook_calendar_event_id: Optional[str] = Field(None, description="Outlook Calendar event ID")

    # Follow-up
    follow_up_required: bool = Field(default=False, description="Requires follow-up appointment")
    follow_up_appointment_id: Optional[UUID] = Field(None, description="Follow-up appointment ID")

    @field_validator('entity_type')
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        """Validate entity type"""
        allowed = ['lead', 'customer', 'project']
        if v.lower() not in allowed:
            raise ValueError(f"Entity type must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator('scheduled_date')
    @classmethod
    def validate_scheduled_date(cls, v: datetime) -> datetime:
        """Ensure scheduled date is not in the past"""
        if v < datetime.utcnow():
            raise ValueError('Scheduled date cannot be in the past')
        return v

    def calculate_end_time(self) -> datetime:
        """Calculate end time based on start time and duration"""
        return self.scheduled_date + timedelta(minutes=self.duration_minutes)

    @property
    def is_upcoming(self) -> bool:
        """Check if appointment is upcoming (future and not cancelled)"""
        return (
            self.scheduled_date > datetime.utcnow() and
            self.status not in [AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED]
        )

    @property
    def is_today(self) -> bool:
        """Check if appointment is today"""
        today = datetime.utcnow().date()
        return self.scheduled_date.date() == today

    @property
    def is_overdue(self) -> bool:
        """Check if appointment time has passed but not completed"""
        return (
            self.scheduled_date < datetime.utcnow() and
            self.status not in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW]
        )

    @property
    def minutes_until_appointment(self) -> Optional[int]:
        """Calculate minutes until appointment"""
        if self.is_upcoming:
            delta = self.scheduled_date - datetime.utcnow()
            return int(delta.total_seconds() / 60)
        return None

    @property
    def needs_reminder(self) -> bool:
        """Check if reminder should be sent"""
        if not self.send_reminder or self.reminder_sent:
            return False

        hours_until = self.minutes_until_appointment / 60 if self.minutes_until_appointment else 0
        return 0 < hours_until <= self.reminder_hours_before


class AppointmentCreate(BaseModel):
    """Schema for creating a new appointment"""
    entity_type: str
    entity_id: UUID
    appointment_type: AppointmentType
    title: str = Field(..., min_length=1, max_length=200)
    scheduled_date: datetime
    duration_minutes: int = Field(..., ge=15, le=480)
    assigned_to: UUID

    # Optional fields
    location: Optional[str] = None
    is_virtual: Optional[bool] = False
    meeting_url: Optional[str] = None
    customer_id: Optional[UUID] = None
    additional_attendees: Optional[str] = None
    description: Optional[str] = None
    preparation_notes: Optional[str] = None
    send_reminder: Optional[bool] = True
    reminder_hours_before: Optional[int] = 24
    confirmation_requested: Optional[bool] = False


class AppointmentUpdate(BaseModel):
    """Schema for updating an appointment"""
    status: Optional[AppointmentStatus] = None
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    scheduled_date: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=480)
    location: Optional[str] = None
    meeting_url: Optional[str] = None
    assigned_to: Optional[UUID] = None
    description: Optional[str] = None
    preparation_notes: Optional[str] = None
    outcome_notes: Optional[str] = None
    confirmed_by_customer: Optional[bool] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    follow_up_required: Optional[bool] = None


class AppointmentReschedule(BaseModel):
    """Schema for rescheduling an appointment"""
    new_scheduled_date: datetime
    reason: Optional[str] = Field(None, max_length=500)
    send_notification: bool = Field(default=True)


class AppointmentResponse(BaseModel):
    """Schema for appointment API response"""
    data: Appointment
    entity_data: Optional[dict] = None  # Lead/Customer/Project data
    assigned_to_data: Optional[dict] = None  # Team member data


class AppointmentListFilters(BaseModel):
    """Filter parameters for appointment list endpoint"""
    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    entity_id: Optional[UUID] = Field(None, description="Filter by specific entity")
    appointment_type: Optional[str] = Field(None, description="Comma-separated types")
    status: Optional[str] = Field(None, description="Comma-separated statuses")
    assigned_to: Optional[UUID] = Field(None, description="Filter by team member")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    is_virtual: Optional[bool] = Field(None, description="Filter virtual meetings")
    needs_confirmation: Optional[bool] = Field(None, description="Filter unconfirmed appointments")
    is_today: Optional[bool] = Field(None, description="Filter today's appointments")
    is_upcoming: Optional[bool] = Field(None, description="Filter upcoming appointments")
