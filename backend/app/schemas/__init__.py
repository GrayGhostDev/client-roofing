"""
Pydantic schemas for iSwitch Roofs CRM
Version: 1.0.0

Validation schemas for API requests and responses.
"""

from .lead import (
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    LeadListResponse,
    LeadScoreBreakdown,
    LeadListFilters
)

from .customer import (
    Customer,
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListFilters,
    CustomerStatus,
    CustomerSegment
)

__all__ = [
    "LeadCreate",
    "LeadUpdate",
    "LeadResponse",
    "LeadListResponse",
    "LeadScoreBreakdown",
    "LeadListFilters",
    "Customer",
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    "CustomerListFilters",
    "CustomerStatus",
    "CustomerSegment"
]