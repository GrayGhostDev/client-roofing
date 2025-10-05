"""
iSwitch Roofs CRM - Team Member Model
Version: 1.0.0

Team member data model for managing staff, roles, performance, and assignments.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from enum import Enum

from app.models.base import BaseDBModel


class TeamRole(str, Enum):
    """Team member role enumeration"""
    ADMIN = "admin"                    # Full system access
    OWNER = "owner"                    # Business owner
    MANAGER = "manager"                # Operations manager
    SALES_REP = "sales_rep"           # Sales representative
    PROJECT_MANAGER = "project_manager"  # Project manager
    INSTALLER = "installer"            # Field installer/technician
    OFFICE_ADMIN = "office_admin"      # Office administrator
    MARKETING = "marketing"            # Marketing specialist
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
    status: TeamMemberStatus = Field(default=TeamMemberStatus.ACTIVE, description="Employment status")
    availability_status: AvailabilityStatus = Field(default=AvailabilityStatus.AVAILABLE, description="Current availability")

    # Employment Details
    employee_id: Optional[str] = Field(None, max_length=50, description="Employee ID number")
    hire_date: Optional[date] = Field(None, description="Date hired")
    termination_date: Optional[date] = Field(None, description="Date terminated")
    department: Optional[str] = Field(None, max_length=100, description="Department")

    # Contact Information
    personal_email: Optional[EmailStr] = Field(None, description="Personal email")
    personal_phone: Optional[str] = Field(None, description="Personal phone")
    address: Optional[str] = Field(None, max_length=255, description="Home address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=2, description="State")
    zip_code: Optional[str] = Field(None, description="ZIP code")

    # Emergency Contact
    emergency_contact_name: Optional[str] = Field(None, max_length=200, description="Emergency contact name")
    emergency_contact_phone: Optional[str] = Field(None, max_length=20, description="Emergency contact phone")
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50, description="Relationship")

    # Permissions & Access
    can_view_all_leads: bool = Field(default=False, description="Can view all leads")
    can_manage_team: bool = Field(default=False, description="Can manage team members")
    can_access_reports: bool = Field(default=False, description="Can access analytics reports")
    can_approve_quotes: bool = Field(default=False, description="Can approve quotes")
    max_quote_approval_amount: Optional[int] = Field(None, ge=0, description="Max quote approval amount USD")

    # Performance Metrics
    active_leads_count: int = Field(default=0, ge=0, description="Currently assigned active leads")
    active_projects_count: int = Field(default=0, ge=0, description="Currently assigned active projects")
    total_leads_converted: int = Field(default=0, ge=0, description="Total leads converted to customers")
    total_revenue_generated: int = Field(default=0, ge=0, description="Total revenue generated USD")
    avg_response_time_minutes: Optional[int] = Field(None, ge=0, description="Average response time")
    conversion_rate: Optional[float] = Field(None, ge=0.0, le=100.0, description="Lead conversion rate %")

    # Sales Performance (for sales roles)
    monthly_sales_target: Optional[int] = Field(None, ge=0, description="Monthly sales target USD")
    monthly_sales_actual: int = Field(default=0, ge=0, description="Current month sales USD")
    quarterly_sales_target: Optional[int] = Field(None, ge=0, description="Quarterly sales target USD")
    quarterly_sales_actual: int = Field(default=0, ge=0, description="Current quarter sales USD")

    # Customer Satisfaction
    avg_customer_rating: Optional[float] = Field(None, ge=0.0, le=5.0, description="Average customer rating")
    total_reviews: int = Field(default=0, ge=0, description="Total customer reviews received")

    # Availability & Scheduling
    work_hours_start: Optional[str] = Field(None, description="Work hours start time (HH:MM)")
    work_hours_end: Optional[str] = Field(None, description="Work hours end time (HH:MM)")
    work_days: Optional[str] = Field(None, description="Work days (comma-separated: Mon,Tue,Wed,Thu,Fri)")
    timezone: str = Field(default="America/Detroit", description="Timezone")

    # Calendar Integration
    google_calendar_id: Optional[str] = Field(None, description="Google Calendar ID")
    outlook_calendar_id: Optional[str] = Field(None, description="Outlook Calendar ID")

    # Compensation (optional, sensitive)
    hourly_rate: Optional[float] = Field(None, ge=0, description="Hourly rate USD")
    salary: Optional[int] = Field(None, ge=0, description="Annual salary USD")
    commission_rate: Optional[float] = Field(None, ge=0, le=100, description="Commission rate %")

    # Skills & Certifications
    skills: Optional[str] = Field(None, description="Skills (comma-separated)")
    certifications: Optional[str] = Field(None, description="Certifications (comma-separated)")
    languages: Optional[str] = Field(None, description="Languages spoken (comma-separated)")

    # Profile
    profile_photo_url: Optional[str] = Field(None, description="Profile photo URL")
    bio: Optional[str] = Field(None, max_length=1000, description="Bio/description")
    notes: Optional[str] = Field(None, description="Internal notes")

    # Last Activity
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")

    @field_validator('phone', 'personal_phone', 'emergency_contact_phone')
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
    def monthly_sales_progress(self) -> Optional[float]:
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
    employee_id: Optional[str] = None
    hire_date: Optional[date] = None
    department: Optional[str] = None
    personal_email: Optional[EmailStr] = None
    personal_phone: Optional[str] = None
    work_hours_start: Optional[str] = None
    work_hours_end: Optional[str] = None
    work_days: Optional[str] = None
    can_view_all_leads: Optional[bool] = False
    can_manage_team: Optional[bool] = False
    can_access_reports: Optional[bool] = False
    monthly_sales_target: Optional[int] = None
    notes: Optional[str] = None


class TeamMemberUpdate(BaseModel):
    """Schema for updating a team member"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: Optional[TeamRole] = None
    status: Optional[TeamMemberStatus] = None
    availability_status: Optional[AvailabilityStatus] = None
    department: Optional[str] = None
    work_hours_start: Optional[str] = None
    work_hours_end: Optional[str] = None
    work_days: Optional[str] = None
    can_view_all_leads: Optional[bool] = None
    can_manage_team: Optional[bool] = None
    can_access_reports: Optional[bool] = None
    monthly_sales_target: Optional[int] = None
    quarterly_sales_target: Optional[int] = None
    notes: Optional[str] = None


class TeamMemberResponse(BaseModel):
    """Schema for team member API response"""
    data: TeamMember
    performance_metrics: Optional[dict] = None  # Detailed performance data
    current_assignments: Optional[dict] = None  # Current leads/projects


class TeamMemberListFilters(BaseModel):
    """Filter parameters for team member list endpoint"""
    role: Optional[str] = Field(None, description="Comma-separated roles")
    status: Optional[TeamMemberStatus] = Field(None, description="Filter by status")
    availability_status: Optional[AvailabilityStatus] = Field(None, description="Filter by availability")
    department: Optional[str] = Field(None, description="Filter by department")
    can_view_all_leads: Optional[bool] = Field(None, description="Filter by permission")
    has_active_assignments: Optional[bool] = Field(None, description="Filter members with assignments")
