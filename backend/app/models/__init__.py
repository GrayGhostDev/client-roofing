"""
iSwitch Roofs CRM - Data Models
Version: 1.0.0
Date: 2025-10-01

Pydantic models for data validation and serialization.
"""

from backend.app.models.base import (
    BaseDBModel,
    PaginationParams,
    SortParams,
    FilterParams,
)

__all__ = [
    "BaseDBModel",
    "PaginationParams",
    "SortParams",
    "FilterParams",
]
