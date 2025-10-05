"""
Pydantic schemas for interactions.
Version: 1.0.0
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class InteractionBase(BaseModel):
    """Common fields for interactions."""

    customer_id: Optional[UUID] = Field(None, description="Related customer ID")
    lead_id: Optional[UUID] = Field(None, description="Related lead ID")
    interaction_type: str = Field(
        ..., description="Type of interaction (phone_call, email, meeting, note, sms)"
    )
    direction: str = Field(..., description="Direction (inbound, outbound, internal)")
    subject: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    assigned_to: Optional[UUID] = None
    follow_up_required: bool = False
    follow_up_due: Optional[datetime] = None


class InteractionCreate(InteractionBase):
    """Schema for creating a new interaction."""

    interaction_time: Optional[datetime] = Field(
        default_factory=datetime.utcnow, description="When the interaction occurred"
    )


class InteractionUpdate(BaseModel):
    """Schema for updating an interaction (all fields optional)."""

    interaction_type: Optional[str] = None
    direction: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[UUID] = None
    follow_up_required: Optional[bool] = None
    follow_up_due: Optional[datetime] = None
    interaction_time: Optional[datetime] = None
