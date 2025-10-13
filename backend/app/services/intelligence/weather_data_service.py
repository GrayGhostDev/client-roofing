"""
Weather Data Integration Service
Tracks storms, hail events, and weather-related roof damage opportunities
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import requests
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)


@dataclass
class StormEvent:
    """Storm event data"""
    event_id: str
    event_type: str  # hail, wind, tornado, flood
    event_date: datetime
    state: str
    county: str
    affected_zips: List[str]
    hail_size: Optional[float]  # inches
    wind_speed: Optional[int]  # mph
    damage_estimate: Optional[int]  # dollars
    injuries: int
    deaths: int
    property_damage_description: str


class WeatherDataService:
    """
    Integrates with weather data sources to identify roof damage opportunities

    Data Sources:
    1. NOAA Storm Events Database (free, public)
    2. Weather Underground API (paid)
    3. National Weather Service (free, public)
    4. Insurance claims data (where available)
    """

    def __init__(self):
        self.noaa_api_key = os.getenv("NOAA_API_KEY", "")
        self.wunderground_api_key = os.getenv("WUNDERGROUND_API_KEY", "")

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "iSwitchRoofs-DataPipeline/1.0"
        })

    async def get_recent_storms(
        self,
        state: str = "MI",
        days_back: int = 90,
        min_hail_size: float = 1.0
    ) -> List[StormEvent]:
        """
        Get recent storm events

        Args:
            state: State abbreviation
            days_back: How many days to look back
            min_hail_size: Minimum hail size in inches (1.0" = potential damage)

        Returns:
            List of storm events
        """
        logger.info(f"Fetching storms for {state} from last {days_back} days")

        start_date = datetime.now() - timedelta(days=days_back)

        # Fetch from NOAA Storm Events Database
        storms = await self._fetch_noaa_storms(state, start_date, min_hail_size)

        logger.info(f"Found {len(storms)} significant storm events")

        return storms

    async def get_affected_properties(
        self,
        storm_event: StormEvent,
        property_value_min: int = 500000
    ) -> List[Dict]:
        """
        Get properties affected by a storm event

        Args:
            storm_event: Storm event data
            property_value_min: Minimum property value to consider

        Returns:
            List of affected properties
        """
        logger.info(f"Finding properties affected by storm {storm_event.event_id}")

        affected_properties = []

        # For each affected ZIP code, get premium properties
        for zip_code in storm_event.affected_zips:
            properties = await self._get_properties_in_zip(zip_code, property_value_min)

            # Add storm context to each property
            for prop in properties:
                prop["storm_event_id"] = storm_event.event_id
                prop["storm_date"] = storm_event.event_date.isoformat()
                prop["storm_type"] = storm_event.event_type
                prop["hail_size"] = storm_event.hail_size
                prop["wind_speed"] = storm_event.wind_speed
                prop["damage_probability"] = self._calculate_damage_probability(storm_event)
                prop["estimated_damage_value"] = self._estimate_damage_cost(
                    prop.get("estimated_roof_size", 0),
                    storm_event
                )

                affected_properties.append(prop)

        logger.info(f"Found {len(affected_properties)} premium properties in affected area")

        return affected_properties

    async def _fetch_noaa_storms(
        self,
        state: str,
        start_date: datetime,
        min_hail_size: float
    ) -> List[StormEvent]:
        """
        Fetch storm data from NOAA Storm Events Database

        API: https://www.ncdc.noaa.gov/stormevents/
        """

        # NOAA Storm Events API endpoint
        base_url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data"

        params = {
            "datasetid": "GHCND",  # Global Historical Climatology Network
            "datatypeid": "PRCP",  # Precipitation
            "locationid": f"FIPS:{state}",
            "startdate": start_date.strftime("%Y-%m-%d"),
            "enddate": datetime.now().strftime("%Y-%m-%d"),
            "limit": 1000
        }

        headers = {
            "token": self.noaa_api_key
        }

        try:
            # TODO: Implement actual API call
            # response = self.session.get(base_url, params=params, headers=headers)
            # response.raise_for_status()
            # data = response.json()

            # For now, return sample data structure
            logger.info("NOAA API call would be made here")

            return []

        except Exception as e:
            logger.error(f"Failed to fetch NOAA data: {str(e)}")
            return []

    async def _get_properties_in_zip(
        self,
        zip_code: str,
        min_value: int
    ) -> List[Dict]:
        """Get premium properties in a ZIP code"""

        # TODO: Integrate with property database service
        # For now, return empty list

        return []

    def _calculate_damage_probability(self, storm: StormEvent) -> float:
        """
        Calculate probability of roof damage based on storm characteristics

        Factors:
        - Hail size: >2" = 95%, 1-2" = 75%, <1" = 30%
        - Wind speed: >80mph = 85%, 60-80mph = 50%, <60mph = 20%
        - Age of roof: Older roofs more susceptible
        """

        probability = 0.0

        # Hail damage probability
        if storm.hail_size:
            if storm.hail_size >= 2.0:
                probability = max(probability, 0.95)
            elif storm.hail_size >= 1.5:
                probability = max(probability, 0.85)
            elif storm.hail_size >= 1.0:
                probability = max(probability, 0.75)
            else:
                probability = max(probability, 0.30)

        # Wind damage probability
        if storm.wind_speed:
            if storm.wind_speed >= 80:
                probability = max(probability, 0.85)
            elif storm.wind_speed >= 70:
                probability = max(probability, 0.65)
            elif storm.wind_speed >= 60:
                probability = max(probability, 0.50)
            else:
                probability = max(probability, 0.20)

        # Tornado = very high probability
        if storm.event_type == "tornado":
            probability = max(probability, 0.90)

        return round(probability, 2)

    def _estimate_damage_cost(
        self,
        roof_size: int,
        storm: StormEvent
    ) -> int:
        """
        Estimate repair/replacement cost based on storm severity

        Costs (per square foot):
        - Minor repairs: $5-10/sq ft
        - Moderate damage: $10-15/sq ft
        - Major damage (replacement): $15-25/sq ft
        """

        if not roof_size:
            roof_size = 3000  # Average premium home roof

        # Determine damage level
        if storm.event_type == "tornado":
            cost_per_sqft = 20  # Full replacement likely
        elif (storm.hail_size and storm.hail_size >= 2.0) or (storm.wind_speed and storm.wind_speed >= 80):
            cost_per_sqft = 18  # Major damage
        elif (storm.hail_size and storm.hail_size >= 1.0) or (storm.wind_speed and storm.wind_speed >= 60):
            cost_per_sqft = 12  # Moderate damage
        else:
            cost_per_sqft = 7  # Minor repairs

        return roof_size * cost_per_sqft

    async def get_weather_alerts(self, zip_codes: List[str]) -> List[Dict]:
        """
        Get active weather alerts for ZIP codes

        Real-time alerts for:
        - Severe thunderstorms
        - Hail warnings
        - High wind warnings
        """

        # TODO: Integrate with National Weather Service API
        # API: https://www.weather.gov/documentation/services-web-api

        alerts = []

        for zip_code in zip_codes:
            # Sample alert structure
            alert = {
                "zip_code": zip_code,
                "alert_type": "Severe Thunderstorm Warning",
                "severity": "Severe",
                "certainty": "Observed",
                "urgency": "Immediate",
                "event": "Severe Thunderstorm",
                "headline": "Severe Thunderstorm Warning",
                "description": "Hail up to 2 inches and wind gusts up to 70 mph expected",
                "instruction": "Move to interior room on lowest floor. Avoid windows.",
                "onset": datetime.now().isoformat(),
                "expires": (datetime.now() + timedelta(hours=2)).isoformat()
            }

        return alerts


# Singleton
_weather_service: Optional[WeatherDataService] = None


def get_weather_service() -> WeatherDataService:
    """Get or create weather service instance"""
    global _weather_service
    if not _weather_service:
        _weather_service = WeatherDataService()
    return _weather_service
