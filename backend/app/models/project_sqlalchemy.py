"""
iSwitch Roofs CRM - Project SQLAlchemy Model
Version: 1.0.0

Project data model for managing roofing projects with status tracking, timeline management,
and document storage.
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, Date, Float, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date
from enum import Enum
import uuid

from app.models.base import BaseModel


class ProjectStatus(str, Enum):
    """Project status enumeration"""
    QUOTE_REQUESTED = "quote_requested"
    QUOTE_SENT = "quote_sent"
    QUOTE_APPROVED = "quote_approved"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    INSPECTION = "inspection"
    COMPLETED = "completed"
    INVOICED = "invoiced"
    PAID = "paid"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class ProjectType(str, Enum):
    """Project type enumeration"""
    FULL_REPLACEMENT = "full_replacement"
    REPAIR = "repair"
    INSPECTION = "inspection"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"
    INSURANCE_CLAIM = "insurance_claim"
    NEW_CONSTRUCTION = "new_construction"


class ProjectPriority(str, Enum):
    """Project priority level"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class RoofMaterial(str, Enum):
    """Roofing material types"""
    ASPHALT_SHINGLES = "asphalt_shingles"
    METAL = "metal"
    TILE = "tile"
    SLATE = "slate"
    FLAT_ROOF = "flat_roof"
    TPO = "tpo"
    EPDM = "epdm"
    MODIFIED_BITUMEN = "modified_bitumen"


class Project(BaseModel):
    """
    Project SQLAlchemy model for roofing projects.

    Tracks complete project lifecycle from quote to completion with status,
    timeline, financial, and document management.
    """
    __tablename__ = 'projects'

    # Basic Information (Required)
    customer_id = Column(String(36), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    project_type = Column(SQLEnum(ProjectType), nullable=False)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.QUOTE_REQUESTED)

    # Metadata
    priority = Column(SQLEnum(ProjectPriority), default=ProjectPriority.MEDIUM)
    is_insurance_claim = Column(Boolean, default=False)
    claim_number = Column(String(100), nullable=True)

    # Property/Project Details
    property_address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(2), nullable=True)
    zip_code = Column(String(20), nullable=True)

    roof_size_sqft = Column(Integer, nullable=True)
    roof_material = Column(SQLEnum(RoofMaterial), nullable=True)
    roof_pitch = Column(String(20), nullable=True)
    num_layers = Column(Integer, nullable=True)

    # Project Scope
    description = Column(Text, nullable=True)
    special_requirements = Column(String(1000), nullable=True)

    # Financial Information
    quote_amount = Column(Integer, nullable=True)
    final_amount = Column(Integer, nullable=True)
    amount_paid = Column(Integer, default=0)
    payment_terms = Column(String(500), nullable=True)

    # Timeline
    quote_date = Column(Date, nullable=True)
    approval_date = Column(Date, nullable=True)
    scheduled_start_date = Column(Date, nullable=True)
    actual_start_date = Column(Date, nullable=True)
    estimated_completion_date = Column(Date, nullable=True)
    actual_completion_date = Column(Date, nullable=True)
    estimated_duration_days = Column(Integer, nullable=True)

    # Assignment
    project_manager_id = Column(String(36), nullable=True)
    lead_installer_id = Column(String(36), nullable=True)
    sales_rep_id = Column(String(36), nullable=True)

    # Quality & Compliance
    warranty_years = Column(Integer, nullable=True)
    permit_number = Column(String(100), nullable=True)
    permit_approved = Column(Boolean, default=False)
    final_inspection_passed = Column(Boolean, default=False)
    inspection_date = Column(Date, nullable=True)

    # Customer Satisfaction
    customer_rating = Column(Float, nullable=True)
    review_requested = Column(Boolean, default=False)
    review_submitted = Column(Boolean, default=False)

    # Documents (stored in Supabase Storage, references stored here)
    contract_document_url = Column(Text, nullable=True)
    invoice_document_url = Column(Text, nullable=True)
    permit_document_url = Column(Text, nullable=True)
    warranty_document_url = Column(Text, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)
    customer_notes = Column(Text, nullable=True)

    # Cancellation
    cancellation_reason = Column(String(500), nullable=True)
    cancelled_date = Column(Date, nullable=True)

    @property
    def full_address(self) -> Optional[str]:
        """Get formatted project address"""
        if not self.property_address:
            return None

        parts = [self.property_address]
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.zip_code:
            parts.append(self.zip_code)

        return ", ".join(parts)

    @property
    def is_active(self) -> bool:
        """Check if project is in active status"""
        active_statuses = [
            ProjectStatus.QUOTE_SENT,
            ProjectStatus.QUOTE_APPROVED,
            ProjectStatus.SCHEDULED,
            ProjectStatus.IN_PROGRESS,
            ProjectStatus.INSPECTION
        ]
        return self.status in active_statuses

    @property
    def is_completed(self) -> bool:
        """Check if project is completed"""
        return self.status in [ProjectStatus.COMPLETED, ProjectStatus.INVOICED, ProjectStatus.PAID]

    @property
    def balance_due(self) -> int:
        """Calculate remaining balance"""
        if self.final_amount:
            return max(0, self.final_amount - self.amount_paid)
        return 0

    @property
    def is_paid_in_full(self) -> bool:
        """Check if project is fully paid"""
        return self.balance_due == 0 and self.final_amount and self.final_amount > 0

    @property
    def days_until_completion(self) -> Optional[int]:
        """Calculate days until estimated completion"""
        if self.estimated_completion_date:
            delta = self.estimated_completion_date - date.today()
            return delta.days
        return None

    @property
    def is_overdue(self) -> bool:
        """Check if project is past estimated completion date"""
        if self.estimated_completion_date and not self.actual_completion_date:
            return date.today() > self.estimated_completion_date
        return False


