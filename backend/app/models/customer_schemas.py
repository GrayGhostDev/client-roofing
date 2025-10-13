"""
iSwitch Roofs CRM - Customer Model
Version: 1.0.0

Customer data model representing converted leads with project history and lifetime value tracking.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator



class CustomerStatus(str, Enum):
    """Customer status enumeration"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    VIP = "vip"
    CHURNED = "churned"


class CustomerSegment(str, Enum):
    """Customer segment classification"""

    PREMIUM = "premium"  # High-value customers ($50K+ LTV)
    STANDARD = "standard"  # Regular customers
    REPEAT = "repeat"  # Multiple projects
    REFERRAL_SOURCE = "referral_source"  # Active referrers


class Customer(BaseModel):
    """
    Customer data model with project history and value tracking.

    Represents a converted lead who has completed at least one project.
    """

    # Contact Information (Required)
    first_name: str = Field(..., min_length=1, max_length=100, description="Customer first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Customer last name")
    phone: str = Field(..., description="Primary phone number")
    email: EmailStr | None = Field(None, description="Email address")

    # Metadata
    status: CustomerStatus = Field(default=CustomerStatus.ACTIVE, description="Customer status")
    segment: CustomerSegment | None = Field(None, description="Customer segment")

    # Address Information
    street_address: str | None = Field(None, max_length=255, description="Street address")
    city: str | None = Field(None, max_length=100, description="City")
    state: str | None = Field(None, max_length=2, description="State code (e.g., MI)")
    zip_code: str | None = Field(None, description="ZIP code")

    # Property Details
    property_value: int | None = Field(None, ge=0, description="Property value in USD")
    property_type: str | None = Field(
        None, max_length=50, description="Property type (single-family, commercial, etc.)"
    )
    roof_age: int | None = Field(None, ge=0, le=100, description="Age of roof in years")
    roof_type: str | None = Field(None, max_length=50, description="Type of roof")
    roof_size_sqft: int | None = Field(None, ge=0, description="Roof size in square feet")

    # Value Metrics
    lifetime_value: int = Field(default=0, ge=0, description="Total lifetime value in USD")
    project_count: int = Field(default=0, ge=0, description="Number of completed projects")
    avg_project_value: int = Field(default=0, ge=0, description="Average project value in USD")

    # Conversion Details
    converted_from_lead_id: UUID | None = Field(None, description="Original lead ID")
    conversion_date: datetime | None = Field(None, description="Date converted from lead")
    original_source: str | None = Field(None, description="Original lead source")

    # Relationship Management
    assigned_to: UUID | None = Field(None, description="Assigned account manager")
    last_contact_date: datetime | None = Field(None, description="Last contact timestamp")
    next_follow_up_date: datetime | None = Field(None, description="Next scheduled follow-up")

    # Referral Tracking
    referral_count: int = Field(default=0, ge=0, description="Number of successful referrals")
    referral_value: int = Field(default=0, ge=0, description="Total value of referred business")
    is_referral_partner: bool = Field(default=False, description="Active in referral program")

    # Review & Satisfaction
    nps_score: int | None = Field(None, ge=0, le=10, description="Net Promoter Score (0-10)")
    satisfaction_rating: float | None = Field(
        None, ge=0.0, le=5.0, description="Average satisfaction (1-5 stars)"
    )
    review_count: int = Field(default=0, ge=0, description="Number of reviews provided")

    # Customer Lifecycle
    customer_since: datetime | None = Field(None, description="Date when became a customer")
    last_interaction: datetime | None = Field(None, description="Last interaction timestamp")
    interaction_count: int = Field(default=0, ge=0, description="Total number of interactions")
    preferred_contact_method: str | None = Field(
        None, description="Preferred contact method (phone/email/text)"
    )
    best_call_time: str | None = Field(None, description="Best time to call")

    # Marketing & Campaign
    campaign_tags: str | None = Field(None, description="Marketing campaign tags")
    email_opt_in: bool = Field(default=True, description="Email marketing opt-in")
    sms_opt_in: bool = Field(default=False, description="SMS marketing opt-in")

    # Notes
    notes: str | None = Field(None, description="Internal notes about customer")
    tags: str | None = Field(None, description="Comma-separated tags")

    @field_validator("phone")
    @classmethod
    def validate_phone_format(cls, v: str) -> str:
        """Validate phone number format"""
        if not v:
            raise ValueError("Phone number is required")

        cleaned = "".join(filter(str.isdigit, v.lstrip("+")))

        if len(cleaned) < 10:
            raise ValueError("Phone must have at least 10 digits")

        if len(cleaned) > 15:
            raise ValueError("Phone cannot exceed 15 digits")

        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip_code(cls, v: str | None) -> str | None:
        """Validate ZIP code format (5 or 9 digits)"""
        if v is None:
            return v

        cleaned = "".join(filter(str.isdigit, v))

        if len(cleaned) not in [5, 9]:
            raise ValueError("ZIP code must be 5 or 9 digits")

        return v

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str | None) -> str | None:
        """Validate state code is uppercase 2 letters"""
        if v is None:
            return v

        if len(v) != 2:
            raise ValueError("State must be 2-letter code")

        return v.upper()

    @property
    def full_name(self) -> str:
        """Get full name"""
        return f"{self.first_name} {self.last_name}"

    @property
    def full_address(self) -> str | None:
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
    def is_vip(self) -> bool:
        """Check if customer is VIP (high lifetime value or status)"""
        return self.status == CustomerStatus.VIP or self.lifetime_value >= 50000

    @property
    def is_repeat_customer(self) -> bool:
        """Check if customer has multiple projects"""
        return self.project_count > 1


class CustomerCreate(BaseModel):
    """Schema for creating a new customer"""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str
    email: EmailStr | None = None

    # Optional fields
    street_address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    property_value: int | None = None
    property_type: str | None = None
    roof_age: int | None = None
    roof_type: str | None = None
    assigned_to: UUID | None = None
    notes: str | None = None
    tags: str | None = None

    # Conversion tracking
    converted_from_lead_id: UUID | None = None
    original_source: str | None = None


class CustomerUpdate(BaseModel):
    """Schema for updating a customer"""

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = None
    email: EmailStr | None = None
    status: CustomerStatus | None = None
    segment: CustomerSegment | None = None

    street_address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    property_value: int | None = None
    property_type: str | None = None
    roof_age: int | None = None
    roof_type: str | None = None
    assigned_to: UUID | None = None
    next_follow_up_date: datetime | None = None
    notes: str | None = None
    tags: str | None = None

    nps_score: int | None = Field(None, ge=0, le=10)
    is_referral_partner: bool | None = None


class CustomerResponse(BaseModel):
    """Schema for customer API response"""

    data: Customer
    projects: list[dict] | None = None  # Will be populated with project data
    recent_interactions: list[dict] | None = None


class CustomerListFilters(BaseModel):
    """Filter parameters for customer list endpoint"""

    status: str | None = Field(None, description="Comma-separated status values")
    segment: str | None = Field(None, description="Comma-separated segment values")
    assigned_to: UUID | None = Field(None, description="Filter by assigned account manager")
    min_lifetime_value: int | None = Field(None, ge=0, description="Minimum lifetime value")
    zip_code: str | None = Field(None, description="Filter by ZIP code")
    is_referral_partner: bool | None = Field(None, description="Filter referral partners")
    tags: str | None = Field(None, description="Filter by tags (comma-separated)")
