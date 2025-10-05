"""
iSwitch Roofs CRM - Project Model
Version: 1.0.0

Project data model for managing roofing projects with status tracking, timeline management,
and document storage.
"""

from datetime import date
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.base import BaseDBModel


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
    status: ProjectStatus = Field(
        default=ProjectStatus.QUOTE_REQUESTED, description="Current status"
    )

    # Metadata
    priority: ProjectPriority = Field(default=ProjectPriority.MEDIUM, description="Priority level")
    is_insurance_claim: bool = Field(
        default=False, description="Is this an insurance claim project?"
    )
    claim_number: str | None = Field(None, max_length=100, description="Insurance claim number")

    # Property/Project Details
    property_address: str | None = Field(None, max_length=255, description="Project site address")
    city: str | None = Field(None, max_length=100, description="City")
    state: str | None = Field(None, max_length=2, description="State code")
    zip_code: str | None = Field(None, description="ZIP code")

    roof_size_sqft: int | None = Field(None, ge=0, description="Roof size in square feet")
    roof_material: RoofMaterial | None = Field(None, description="Roofing material to be used")
    roof_pitch: str | None = Field(None, max_length=20, description="Roof pitch (e.g., 6/12)")
    num_layers: int | None = Field(None, ge=1, le=5, description="Number of existing roof layers")

    # Project Scope
    description: str | None = Field(
        None, max_length=2000, description="Project description and scope"
    )
    special_requirements: str | None = Field(
        None, max_length=1000, description="Special requirements or notes"
    )

    # Financial Information
    quote_amount: int | None = Field(None, ge=0, description="Initial quote amount in USD")
    final_amount: int | None = Field(None, ge=0, description="Final invoiced amount in USD")
    amount_paid: int = Field(default=0, ge=0, description="Amount paid to date in USD")
    payment_terms: str | None = Field(None, max_length=500, description="Payment terms")

    # Timeline
    quote_date: date | None = Field(None, description="Date quote was sent")
    approval_date: date | None = Field(None, description="Date quote was approved")
    scheduled_start_date: date | None = Field(None, description="Scheduled start date")
    actual_start_date: date | None = Field(None, description="Actual start date")
    estimated_completion_date: date | None = Field(None, description="Estimated completion date")
    actual_completion_date: date | None = Field(None, description="Actual completion date")
    estimated_duration_days: int | None = Field(
        None, ge=1, description="Estimated duration in days"
    )

    # Assignment
    project_manager_id: UUID | None = Field(None, description="Assigned project manager")
    lead_installer_id: UUID | None = Field(None, description="Lead installer/crew chief")
    sales_rep_id: UUID | None = Field(None, description="Sales representative")

    # Quality & Compliance
    warranty_years: int | None = Field(None, ge=0, le=50, description="Warranty period in years")
    permit_number: str | None = Field(None, max_length=100, description="Building permit number")
    permit_approved: bool = Field(default=False, description="Has permit been approved?")
    final_inspection_passed: bool = Field(default=False, description="Did final inspection pass?")
    inspection_date: date | None = Field(None, description="Final inspection date")

    # Customer Satisfaction
    customer_rating: float | None = Field(
        None, ge=0.0, le=5.0, description="Customer rating (1-5 stars)"
    )
    review_requested: bool = Field(default=False, description="Has review request been sent?")
    review_submitted: bool = Field(default=False, description="Has customer submitted review?")

    # Documents (stored in Supabase Storage, references stored here)
    contract_document_url: str | None = Field(None, description="Contract document URL")
    invoice_document_url: str | None = Field(None, description="Invoice document URL")
    permit_document_url: str | None = Field(None, description="Permit document URL")
    warranty_document_url: str | None = Field(None, description="Warranty document URL")

    # Notes
    notes: str | None = Field(None, description="Internal project notes")
    customer_notes: str | None = Field(None, description="Notes visible to customer")

    # Cancellation
    cancellation_reason: str | None = Field(None, max_length=500, description="Reason if cancelled")
    cancelled_date: date | None = Field(None, description="Date cancelled")

    @field_validator("zip_code")
    @classmethod
    def validate_zip_code(cls, v: str | None) -> str | None:
        """Validate ZIP code format"""
        if v is None:
            return v

        cleaned = "".join(filter(str.isdigit, v))

        if len(cleaned) not in [5, 9]:
            raise ValueError("ZIP code must be 5 or 9 digits")

        return v

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str | None) -> str | None:
        """Validate state code"""
        if v is None:
            return v

        if len(v) != 2:
            raise ValueError("State must be 2-letter code")

        return v.upper()

    @property
    def full_address(self) -> str | None:
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
            ProjectStatus.INSPECTION,
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
    def days_until_completion(self) -> int | None:
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
    property_address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    is_insurance_claim: bool | None = False
    claim_number: str | None = None
    roof_size_sqft: int | None = None
    roof_material: RoofMaterial | None = None
    description: str | None = None
    quote_amount: int | None = None
    scheduled_start_date: date | None = None
    estimated_duration_days: int | None = None
    project_manager_id: UUID | None = None
    sales_rep_id: UUID | None = None
    notes: str | None = None


class ProjectUpdate(BaseModel):
    """Schema for updating a project"""

    name: str | None = Field(None, min_length=1, max_length=200)
    status: ProjectStatus | None = None
    priority: ProjectPriority | None = None
    description: str | None = None
    quote_amount: int | None = None
    final_amount: int | None = None
    amount_paid: int | None = None
    scheduled_start_date: date | None = None
    actual_start_date: date | None = None
    estimated_completion_date: date | None = None
    actual_completion_date: date | None = None
    project_manager_id: UUID | None = None
    lead_installer_id: UUID | None = None
    permit_number: str | None = None
    permit_approved: bool | None = None
    final_inspection_passed: bool | None = None
    customer_rating: float | None = None
    notes: str | None = None
    customer_notes: str | None = None
    cancellation_reason: str | None = None


class ProjectResponse(BaseModel):
    """Schema for project API response"""

    data: Project
    customer: dict | None = None  # Customer data
    documents: list[dict] | None = None  # Project documents
    timeline_events: list[dict] | None = None  # Status history


class ProjectListFilters(BaseModel):
    """Filter parameters for project list endpoint"""

    status: str | None = Field(None, description="Comma-separated status values")
    project_type: str | None = Field(None, description="Comma-separated type values")
    priority: str | None = Field(None, description="Comma-separated priority values")
    customer_id: UUID | None = Field(None, description="Filter by customer")
    project_manager_id: UUID | None = Field(None, description="Filter by project manager")
    is_insurance_claim: bool | None = Field(None, description="Filter insurance claims")
    scheduled_after: date | None = Field(None, description="Scheduled after date")
    scheduled_before: date | None = Field(None, description="Scheduled before date")
    min_amount: int | None = Field(None, ge=0, description="Minimum project amount")
    is_overdue: bool | None = Field(None, description="Filter overdue projects")
