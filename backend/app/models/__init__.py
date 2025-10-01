"""
iSwitch Roofs CRM - Models Package
Version: 1.0.0

Comprehensive Pydantic data models for all CRM entities.
"""

# Base models
from backend.app.models.base import (
    BaseDBModel,
    PaginationParams,
    SortParams,
    FilterParams,
    PaginatedResponse,
    ErrorResponse,
    SuccessResponse
)

# Lead models
from backend.app.models.lead import (
    Lead,
    LeadStatus,
    LeadTemperature,
    LeadSource,
    UrgencyLevel,
    LeadScoreBreakdown,
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    LeadListFilters
)

# Customer models
from backend.app.models.customer import (
    Customer,
    CustomerStatus,
    CustomerSegment,
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListFilters
)

# Project models
from backend.app.models.project import (
    Project,
    ProjectStatus,
    ProjectType,
    ProjectPriority,
    RoofMaterial,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListFilters
)

# Interaction models
from backend.app.models.interaction import (
    Interaction,
    InteractionType,
    InteractionDirection,
    InteractionOutcome,
    EntityType,
    InteractionCreate,
    InteractionUpdate,
    InteractionResponse,
    InteractionListFilters
)

# Appointment models
from backend.app.models.appointment import (
    Appointment,
    AppointmentType,
    AppointmentStatus,
    ReminderStatus,
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentReschedule,
    AppointmentResponse,
    AppointmentListFilters
)

# Team models
from backend.app.models.team import (
    TeamMember,
    TeamRole,
    TeamMemberStatus,
    AvailabilityStatus,
    TeamMemberCreate,
    TeamMemberUpdate,
    TeamMemberResponse,
    TeamMemberListFilters
)

# Review models
from backend.app.models.review import (
    Review,
    ReviewPlatform,
    ReviewStatus,
    ReviewSentiment,
    ReviewCreate,
    ReviewUpdate,
    ReviewResponse,
    ReviewRequestCreate,
    ReviewListFilters
)

# Partnership models
from backend.app.models.partnership import (
    Partnership,
    PartnerType,
    PartnershipStatus,
    CommissionStructure,
    PartnershipCreate,
    PartnershipUpdate,
    PartnershipReferral,
    PartnershipResponse,
    PartnershipListFilters
)

__all__ = [
    # Base
    "BaseDBModel",
    "PaginationParams",
    "SortParams",
    "FilterParams",
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",

    # Lead
    "Lead",
    "LeadStatus",
    "LeadTemperature",
    "LeadSource",
    "UrgencyLevel",
    "LeadScoreBreakdown",
    "LeadCreate",
    "LeadUpdate",
    "LeadResponse",
    "LeadListFilters",

    # Customer
    "Customer",
    "CustomerStatus",
    "CustomerSegment",
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    "CustomerListFilters",

    # Project
    "Project",
    "ProjectStatus",
    "ProjectType",
    "ProjectPriority",
    "RoofMaterial",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectListFilters",

    # Interaction
    "Interaction",
    "InteractionType",
    "InteractionDirection",
    "InteractionOutcome",
    "EntityType",
    "InteractionCreate",
    "InteractionUpdate",
    "InteractionResponse",
    "InteractionListFilters",

    # Appointment
    "Appointment",
    "AppointmentType",
    "AppointmentStatus",
    "ReminderStatus",
    "AppointmentCreate",
    "AppointmentUpdate",
    "AppointmentReschedule",
    "AppointmentResponse",
    "AppointmentListFilters",

    # Team
    "TeamMember",
    "TeamRole",
    "TeamMemberStatus",
    "AvailabilityStatus",
    "TeamMemberCreate",
    "TeamMemberUpdate",
    "TeamMemberResponse",
    "TeamMemberListFilters",

    # Review
    "Review",
    "ReviewPlatform",
    "ReviewStatus",
    "ReviewSentiment",
    "ReviewCreate",
    "ReviewUpdate",
    "ReviewResponse",
    "ReviewRequestCreate",
    "ReviewListFilters",

    # Partnership
    "Partnership",
    "PartnerType",
    "PartnershipStatus",
    "CommissionStructure",
    "PartnershipCreate",
    "PartnershipUpdate",
    "PartnershipReferral",
    "PartnershipResponse",
    "PartnershipListFilters",
]
