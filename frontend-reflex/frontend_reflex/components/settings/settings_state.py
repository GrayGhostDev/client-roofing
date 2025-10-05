"""Settings state management for the iSwitch Roofs CRM dashboard."""

import reflex as rx
from typing import Dict, List, Optional, Any
from datetime import datetime


class UserProfile(rx.Base):
    """User profile data model."""
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    username: str = ""
    bio: str = ""
    profile_photo_url: str = ""
    language: str = "en"
    timezone: str = "America/Detroit"
    date_format: str = "MM/DD/YYYY"
    number_format: str = "US"
    theme: str = "auto"  # light, dark, auto
    two_factor_enabled: bool = False
    email_verified: bool = False
    phone_verified: bool = False
    last_login: Optional[str] = None
    created_at: Optional[str] = None


class TeamMember(rx.Base):
    """Team member data model."""
    id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    role: str  # Admin, Manager, Sales, Tech
    status: str  # Active, Inactive, Pending
    avatar_url: str = ""
    last_active: Optional[str] = None
    hire_date: Optional[str] = None
    territory: str = ""
    commission_rate: float = 0.0
    commission_type: str = "percentage"  # percentage, flat
    skills: List[str] = []
    certifications: List[str] = []
    working_hours: Dict[str, Dict[str, str]] = {}  # {"monday": {"start": "09:00", "end": "17:00"}}
    performance_score: float = 0.0
    total_leads: int = 0
    total_sales: float = 0.0
    conversion_rate: float = 0.0


class BusinessInfo(rx.Base):
    """Business information data model."""
    company_name: str = "iSwitch Roofs"
    business_address: str = ""
    phone_primary: str = ""
    phone_secondary: str = ""
    email_primary: str = ""
    email_support: str = ""
    license_number: str = ""
    tax_id: str = ""
    logo_url: str = ""
    website: str = ""
    established_year: int = 2020
    service_areas: List[str] = []


class OperatingSettings(rx.Base):
    """Operating settings data model."""
    business_hours: Dict[str, Dict[str, Any]] = {
        "monday": {"enabled": True, "start": "08:00", "end": "17:00"},
        "tuesday": {"enabled": True, "start": "08:00", "end": "17:00"},
        "wednesday": {"enabled": True, "start": "08:00", "end": "17:00"},
        "thursday": {"enabled": True, "start": "08:00", "end": "17:00"},
        "friday": {"enabled": True, "start": "08:00", "end": "17:00"},
        "saturday": {"enabled": False, "start": "09:00", "end": "15:00"},
        "sunday": {"enabled": False, "start": "09:00", "end": "15:00"}
    }
    holidays: List[Dict[str, str]] = []  # [{"date": "2024-07-04", "name": "Independence Day"}]
    lead_response_target_minutes: int = 2
    auto_assignment_enabled: bool = True
    auto_assignment_rules: Dict[str, Any] = {
        "method": "round_robin",  # round_robin, territory, skill_based
        "consider_workload": True,
        "consider_availability": True
    }


class LeadScoringConfig(rx.Base):
    """Lead scoring configuration data model."""
    score_thresholds: Dict[str, int] = {
        "hot": 80,
        "warm": 60,
        "cool": 40,
        "cold": 0
    }
    scoring_weights: Dict[str, float] = {
        "source_quality": 0.25,
        "demographic_fit": 0.20,
        "engagement_level": 0.20,
        "urgency": 0.15,
        "budget_qualification": 0.20
    }
    custom_rules: List[Dict[str, Any]] = []


class NotificationPreferences(rx.Base):
    """Notification preferences data model."""
    email_notifications: Dict[str, Any] = {
        "new_leads": {"enabled": True, "frequency": "instant"},
        "appointment_reminders": {"enabled": True, "frequency": "instant"},
        "status_changes": {"enabled": True, "frequency": "hourly"},
        "team_messages": {"enabled": True, "frequency": "instant"},
        "system_updates": {"enabled": True, "frequency": "daily"},
        "performance_reports": {"enabled": True, "frequency": "weekly"}
    }
    sms_notifications: Dict[str, bool] = {
        "critical_alerts": True,
        "lead_responses": False,
        "appointment_confirmations": True,
        "urgent_messages": True
    }
    push_notifications: Dict[str, Any] = {
        "desktop_enabled": True,
        "mobile_enabled": True,
        "sound_alerts": True,
        "quiet_hours_start": "22:00",
        "quiet_hours_end": "07:00"
    }
    alert_rules: List[Dict[str, Any]] = []


