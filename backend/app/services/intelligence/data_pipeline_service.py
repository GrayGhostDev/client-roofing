"""
iSwitchRoofs Data Communication Pipeline
Automated lead discovery and customer intelligence system

This service orchestrates data collection from multiple sources:
- Public property databases (assessor records, permits, insurance claims)
- Social media (Facebook, Nextdoor, Twitter/X)
- Weather data (storm tracking, hail reports)
- Web scraping (competitor sites, review platforms)
- AI-powered analysis and lead scoring
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from dataclasses import dataclass
import asyncio
import json

from app.models.lead_sqlalchemy import Lead, LeadSourceEnum, LeadStatusEnum, LeadTemperatureEnum
from app.database import get_db

logger = logging.getLogger(__name__)


@dataclass
class LeadScore:
    """Lead scoring result"""
    total_score: int  # 0-100
    roof_age_score: int  # 0-25
    storm_damage_score: int  # 0-25
    financial_score: int  # 0-20
    urgency_score: int  # 0-15
    behavioral_score: int  # 0-15
    confidence: float  # 0.0-1.0
    reasons: List[str]


@dataclass
class DataSource:
    """Data source configuration"""
    name: str
    type: str  # public_db, social_media, weather, web_scraping
    enabled: bool
    priority: int  # 1-5, higher is more important
    rate_limit: int  # requests per hour
    cost_per_request: float  # in dollars


class DataPipelineService:
    """
    Orchestrates the entire data pipeline for lead discovery
    """

    def __init__(self, db: Session):
        self.db = db
        self.data_sources = self._initialize_data_sources()

    def _initialize_data_sources(self) -> Dict[str, DataSource]:
        """Initialize all available data sources"""
        return {
            # Public Databases
            "property_assessor": DataSource(
                name="County Property Assessor",
                type="public_db",
                enabled=True,
                priority=5,
                rate_limit=100,
                cost_per_request=0.0
            ),
            "building_permits": DataSource(
                name="Building Permit Records",
                type="public_db",
                enabled=True,
                priority=5,
                rate_limit=50,
                cost_per_request=0.0
            ),
            "insurance_claims": DataSource(
                name="Insurance Claim Data (NFIP/Public)",
                type="public_db",
                enabled=True,
                priority=4,
                rate_limit=20,
                cost_per_request=0.50
            ),

            # Social Media
            "facebook_groups": DataSource(
                name="Facebook Local Groups",
                type="social_media",
                enabled=True,
                priority=3,
                rate_limit=200,
                cost_per_request=0.0
            ),
            "nextdoor": DataSource(
                name="Nextdoor Neighborhoods",
                type="social_media",
                enabled=True,
                priority=4,
                rate_limit=100,
                cost_per_request=0.0
            ),
            "twitter": DataSource(
                name="Twitter/X Local Search",
                type="social_media",
                enabled=True,
                priority=2,
                rate_limit=150,
                cost_per_request=0.0
            ),

            # Weather Data
            "noaa_storms": DataSource(
                name="NOAA Storm Events Database",
                type="weather",
                enabled=True,
                priority=5,
                rate_limit=1000,
                cost_per_request=0.0
            ),
            "weather_underground": DataSource(
                name="Weather Underground API",
                type="weather",
                enabled=True,
                priority=4,
                rate_limit=500,
                cost_per_request=0.001
            ),

            # Web Scraping
            "competitor_sites": DataSource(
                name="Competitor Websites",
                type="web_scraping",
                enabled=True,
                priority=2,
                rate_limit=50,
                cost_per_request=0.0
            ),
            "review_platforms": DataSource(
                name="Review Platforms (Google, Yelp)",
                type="web_scraping",
                enabled=True,
                priority=3,
                rate_limit=100,
                cost_per_request=0.0
            ),
            "real_estate_listings": DataSource(
                name="Real Estate Listings (Zillow, Realtor.com)",
                type="web_scraping",
                enabled=True,
                priority=4,
                rate_limit=100,
                cost_per_request=0.10
            )
        }

    async def run_pipeline(self, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute the complete data pipeline

        Args:
            filters: Optional filters for geographic area, date range, etc.

        Returns:
            Pipeline execution results with lead count and statistics
        """
        logger.info("Starting data pipeline execution")
        start_time = datetime.utcnow()

        # Default filters for Southeast Michigan premium markets
        if not filters:
            filters = {
                "cities": [
                    "Bloomfield Hills", "Birmingham", "Grosse Pointe",
                    "Troy", "Rochester Hills", "West Bloomfield",
                    "Ann Arbor", "Canton", "Plymouth", "Northville"
                ],
                "min_home_value": 500000,  # Premium market focus
                "max_roof_age": 20,  # Roofs older than 20 years
                "date_range_days": 30  # Last 30 days
            }

        # Execute each stage of the pipeline
        results = {
            "pipeline_start": start_time.isoformat(),
            "filters": filters,
            "stages": {}
        }

        try:
            # Stage 1: Property Discovery
            logger.info("Stage 1: Property Discovery")
            property_leads = await self._discover_properties(filters)
            results["stages"]["property_discovery"] = {
                "leads_found": len(property_leads),
                "sources": ["property_assessor", "building_permits"]
            }

            # Stage 2: Storm Damage Detection
            logger.info("Stage 2: Storm Damage Detection")
            storm_leads = await self._detect_storm_damage(filters)
            results["stages"]["storm_detection"] = {
                "leads_found": len(storm_leads),
                "sources": ["noaa_storms", "weather_underground", "insurance_claims"]
            }

            # Stage 3: Social Media Monitoring
            logger.info("Stage 3: Social Media Monitoring")
            social_leads = await self._monitor_social_media(filters)
            results["stages"]["social_monitoring"] = {
                "leads_found": len(social_leads),
                "sources": ["facebook_groups", "nextdoor", "twitter"]
            }

            # Stage 4: Market Intelligence
            logger.info("Stage 4: Market Intelligence")
            market_leads = await self._gather_market_intelligence(filters)
            results["stages"]["market_intelligence"] = {
                "leads_found": len(market_leads),
                "sources": ["competitor_sites", "review_platforms", "real_estate_listings"]
            }

            # Stage 5: Lead Enrichment & Scoring
            logger.info("Stage 5: Lead Enrichment & Scoring")
            all_raw_leads = property_leads + storm_leads + social_leads + market_leads
            enriched_leads = await self._enrich_and_score_leads(all_raw_leads, filters)

            # Stage 6: Deduplication & Validation
            logger.info("Stage 6: Deduplication & Validation")
            validated_leads = await self._deduplicate_and_validate(enriched_leads)

            # Stage 7: Lead Ingestion
            logger.info("Stage 7: Lead Ingestion")
            ingested_count = await self._ingest_leads(validated_leads)

            # Calculate final statistics
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            results["pipeline_end"] = end_time.isoformat()
            results["duration_seconds"] = duration
            results["total_raw_leads"] = len(all_raw_leads)
            results["total_enriched_leads"] = len(enriched_leads)
            results["total_validated_leads"] = len(validated_leads)
            results["total_ingested_leads"] = ingested_count
            results["deduplication_rate"] = (
                (len(enriched_leads) - len(validated_leads)) / len(enriched_leads) * 100
                if enriched_leads else 0
            )
            results["status"] = "success"

            logger.info(f"Pipeline completed: {ingested_count} leads ingested in {duration:.2f}s")

        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            results["status"] = "failed"
            results["error"] = str(e)

        return results

    async def _discover_properties(self, filters: Dict) -> List[Dict]:
        """
        Stage 1: Discover properties from public databases

        Sources:
        - County property assessor records (roof age, home value, owner info)
        - Building permit records (recent roof permits = competitors, no permits = opportunity)
        """
        leads = []

        # This would integrate with actual APIs/databases
        # For now, returning sample structure

        logger.info("Searching property assessor records...")
        # TODO: Integrate with county assessor APIs
        # - Oakland County: https://www.oakgov.com/assessor/
        # - Wayne County: https://www.waynecounty.com/elected/treasurer/
        # - Washtenaw County: https://www.ewashtenaw.org/government/departments/equalization

        logger.info("Searching building permit records...")
        # TODO: Integrate with municipal building departments
        # - Pull permits for roofing work in last 5 years
        # - Properties WITHOUT recent permits = opportunity

        # Sample lead structure
        sample_lead = {
            "source": "property_assessor",
            "address": "1234 Example St",
            "city": "Bloomfield Hills",
            "state": "MI",
            "zip": "48301",
            "owner_name": "John Smith",
            "home_value": 850000,
            "year_built": 1995,
            "roof_age": 28,  # Calculated from building records
            "last_roof_permit": None,  # No recent roof work = opportunity
            "square_footage": 4500,
            "estimated_roof_size": 3600,  # sq ft
            "raw_data": {}
        }

        return leads

    async def _detect_storm_damage(self, filters: Dict) -> List[Dict]:
        """
        Stage 2: Detect storm damage opportunities

        Sources:
        - NOAA Storm Events Database (hail, wind, tornado events)
        - Weather Underground severe weather alerts
        - NFIP insurance claim data (public flood claims)
        """
        leads = []

        logger.info("Checking NOAA storm events...")
        # TODO: Integrate with NOAA Storm Events Database
        # API: https://www.ncdc.noaa.gov/stormevents/
        # - Search for hail events (>1 inch = roof damage)
        # - Wind events (>70 mph = potential damage)
        # - Map affected ZIP codes to properties

        logger.info("Checking weather alerts...")
        # TODO: Integrate with Weather Underground API
        # - Recent severe weather alerts
        # - Hail damage reports
        # - Wind damage areas

        logger.info("Checking insurance claims...")
        # TODO: Integrate with NFIP/insurance claim databases
        # - Public flood insurance claims
        # - Areas with high claim density

        # Sample lead structure
        sample_lead = {
            "source": "storm_damage",
            "address": "5678 Storm St",
            "city": "Troy",
            "state": "MI",
            "zip": "48098",
            "storm_date": "2025-09-15",
            "storm_type": "hail",
            "hail_size": 2.0,  # inches
            "wind_speed": 75,  # mph
            "damage_probability": 0.85,  # 85% chance of roof damage
            "estimated_damage_value": 15000,
            "raw_data": {}
        }

        return leads

    async def _monitor_social_media(self, filters: Dict) -> List[Dict]:
        """
        Stage 3: Monitor social media for roof-related discussions

        Sources:
        - Facebook local groups (roof damage posts, recommendations)
        - Nextdoor neighborhoods (roof questions, contractor searches)
        - Twitter/X local search (storm damage, roof issues)
        """
        leads = []

        logger.info("Monitoring Facebook groups...")
        # TODO: Integrate with Facebook Graph API
        # - Search local groups for keywords: "roof", "leak", "hail damage", "need roofer"
        # - Extract poster information
        # - Analyze post sentiment (urgent = hot lead)

        logger.info("Monitoring Nextdoor...")
        # TODO: Integrate with Nextdoor API (if available) or web scraping
        # - Monitor neighborhood posts
        # - Keywords: "roof repair", "roofing company", "recommendations"
        # - Extract homeowner information

        logger.info("Monitoring Twitter/X...")
        # TODO: Integrate with Twitter API v2
        # - Geo-tagged tweets mentioning roof issues
        # - Local hashtags: #MichiganWeather, #RoofDamage, etc.
        # - Real-time storm damage reports

        # Sample lead structure
        sample_lead = {
            "source": "nextdoor",
            "platform": "nextdoor",
            "post_text": "Does anyone know a good roofer? We have a leak after the storm.",
            "poster_name": "Jane Doe",
            "neighborhood": "Downtown Birmingham",
            "city": "Birmingham",
            "state": "MI",
            "post_date": "2025-10-10",
            "urgency": "high",  # leak = urgent
            "intent": "active_search",  # looking for roofer now
            "raw_data": {}
        }

        return leads

    async def _gather_market_intelligence(self, filters: Dict) -> List[Dict]:
        """
        Stage 4: Gather competitive and market intelligence

        Sources:
        - Competitor websites (who they're targeting, service areas)
        - Review platforms (unhappy customers = opportunities)
        - Real estate listings (new homeowners need roof inspections)
        """
        leads = []

        logger.info("Analyzing competitor activity...")
        # TODO: Web scraping competitor sites
        # - Service areas they target
        # - Pricing information
        # - Customer testimonials
        # - Active project locations

        logger.info("Mining review platforms...")
        # TODO: Integrate with Google Places API, Yelp API
        # - Find negative reviews of competitors
        # - Extract customer information
        # - Identify service gaps

        logger.info("Monitoring real estate listings...")
        # TODO: Integrate with Zillow API, Realtor.com
        # - Recently sold homes (new owners)
        # - Listings with old roofs (visible in photos)
        # - Pre-listing opportunities (sellers need roof repairs)

        # Sample lead structure
        sample_lead = {
            "source": "zillow",
            "address": "9012 Market Ave",
            "city": "Ann Arbor",
            "state": "MI",
            "zip": "48104",
            "sale_date": "2025-09-20",
            "sale_price": 725000,
            "new_owner": "Bob Johnson",
            "listing_photos_show_old_roof": True,
            "estimated_roof_age": 22,
            "opportunity_type": "new_homeowner_inspection",
            "raw_data": {}
        }

        return leads

    async def _enrich_and_score_leads(self, raw_leads: List[Dict], filters: Dict) -> List[Dict]:
        """
        Stage 5: Enrich leads with additional data and calculate lead scores

        Uses the iSwitchRoofs Lead Scoring Algorithm
        """
        enriched_leads = []

        for lead in raw_leads:
            try:
                # Enrich with additional data
                enriched_lead = await self._enrich_lead_data(lead)

                # Calculate lead score
                lead_score = self.calculate_lead_score(enriched_lead)
                enriched_lead["lead_score"] = lead_score.total_score
                enriched_lead["score_breakdown"] = {
                    "roof_age_score": lead_score.roof_age_score,
                    "storm_damage_score": lead_score.storm_damage_score,
                    "financial_score": lead_score.financial_score,
                    "urgency_score": lead_score.urgency_score,
                    "behavioral_score": lead_score.behavioral_score
                }
                enriched_lead["score_confidence"] = lead_score.confidence
                enriched_lead["score_reasons"] = lead_score.reasons

                # Determine temperature based on score
                enriched_lead["temperature"] = self._score_to_temperature(lead_score.total_score)

                enriched_leads.append(enriched_lead)

            except Exception as e:
                logger.error(f"Failed to enrich lead: {str(e)}")
                continue

        # Sort by lead score (highest first)
        enriched_leads.sort(key=lambda x: x.get("lead_score", 0), reverse=True)

        return enriched_leads

    async def _enrich_lead_data(self, lead: Dict) -> Dict:
        """Enrich lead with additional data from multiple sources"""

        # TODO: Enrich with:
        # - Demographic data (income, age, family size)
        # - Property details (roof type, material, pitch)
        # - Historical weather data for location
        # - Neighborhood average income
        # - Recent home sales in area
        # - Credit score indicators (if available)

        return lead

    def calculate_lead_score(self, lead: Dict) -> LeadScore:
        """
        🎯 iSwitchRoofs Lead Scoring Algorithm

        Total Score: 0-100 points

        Components:
        1. Roof Age Score (0-25 points)
           - Age 0-5 years: 0 points (too new)
           - Age 6-10 years: 5 points (planning phase)
           - Age 11-15 years: 10 points (consideration phase)
           - Age 16-20 years: 20 points (decision phase)
           - Age 21+ years: 25 points (urgent replacement needed)

        2. Storm Damage Score (0-25 points)
           - No recent storm: 0 points
           - Minor storm (< 1" hail, <60 mph wind): 5 points
           - Moderate storm (1-2" hail, 60-80 mph wind): 15 points
           - Major storm (> 2" hail, >80 mph wind): 25 points
           - Bonus: Insurance claim filed = +5 points

        3. Financial Capacity Score (0-20 points)
           - Home value < $300K: 5 points
           - Home value $300-500K: 10 points
           - Home value $500-750K: 15 points (premium target)
           - Home value > $750K: 20 points (ultra-premium)
           - Bonus: Recent home purchase = +5 points

        4. Urgency Score (0-15 points)
           - Active leak reported: 15 points
           - Visible damage: 10 points
           - Requesting quotes: 12 points
           - General inquiry: 5 points
           - No urgency indicators: 0 points

        5. Behavioral Score (0-15 points)
           - Social media post seeking roofer: 15 points
           - Engaged with roofing content: 10 points
           - Requested inspection: 12 points
           - Website visit only: 5 points
           - No engagement: 0 points

        Lead Temperature Mapping:
        - HOT (80-100 points): Immediate action needed, high close probability
        - WARM (60-79 points): Ready to engage, good close probability
        - COOL (40-59 points): Early stage, nurture needed
        - COLD (0-39 points): Long-term nurture, low immediate probability
        """

        reasons = []

        # 1. Roof Age Score (0-25 points)
        roof_age = lead.get("roof_age", 0)
        if roof_age >= 21:
            roof_age_score = 25
            reasons.append("Roof is 21+ years old - urgent replacement needed")
        elif roof_age >= 16:
            roof_age_score = 20
            reasons.append("Roof is 16-20 years old - in decision phase")
        elif roof_age >= 11:
            roof_age_score = 10
            reasons.append("Roof is 11-15 years old - in consideration phase")
        elif roof_age >= 6:
            roof_age_score = 5
            reasons.append("Roof is 6-10 years old - early planning phase")
        else:
            roof_age_score = 0

        # 2. Storm Damage Score (0-25 points)
        storm_damage_score = 0
        hail_size = lead.get("hail_size", 0)
        wind_speed = lead.get("wind_speed", 0)
        insurance_claim = lead.get("insurance_claim_filed", False)

        if hail_size > 2 or wind_speed > 80:
            storm_damage_score = 25
            reasons.append("Major storm damage - high probability of roof damage")
        elif hail_size > 1 or wind_speed > 60:
            storm_damage_score = 15
            reasons.append("Moderate storm damage - likely roof damage")
        elif hail_size > 0 or wind_speed > 0:
            storm_damage_score = 5
            reasons.append("Minor storm event - possible roof damage")

        if insurance_claim:
            storm_damage_score = min(30, storm_damage_score + 5)  # Cap at 30 with bonus
            reasons.append("Insurance claim filed - damage confirmed")

        # 3. Financial Capacity Score (0-20 points)
        home_value = lead.get("home_value", 0)
        recent_purchase = lead.get("recent_home_purchase", False)

        if home_value > 750000:
            financial_score = 20
            reasons.append("Ultra-premium home value >$750K - excellent financial capacity")
        elif home_value > 500000:
            financial_score = 15
            reasons.append("Premium home value $500-750K - strong financial capacity")
        elif home_value > 300000:
            financial_score = 10
            reasons.append("Mid-tier home value $300-500K - good financial capacity")
        else:
            financial_score = 5

        if recent_purchase:
            financial_score = min(25, financial_score + 5)  # Cap at 25 with bonus
            reasons.append("Recent home purchase - motivated buyer")

        # 4. Urgency Score (0-15 points)
        has_leak = lead.get("has_leak", False)
        visible_damage = lead.get("visible_damage", False)
        requesting_quotes = lead.get("requesting_quotes", False)

        if has_leak:
            urgency_score = 15
            reasons.append("Active leak reported - URGENT")
        elif requesting_quotes:
            urgency_score = 12
            reasons.append("Actively requesting quotes - ready to buy")
        elif visible_damage:
            urgency_score = 10
            reasons.append("Visible damage - needs attention")
        elif lead.get("urgency") == "high":
            urgency_score = 12
            reasons.append("High urgency indicated")
        elif lead.get("urgency") == "medium":
            urgency_score = 8
        else:
            urgency_score = lead.get("urgency_score", 0)

        # 5. Behavioral Score (0-15 points)
        intent = lead.get("intent", "")
        engagement_level = lead.get("engagement_level", "")

        if intent == "active_search":
            behavioral_score = 15
            reasons.append("Actively searching for roofer - high intent")
        elif engagement_level == "high":
            behavioral_score = 12
            reasons.append("High engagement level")
        elif lead.get("requested_inspection", False):
            behavioral_score = 12
            reasons.append("Requested inspection - strong interest")
        elif engagement_level == "medium":
            behavioral_score = 10
            reasons.append("Engaged with roofing content")
        elif lead.get("website_visit", False):
            behavioral_score = 5
        else:
            behavioral_score = 0

        # Calculate total score
        total_score = (
            roof_age_score +
            storm_damage_score +
            financial_score +
            urgency_score +
            behavioral_score
        )

        # Cap at 100
        total_score = min(100, total_score)

        # Calculate confidence based on data completeness
        data_fields = ["roof_age", "home_value", "storm_date", "urgency", "intent"]
        available_fields = sum(1 for field in data_fields if lead.get(field))
        confidence = available_fields / len(data_fields)

        return LeadScore(
            total_score=total_score,
            roof_age_score=roof_age_score,
            storm_damage_score=storm_damage_score,
            financial_score=financial_score,
            urgency_score=urgency_score,
            behavioral_score=behavioral_score,
            confidence=confidence,
            reasons=reasons
        )

    def _score_to_temperature(self, score: int) -> str:
        """Convert lead score to temperature"""
        if score >= 80:
            return "hot"
        elif score >= 60:
            return "warm"
        elif score >= 40:
            return "cool"
        else:
            return "cold"

    async def _deduplicate_and_validate(self, leads: List[Dict]) -> List[Dict]:
        """
        Stage 6: Deduplicate leads and validate contact information
        """
        validated_leads = []
        seen_addresses = set()
        seen_phones = set()
        seen_emails = set()

        for lead in leads:
            # Create deduplication key
            address_key = f"{lead.get('address', '')}{lead.get('zip', '')}".lower().strip()
            phone_key = lead.get("phone", "").replace("-", "").replace(" ", "").strip()
            email_key = lead.get("email", "").lower().strip()

            # Check for duplicates
            is_duplicate = False

            if address_key and address_key in seen_addresses:
                is_duplicate = True
                logger.debug(f"Duplicate address found: {address_key}")

            if phone_key and phone_key in seen_phones:
                is_duplicate = True
                logger.debug(f"Duplicate phone found: {phone_key}")

            if email_key and email_key in seen_emails:
                is_duplicate = True
                logger.debug(f"Duplicate email found: {email_key}")

            # Skip duplicates
            if is_duplicate:
                continue

            # Check if lead already exists in database
            if await self._lead_exists_in_db(lead):
                logger.debug(f"Lead already in database: {address_key}")
                continue

            # Validate required fields
            if not self._validate_lead(lead):
                logger.debug(f"Lead validation failed: {address_key}")
                continue

            # Mark as seen
            if address_key:
                seen_addresses.add(address_key)
            if phone_key:
                seen_phones.add(phone_key)
            if email_key:
                seen_emails.add(email_key)

            validated_leads.append(lead)

        logger.info(f"Validated {len(validated_leads)} leads (removed {len(leads) - len(validated_leads)} duplicates)")

        return validated_leads

    async def _lead_exists_in_db(self, lead: Dict) -> bool:
        """Check if lead already exists in database"""
        try:
            # Check by address
            address = lead.get("address")
            if address:
                existing = self.db.query(Lead).filter(
                    Lead.address == address,
                    Lead.is_deleted == False
                ).first()
                if existing:
                    return True

            # Check by phone
            phone = lead.get("phone")
            if phone:
                existing = self.db.query(Lead).filter(
                    Lead.phone == phone,
                    Lead.is_deleted == False
                ).first()
                if existing:
                    return True

            # Check by email
            email = lead.get("email")
            if email:
                existing = self.db.query(Lead).filter(
                    Lead.email == email,
                    Lead.is_deleted == False
                ).first()
                if existing:
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking for existing lead: {str(e)}")
            return False

    def _validate_lead(self, lead: Dict) -> bool:
        """Validate lead has minimum required information"""

        # Must have at least ONE contact method
        has_contact = any([
            lead.get("address"),
            lead.get("phone"),
            lead.get("email"),
            lead.get("owner_name")
        ])

        if not has_contact:
            return False

        # Must have location information
        has_location = lead.get("city") and lead.get("state")

        if not has_location:
            return False

        # Must have minimum lead score
        min_score = 40  # Only ingest leads with score >= 40 (warm or hot)
        if lead.get("lead_score", 0) < min_score:
            return False

        return True

    async def _ingest_leads(self, validated_leads: List[Dict]) -> int:
        """
        Stage 7: Ingest validated leads into CRM database
        """
        ingested_count = 0

        for lead_data in validated_leads:
            try:
                # Map to Lead model
                lead = Lead(
                    first_name=self._extract_first_name(lead_data.get("owner_name", "")),
                    last_name=self._extract_last_name(lead_data.get("owner_name", "")),
                    email=lead_data.get("email"),
                    phone=lead_data.get("phone"),
                    address=lead_data.get("address"),
                    city=lead_data.get("city"),
                    state=lead_data.get("state", "MI"),
                    zip_code=lead_data.get("zip"),

                    # Lead scoring
                    lead_score=lead_data.get("lead_score", 0),
                    temperature=LeadTemperatureEnum(lead_data.get("temperature", "cool")),
                    status=LeadStatusEnum.new,
                    source=self._map_source_to_enum(lead_data.get("source")),

                    # Additional metadata
                    notes=self._generate_lead_notes(lead_data),

                    # Timestamps
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )

                self.db.add(lead)
                ingested_count += 1

            except Exception as e:
                logger.error(f"Failed to ingest lead: {str(e)}")
                continue

        # Commit all leads
        try:
            self.db.commit()
            logger.info(f"Successfully ingested {ingested_count} leads")
        except Exception as e:
            logger.error(f"Failed to commit leads: {str(e)}")
            self.db.rollback()
            ingested_count = 0

        return ingested_count

    def _extract_first_name(self, full_name: str) -> str:
        """Extract first name from full name"""
        if not full_name:
            return "Unknown"
        parts = full_name.split()
        return parts[0] if parts else "Unknown"

    def _extract_last_name(self, full_name: str) -> str:
        """Extract last name from full name"""
        if not full_name:
            return "Lead"
        parts = full_name.split()
        return parts[-1] if len(parts) > 1 else "Lead"

    def _map_source_to_enum(self, source: str) -> LeadSourceEnum:
        """Map data source to LeadSourceEnum"""
        source_mapping = {
            "property_assessor": LeadSourceEnum.website_form,
            "building_permits": LeadSourceEnum.website_form,
            "storm_damage": LeadSourceEnum.door_to_door,
            "insurance_claims": LeadSourceEnum.partner_referral,
            "nextdoor": LeadSourceEnum.referral,
            "facebook_groups": LeadSourceEnum.facebook_ads,
            "twitter": LeadSourceEnum.website_form,
            "zillow": LeadSourceEnum.partner_referral,
            "competitor_sites": LeadSourceEnum.website_form,
            "review_platforms": LeadSourceEnum.referral
        }

        return source_mapping.get(source, LeadSourceEnum.website_form)

    def _generate_lead_notes(self, lead_data: Dict) -> str:
        """Generate initial notes for the lead"""
        notes_parts = []

        # Add source information
        source = lead_data.get("source", "unknown")
        notes_parts.append(f"Source: {source}")

        # Add score breakdown
        score = lead_data.get("lead_score", 0)
        notes_parts.append(f"Lead Score: {score}/100")

        # Add reasons
        reasons = lead_data.get("score_reasons", [])
        if reasons:
            notes_parts.append("Scoring Factors:")
            for reason in reasons[:3]:  # Top 3 reasons
                notes_parts.append(f"- {reason}")

        # Add storm information
        if lead_data.get("storm_date"):
            notes_parts.append(f"Storm Event: {lead_data.get('storm_type')} on {lead_data.get('storm_date')}")

        # Add urgency
        if lead_data.get("has_leak"):
            notes_parts.append("⚠️ URGENT: Active leak reported")

        return "\n".join(notes_parts)


# Singleton instance
_pipeline_service: Optional[DataPipelineService] = None


def get_pipeline_service(db: Session) -> DataPipelineService:
    """Get or create pipeline service instance"""
    return DataPipelineService(db)