# Pydantic schemas for API validation
class ProjectCreateSchema(BaseModel):
    """Schema for creating a new project"""
    model_config = ConfigDict(from_attributes=True)

    customer_id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    project_type: ProjectType
    priority: ProjectPriority = ProjectPriority.MEDIUM

    # Optional fields
    property_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    is_insurance_claim: Optional[bool] = False
    claim_number: Optional[str] = None
    roof_size_sqft: Optional[int] = None
    roof_material: Optional[RoofMaterial] = None
    description: Optional[str] = None
    quote_amount: Optional[int] = None
    scheduled_start_date: Optional[date] = None
    estimated_duration_days: Optional[int] = None
    project_manager_id: Optional[UUID] = None
    sales_rep_id: Optional[UUID] = None
    notes: Optional[str] = None

    @field_validator('zip_code')
    @classmethod
    def validate_zip_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate ZIP code format"""
        if v is None:
            return v

        cleaned = ''.join(filter(str.isdigit, v))

        if len(cleaned) not in [5, 9]:
            raise ValueError('ZIP code must be 5 or 9 digits')

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


class ProjectUpdateSchema(BaseModel):
    """Schema for updating a project"""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[ProjectStatus] = None
    priority: Optional[ProjectPriority] = None
    description: Optional[str] = None
    quote_amount: Optional[int] = None
    final_amount: Optional[int] = None
    amount_paid: Optional[int] = None
    scheduled_start_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    estimated_completion_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    project_manager_id: Optional[UUID] = None
    lead_installer_id: Optional[UUID] = None
    permit_number: Optional[str] = None
    permit_approved: Optional[bool] = None
    final_inspection_passed: Optional[bool] = None
    customer_rating: Optional[float] = None
    notes: Optional[str] = None
    customer_notes: Optional[str] = None
    cancellation_reason: Optional[str] = None


class ProjectResponseSchema(BaseModel):
    """Schema for project API response"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    name: str
    project_type: ProjectType
    status: ProjectStatus
    priority: ProjectPriority
    property_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    quote_amount: Optional[int] = None
    final_amount: Optional[int] = None
    amount_paid: int = 0
    scheduled_start_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    estimated_completion_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime


class ProjectListFiltersSchema(BaseModel):
    """Filter parameters for project list endpoint"""
    status: Optional[str] = Field(None, description="Comma-separated status values")
    project_type: Optional[str] = Field(None, description="Comma-separated type values")
    priority: Optional[str] = Field(None, description="Comma-separated priority values")
    customer_id: Optional[UUID] = Field(None, description="Filter by customer")
    project_manager_id: Optional[UUID] = Field(None, description="Filter by project manager")
    is_insurance_claim: Optional[bool] = Field(None, description="Filter insurance claims")
    scheduled_after: Optional[date] = Field(None, description="Scheduled after date")
    scheduled_before: Optional[date] = Field(None, description="Scheduled before date")
    min_amount: Optional[int] = Field(None, ge=0, description="Minimum project amount")
    is_overdue: Optional[bool] = Field(None, description="Filter overdue projects")