class IntegrationSettings(rx.Base):
    """Integration settings data model."""
    api_keys: Dict[str, str] = {}
    webhooks: List[Dict[str, Any]] = []
    oauth_connections: Dict[str, Any] = {}
    import_export_settings: Dict[str, Any] = {
        "auto_backup_enabled": True,
        "backup_frequency": "daily",
        "export_format": "csv"
    }


class SecuritySettings(rx.Base):
    """Security settings data model."""
    password_policy: Dict[str, Any] = {
        "min_length": 8,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_numbers": True,
        "require_special_chars": True,
        "password_history": 5
    }
    session_timeout_minutes: int = 480  # 8 hours
    ip_whitelist: List[str] = []
    audit_log_retention_days: int = 90
    data_retention_policy: Dict[str, int] = {
        "leads": 2555,  # 7 years
        "customers": 3650,  # 10 years
        "projects": 2555,  # 7 years
        "interactions": 1095  # 3 years
    }


class SettingsState(rx.Base):
    """Settings state management class."""

    # Current tab
    active_tab: str = "profile"

    # Settings data
    user_profile: UserProfile = UserProfile()
    team_members: List[TeamMember] = []
    business_info: BusinessInfo = BusinessInfo()
    operating_settings: OperatingSettings = OperatingSettings()
    scoring_config: LeadScoringConfig = LeadScoringConfig()
    notification_preferences: NotificationPreferences = NotificationPreferences()
    integration_settings: IntegrationSettings = IntegrationSettings()
    security_settings: SecuritySettings = SecuritySettings()

    # UI state
    has_unsaved_changes: bool = False
    saving: bool = False
    loading: bool = False
    error_message: str = ""
    success_message: str = ""

    # Team management
    selected_member_id: Optional[str] = None
    show_add_member_modal: bool = False
    show_edit_member_modal: bool = False
    show_delete_member_modal: bool = False

    # Search and filters
    search_query: str = ""
    member_role_filter: str = "all"
    member_status_filter: str = "all"

    # Recent activity
    recent_changes: List[Dict[str, Any]] = []

    # Sample data initialization
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._initialize_sample_data()

    def _initialize_sample_data(self):
        """Initialize with sample data for development."""

        # Sample user profile
        self.user_profile = UserProfile(
            first_name="John",
            last_name="Manager",
            email="john.manager@iswitchroofs.com",
            phone="(248) 555-0123",
            username="jmanager",
            bio="Operations Manager at iSwitch Roofs with 8+ years experience in roofing and team management.",
            language="en",
            timezone="America/Detroit",
            date_format="MM/DD/YYYY",
            number_format="US",
            theme="light",
            two_factor_enabled=True,
            email_verified=True,
            phone_verified=True,
            last_login="2024-10-05T10:30:00Z",
            created_at="2023-06-15T09:00:00Z"
        )

        # Sample team members
        self.team_members = [
            TeamMember(
                id="tm_001",
                first_name="Sarah",
                last_name="Johnson",
                email="sarah.johnson@iswitchroofs.com",
                phone="(248) 555-0124",
                role="Sales",
                status="Active",
                avatar_url="https://images.unsplash.com/photo-1494790108755-2616b612b647?w=150&h=150&fit=crop&crop=face",
                last_active="2024-10-05T09:45:00Z",
                hire_date="2023-03-15",
                territory="Oakland County North",
                commission_rate=5.5,
                commission_type="percentage",
                skills=["Residential Sales", "Insurance Claims", "Customer Relations"],
                certifications=["GAF Master Elite", "Owens Corning Preferred"],
                working_hours={
                    "monday": {"start": "08:00", "end": "17:00"},
                    "tuesday": {"start": "08:00", "end": "17:00"},
                    "wednesday": {"start": "08:00", "end": "17:00"},
                    "thursday": {"start": "08:00", "end": "17:00"},
                    "friday": {"start": "08:00", "end": "16:00"}
                },
                performance_score=94.2,
                total_leads=157,
                total_sales=890000.0,
                conversion_rate=28.7
            ),
            TeamMember(
                id="tm_002",
                first_name="Mike",
                last_name="Rodriguez",
                email="mike.rodriguez@iswitchroofs.com",
                phone="(248) 555-0125",
                role="Tech",
                status="Active",
                avatar_url="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face",
                last_active="2024-10-05T08:20:00Z",
                hire_date="2022-08-01",
                territory="Wayne County",
                commission_rate=0,
                commission_type="flat",
                skills=["Roof Inspection", "Drone Operations", "3D Modeling", "Project Management"],
                certifications=["HAAG Certified Inspector", "Drone Pilot License"],
                working_hours={
                    "monday": {"start": "07:00", "end": "15:30"},
                    "tuesday": {"start": "07:00", "end": "15:30"},
                    "wednesday": {"start": "07:00", "end": "15:30"},
                    "thursday": {"start": "07:00", "end": "15:30"},
                    "friday": {"start": "07:00", "end": "14:00"}
                },
                performance_score=91.8,
                total_leads=0,
                total_sales=0.0,
                conversion_rate=0.0
            ),
            TeamMember(
                id="tm_003",
                first_name="Emily",
                last_name="Chen",
                email="emily.chen@iswitchroofs.com",
                phone="(248) 555-0126",
                role="Manager",
                status="Active",
                avatar_url="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face",
                last_active="2024-10-05T11:15:00Z",
                hire_date="2023-01-10",
                territory="All Territories",
                commission_rate=2.0,
                commission_type="percentage",
                skills=["Team Management", "Process Optimization", "Training", "Quality Control"],
                certifications=["Management Certified", "Safety Coordinator"],
                working_hours={
                    "monday": {"start": "08:00", "end": "18:00"},
                    "tuesday": {"start": "08:00", "end": "18:00"},
                    "wednesday": {"start": "08:00", "end": "18:00"},
                    "thursday": {"start": "08:00", "end": "18:00"},
                    "friday": {"start": "08:00", "end": "17:00"}
                },
                performance_score=96.5,
                total_leads=0,
                total_sales=0.0,
                conversion_rate=0.0
            ),
            TeamMember(
                id="tm_004",
                first_name="David",
                last_name="Thompson",
                email="david.thompson@iswitchroofs.com",
                phone="(248) 555-0127",
                role="Sales",
                status="Active",
                avatar_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face",
                last_active="2024-10-05T10:05:00Z",
                hire_date="2023-09-20",
                territory="Oakland County South",
                commission_rate=6.0,
                commission_type="percentage",
                skills=["Premium Sales", "Commercial Roofing", "Insurance Negotiations"],
                certifications=["GAF Master Elite", "Commercial Roofing Certified"],
                working_hours={
                    "monday": {"start": "09:00", "end": "18:00"},
                    "tuesday": {"start": "09:00", "end": "18:00"},
                    "wednesday": {"start": "09:00", "end": "18:00"},
                    "thursday": {"start": "09:00", "end": "18:00"},
                    "friday": {"start": "09:00", "end": "17:00"}
                },
                performance_score=87.3,
                total_leads=89,
                total_sales=567000.0,
                conversion_rate=31.2
            )
        ]

        # Sample business info
        self.business_info = BusinessInfo(
            company_name="iSwitch Roofs",
            business_address="1234 Main Street, Birmingham, MI 48009",
            phone_primary="(248) 555-ROOF",
            phone_secondary="(248) 555-0100",
            email_primary="info@iswitchroofs.com",
            email_support="support@iswitchroofs.com",
            license_number="MI-2101234567",
            tax_id="12-3456789",
            website="https://iswitchroofs.com",
            established_year=2018,
            service_areas=[
                "48009", "48012", "48025", "48067", "48071", "48073", "48076",
                "48084", "48236", "48237", "48301", "48302", "48304", "48307"
            ]
        )

        # Sample recent changes
        self.recent_changes = [
            {
                "timestamp": "2024-10-05T11:30:00Z",
                "user": "John Manager",
                "action": "Updated business hours",
                "details": "Modified Saturday hours to 9:00 AM - 3:00 PM"
            },
            {
                "timestamp": "2024-10-05T10:15:00Z",
                "user": "Emily Chen",
                "action": "Added team member",
                "details": "David Thompson joined as Sales representative"
            },
            {
                "timestamp": "2024-10-05T09:45:00Z",
                "user": "John Manager",
                "action": "Updated notification settings",
                "details": "Enabled SMS alerts for critical notifications"
            }
        ]


# Global settings state instance
settings_state = SettingsState()