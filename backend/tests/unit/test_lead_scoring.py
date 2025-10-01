"""
iSwitch Roofs CRM - Lead Scoring Algorithm Unit Tests
Version: 1.0.0

Comprehensive test suite for lead scoring engine with 20+ test scenarios.
Tests all scoring components: demographics, behavioral, BANT, and temperature classification.
"""

import pytest
from backend.app.services.lead_scoring import LeadScoringEngine, lead_scoring_engine
from backend.app.models.lead import (
    Lead,
    LeadSource,
    LeadStatus,
    LeadTemperature,
    UrgencyLevel
)


class TestLeadScoringEngine:
    """Test suite for LeadScoringEngine"""

    def setup_method(self):
        """Setup for each test"""
        self.engine = LeadScoringEngine()

    # ========================================================================
    # HOT LEAD SCENARIOS (80-100 points)
    # ========================================================================

    def test_premium_property_hot_lead(self):
        """Test that premium properties in premium locations score HOT"""
        lead = Lead(
            first_name="John",
            last_name="Premium",
            phone="2485551234",
            source=LeadSource.WEBSITE_FORM,
            status=LeadStatus.QUALIFIED,
            property_value=600000,
            zip_code="48009",  # Birmingham (premium)
            urgency=UrgencyLevel.IMMEDIATE
        )

        breakdown = self.engine.calculate_score(
            lead,
            interaction_count=5,
            response_time_minutes=1,
            budget_confirmed=True,
            is_decision_maker=True
        )

        assert breakdown.total_score >= 80, "Premium lead should score HOT"
        assert breakdown.temperature == LeadTemperature.HOT
        assert breakdown.property_value_points == 30
        assert breakdown.location_points == 10
        assert breakdown.response_time_points == 10

    def test_urgent_referral_warm_lead(self):
        """Test urgent referral with good engagement scores WARM"""
        lead = Lead(
            first_name="Jane",
            last_name="Referral",
            phone="2485559999",
            source=LeadSource.REFERRAL,
            status=LeadStatus.APPOINTMENT_SCHEDULED,
            property_value=450000,
            zip_code="48075",  # Troy (target market)
            urgency=UrgencyLevel.IMMEDIATE
        )

        breakdown = self.engine.calculate_score(
            lead,
            interaction_count=8,
            response_time_minutes=3,
            budget_confirmed=True,
            is_decision_maker=True
        )

        assert 60 <= breakdown.total_score < 80
        assert breakdown.temperature == LeadTemperature.WARM

    def test_repeat_customer_hot_lead(self):
        """Test repeat customer automatically scores high"""
        lead = Lead(
            first_name="Bob",
            last_name="Repeat",
            phone="2485558888",
            source=LeadSource.REPEAT_CUSTOMER,
            property_value=350000,
            urgency=UrgencyLevel.ONE_TO_THREE_MONTHS
        )

        breakdown = self.engine.calculate_score(
            lead,
            interaction_count=3,
            response_time_minutes=5,
            is_decision_maker=True
        )

        # Repeat customers get high engagement points
        assert breakdown.engagement_points >= 14
        assert breakdown.total_score >= 60  # At least WARM

    # ========================================================================
    # WARM LEAD SCENARIOS (60-79 points)
    # ========================================================================

    def test_qualified_middle_market_warm_lead(self):
        """Test middle-market qualified lead scores WARM"""
        lead = Lead(
            first_name="Alice",
            last_name="Middle",
            phone="2485557777",
            source=LeadSource.GOOGLE_ADS,
            status=LeadStatus.QUALIFIED,
            property_value=350000,
            zip_code="48103",  # Ann Arbor (target)
            urgency=UrgencyLevel.ONE_TO_THREE_MONTHS
        )

        breakdown = self.engine.calculate_score(
            lead,
            interaction_count=4,
            response_time_minutes=30,
            budget_confirmed=True
        )

        assert 60 <= breakdown.total_score < 80
        assert breakdown.temperature == LeadTemperature.WARM

    def test_phone_inquiry_cool_lead(self):
        """Test direct phone inquiry with lower property value scores COOL"""
        lead = Lead(
            first_name="Charlie",
            last_name="Caller",
            phone="2485556666",
            source=LeadSource.PHONE_INQUIRY,
            property_value=280000,
            urgency=UrgencyLevel.IMMEDIATE
        )

        breakdown = self.engine.calculate_score(
            lead,
            interaction_count=2,
            response_time_minutes=2,
            is_decision_maker=True
        )

        assert 40 <= breakdown.total_score < 60
        assert breakdown.engagement_points == 15  # Phone inquiry = max engagement

    # ========================================================================
    # COOL LEAD SCENARIOS (40-59 points)
    # ========================================================================

    def test_organic_search_cold_lead(self):
        """Test organic search lead with moderate data scores COLD"""
        lead = Lead(
            first_name="David",
            last_name="Organic",
            phone="2485555555",
            source=LeadSource.ORGANIC_SEARCH,
            property_value=250000,
            urgency=UrgencyLevel.THREE_TO_SIX_MONTHS
        )

        breakdown = self.engine.calculate_score(
            lead,
            interaction_count=1,
            response_time_minutes=120
        )

        assert breakdown.total_score < 40
        assert breakdown.temperature == LeadTemperature.COLD

    def test_facebook_ad_cold_lead(self):
        """Test Facebook ad lead scores COLD"""
        lead = Lead(
            first_name="Emma",
            last_name="Facebook",
            phone="2485554444",
            source=LeadSource.FACEBOOK_ADS,
            property_value=220000
        )

        breakdown = self.engine.calculate_score(
            lead,
            interaction_count=2,
            response_time_minutes=60
        )

        assert breakdown.total_score < 40
        assert breakdown.temperature == LeadTemperature.COLD

    # ========================================================================
    # COLD LEAD SCENARIOS (0-39 points)
    # ========================================================================

    def test_door_to_door_cold_lead(self):
        """Test door-to-door lead with no follow-up scores COLD"""
        lead = Lead(
            first_name="Frank",
            last_name="Door",
            phone="2485553333",
            source=LeadSource.DOOR_TO_DOOR,
            urgency=UrgencyLevel.PLANNING
        )

        breakdown = self.engine.calculate_score(
            lead,
            interaction_count=0,
            response_time_minutes=None
        )

        assert breakdown.total_score < 40
        assert breakdown.temperature == LeadTemperature.COLD

    def test_unqualified_no_data_cold_lead(self):
        """Test lead with minimal information scores COLD"""
        lead = Lead(
            first_name="Grace",
            last_name="Unknown",
            phone="2485552222",
            source=LeadSource.ORGANIC_SEARCH
        )

        breakdown = self.engine.calculate_score(lead)

        assert breakdown.total_score < 40
        assert breakdown.temperature == LeadTemperature.COLD

    # ========================================================================
    # COMPONENT SCORING TESTS
    # ========================================================================

    def test_property_value_scoring(self):
        """Test property value scoring tiers"""
        assert self.engine._score_property_value(600000) == 30
        assert self.engine._score_property_value(400000) == 20
        assert self.engine._score_property_value(250000) == 10
        assert self.engine._score_property_value(150000) == 5
        assert self.engine._score_property_value(None) == 5

    def test_location_scoring(self):
        """Test ZIP code location scoring"""
        assert self.engine._score_location("48009") == 10  # Birmingham (premium)
        assert self.engine._score_location("48075") == 7   # Troy (target)
        assert self.engine._score_location("48201") == 3   # Detroit (other)
        assert self.engine._score_location(None) == 3

    def test_income_estimate_scoring(self):
        """Test income estimation based on property and location"""
        score = self.engine._estimate_income_score(600000, "48009")
        assert score == 15  # Max score: premium property + premium location

        score = self.engine._estimate_income_score(400000, "48075")
        assert score == 5   # Mid score: mid property + target location

        score = self.engine._estimate_income_score(None, None)
        assert score == 0   # No data

    def test_engagement_scoring_by_source(self):
        """Test engagement scoring for different lead sources"""
        # High-intent sources
        assert self.engine._score_engagement(LeadSource.WEBSITE_FORM, LeadStatus.NEW) == 15
        assert self.engine._score_engagement(LeadSource.PHONE_INQUIRY, LeadStatus.NEW) == 15
        assert self.engine._score_engagement(LeadSource.EMAIL_INQUIRY, LeadStatus.NEW) == 14

        # Medium-intent sources
        assert self.engine._score_engagement(LeadSource.GOOGLE_ADS, LeadStatus.NEW) == 12
        assert self.engine._score_engagement(LeadSource.REFERRAL, LeadStatus.NEW) == 13

        # Lower-intent sources
        assert self.engine._score_engagement(LeadSource.DOOR_TO_DOOR, LeadStatus.NEW) == 6

    def test_response_time_scoring_tiers(self):
        """Test response time scoring (critical 2-minute KPI)"""
        assert self.engine._score_response_time(1) == 10   # Target: <2 min
        assert self.engine._score_response_time(2) == 10   # Target: 2 min
        assert self.engine._score_response_time(5) == 9    # Excellent
        assert self.engine._score_response_time(30) == 5   # Acceptable
        assert self.engine._score_response_time(120) == 3  # Delayed
        assert self.engine._score_response_time(2000) == 1 # Poor
        assert self.engine._score_response_time(None) == 1 # No response

    def test_interaction_count_scoring(self):
        """Test interaction count scoring (16-touch industry standard)"""
        assert self.engine._score_interactions(0) == 0
        assert self.engine._score_interactions(2) == 3
        assert self.engine._score_interactions(4) == 5
        assert self.engine._score_interactions(7) == 7
        assert self.engine._score_interactions(15) == 10

    def test_budget_scoring(self):
        """Test budget qualification scoring"""
        assert self.engine._score_budget(True, None, None) == 8         # Confirmed
        assert self.engine._score_budget(False, 20000, None) == 6       # High range
        assert self.engine._score_budget(False, 10000, None) == 4       # Mid range
        assert self.engine._score_budget(False, None, 400000) == 3      # Inferred from property
        assert self.engine._score_budget(False, None, None) == 0        # Unknown

    def test_urgency_need_scoring(self):
        """Test urgency (Need in BANT) scoring"""
        assert self.engine._score_urgency(UrgencyLevel.IMMEDIATE) == 5
        assert self.engine._score_urgency(UrgencyLevel.ONE_TO_THREE_MONTHS) == 3
        assert self.engine._score_urgency(UrgencyLevel.THREE_TO_SIX_MONTHS) == 2
        assert self.engine._score_urgency(UrgencyLevel.PLANNING) == 1
        assert self.engine._score_urgency(None) == 1

    def test_timeline_scoring(self):
        """Test timeline (Timeline in BANT) scoring"""
        assert self.engine._score_timeline(UrgencyLevel.IMMEDIATE) == 5
        assert self.engine._score_timeline(UrgencyLevel.ONE_TO_THREE_MONTHS) == 3
        assert self.engine._score_timeline(UrgencyLevel.THREE_TO_SIX_MONTHS) == 1
        assert self.engine._score_timeline(UrgencyLevel.PLANNING) == 0
        assert self.engine._score_timeline(None) == 0

    def test_temperature_classification_boundaries(self):
        """Test temperature classification thresholds"""
        assert self.engine._classify_temperature(100) == LeadTemperature.HOT
        assert self.engine._classify_temperature(80) == LeadTemperature.HOT
        assert self.engine._classify_temperature(79) == LeadTemperature.WARM
        assert self.engine._classify_temperature(60) == LeadTemperature.WARM
        assert self.engine._classify_temperature(59) == LeadTemperature.COOL
        assert self.engine._classify_temperature(40) == LeadTemperature.COOL
        assert self.engine._classify_temperature(39) == LeadTemperature.COLD
        assert self.engine._classify_temperature(0) == LeadTemperature.COLD

    # ========================================================================
    # EDGE CASES AND ERROR HANDLING
    # ========================================================================

    def test_score_never_exceeds_100(self):
        """Test that score is capped at 100 even with max inputs"""
        lead = Lead(
            first_name="Max",
            last_name="Score",
            phone="2485551111",
            source=LeadSource.WEBSITE_FORM,
            status=LeadStatus.QUALIFIED,
            property_value=1000000,  # Very high
            zip_code="48009",
            urgency=UrgencyLevel.IMMEDIATE
        )

        breakdown = self.engine.calculate_score(
            lead,
            interaction_count=100,  # Excessive
            response_time_minutes=0,
            budget_confirmed=True,
            is_decision_maker=True
        )

        assert breakdown.total_score <= 100

    def test_missing_all_optional_data(self):
        """Test lead with only required fields"""
        lead = Lead(
            first_name="Min",
            last_name="Data",
            phone="2485550000",
            source=LeadSource.ORGANIC_SEARCH
        )

        breakdown = self.engine.calculate_score(lead)

        # Should still calculate a score, even if low
        assert 0 <= breakdown.total_score <= 100
        assert breakdown.temperature in [LeadTemperature.COLD, LeadTemperature.COOL]

    def test_recalculate_lead_score(self):
        """Test score recalculation with updated data"""
        lead = Lead(
            first_name="Update",
            last_name="Test",
            phone="2485559876",
            source=LeadSource.GOOGLE_ADS,
            status=LeadStatus.NEW,
            property_value=300000,
            response_time_minutes=5,
            interaction_count=1
        )

        # Initial score
        initial = self.engine.calculate_score(lead, interaction_count=1)
        assert initial.temperature in [LeadTemperature.COOL, LeadTemperature.WARM]

        # Update lead data
        lead.status = LeadStatus.QUALIFIED
        lead.interaction_count = 6

        # Recalculate
        updated = self.engine.recalculate_lead_score(lead, interaction_count=6)

        # Score should improve
        assert updated.total_score > initial.total_score

    def test_singleton_instance(self):
        """Test that lead_scoring_engine is a singleton"""
        from backend.app.services.lead_scoring import lead_scoring_engine as engine1
        from backend.app.services.lead_scoring import lead_scoring_engine as engine2

        assert engine1 is engine2


# Run tests with: pytest backend/tests/unit/test_lead_scoring.py -v
