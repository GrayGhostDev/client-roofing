"""
iSwitch Roofs CRM - Lead Pydantic Schemas
Version: 1.0.0

Pydantic validation schemas for Lead API operations
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime
from enum import Enum


class LeadStatus(str, Enum):
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


class LeadTemperature(str, Enum):
    """Lead temperature classification based on score"""
    HOT = "hot"      # 80-100 points
    WARM = "warm"    # 60-79 points
    COOL = "cool"    # 40-59 points
    COLD = "cold"    # 0-39 points


class LeadSource(str, Enum):
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


class UrgencyLevel(str, Enum):
    """Project urgency level"""
    IMMEDIATE = "immediate"
    ONE_TO_THREE_MONTHS = "1-3_months"
    THREE_TO_SIX_MONTHS = "3-6_months"
    PLANNING = "planning"


class LeadBase(BaseModel):
    """Base lead schema with common fields"""
    first_name: str = Field(..., min_length=1, max_length=100, description="Lead first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Lead last name")
    phone: str = Field(..., description="Primary phone number (10-15 digits)")
    email: Optional[EmailStr] = Field(None, description="Email address")
    source: LeadSource = Field(..., description="How the lead was acquired")

    @field_validator('phone')
    @classmethod
    def validate_phone_format(cls, v: str) -> str:
        """
        Validate phone number format.

        Accepts formats:
        - (248) 555-1234
        - 248-555-1234
        - 2485551234
        - +12485551234
        """
        if not v:
            raise ValueError('Phone number is required')

        # Remove all non-digit characters except leading +
        cleaned = ''.join(filter(str.isdigit, v.lstrip('+')))

        if len(cleaned) < 10:
            raise ValueError('Phone must have at least 10 digits')

        if len(cleaned) > 15:
            raise ValueError('Phone cannot exceed 15 digits')

        return v


class LeadCreate(LeadBase):
    """Schema for creating a new lead"""
    # Optional fields for creation
    street_address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=2)
    zip_code: Optional[str] = None
    property_value: Optional[int] = Field(None, ge=0)
    roof_age: Optional[int] = Field(None, ge=0, le=100)
    roof_type: Optional[str] = Field(None, max_length=50)
    roof_size_sqft: Optional[int] = Field(None, ge=0)
    urgency: Optional[UrgencyLevel] = None
    project_description: Optional[str] = Field(None, max_length=2000)
    budget_range_min: Optional[int] = Field(None, ge=0)
    budget_range_max: Optional[int] = Field(None, ge=0)
    insurance_claim: Optional[bool] = False
    notes: Optional[str] = None

    # Scoring context (not stored, used for calculation)
    budget_confirmed: bool = False
    is_decision_maker: bool = False

    @field_validator('zip_code')
    @classmethod
    def validate_zip_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate ZIP code format (5 or 9 digits)"""
        if v is None:
            return v

        # Remove any non-digit characters
        cleaned = ''.join(filter(str.isdigit, v))

        if len(cleaned) not in [5, 9]:
            raise ValueError('ZIP code must be 5 or 9 digits')

        return v

    @field_validator('state')
    @classmethod
    def validate_state(cls, v: Optional[str]) -> Optional[str]:
        """Validate state code is uppercase 2 letters"""
        if v is None:
            return v

        if len(v) != 2:
            raise ValueError('State must be 2-letter code')

        return v.upper()

    @field_validator('budget_range_max')
    @classmethod
    def validate_budget_range(cls, v: Optional[int], info) -> Optional[int]:
        """Validate max budget is greater than min budget"""
        if v is not None and 'budget_range_min' in info.data:
            min_budget = info.data.get('budget_range_min')
            if min_budget and v < min_budget:
                raise ValueError('Maximum budget must be greater than minimum budget')
        return v


