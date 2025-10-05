"""
Reviews Service Module

Handles multi-platform review management including:
- Google My Business reviews
- Yelp reviews
- Facebook reviews
- BirdEye integration
- Sentiment analysis
- Review responses
"""

import json
import logging
import os
import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

import redis
import requests
from cachetools import TTLCache
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Third-party imports
from textblob import TextBlob

from app.utils.pusher_client import PusherClient

# Local imports
from app.utils.supabase_client import SupabaseClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReviewsService:
    """Service for managing multi-platform reviews"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ReviewsService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._supabase = None
        self._pusher = None
        self._redis = None
        self._cache = TTLCache(maxsize=100, ttl=300)  # 5 minute cache

        # API configurations
        self.gmb_credentials = None
        self.yelp_api_key = os.environ.get("YELP_API_KEY")
        self.facebook_access_token = os.environ.get("FACEBOOK_ACCESS_TOKEN")
        self.facebook_page_id = os.environ.get("FACEBOOK_PAGE_ID")
        self.birdeye_api_key = os.environ.get("BIRDEYE_API_KEY")
        self.birdeye_business_id = os.environ.get("BIRDEYE_BUSINESS_ID")

        # Platform configurations
        self.platforms = {
            "google": {"enabled": True, "weight": 0.4},
            "yelp": {"enabled": True, "weight": 0.2},
            "facebook": {"enabled": True, "weight": 0.2},
            "birdeye": {"enabled": True, "weight": 0.2},
        }

    @property
    def supabase(self):
        """Lazy initialization of Supabase client"""
        if self._supabase is None:
            self._supabase = SupabaseClient()
        return self._supabase

    @property
    def pusher(self):
        """Lazy initialization of Pusher client"""
        if self._pusher is None:
            self._pusher = PusherClient()
        return self._pusher

    @property
    def redis_client(self):
        """Lazy initialization of Redis client"""
        if self._redis is None:
            try:
                self._redis = redis.StrictRedis(
                    host=os.environ.get("REDIS_HOST", "localhost"),
                    port=int(os.environ.get("REDIS_PORT", 6379)),
                    db=0,
                    decode_responses=True,
                )
                self._redis.ping()
            except:
                logger.warning("Redis not available, using in-memory cache only")
                self._redis = None
        return self._redis

    def _cache_result(self, key: str, data: Any, ttl: int = 300):
        """Cache result in Redis and memory"""
        self._cache[key] = data
        if self.redis_client:
            try:
                self.redis_client.setex(key, ttl, json.dumps(data))
            except:
                pass

    def _get_cached(self, key: str) -> Any | None:
        """Get cached result from Redis or memory"""
        if key in self._cache:
            return self._cache[key]

        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            except:
                pass

        return None

    # Google My Business Methods

    def init_gmb_oauth(self, redirect_uri: str) -> str:
        """Initialize Google My Business OAuth flow"""
        try:
            flow = Flow.from_client_secrets_file(
                "client_secrets.json",
                scopes=[
                    "https://www.googleapis.com/auth/business.manage",
                    "https://www.googleapis.com/auth/plus.business.manage",
                ],
                redirect_uri=redirect_uri,
            )

            auth_url, _ = flow.authorization_url(
                access_type="offline", include_granted_scopes="true"
            )

            return auth_url
        except Exception as e:
            logger.error(f"GMB OAuth init error: {e}")
            return None

    def complete_gmb_oauth(self, auth_code: str, redirect_uri: str) -> tuple[bool, str | None]:
        """Complete GMB OAuth flow and store credentials"""
        try:
            flow = Flow.from_client_secrets_file(
                "client_secrets.json",
                scopes=[
                    "https://www.googleapis.com/auth/business.manage",
                    "https://www.googleapis.com/auth/plus.business.manage",
                ],
                redirect_uri=redirect_uri,
            )

            flow.fetch_token(code=auth_code)
            self.gmb_credentials = flow.credentials

            # Store credentials
            creds_data = {
                "token": self.gmb_credentials.token,
                "refresh_token": self.gmb_credentials.refresh_token,
                "token_uri": self.gmb_credentials.token_uri,
                "client_id": self.gmb_credentials.client_id,
                "client_secret": self.gmb_credentials.client_secret,
                "scopes": self.gmb_credentials.scopes,
            }

            result = (
                self.supabase.client.table("platform_credentials")
                .upsert(
                    {
                        "platform": "google_my_business",
                        "credentials": json.dumps(creds_data),
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                )
                .execute()
            )

            return True, None
        except Exception as e:
            logger.error(f"GMB OAuth completion error: {e}")
            return False, str(e)

    def fetch_gmb_reviews(
        self, location_name: str = None
    ) -> tuple[bool, list[dict] | None, str | None]:
        """Fetch reviews from Google My Business"""
        try:
            # Load credentials if not in memory
            if not self.gmb_credentials:
                result = (
                    self.supabase.client.table("platform_credentials")
                    .select("*")
                    .eq("platform", "google_my_business")
                    .single()
                    .execute()
                )

                if result.data:
                    creds_data = json.loads(result.data["credentials"])
                    self.gmb_credentials = Credentials(**creds_data)
                else:
                    return False, None, "GMB credentials not found"

            # Refresh token if needed
            if self.gmb_credentials.expired and self.gmb_credentials.refresh_token:
                self.gmb_credentials.refresh(Request())

            # Build service
            service = build("mybusiness", "v4", credentials=self.gmb_credentials)

            # Get accounts
            accounts = service.accounts().list().execute()
            if not accounts.get("accounts"):
                return False, None, "No GMB accounts found"

            account_name = accounts["accounts"][0]["name"]

            # Get locations
            locations = service.accounts().locations().list(parent=account_name).execute()

            if not locations.get("locations"):
                return False, None, "No GMB locations found"

            # Find specific location or use first
            target_location = None
            for loc in locations["locations"]:
                if not location_name or location_name in loc.get("locationName", ""):
                    target_location = loc
                    break

            if not target_location:
                target_location = locations["locations"][0]

            # Fetch reviews
            reviews_response = (
                service.accounts()
                .locations()
                .reviews()
                .list(parent=target_location["name"])
                .execute()
            )

            reviews = []
            for review in reviews_response.get("reviews", []):
                reviews.append(
                    {
                        "platform": "google",
                        "review_id": review.get("reviewId"),
                        "reviewer_name": review.get("reviewer", {}).get("displayName"),
                        "rating": review.get("starRating"),
                        "comment": review.get("comment"),
                        "created_at": review.get("createTime"),
                        "updated_at": review.get("updateTime"),
                        "reply": review.get("reviewReply", {}).get("comment"),
                        "reply_at": review.get("reviewReply", {}).get("updateTime"),
                    }
                )

            return True, reviews, None

        except Exception as e:
            logger.error(f"GMB fetch error: {e}")
            return False, None, str(e)

    # Yelp Methods

    def fetch_yelp_reviews(
        self, business_alias: str = None
    ) -> tuple[bool, list[dict] | None, str | None]:
        """Fetch reviews from Yelp"""
        try:
            if not self.yelp_api_key:
                return False, None, "Yelp API key not configured"

            # Use configured business alias or default
            if not business_alias:
                business_alias = os.environ.get("YELP_BUSINESS_ALIAS", "iswitch-roofs-detroit")

            headers = {"Authorization": f"Bearer {self.yelp_api_key}"}

            # Fetch business details
            business_url = f"https://api.yelp.com/v3/businesses/{business_alias}"
            business_response = requests.get(business_url, headers=headers)

            if business_response.status_code != 200:
                return False, None, f"Yelp API error: {business_response.status_code}"

            business_data = business_response.json()

            # Fetch reviews
            reviews_url = f"https://api.yelp.com/v3/businesses/{business_alias}/reviews"
            reviews_response = requests.get(reviews_url, headers=headers)

            if reviews_response.status_code != 200:
                return False, None, f"Yelp reviews API error: {reviews_response.status_code}"

            reviews_data = reviews_response.json()

            reviews = []
            for review in reviews_data.get("reviews", []):
                reviews.append(
                    {
                        "platform": "yelp",
                        "review_id": review.get("id"),
                        "reviewer_name": review.get("user", {}).get("name"),
                        "rating": review.get("rating"),
                        "comment": review.get("text"),
                        "created_at": review.get("time_created"),
                        "url": review.get("url"),
                    }
                )

            return True, reviews, None

        except Exception as e:
            logger.error(f"Yelp fetch error: {e}")
            return False, None, str(e)

    # Facebook Methods

    def fetch_facebook_reviews(self) -> tuple[bool, list[dict] | None, str | None]:
        """Fetch reviews from Facebook"""
        try:
            if not self.facebook_access_token or not self.facebook_page_id:
                return False, None, "Facebook credentials not configured"

            url = f"https://graph.facebook.com/v18.0/{self.facebook_page_id}/ratings"
            params = {
                "access_token": self.facebook_access_token,
                "fields": "reviewer,rating,review_text,created_time",
            }

            response = requests.get(url, params=params)

            if response.status_code != 200:
                return False, None, f"Facebook API error: {response.status_code}"

            data = response.json()

            reviews = []
            for review in data.get("data", []):
                reviews.append(
                    {
                        "platform": "facebook",
                        "review_id": review.get("id"),
                        "reviewer_name": review.get("reviewer", {}).get("name"),
                        "rating": review.get("rating"),
                        "comment": review.get("review_text"),
                        "created_at": review.get("created_time"),
                    }
                )

            return True, reviews, None

        except Exception as e:
            logger.error(f"Facebook fetch error: {e}")
            return False, None, str(e)

    # BirdEye Methods

    def fetch_birdeye_reviews(self) -> tuple[bool, list[dict] | None, str | None]:
        """Fetch reviews from BirdEye"""
        try:
            if not self.birdeye_api_key or not self.birdeye_business_id:
                return False, None, "BirdEye credentials not configured"

            headers = {
                "Accept": "application/json",
                "content-type": "application/json",
                "Authorization": f"Bearer {self.birdeye_api_key}",
            }

            url = (
                f"https://api.birdeye.com/resources/v1/review/businessId/{self.birdeye_business_id}"
            )

            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                return False, None, f"BirdEye API error: {response.status_code}"

            data = response.json()

            reviews = []
            for review in data:
                reviews.append(
                    {
                        "platform": "birdeye",
                        "review_id": review.get("id"),
                        "reviewer_name": review.get("reviewer", {}).get("name"),
                        "rating": review.get("rating"),
                        "comment": review.get("comments"),
                        "created_at": review.get("reviewDate"),
                        "source": review.get("sourceName"),
                        "reply": review.get("businessResponse", {}).get("comment"),
                        "reply_at": review.get("businessResponse", {}).get("responseDate"),
                    }
                )

            return True, reviews, None

        except Exception as e:
            logger.error(f"BirdEye fetch error: {e}")
            return False, None, str(e)

    # Aggregation Methods

    def fetch_all_reviews(
        self, refresh: bool = False
    ) -> tuple[bool, dict | None, str | None]:
        """Fetch and aggregate reviews from all platforms"""
        try:
            cache_key = "reviews:all"

            if not refresh:
                cached = self._get_cached(cache_key)
                if cached:
                    return True, cached, None

            all_reviews = []
            errors = []

            # Fetch from each platform
            if self.platforms["google"]["enabled"]:
                success, reviews, error = self.fetch_gmb_reviews()
                if success and reviews:
                    all_reviews.extend(reviews)
                elif error:
                    errors.append(f"Google: {error}")

            if self.platforms["yelp"]["enabled"]:
                success, reviews, error = self.fetch_yelp_reviews()
                if success and reviews:
                    all_reviews.extend(reviews)
                elif error:
                    errors.append(f"Yelp: {error}")

            if self.platforms["facebook"]["enabled"]:
                success, reviews, error = self.fetch_facebook_reviews()
                if success and reviews:
                    all_reviews.extend(reviews)
                elif error:
                    errors.append(f"Facebook: {error}")

            if self.platforms["birdeye"]["enabled"]:
                success, reviews, error = self.fetch_birdeye_reviews()
                if success and reviews:
                    all_reviews.extend(reviews)
                elif error:
                    errors.append(f"BirdEye: {error}")

            # Store in database
            for review in all_reviews:
                # Perform sentiment analysis
                sentiment = self.analyze_sentiment(review.get("comment", ""))
                review["sentiment_score"] = sentiment["score"]
                review["sentiment_label"] = sentiment["label"]

                # Upsert review
                self.supabase.client.table("reviews").upsert(
                    {
                        "platform": review["platform"],
                        "platform_review_id": review["review_id"],
                        "reviewer_name": review.get("reviewer_name"),
                        "rating": review.get("rating"),
                        "comment": review.get("comment"),
                        "sentiment_score": sentiment["score"],
                        "sentiment_label": sentiment["label"],
                        "created_at": review.get("created_at"),
                        "reply": review.get("reply"),
                        "reply_at": review.get("reply_at"),
                        "metadata": json.dumps(
                            {"url": review.get("url"), "source": review.get("source")}
                        ),
                    }
                ).execute()

            # Calculate aggregated metrics
            metrics = self.calculate_review_metrics(all_reviews)

            result = {
                "reviews": all_reviews,
                "metrics": metrics,
                "errors": errors if errors else None,
                "fetched_at": datetime.utcnow().isoformat(),
            }

            # Cache result
            self._cache_result(cache_key, result, ttl=600)  # 10 minute cache

            # Broadcast update
            self.pusher.trigger(
                "reviews", "reviews-updated", {"metrics": metrics, "new_reviews": len(all_reviews)}
            )

            return True, result, None

        except Exception as e:
            logger.error(f"Fetch all reviews error: {e}")
            return False, None, str(e)

    def calculate_review_metrics(self, reviews: list[dict]) -> dict[str, Any]:
        """Calculate aggregated review metrics"""
        if not reviews:
            return {
                "total_reviews": 0,
                "average_rating": 0,
                "rating_distribution": {},
                "sentiment_distribution": {},
                "platform_distribution": {},
                "response_rate": 0,
                "recent_trend": "stable",
            }

        # Basic metrics
        total_reviews = len(reviews)
        ratings = [r.get("rating", 0) for r in reviews if r.get("rating")]
        average_rating = statistics.mean(ratings) if ratings else 0

        # Rating distribution
        rating_distribution = defaultdict(int)
        for r in reviews:
            if r.get("rating"):
                rating_distribution[int(r["rating"])] += 1

        # Sentiment distribution
        sentiment_distribution = defaultdict(int)
        for r in reviews:
            if r.get("sentiment_label"):
                sentiment_distribution[r["sentiment_label"]] += 1

        # Platform distribution
        platform_distribution = defaultdict(int)
        for r in reviews:
            platform_distribution[r.get("platform", "unknown")] += 1

        # Response rate
        replied_reviews = [r for r in reviews if r.get("reply")]
        response_rate = (len(replied_reviews) / total_reviews * 100) if total_reviews > 0 else 0

        # Recent trend (last 30 days vs previous 30 days)
        recent_trend = self._calculate_trend(reviews)

        # Calculate weighted rating
        weighted_rating = self._calculate_weighted_rating(reviews)

        return {
            "total_reviews": total_reviews,
            "average_rating": round(average_rating, 2),
            "weighted_rating": round(weighted_rating, 2),
            "rating_distribution": dict(rating_distribution),
            "sentiment_distribution": dict(sentiment_distribution),
            "platform_distribution": dict(platform_distribution),
            "response_rate": round(response_rate, 1),
            "recent_trend": recent_trend,
            "nps_score": self._calculate_nps(reviews),
        }

    def _calculate_weighted_rating(self, reviews: list[dict]) -> float:
        """Calculate weighted rating based on platform weights and recency"""
        weighted_sum = 0
        weight_total = 0

        now = datetime.utcnow()

        for review in reviews:
            if not review.get("rating"):
                continue

            # Platform weight
            platform = review.get("platform", "unknown")
            platform_weight = self.platforms.get(platform, {}).get("weight", 0.1)

            # Recency weight (newer reviews weighted more)
            try:
                review_date = datetime.fromisoformat(review.get("created_at", ""))
                days_old = (now - review_date).days
                recency_weight = max(0.1, 1 - (days_old / 365))  # Decay over a year
            except:
                recency_weight = 0.5

            # Combined weight
            combined_weight = platform_weight * recency_weight

            weighted_sum += review["rating"] * combined_weight
            weight_total += combined_weight

        return (weighted_sum / weight_total) if weight_total > 0 else 0

    def _calculate_trend(self, reviews: list[dict]) -> str:
        """Calculate rating trend"""
        try:
            now = datetime.utcnow()
            thirty_days_ago = now - timedelta(days=30)
            sixty_days_ago = now - timedelta(days=60)

            recent_reviews = []
            previous_reviews = []

            for review in reviews:
                if not review.get("created_at") or not review.get("rating"):
                    continue

                review_date = datetime.fromisoformat(review["created_at"])

                if review_date >= thirty_days_ago:
                    recent_reviews.append(review["rating"])
                elif review_date >= sixty_days_ago:
                    previous_reviews.append(review["rating"])

            if not recent_reviews or not previous_reviews:
                return "stable"

            recent_avg = statistics.mean(recent_reviews)
            previous_avg = statistics.mean(previous_reviews)

            diff = recent_avg - previous_avg

            if diff > 0.2:
                return "improving"
            elif diff < -0.2:
                return "declining"
            else:
                return "stable"

        except Exception:
            return "stable"

    def _calculate_nps(self, reviews: list[dict]) -> int:
        """Calculate Net Promoter Score"""
        if not reviews:
            return 0

        promoters = 0
        detractors = 0
        total = 0

        for review in reviews:
            rating = review.get("rating")
            if rating is None:
                continue

            total += 1
            if rating >= 4.5:  # 4.5-5 stars = promoters
                promoters += 1
            elif rating <= 3:  # 1-3 stars = detractors
                detractors += 1

        if total == 0:
            return 0

        nps = ((promoters - detractors) / total) * 100
        return int(nps)

    # Sentiment Analysis

    def analyze_sentiment(self, text: str) -> dict[str, Any]:
        """Analyze sentiment of review text"""
        if not text:
            return {"score": 0, "label": "neutral", "polarity": 0, "subjectivity": 0}

        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            # Determine label
            if polarity > 0.3:
                label = "positive"
            elif polarity < -0.3:
                label = "negative"
            else:
                label = "neutral"

            # Calculate score (0-100)
            score = int((polarity + 1) * 50)  # Convert -1 to 1 range to 0-100

            return {
                "score": score,
                "label": label,
                "polarity": round(polarity, 3),
                "subjectivity": round(subjectivity, 3),
            }

        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {"score": 50, "label": "neutral", "polarity": 0, "subjectivity": 0}

    # Response Management

    def generate_response_suggestion(
        self, review: dict
    ) -> tuple[bool, str | None, str | None]:
        """Generate AI-suggested response to a review"""
        try:
            rating = review.get("rating", 0)
            comment = review.get("comment", "")
            sentiment = review.get("sentiment_label", "neutral")

            # Templates based on rating and sentiment
            if rating >= 4:
                # Positive review
                template = (
                    f"Thank you so much for your {rating}-star review! "
                    "We're thrilled to hear about your positive experience with iSwitch Roofs. "
                    "Your feedback means the world to us and motivates our team to continue "
                    "delivering exceptional roofing services. We look forward to serving you "
                    "and your referrals in the future!"
                )
            elif rating == 3:
                # Neutral review
                template = (
                    "Thank you for taking the time to share your feedback. "
                    "We appreciate your honest review and would love to understand how we "
                    "could have made your experience even better. Please feel free to reach "
                    "out to us directly at (248) 123-4567 so we can address any concerns and "
                    "ensure your complete satisfaction."
                )
            else:
                # Negative review
                template = (
                    "We sincerely apologize that your experience didn't meet expectations. "
                    "Your feedback is extremely important to us, and we take it very seriously. "
                    "We would appreciate the opportunity to make this right. Please contact our "
                    "management team directly at (248) 123-4567 or email us at "
                    "service@iswitchroofs.com so we can resolve this matter promptly."
                )

            # Customize based on specific keywords in comment
            if comment:
                comment_lower = comment.lower()

                if "quality" in comment_lower and rating >= 4:
                    template += " We're proud of our commitment to quality workmanship!"
                elif "professional" in comment_lower and rating >= 4:
                    template += (
                        " Our team takes pride in maintaining the highest professional standards."
                    )
                elif "price" in comment_lower or "cost" in comment_lower:
                    if rating < 3:
                        template += " We understand pricing concerns and would be happy to discuss our value proposition and financing options."
                elif "communication" in comment_lower:
                    if rating < 3:
                        template += " We're actively working on improving our communication processes based on valuable feedback like yours."

            return True, template, None

        except Exception as e:
            logger.error(f"Generate response error: {e}")
            return False, None, str(e)

    def post_review_response(
        self, review_id: str, response_text: str, platform: str
    ) -> tuple[bool, str | None]:
        """Post a response to a review"""
        try:
            if platform == "google":
                return self._post_gmb_response(review_id, response_text)
            elif platform == "yelp":
                return False, "Yelp API doesn't support review responses"
            elif platform == "facebook":
                return self._post_facebook_response(review_id, response_text)
            elif platform == "birdeye":
                return self._post_birdeye_response(review_id, response_text)
            else:
                return False, f"Unsupported platform: {platform}"

        except Exception as e:
            logger.error(f"Post response error: {e}")
            return False, str(e)

    def _post_gmb_response(
        self, review_name: str, response_text: str
    ) -> tuple[bool, str | None]:
        """Post response to Google My Business review"""
        try:
            if not self.gmb_credentials:
                return False, "GMB credentials not configured"

            # Refresh token if needed
            if self.gmb_credentials.expired and self.gmb_credentials.refresh_token:
                self.gmb_credentials.refresh(Request())

            service = build("mybusiness", "v4", credentials=self.gmb_credentials)

            response = (
                service.accounts()
                .locations()
                .reviews()
                .updateReply(name=review_name, body={"comment": response_text})
                .execute()
            )

            # Update database
            self.supabase.client.table("reviews").update(
                {"reply": response_text, "reply_at": datetime.utcnow().isoformat()}
            ).eq("platform_review_id", review_name).execute()

            return True, None

        except Exception as e:
            logger.error(f"GMB response error: {e}")
            return False, str(e)

    def _post_facebook_response(
        self, comment_id: str, response_text: str
    ) -> tuple[bool, str | None]:
        """Post response to Facebook review"""
        try:
            if not self.facebook_access_token:
                return False, "Facebook access token not configured"

            url = f"https://graph.facebook.com/v18.0/{comment_id}/comments"
            data = {"message": response_text, "access_token": self.facebook_access_token}

            response = requests.post(url, data=data)

            if response.status_code == 200:
                # Update database
                self.supabase.client.table("reviews").update(
                    {"reply": response_text, "reply_at": datetime.utcnow().isoformat()}
                ).eq("platform_review_id", comment_id).execute()

                return True, None
            else:
                return False, f"Facebook API error: {response.status_code}"

        except Exception as e:
            logger.error(f"Facebook response error: {e}")
            return False, str(e)

    def _post_birdeye_response(
        self, review_id: str, response_text: str
    ) -> tuple[bool, str | None]:
        """Post response to BirdEye review"""
        try:
            if not self.birdeye_api_key:
                return False, "BirdEye API key not configured"

            headers = {
                "Accept": "application/json",
                "content-type": "application/json",
                "Authorization": f"Bearer {self.birdeye_api_key}",
            }

            url = f"https://api.birdeye.com/resources/v1/review/{review_id}/response"
            data = {"comment": response_text, "publishToSourceSite": True}

            response = requests.post(url, json=data, headers=headers)

            if response.status_code == 200:
                # Update database
                self.supabase.client.table("reviews").update(
                    {"reply": response_text, "reply_at": datetime.utcnow().isoformat()}
                ).eq("platform_review_id", review_id).execute()

                return True, None
            else:
                return False, f"BirdEye API error: {response.status_code}"

        except Exception as e:
            logger.error(f"BirdEye response error: {e}")
            return False, str(e)

    # Review Campaigns

    def create_review_campaign(
        self, customer_ids: list[str], campaign_name: str, template_id: str = None
    ) -> tuple[bool, dict | None, str | None]:
        """Create a review request campaign"""
        try:
            # Create campaign
            campaign = {
                "name": campaign_name,
                "customer_count": len(customer_ids),
                "template_id": template_id,
                "status": "active",
                "created_at": datetime.utcnow().isoformat(),
                "sent_count": 0,
                "response_count": 0,
            }

            result = self.supabase.client.table("review_campaigns").insert(campaign).execute()
            campaign_id = result.data[0]["id"]

            # Create campaign recipients
            recipients = []
            for customer_id in customer_ids:
                # Get customer info
                customer = (
                    self.supabase.client.table("customers")
                    .select("*")
                    .eq("id", customer_id)
                    .single()
                    .execute()
                )

                if customer.data:
                    recipients.append(
                        {
                            "campaign_id": campaign_id,
                            "customer_id": customer_id,
                            "email": customer.data.get("email"),
                            "phone": customer.data.get("phone"),
                            "status": "pending",
                            "created_at": datetime.utcnow().isoformat(),
                        }
                    )

            if recipients:
                self.supabase.client.table("campaign_recipients").insert(recipients).execute()

            return True, {"campaign_id": campaign_id, "recipients_added": len(recipients)}, None

        except Exception as e:
            logger.error(f"Create campaign error: {e}")
            return False, None, str(e)

    def send_review_request(
        self, customer_id: str, method: str = "email"
    ) -> tuple[bool, str | None]:
        """Send review request to customer"""
        try:
            # Get customer info
            customer = (
                self.supabase.client.table("customers")
                .select("*")
                .eq("id", customer_id)
                .single()
                .execute()
            )

            if not customer.data:
                return False, "Customer not found"

            # Generate review links
            review_links = {
                "google": "https://g.page/r/CYourGooglePlaceId/review",
                "yelp": "https://www.yelp.com/writeareview/biz/your-yelp-id",
                "facebook": "https://www.facebook.com/pg/yourpage/reviews",
                "birdeye": f"https://review.birdeye.com/iswitch-roofs/{customer_id}",
            }

            if method == "email":
                # Send email (integrate with email service)
                # For now, just log the action
                logger.info(f"Sending review request email to {customer.data.get('email')}")

                # Record request
                self.supabase.client.table("review_requests").insert(
                    {
                        "customer_id": customer_id,
                        "method": "email",
                        "links": json.dumps(review_links),
                        "sent_at": datetime.utcnow().isoformat(),
                        "status": "sent",
                    }
                ).execute()

                return True, None

            elif method == "sms":
                # Send SMS (integrate with SMS service)
                logger.info(f"Sending review request SMS to {customer.data.get('phone')}")

                # Record request
                self.supabase.client.table("review_requests").insert(
                    {
                        "customer_id": customer_id,
                        "method": "sms",
                        "links": json.dumps(review_links),
                        "sent_at": datetime.utcnow().isoformat(),
                        "status": "sent",
                    }
                ).execute()

                return True, None
            else:
                return False, f"Unsupported method: {method}"

        except Exception as e:
            logger.error(f"Send review request error: {e}")
            return False, str(e)

    def get_review_insights(self, days: int = 30) -> tuple[bool, dict | None, str | None]:
        """Get review insights and recommendations"""
        try:
            cache_key = f"reviews:insights:{days}"
            cached = self._get_cached(cache_key)
            if cached:
                return True, cached, None

            # Fetch recent reviews
            since_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

            reviews = (
                self.supabase.client.table("reviews")
                .select("*")
                .gte("created_at", since_date)
                .execute()
            )

            if not reviews.data:
                return True, {"message": "No recent reviews found"}, None

            # Analyze patterns
            positive_keywords = defaultdict(int)
            negative_keywords = defaultdict(int)
            improvement_areas = []

            for review in reviews.data:
                if not review.get("comment"):
                    continue

                # Extract keywords
                blob = TextBlob(review["comment"])

                if review.get("rating", 0) >= 4:
                    for word in blob.words:
                        if len(word) > 4:  # Skip short words
                            positive_keywords[word.lower()] += 1
                elif review.get("rating", 0) <= 2:
                    for word in blob.words:
                        if len(word) > 4:
                            negative_keywords[word.lower()] += 1

            # Sort keywords by frequency
            top_positive = sorted(positive_keywords.items(), key=lambda x: x[1], reverse=True)[:10]
            top_negative = sorted(negative_keywords.items(), key=lambda x: x[1], reverse=True)[:10]

            # Generate recommendations
            recommendations = []

            if "communication" in negative_keywords or "response" in negative_keywords:
                recommendations.append(
                    {
                        "area": "Communication",
                        "issue": "Customers mention communication issues",
                        "action": "Implement automated status updates and response tracking",
                    }
                )

            if "price" in negative_keywords or "expensive" in negative_keywords:
                recommendations.append(
                    {
                        "area": "Pricing",
                        "issue": "Price concerns in negative reviews",
                        "action": "Better communicate value proposition and offer financing options",
                    }
                )

            if "quality" in negative_keywords:
                recommendations.append(
                    {
                        "area": "Quality",
                        "issue": "Quality concerns mentioned",
                        "action": "Review QA processes and implement additional inspections",
                    }
                )

            insights = {
                "period_days": days,
                "total_reviews": len(reviews.data),
                "average_rating": statistics.mean(
                    [r.get("rating", 0) for r in reviews.data if r.get("rating")]
                ),
                "response_rate": len([r for r in reviews.data if r.get("reply")])
                / len(reviews.data)
                * 100,
                "top_positive_keywords": top_positive,
                "top_negative_keywords": top_negative,
                "recommendations": recommendations,
                "sentiment_trend": self._calculate_sentiment_trend(reviews.data),
            }

            # Cache results
            self._cache_result(cache_key, insights, ttl=3600)  # 1 hour cache

            return True, insights, None

        except Exception as e:
            logger.error(f"Get insights error: {e}")
            return False, None, str(e)

    def _calculate_sentiment_trend(self, reviews: list[dict]) -> str:
        """Calculate sentiment trend over time"""
        try:
            # Group reviews by week
            weekly_sentiments = defaultdict(list)

            for review in reviews:
                if not review.get("created_at") or not review.get("sentiment_score"):
                    continue

                date = datetime.fromisoformat(review["created_at"])
                week = date.isocalendar()[1]
                weekly_sentiments[week].append(review["sentiment_score"])

            if len(weekly_sentiments) < 2:
                return "insufficient_data"

            # Calculate weekly averages
            weekly_avg = {
                week: statistics.mean(scores) for week, scores in weekly_sentiments.items()
            }

            # Compare recent weeks to earlier weeks
            weeks = sorted(weekly_avg.keys())
            recent_avg = statistics.mean([weekly_avg[w] for w in weeks[-2:]])
            earlier_avg = statistics.mean([weekly_avg[w] for w in weeks[:-2]])

            diff = recent_avg - earlier_avg

            if diff > 5:
                return "improving"
            elif diff < -5:
                return "declining"
            else:
                return "stable"

        except Exception:
            return "unknown"


# Create singleton instance
reviews_service = ReviewsService()
