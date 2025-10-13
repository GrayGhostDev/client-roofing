"""
Property Intelligence Service - Week 11 Day 1
Enrich lead data with comprehensive property intelligence

This service provides:
- Property data enrichment from multiple sources (Zillow, public records)
- Home value estimation and market analysis
- Roof age prediction and replacement timeline
- Material recommendations by property value tier
- Neighborhood trend analysis
- Risk factor detection (weather, age, condition)
- Premium property identification

Author: Week 11 Implementation
Created: 2025-10-11
"""

import os
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import json
import aiohttp
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

# Models
from app.models.lead_sqlalchemy import Lead
from app.models.project_sqlalchemy import Project

# Database
from app.utils.database import get_session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
ZILLOW_API_KEY = os.getenv("ZILLOW_API_KEY")
ZILLOW_API_BASE = "https://api.bridgedataoutput.com/api/v2/zestimates_v2/zestimates"


class PropertyIntelligenceService:
    """
    Property intelligence and enrichment service

    Provides comprehensive property data including:
    - Home values and market trends
    - Property characteristics
    - Roof age estimation
    - Material recommendations
    - Risk assessment
    """

    def __init__(self, db: Session = None):
        """Initialize property intelligence service"""
        self.db = db or next(get_session())
        self.zillow_api_key = ZILLOW_API_KEY

        if not self.zillow_api_key:
            logger.warning("⚠️ Zillow API key not configured - using fallback data sources")

    # =====================================================
    # MAIN PROPERTY INTELLIGENCE METHODS
    # =====================================================

    async def enrich_property_data(
        self,
        address: str,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None
    ) -> Dict:
        """
        Pull comprehensive property data from multiple sources

        Args:
            address: Street address
            city: City name
            state: State abbreviation (e.g., 'MI')
            zip_code: ZIP code

        Returns:
            {
                "address": "123 Main St",
                "city": "Birmingham",
                "state": "MI",
                "zip_code": "48009",
                "home_value": 650000,
                "year_built": 1995,
                "square_footage": 3500,
                "lot_size": 0.5,
                "bedrooms": 4,
                "bathrooms": 3.5,
                "property_type": "Single Family",
                "roof_data": {...},
                "neighborhood_data": {...},
                "market_trend": "hot",
                "data_sources": ["zillow", "public_records"],
                "confidence_score": 0.92,
                "last_updated": "2025-10-11T23:00:00"
            }
        """
        try:
            # Check cache first
            cached_data = await self._check_property_cache(address, zip_code)
            if cached_data:
                logger.info(f"✅ Using cached property data for {address}")
                return cached_data

            # Normalize address
            normalized_address = self._normalize_address(address, city, state, zip_code)

            # Fetch from Zillow API
            property_data = await self._fetch_zillow_data(normalized_address)

            if not property_data:
                # Fallback to public records estimate
                property_data = await self._estimate_from_public_records(
                    normalized_address, zip_code
                )

            # Enrich with roof intelligence
            property_data = await self._add_roof_intelligence(property_data)

            # Add neighborhood analysis
            property_data = await self._add_neighborhood_intelligence(
                property_data, zip_code
            )

            # Calculate confidence score
            property_data["confidence_score"] = self._calculate_data_confidence(property_data)

            # Cache the results
            await self._cache_property_data(property_data)

            logger.info(f"✅ Property enrichment complete for {address}")
            return property_data

        except Exception as e:
            logger.error(f"❌ Error enriching property data for {address}: {e}")
            # Return minimal fallback data
            return self._create_fallback_property_data(address, city, state, zip_code)

    async def estimate_roof_age(self, property_data: Dict) -> Dict:
        """
        Predict roof age and replacement timeline

        Estimates based on:
        - Home construction year
        - Last known roof replacement (if available)
        - Typical roof lifespan by material type
        - Climate factors (Michigan weather)

        Args:
            property_data: Property information dict

        Returns:
            {
                "estimated_roof_age": 18,
                "estimated_roof_year": 2007,
                "estimated_replacement_year": 2027,
                "years_until_replacement": 2,
                "roof_condition": "fair",
                "urgency_level": "medium",
                "confidence": 0.75
            }
        """
        try:
            year_built = property_data.get("year_built")
            current_year = datetime.now().year

            if not year_built:
                return {
                    "estimated_roof_age": None,
                    "urgency_level": "unknown",
                    "confidence": 0.0
                }

            # Assume original roof unless we have replacement data
            estimated_roof_year = year_built
            estimated_roof_age = current_year - estimated_roof_year

            # Typical lifespan by material (Michigan climate)
            material_lifespans = {
                "asphalt_shingles": 20,
                "architectural_shingles": 25,
                "metal": 50,
                "cedar_shake": 30,
                "slate": 100,
                "tile": 50
            }

            # Default to asphalt shingles (most common)
            assumed_material = property_data.get("roof_material", "asphalt_shingles")
            expected_lifespan = material_lifespans.get(assumed_material, 20)

            # Calculate replacement timeline
            estimated_replacement_year = estimated_roof_year + expected_lifespan
            years_until_replacement = estimated_replacement_year - current_year

            # Determine condition and urgency
            if estimated_roof_age >= expected_lifespan:
                roof_condition = "critical"
                urgency_level = "high"
            elif estimated_roof_age >= expected_lifespan * 0.8:
                roof_condition = "poor"
                urgency_level = "medium"
            elif estimated_roof_age >= expected_lifespan * 0.6:
                roof_condition = "fair"
                urgency_level = "medium"
            else:
                roof_condition = "good"
                urgency_level = "low"

            result = {
                "estimated_roof_age": estimated_roof_age,
                "estimated_roof_year": estimated_roof_year,
                "estimated_replacement_year": estimated_replacement_year,
                "years_until_replacement": years_until_replacement,
                "roof_condition": roof_condition,
                "urgency_level": urgency_level,
                "assumed_material": assumed_material,
                "expected_lifespan": expected_lifespan,
                "confidence": 0.7 if year_built else 0.0
            }

            logger.info(f"✅ Roof age estimated: {estimated_roof_age} years, condition: {roof_condition}")
            return result

        except Exception as e:
            logger.error(f"❌ Error estimating roof age: {e}")
            return {"estimated_roof_age": None, "urgency_level": "unknown", "confidence": 0.0}

    async def calculate_project_value(self, property_data: Dict) -> Dict:
        """
        Estimate appropriate pricing tier for property

        Factors:
        - Home value
        - Property type
        - Neighborhood
        - Square footage
        - Current roof condition

        Args:
            property_data: Property information

        Returns:
            {
                "recommended_tier": "ultra_premium",
                "estimated_project_cost": 45000,
                "cost_range": {"low": 40000, "high": 50000},
                "price_per_sqft": 12.50,
                "material_recommendations": [...],
                "financing_recommended": true
            }
        """
        try:
            home_value = property_data.get("home_value", 0)
            square_footage = property_data.get("square_footage", 2000)
            roof_sqft = square_footage * 1.2  # Rough estimate: roof is ~120% of floor area

            # Determine tier based on home value
            if home_value >= 500000:
                tier = "ultra_premium"
                price_per_sqft = 12.50
            elif home_value >= 250000:
                tier = "professional"
                price_per_sqft = 8.50
            else:
                tier = "standard"
                price_per_sqft = 6.00

            # Calculate estimated project cost
            estimated_cost = int(roof_sqft * price_per_sqft)
            cost_range = {
                "low": int(estimated_cost * 0.85),
                "high": int(estimated_cost * 1.15)
            }

            # Material recommendations
            material_recommendations = await self._get_material_recommendations(tier, home_value)

            # Financing recommendation
            financing_recommended = estimated_cost > 15000

            result = {
                "recommended_tier": tier,
                "estimated_project_cost": estimated_cost,
                "cost_range": cost_range,
                "price_per_sqft": price_per_sqft,
                "roof_square_footage": int(roof_sqft),
                "material_recommendations": material_recommendations,
                "financing_recommended": financing_recommended,
                "calculation_basis": {
                    "home_value": home_value,
                    "floor_sqft": square_footage,
                    "roof_sqft": int(roof_sqft)
                }
            }

            logger.info(f"✅ Project value calculated: {tier} tier, ${estimated_cost:,}")
            return result

        except Exception as e:
            logger.error(f"❌ Error calculating project value: {e}")
            return {
                "recommended_tier": "standard",
                "estimated_project_cost": 25000,
                "cost_range": {"low": 20000, "high": 30000}
            }

    async def identify_premium_indicators(self, property_data: Dict) -> List[str]:
        """
        Detect ultra-premium property signals

        Premium indicators:
        - Home value > $500K
        - Luxury neighborhood
        - Large lot size (> 0.5 acres)
        - High-end property type (Victorian, Colonial, etc.)
        - Custom features
        - Gated community

        Args:
            property_data: Property information

        Returns:
            List of premium indicator strings
        """
        indicators = []

        try:
            home_value = property_data.get("home_value", 0)
            lot_size = property_data.get("lot_size", 0)
            property_type = property_data.get("property_type", "").lower()
            neighborhood = property_data.get("neighborhood", "").lower()

            # High home value
            if home_value >= 1000000:
                indicators.append("Million-dollar property")
            elif home_value >= 500000:
                indicators.append("Premium home value ($500K+)")

            # Large lot
            if lot_size >= 1.0:
                indicators.append("Large lot size (1+ acres)")
            elif lot_size >= 0.5:
                indicators.append("Above-average lot size")

            # Premium property types
            premium_types = ["victorian", "colonial", "estate", "manor", "custom"]
            if any(ptype in property_type for ptype in premium_types):
                indicators.append(f"Premium property type: {property_type.title()}")

            # Premium neighborhoods (Michigan ultra-premium areas)
            premium_neighborhoods = [
                "bloomfield", "birmingham", "grosse pointe", "franklin",
                "bingham farms", "orchard lake", "rochester hills"
            ]
            if any(hood in neighborhood for hood in premium_neighborhoods):
                indicators.append(f"Ultra-premium neighborhood: {property_data.get('neighborhood', '')}")

            # High square footage
            sqft = property_data.get("square_footage", 0)
            if sqft >= 5000:
                indicators.append("Large home (5,000+ sq ft)")
            elif sqft >= 3500:
                indicators.append("Above-average size (3,500+ sq ft)")

            # Multiple bathrooms (indicator of luxury)
            bathrooms = property_data.get("bathrooms", 0)
            if bathrooms >= 4:
                indicators.append("Luxury bathroom count (4+)")

            logger.info(f"✅ Identified {len(indicators)} premium indicators")
            return indicators

        except Exception as e:
            logger.error(f"❌ Error identifying premium indicators: {e}")
            return []

    async def analyze_neighborhood_trends(self, zip_code: str) -> Dict:
        """
        Market trends, recent projects, competitor activity

        Analyzes:
        - Average home values in ZIP code
        - Market trend (hot, rising, stable, cooling)
        - Recent roofing projects in area
        - Competitor presence
        - Lead conversion rates in area

        Args:
            zip_code: ZIP code to analyze

        Returns:
            {
                "zip_code": "48009",
                "avg_home_value": 550000,
                "market_trend": "hot",
                "recent_projects_count": 15,
                "competitor_count": 3,
                "lead_conversion_rate": 0.32,
                "opportunity_score": 85
            }
        """
        try:
            # Query recent projects in ZIP code
            recent_projects = self.db.query(Project).filter(
                and_(
                    Project.zip_code == zip_code,
                    Project.created_at >= datetime.now() - timedelta(days=180)
                )
            ).all()

            # Query leads in ZIP code
            leads_in_area = self.db.query(Lead).filter(
                Lead.zip_code == zip_code
            ).count()

            closed_leads = self.db.query(Lead).filter(
                and_(
                    Lead.zip_code == zip_code,
                    Lead.status == "closed_won"
                )
            ).count()

            # Calculate metrics
            avg_home_value = self._estimate_zip_avg_value(zip_code)
            market_trend = self._determine_market_trend(zip_code, recent_projects)
            conversion_rate = closed_leads / leads_in_area if leads_in_area > 0 else 0.0

            # Opportunity score (0-100)
            opportunity_score = self._calculate_opportunity_score(
                avg_home_value, len(recent_projects), conversion_rate
            )

            result = {
                "zip_code": zip_code,
                "avg_home_value": avg_home_value,
                "market_trend": market_trend,
                "recent_projects_count": len(recent_projects),
                "total_leads": leads_in_area,
                "closed_deals": closed_leads,
                "lead_conversion_rate": round(conversion_rate, 3),
                "opportunity_score": opportunity_score,
                "analysis_date": datetime.now().isoformat()
            }

            logger.info(f"✅ Neighborhood analysis complete for {zip_code}: {market_trend} market, {opportunity_score} opportunity score")
            return result

        except Exception as e:
            logger.error(f"❌ Error analyzing neighborhood trends: {e}")
            return {
                "zip_code": zip_code,
                "market_trend": "unknown",
                "opportunity_score": 50
            }

    async def detect_risk_factors(
        self,
        property_data: Dict,
        weather_history: Optional[Dict] = None
    ) -> Dict:
        """
        Identify roof vulnerability factors

        Risk factors:
        - Roof age (> 15 years)
        - Recent severe weather
        - Tree coverage (debris damage)
        - North-facing slopes (ice dams in Michigan)
        - Poor ventilation indicators
        - Known problem materials

        Args:
            property_data: Property information
            weather_history: Recent weather events

        Returns:
            {
                "risk_level": "high",
                "risk_score": 75,
                "risk_factors": [
                    {"factor": "Roof age", "severity": "high", "details": "18 years old"},
                    {"factor": "Recent hail", "severity": "medium", "details": "3\" hail 30 days ago"}
                ],
                "recommendations": [...]
            }
        """
        try:
            risk_factors = []
            risk_score = 0

            # Roof age risk
            roof_age_data = await self.estimate_roof_age(property_data)
            roof_age = roof_age_data.get("estimated_roof_age", 0)

            if roof_age >= 20:
                risk_factors.append({
                    "factor": "Critical roof age",
                    "severity": "high",
                    "details": f"{roof_age} years old - likely needs replacement"
                })
                risk_score += 40
            elif roof_age >= 15:
                risk_factors.append({
                    "factor": "Aging roof",
                    "severity": "medium",
                    "details": f"{roof_age} years old - inspection recommended"
                })
                risk_score += 25

            # Weather risk
            if weather_history and weather_history.get("recent_events"):
                severe_events = [
                    e for e in weather_history["recent_events"]
                    if e.get("severity") in ["high", "severe"]
                ]

                if severe_events:
                    risk_factors.append({
                        "factor": "Recent severe weather",
                        "severity": "high",
                        "details": f"{len(severe_events)} severe weather events in last 60 days"
                    })
                    risk_score += 30

            # Michigan-specific: Winter ice dam risk
            year_built = property_data.get("year_built")
            if year_built and year_built < 2000:
                risk_factors.append({
                    "factor": "Ice dam vulnerability",
                    "severity": "medium",
                    "details": "Older Michigan home - prone to winter ice dams"
                })
                risk_score += 15

            # Property value risk (high-value homes need premium protection)
            home_value = property_data.get("home_value", 0)
            if home_value >= 500000:
                risk_factors.append({
                    "factor": "High-value property",
                    "severity": "info",
                    "details": "Premium home requires quality roofing materials"
                })
                risk_score += 10

            # Determine risk level
            if risk_score >= 60:
                risk_level = "high"
            elif risk_score >= 35:
                risk_level = "medium"
            elif risk_score >= 15:
                risk_level = "low"
            else:
                risk_level = "minimal"

            # Generate recommendations
            recommendations = self._generate_risk_recommendations(risk_factors, risk_level)

            result = {
                "risk_level": risk_level,
                "risk_score": min(100, risk_score),
                "risk_factors": risk_factors,
                "recommendations": recommendations,
                "assessment_date": datetime.now().isoformat()
            }

            logger.info(f"✅ Risk assessment complete: {risk_level} risk ({risk_score} score)")
            return result

        except Exception as e:
            logger.error(f"❌ Error detecting risk factors: {e}")
            return {
                "risk_level": "unknown",
                "risk_score": 50,
                "risk_factors": []
            }

    # =====================================================
    # HELPER METHODS
    # =====================================================

    async def _fetch_zillow_data(self, address: str) -> Optional[Dict]:
        """Fetch property data from Zillow API"""
        if not self.zillow_api_key:
            return None

        try:
            # Note: This is a placeholder for Zillow API integration
            # Actual implementation would use aiohttp to call Zillow API
            logger.info(f"📡 Fetching Zillow data for {address}")

            # Placeholder - in production, make actual API call
            # async with aiohttp.ClientSession() as session:
            #     async with session.get(ZILLOW_API_BASE, params={...}) as response:
            #         data = await response.json()

            # Return None for now (will use fallback data)
            return None

        except Exception as e:
            logger.error(f"❌ Zillow API error: {e}")
            return None

    async def _estimate_from_public_records(
        self,
        address: str,
        zip_code: Optional[str]
    ) -> Dict:
        """Estimate property data from public records and heuristics"""
        # Fallback estimates based on ZIP code averages
        zip_averages = {
            "48009": {"avg_value": 550000, "avg_sqft": 3200},  # Birmingham
            "48304": {"avg_value": 650000, "avg_sqft": 3500},  # Bloomfield Hills
            "48230": {"avg_value": 500000, "avg_sqft": 2800},  # Grosse Pointe
        }

        defaults = zip_averages.get(zip_code, {"avg_value": 300000, "avg_sqft": 2000})

        return {
            "address": address,
            "zip_code": zip_code,
            "home_value": defaults["avg_value"],
            "square_footage": defaults["avg_sqft"],
            "year_built": 1995,
            "property_type": "Single Family",
            "data_source": "estimated",
            "last_updated": datetime.now().isoformat()
        }

    async def _add_roof_intelligence(self, property_data: Dict) -> Dict:
        """Add roof-specific intelligence to property data"""
        roof_data = await self.estimate_roof_age(property_data)
        property_data["roof_intelligence"] = roof_data
        return property_data

    async def _add_neighborhood_intelligence(
        self,
        property_data: Dict,
        zip_code: Optional[str]
    ) -> Dict:
        """Add neighborhood analysis to property data"""
        if zip_code:
            neighborhood_data = await self.analyze_neighborhood_trends(zip_code)
            property_data["neighborhood_intelligence"] = neighborhood_data
        return property_data

    async def _get_material_recommendations(
        self,
        tier: str,
        home_value: int
    ) -> List[Dict]:
        """Get material recommendations based on property tier"""
        materials = {
            "ultra_premium": [
                {"name": "DaVinci Slate", "lifespan": 50, "price_psf": 18.50, "warranty": "Lifetime"},
                {"name": "Cedar Shake", "lifespan": 30, "price_psf": 15.00, "warranty": "30 years"},
                {"name": "Premium Architectural Shingles", "lifespan": 30, "price_psf": 8.50, "warranty": "Lifetime"}
            ],
            "professional": [
                {"name": "GAF Timberline HDZ", "lifespan": 25, "price_psf": 6.50, "warranty": "50 years"},
                {"name": "Standing Seam Metal", "lifespan": 50, "price_psf": 12.00, "warranty": "50 years"},
                {"name": "CertainTeed Landmark Pro", "lifespan": 25, "price_psf": 7.00, "warranty": "Lifetime"}
            ],
            "standard": [
                {"name": "Architectural Shingles", "lifespan": 25, "price_psf": 5.50, "warranty": "30 years"},
                {"name": "3-Tab Shingles", "lifespan": 20, "price_psf": 4.50, "warranty": "25 years"}
            ]
        }

        return materials.get(tier, materials["standard"])

    def _normalize_address(
        self,
        address: str,
        city: Optional[str],
        state: Optional[str],
        zip_code: Optional[str]
    ) -> str:
        """Normalize address for API calls and caching"""
        parts = [address]
        if city:
            parts.append(city)
        if state:
            parts.append(state)
        if zip_code:
            parts.append(zip_code)

        return ", ".join(parts).strip()

    async def _check_property_cache(
        self,
        address: str,
        zip_code: Optional[str]
    ) -> Optional[Dict]:
        """Check if property data is cached"""
        # TODO: Implement cache lookup from property_intelligence_cache table
        return None

    async def _cache_property_data(self, property_data: Dict) -> None:
        """Cache property data for future lookups"""
        # TODO: Implement cache storage to property_intelligence_cache table
        pass

    def _calculate_data_confidence(self, property_data: Dict) -> float:
        """Calculate confidence score for property data"""
        confidence = 0.5  # Base confidence

        if property_data.get("data_source") == "zillow":
            confidence += 0.3
        if property_data.get("home_value"):
            confidence += 0.1
        if property_data.get("year_built"):
            confidence += 0.1

        return min(1.0, confidence)

    def _create_fallback_property_data(
        self,
        address: str,
        city: Optional[str],
        state: Optional[str],
        zip_code: Optional[str]
    ) -> Dict:
        """Create minimal fallback property data"""
        return {
            "address": address,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "home_value": 300000,
            "data_source": "fallback",
            "confidence_score": 0.3,
            "last_updated": datetime.now().isoformat()
        }

    def _estimate_zip_avg_value(self, zip_code: str) -> int:
        """Estimate average home value for ZIP code"""
        # Premium Michigan ZIP codes
        premium_zips = {
            "48009": 550000,  # Birmingham
            "48304": 650000,  # Bloomfield Hills
            "48025": 700000,  # Franklin
            "48230": 500000,  # Grosse Pointe
        }
        return premium_zips.get(zip_code, 300000)

    def _determine_market_trend(self, zip_code: str, recent_projects: List) -> str:
        """Determine market trend from recent activity"""
        project_count = len(recent_projects)

        if project_count >= 20:
            return "hot"
        elif project_count >= 10:
            return "rising"
        elif project_count >= 5:
            return "stable"
        else:
            return "cooling"

    def _calculate_opportunity_score(
        self,
        avg_home_value: int,
        project_count: int,
        conversion_rate: float
    ) -> int:
        """Calculate opportunity score for ZIP code"""
        score = 0

        # Home value component (0-40 points)
        if avg_home_value >= 500000:
            score += 40
        elif avg_home_value >= 300000:
            score += 25
        else:
            score += 10

        # Activity component (0-30 points)
        score += min(30, project_count * 2)

        # Conversion component (0-30 points)
        score += int(conversion_rate * 100 * 0.3)

        return min(100, score)

    def _generate_risk_recommendations(
        self,
        risk_factors: List[Dict],
        risk_level: str
    ) -> List[str]:
        """Generate recommendations based on risk factors"""
        recommendations = []

        if risk_level in ["high", "medium"]:
            recommendations.append("Schedule free inspection within 7 days")

        if any(f["factor"] == "Critical roof age" for f in risk_factors):
            recommendations.append("Budget for roof replacement within 12 months")

        if any(f["factor"] == "Recent severe weather" for f in risk_factors):
            recommendations.append("Check for hidden storm damage - insurance may cover")

        if any(f["factor"] == "Ice dam vulnerability" for f in risk_factors):
            recommendations.append("Consider ice dam prevention system for Michigan winters")

        if not recommendations:
            recommendations.append("Schedule routine inspection for peace of mind")

        return recommendations


# =====================================================
# STANDALONE FUNCTIONS
# =====================================================

async def enrich_lead_with_property_data(lead_id: int, db: Session = None) -> Dict:
    """
    Convenience function to enrich a lead with property intelligence

    Usage:
        property_data = await enrich_lead_with_property_data(123)
    """
    service = PropertyIntelligenceService(db)
    db_session = db or next(get_session())

    lead = db_session.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise ValueError(f"Lead {lead_id} not found")

    return await service.enrich_property_data(
        address=lead.address or "",
        city=lead.city,
        state=lead.state,
        zip_code=lead.zip_code
    )
