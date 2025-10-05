"""
iSwitch Roofs CRM - Partnership SQLAlchemy Model
Version: 1.0.0

Partnership data model for managing referral partners (insurance agents, realtors,
property managers, etc.) and tracking referral performance.
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, Date, Float, Enum as SQLEnum
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from enum import Enum

from app.models.base import BaseModel


class PartnerType(str, Enum):
    """Partnership type enumeration"""
    INSURANCE_AGENT = "insurance_agent"
    REALTOR = "realtor"
    PROPERTY_MANAGER = "property_manager"
    HOME_INSPECTOR = "home_inspector"
    CONTRACTOR = "contractor"
    SUPPLIER = "supplier"
    COMMUNITY_LEADER = "community_leader"
    PROFESSIONAL_NETWORK = "professional_network"
    OTHER = "other"


class PartnershipStatus(str, Enum):
    """Partnership status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"      # Onboarding
    PAUSED = "paused"        # Temporarily inactive
    TERMINATED = "terminated"


class CommissionStructure(str, Enum):
    """Commission payment structure"""
    FLAT_FEE = "flat_fee"              # Fixed amount per referral
    PERCENTAGE = "percentage"           # Percentage of project value
    TIERED = "tiered"                  # Different rates based on volume
    NONE = "none"                       # No commission (goodwill partner)


class Partnership(BaseModel):
    """
    Partnership SQLAlchemy model for referral partner management.

    Tracks relationships with insurance agents, realtors, property managers,
    and other referral sources. Manages commission, performance, and engagement.
    """
    __tablename__ = 'partnerships'

    # Basic Information (Required)
    company_name = Column(String(200), nullable=True)
    contact_first_name = Column(String(100), nullable=False)
    contact_last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(20), nullable=False)

    # Partnership Details
    partner_type = Column(SQLEnum(PartnerType), nullable=False)
    status = Column(SQLEnum(PartnershipStatus), default=PartnershipStatus.PENDING)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # Business Information
    business_address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(2), nullable=True)
    zip_code = Column(String(20), nullable=True)
    website = Column(String(500), nullable=True)
    license_number = Column(String(100), nullable=True)

    # Secondary Contact
    secondary_contact_name = Column(String(200), nullable=True)
    secondary_contact_email = Column(String(255), nullable=True)
    secondary_contact_phone = Column(String(20), nullable=True)

    # Commission & Payment
    commission_structure = Column(SQLEnum(CommissionStructure), nullable=False)
    commission_rate = Column(Float, nullable=True)
    commission_notes = Column(String(1000), nullable=True)
    payment_method = Column(String(50), nullable=True)
    payment_terms = Column(String(500), nullable=True)

    # Tax Information
    tax_id = Column(String(50), nullable=True)
    w9_on_file = Column(Boolean, default=False)
    w9_received_date = Column(Date, nullable=True)

    # Performance Metrics
    total_referrals = Column(Integer, default=0)
    successful_referrals = Column(Integer, default=0)
    active_referrals = Column(Integer, default=0)
    total_revenue_generated = Column(Integer, default=0)
    total_commission_paid = Column(Integer, default=0)
    total_commission_pending = Column(Integer, default=0)

    # Conversion Metrics
    conversion_rate = Column(Float, nullable=True)
    avg_project_value = Column(Integer, nullable=True)
    avg_days_to_close = Column(Integer, nullable=True)

    # Engagement
    last_referral_date = Column(Date, nullable=True)
    last_contact_date = Column(Date, nullable=True)
    next_follow_up_date = Column(Date, nullable=True, index=True)
    assigned_to = Column(String(36), nullable=True, index=True)

    # Agreement Details
    agreement_signed = Column(Boolean, default=False)
    agreement_date = Column(Date, nullable=True)
    agreement_document_url = Column(Text, nullable=True)
    agreement_expiry_date = Column(Date, nullable=True, index=True)
    auto_renew = Column(Boolean, default=False)

    # Marketing & Co-branding
    can_use_logo = Column(Boolean, default=False)
    can_list_as_partner = Column(Boolean, default=False)
    co_marketing_agreement = Column(Boolean, default=False)
    marketing_materials_provided = Column(Boolean, default=False)

    # Service Areas
    service_areas = Column(Text, nullable=True)
    specialization = Column(String(500), nullable=True)

    # Quality & Ratings
    partner_rating = Column(Float, nullable=True)
    quality_score = Column(Integer, nullable=True)
    satisfaction_score = Column(Integer, nullable=True)

    # Communication Preferences
    preferred_contact_method = Column(String(50), nullable=True)
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    monthly_report = Column(Boolean, default=True)

    # Notes & Tags
    notes = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    strengths = Column(String(1000), nullable=True)
    concerns = Column(String(1000), nullable=True)

    # Termination
    termination_reason = Column(String(500), nullable=True)
    termination_date = Column(Date, nullable=True)

    @property
    def full_name(self) -> str:
        """Get full contact name"""
        return f"{self.contact_first_name} {self.contact_last_name}"

    @property
    def display_name(self) -> str:
        """Get display name (company or contact)"""
        return self.company_name or self.full_name

    @property
    def is_active(self) -> bool:
        """Check if partnership is active"""
        return self.status == PartnershipStatus.ACTIVE

    @property
    def is_high_performer(self) -> bool:
        """Check if partner is high performer (>50% conversion, 10+ referrals)"""
        return (
            self.total_referrals >= 10 and
            self.conversion_rate and
            self.conversion_rate >= 50.0
        )

    @property
    def roi(self) -> Optional[float]:
        """Calculate ROI (revenue vs commission)"""
        if self.total_commission_paid and self.total_commission_paid > 0:
            return (self.total_revenue_generated / self.total_commission_paid) * 100
        return None

    @property
    def needs_follow_up(self) -> bool:
        """Check if follow-up is overdue"""
        if self.next_follow_up_date:
            return date.today() > self.next_follow_up_date
        return False

    @property
    def agreement_expires_soon(self) -> bool:
        """Check if agreement expires within 30 days"""
        if self.agreement_expiry_date and not self.auto_renew:
            days_until_expiry = (self.agreement_expiry_date - date.today()).days
            return 0 <= days_until_expiry <= 30
        return False