class LeadUpdate(BaseModel):
    """Schema for updating a lead"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    status: Optional[LeadStatus] = None

    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    property_value: Optional[int] = None
    roof_age: Optional[int] = None
    roof_type: Optional[str] = None
    urgency: Optional[UrgencyLevel] = None
    project_description: Optional[str] = None
    budget_range_min: Optional[int] = None
    budget_range_max: Optional[int] = None
    insurance_claim: Optional[bool] = None
    assigned_to: Optional[UUID] = None
    next_follow_up_date: Optional[datetime] = None
    notes: Optional[str] = None
    lost_reason: Optional[str] = None


class LeadResponse(BaseModel):
    """Schema for lead API response"""
    id: str
    first_name: str
    last_name: str
    phone: str
    email: Optional[str] = None
    source: LeadSource
    status: LeadStatus
    temperature: Optional[LeadTemperature] = None
    lead_score: int

    # Address
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None

    # Property
    property_value: Optional[int] = None
    roof_age: Optional[int] = None
    roof_type: Optional[str] = None
    roof_size_sqft: Optional[int] = None
    urgency: Optional[UrgencyLevel] = None

    # Project
    project_description: Optional[str] = None
    budget_range_min: Optional[int] = None
    budget_range_max: Optional[int] = None
    insurance_claim: bool = False

    # Assignment
    assigned_to: Optional[str] = None
    converted_to_customer: bool = False
    customer_id: Optional[str] = None

    # Tracking
    last_contact_date: Optional[datetime] = None
    next_follow_up_date: Optional[datetime] = None
    response_time_minutes: Optional[int] = None
    interaction_count: int = 0

    # Notes
    notes: Optional[str] = None
    lost_reason: Optional[str] = None

    # Metadata
    created_at: datetime
    updated_at: datetime

    # Computed properties
    full_name: str
    full_address: Optional[str] = None
    is_hot_lead: bool
    is_qualified: bool

    model_config = {"from_attributes": True}


class LeadScoreBreakdown(BaseModel):
    """
    Detailed breakdown of lead scoring calculation.

    Total Score = Demographics (55) + Behavioral (35) + BANT (10)
    """
    # Total
    total_score: int = Field(..., ge=0, le=100, description="Total lead score")
    temperature: LeadTemperature = Field(..., description="Lead temperature classification")

    # Demographics (55 points)
    demographics_score: int = Field(..., ge=0, le=55, description="Total demographics score")
    property_value_points: int = Field(..., ge=0, le=30, description="Property value score")
    location_points: int = Field(..., ge=0, le=10, description="Location/ZIP code score")
    income_estimate_points: int = Field(..., ge=0, le=15, description="Estimated income score")

    # Behavioral (35 points)
    behavioral_score: int = Field(..., ge=0, le=35, description="Total behavioral score")
    engagement_points: int = Field(..., ge=0, le=15, description="Website/form engagement score")
    response_time_points: int = Field(..., ge=0, le=10, description="Response time score")
    interaction_count_points: int = Field(..., ge=0, le=10, description="Interaction count score")

    # BANT (10 points)
    bant_score: int = Field(..., ge=0, le=10, description="Total BANT score")
    budget_points: int = Field(..., ge=0, le=8, description="Budget qualification score")
    authority_points: int = Field(..., ge=0, le=7, description="Authority/decision maker score")
    need_points: int = Field(..., ge=0, le=5, description="Need urgency score")
    timeline_points: int = Field(..., ge=0, le=5, description="Timeline score")


class LeadListFilters(BaseModel):
    """Filter parameters for lead list endpoint"""
    status: Optional[str] = Field(None, description="Comma-separated status values")
    temperature: Optional[str] = Field(None, description="Comma-separated temperature values")
    source: Optional[str] = Field(None, description="Comma-separated source values")
    assigned_to: Optional[UUID] = Field(None, description="Filter by assigned team member")
    created_after: Optional[datetime] = Field(None, description="Filter by creation date")
    min_score: Optional[int] = Field(None, ge=0, le=100, description="Minimum lead score")
    max_score: Optional[int] = Field(None, ge=0, le=100, description="Maximum lead score")
    zip_code: Optional[str] = Field(None, description="Filter by ZIP code")
    converted: Optional[bool] = Field(None, description="Filter by conversion status")


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(50, ge=1, le=100, description="Items per page")


class SortParams(BaseModel):
    """Sorting parameters"""
    sort: str = Field("created_at:desc", description="Sort field:direction (e.g., lead_score:desc)")


class LeadListResponse(BaseModel):
    """Response schema for lead list endpoint"""
    leads: list[LeadResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def create(cls, data: list[dict], page: int, per_page: int, total: int) -> "LeadListResponse":
        """Create paginated response"""
        pages = (total + per_page - 1) // per_page

        return cls(
            leads=[LeadResponse(**item) for item in data],
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )