"""
iSwitch Roofs CRM - Alert SQLAlchemy Model
Version: 1.0.0

Alert data model for system alerts and notifications management.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy import Enum as SQLEnum

from app.models.base import BaseModel


class AlertType(str, Enum):
    """Alert type enumeration"""

    # Lead alerts
    NEW_LEAD = "new_lead"
    HOT_LEAD = "hot_lead"
    LEAD_FOLLOW_UP = "lead_follow_up"
    LEAD_UNRESPONDED = "lead_unresponded"

    # Customer alerts
    CUSTOMER_MILESTONE = "customer_milestone"
    REVIEW_REQUEST_DUE = "review_request_due"
    CUSTOMER_ANNIVERSARY = "customer_anniversary"

    # Project alerts
    PROJECT_OVERDUE = "project_overdue"
    PROJECT_MILESTONE = "project_milestone"
    PERMIT_EXPIRING = "permit_expiring"
    INSPECTION_DUE = "inspection_due"

    # Appointment alerts
    APPOINTMENT_REMINDER = "appointment_reminder"
    APPOINTMENT_SOON = "appointment_soon"
    APPOINTMENT_OVERDUE = "appointment_overdue"

    # Team alerts
    QUOTA_DEADLINE = "quota_deadline"
    PERFORMANCE_ISSUE = "performance_issue"
    TEAM_MILESTONE = "team_milestone"

    # System alerts
    SYSTEM_ERROR = "system_error"
    INTEGRATION_FAILURE = "integration_failure"
    BACKUP_FAILED = "backup_failed"

    # Business alerts
    REVENUE_TARGET = "revenue_target"
    LOW_CONVERSION = "low_conversion"
    HIGH_CANCELLATION = "high_cancellation"


class AlertPriority(str, Enum):
    """Alert priority levels"""

    CRITICAL = "critical"  # Immediate attention required
    HIGH = "high"  # Attention needed soon
    MEDIUM = "medium"  # Normal priority
    LOW = "low"  # Informational


class AlertStatus(str, Enum):
    """Alert status"""

    ACTIVE = "active"  # Alert is active
    ACKNOWLEDGED = "acknowledged"  # Alert has been seen
    RESOLVED = "resolved"  # Alert has been resolved
    DISMISSED = "dismissed"  # Alert was dismissed
    EXPIRED = "expired"  # Alert expired automatically


class Alert(BaseModel):
    """
    Alert SQLAlchemy model for system alerts and notifications management.

    Tracks various types of alerts including lead follow-ups, project deadlines,
    system issues, and performance notifications.
    """

    __tablename__ = "alerts"

    # Basic Information
    type = Column(SQLEnum(AlertType), nullable=False, index=True)
    priority = Column(SQLEnum(AlertPriority), nullable=False, index=True)
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.ACTIVE, index=True)

    # Content
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    action_url = Column(String(500), nullable=True)
    action_text = Column(String(100), nullable=True)

    # Recipients and Assignment
    assigned_to = Column(String(36), nullable=True, index=True)  # Team member ID
    created_by = Column(String(36), nullable=True, index=True)  # Who/what created the alert

    # Related Entities
    related_lead_id = Column(String(36), nullable=True, index=True)
    related_customer_id = Column(String(36), nullable=True, index=True)
    related_project_id = Column(String(36), nullable=True, index=True)
    related_appointment_id = Column(String(36), nullable=True, index=True)

    # Timing
    alert_date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    due_date = Column(DateTime, nullable=True, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)

    # Status Management
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(36), nullable=True, index=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(36), nullable=True, index=True)
    resolution_notes = Column(Text, nullable=True)

    # Auto-resolution
    auto_resolve = Column(Boolean, default=False)
    auto_resolve_condition = Column(String(500), nullable=True)

    # Notification
    notification_sent = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime, nullable=True)
    send_email = Column(Boolean, default=True)
    send_sms = Column(Boolean, default=False)
    send_push = Column(Boolean, default=True)

    # Recurrence
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(100), nullable=True)  # daily, weekly, monthly
    next_occurrence = Column(DateTime, nullable=True)

    # Metadata (stored as JSON string)
    metadata_json = Column(Text, nullable=True)

    # Tags and Categories
    tags = Column(Text, nullable=True)
    category = Column(String(50), nullable=True, index=True)

    @property
    def is_overdue(self) -> bool:
        """Check if alert is overdue"""
        if self.due_date and self.status == AlertStatus.ACTIVE:
            return datetime.utcnow() > self.due_date
        return False

    @property
    def is_expired(self) -> bool:
        """Check if alert has expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False

    @property
    def time_until_due(self) -> int | None:
        """Get minutes until due date"""
        if self.due_date and self.status == AlertStatus.ACTIVE:
            delta = self.due_date - datetime.utcnow()
            return int(delta.total_seconds() / 60) if delta.total_seconds() > 0 else 0
        return None

    @property
    def is_critical(self) -> bool:
        """Check if alert is critical priority"""
        return self.priority == AlertPriority.CRITICAL

    @property
    def needs_attention(self) -> bool:
        """Check if alert needs attention"""
        return (
            self.status == AlertStatus.ACTIVE
            and not self.is_expired
            and self.priority in [AlertPriority.CRITICAL, AlertPriority.HIGH]
        )


