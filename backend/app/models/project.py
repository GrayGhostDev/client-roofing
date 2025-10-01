"""
iSwitch Roofs CRM - Project Model
Version: 1.0.0

Project data model for managing roofing projects with status tracking, timeline management,
and document storage.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date
from enum import Enum

from backend.app.models.base import BaseDBModel


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


class Project(BaseDBModel):
    """
    Project data model for roofing projects.

    Tracks complete project lifecycle from quote to completion with status,
    timeline, financial, and document management.
    """

    # Basic Information (Required)
    customer_id: UUID = Field(..., description="Associated customer ID")
    name: str = Field(..., min_length=1, max_length=200, description="Project name/description")
    project_type: ProjectType = Field(..., description="Type of project")
    status: ProjectStatus = Field(default=ProjectStatus.QUOTE_REQUESTED, description="Current status")

    # Metadata
    priority: ProjectPriority = Field(default=ProjectPriority.MEDIUM, description="Priority level")
    is_insurance_claim: bool = Field(default=False, description="Is this an insurance claim project?")
    claim_number: Optional[str] = Field(None, max_length=100, description="Insurance claim number")

    # Property/Project Details
    property_address: Optional[str] = Field(None, max_length=255, description="Project site address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=2, description="State code")
    zip_code: Optional[str] = Field(None, description="ZIP code")

    roof_size_sqft: Optional[int] = Field(None, ge=0, description="Roof size in square feet")
    roof_material: Optional[RoofMaterial] = Field(None, description="Roofing material to be used")
    roof_pitch: Optional[str] = Field(None, max_length=20, description="Roof pitch (e.g., 6/12)")
    num_layers: Optional[int] = Field(None, ge=1, le=5, description="Number of existing roof layers")

    # Project Scope
    description: Optional[str] = Field(None, max_length=2000, description="Project description and scope")
    special_requirements: Optional[str] = Field(None, max_length=1000, description="Special requirements or notes")

    # Financial Information
    quote_amount: Optional[int] = Field(None, ge=0, description="Initial quote amount in USD")
    final_amount: Optional[int] = Field(None, ge=0, description="Final invoiced amount in USD")
    amount_paid: int = Field(default=0, ge=0, description="Amount paid to date in USD")
    payment_terms: Optional[str] = Field(None, max_length=500, description="Payment terms")

    # Timeline
    quote_date: Optional[date] = Field(None, description="Date quote was sent")
    approval_date: Optional[date] = Field(None, description="Date quote was approved")
    scheduled_start_date: Optional[date] = Field(None, description="Scheduled start date")
    actual_start_date: Optional[date] = Field(None, description="Actual start date")
    estimated_completion_date: Optional[date] = Field(None, description="Estimated completion date")
    actual_completion_date: Optional[date] = Field(None, description="Actual completion date")
    estimated_duration_days: Optional[int] = Field(None, ge=1, description="Estimated duration in days")

    # Assignment
    project_manager_id: Optional[UUID] = Field(None, description="Assigned project manager")
    lead_installer_id: Optional[UUID] = Field(None, description="Lead installer/crew chief")
    sales_rep_id: Optional[UUID] = Field(None, description="Sales representative")

    # Quality & Compliance
    warranty_years: Optional[int] = Field(None, ge=0, le=50, description="Warranty period in years")
    permit_number: Optional[str] = Field(None, max_length=100, description="Building permit number")
    permit_approved: bool = Field(default=False, description="Has permit been approved?")
    final_inspection_passed: bool = Field(default=False, description="Did final inspection pass?")
    inspection_date: Optional[date] = Field(None, description="Final inspection date")

    # Customer Satisfaction
    customer_rating: Optional[float] = Field(None, ge=0.0, le=5.0, description="Customer rating (1-5 stars)")
    review_requested: bool = Field(default=False, description="Has review request been sent?")
    review_submitted: bool = Field(default=False, description="Has customer submitted review?")

    # Documents (stored in Supabase Storage, references stored here)
    contract_document_url: Optional[str] = Field(None, description="Contract document URL")
    invoice_document_url: Optional[str] = Field(None, description="Invoice document URL")
    permit_document_url: Optional[str] = Field(None, description="Permit document URL")
    warranty_document_url: Optional[str] = Field(None, description="Warranty document URL")

    # Notes
    notes: Optional[str] = Field(None, description="Internal project notes")
    customer_notes: Optional[str] = Field(None, description="Notes visible to customer")

    # Cancellation
    cancellation_reason: Optional[str] = Field(None, max_length=500, description="Reason if cancelled")
    cancelled_date: Optional[date] = Field(None, description="Date cancelled")

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


class ProjectCreate(BaseModel):
    """Schema for creating a new project"""
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


class ProjectUpdate(BaseModel):
    """Schema for updating a project"""
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


class ProjectResponse(BaseModel):
    """Schema for project API response"""
    data: Project
    customer: Optional[dict] = None  # Customer data
    documents: Optional[List[dict]] = None  # Project documents
    timeline_events: Optional[List[dict]] = None  # Status history


class ProjectListFilters(BaseModel):
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
