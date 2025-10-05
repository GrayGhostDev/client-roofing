"""
iSwitch Roofs CRM - Interaction Model
Version: 1.0.0

Interaction data model for tracking all customer/lead touchpoints including calls, emails,
meetings, and notes.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

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

    INBOUND = "inbound"  # Customer contacted us
    OUTBOUND = "outbound"  # We contacted customer
    INTERNAL = "internal"  # Internal note/communication


class InteractionOutcome(str, Enum):
    """Interaction outcome/result"""

    SUCCESSFUL = "successful"  # Connected and productive
    NO_ANSWER = "no_answer"  # Call/message not answered
    LEFT_VOICEMAIL = "left_voicemail"  # Voicemail left
    SCHEDULED_CALLBACK = "scheduled_callback"  # Arranged follow-up
    SCHEDULED_APPOINTMENT = "scheduled_appointment"  # Appointment set
    QUOTE_REQUESTED = "quote_requested"  # Customer requested quote
    OBJECTION_HANDLED = "objection_handled"  # Addressed concerns
    NOT_INTERESTED = "not_interested"  # Customer declined
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
    subject: str = Field(
        ..., min_length=1, max_length=200, description="Subject/title of interaction"
    )

    # Content
    description: str | None = Field(None, max_length=5000, description="Detailed description/notes")
    outcome: InteractionOutcome | None = Field(None, description="Outcome of the interaction")

    # Metadata
    performed_by: UUID = Field(..., description="Team member who performed/logged interaction")
    interaction_date: datetime = Field(
        default_factory=datetime.utcnow, description="Date and time of interaction"
    )
    duration_minutes: int | None = Field(None, ge=0, description="Duration in minutes")

    # Follow-up
    requires_follow_up: bool = Field(default=False, description="Does this require follow-up?")
    follow_up_date: datetime | None = Field(None, description="Scheduled follow-up date")
    follow_up_completed: bool = Field(default=False, description="Has follow-up been completed?")

    # Call Tracking (for phone interactions)
    call_recording_url: str | None = Field(None, description="CallRail recording URL")
    call_duration_seconds: int | None = Field(None, ge=0, description="Call duration in seconds")
    call_from_number: str | None = Field(None, max_length=20, description="Caller phone number")
    call_to_number: str | None = Field(None, max_length=20, description="Recipient phone number")
    call_sid: str | None = Field(None, max_length=100, description="CallRail/Twilio call SID")

    # Email Tracking (for email interactions)
    email_from: str | None = Field(None, max_length=255, description="Sender email")
    email_to: str | None = Field(None, max_length=255, description="Recipient email")
    email_opened: bool = Field(default=False, description="Was email opened?")
    email_clicked: bool = Field(default=False, description="Did recipient click links?")

    # Sentiment & Quality
    sentiment: str | None = Field(None, max_length=20, description="positive, neutral, negative")
    quality_score: int | None = Field(None, ge=0, le=10, description="Quality score (0-10)")

    # Tags
    tags: str | None = Field(None, description="Comma-separated tags for categorization")

    # Transcription (for calls/meetings)
    transcription: str | None = Field(None, description="AI transcription of call/meeting")
    ai_summary: str | None = Field(None, max_length=1000, description="AI-generated summary")

    @field_validator("sentiment")
    @classmethod
    def validate_sentiment(cls, v: str | None) -> str | None:
        """Validate sentiment is one of allowed values"""
        if v is None:
            return v

        allowed = ["positive", "neutral", "negative"]
        if v.lower() not in allowed:
            raise ValueError(f"Sentiment must be one of: {', '.join(allowed)}")

        return v.lower()

    @property
    def is_call(self) -> bool:
        """Check if interaction is a phone call"""
        return self.interaction_type in [InteractionType.PHONE_CALL, InteractionType.VOICEMAIL]

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
            InteractionType.SITE_VISIT,
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
    description: str | None = None
    outcome: InteractionOutcome | None = None
    performed_by: UUID  # Required
    interaction_date: datetime | None = None
    duration_minutes: int | None = None

    requires_follow_up: bool | None = False
    follow_up_date: datetime | None = None

    # Call tracking
    call_recording_url: str | None = None
    call_duration_seconds: int | None = None
    call_from_number: str | None = None
    call_to_number: str | None = None
    call_sid: str | None = None

    # Email tracking
    email_from: str | None = None
    email_to: str | None = None

    sentiment: str | None = None
    tags: str | None = None


class InteractionUpdate(BaseModel):
    """Schema for updating an interaction"""

    subject: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    outcome: InteractionOutcome | None = None
    duration_minutes: int | None = None
    requires_follow_up: bool | None = None
    follow_up_date: datetime | None = None
    follow_up_completed: bool | None = None
    sentiment: str | None = None
    quality_score: int | None = Field(None, ge=0, le=10)
    tags: str | None = None
    transcription: str | None = None
    ai_summary: str | None = None


class InteractionResponse(BaseModel):
    """Schema for interaction API response"""

    data: Interaction
    entity_data: dict | None = None  # Lead/Customer/Project data
    performed_by_data: dict | None = None  # Team member data


class InteractionListFilters(BaseModel):
    """Filter parameters for interaction list endpoint"""

    entity_type: EntityType | None = Field(None, description="Filter by entity type")
    entity_id: UUID | None = Field(None, description="Filter by specific entity")
    interaction_type: str | None = Field(None, description="Comma-separated types")
    direction: InteractionDirection | None = Field(None, description="Filter by direction")
    outcome: str | None = Field(None, description="Comma-separated outcomes")
    performed_by: UUID | None = Field(None, description="Filter by team member")
    date_from: datetime | None = Field(None, description="Filter from date")
    date_to: datetime | None = Field(None, description="Filter to date")
    requires_follow_up: bool | None = Field(None, description="Filter items needing follow-up")
    sentiment: str | None = Field(None, description="Filter by sentiment")
    tags: str | None = Field(None, description="Filter by tags")
