"""
iSwitch Roofs CRM - Lead SQLAlchemy Model
Version: 1.0.0

Proper SQLAlchemy model for database operations
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, Text

from app.models.base import BaseModel


class LeadStatusEnum(enum.Enum):
    """Lead status enumeration"""

    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    APPOINTMENT_SCHEDULED = "appointment_scheduled"
    INSPECTION_COMPLETED = "inspection_completed"
    QUOTE_SENT = "quote_sent"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"
    NURTURE = "nurture"


class LeadTemperatureEnum(enum.Enum):
    """Lead temperature classification"""

    HOT = "hot"  # 80-100 points
    WARM = "warm"  # 60-79 points
    COOL = "cool"  # 40-59 points
    COLD = "cold"  # 0-39 points


class LeadSourceEnum(enum.Enum):
    """Lead source enumeration"""

    WEBSITE_FORM = "website_form"
    GOOGLE_LSA = "google_lsa"
    GOOGLE_ADS = "google_ads"
    FACEBOOK_ADS = "facebook_ads"
    REFERRAL = "referral"
    DOOR_TO_DOOR = "door_to_door"
    STORM_RESPONSE = "storm_response"
    ORGANIC_SEARCH = "organic_search"
    PHONE_INQUIRY = "phone_inquiry"
    EMAIL_INQUIRY = "email_inquiry"
    PARTNER_REFERRAL = "partner_referral"
    REPEAT_CUSTOMER = "repeat_customer"


class UrgencyLevelEnum(enum.Enum):
    """Project urgency level"""

    IMMEDIATE = "immediate"
    ONE_TO_THREE_MONTHS = "1-3_months"
    THREE_TO_SIX_MONTHS = "3-6_months"
    PLANNING = "planning"


class Lead(BaseModel):
    """
    Lead SQLAlchemy model for database operations.

    Represents a potential customer in the CRM system with scoring,
    temperature classification, and full contact/property details.
    """

    __tablename__ = "leads"

    # Primary key - UUID as string for Supabase compatibility
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Contact Information (Required)
    first_name = Column(String(100), nullable=False, index=True)
    last_name = Column(String(100), nullable=False, index=True)
    phone = Column(String(20), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)

    # Lead Metadata
    source = Column(Enum(LeadSourceEnum), nullable=False)
    status = Column(Enum(LeadStatusEnum), default=LeadStatusEnum.NEW, nullable=False, index=True)
    temperature = Column(Enum(LeadTemperatureEnum), nullable=True, index=True)
    lead_score = Column(Integer, default=0, nullable=False)

    # Address Information
    street_address = Column(String(255))
    city = Column(String(100), index=True)
    state = Column(String(2))
    zip_code = Column(String(10), index=True)

    # Property Details
    property_value = Column(Integer)
    roof_age = Column(Integer)
    roof_type = Column(String(50))
    roof_size_sqft = Column(Integer)
    urgency = Column(Enum(UrgencyLevelEnum))

    # Project Details
    project_description = Column(Text)
    budget_range_min = Column(Integer)
    budget_range_max = Column(Integer)
    insurance_claim = Column(Boolean, default=False)

    # Assignment & Conversion
    assigned_to = Column(String(36))  # UUID reference to team member
    converted_to_customer = Column(Boolean, default=False, index=True)
    customer_id = Column(String(36))  # UUID reference to customer

    # Tracking
    last_contact_date = Column(DateTime)
    next_follow_up_date = Column(DateTime, index=True)
    response_time_minutes = Column(Integer)
    interaction_count = Column(Integer, default=0)

    # Notes and metadata
    notes = Column(Text)
    lost_reason = Column(String(500))
    metadata_json = Column(Text)  # Additional JSON metadata

    # Base model fields (from BaseModel)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    def __repr__(self):
        """String representation of lead"""
        return f"<Lead(id='{self.id}', name='{self.first_name} {self.last_name}', status='{self.status.value}')>"

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
    def is_hot_lead(self):
        """Check if lead is hot (score >= 80)"""
        return self.lead_score >= 80

    @property
    def is_qualified(self):
        """Check if lead is in qualified status or beyond"""
        qualified_statuses = [
            LeadStatusEnum.QUALIFIED,
            LeadStatusEnum.APPOINTMENT_SCHEDULED,
            LeadStatusEnum.INSPECTION_COMPLETED,
            LeadStatusEnum.QUOTE_SENT,
            LeadStatusEnum.NEGOTIATION,
        ]
        return self.status in qualified_statuses

    def to_dict(self):
        """Convert lead to dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, enum.Enum):
                value = value.value
            result[column.name] = value
        return result
