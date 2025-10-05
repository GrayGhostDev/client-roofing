"""
iSwitch Roofs CRM - Notification SQLAlchemy Model
Version: 1.0.0

Notification data model for tracking all sent notifications.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy import Enum as SQLEnum

from app.models.base import BaseModel


class NotificationChannel(str, Enum):
    """Notification delivery channels."""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class NotificationPriority(str, Enum):
    """Notification priority levels."""

    URGENT = "urgent"  # Immediate delivery
    HIGH = "high"  # Within 5 minutes
    NORMAL = "normal"  # Within 30 minutes
    LOW = "low"  # Batched delivery


class NotificationStatus(str, Enum):
    """Notification delivery status."""

    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    OPENED = "opened"
    CLICKED = "clicked"
    UNSUBSCRIBED = "unsubscribed"


class NotificationType(str, Enum):
    """Types of notifications."""

    # Lead notifications
    LEAD_CREATED = "lead_created"
    LEAD_HOT = "lead_hot"
    LEAD_ASSIGNED = "lead_assigned"
    LEAD_CONVERTED = "lead_converted"

    # Customer notifications
    CUSTOMER_CREATED = "customer_created"
    CUSTOMER_UPDATED = "customer_updated"
    CUSTOMER_MILESTONE = "customer_milestone"

    # Appointment notifications
    APPOINTMENT_SCHEDULED = "appointment_scheduled"
    APPOINTMENT_REMINDER = "appointment_reminder"
    APPOINTMENT_RESCHEDULED = "appointment_rescheduled"
    APPOINTMENT_CANCELLED = "appointment_cancelled"

    # Project notifications
    PROJECT_CREATED = "project_created"
    PROJECT_STARTED = "project_started"
    PROJECT_COMPLETED = "project_completed"
    PROJECT_DELAYED = "project_delayed"

    # Team notifications
    TEAM_ASSIGNMENT = "team_assignment"
    TEAM_MENTION = "team_mention"
    TEAM_REVIEW_REQUEST = "team_review_request"

    # System notifications
    SYSTEM_ALERT = "system_alert"
    SYSTEM_MAINTENANCE = "system_maintenance"
    SYSTEM_UPDATE = "system_update"

    # Marketing notifications
    MARKETING_CAMPAIGN = "marketing_campaign"
    MARKETING_NEWSLETTER = "marketing_newsletter"
    MARKETING_PROMOTION = "marketing_promotion"

    # Review notifications
    REVIEW_REQUEST = "review_request"
    REVIEW_RECEIVED = "review_received"
    NPS_SURVEY = "nps_survey"


class Notification(BaseModel):
    """
    Notification SQLAlchemy model for tracking all sent notifications.
    """

    __tablename__ = "notifications"

    # Basic Information
    type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL)

    # Recipients
    recipient_id = Column(String(36), nullable=True, index=True)
    recipient_email = Column(String(255), nullable=True, index=True)
    recipient_phone = Column(String(20), nullable=True)
    recipient_name = Column(String(200), nullable=True)

    # Content
    subject = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    content_plain = Column(Text, nullable=True)
    template_id = Column(String(36), nullable=True)

    # Delivery Information
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING, index=True)
    scheduled_for = Column(DateTime, nullable=True, index=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)

    # Tracking
    external_id = Column(String(255), nullable=True)
    open_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)
    bounce_reason = Column(Text, nullable=True)

    # Retry Information
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_retry_at = Column(DateTime, nullable=True)

    # Related Entities
    related_lead_id = Column(String(36), nullable=True, index=True)
    related_customer_id = Column(String(36), nullable=True, index=True)
    related_project_id = Column(String(36), nullable=True, index=True)
    related_appointment_id = Column(String(36), nullable=True, index=True)

    # Metadata (stored as JSON string)
    metadata_json = Column(Text, nullable=True)


class NotificationTemplate(BaseModel):
    """
    Reusable notification templates.
    """

    __tablename__ = "notification_templates"

    name = Column(String(100), nullable=False)
    type = Column(SQLEnum(NotificationType), nullable=False)
    channel = Column(SQLEnum(NotificationChannel), nullable=False)

    # Content
    subject = Column(String(200), nullable=True)
    content_html = Column(Text, nullable=True)
    content_plain = Column(Text, nullable=False)

    # Settings
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    # Usage
    use_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)

    # Performance
    avg_open_rate = Column(String(10), nullable=True)  # Store as percentage string
    avg_click_rate = Column(String(10), nullable=True)  # Store as percentage string

    # Metadata
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)


# Pydantic schemas for API validation
class NotificationCreateSchema(BaseModel):
    """Schema for creating a new notification"""

    model_config = ConfigDict(from_attributes=True)

    type: NotificationType
    channel: NotificationChannel
    content: str
    priority: NotificationPriority = NotificationPriority.NORMAL

    # Recipients
    recipient_id: UUID | None = None
    recipient_email: EmailStr | None = None
    recipient_phone: str | None = None
    recipient_name: str | None = None

    # Content
    subject: str | None = None
    content_plain: str | None = None
    template_id: UUID | None = None

    # Scheduling
    scheduled_for: datetime | None = None

    # Related entities
    related_lead_id: UUID | None = None
    related_customer_id: UUID | None = None
    related_project_id: UUID | None = None
    related_appointment_id: UUID | None = None

    @field_validator("recipient_phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """Validate phone number format."""
        if not v:
            return v

        # Remove non-digits except +
        cleaned = "".join(c for c in v if c.isdigit() or c == "+")

        # Ensure it starts with + for international format
        if not cleaned.startswith("+"):
            # Assume US number if no country code
            if len(cleaned) == 10:
                cleaned = "+1" + cleaned
            elif len(cleaned) == 11 and cleaned.startswith("1"):
                cleaned = "+" + cleaned

        return cleaned


class NotificationUpdateSchema(BaseModel):
    """Schema for updating a notification"""

    model_config = ConfigDict(from_attributes=True)

    status: NotificationStatus | None = None
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    opened_at: datetime | None = None
    clicked_at: datetime | None = None
    bounce_reason: str | None = None
    external_id: str | None = None
    open_count: int | None = None
    click_count: int | None = None


class NotificationResponseSchema(BaseModel):
    """Schema for notification API response"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    type: NotificationType
    channel: NotificationChannel
    priority: NotificationPriority
    recipient_email: str | None = None
    recipient_phone: str | None = None
    recipient_name: str | None = None
    subject: str | None = None
    status: NotificationStatus
    scheduled_for: datetime | None = None
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class NotificationTemplateCreateSchema(BaseModel):
    """Schema for creating a notification template"""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=100)
    type: NotificationType
    channel: NotificationChannel
    content_plain: str

    subject: str | None = None
    content_html: str | None = None
    description: str | None = None
    category: str | None = None
    is_default: bool | None = False


class NotificationTemplateResponseSchema(BaseModel):
    """Schema for notification template API response"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: NotificationType
    channel: NotificationChannel
    subject: str | None = None
    content_plain: str
    is_active: bool = True
    is_default: bool = False
    use_count: int = 0
    created_at: datetime
    updated_at: datetime


class NotificationListFiltersSchema(BaseModel):
    """Filter parameters for notification list endpoint"""

    type: str | None = Field(None, description="Comma-separated types")
    channel: NotificationChannel | None = Field(None, description="Filter by channel")
    status: str | None = Field(None, description="Comma-separated statuses")
    priority: NotificationPriority | None = Field(None, description="Filter by priority")
    recipient_id: UUID | None = Field(None, description="Filter by recipient")
    date_from: datetime | None = Field(None, description="Filter from date")
    date_to: datetime | None = Field(None, description="Filter to date")
    needs_retry: bool | None = Field(None, description="Filter failed notifications needing retry")
