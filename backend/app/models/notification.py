"""
Notification Models
Version: 1.0.0

Data models for notification system including templates, logs, and preferences.
"""

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

from app.models.base import BaseDBModel


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    URGENT = "urgent"      # Immediate delivery
    HIGH = "high"          # Within 5 minutes
    NORMAL = "normal"      # Within 30 minutes
    LOW = "low"            # Batched delivery


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


class Notification(BaseDBModel):
    """
    Notification model for tracking all sent notifications.
    """

    # Basic Information
    type: NotificationType = Field(..., description="Type of notification")
    channel: NotificationChannel = Field(..., description="Delivery channel")
    priority: NotificationPriority = Field(
        default=NotificationPriority.NORMAL,
        description="Notification priority"
    )

    # Recipients
    recipient_id: Optional[UUID] = Field(None, description="User ID of recipient")
    recipient_email: Optional[EmailStr] = Field(None, description="Email address")
    recipient_phone: Optional[str] = Field(None, description="Phone number")
    recipient_name: Optional[str] = Field(None, description="Recipient name")

    # Content
    subject: Optional[str] = Field(None, max_length=200, description="Email subject or SMS preview")
    content: str = Field(..., description="Notification content (HTML or plain text)")
    content_plain: Optional[str] = Field(None, description="Plain text version")
    template_id: Optional[UUID] = Field(None, description="Template used")
    template_variables: Optional[Dict[str, Any]] = Field(None, description="Template variables")

    # Delivery Information
    status: NotificationStatus = Field(
        default=NotificationStatus.PENDING,
        description="Current delivery status"
    )
    scheduled_for: Optional[datetime] = Field(None, description="Scheduled delivery time")
    sent_at: Optional[datetime] = Field(None, description="Actual sent timestamp")
    delivered_at: Optional[datetime] = Field(None, description="Delivery confirmation timestamp")
    opened_at: Optional[datetime] = Field(None, description="First opened timestamp")
    clicked_at: Optional[datetime] = Field(None, description="First click timestamp")

    # Tracking
    external_id: Optional[str] = Field(None, description="External service message ID")
    open_count: int = Field(default=0, ge=0, description="Number of opens")
    click_count: int = Field(default=0, ge=0, description="Number of clicks")
    bounce_reason: Optional[str] = Field(None, description="Reason for bounce/failure")

    # Retry Information
    retry_count: int = Field(default=0, ge=0, description="Number of retry attempts")
    max_retries: int = Field(default=3, ge=0, description="Maximum retry attempts")
    next_retry_at: Optional[datetime] = Field(None, description="Next retry timestamp")

    # Related Entities
    related_lead_id: Optional[UUID] = Field(None, description="Related lead ID")
    related_customer_id: Optional[UUID] = Field(None, description="Related customer ID")
    related_project_id: Optional[UUID] = Field(None, description="Related project ID")
    related_appointment_id: Optional[UUID] = Field(None, description="Related appointment ID")

    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    tags: Optional[List[str]] = Field(None, description="Notification tags")

    @field_validator('recipient_phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if not v:
            return v

        # Remove non-digits except +
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')

        # Ensure it starts with + for international format
        if not cleaned.startswith('+'):
            # Assume US number if no country code
            if len(cleaned) == 10:
                cleaned = '+1' + cleaned
            elif len(cleaned) == 11 and cleaned.startswith('1'):
                cleaned = '+' + cleaned

        return cleaned


class NotificationTemplate(BaseDBModel):
    """
    Reusable notification templates.
    """

    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    type: NotificationType = Field(..., description="Notification type")
    channel: NotificationChannel = Field(..., description="Target channel")

    # Content
    subject: Optional[str] = Field(None, max_length=200, description="Email subject template")
    content_html: Optional[str] = Field(None, description="HTML content template")
    content_plain: str = Field(..., description="Plain text content template")

    # Variables
    required_variables: List[str] = Field(default_factory=list, description="Required template variables")
    optional_variables: List[str] = Field(default_factory=list, description="Optional template variables")
    default_values: Optional[Dict[str, Any]] = Field(None, description="Default variable values")

    # Settings
    is_active: bool = Field(default=True, description="Template active status")
    is_default: bool = Field(default=False, description="Default template for type")

    # Usage
    use_count: int = Field(default=0, ge=0, description="Number of times used")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")

    # Performance
    avg_open_rate: Optional[float] = Field(None, ge=0.0, le=100.0, description="Average open rate %")
    avg_click_rate: Optional[float] = Field(None, ge=0.0, le=100.0, description="Average click rate %")

    # Metadata
    description: Optional[str] = Field(None, description="Template description")
    category: Optional[str] = Field(None, max_length=50, description="Template category")
    tags: Optional[List[str]] = Field(None, description="Template tags")


class NotificationPreferences(BaseDBModel):
    """
    User notification preferences.
    """

    user_id: UUID = Field(..., description="User ID")
    user_email: EmailStr = Field(..., description="User email")
    user_phone: Optional[str] = Field(None, description="User phone")

    # Channel Preferences
    email_enabled: bool = Field(default=True, description="Email notifications enabled")
    sms_enabled: bool = Field(default=False, description="SMS notifications enabled")
    push_enabled: bool = Field(default=True, description="Push notifications enabled")
    in_app_enabled: bool = Field(default=True, description="In-app notifications enabled")

    # Type Preferences (by notification type)
    enabled_types: List[NotificationType] = Field(
        default_factory=lambda: list(NotificationType),
        description="Enabled notification types"
    )
    disabled_types: List[NotificationType] = Field(
        default_factory=list,
        description="Explicitly disabled types"
    )

    # Delivery Preferences
    quiet_hours_enabled: bool = Field(default=False, description="Enable quiet hours")
    quiet_hours_start: Optional[str] = Field(None, description="Quiet hours start (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="Quiet hours end (HH:MM)")
    timezone: str = Field(default="America/Detroit", description="User timezone")

    # Frequency Limits
    daily_email_limit: Optional[int] = Field(None, ge=0, description="Max emails per day")
    daily_sms_limit: Optional[int] = Field(None, ge=0, description="Max SMS per day")

    # Batching Preferences
    batch_emails: bool = Field(default=False, description="Batch non-urgent emails")
    batch_frequency: Optional[str] = Field(None, description="Batch frequency (daily, weekly)")
    batch_time: Optional[str] = Field(None, description="Preferred batch time (HH:MM)")

    # Marketing Preferences
    marketing_emails: bool = Field(default=True, description="Marketing emails opt-in")
    marketing_sms: bool = Field(default=False, description="Marketing SMS opt-in")
    newsletter_subscription: bool = Field(default=True, description="Newsletter subscription")

    # Unsubscribe
    unsubscribed_all: bool = Field(default=False, description="Unsubscribed from all")
    unsubscribe_token: Optional[str] = Field(None, description="Unsubscribe token")
    unsubscribed_at: Optional[datetime] = Field(None, description="Unsubscribe timestamp")

    @field_validator('quiet_hours_start', 'quiet_hours_end', 'batch_time')
    @classmethod
    def validate_time_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate time format (HH:MM)."""
        if not v:
            return v

        try:
            parts = v.split(':')
            if len(parts) != 2:
                raise ValueError

            hour = int(parts[0])
            minute = int(parts[1])

            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError

            return f"{hour:02d}:{minute:02d}"
        except (ValueError, IndexError):
            raise ValueError("Time must be in HH:MM format")


class NotificationLog(BaseDBModel):
    """
    Detailed log of notification events for audit trail.
    """

    notification_id: UUID = Field(..., description="Parent notification ID")
    event_type: str = Field(..., max_length=50, description="Event type")
    event_data: Optional[Dict[str, Any]] = Field(None, description="Event data")

    # Tracking
    ip_address: Optional[str] = Field(None, description="IP address of event")
    user_agent: Optional[str] = Field(None, description="User agent string")

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NotificationBatch(BaseDBModel):
    """
    Batch notification for bulk sending.
    """

    name: str = Field(..., min_length=1, max_length=100, description="Batch name")
    type: NotificationType = Field(..., description="Notification type")
    channel: NotificationChannel = Field(..., description="Delivery channel")

    # Recipients
    recipient_count: int = Field(default=0, ge=0, description="Total recipients")
    recipient_list: Optional[List[Dict[str, Any]]] = Field(None, description="Recipient list")

    # Content
    template_id: Optional[UUID] = Field(None, description="Template to use")
    subject: Optional[str] = Field(None, description="Batch subject")
    content: Optional[str] = Field(None, description="Batch content")

    # Status
    status: NotificationStatus = Field(default=NotificationStatus.PENDING)
    scheduled_for: Optional[datetime] = Field(None, description="Scheduled send time")
    started_at: Optional[datetime] = Field(None, description="Processing start time")
    completed_at: Optional[datetime] = Field(None, description="Processing end time")

    # Statistics
    sent_count: int = Field(default=0, ge=0, description="Successfully sent")
    failed_count: int = Field(default=0, ge=0, description="Failed sends")
    pending_count: int = Field(default=0, ge=0, description="Pending sends")

    # Performance
    open_count: int = Field(default=0, ge=0, description="Total opens")
    click_count: int = Field(default=0, ge=0, description="Total clicks")
    unsubscribe_count: int = Field(default=0, ge=0, description="Unsubscribes")

    # Metadata
    tags: Optional[List[str]] = Field(None, description="Batch tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")