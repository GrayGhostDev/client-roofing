"""
iSwitch Roofs CRM - Review Model
Version: 1.0.0

Review data model for managing customer reviews from BirdEye and other platforms.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.base import BaseDBModel


class ReviewPlatform(str, Enum):
    """Review platform enumeration"""

    GOOGLE = "google"
    FACEBOOK = "facebook"
    YELP = "yelp"
    BBB = "bbb"  # Better Business Bureau
    ANGIES_LIST = "angies_list"
    HOME_ADVISOR = "home_advisor"
    THUMBTACK = "thumbtack"
    BIRDEYE = "birdeye"
    DIRECT = "direct"  # Direct to website


class ReviewStatus(str, Enum):
    """Review status"""

    PENDING = "pending"  # Awaiting review
    PUBLISHED = "published"  # Live on platform
    RESPONDED = "responded"  # Response posted
    FLAGGED = "flagged"  # Flagged for review
    REMOVED = "removed"  # Removed from platform


class ReviewSentiment(str, Enum):
    """Review sentiment"""

    POSITIVE = "positive"  # 4-5 stars
    NEUTRAL = "neutral"  # 3 stars
    NEGATIVE = "negative"  # 1-2 stars


class Review(BaseDBModel):
    """
    Review data model for customer reviews and reputation management.

    Tracks reviews from multiple platforms with sentiment analysis,
    response management, and integration with BirdEye.
    """

    # Association (Required)
    customer_id: UUID = Field(..., description="Associated customer ID")
    project_id: UUID | None = Field(None, description="Associated project ID")

    # Review Details (Required)
    platform: ReviewPlatform = Field(..., description="Review platform")
    rating: float = Field(..., ge=0.0, le=5.0, description="Star rating (0-5)")
    status: ReviewStatus = Field(default=ReviewStatus.PUBLISHED, description="Review status")

    # Content
    title: str | None = Field(None, max_length=200, description="Review title")
    review_text: str | None = Field(None, description="Review text content")
    reviewer_name: str | None = Field(None, max_length=200, description="Reviewer name")
    reviewer_email: str | None = Field(None, max_length=255, description="Reviewer email")

    # Metadata
    review_date: datetime = Field(
        default_factory=datetime.utcnow, description="Date review was posted"
    )
    is_verified: bool = Field(default=False, description="Is this a verified purchase/project?")
    is_featured: bool = Field(default=False, description="Feature on website/marketing?")

    # Platform-Specific IDs
    platform_review_id: str | None = Field(None, max_length=255, description="Platform's review ID")
    platform_url: str | None = Field(None, description="Direct URL to review")
    birdeye_review_id: str | None = Field(None, max_length=255, description="BirdEye review ID")

    # Sentiment Analysis
    sentiment: ReviewSentiment | None = Field(None, description="Sentiment classification")
    sentiment_score: float | None = Field(
        None, ge=-1.0, le=1.0, description="Sentiment score (-1 to 1)"
    )
    keywords: str | None = Field(None, description="Extracted keywords (comma-separated)")

    # Response Management
    has_response: bool = Field(default=False, description="Has business responded?")
    response_text: str | None = Field(None, description="Business response text")
    response_date: datetime | None = Field(None, description="Date of response")
    responded_by: UUID | None = Field(None, description="Team member who responded")
    response_time_hours: int | None = Field(None, ge=0, description="Hours to respond")

    # Review Request Tracking
    request_sent: bool = Field(default=False, description="Was review request sent?")
    request_sent_date: datetime | None = Field(None, description="Date request was sent")
    request_method: str | None = Field(None, max_length=50, description="email, sms, or birdeye")
    days_after_completion: int | None = Field(
        None, ge=0, description="Days after project completion"
    )

    # Quality Indicators
    is_detailed: bool = Field(default=False, description="Is review detailed/substantial?")
    has_photos: bool = Field(default=False, description="Does review include photos?")
    photo_urls: str | None = Field(None, description="Photo URLs (comma-separated)")

    # Flags & Moderation
    is_flagged: bool = Field(default=False, description="Flagged for attention")
    flag_reason: str | None = Field(None, max_length=500, description="Reason for flagging")
    flagged_by: UUID | None = Field(None, description="Team member who flagged")
    flagged_date: datetime | None = Field(None, description="Date flagged")

    # Impact Metrics
    helpful_count: int = Field(default=0, ge=0, description="Number of 'helpful' votes")
    view_count: int = Field(default=0, ge=0, description="Number of views")
    share_count: int = Field(default=0, ge=0, description="Number of shares")

    # Internal Notes
    notes: str | None = Field(None, description="Internal notes about review")
    tags: str | None = Field(None, description="Tags for categorization")

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: float) -> float:
        """Ensure rating is in 0.5 increments"""
        if v % 0.5 != 0:
            raise ValueError("Rating must be in 0.5 increments (0, 0.5, 1.0, etc.)")
        return v

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


class ReviewCreate(BaseModel):
    """Schema for creating a new review"""

    customer_id: UUID
    platform: ReviewPlatform
    rating: float = Field(..., ge=0.0, le=5.0)

    # Optional fields
    project_id: UUID | None = None
    title: str | None = None
    review_text: str | None = None
    reviewer_name: str | None = None
    reviewer_email: str | None = None
    review_date: datetime | None = None
    is_verified: bool | None = False
    platform_review_id: str | None = None
    platform_url: str | None = None
    birdeye_review_id: str | None = None
    has_photos: bool | None = False
    photo_urls: str | None = None
    request_sent: bool | None = False
    request_method: str | None = None
    notes: str | None = None


class ReviewUpdate(BaseModel):
    """Schema for updating a review"""

    status: ReviewStatus | None = None
    is_featured: bool | None = None
    response_text: str | None = None
    responded_by: UUID | None = None
    is_flagged: bool | None = None
    flag_reason: str | None = None
    helpful_count: int | None = None
    view_count: int | None = None
    notes: str | None = None
    tags: str | None = None


class ReviewResponse(BaseModel):
    """Schema for review API response"""

    data: Review
    customer: dict | None = None  # Customer data
    project: dict | None = None  # Project data
    responder: dict | None = None  # Team member who responded


class ReviewRequestCreate(BaseModel):
    """Schema for requesting a review from customer"""

    customer_id: UUID
    project_id: UUID | None = None
    method: str = Field(..., description="email, sms, or birdeye")
    send_immediately: bool = Field(default=False)
    delay_days: int | None = Field(None, ge=0, description="Days to wait before sending")


class ReviewListFilters(BaseModel):
    """Filter parameters for review list endpoint"""

    platform: str | None = Field(None, description="Comma-separated platforms")
    status: ReviewStatus | None = Field(None, description="Filter by status")
    min_rating: float | None = Field(None, ge=0, le=5, description="Minimum rating")
    max_rating: float | None = Field(None, ge=0, le=5, description="Maximum rating")
    sentiment: ReviewSentiment | None = Field(None, description="Filter by sentiment")
    customer_id: UUID | None = Field(None, description="Filter by customer")
    project_id: UUID | None = Field(None, description="Filter by project")
    has_response: bool | None = Field(None, description="Filter by response status")
    needs_response: bool | None = Field(None, description="Filter needing response")
    is_featured: bool | None = Field(None, description="Filter featured reviews")
    is_flagged: bool | None = Field(None, description="Filter flagged reviews")
    date_from: datetime | None = Field(None, description="Filter from date")
    date_to: datetime | None = Field(None, description="Filter to date")
    is_recent: bool | None = Field(None, description="Filter last 30 days")
