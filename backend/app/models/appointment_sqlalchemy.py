"""
iSwitch Roofs CRM - Appointment SQLAlchemy Model
Version: 1.0.0

Appointment data model for scheduling inspections, consultations, and follow-ups.
"""

from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel, ConfigDict, Field, field_validator
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy import Enum as SQLEnum

from app.models.base import BaseModel


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


class Appointment(BaseModel):
    """
    Appointment SQLAlchemy model for scheduling and managing customer appointments.

    Supports scheduling, reminders, calendar integration, and completion tracking.
    """

    __tablename__ = "appointments"
    __table_args__ = {'extend_existing': True}

    # Association (Required)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=False, index=True)

    # Appointment Details (Required)
    appointment_type = Column(SQLEnum(AppointmentType), nullable=False)
    status = Column(SQLEnum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)
    title = Column(String(200), nullable=False)

    # Scheduling
    scheduled_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    end_time = Column(DateTime, nullable=True)

    # Location
    location = Column(String(500), nullable=True)
    is_virtual = Column(Boolean, default=False)
    meeting_url = Column(Text, nullable=True)

    # Participants
    assigned_to = Column(String(36), nullable=False, index=True)
    customer_id = Column(String(36), nullable=True, index=True)
    additional_attendees = Column(Text, nullable=True)

    # Description & Notes
    description = Column(Text, nullable=True)
    preparation_notes = Column(String(1000), nullable=True)
    outcome_notes = Column(Text, nullable=True)

    # Reminders
    send_reminder = Column(Boolean, default=True)
    reminder_hours_before = Column(Integer, default=24)
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime, nullable=True)
    reminder_status = Column(SQLEnum(ReminderStatus), default=ReminderStatus.PENDING)

    # Confirmation
    confirmation_requested = Column(Boolean, default=False)
    confirmed_by_customer = Column(Boolean, default=False)
    confirmed_at = Column(DateTime, nullable=True)

    # Completion
    actual_start_time = Column(DateTime, nullable=True)
    actual_end_time = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Cancellation/Rescheduling
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(String(500), nullable=True)
    rescheduled_from = Column(String(36), nullable=True)
    rescheduled_to = Column(String(36), nullable=True)

    # Calendar Integration
    google_calendar_event_id = Column(String(255), nullable=True)
    outlook_calendar_event_id = Column(String(255), nullable=True)

    # Follow-up
    follow_up_required = Column(Boolean, default=False)
    follow_up_appointment_id = Column(String(36), nullable=True)

    def calculate_end_time(self) -> datetime:
        """Calculate end time based on start time and duration"""
        return self.scheduled_date + timedelta(minutes=self.duration_minutes)

    @property
    def is_upcoming(self) -> bool:
        """Check if appointment is upcoming (future and not cancelled)"""
        return self.scheduled_date > datetime.utcnow() and self.status not in [
            AppointmentStatus.CANCELLED,
            AppointmentStatus.COMPLETED,
        ]

    @property
    def is_today(self) -> bool:
        """Check if appointment is today"""
        today = datetime.utcnow().date()
        return self.scheduled_date.date() == today

    @property
    def is_overdue(self) -> bool:
        """Check if appointment time has passed but not completed"""
        return self.scheduled_date < datetime.utcnow() and self.status not in [
            AppointmentStatus.COMPLETED,
            AppointmentStatus.CANCELLED,
            AppointmentStatus.NO_SHOW,
        ]

    @property
    def minutes_until_appointment(self) -> int | None:
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


# Pydantic schemas for API validation
class AppointmentCreateSchema(PydanticBaseModel):
    """Schema for creating a new appointment"""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str
    entity_id: UUID
    appointment_type: AppointmentType
    title: str = Field(..., min_length=1, max_length=200)
    scheduled_date: datetime
    duration_minutes: int = Field(..., ge=15, le=480)
    assigned_to: UUID

    # Optional fields
    location: str | None = None
    is_virtual: bool | None = False
    meeting_url: str | None = None
    customer_id: UUID | None = None
    additional_attendees: str | None = None
    description: str | None = None
    preparation_notes: str | None = None
    send_reminder: bool | None = True
    reminder_hours_before: int | None = 24
    confirmation_requested: bool | None = False

    @field_validator("entity_type")
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        """Validate entity type"""
        allowed = ["lead", "customer", "project"]
        if v.lower() not in allowed:
            raise ValueError(f"Entity type must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator("scheduled_date")
    @classmethod
    def validate_scheduled_date(cls, v: datetime) -> datetime:
        """Ensure scheduled date is not in the past"""
        if v < datetime.utcnow():
            raise ValueError("Scheduled date cannot be in the past")
        return v


class AppointmentUpdateSchema(PydanticBaseModel):
    """Schema for updating an appointment"""

    model_config = ConfigDict(from_attributes=True)

    status: AppointmentStatus | None = None
    title: str | None = Field(None, min_length=1, max_length=200)
    scheduled_date: datetime | None = None
    duration_minutes: int | None = Field(None, ge=15, le=480)
    location: str | None = None
    meeting_url: str | None = None
    assigned_to: UUID | None = None
    description: str | None = None
    preparation_notes: str | None = None
    outcome_notes: str | None = None
    confirmed_by_customer: bool | None = None
    actual_start_time: datetime | None = None
    actual_end_time: datetime | None = None
    cancellation_reason: str | None = None
    follow_up_required: bool | None = None


class AppointmentRescheduleSchema(PydanticBaseModel):
    """Schema for rescheduling an appointment"""

    new_scheduled_date: datetime
    reason: str | None = Field(None, max_length=500)
    send_notification: bool = Field(default=True)


class AppointmentResponseSchema(PydanticBaseModel):
    """Schema for appointment API response"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_type: str
    entity_id: str
    appointment_type: AppointmentType
    status: AppointmentStatus
    title: str
    scheduled_date: datetime
    duration_minutes: int
    assigned_to: str
    location: str | None = None
    is_virtual: bool = False
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class AppointmentListFiltersSchema(PydanticBaseModel):
    """Filter parameters for appointment list endpoint"""

    entity_type: str | None = Field(None, description="Filter by entity type")
    entity_id: UUID | None = Field(None, description="Filter by specific entity")
    appointment_type: str | None = Field(None, description="Comma-separated types")
    status: str | None = Field(None, description="Comma-separated statuses")
    assigned_to: UUID | None = Field(None, description="Filter by team member")
    date_from: datetime | None = Field(None, description="Filter from date")
    date_to: datetime | None = Field(None, description="Filter to date")
    is_virtual: bool | None = Field(None, description="Filter virtual meetings")
    needs_confirmation: bool | None = Field(None, description="Filter unconfirmed appointments")
    is_today: bool | None = Field(None, description="Filter today's appointments")
    is_upcoming: bool | None = Field(None, description="Filter upcoming appointments")
