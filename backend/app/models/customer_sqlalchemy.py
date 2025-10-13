"""
iSwitch Roofs CRM - Customer SQLAlchemy Model
Version: 1.0.0

Proper SQLAlchemy model for database operations
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class CustomerStatusEnum(enum.Enum):
    """Customer status enumeration"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    VIP = "vip"
    CHURNED = "churned"


class CustomerSegmentEnum(enum.Enum):
    """Customer segment classification"""

    PREMIUM = "premium"  # High-value customers ($50K+ LTV)
    STANDARD = "standard"  # Regular customers
    REPEAT = "repeat"  # Multiple projects
    REFERRAL_SOURCE = "referral_source"  # Active referrers


class Customer(BaseModel):
    """
    Customer SQLAlchemy model for database operations.

    Represents a converted lead who has completed at least one project.
    """

    __tablename__ = "customers"

    # Primary key - UUID as string for Supabase compatibility
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Contact Information (Required)
    first_name = Column(String(100), nullable=False, index=True)
    last_name = Column(String(100), nullable=False, index=True)
    phone = Column(String(20), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)

    # Metadata
    status = Column(
        Enum(CustomerStatusEnum), default=CustomerStatusEnum.ACTIVE, nullable=False, index=True
    )
    segment = Column(Enum(CustomerSegmentEnum), nullable=True, index=True)

    # Address Information
    street_address = Column(String(255))
    city = Column(String(100), index=True)
    state = Column(String(2))
    zip_code = Column(String(10), index=True)

    # Property Details
    property_value = Column(Integer)
    property_type = Column(String(50))
    roof_age = Column(Integer)
    roof_type = Column(String(50))
    roof_size_sqft = Column(Integer)

    # Value Metrics
    lifetime_value = Column(Integer, default=0, nullable=False, index=True)
    project_count = Column(Integer, default=0, nullable=False)
    avg_project_value = Column(Integer, default=0, nullable=False)

    # Conversion Details
    converted_from_lead_id = Column(String(36))  # UUID reference to original lead
    conversion_date = Column(DateTime, index=True)
    original_source = Column(String(100))

    # Relationship Management
    assigned_to = Column(String(36))  # UUID reference to account manager
    last_contact_date = Column(DateTime)
    next_follow_up_date = Column(DateTime, index=True)

    # Referral Tracking
    referral_count = Column(Integer, default=0, nullable=False)
    referral_value = Column(Integer, default=0, nullable=False)
    is_referral_partner = Column(Boolean, default=False, index=True)

    # Review & Satisfaction
    nps_score = Column(Integer)  # 0-10 scale
    satisfaction_rating = Column(Float)  # 1-5 stars
    review_count = Column(Integer, default=0, nullable=False)

    # Customer Lifecycle
    customer_since = Column(DateTime, index=True)
    last_interaction = Column(DateTime)
    interaction_count = Column(Integer, default=0, nullable=False)
    preferred_contact_method = Column(String(20))
    best_call_time = Column(String(50))

    # Marketing & Campaign
    campaign_tags = Column(Text)
    email_opt_in = Column(Boolean, default=True, nullable=False)
    sms_opt_in = Column(Boolean, default=False, nullable=False)

    # Notes
    notes = Column(Text)
    tags = Column(Text)

    # Base model fields (from BaseModel)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships (Week 10: Conversational AI integration)
    voice_interactions = relationship("VoiceInteraction", back_populates="customer", foreign_keys="[VoiceInteraction.customer_id]")
    chat_conversations = relationship("ChatConversation", back_populates="customer", foreign_keys="[ChatConversation.customer_id]")

    def __repr__(self):
        """String representation of customer"""
        return f"<Customer(id='{self.id}', name='{self.first_name} {self.last_name}', status='{self.status.value if self.status else None}')>"

    @property
    def full_name(self):
        """Get full name"""
        return f"{self.first_name} {self.last_name}"

    @property
    def full_address(self):
        """Get formatted full address"""
        if not self.street_address:
            return None

        parts = [self.street_address]
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.zip_code:
            parts.append(self.zip_code)

        return ", ".join(parts)

    @property
    def is_vip(self):
        """Check if customer is VIP (high lifetime value or status)"""
        return self.status == CustomerStatusEnum.VIP or self.lifetime_value >= 50000

    @property
    def is_repeat_customer(self):
        """Check if customer has multiple projects"""
        return self.project_count > 1

    def to_dict(self):
        """Convert customer to dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, enum.Enum):
                value = value.value
            result[column.name] = value
        return result

    def soft_delete(self):
        """Mark customer as deleted without removing from database"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
