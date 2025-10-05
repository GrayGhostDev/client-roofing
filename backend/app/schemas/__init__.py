"""
Pydantic schemas for iSwitch Roofs CRM
Version: 1.0.0

Validation schemas for API requests and responses.
"""

from .customer import (
    Customer,
    CustomerCreate,
    CustomerListFilters,
    CustomerResponse,
    CustomerSegment,
    CustomerStatus,
    CustomerUpdate,
)
from .lead import (
    LeadCreate,
    LeadListFilters,
    LeadListResponse,
    LeadResponse,
    LeadScoreBreakdown,
    LeadUpdate,
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
    "CustomerSegment",
]
