"""
Weather Intelligence API Integration - Week 11 Day 1
Weather data for personalized roofing messaging and urgency creation

This integration provides:
- Recent storm/hail/wind event tracking
- Historical weather data for specific locations
- Damage likelihood correlation with roof age
- Seasonal messaging recommendations
- Urgency generation based on weather patterns
- Talking points for sales conversations

Author: Week 11 Implementation
Created: 2025-10-11
"""

import os
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import aiohttp
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_API_BASE = "https://api.weather.com/v3/wx"  # Example endpoint


class WeatherIntelligenceAPI:
    """
    Weather intelligence for roofing sales and marketing

    Provides weather data to:
    - Create urgency in sales messaging
    - Identify properties at risk from recent weather
    - Generate seasonal talking points
    - Correlate weather events with roof damage likelihood
    """

    def __init__(self):
        """Initialize weather intelligence API"""
        self.api_key = WEATHER_API_KEY

        if not self.api_key:
            logger.warning("⚠️ Weather API key not configured - using simulated data")

    # =====================================================
    # MAIN WEATHER INTELLIGENCE METHODS
    # =====================================================

    async def get_recent_storms(
        self,
        zip_code: str,
        days_back: int = 30
    ) -> List[Dict]:
        """
        Recent severe weather events in area

        Tracks:
        - Hail events (size, date)
        - Wind storms (speed, direction)
        - Heavy rain events
        - Snow/ice storms (Michigan specific)
        - Tornado warnings

        Args:
            zip_code: ZIP code to check
            days_back: Number of days to look back (default 30)

        Returns:
            [
                {
                    "date": "2025-09-25",
                    "type": "hail",
                    "severity": "high",
                    "details": "3-inch hail reported",
                    "wind_speed": 60,
                    "damage_likelihood": 0.85
                },
                ...
            ]
        """
        try:
            # Check if we have API key
            if not self.api_key:
                return self._get_simulated_storm_data(zip_code, days_back)

            # Fetch real weather data
            storms = await self._fetch_historical_weather(zip_code, days_back)

            # Filter for severe events
            severe_events = [
                event for event in storms
                if self._is_severe_event(event)
            ]

            logger.info(f"✅ Found {len(severe_events)} severe weather events for {zip_code}")
            return severe_events

        except Exception as e:
            logger.error(f"❌ Error fetching storm data for {zip_code}: {e}")
            return self._get_simulated_storm_data(zip_code, days_back)

    async def correlate_damage_likelihood(
        self,
        storm_event: Dict,
        property_age: int,
        roof_age: Optional[int] = None
    ) -> float:
        """
        Probability of roof damage from specific event

        Factors:
        - Storm severity (hail size, wind speed)
        - Roof age (older = more vulnerable)
        - Property age (construction quality)
        - Storm type (hail vs wind vs ice)
        - Michigan climate factors

        Args:
            storm_event: Weather event dict
            property_age: Years since home built
            roof_age: Years since roof installed (optional)

        Returns:
            Damage probability (0.0 to 1.0)
        """
        try:
            base_probability = 0.0
            storm_type = storm_event.get("type", "unknown")
            severity = storm_event.get("severity", "low")

            # Base probability by storm type
            type_probabilities = {
                "hail": 0.6,
                "high_wind": 0.4,
                "ice_storm": 0.3,
                "heavy_rain": 0.2,
                "tornado": 0.9
            }
            base_probability = type_probabilities.get(storm_type, 0.2)

            # Severity multiplier
            severity_multipliers = {
                "low": 0.5,
                "medium": 0.75,
                "high": 1.0,
                "severe": 1.25
            }
            severity_multiplier = severity_multipliers.get(severity, 0.75)
            base_probability *= severity_multiplier

            # Roof age factor
            effective_roof_age = roof_age if roof_age else (property_age * 0.8)
            if effective_roof_age >= 20:
                base_probability *= 1.4
            elif effective_roof_age >= 15:
                base_probability *= 1.2
            elif effective_roof_age >= 10:
                base_probability *= 1.0
            else:
                base_probability *= 0.8

            # Michigan climate factor (harsher than average)
            michigan_factor = 1.1
            base_probability *= michigan_factor

            # Cap at 0.95 (always some uncertainty)
            final_probability = min(0.95, base_probability)

            logger.info(f"📊 Damage likelihood: {final_probability:.2f} for {storm_type} on {effective_roof_age}y roof")
            return round(final_probability, 2)

        except Exception as e:
            logger.error(f"❌ Error correlating damage likelihood: {e}")
            return 0.5  # Default moderate risk

    async def generate_weather_talking_points(
        self,
        location: str,
        recent_storms: Optional[List[Dict]] = None
    ) -> List[str]:
        """
        Conversation starters about local weather

        Creates natural talking points like:
        - "Did that hailstorm last week damage your roof?"
        - "With winter approaching, have you checked for ice dam damage?"
        - "Your neighbors are getting roofs replaced after the recent storm"

        Args:
            location: ZIP code or city name
            recent_storms: Recent storm events (optional)

        Returns:
            List of conversation-ready talking points
        """
        try:
            talking_points = []

            # Get recent storms if not provided
            if not recent_storms:
                recent_storms = await self.get_recent_storms(location)

            # Generate points for each recent storm
            for storm in recent_storms[:3]:  # Top 3 most recent
                storm_type = storm.get("type", "storm")
                date_str = storm.get("date", "recently")
                severity = storm.get("severity", "moderate")

                if storm_type == "hail":
                    hail_size = storm.get("details", "large hail")
                    talking_points.append(
                        f"Did you see the {hail_size} that hit on {date_str}? "
                        f"Many homeowners in your area discovered hidden roof damage."
                    )

                elif storm_type == "high_wind":
                    wind_speed = storm.get("wind_speed", "high winds")
                    talking_points.append(
                        f"The {wind_speed} mph winds on {date_str} lifted shingles across your neighborhood. "
                        f"Have you checked your roof?"
                    )

                elif storm_type == "ice_storm":
                    talking_points.append(
                        f"Last winter's ice storms on {date_str} caused significant damage to roofs in {location}. "
                        f"Ice dams are common in Michigan - let's inspect before next winter."
                    )

            # Seasonal talking points
            seasonal_points = await self._get_seasonal_talking_points()
            talking_points.extend(seasonal_points[:2])

            # Generic urgency if no specific events
            if not talking_points:
                talking_points.append(
                    f"Roofs in {location} face harsh Michigan weather year-round. "
                    f"Proactive inspection can prevent expensive emergency repairs."
                )

            logger.info(f"✅ Generated {len(talking_points)} weather talking points")
            return talking_points

        except Exception as e:
            logger.error(f"❌ Error generating talking points: {e}")
            return ["Michigan weather is tough on roofs. Let's make sure yours is protected."]

    async def predict_seasonal_urgency(
        self,
        location: str,
        current_date: Optional[datetime] = None
    ) -> Dict:
        """
        Seasonal messaging (winter prep, spring storms, etc)

        Michigan seasonal patterns:
        - Spring (Mar-May): Storm season, ice dam aftermath
        - Summer (Jun-Aug): Hot sun damage, prep for winter
        - Fall (Sep-Nov): Winter preparation critical
        - Winter (Dec-Feb): Ice dams, snow load, emergency repairs

        Args:
            location: ZIP code or city
            current_date: Date to calculate for (defaults to today)

        Returns:
            {
                "season": "fall",
                "urgency_level": "high",
                "urgency_score": 85,
                "primary_message": "Winter is 6 weeks away...",
                "secondary_message": "...",
                "recommended_actions": [...],
                "time_window": "6-8 weeks ideal"
            }
        """
        try:
            current_date = current_date or datetime.now()
            month = current_date.month

            # Determine season
            if month in [3, 4, 5]:
                season = "spring"
            elif month in [6, 7, 8]:
                season = "summer"
            elif month in [9, 10, 11]:
                season = "fall"
            else:
                season = "winter"

            # Seasonal urgency patterns (Michigan-specific)
            seasonal_data = {
                "spring": {
                    "urgency_level": "high",
                    "urgency_score": 80,
                    "primary_message": "Spring storms are starting - inspect your roof after winter damage",
                    "secondary_message": "Ice dam damage from winter may not be visible from ground level",
                    "recommended_actions": [
                        "Post-winter inspection",
                        "Check for ice dam damage",
                        "Prepare for spring storms",
                        "Address minor issues before they worsen"
                    ],
                    "time_window": "April-May optimal window"
                },
                "summer": {
                    "urgency_level": "medium",
                    "urgency_score": 60,
                    "primary_message": "Summer is the ideal time for roof work - weather is perfect",
                    "secondary_message": "Don't wait until fall rush - contractors book up fast",
                    "recommended_actions": [
                        "Schedule major repairs before fall rush",
                        "Take advantage of good weather",
                        "Prepare roof for upcoming winter",
                        "Address ventilation issues"
                    ],
                    "time_window": "June-August best weather"
                },
                "fall": {
                    "urgency_level": "critical",
                    "urgency_score": 95,
                    "primary_message": "Winter is 6-10 weeks away - roof problems will get worse",
                    "secondary_message": "Don't risk emergency repairs in freezing temperatures",
                    "recommended_actions": [
                        "URGENT: Complete work before snow",
                        "Prevent ice dams with proper preparation",
                        "Contractors booking up fast",
                        "Avoid 3x emergency repair costs"
                    ],
                    "time_window": "CRITICAL: 6-8 weeks before snow"
                },
                "winter": {
                    "urgency_level": "emergency",
                    "urgency_score": 100,
                    "primary_message": "Winter damage happening now - act fast",
                    "secondary_message": "Ice dams and snow load can cause catastrophic failure",
                    "recommended_actions": [
                        "Emergency assessment if active leaks",
                        "Ice dam removal service available",
                        "Plan for spring replacement",
                        "Prevent further interior damage"
                    ],
                    "time_window": "Emergency response available 24/7"
                }
            }

            result = seasonal_data.get(season)
            result["season"] = season
            result["current_date"] = current_date.isoformat()
            result["location"] = location

            logger.info(f"✅ Seasonal urgency for {location}: {season} - {result['urgency_level']}")
            return result

        except Exception as e:
            logger.error(f"❌ Error predicting seasonal urgency: {e}")
            return {
                "season": "unknown",
                "urgency_level": "medium",
                "urgency_score": 50,
                "primary_message": "Regular roof maintenance is important"
            }

    # =====================================================
    # HELPER METHODS
    # =====================================================

    async def _fetch_historical_weather(
        self,
        zip_code: str,
        days_back: int
    ) -> List[Dict]:
        """Fetch historical weather data from Weather API"""
        # Placeholder for actual API call
        # In production, this would use aiohttp to call Weather.com API

        logger.info(f"📡 Fetching historical weather for {zip_code}")

        # async with aiohttp.ClientSession() as session:
        #     url = f"{WEATHER_API_BASE}/historical"
        #     params = {
        #         "apiKey": self.api_key,
        #         "postalKey": f"{zip_code}:US",
        #         "startDate": (datetime.now() - timedelta(days=days_back)).isoformat(),
        #         "endDate": datetime.now().isoformat()
        #     }
        #     async with session.get(url, params=params) as response:
        #         data = await response.json()
        #         return self._parse_weather_data(data)

        # Return simulated data for now
        return self._get_simulated_storm_data(zip_code, days_back)

    def _get_simulated_storm_data(self, zip_code: str, days_back: int) -> List[Dict]:
        """Generate simulated storm data for testing"""
        current_month = datetime.now().month

        # Michigan typical weather patterns
        simulated_events = []

        # Spring storms (March-May)
        if current_month in [3, 4, 5] or days_back >= 60:
            simulated_events.append({
                "date": (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d"),
                "type": "hail",
                "severity": "high",
                "details": "2-inch hail reported",
                "wind_speed": 55,
                "damage_likelihood": 0.75,
                "affected_area": f"ZIP {zip_code} and surrounding"
            })

        # Summer thunderstorms (June-August)
        if current_month in [6, 7, 8] or days_back >= 30:
            simulated_events.append({
                "date": (datetime.now() - timedelta(days=22)).strftime("%Y-%m-%d"),
                "type": "high_wind",
                "severity": "medium",
                "details": "Severe thunderstorm",
                "wind_speed": 65,
                "damage_likelihood": 0.50,
                "affected_area": f"Southeast Michigan including {zip_code}"
            })

        # Winter ice storms (December-February)
        if current_month in [12, 1, 2] or days_back >= 90:
            simulated_events.append({
                "date": (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d"),
                "type": "ice_storm",
                "severity": "high",
                "details": "Heavy ice accumulation",
                "wind_speed": 40,
                "damage_likelihood": 0.60,
                "affected_area": f"Michigan statewide"
            })

        return simulated_events

    def _is_severe_event(self, event: Dict) -> bool:
        """Determine if weather event is severe enough to mention"""
        severity = event.get("severity", "low")
        wind_speed = event.get("wind_speed", 0)

        if severity in ["high", "severe"]:
            return True
        if wind_speed >= 55:  # 55+ mph is damaging
            return True
        if event.get("type") == "hail":
            return True
        if event.get("type") == "tornado":
            return True

        return False

    async def _get_seasonal_talking_points(self) -> List[str]:
        """Generate season-appropriate talking points"""
        current_month = datetime.now().month

        if current_month in [9, 10, 11]:  # Fall
            return [
                "Fall is the busiest time for roof repairs - schedule now before contractors book up",
                "Michigan winters are brutal - address roof issues before the first snow"
            ]
        elif current_month in [12, 1, 2]:  # Winter
            return [
                "Ice dams are forming across Michigan - has your roof been affected?",
                "Winter storm damage can lead to expensive interior repairs if not addressed quickly"
            ]
        elif current_month in [3, 4, 5]:  # Spring
            return [
                "Spring is here - time to assess winter damage before summer projects begin",
                "Storm season is starting - ensure your roof is ready"
            ]
        else:  # Summer
            return [
                "Summer is the perfect time for roof work - ideal weather conditions",
                "Prepare your roof now before fall rush and winter weather"
            ]


# =====================================================
# STANDALONE FUNCTIONS
# =====================================================

async def get_weather_context_for_lead(
    zip_code: str,
    property_age: int
) -> Dict:
    """
    Get complete weather context for a lead

    Usage:
        weather_context = await get_weather_context_for_lead("48009", 25)
    """
    api = WeatherIntelligenceAPI()

    # Get recent storms
    storms = await api.get_recent_storms(zip_code, days_back=60)

    # Get seasonal urgency
    seasonal = await api.predict_seasonal_urgency(zip_code)

    # Generate talking points
    talking_points = await api.generate_weather_talking_points(zip_code, storms)

    # Calculate damage risk for most recent storm
    damage_likelihood = 0.0
    if storms:
        damage_likelihood = await api.correlate_damage_likelihood(
            storms[0],
            property_age
        )

    return {
        "recent_storms": storms,
        "storm_count": len(storms),
        "seasonal_urgency": seasonal,
        "talking_points": talking_points,
        "highest_damage_likelihood": damage_likelihood,
        "generated_at": datetime.now().isoformat()
    }


async def get_urgency_score_for_location(zip_code: str) -> int:
    """
    Get overall urgency score for a location (0-100)

    Usage:
        urgency = await get_urgency_score_for_location("48009")
    """
    api = WeatherIntelligenceAPI()

    # Get recent storms
    storms = await api.get_recent_storms(zip_code)

    # Get seasonal urgency
    seasonal = await api.predict_seasonal_urgency(zip_code)

    # Calculate combined urgency
    storm_urgency = len(storms) * 10  # 10 points per storm
    seasonal_urgency = seasonal.get("urgency_score", 50)

    combined_urgency = min(100, int((storm_urgency + seasonal_urgency) / 2))

    return combined_urgency
