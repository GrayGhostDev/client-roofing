"""
iSwitch Roofs CRM - Interaction Model
Version: 1.0.0

Interaction data model for tracking all customer/lead touchpoints including calls, emails,
meetings, and notes.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

from app.models.base import BaseDBModel


class InteractionType(str, Enum):
    """Interaction type enumeration"""
    PHONE_CALL = "phone_call"
    EMAIL = "email"
    SMS = "sms"
    IN_PERSON_MEETING = "in_person_meeting"
    VIDEO_CALL = "video_call"
    SITE_VISIT = "site_visit"
    NOTE = "note"
    VOICEMAIL = "voicemail"
    SOCIAL_MEDIA = "social_media"
    LIVE_CHAT = "live_chat"


class InteractionDirection(str, Enum):
    """Interaction direction"""
    INBOUND = "inbound"    # Customer contacted us
    OUTBOUND = "outbound"  # We contacted customer
    INTERNAL = "internal"  # Internal note/communication


class InteractionOutcome(str, Enum):
    """Interaction outcome/result"""
    SUCCESSFUL = "successful"           # Connected and productive
    NO_ANSWER = "no_answer"            # Call/message not answered
    LEFT_VOICEMAIL = "left_voicemail"  # Voicemail left
    SCHEDULED_CALLBACK = "scheduled_callback"  # Arranged follow-up
    SCHEDULED_APPOINTMENT = "scheduled_appointment"  # Appointment set
    QUOTE_REQUESTED = "quote_requested"  # Customer requested quote
    OBJECTION_HANDLED = "objection_handled"  # Addressed concerns
    NOT_INTERESTED = "not_interested"    # Customer declined
    FOLLOW_UP_REQUIRED = "follow_up_required"  # Needs follow-up


class EntityType(str, Enum):
    """Entity type for interaction"""
    LEAD = "lead"
    CUSTOMER = "customer"
    PROJECT = "project"


class Interaction(BaseDBModel):
    """
    Interaction data model for tracking all customer/lead touchpoints.

    Records every communication and touchpoint with leads/customers,
    supporting the 16-touch campaign strategy and relationship management.
    """

    # Association (Required)
    entity_type: EntityType = Field(..., description="Type of entity (lead, customer, project)")
    entity_id: UUID = Field(..., description="ID of the associated lead/customer/project")

    # Interaction Details (Required)
    interaction_type: InteractionType = Field(..., description="Type of interaction")
    direction: InteractionDirection = Field(..., description="Direction of communication")
    subject: str = Field(..., min_length=1, max_length=200, description="Subject/title of interaction")

    # Content
    description: Optional[str] = Field(None, max_length=5000, description="Detailed description/notes")
    outcome: Optional[InteractionOutcome] = Field(None, description="Outcome of the interaction")

    # Metadata
    performed_by: UUID = Field(..., description="Team member who performed/logged interaction")
    interaction_date: datetime = Field(default_factory=datetime.utcnow, description="Date and time of interaction")
    duration_minutes: Optional[int] = Field(None, ge=0, description="Duration in minutes")

    # Follow-up
    requires_follow_up: bool = Field(default=False, description="Does this require follow-up?")
    follow_up_date: Optional[datetime] = Field(None, description="Scheduled follow-up date")
    follow_up_completed: bool = Field(default=False, description="Has follow-up been completed?")

    # Call Tracking (for phone interactions)
    call_recording_url: Optional[str] = Field(None, description="CallRail recording URL")
    call_duration_seconds: Optional[int] = Field(None, ge=0, description="Call duration in seconds")
    call_from_number: Optional[str] = Field(None, max_length=20, description="Caller phone number")
    call_to_number: Optional[str] = Field(None, max_length=20, description="Recipient phone number")
    call_sid: Optional[str] = Field(None, max_length=100, description="CallRail/Twilio call SID")

    # Email Tracking (for email interactions)
    email_from: Optional[str] = Field(None, max_length=255, description="Sender email")
    email_to: Optional[str] = Field(None, max_length=255, description="Recipient email")
    email_opened: bool = Field(default=False, description="Was email opened?")
    email_clicked: bool = Field(default=False, description="Did recipient click links?")

    # Sentiment & Quality
    sentiment: Optional[str] = Field(None, max_length=20, description="positive, neutral, negative")
    quality_score: Optional[int] = Field(None, ge=0, le=10, description="Quality score (0-10)")

    # Tags
    tags: Optional[str] = Field(None, description="Comma-separated tags for categorization")

    # Transcription (for calls/meetings)
    transcription: Optional[str] = Field(None, description="AI transcription of call/meeting")
    ai_summary: Optional[str] = Field(None, max_length=1000, description="AI-generated summary")

    @field_validator('sentiment')
    @classmethod
    def validate_sentiment(cls, v: Optional[str]) -> Optional[str]:
        """Validate sentiment is one of allowed values"""
        if v is None:
            return v

        allowed = ['positive', 'neutral', 'negative']
        if v.lower() not in allowed:
            raise ValueError(f"Sentiment must be one of: {', '.join(allowed)}")

        return v.lower()

    @property
    def is_call(self) -> bool:
        """Check if interaction is a phone call"""
        return self.interaction_type in [
            InteractionType.PHONE_CALL,
            InteractionType.VOICEMAIL
        ]

    @property
    def is_email(self) -> bool:
        """Check if interaction is an email"""
        return self.interaction_type == InteractionType.EMAIL

    @property
    def is_meeting(self) -> bool:
        """Check if interaction is a meeting"""
        return self.interaction_type in [
            InteractionType.IN_PERSON_MEETING,
            InteractionType.VIDEO_CALL,
            InteractionType.SITE_VISIT
        ]

    @property
    def needs_follow_up(self) -> bool:
        """Check if follow-up is needed and not yet completed"""
        return self.requires_follow_up and not self.follow_up_completed


class InteractionCreate(BaseModel):
    """Schema for creating a new interaction"""
    entity_type: EntityType
    entity_id: UUID
    interaction_type: InteractionType
    direction: InteractionDirection
    subject: str = Field(..., min_length=1, max_length=200)

    # Optional fields
    description: Optional[str] = None
    outcome: Optional[InteractionOutcome] = None
    performed_by: UUID  # Required
    interaction_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None

    requires_follow_up: Optional[bool] = False
    follow_up_date: Optional[datetime] = None

    # Call tracking
    call_recording_url: Optional[str] = None
    call_duration_seconds: Optional[int] = None
    call_from_number: Optional[str] = None
    call_to_number: Optional[str] = None
    call_sid: Optional[str] = None

    # Email tracking
    email_from: Optional[str] = None
    email_to: Optional[str] = None

    sentiment: Optional[str] = None
    tags: Optional[str] = None


class InteractionUpdate(BaseModel):
    """Schema for updating an interaction"""
    subject: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    outcome: Optional[InteractionOutcome] = None
    duration_minutes: Optional[int] = None
    requires_follow_up: Optional[bool] = None
    follow_up_date: Optional[datetime] = None
    follow_up_completed: Optional[bool] = None
    sentiment: Optional[str] = None
    quality_score: Optional[int] = Field(None, ge=0, le=10)
    tags: Optional[str] = None
    transcription: Optional[str] = None
    ai_summary: Optional[str] = None


class InteractionResponse(BaseModel):
    """Schema for interaction API response"""
    data: Interaction
    entity_data: Optional[dict] = None  # Lead/Customer/Project data
    performed_by_data: Optional[dict] = None  # Team member data


class InteractionListFilters(BaseModel):
    """Filter parameters for interaction list endpoint"""
    entity_type: Optional[EntityType] = Field(None, description="Filter by entity type")
    entity_id: Optional[UUID] = Field(None, description="Filter by specific entity")
    interaction_type: Optional[str] = Field(None, description="Comma-separated types")
    direction: Optional[InteractionDirection] = Field(None, description="Filter by direction")
    outcome: Optional[str] = Field(None, description="Comma-separated outcomes")
    performed_by: Optional[UUID] = Field(None, description="Filter by team member")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    requires_follow_up: Optional[bool] = Field(None, description="Filter items needing follow-up")
    sentiment: Optional[str] = Field(None, description="Filter by sentiment")
    tags: Optional[str] = Field(None, description="Filter by tags")
