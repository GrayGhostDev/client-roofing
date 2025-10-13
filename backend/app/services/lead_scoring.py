"""
iSwitch Roofs CRM - Lead Scoring Engine
Version: 1.0.0

Rule-based lead scoring algorithm (0-100 points) for qualifying and prioritizing leads.

Scoring Breakdown:
    Demographics (55 points):
      - Property Value: 30 pts
      - Location (ZIP code): 10 pts
      - Income Estimate: 15 pts

    Behavioral (35 points):
      - Website/Form Engagement: 15 pts
      - Response Time: 10 pts
      - Interaction Count: 10 pts

    BANT Qualification (10 points):
      - Budget: 8 pts
      - Authority: 7 pts (capped to keep total at 10)
      - Need: 5 pts
      - Timeline: 5 pts

Temperature Classification:
    HOT: 80-100 points (immediate action required)
    WARM: 60-79 points (qualified, high priority)
    COOL: 40-59 points (needs nurturing)
    COLD: 0-39 points (low priority/unqualified)
"""

import logging

# Import SQLAlchemy ORM model
from app.models.lead_sqlalchemy import Lead

# Import Pydantic schemas and enums
from app.models.lead_schemas import (
    LeadScoreBreakdown,
    LeadSource,
    LeadStatus,
    LeadTemperature,
    UrgencyLevel,
)

logger = logging.getLogger(__name__)


