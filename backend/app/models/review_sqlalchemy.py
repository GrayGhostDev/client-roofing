"""
iSwitch Roofs CRM - Review SQLAlchemy Model
Version: 1.0.0

Review data model for managing customer reviews from BirdEye and other platforms.
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, Float, Enum as SQLEnum
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

from app.models.base import BaseModel


class ReviewPlatform(str, Enum):
    """Review platform enumeration"""
    GOOGLE = "google"
    FACEBOOK = "facebook"
    YELP = "yelp"
    BBB = "bbb"                # Better Business Bureau
    ANGIES_LIST = "angies_list"
    HOME_ADVISOR = "home_advisor"
    THUMBTACK = "thumbtack"
    BIRDEYE = "birdeye"
    DIRECT = "direct"          # Direct to website


class ReviewStatus(str, Enum):
    """Review status"""
    PENDING = "pending"        # Awaiting review
    PUBLISHED = "published"    # Live on platform
    RESPONDED = "responded"    # Response posted
    FLAGGED = "flagged"        # Flagged for review
    REMOVED = "removed"        # Removed from platform


class ReviewSentiment(str, Enum):
    """Review sentiment"""
    POSITIVE = "positive"      # 4-5 stars
    NEUTRAL = "neutral"        # 3 stars
    NEGATIVE = "negative"      # 1-2 stars


class Review(BaseModel):
    """
    Review SQLAlchemy model for customer reviews and reputation management.

    Tracks reviews from multiple platforms with sentiment analysis,
    response management, and integration with BirdEye.
    """
    __tablename__ = 'reviews'

    # Association (Required)
    customer_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), nullable=True, index=True)

    # Review Details (Required)
    platform = Column(SQLEnum(ReviewPlatform), nullable=False)
    rating = Column(Float, nullable=False)
    status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.PUBLISHED)

    # Content
    title = Column(String(200), nullable=True)
    review_text = Column(Text, nullable=True)
    reviewer_name = Column(String(200), nullable=True)
    reviewer_email = Column(String(255), nullable=True)

    # Metadata
    review_date = Column(DateTime, nullable=False, index=True)
    is_verified = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)

    # Platform-Specific IDs
    platform_review_id = Column(String(255), nullable=True, unique=True)
    platform_url = Column(Text, nullable=True)
    birdeye_review_id = Column(String(255), nullable=True)

    # Sentiment Analysis
    sentiment = Column(SQLEnum(ReviewSentiment), nullable=True)
    sentiment_score = Column(Float, nullable=True)
    keywords = Column(Text, nullable=True)

    # Response Management
    has_response = Column(Boolean, default=False)
    response_text = Column(Text, nullable=True)
    response_date = Column(DateTime, nullable=True)
    responded_by = Column(String(36), nullable=True, index=True)
    response_time_hours = Column(Integer, nullable=True)

    # Review Request Tracking
    request_sent = Column(Boolean, default=False)
    request_sent_date = Column(DateTime, nullable=True)
    request_method = Column(String(50), nullable=True)
    days_after_completion = Column(Integer, nullable=True)

    # Quality Indicators
    is_detailed = Column(Boolean, default=False)
    has_photos = Column(Boolean, default=False)
    photo_urls = Column(Text, nullable=True)

    # Flags & Moderation
    is_flagged = Column(Boolean, default=False)
    flag_reason = Column(String(500), nullable=True)
    flagged_by = Column(String(36), nullable=True)
    flagged_date = Column(DateTime, nullable=True)

    # Impact Metrics
    helpful_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)

    # Internal Notes
    notes = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)

    @property
    def is_positive(self) -> bool:
        """Check if review is positive (4+ stars)"""
        return self.rating >= 4.0

    @property
    def is_negative(self) -> bool:
        """Check if review is negative (1-2 stars)"""
        return self.rating <= 2.0

    @property
    def star_rating_int(self) -> int:
        """Get star rating as integer"""
        return int(round(self.rating))

    @property
    def needs_response(self) -> bool:
        """Check if review needs a response"""
        return not self.has_response and self.status == ReviewStatus.PUBLISHED

    @property
    def is_recent(self) -> bool:
        """Check if review is within last 30 days"""
        if self.review_date:
            delta = datetime.utcnow() - self.review_date
            return delta.days <= 30
        return False

    def calculate_sentiment(self) -> ReviewSentiment:
        """Calculate sentiment based on rating"""
        if self.rating >= 4.0:
            return ReviewSentiment.POSITIVE
        elif self.rating >= 3.0:
            return ReviewSentiment.NEUTRAL
        else:
            return ReviewSentiment.NEGATIVE


# Pydantic schemas for API validation
class ReviewCreateSchema(BaseModel):
    """Schema for creating a new review"""
    model_config = ConfigDict(from_attributes=True)

    customer_id: UUID
    platform: ReviewPlatform
    rating: float = Field(..., ge=0.0, le=5.0)

    # Optional fields
    project_id: Optional[UUID] = None
    title: Optional[str] = None
    review_text: Optional[str] = None
    reviewer_name: Optional[str] = None
    reviewer_email: Optional[str] = None
    review_date: Optional[datetime] = None
    is_verified: Optional[bool] = False
    platform_review_id: Optional[str] = None
    platform_url: Optional[str] = None
    birdeye_review_id: Optional[str] = None
    has_photos: Optional[bool] = False
    photo_urls: Optional[str] = None
    request_sent: Optional[bool] = False
    request_method: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v: float) -> float:
        """Ensure rating is in 0.5 increments"""
        if v % 0.5 != 0:
            raise ValueError('Rating must be in 0.5 increments (0, 0.5, 1.0, etc.)')
        return v


class ReviewUpdateSchema(BaseModel):
    """Schema for updating a review"""
    model_config = ConfigDict(from_attributes=True)

    status: Optional[ReviewStatus] = None
    is_featured: Optional[bool] = None
    response_text: Optional[str] = None
    responded_by: Optional[UUID] = None
    is_flagged: Optional[bool] = None
    flag_reason: Optional[str] = None
    helpful_count: Optional[int] = None
    view_count: Optional[int] = None
    notes: Optional[str] = None
    tags: Optional[str] = None


class ReviewResponseSchema(BaseModel):
    """Schema for review API response"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    project_id: Optional[str] = None
    platform: ReviewPlatform
    rating: float
    status: ReviewStatus
    title: Optional[str] = None
    review_text: Optional[str] = None
    reviewer_name: Optional[str] = None
    review_date: datetime
    is_verified: bool = False
    is_featured: bool = False
    has_response: bool = False
    sentiment: Optional[ReviewSentiment] = None
    created_at: datetime
    updated_at: datetime


