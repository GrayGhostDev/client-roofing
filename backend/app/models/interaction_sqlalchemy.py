"""
iSwitch Roofs CRM - Interaction SQLAlchemy Model
Version: 1.0.0

Interaction data model for tracking all customer/lead touchpoints including calls, emails,
meetings, and notes.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel, ConfigDict, Field, field_validator
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy import Enum as SQLEnum

from app.models.base import BaseModel


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


class Interaction(BaseModel):
    """
    Interaction SQLAlchemy model for tracking all customer/lead touchpoints.

    Records every communication and touchpoint with leads/customers,
    supporting the 16-touch campaign strategy and relationship management.
    """

    __tablename__ = "interactions"
    __table_args__ = {'extend_existing': True}

    # Association (Required)
    entity_type = Column(SQLEnum(EntityType), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)

    # Interaction Details (Required)
    interaction_type = Column(SQLEnum(InteractionType), nullable=False)
    direction = Column(SQLEnum(InteractionDirection), nullable=False)
    subject = Column(String(200), nullable=False)

    # Content
    description = Column(Text, nullable=True)
    outcome = Column(SQLEnum(InteractionOutcome), nullable=True)

    # Metadata
    performed_by = Column(String(36), nullable=False, index=True)
    interaction_date = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, nullable=True)

    # Follow-up
    requires_follow_up = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True, index=True)
    follow_up_completed = Column(Boolean, default=False)

    # Call Tracking (for phone interactions)
    call_recording_url = Column(Text, nullable=True)
    call_duration_seconds = Column(Integer, nullable=True)
    call_from_number = Column(String(20), nullable=True)
    call_to_number = Column(String(20), nullable=True)
    call_sid = Column(String(100), nullable=True)

    # Email Tracking (for email interactions)
    email_from = Column(String(255), nullable=True)
    email_to = Column(String(255), nullable=True)
    email_opened = Column(Boolean, default=False)
    email_clicked = Column(Boolean, default=False)

    # Sentiment & Quality
    sentiment = Column(String(20), nullable=True)
    quality_score = Column(Integer, nullable=True)

    # Tags
    tags = Column(Text, nullable=True)

    # Transcription (for calls/meetings)
    transcription = Column(Text, nullable=True)
    ai_summary = Column(String(1000), nullable=True)

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


# Pydantic schemas for API validation
class InteractionCreateSchema(PydanticBaseModel):
    """Schema for creating a new interaction"""

    model_config = ConfigDict(from_attributes=True)

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


class InteractionUpdateSchema(PydanticBaseModel):
    """Schema for updating an interaction"""

    model_config = ConfigDict(from_attributes=True)

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


class InteractionResponseSchema(PydanticBaseModel):
    """Schema for interaction API response"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_type: EntityType
    entity_id: str
    interaction_type: InteractionType
    direction: InteractionDirection
    subject: str
    description: str | None = None
    outcome: InteractionOutcome | None = None
    performed_by: str
    interaction_date: datetime
    duration_minutes: int | None = None
    requires_follow_up: bool = False
    follow_up_date: datetime | None = None
    sentiment: str | None = None
    created_at: datetime
    updated_at: datetime


class InteractionListFiltersSchema(PydanticBaseModel):
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