# Pydantic schemas for API validation
class AlertCreateSchema(BaseModel):
    """Schema for creating a new alert"""

    model_config = ConfigDict(from_attributes=True)

    type: AlertType
    priority: AlertPriority
    title: str = Field(..., min_length=1, max_length=200)
    message: str

    # Optional fields
    assigned_to: UUID | None = None
    action_url: str | None = None
    action_text: str | None = None
    due_date: datetime | None = None
    expires_at: datetime | None = None

    # Related entities
    related_lead_id: UUID | None = None
    related_customer_id: UUID | None = None
    related_project_id: UUID | None = None
    related_appointment_id: UUID | None = None

    # Notification preferences
    send_email: bool | None = True
    send_sms: bool | None = False
    send_push: bool | None = True

    # Recurrence
    is_recurring: bool | None = False
    recurrence_pattern: str | None = None

    # Metadata
    tags: str | None = None
    category: str | None = None


class AlertUpdateSchema(BaseModel):
    """Schema for updating an alert"""

    model_config = ConfigDict(from_attributes=True)

    status: AlertStatus | None = None
    priority: AlertPriority | None = None
    assigned_to: UUID | None = None
    due_date: datetime | None = None
    resolution_notes: str | None = None
    tags: str | None = None


class AlertAcknowledgeSchema(BaseModel):
    """Schema for acknowledging an alert"""

    notes: str | None = None


class AlertResolveSchema(BaseModel):
    """Schema for resolving an alert"""

    resolution_notes: str | None = None


class AlertResponseSchema(BaseModel):
    """Schema for alert API response"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    type: AlertType
    priority: AlertPriority
    status: AlertStatus
    title: str
    message: str
    assigned_to: str | None = None
    alert_date: datetime
    due_date: datetime | None = None
    expires_at: datetime | None = None
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None

    # Related entities
    related_lead_id: str | None = None
    related_customer_id: str | None = None
    related_project_id: str | None = None
    related_appointment_id: str | None = None

    # Computed properties
    is_overdue: bool = False
    is_expired: bool = False
    needs_attention: bool = False

    created_at: datetime
    updated_at: datetime


class AlertListFiltersSchema(BaseModel):
    """Filter parameters for alert list endpoint"""

    type: str | None = Field(None, description="Comma-separated alert types")
    priority: str | None = Field(None, description="Comma-separated priorities")
    status: str | None = Field(None, description="Comma-separated statuses")
    assigned_to: UUID | None = Field(None, description="Filter by assignee")
    created_by: UUID | None = Field(None, description="Filter by creator")
    category: str | None = Field(None, description="Filter by category")

    # Related entities
    related_lead_id: UUID | None = Field(None, description="Filter by related lead")
    related_customer_id: UUID | None = Field(None, description="Filter by related customer")
    related_project_id: UUID | None = Field(None, description="Filter by related project")
    related_appointment_id: UUID | None = Field(None, description="Filter by related appointment")

    # Date filters
    date_from: datetime | None = Field(None, description="Filter from date")
    date_to: datetime | None = Field(None, description="Filter to date")
    due_from: datetime | None = Field(None, description="Filter by due date from")
    due_to: datetime | None = Field(None, description="Filter by due date to")

    # Status filters
    is_overdue: bool | None = Field(None, description="Filter overdue alerts")
    is_expired: bool | None = Field(None, description="Filter expired alerts")
    needs_attention: bool | None = Field(None, description="Filter alerts needing attention")
    unacknowledged: bool | None = Field(None, description="Filter unacknowledged alerts")

    tags: str | None = Field(None, description="Filter by tags")
