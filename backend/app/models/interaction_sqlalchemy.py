"""
iSwitch Roofs CRM - Interaction SQLAlchemy Model
Version: 1.0.0

Interaction data model for tracking all customer/lead touchpoints including calls, emails,
meetings, and notes.
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, Enum as SQLEnum
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

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


class Interaction(BaseModel):
    """
    Interaction SQLAlchemy model for tracking all customer/lead touchpoints.

    Records every communication and touchpoint with leads/customers,
    supporting the 16-touch campaign strategy and relationship management.
    """
    __tablename__ = 'interactions'

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


# Pydantic schemas for API validation
class InteractionCreateSchema(BaseModel):
    """Schema for creating a new interaction"""
    model_config = ConfigDict(from_attributes=True)

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


class InteractionUpdateSchema(BaseModel):
    """Schema for updating an interaction"""
    model_config = ConfigDict(from_attributes=True)

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


class InteractionResponseSchema(BaseModel):
    """Schema for interaction API response"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_type: EntityType
    entity_id: str
    interaction_type: InteractionType
    direction: InteractionDirection
    subject: str
    description: Optional[str] = None
    outcome: Optional[InteractionOutcome] = None
    performed_by: str
    interaction_date: datetime
    duration_minutes: Optional[int] = None
    requires_follow_up: bool = False
    follow_up_date: Optional[datetime] = None
    sentiment: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class InteractionListFiltersSchema(BaseModel):
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