class ReviewRequestCreateSchema(BaseModel):
    """Schema for requesting a review from customer"""
    customer_id: UUID
    project_id: Optional[UUID] = None
    method: str = Field(..., description="email, sms, or birdeye")
    send_immediately: bool = Field(default=False)
    delay_days: Optional[int] = Field(None, ge=0, description="Days to wait before sending")


class ReviewListFiltersSchema(BaseModel):
    """Filter parameters for review list endpoint"""
    platform: Optional[str] = Field(None, description="Comma-separated platforms")
    status: Optional[ReviewStatus] = Field(None, description="Filter by status")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="Minimum rating")
    max_rating: Optional[float] = Field(None, ge=0, le=5, description="Maximum rating")
    sentiment: Optional[ReviewSentiment] = Field(None, description="Filter by sentiment")
    customer_id: Optional[UUID] = Field(None, description="Filter by customer")
    project_id: Optional[UUID] = Field(None, description="Filter by project")
    has_response: Optional[bool] = Field(None, description="Filter by response status")
    needs_response: Optional[bool] = Field(None, description="Filter needing response")
    is_featured: Optional[bool] = Field(None, description="Filter featured reviews")
    is_flagged: Optional[bool] = Field(None, description="Filter flagged reviews")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    is_recent: Optional[bool] = Field(None, description="Filter last 30 days")