"""
iSwitch Roofs CRM - Base Models
Version: 1.0.0

Base Pydantic models for all database entities and common parameters.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
import re


class BaseDBModel(BaseModel):
    """
    Base model for all database entities.

    Provides common fields and configuration for all database models.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v) if v else None,
        }
    )

    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaginationParams(BaseModel):
    """
    Standard pagination parameters for list endpoints.

    Usage:
        GET /api/leads/?page=1&per_page=50
    """
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    per_page: int = Field(default=50, ge=1, le=100, description="Items per page (max 100)")

    @property
    def offset(self) -> int:
        """Calculate offset for database query"""
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        """Get limit for database query"""
        return self.per_page


class SortParams(BaseModel):
    """
    Standard sorting parameters for list endpoints.

    Usage:
        GET /api/leads/?sort=lead_score:desc
        GET /api/leads/?sort=created_at:asc

    Format: field:direction (asc or desc)
    """
    sort: Optional[str] = Field(
        default="created_at:desc",
        pattern=r'^[a-z_]+:(asc|desc)$',
        description="Sort format: field:direction"
    )

    @property
    def field(self) -> str:
        """Extract sort field"""
        if self.sort:
            return self.sort.split(':')[0]
        return "created_at"

    @property
    def direction(self) -> str:
        """Extract sort direction"""
        if self.sort and ':' in self.sort:
            return self.sort.split(':')[1]
        return "desc"

    @property
    def is_descending(self) -> bool:
        """Check if sort direction is descending"""
        return self.direction == "desc"


class FilterParams(BaseModel):
    """
    Base class for filter parameters.

    Extend this for specific filter needs per endpoint.
    """
    model_config = ConfigDict(extra='allow')

    def to_supabase_filters(self) -> Dict[str, Any]:
        """
        Convert filter parameters to Supabase query filters.

        Returns:
            Dict of field: value pairs for exact matches
        """
        filters = {}
        for field, value in self.model_dump(exclude_none=True).items():
            if value is not None and value != "":
                filters[field] = value
        return filters


class PaginatedResponse(BaseModel):
    """
    Standard paginated response format.

    Generic type for any list response with pagination metadata.
    """
    data: List[Any] = Field(default_factory=list)
    pagination: Dict[str, int]

    @staticmethod
    def create(
        data: List[Any],
        page: int,
        per_page: int,
        total: int
    ) -> Dict[str, Any]:
        """
        Create a paginated response dictionary.

        Args:
            data: List of items to return
            page: Current page number
            per_page: Items per page
            total: Total number of items

        Returns:
            Formatted paginated response
        """
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0

        return {
            "data": data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response format"""
    error: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class SuccessResponse(BaseModel):
    """Standard success response format"""
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
