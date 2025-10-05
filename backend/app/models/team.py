"""
iSwitch Roofs CRM - Team Member Model
Version: 1.0.0

Team member data model for managing staff, roles, performance, and assignments.
"""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.base import BaseDBModel


class TeamRole(str, Enum):
    """Team member role enumeration"""

    ADMIN = "admin"  # Full system access
    OWNER = "owner"  # Business owner
    MANAGER = "manager"  # Operations manager
    SALES_REP = "sales_rep"  # Sales representative
    PROJECT_MANAGER = "project_manager"  # Project manager
    INSTALLER = "installer"  # Field installer/technician
    OFFICE_ADMIN = "office_admin"  # Office administrator
    MARKETING = "marketing"  # Marketing specialist
    CUSTOMER_SERVICE = "customer_service"  # Customer service rep


class TeamMemberStatus(str, Enum):
    """Team member status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"


class AvailabilityStatus(str, Enum):
    """Current availability status"""

    AVAILABLE = "available"
    BUSY = "busy"
    IN_FIELD = "in_field"
    IN_MEETING = "in_meeting"
    ON_BREAK = "on_break"
    OFF_DUTY = "off_duty"


class TeamMember(BaseDBModel):
    """
    Team member data model for staff management.

    Tracks employee information, roles, permissions, performance metrics,
    and availability for assignment and scheduling.
    """

    # Basic Information (Required)
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    email: EmailStr = Field(..., description="Work email address")
    phone: str = Field(..., description="Work phone number")

    # Role & Status
    role: TeamRole = Field(..., description="Team member role")
    status: TeamMemberStatus = Field(
        default=TeamMemberStatus.ACTIVE, description="Employment status"
    )
    availability_status: AvailabilityStatus = Field(
        default=AvailabilityStatus.AVAILABLE, description="Current availability"
    )

    # Employment Details
    employee_id: str | None = Field(None, max_length=50, description="Employee ID number")
    hire_date: date | None = Field(None, description="Date hired")
    termination_date: date | None = Field(None, description="Date terminated")
    department: str | None = Field(None, max_length=100, description="Department")

    # Contact Information
    personal_email: EmailStr | None = Field(None, description="Personal email")
    personal_phone: str | None = Field(None, description="Personal phone")
    address: str | None = Field(None, max_length=255, description="Home address")
    city: str | None = Field(None, max_length=100, description="City")
    state: str | None = Field(None, max_length=2, description="State")
    zip_code: str | None = Field(None, description="ZIP code")

    # Emergency Contact
    emergency_contact_name: str | None = Field(
        None, max_length=200, description="Emergency contact name"
    )
    emergency_contact_phone: str | None = Field(
        None, max_length=20, description="Emergency contact phone"
    )
    emergency_contact_relationship: str | None = Field(
        None, max_length=50, description="Relationship"
    )

    # Permissions & Access
    can_view_all_leads: bool = Field(default=False, description="Can view all leads")
    can_manage_team: bool = Field(default=False, description="Can manage team members")
    can_access_reports: bool = Field(default=False, description="Can access analytics reports")
    can_approve_quotes: bool = Field(default=False, description="Can approve quotes")
    max_quote_approval_amount: int | None = Field(
        None, ge=0, description="Max quote approval amount USD"
    )

    # Performance Metrics
    active_leads_count: int = Field(default=0, ge=0, description="Currently assigned active leads")
    active_projects_count: int = Field(
        default=0, ge=0, description="Currently assigned active projects"
    )
    total_leads_converted: int = Field(
        default=0, ge=0, description="Total leads converted to customers"
    )
    total_revenue_generated: int = Field(default=0, ge=0, description="Total revenue generated USD")
    avg_response_time_minutes: int | None = Field(
        None, ge=0, description="Average response time"
    )
    conversion_rate: float | None = Field(
        None, ge=0.0, le=100.0, description="Lead conversion rate %"
    )

    # Sales Performance (for sales roles)
    monthly_sales_target: int | None = Field(None, ge=0, description="Monthly sales target USD")
    monthly_sales_actual: int = Field(default=0, ge=0, description="Current month sales USD")
    quarterly_sales_target: int | None = Field(
        None, ge=0, description="Quarterly sales target USD"
    )
    quarterly_sales_actual: int = Field(default=0, ge=0, description="Current quarter sales USD")

    # Customer Satisfaction
    avg_customer_rating: float | None = Field(
        None, ge=0.0, le=5.0, description="Average customer rating"
    )
    total_reviews: int = Field(default=0, ge=0, description="Total customer reviews received")

    # Availability & Scheduling
    work_hours_start: str | None = Field(None, description="Work hours start time (HH:MM)")
    work_hours_end: str | None = Field(None, description="Work hours end time (HH:MM)")
    work_days: str | None = Field(
        None, description="Work days (comma-separated: Mon,Tue,Wed,Thu,Fri)"
    )
    timezone: str = Field(default="America/Detroit", description="Timezone")

    # Calendar Integration
    google_calendar_id: str | None = Field(None, description="Google Calendar ID")
    outlook_calendar_id: str | None = Field(None, description="Outlook Calendar ID")

    # Compensation (optional, sensitive)
    hourly_rate: float | None = Field(None, ge=0, description="Hourly rate USD")
    salary: int | None = Field(None, ge=0, description="Annual salary USD")
    commission_rate: float | None = Field(None, ge=0, le=100, description="Commission rate %")

    # Skills & Certifications
    skills: str | None = Field(None, description="Skills (comma-separated)")
    certifications: str | None = Field(None, description="Certifications (comma-separated)")
    languages: str | None = Field(None, description="Languages spoken (comma-separated)")

    # Profile
    profile_photo_url: str | None = Field(None, description="Profile photo URL")
    bio: str | None = Field(None, max_length=1000, description="Bio/description")
    notes: str | None = Field(None, description="Internal notes")

    # Last Activity
    last_login: datetime | None = Field(None, description="Last login timestamp")
    last_activity: datetime | None = Field(None, description="Last activity timestamp")

    @field_validator("phone", "personal_phone", "emergency_contact_phone")
    @classmethod
    def validate_phone_format(cls, v: str | None) -> str | None:
        """Validate phone number format"""
        if not v:
            return v

        cleaned = "".join(filter(str.isdigit, v.lstrip("+")))

        if len(cleaned) < 10:
            raise ValueError("Phone must have at least 10 digits")

        if len(cleaned) > 15:
            raise ValueError("Phone cannot exceed 15 digits")

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
    def full_name(self) -> str:
        """Get full name"""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_active(self) -> bool:
        """Check if team member is active"""
        return self.status == TeamMemberStatus.ACTIVE

    @property
    def is_sales_role(self) -> bool:
        """Check if role is sales-related"""
        return self.role in [TeamRole.SALES_REP, TeamRole.OWNER, TeamRole.MANAGER]

    @property
    def is_field_role(self) -> bool:
        """Check if role is field-based"""
        return self.role in [TeamRole.INSTALLER, TeamRole.PROJECT_MANAGER]

    @property
    def monthly_sales_progress(self) -> float | None:
        """Calculate monthly sales progress percentage"""
        if self.monthly_sales_target and self.monthly_sales_target > 0:
            return (self.monthly_sales_actual / self.monthly_sales_target) * 100
        return None

    @property
    def is_meeting_target(self) -> bool:
        """Check if meeting sales target"""
        progress = self.monthly_sales_progress
        return progress >= 100 if progress else False


class TeamMemberCreate(BaseModel):
    """Schema for creating a new team member"""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str
    role: TeamRole

    # Optional fields
    employee_id: str | None = None
    hire_date: date | None = None
    department: str | None = None
    personal_email: EmailStr | None = None
    personal_phone: str | None = None
    work_hours_start: str | None = None
    work_hours_end: str | None = None
    work_days: str | None = None
    can_view_all_leads: bool | None = False
    can_manage_team: bool | None = False
    can_access_reports: bool | None = False
    monthly_sales_target: int | None = None
    notes: str | None = None


class TeamMemberUpdate(BaseModel):
    """Schema for updating a team member"""

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = None
    role: TeamRole | None = None
    status: TeamMemberStatus | None = None
    availability_status: AvailabilityStatus | None = None
    department: str | None = None
    work_hours_start: str | None = None
    work_hours_end: str | None = None
    work_days: str | None = None
    can_view_all_leads: bool | None = None
    can_manage_team: bool | None = None
    can_access_reports: bool | None = None
    monthly_sales_target: int | None = None
    quarterly_sales_target: int | None = None
    notes: str | None = None


class TeamMemberResponse(BaseModel):
    """Schema for team member API response"""

    data: TeamMember
    performance_metrics: dict | None = None  # Detailed performance data
    current_assignments: dict | None = None  # Current leads/projects


class TeamMemberListFilters(BaseModel):
    """Filter parameters for team member list endpoint"""

    role: str | None = Field(None, description="Comma-separated roles")
    status: TeamMemberStatus | None = Field(None, description="Filter by status")
    availability_status: AvailabilityStatus | None = Field(
        None, description="Filter by availability"
    )
    department: str | None = Field(None, description="Filter by department")
    can_view_all_leads: bool | None = Field(None, description="Filter by permission")
    has_active_assignments: bool | None = Field(
        None, description="Filter members with assignments"
    )
