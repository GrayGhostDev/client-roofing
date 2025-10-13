"""
iSwitch Roofs CRM - Lead Model
Version: 1.0.0

Comprehensive lead data model with validation, scoring, and temperature classification.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

# NOTE: Do NOT import BaseDBModel here - it causes conflicts with SQLAlchemy models
# The actual Lead SQLAlchemy model is in lead_sqlalchemy.py
# This file contains ONLY enums and Pydantic schemas


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

    HOT = "hot"  # 80-100 points
    WARM = "warm"  # 60-79 points
    COOL = "cool"  # 40-59 points
    COLD = "cold"  # 0-39 points


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


# ============================================================================
# NOTE: The Lead SQLAlchemy ORM model is in lead_sqlalchemy.py
# This file contains ONLY Pydantic schemas and enums to avoid conflicts
# ============================================================================

# The Lead(BaseDBModel) class was removed from here to prevent conflicts
# with the SQLAlchemy Lead model in lead_sqlalchemy.py
# If you need the ORM model, import from: app.models.lead_sqlalchemy


class LeadScoreBreakdown(BaseModel):
    """
    Detailed breakdown of lead scoring calculation.

    Total Score = Demographics (55) + Behavioral (35) + BANT (10)
    """

    model_config = {"from_attributes": True}

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


class LeadCreate(BaseModel):
    """Schema for creating a new lead"""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str
    email: EmailStr | None = None
    source: LeadSource

    # Optional fields
    street_address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    property_value: int | None = None
    roof_age: int | None = None
    roof_type: str | None = None
    urgency: UrgencyLevel | None = None
    project_description: str | None = None
    budget_range_min: int | None = None
    budget_range_max: int | None = None
    insurance_claim: bool | None = False
    notes: str | None = None

    # Scoring context (not stored, used for calculation)
    budget_confirmed: bool = False
    is_decision_maker: bool = False


class LeadUpdate(BaseModel):
    """Schema for updating a lead"""

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = None
    email: EmailStr | None = None
    status: LeadStatus | None = None

    street_address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    property_value: int | None = None
    roof_age: int | None = None
    roof_type: str | None = None
    urgency: UrgencyLevel | None = None
    project_description: str | None = None
    budget_range_min: int | None = None
    budget_range_max: int | None = None
    insurance_claim: bool | None = None
    assigned_to: UUID | None = None
    next_follow_up_date: datetime | None = None
    notes: str | None = None
    lost_reason: str | None = None


class LeadResponse(BaseModel):
    """
    Schema for lead API response

    Note: This should use the SQLAlchemy Lead model from lead_sqlalchemy
    when converting database records to responses
    """

    model_config = {"from_attributes": True}

    # These fields match the SQLAlchemy Lead model
    id: str
    first_name: str
    last_name: str
    phone: str
    email: EmailStr | None = None
    source: LeadSource
    status: LeadStatus
    temperature: LeadTemperature | None = None
    lead_score: int = 0

    street_address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None

    property_value: int | None = None
    roof_age: int | None = None
    roof_type: str | None = None
    roof_size_sqft: int | None = None
    urgency: UrgencyLevel | None = None

    project_description: str | None = None
    budget_range_min: int | None = None
    budget_range_max: int | None = None
    insurance_claim: bool | None = False

    assigned_to: UUID | None = None
    converted_to_customer: bool = False
    customer_id: UUID | None = None

    last_contact_date: datetime | None = None
    next_follow_up_date: datetime | None = None
    response_time_minutes: int | None = None
    interaction_count: int = 0

    notes: str | None = None
    lost_reason: str | None = None

    created_at: datetime
    updated_at: datetime

    score_breakdown: LeadScoreBreakdown | None = None


class LeadListFilters(BaseModel):
    """Filter parameters for lead list endpoint"""

    status: str | None = Field(None, description="Comma-separated status values")
    temperature: str | None = Field(None, description="Comma-separated temperature values")
    source: str | None = Field(None, description="Comma-separated source values")
    assigned_to: UUID | None = Field(None, description="Filter by assigned team member")
    created_after: datetime | None = Field(None, description="Filter by creation date")
    min_score: int | None = Field(None, ge=0, le=100, description="Minimum lead score")
    max_score: int | None = Field(None, ge=0, le=100, description="Maximum lead score")
    zip_code: str | None = Field(None, description="Filter by ZIP code")
    converted: bool | None = Field(None, description="Filter by conversion status")
