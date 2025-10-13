"""
Social Media Monitoring Service
Monitors social media platforms for roof-related discussions and lead opportunities
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import requests
import re
import os

logger = logging.getLogger(__name__)


class SocialMediaService:
    """
    Monitors social media platforms for roofing lead opportunities

    Platforms:
    1. Facebook Groups (via Graph API)
    2. Nextdoor (web scraping or API if available)
    3. Twitter/X (via API v2)
    4. Instagram (hashtag monitoring)
    """

    def __init__(self):
        self.facebook_token = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
        self.twitter_bearer = os.getenv("TWITTER_BEARER_TOKEN", "")

        self.session = requests.Session()

        # Keywords to monitor
        self.roof_keywords = [
            "roof", "roofing", "roofer", "leak", "shingles",
            "hail damage", "wind damage", "roof repair",
            "need roofer", "roofing company", "roof replacement"
        ]

        self.urgency_keywords = [
            "leak", "emergency", "urgent", "asap", "help",
            "water damage", "ceiling damage", "now"
        ]

    async def monitor_facebook_groups(
        self,
        cities: List[str],
        days_back: int = 7
    ) -> List[Dict]:
        """
        Monitor Facebook local groups for roof-related posts

        Args:
            cities: List of cities to monitor
            days_back: How many days to search

        Returns:
            List of potential leads from Facebook
        """
        logger.info(f"Monitoring Facebook groups for {len(cities)} cities")

        leads = []

        # Facebook Graph API
        base_url = "https://graph.facebook.com/v18.0"

        for city in cities:
            try:
                # Search for groups in this city
                groups = await self._search_facebook_groups(city)

                # Monitor posts in each group
                for group in groups:
                    posts = await self._get_group_posts(group["id"], days_back)

                    # Filter for roof-related posts
                    roof_posts = [
                        post for post in posts
                        if self._contains_roof_keywords(post.get("message", ""))
                    ]

                    # Convert posts to leads
                    for post in roof_posts:
                        lead = self._facebook_post_to_lead(post, city, group)
                        if lead:
                            leads.append(lead)

            except Exception as e:
                logger.error(f"Error monitoring Facebook for {city}: {str(e)}")
                continue

        logger.info(f"Found {len(leads)} Facebook leads")

        return leads

    async def monitor_nextdoor(
        self,
        cities: List[str],
        days_back: int = 7
    ) -> List[Dict]:
        """
        Monitor Nextdoor for roof-related posts

        Note: Nextdoor doesn't have a public API, so this would require
        web scraping with proper rate limiting and respect for robots.txt

        Args:
            cities: List of cities to monitor
            days_back: How many days to search

        Returns:
            List of potential leads from Nextdoor
        """
        logger.info(f"Monitoring Nextdoor for {len(cities)} cities")

        leads = []

        # TODO: Implement Nextdoor monitoring
        # Options:
        # 1. Web scraping (careful with ToS)
        # 2. Nextdoor Business API (if available)
        # 3. Manual monitoring + data entry

        # Sample lead structure
        sample_lead = {
            "source": "nextdoor",
            "platform": "nextdoor",
            "post_url": "https://nextdoor.com/...",
            "post_text": "Looking for roof repair after yesterday's storm",
            "poster_name": "Jane Doe",
            "neighborhood": "Downtown Birmingham",
            "city": "Birmingham",
            "state": "MI",
            "post_date": datetime.now().isoformat(),
            "urgency": "high",
            "intent": "active_search",
            "engagement_level": "high"
        }

        return leads

    async def monitor_twitter(
        self,
        cities: List[str],
        days_back: int = 7
    ) -> List[Dict]:
        """
        Monitor Twitter/X for roof-related posts

        Args:
            cities: List of cities to monitor
            days_back: How many days to search

        Returns:
            List of potential leads from Twitter
        """
        logger.info(f"Monitoring Twitter for {len(cities)} cities")

        leads = []

        # Twitter API v2
        base_url = "https://api.twitter.com/2"
        headers = {"Authorization": f"Bearer {self.twitter_bearer}"}

        for city in cities:
            try:
                # Build search query
                # Example: "(roof OR roofing) (leak OR damage) near:Birmingham,MI within:15mi"
                query = self._build_twitter_query(city)

                # Search tweets
                endpoint = f"{base_url}/tweets/search/recent"
                params = {
                    "query": query,
                    "max_results": 100,
                    "tweet.fields": "created_at,author_id,geo",
                    "expansions": "author_id",
                    "user.fields": "name,username,location"
                }

                # TODO: Implement actual API call
                # response = self.session.get(endpoint, headers=headers, params=params)
                # response.raise_for_status()
                # data = response.json()

                # Convert tweets to leads
                # for tweet in data.get("data", []):
                #     lead = self._twitter_tweet_to_lead(tweet, city)
                #     if lead:
                #         leads.append(lead)

            except Exception as e:
                logger.error(f"Error monitoring Twitter for {city}: {str(e)}")
                continue

        logger.info(f"Found {len(leads)} Twitter leads")

        return leads

    def _contains_roof_keywords(self, text: str) -> bool:
        """Check if text contains roof-related keywords"""
        text_lower = text.lower()

        return any(keyword in text_lower for keyword in self.roof_keywords)

    def _contains_urgency_keywords(self, text: str) -> bool:
        """Check if text contains urgency keywords"""
        text_lower = text.lower()

        return any(keyword in text_lower for keyword in self.urgency_keywords)

    def _extract_intent(self, text: str) -> str:
        """
        Extract intent from post text

        Intents:
        - active_search: Actively looking for roofer
        - information_gathering: Asking questions
        - problem_reporting: Reporting issues
        - recommendation_request: Asking for recommendations
        """

        text_lower = text.lower()

        # Active search patterns
        if any(pattern in text_lower for pattern in [
            "looking for", "need a", "anyone know", "recommendations",
            "who should i call", "best roofer"
        ]):
            return "active_search"

        # Information gathering
        if any(pattern in text_lower for pattern in [
            "how much", "what does it cost", "should i",
            "is it normal", "how long"
        ]):
            return "information_gathering"

        # Problem reporting
        if any(pattern in text_lower for pattern in [
            "leak", "damaged", "broken", "problem with",
            "water coming in"
        ]):
            return "problem_reporting"

        return "general"

    def _calculate_urgency(self, text: str) -> str:
        """Calculate urgency level from text"""

        text_lower = text.lower()

        # High urgency
        if any(word in text_lower for word in [
            "emergency", "urgent", "asap", "immediate",
            "leak", "water damage", "ceiling damage"
        ]):
            return "high"

        # Medium urgency
        if any(word in text_lower for word in [
            "soon", "this week", "need help", "damaged"
        ]):
            return "medium"

        return "low"

    def _facebook_post_to_lead(
        self,
        post: Dict,
        city: str,
        group: Dict
    ) -> Optional[Dict]:
        """Convert Facebook post to lead data"""

        try:
            text = post.get("message", "")

            lead = {
                "source": "facebook_groups",
                "platform": "facebook",
                "post_id": post.get("id"),
                "post_url": f"https://facebook.com/{post.get('id')}",
                "post_text": text,
                "post_date": post.get("created_time"),
                "group_name": group.get("name"),
                "city": city,
                "state": "MI",
                "intent": self._extract_intent(text),
                "urgency": self._calculate_urgency(text),
                "engagement_level": "medium",
                "has_leak": "leak" in text.lower(),
                "requesting_quotes": any(word in text.lower() for word in [
                    "quote", "estimate", "price", "cost"
                ])
            }

            return lead

        except Exception as e:
            logger.error(f"Failed to convert Facebook post: {str(e)}")
            return None

    def _twitter_tweet_to_lead(self, tweet: Dict, city: str) -> Optional[Dict]:
        """Convert Twitter tweet to lead data"""

        try:
            text = tweet.get("text", "")

            lead = {
                "source": "twitter",
                "platform": "twitter",
                "tweet_id": tweet.get("id"),
                "tweet_url": f"https://twitter.com/i/web/status/{tweet.get('id')}",
                "post_text": text,
                "post_date": tweet.get("created_at"),
                "city": city,
                "state": "MI",
                "intent": self._extract_intent(text),
                "urgency": self._calculate_urgency(text),
                "engagement_level": "low"
            }

            return lead

        except Exception as e:
            logger.error(f"Failed to convert tweet: {str(e)}")
            return None

    def _build_twitter_query(self, city: str) -> str:
        """Build Twitter search query for city"""

        # Combine roof keywords with location
        keyword_query = " OR ".join([f'"{kw}"' for kw in self.roof_keywords[:5]])

        # Add location filter
        query = f"({keyword_query}) near:{city},MI within:15mi -is:retweet"

        return query

    async def _search_facebook_groups(self, city: str) -> List[Dict]:
        """Search for relevant Facebook groups in city"""

        # TODO: Implement Facebook Graph API group search
        # For now, return sample structure

        groups = [
            {
                "id": "12345",
                "name": f"{city} Community",
                "member_count": 5000
            },
            {
                "id": "67890",
                "name": f"{city} Home Owners",
                "member_count": 3000
            }
        ]

        return groups

    async def _get_group_posts(self, group_id: str, days_back: int) -> List[Dict]:
        """Get recent posts from Facebook group"""

        # TODO: Implement Facebook Graph API post fetching
        # For now, return empty list

        return []


# Singleton
_social_media_service: Optional[SocialMediaService] = None


def get_social_media_service() -> SocialMediaService:
    """Get or create social media service instance"""
    global _social_media_service
    if not _social_media_service:
        _social_media_service = SocialMediaService()
    return _social_media_service
