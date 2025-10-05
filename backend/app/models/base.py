"""
Base Model for SQLAlchemy

Provides common fields and functionality for all models
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.ext.declarative import declarative_base

# Create base class for declarative models
Base = declarative_base()


class BaseModel(Base):
    """
    Abstract base model with common fields

    All models should inherit from this class
    """

    __abstract__ = True

    # Primary key - UUID as string for Supabase compatibility
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Metadata
    metadata_json = Column(Text, nullable=True)  # Store JSON data as text

    def __repr__(self):
        """String representation of model"""
        return f"<{self.__class__.__name__}(id='{self.id}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

    def soft_delete(self):
        """Mark record as deleted without removing from database"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()


# Alias for compatibility with existing imports
BaseDBModel = BaseModel