# Pydantic schemas for API validation
class PartnershipCreateSchema(BaseModel):
    """Schema for creating a new partnership"""
    model_config = ConfigDict(from_attributes=True)

    contact_first_name: str = Field(..., min_length=1, max_length=100)
    contact_last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str
    partner_type: PartnerType
    commission_structure: CommissionStructure

    # Optional fields
    company_name: Optional[str] = None
    business_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    website: Optional[str] = None
    commission_rate: Optional[float] = None
    commission_notes: Optional[str] = None
    start_date: Optional[date] = None
    assigned_to: Optional[UUID] = None
    service_areas: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('phone')
    @classmethod
    def validate_phone_format(cls, v: str) -> str:
        """Validate phone number format"""
        if not v:
            raise ValueError('Phone number is required')

        cleaned = ''.join(filter(str.isdigit, v.lstrip('+')))

        if len(cleaned) < 10:
            raise ValueError('Phone must have at least 10 digits')

        if len(cleaned) > 15:
            raise ValueError('Phone cannot exceed 15 digits')

        return v

    @field_validator('state')
    @classmethod
    def validate_state(cls, v: Optional[str]) -> Optional[str]:
        """Validate state code"""
        if v is None:
            return v

        if len(v) != 2:
            raise ValueError('State must be 2-letter code')

        return v.upper()


class PartnershipUpdateSchema(BaseModel):
    """Schema for updating a partnership"""
    model_config = ConfigDict(from_attributes=True)

    company_name: Optional[str] = None
    contact_first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    contact_last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[PartnershipStatus] = None
    commission_rate: Optional[float] = None
    commission_notes: Optional[str] = None
    assigned_to: Optional[UUID] = None
    next_follow_up_date: Optional[date] = None
    partner_rating: Optional[float] = None
    quality_score: Optional[int] = None
    agreement_signed: Optional[bool] = None
    can_use_logo: Optional[bool] = None
    can_list_as_partner: Optional[bool] = None
    notes: Optional[str] = None
    tags: Optional[str] = None


class PartnershipReferralSchema(BaseModel):
    """Schema for logging a referral from partner"""
    partnership_id: UUID
    lead_first_name: str
    lead_last_name: str
    lead_phone: str
    lead_email: Optional[EmailStr] = None
    property_address: Optional[str] = None
    notes: Optional[str] = None


class PartnershipResponseSchema(BaseModel):
    """Schema for partnership API response"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_name: Optional[str] = None
    contact_first_name: str
    contact_last_name: str
    email: str
    phone: str
    partner_type: PartnerType
    status: PartnershipStatus
    commission_structure: CommissionStructure
    commission_rate: Optional[float] = None
    total_referrals: int = 0
    successful_referrals: int = 0
    conversion_rate: Optional[float] = None
    total_revenue_generated: int = 0
    created_at: datetime
    updated_at: datetime


class PartnershipListFiltersSchema(BaseModel):
    """Filter parameters for partnership list endpoint"""
    partner_type: Optional[str] = Field(None, description="Comma-separated types")
    status: Optional[PartnershipStatus] = Field(None, description="Filter by status")
    assigned_to: Optional[UUID] = Field(None, description="Filter by relationship manager")
    min_referrals: Optional[int] = Field(None, ge=0, description="Minimum referral count")
    min_conversion_rate: Optional[float] = Field(None, ge=0, le=100, description="Min conversion rate %")
    is_high_performer: Optional[bool] = Field(None, description="Filter high performers")
    needs_follow_up: Optional[bool] = Field(None, description="Filter needing follow-up")
    agreement_expires_soon: Optional[bool] = Field(None, description="Filter expiring agreements")
    service_area: Optional[str] = Field(None, description="Filter by service area")
    tags: Optional[str] = Field(None, description="Filter by tags")