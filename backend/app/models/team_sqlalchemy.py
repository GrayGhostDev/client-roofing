"""
iSwitch Roofs CRM - Team Member SQLAlchemy Model
Version: 1.0.0

Team member data model for managing staff, roles, performance, and assignments.
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, Date, Float, Enum as SQLEnum
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from enum import Enum

from app.models.base import BaseModel


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


class TeamMember(BaseModel):
    """
    Team member SQLAlchemy model for staff management.

    Tracks employee information, roles, permissions, performance metrics,
    and availability for assignment and scheduling.
    """
    __tablename__ = 'team_members'

    # Basic Information (Required)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(20), nullable=False)

    # Role & Status
    role = Column(SQLEnum(TeamRole), nullable=False)
    status = Column(SQLEnum(TeamMemberStatus), default=TeamMemberStatus.ACTIVE)
    availability_status = Column(SQLEnum(AvailabilityStatus), default=AvailabilityStatus.AVAILABLE)

    # Employment Details
    employee_id = Column(String(50), nullable=True, unique=True)
    hire_date = Column(Date, nullable=True)
    termination_date = Column(Date, nullable=True)
    department = Column(String(100), nullable=True)

    # Contact Information
    personal_email = Column(String(255), nullable=True)
    personal_phone = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(2), nullable=True)
    zip_code = Column(String(20), nullable=True)

    # Emergency Contact
    emergency_contact_name = Column(String(200), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relationship = Column(String(50), nullable=True)

    # Permissions & Access
    can_view_all_leads = Column(Boolean, default=False)
    can_manage_team = Column(Boolean, default=False)
    can_access_reports = Column(Boolean, default=False)
    can_approve_quotes = Column(Boolean, default=False)
    max_quote_approval_amount = Column(Integer, nullable=True)

    # Performance Metrics
    active_leads_count = Column(Integer, default=0)
    active_projects_count = Column(Integer, default=0)
    total_leads_converted = Column(Integer, default=0)
    total_revenue_generated = Column(Integer, default=0)
    avg_response_time_minutes = Column(Integer, nullable=True)
    conversion_rate = Column(Float, nullable=True)

    # Sales Performance (for sales roles)
    monthly_sales_target = Column(Integer, nullable=True)
    monthly_sales_actual = Column(Integer, default=0)
    quarterly_sales_target = Column(Integer, nullable=True)
    quarterly_sales_actual = Column(Integer, default=0)

    # Customer Satisfaction
    avg_customer_rating = Column(Float, nullable=True)
    total_reviews = Column(Integer, default=0)

    # Availability & Scheduling
    work_hours_start = Column(String(5), nullable=True)  # HH:MM format
    work_hours_end = Column(String(5), nullable=True)    # HH:MM format
    work_days = Column(String(50), nullable=True)        # Comma-separated days
    timezone = Column(String(50), default="America/Detroit")

    # Calendar Integration
    google_calendar_id = Column(String(255), nullable=True)
    outlook_calendar_id = Column(String(255), nullable=True)

    # Compensation (optional, sensitive)
    hourly_rate = Column(Float, nullable=True)
    salary = Column(Integer, nullable=True)
    commission_rate = Column(Float, nullable=True)

    # Skills & Certifications
    skills = Column(Text, nullable=True)
    certifications = Column(Text, nullable=True)
    languages = Column(Text, nullable=True)

    # Profile
    profile_photo_url = Column(Text, nullable=True)
    bio = Column(String(1000), nullable=True)
    notes = Column(Text, nullable=True)

    # Last Activity
    last_login = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, nullable=True)

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


# Pydantic schemas for API validation
class TeamMemberCreateSchema(BaseModel):
    """Schema for creating a new team member"""
    model_config = ConfigDict(from_attributes=True)

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

    @field_validator('phone', 'personal_phone')
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


class TeamMemberUpdateSchema(BaseModel):
    """Schema for updating a team member"""
    model_config = ConfigDict(from_attributes=True)

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


class TeamMemberResponseSchema(BaseModel):
    """Schema for team member API response"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    role: TeamRole
    status: TeamMemberStatus
    availability_status: AvailabilityStatus
    department: Optional[str] = None
    active_leads_count: int = 0
    active_projects_count: int = 0
    created_at: datetime
    updated_at: datetime


class TeamMemberListFiltersSchema(BaseModel):
    """Filter parameters for team member list endpoint"""
    role: Optional[str] = Field(None, description="Comma-separated roles")
    status: Optional[TeamMemberStatus] = Field(None, description="Filter by status")
    availability_status: Optional[AvailabilityStatus] = Field(None, description="Filter by availability")
    department: Optional[str] = Field(None, description="Filter by department")
    can_view_all_leads: Optional[bool] = Field(None, description="Filter by permission")
    has_active_assignments: Optional[bool] = Field(None, description="Filter members with assignments")