class LeadScoringEngine:
    """
    Rule-based lead scoring engine for iSwitch Roofs CRM.

    Calculates a comprehensive 0-100 point score based on demographics,
    behavioral data, and BANT qualification criteria.
    """

    # Premium zip codes in Southeast Michigan (highest value areas)
    PREMIUM_ZIP_CODES: set[str] = {
        "48009",
        "48012",
        "48025",
        "48067",  # Birmingham, Beverly Hills
        "48301",
        "48302",
        "48304",  # Bloomfield Hills, Bloomfield Township
        "48236",
        "48230",
        # Grosse Pointe (multiple areas)
        "48306",
        "48309",  # Rochester Hills
    }

    # Target market zip codes (secondary premium areas)
    TARGET_ZIP_CODES: set[str] = {
        "48075",
        "48084",
        "48098",  # Troy, West Bloomfield
        "48167",
        "48103",
        "48105",
        "48108",  # Northville, Ann Arbor
        "48331",
        "48334",
        "48335",  # Farmington Hills
        "48187",
        "48188",  # Canton, Plymouth
    }

    def calculate_score(
        self,
        lead: Lead,
        interaction_count: int = 0,
        response_time_minutes: int | None = None,
        budget_confirmed: bool = False,
        is_decision_maker: bool = False,
    ) -> LeadScoreBreakdown:
        """
        Calculate comprehensive lead score with detailed breakdown.

        Args:
            lead: Lead object with property and contact details
            interaction_count: Number of interactions with lead
            response_time_minutes: Time to first response in minutes
            budget_confirmed: Whether budget has been confirmed
            is_decision_maker: Whether contact is the decision maker

        Returns:
            LeadScoreBreakdown with total score, temperature, and point breakdown
        """
        try:
            # Demographics (55 points)
            property_value_pts = self._score_property_value(lead.property_value)
            location_pts = self._score_location(lead.zip_code)
            income_pts = self._estimate_income_score(lead.property_value, lead.zip_code)
            demographics_total = property_value_pts + location_pts + income_pts

            # Behavioral (35 points)
            engagement_pts = self._score_engagement(lead.source, lead.status)
            response_pts = self._score_response_time(
                response_time_minutes or lead.response_time_minutes
            )
            interaction_pts = self._score_interactions(interaction_count or lead.interaction_count)
            behavioral_total = engagement_pts + response_pts + interaction_pts

            # BANT (10 points max)
            budget_pts = self._score_budget(
                budget_confirmed, lead.budget_range_min, lead.property_value
            )
            authority_pts = 7 if is_decision_maker else 1
            need_pts = self._score_urgency(lead.urgency)
            timeline_pts = self._score_timeline(lead.urgency)
            bant_total = min(10, budget_pts + authority_pts + need_pts + timeline_pts)

            # Calculate total
            total = min(100, demographics_total + behavioral_total + bant_total)
            temperature = self._classify_temperature(total)

            logger.debug(
                f"Lead score calculated: {total} (Demo: {demographics_total}, "
                f"Behavior: {behavioral_total}, BANT: {bant_total}) -> {temperature.value}"
            )

            return LeadScoreBreakdown(
                total_score=total,
                temperature=temperature,
                demographics_score=demographics_total,
                property_value_points=property_value_pts,
                location_points=location_pts,
                income_estimate_points=income_pts,
                behavioral_score=behavioral_total,
                engagement_points=engagement_pts,
                response_time_points=response_pts,
                interaction_count_points=interaction_pts,
                bant_score=bant_total,
                budget_points=budget_pts,
                authority_points=authority_pts,
                need_points=need_pts,
                timeline_points=timeline_pts,
            )

        except Exception as e:
            logger.error(f"Error calculating lead score: {str(e)}", exc_info=True)
            # Return minimum score on error
            return self._get_default_score()

    def _score_property_value(self, value: int | None) -> int:
        """
        Score based on property value (0-30 points).

        Premium properties (500K+) score highest, indicating higher project value
        and customer lifetime value potential.
        """
        if not value:
            return 5  # Default for unknown

        if value >= 500000:
            return 30  # Premium property
        elif value >= 300000:
            return 20  # Upper-middle market
        elif value >= 200000:
            return 10  # Middle market
        else:
            return 5  # Entry-level market

    def _score_location(self, zip_code: str | None) -> int:
        """
        Score based on location/ZIP code (0-10 points).

        Premium and target ZIP codes in Southeast Michigan indicate
        higher-value neighborhoods with better conversion potential.
        """
        if not zip_code:
            return 3  # Default for unknown

        # Clean zip code (remove any dashes or extra digits)
        cleaned_zip = zip_code[:5] if len(zip_code) > 5 else zip_code

        if cleaned_zip in self.PREMIUM_ZIP_CODES:
            return 10  # Premium locations (Bloomfield, Grosse Pointe, etc.)
        elif cleaned_zip in self.TARGET_ZIP_CODES:
            return 7  # Target market locations (Troy, Ann Arbor, etc.)
        else:
            return 3  # Other locations

    def _estimate_income_score(self, property_value: int | None, zip_code: str | None) -> int:
        """
        Estimate income level based on property value and location (0-15 points).

        Higher income correlates with ability to afford premium roofing services
        and likelihood to invest in quality materials.
        """
        score = 0

        # Property value indicator
        if property_value:
            if property_value >= 500000:
                score += 10  # Likely $200K+ household income
            elif property_value >= 300000:
                score += 5  # Likely $100-200K household income

        # Location indicator
        if zip_code:
            cleaned_zip = zip_code[:5] if len(zip_code) > 5 else zip_code
            if cleaned_zip in self.PREMIUM_ZIP_CODES:
                score += 5  # Premium areas typically have higher incomes

        return min(15, score)  # Cap at 15 points

    def _score_engagement(self, source: LeadSource, status: LeadStatus) -> int:
        """
        Score website/form engagement (0-15 points).

        High-intent sources and qualified statuses indicate stronger interest
        and higher likelihood of conversion.
        """
        # Base score by source (intent level)
        source_scores = {
            LeadSource.WEBSITE_FORM: 15,  # Highest intent - filled out form
            LeadSource.PHONE_INQUIRY: 15,  # Direct contact
            LeadSource.EMAIL_INQUIRY: 14,  # Direct contact
            LeadSource.REFERRAL: 13,  # Trusted referral
            LeadSource.GOOGLE_LSA: 12,  # High-intent Google ads
            LeadSource.GOOGLE_ADS: 12,  # Paid search
            LeadSource.PARTNER_REFERRAL: 11,  # Professional referral
            LeadSource.ORGANIC_SEARCH: 10,  # Organic search
            LeadSource.FACEBOOK_ADS: 9,  # Social media
            LeadSource.STORM_RESPONSE: 11,  # Urgent need
            LeadSource.REPEAT_CUSTOMER: 14,  # Previous customer
            LeadSource.DOOR_TO_DOOR: 6,  # Lowest intent
        }

        base_score = source_scores.get(source, 8)

        # Boost for qualified status (shows progression)
        qualified_statuses = {
            LeadStatus.QUALIFIED,
            LeadStatus.APPOINTMENT_SCHEDULED,
            LeadStatus.INSPECTION_COMPLETED,
        }

        if status in qualified_statuses:
            base_score = min(15, base_score + 3)

        return base_score

    def _score_response_time(self, minutes: int | None) -> int:
        """
        Score response time (0-10 points).

        Critical KPI: 2-minute response time is 78% more likely to convert.
        Faster response = higher score.
        """
        if minutes is None:
            return 1  # Default for no response yet

        if minutes <= 2:
            return 10  # Target: 2-minute response (best practice)
        elif minutes <= 5:
            return 9  # Excellent response
        elif minutes <= 15:
            return 7  # Good response
        elif minutes <= 60:
            return 5  # Acceptable response (within 1 hour)
        elif minutes <= 1440:  # 24 hours
            return 3  # Delayed response
        else:
            return 1  # Poor response (>24 hours)

    def _score_interactions(self, count: int) -> int:
        """
        Score interaction count (0-10 points).

        More interactions indicate higher engagement and nurturing effort.
        Industry standard: 16+ touchpoints for conversion.
        """
        if count == 0:
            return 0  # No engagement yet
        elif count >= 10:
            return 10  # Highly engaged (approaching 16-touch standard)
        elif count >= 5:
            return 7  # Well engaged
        elif count >= 3:
            return 5  # Moderately engaged
        else:
            return 3  # Minimally engaged (1-2 interactions)

    def _score_budget(
        self, budget_confirmed: bool, budget_range_min: int | None, property_value: int | None
    ) -> int:
        """
        Score budget qualification (0-8 points).

        Budget is the 'B' in BANT - critical for qualification.
        """
        if budget_confirmed:
            return 8  # Budget explicitly confirmed

        # Infer budget potential from property value or budget range
        if budget_range_min and budget_range_min >= 15000:
            return 6  # Substantial budget indicated
        elif budget_range_min and budget_range_min >= 8000:
            return 4  # Moderate budget indicated
        elif property_value and property_value >= 300000:
            return 3  # Property value suggests budget capacity
        else:
            return 0  # No budget information

    def _score_urgency(self, urgency: UrgencyLevel | None) -> int:
        """
        Score need urgency (0-5 points).

        Urgency indicates the 'N' (Need) in BANT - how pressing is the need?
        """
        urgency_map = {
            UrgencyLevel.IMMEDIATE: 5,  # Urgent need (storm damage, leak)
            UrgencyLevel.ONE_TO_THREE_MONTHS: 3,  # Near-term need
            UrgencyLevel.THREE_TO_SIX_MONTHS: 2,  # Planning ahead
            UrgencyLevel.PLANNING: 1,  # Long-term planning
        }
        return urgency_map.get(urgency, 1) if urgency else 1

    def _score_timeline(self, urgency: UrgencyLevel | None) -> int:
        """
        Score timeline (0-5 points).

        Timeline is the 'T' in BANT - when do they plan to buy?
        """
        timeline_map = {
            UrgencyLevel.IMMEDIATE: 5,  # Ready to buy now
            UrgencyLevel.ONE_TO_THREE_MONTHS: 3,  # Near-term buyer
            UrgencyLevel.THREE_TO_SIX_MONTHS: 1,  # Future buyer
            UrgencyLevel.PLANNING: 0,  # No immediate timeline
        }
        return timeline_map.get(urgency, 0) if urgency else 0

    def _classify_temperature(self, score: int) -> LeadTemperature:
        """
        Classify lead temperature based on total score.

        Temperature determines prioritization and automated workflows:
        - HOT: Immediate sales team alert, 2-minute response required
        - WARM: High priority, same-day response
        - COOL: Nurture campaign, regular follow-up
        - COLD: Low priority, passive nurturing
        """
        if score >= 80:
            return LeadTemperature.HOT
        elif score >= 60:
            return LeadTemperature.WARM
        elif score >= 40:
            return LeadTemperature.COOL
        else:
            return LeadTemperature.COLD

    def _get_default_score(self) -> LeadScoreBreakdown:
        """Return default/minimum score breakdown on error"""
        return LeadScoreBreakdown(
            total_score=0,
            temperature=LeadTemperature.COLD,
            demographics_score=0,
            property_value_points=0,
            location_points=0,
            income_estimate_points=0,
            behavioral_score=0,
            engagement_points=0,
            response_time_points=0,
            interaction_count_points=0,
            bant_score=0,
            budget_points=0,
            authority_points=0,
            need_points=0,
            timeline_points=0,
        )

    def recalculate_lead_score(self, lead: Lead, interaction_count: int) -> LeadScoreBreakdown:
        """
        Recalculate lead score with current data.

        Use this when lead data changes (status update, new interaction, etc.)

        Args:
            lead: Updated lead object
            interaction_count: Current interaction count

        Returns:
            Updated score breakdown
        """
        return self.calculate_score(
            lead=lead,
            interaction_count=interaction_count,
            response_time_minutes=lead.response_time_minutes,
        )


# Singleton instance for application-wide use
lead_scoring_engine = LeadScoringEngine()
