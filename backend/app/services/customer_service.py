"""
Customer Service - Business Logic Layer
Version: 1.0.0

Handles customer lifecycle management, segmentation, and value calculations.
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID

# Import SQLAlchemy ORM model
from app.models.customer_sqlalchemy import Customer

# Import Pydantic enums
from app.models.customer_schemas import CustomerSegment, CustomerStatus

# Import caching decorator
from app.utils.cache import cache_result

logger = logging.getLogger(__name__)


class CustomerService:
    """Service for customer business logic and lifecycle management."""

    def __init__(self):
        """Initialize Customer Service."""
        self.segment_thresholds = {
            "premium_ltv": 50000,  # LTV for premium segment
            "repeat_projects": 2,  # Projects for repeat customer
            "vip_ltv": 100000,  # LTV for VIP status
            "referral_min": 3,  # Min referrals for partner
        }

    def calculate_lifetime_value(self, projects: list[dict[str, Any]]) -> tuple[int, int]:
        """
        Calculate customer lifetime value from projects.

        Args:
            projects: List of customer projects

        Returns:
            Tuple of (lifetime_value, project_count)
        """
        total_value = 0
        completed_count = 0

        for project in projects:
            if project.get("status") in ["completed", "in_progress"]:
                amount = project.get("total_amount", 0)
                if amount:
                    total_value += amount
                    if project.get("status") == "completed":
                        completed_count += 1

        return total_value, completed_count

    def determine_segment(self, customer: Customer) -> CustomerSegment:
        """
        Determine customer segment based on metrics.

        Args:
            customer: Customer object

        Returns:
            CustomerSegment enum value
        """
        # Premium segment - high lifetime value
        if customer.lifetime_value >= self.segment_thresholds["premium_ltv"]:
            return CustomerSegment.PREMIUM

        # Referral source - active referrers
        if customer.referral_count >= self.segment_thresholds["referral_min"]:
            return CustomerSegment.REFERRAL_SOURCE

        # Repeat customer - multiple projects
        if customer.project_count >= self.segment_thresholds["repeat_projects"]:
            return CustomerSegment.REPEAT

        # Standard segment
        return CustomerSegment.STANDARD

    def determine_segment_from_dict(self, customer_data: dict[str, Any]) -> str:
        """
        Determine customer segment based on metrics from dict data.

        Args:
            customer_data: Customer data as dictionary

        Returns:
            String segment value
        """
        lifetime_value = customer_data.get("lifetime_value", 0)
        referral_count = customer_data.get("referral_count", 0)
        project_count = customer_data.get("project_count", 0)

        # Premium segment - high lifetime value
        if lifetime_value >= self.segment_thresholds["premium_ltv"]:
            return "premium"

        # Referral source - active referrers
        if referral_count >= self.segment_thresholds["referral_min"]:
            return "referral_source"

        # Repeat customer - multiple projects
        if project_count >= self.segment_thresholds["repeat_projects"]:
            return "repeat"

        # Standard segment
        return "standard"

    def determine_status(
        self, customer: Customer, last_project_date: datetime | None = None
    ) -> CustomerStatus:
        """
        Determine customer status based on activity.

        Args:
            customer: Customer object
            last_project_date: Date of last project

        Returns:
            CustomerStatus enum value
        """
        # VIP status for high-value customers
        if customer.lifetime_value >= self.segment_thresholds["vip_ltv"]:
            return CustomerStatus.VIP

        # Check for churn (no activity in 18 months)
        if last_project_date:
            days_since_project = (datetime.utcnow() - last_project_date).days
            if days_since_project > 547:  # 18 months
                return CustomerStatus.CHURNED

        # Check for inactive (no activity in 6 months)
        if customer.last_interaction:
            days_since_interaction = (datetime.utcnow() - customer.last_interaction).days
            if days_since_interaction > 180:
                return CustomerStatus.INACTIVE

        return CustomerStatus.ACTIVE

    def calculate_nps_category(self, nps_score: int | None) -> str:
        """
        Categorize NPS score.

        Args:
            nps_score: Net Promoter Score (0-10)

        Returns:
            NPS category string
        """
        if nps_score is None:
            return "unknown"
        elif nps_score >= 9:
            return "promoter"
        elif nps_score >= 7:
            return "passive"
        else:
            return "detractor"

    def calculate_average_project_value(self, lifetime_value: int, project_count: int) -> int:
        """
        Calculate average project value.

        Args:
            lifetime_value: Total lifetime value
            project_count: Number of projects

        Returns:
            Average project value
        """
        if project_count == 0:
            return 0
        return lifetime_value // project_count

    def get_follow_up_schedule(
        self, customer: Customer, last_project_date: datetime | None
    ) -> datetime | None:
        """
        Determine next follow-up date based on customer profile.

        Args:
            customer: Customer object
            last_project_date: Date of last project

        Returns:
            Recommended follow-up date
        """
        # VIP customers - monthly check-ins
        if customer.status == CustomerStatus.VIP:
            return datetime.utcnow() + timedelta(days=30)

        # Recent project - follow up in 3 months
        if last_project_date:
            days_since_project = (datetime.utcnow() - last_project_date).days
            if days_since_project < 90:
                return datetime.utcnow() + timedelta(days=90)

        # Active customers - quarterly
        if customer.status == CustomerStatus.ACTIVE:
            return datetime.utcnow() + timedelta(days=90)

        # Inactive - attempt re-engagement in 2 weeks
        if customer.status == CustomerStatus.INACTIVE:
            return datetime.utcnow() + timedelta(days=14)

        # Default to monthly
        return datetime.utcnow() + timedelta(days=30)

    def merge_customers(
        self, primary_id: UUID, duplicate_id: UUID, customer_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Merge duplicate customer records.

        Args:
            primary_id: Primary customer ID to keep
            duplicate_id: Duplicate customer ID to merge
            customer_data: Combined customer data

        Returns:
            Merged customer data
        """
        # Combine lifetime values
        primary_ltv = customer_data.get("primary", {}).get("lifetime_value", 0)
        duplicate_ltv = customer_data.get("duplicate", {}).get("lifetime_value", 0)

        # Combine project counts
        primary_projects = customer_data.get("primary", {}).get("project_count", 0)
        duplicate_projects = customer_data.get("duplicate", {}).get("project_count", 0)

        # Combine referral metrics
        primary_referrals = customer_data.get("primary", {}).get("referral_count", 0)
        duplicate_referrals = customer_data.get("duplicate", {}).get("referral_count", 0)

        merged = {
            "id": str(primary_id),
            "lifetime_value": primary_ltv + duplicate_ltv,
            "project_count": primary_projects + duplicate_projects,
            "referral_count": primary_referrals + duplicate_referrals,
            "merged_from": str(duplicate_id),
            "merge_date": datetime.utcnow().isoformat(),
        }

        # Recalculate average project value
        if merged["project_count"] > 0:
            merged["avg_project_value"] = merged["lifetime_value"] // merged["project_count"]

        return merged

    def export_customers_csv(
        self, customers: list[Customer], include_fields: list[str] | None = None
    ) -> str:
        """
        Export customers to CSV format.

        Args:
            customers: List of customer objects
            include_fields: Specific fields to include

        Returns:
            CSV string
        """
        import csv
        import io

        # Default fields if not specified
        if not include_fields:
            include_fields = [
                "first_name",
                "last_name",
                "email",
                "phone",
                "street_address",
                "city",
                "state",
                "zip_code",
                "lifetime_value",
                "project_count",
                "status",
                "segment",
                "nps_score",
                "created_at",
            ]

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=include_fields)
        writer.writeheader()

        for customer in customers:
            row = {}
            for field in include_fields:
                value = getattr(customer, field, None)
                if isinstance(value, (datetime, UUID)):
                    value = str(value)
                elif isinstance(value, Enum):
                    value = value.value
                row[field] = value
            writer.writerow(row)

        return output.getvalue()

    def calculate_customer_health_score(self, customer: Customer) -> int:
        """
        Calculate customer health score (0-100).

        Args:
            customer: Customer object

        Returns:
            Health score 0-100
        """
        score = 0

        # Lifetime value component (30 points)
        if customer.lifetime_value >= 100000:
            score += 30
        elif customer.lifetime_value >= 50000:
            score += 25
        elif customer.lifetime_value >= 25000:
            score += 20
        elif customer.lifetime_value >= 10000:
            score += 15
        elif customer.lifetime_value > 0:
            score += 10

        # Project frequency (20 points)
        if customer.project_count >= 5:
            score += 20
        elif customer.project_count >= 3:
            score += 15
        elif customer.project_count >= 2:
            score += 10
        elif customer.project_count == 1:
            score += 5

        # NPS score component (20 points)
        if customer.nps_score:
            if customer.nps_score >= 9:
                score += 20
            elif customer.nps_score >= 7:
                score += 15
            elif customer.nps_score >= 5:
                score += 10

        # Referral activity (15 points)
        if customer.referral_count >= 5:
            score += 15
        elif customer.referral_count >= 3:
            score += 12
        elif customer.referral_count >= 1:
            score += 8

        # Recent interaction (15 points)
        if customer.last_interaction:
            days_since = (datetime.utcnow() - customer.last_interaction).days
            if days_since <= 30:
                score += 15
            elif days_since <= 90:
                score += 10
            elif days_since <= 180:
                score += 5

        return min(score, 100)

    @cache_result(ttl=3600, key_prefix="customers")
    def get_customer_insights(
        self, customer: Customer, interactions: list[dict], projects: list[dict]
    ) -> dict[str, Any]:
        """
        Generate insights about a customer.
        Cached for 1hr (historical analytics).

        Args:
            customer: Customer object
            interactions: List of customer interactions
            projects: List of customer projects

        Returns:
            Dictionary of insights
        """
        insights = {
            "health_score": self.calculate_customer_health_score(customer),
            "nps_category": self.calculate_nps_category(customer.nps_score),
            "is_at_risk": False,
            "opportunities": [],
            "recommendations": [],
        }

        # Check if at risk
        if customer.status in [CustomerStatus.INACTIVE, CustomerStatus.CHURNED]:
            insights["is_at_risk"] = True
            insights["recommendations"].append("Schedule re-engagement campaign")

        # Check for opportunities
        if customer.lifetime_value > 30000 and not customer.is_referral_partner:
            insights["opportunities"].append("Candidate for referral program")

        if customer.project_count == 1 and customer.roof_age and customer.roof_age > 15:
            insights["opportunities"].append("May need maintenance or replacement soon")

        # Recent interaction patterns
        if interactions:
            recent_interactions = [
                i
                for i in interactions
                if (datetime.utcnow() - datetime.fromisoformat(i["date"])).days <= 30
            ]
            if len(recent_interactions) > 5:
                insights["opportunities"].append("High engagement - potential upsell opportunity")

        # Seasonal recommendations
        current_month = datetime.utcnow().month
        if current_month in [3, 4, 5]:  # Spring
            insights["recommendations"].append("Good time for roof inspection outreach")
        elif current_month in [9, 10]:  # Fall
            insights["recommendations"].append("Winter preparation services")

        return insights


# Singleton instance
customer_service = CustomerService()
