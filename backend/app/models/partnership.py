"""
iSwitch Roofs CRM - Partnership Model
Version: 1.0.0

Partnership data model for managing referral partners (insurance agents, realtors,
property managers, etc.) and tracking referral performance.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from enum import Enum

from backend.app.models.base import BaseDBModel


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


class Partnership(BaseDBModel):
    """
    Partnership data model for referral partner management.

    Tracks relationships with insurance agents, realtors, property managers,
    and other referral sources. Manages commission, performance, and engagement.
    """

    # Basic Information (Required)
    company_name: Optional[str] = Field(None, max_length=200, description="Company/Agency name")
    contact_first_name: str = Field(..., min_length=1, max_length=100, description="Contact first name")
    contact_last_name: str = Field(..., min_length=1, max_length=100, description="Contact last name")
    email: EmailStr = Field(..., description="Primary email")
    phone: str = Field(..., description="Primary phone number")

    # Partnership Details
    partner_type: PartnerType = Field(..., description="Type of partnership")
    status: PartnershipStatus = Field(default=PartnershipStatus.PENDING, description="Partnership status")
    start_date: Optional[date] = Field(None, description="Partnership start date")
    end_date: Optional[date] = Field(None, description="Partnership end date")

    # Business Information
    business_address: Optional[str] = Field(None, max_length=255, description="Business address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=2, description="State code")
    zip_code: Optional[str] = Field(None, description="ZIP code")
    website: Optional[str] = Field(None, description="Website URL")
    license_number: Optional[str] = Field(None, max_length=100, description="Professional license number")

    # Secondary Contact
    secondary_contact_name: Optional[str] = Field(None, max_length=200, description="Secondary contact name")
    secondary_contact_email: Optional[EmailStr] = Field(None, description="Secondary email")
    secondary_contact_phone: Optional[str] = Field(None, description="Secondary phone")

    # Commission & Payment
    commission_structure: CommissionStructure = Field(..., description="Commission structure")
    commission_rate: Optional[float] = Field(None, ge=0, le=100, description="Commission rate (% or flat fee)")
    commission_notes: Optional[str] = Field(None, max_length=1000, description="Commission terms details")
    payment_method: Optional[str] = Field(None, max_length=50, description="check, ach, wire, etc.")
    payment_terms: Optional[str] = Field(None, max_length=500, description="Payment terms description")

    # Tax Information
    tax_id: Optional[str] = Field(None, max_length=50, description="Tax ID/EIN")
    w9_on_file: bool = Field(default=False, description="W-9 form on file")
    w9_received_date: Optional[date] = Field(None, description="Date W-9 received")

    # Performance Metrics
    total_referrals: int = Field(default=0, ge=0, description="Total referrals sent")
    successful_referrals: int = Field(default=0, ge=0, description="Referrals that became customers")
    active_referrals: int = Field(default=0, ge=0, description="Currently active referred leads")
    total_revenue_generated: int = Field(default=0, ge=0, description="Total revenue from referrals USD")
    total_commission_paid: int = Field(default=0, ge=0, description="Total commission paid USD")
    total_commission_pending: int = Field(default=0, ge=0, description="Pending commission USD")

    # Conversion Metrics
    conversion_rate: Optional[float] = Field(None, ge=0, le=100, description="Referral conversion rate %")
    avg_project_value: Optional[int] = Field(None, ge=0, description="Average project value from referrals")
    avg_days_to_close: Optional[int] = Field(None, ge=0, description="Average days to close referral")

    # Engagement
    last_referral_date: Optional[date] = Field(None, description="Date of last referral")
    last_contact_date: Optional[date] = Field(None, description="Last contact timestamp")
    next_follow_up_date: Optional[date] = Field(None, description="Next scheduled follow-up")
    assigned_to: Optional[UUID] = Field(None, description="Assigned relationship manager")

    # Agreement Details
    agreement_signed: bool = Field(default=False, description="Partnership agreement signed")
    agreement_date: Optional[date] = Field(None, description="Agreement signature date")
    agreement_document_url: Optional[str] = Field(None, description="Agreement document URL")
    agreement_expiry_date: Optional[date] = Field(None, description="Agreement expiry date")
    auto_renew: bool = Field(default=False, description="Automatically renew agreement")

    # Marketing & Co-branding
    can_use_logo: bool = Field(default=False, description="Permission to use partner logo")
    can_list_as_partner: bool = Field(default=False, description="Can list publicly as partner")
    co_marketing_agreement: bool = Field(default=False, description="Co-marketing agreement in place")
    marketing_materials_provided: bool = Field(default=False, description="Marketing materials given")

    # Service Areas
    service_areas: Optional[str] = Field(None, description="ZIP codes or cities served (comma-separated)")
    specialization: Optional[str] = Field(None, max_length=500, description="Specialization or niche")

    # Quality & Ratings
    partner_rating: Optional[float] = Field(None, ge=0, le=5, description="Internal partner rating (1-5)")
    quality_score: Optional[int] = Field(None, ge=0, le=100, description="Quality score (0-100)")
    satisfaction_score: Optional[int] = Field(None, ge=0, le=10, description="NPS-style score (0-10)")

    # Communication Preferences
    preferred_contact_method: Optional[str] = Field(None, max_length=50, description="email, phone, text")
    email_notifications: bool = Field(default=True, description="Send email notifications")
    sms_notifications: bool = Field(default=False, description="Send SMS notifications")
    monthly_report: bool = Field(default=True, description="Send monthly performance report")

    # Notes & Tags
    notes: Optional[str] = Field(None, description="Internal notes about partnership")
    tags: Optional[str] = Field(None, description="Tags for categorization")
    strengths: Optional[str] = Field(None, max_length=1000, description="Partner strengths")
    concerns: Optional[str] = Field(None, max_length=1000, description="Concerns or issues")

    # Termination
    termination_reason: Optional[str] = Field(None, max_length=500, description="Reason if terminated")
    termination_date: Optional[date] = Field(None, description="Date terminated")

    @field_validator('phone', 'secondary_contact_phone')
    @classmethod
    def validate_phone_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format"""
        if not v:
            return v

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


class PartnershipCreate(BaseModel):
    """Schema for creating a new partnership"""
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


class PartnershipUpdate(BaseModel):
    """Schema for updating a partnership"""
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


class PartnershipReferral(BaseModel):
    """Schema for logging a referral from partner"""
    partnership_id: UUID
    lead_first_name: str
    lead_last_name: str
    lead_phone: str
    lead_email: Optional[EmailStr] = None
    property_address: Optional[str] = None
    notes: Optional[str] = None


class PartnershipResponse(BaseModel):
    """Schema for partnership API response"""
    data: Partnership
    performance_metrics: Optional[dict] = None  # Detailed performance data
    recent_referrals: Optional[list] = None  # Recent referred leads


class PartnershipListFilters(BaseModel):
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
