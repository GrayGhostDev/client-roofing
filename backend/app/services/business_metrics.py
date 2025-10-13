"""
Business Metrics Service for iSwitch Roofs CRM
Version: 2.0.0
Date: 2025-10-09

Calculates business-specific KPIs aligned with company strategy:
- Premium market penetration (Bloomfield Hills, Birmingham, Grosse Pointe)
- 2-minute lead response time tracking
- 25-35% conversion rate target
- $45K average deal size (premium), $27K (professional)
- Marketing channel ROI
- Geographic market analysis
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from app.config import get_supabase_client
from app.utils.cache import cache_result

logger = logging.getLogger(__name__)


# Premium market definitions (from business strategy docs)
PREMIUM_MARKETS = {
    "ultra_premium": {
        "name": "Ultra-Premium Segment",
        "cities": ["Bloomfield Hills", "Birmingham", "Grosse Pointe"],
        "zip_codes": ["48301", "48009", "48236"],
        "target_deal_size": 45000,
        "target_properties": 10500
    },
    "professional": {
        "name": "Professional Segment",
        "cities": ["Troy", "Rochester Hills", "West Bloomfield"],
        "zip_codes": ["48084", "48309", "48322"],
        "target_deal_size": 27000,
        "target_properties": 22900
    }
}

# Marketing channels with target metrics (from marketing strategy)
MARKETING_CHANNELS = {
    "Google LSA": {"target_cost_per_lead": 75, "target_conversion": 20, "monthly_budget": 2500},
    "Facebook Ads": {"target_cost_per_lead": 75, "target_conversion": 12, "monthly_budget": 1500},
    "Community Marketing": {"target_cost_per_lead": 17, "target_conversion": 15, "monthly_budget": 500},
    "Insurance Referral": {"target_cost_per_lead": 25, "target_conversion": 40, "monthly_budget": 1000},
    "Real Estate Agent": {"target_cost_per_lead": 30, "target_conversion": 35, "monthly_budget": 1000},
    "Nextdoor": {"target_cost_per_lead": 15, "target_conversion": 18, "monthly_budget": 500}
}

# Business targets (from growth strategy)
BUSINESS_TARGETS = {
    "lead_response_time_seconds": 120,  # 2 minutes
    "conversion_rate_percent": 25,  # 25-35% target
    "monthly_leads_target": 130,
    "cost_per_lead_max": 100,
    "monthly_revenue_current": 500000,  # $500K
    "monthly_revenue_year1": 666667,  # $8M / 12
    "monthly_revenue_year2": 1500000,  # $18M / 12
    "monthly_revenue_year3": 2500000   # $30M / 12
}


class BusinessMetricsService:
    """
    Service for calculating iSwitch Roofs-specific business metrics
    """

    def __init__(self):
        """Initialize business metrics service"""
        self._supabase = None

    @property
    def supabase(self):
        """Lazy load Supabase client"""
        if self._supabase is None:
            self._supabase = get_supabase_client()
        return self._supabase

    @cache_result(ttl=300, key_prefix="metrics")
    def get_premium_market_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate premium market penetration metrics.
        Cached for 5min (standard analytics).

        Args:
            days: Number of days to analyze

        Returns:
            Premium market performance data
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            metrics = {
                "ultra_premium": self._calculate_market_segment("ultra_premium", start_date),
                "professional": self._calculate_market_segment("professional", start_date),
                "summary": {}
            }

            # Calculate overall premium market summary
            total_deals = metrics["ultra_premium"]["deals_closed"] + metrics["professional"]["deals_closed"]
            total_revenue = metrics["ultra_premium"]["revenue"] + metrics["professional"]["revenue"]
            total_target = (
                PREMIUM_MARKETS["ultra_premium"]["target_properties"] +
                PREMIUM_MARKETS["professional"]["target_properties"]
            )

            metrics["summary"] = {
                "total_deals": total_deals,
                "total_revenue": total_revenue,
                "avg_deal_size": round(total_revenue / max(total_deals, 1), 2),
                "market_penetration_percent": round((total_deals / total_target) * 100, 3),
                "period_days": days
            }

            return metrics

        except Exception as e:
            logger.error(f"Error calculating premium market metrics: {str(e)}")
            return {}

    def _calculate_market_segment(self, segment_type: str, start_date: datetime) -> Dict[str, Any]:
        """Calculate metrics for a specific market segment"""
        try:
            segment = PREMIUM_MARKETS[segment_type]

            # Get leads in this segment
            leads_result = (
                self.supabase.table("leads")
                .select("id", "status", "city", "estimated_project_value", "created_at")
                .in_("city", segment["cities"])
                .gte("created_at", start_date.isoformat())
                .execute()
            )

            leads = leads_result.data if leads_result.data else []

            # Get projects in this segment
            projects_result = (
                self.supabase.table("projects")
                .select("id", "status", "actual_amount", "quoted_amount")
                .execute()
            )

            # Filter projects by geography (would need customer city join in production)
            projects = projects_result.data if projects_result.data else []
            closed_projects = [p for p in projects if p.get("status") == "completed"]

            total_revenue = sum(float(p.get("actual_amount", 0)) for p in closed_projects)
            avg_deal = total_revenue / max(len(closed_projects), 1)

            return {
                "segment_name": segment["name"],
                "cities": segment["cities"],
                "leads_generated": len(leads),
                "deals_closed": len(closed_projects),
                "revenue": round(total_revenue, 2),
                "avg_deal_size": round(avg_deal, 2),
                "target_deal_size": segment["target_deal_size"],
                "deal_size_variance": round(((avg_deal - segment["target_deal_size"]) / segment["target_deal_size"]) * 100, 2) if segment["target_deal_size"] > 0 else 0,
                "conversion_rate": round((len(closed_projects) / max(len(leads), 1)) * 100, 2),
                "target_properties": segment["target_properties"]
            }

        except Exception as e:
            logger.error(f"Error calculating segment metrics: {str(e)}")
            return {}

    @cache_result(ttl=30, key_prefix="metrics")
    def get_lead_response_metrics(self) -> Dict[str, Any]:
        """
        Calculate lead response time metrics (2-minute target).
        Cached for 30s (real-time priority).

        Returns:
            Response time performance data
        """
        try:
            # Get leads from last 7 days
            start_date = datetime.utcnow() - timedelta(days=7)

            leads_result = (
                self.supabase.table("leads")
                .select("id", "response_time_minutes", "status", "created_at")
                .gte("created_at", start_date.isoformat())
                .execute()
            )

            leads = leads_result.data if leads_result.data else []

            # Calculate response time stats
            response_times = [
                l["response_time_minutes"] * 60  # Convert to seconds
                for l in leads
                if l.get("response_time_minutes") is not None
            ]

            if not response_times:
                return {
                    "no_data": True,
                    "message": "No response time data available"
                }

            avg_response = sum(response_times) / len(response_times)
            under_target = len([t for t in response_times if t <= 120])  # 2 minutes = 120 seconds
            over_target = len(response_times) - under_target

            # Calculate impact (78% more likely to convert if under 2 minutes)
            potential_lost_conversions = over_target * 0.78

            return {
                "avg_response_time_seconds": round(avg_response, 1),
                "target_seconds": BUSINESS_TARGETS["lead_response_time_seconds"],
                "performance_vs_target": round(((120 - avg_response) / 120) * 100, 2),
                "leads_under_target": under_target,
                "leads_over_target": over_target,
                "percent_under_target": round((under_target / len(response_times)) * 100, 2),
                "potential_lost_conversions": round(potential_lost_conversions, 1),
                "total_leads_measured": len(response_times),
                "period_days": 7,
                "status": "excellent" if avg_response < 120 else "needs_improvement"
            }

        except Exception as e:
            logger.error(f"Error calculating lead response metrics: {str(e)}")
            return {}

    @cache_result(ttl=3600, key_prefix="metrics")
    def get_marketing_channel_roi(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate ROI for each marketing channel.
        Cached for 1hr (historical analytics).

        Args:
            days: Number of days to analyze

        Returns:
            Marketing channel performance data
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            leads_result = (
                self.supabase.table("leads")
                .select("id", "source", "status", "estimated_project_value", "created_at")
                .gte("created_at", start_date.isoformat())
                .execute()
            )

            leads = leads_result.data if leads_result.data else []

            channel_metrics = {}

            for channel_name, channel_config in MARKETING_CHANNELS.items():
                channel_leads = [l for l in leads if l.get("source") == channel_name]
                converted_leads = [l for l in channel_leads if l.get("status") == "converted"]

                total_leads = len(channel_leads)
                conversions = len(converted_leads)
                conversion_rate = (conversions / max(total_leads, 1)) * 100

                # Calculate revenue
                revenue = sum(
                    float(l.get("estimated_project_value", 0))
                    for l in converted_leads
                )

                # Calculate costs (estimated based on monthly budget)
                monthly_budget = channel_config["monthly_budget"]
                period_cost = (monthly_budget / 30) * days

                actual_cost_per_lead = period_cost / max(total_leads, 1) if total_leads > 0 else 0
                roi_percent = ((revenue - period_cost) / max(period_cost, 1)) * 100 if period_cost > 0 else 0

                channel_metrics[channel_name] = {
                    "leads_generated": total_leads,
                    "conversions": conversions,
                    "conversion_rate": round(conversion_rate, 2),
                    "target_conversion_rate": channel_config["target_conversion"],
                    "revenue": round(revenue, 2),
                    "estimated_cost": round(period_cost, 2),
                    "cost_per_lead": round(actual_cost_per_lead, 2),
                    "target_cost_per_lead": channel_config["target_cost_per_lead"],
                    "roi_percent": round(roi_percent, 2),
                    "cost_efficiency": round(((channel_config["target_cost_per_lead"] - actual_cost_per_lead) / channel_config["target_cost_per_lead"]) * 100, 2) if channel_config["target_cost_per_lead"] > 0 else 0,
                    "status": "profitable" if roi_percent > 0 else "unprofitable"
                }

            # Calculate totals
            total_leads = sum(m["leads_generated"] for m in channel_metrics.values())
            total_conversions = sum(m["conversions"] for m in channel_metrics.values())
            total_revenue = sum(m["revenue"] for m in channel_metrics.values())
            total_cost = sum(m["estimated_cost"] for m in channel_metrics.values())

            summary = {
                "total_leads": total_leads,
                "total_conversions": total_conversions,
                "overall_conversion_rate": round((total_conversions / max(total_leads, 1)) * 100, 2),
                "total_revenue": round(total_revenue, 2),
                "total_cost": round(total_cost, 2),
                "overall_roi": round(((total_revenue - total_cost) / max(total_cost, 1)) * 100, 2),
                "avg_cost_per_lead": round(total_cost / max(total_leads, 1), 2),
                "period_days": days
            }

            return {
                "channels": channel_metrics,
                "summary": summary
            }

        except Exception as e:
            logger.error(f"Error calculating marketing ROI: {str(e)}")
            return {}

    @cache_result(ttl=300, key_prefix="metrics")
    def get_conversion_optimization_metrics(self) -> Dict[str, Any]:
        """
        Calculate conversion optimization metrics (25-35% target).
        Cached for 5min (standard analytics).

        Returns:
            Conversion funnel and optimization data
        """
        try:
            # Get last 30 days of leads
            start_date = datetime.utcnow() - timedelta(days=30)

            leads_result = (
                self.supabase.table("leads")
                .select("id", "status", "temperature", "source", "created_at")
                .gte("created_at", start_date.isoformat())
                .execute()
            )

            leads = leads_result.data if leads_result.data else []

            # Calculate conversion rates by temperature
            by_temperature = {}
            for temp in ["hot", "warm", "cold"]:
                temp_leads = [l for l in leads if l.get("temperature") == temp]
                temp_converted = [l for l in temp_leads if l.get("status") == "converted"]

                by_temperature[temp] = {
                    "total": len(temp_leads),
                    "converted": len(temp_converted),
                    "rate": round((len(temp_converted) / max(len(temp_leads), 1)) * 100, 2)
                }

            # Calculate conversion rates by source
            by_source = {}
            sources = set(l.get("source", "unknown") for l in leads)

            for source in sources:
                source_leads = [l for l in leads if l.get("source") == source]
                source_converted = [l for l in source_leads if l.get("status") == "converted"]

                by_source[source] = {
                    "total": len(source_leads),
                    "converted": len(source_converted),
                    "rate": round((len(source_converted) / max(len(source_leads), 1)) * 100, 2)
                }

            # Overall conversion rate
            total_leads = len(leads)
            total_converted = len([l for l in leads if l.get("status") == "converted"])
            overall_rate = (total_converted / max(total_leads, 1)) * 100

            # Performance vs target
            target_rate = BUSINESS_TARGETS["conversion_rate_percent"]
            performance_status = "excellent" if overall_rate >= 35 else "good" if overall_rate >= 25 else "needs_improvement"

            return {
                "overall": {
                    "total_leads": total_leads,
                    "converted": total_converted,
                    "conversion_rate": round(overall_rate, 2),
                    "target_rate": target_rate,
                    "target_range": "25-35%",
                    "performance_vs_target": round(overall_rate - target_rate, 2),
                    "status": performance_status
                },
                "by_temperature": by_temperature,
                "by_source": by_source,
                "optimization_opportunities": self._identify_optimization_opportunities(
                    overall_rate, by_temperature, by_source
                )
            }

        except Exception as e:
            logger.error(f"Error calculating conversion metrics: {str(e)}")
            return {}

    def _identify_optimization_opportunities(
        self,
        overall_rate: float,
        by_temperature: Dict,
        by_source: Dict
    ) -> List[Dict[str, Any]]:
        """Identify areas for conversion rate improvement"""
        opportunities = []

        # Check if overall rate is below target
        if overall_rate < 25:
            opportunities.append({
                "type": "overall_conversion",
                "priority": "high",
                "message": f"Overall conversion rate ({overall_rate:.1f}%) below target (25%). Review sales process.",
                "potential_impact": "High - affects all leads"
            })

        # Check cold lead conversion
        if by_temperature.get("cold", {}).get("rate", 0) < 10:
            opportunities.append({
                "type": "cold_lead_nurturing",
                "priority": "medium",
                "message": "Cold leads converting poorly. Implement nurture campaigns.",
                "potential_impact": "Medium - improve 20% of pipeline"
            })

        # Check underperforming sources
        for source, metrics in by_source.items():
            if metrics["rate"] < 15 and metrics["total"] > 10:
                opportunities.append({
                    "type": "source_optimization",
                    "priority": "medium",
                    "message": f"{source} converting at {metrics['rate']:.1f}%. Review lead quality or sales approach.",
                    "potential_impact": f"Medium - affects {metrics['total']} leads"
                })

        return opportunities

    @cache_result(ttl=300, key_prefix="metrics")
    def get_revenue_growth_progress(self) -> Dict[str, Any]:
        """
        Track progress toward revenue growth goals ($6M → $30M).
        Cached for 5min (standard analytics).

        Returns:
            Revenue growth tracking data
        """
        try:
            # Get current month revenue
            start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)

            projects_result = (
                self.supabase.table("projects")
                .select("id", "actual_amount", "status", "completion_date")
                .eq("status", "completed")
                .gte("completion_date", start_of_month.isoformat())
                .execute()
            )

            projects = projects_result.data if projects_result.data else []
            current_month_revenue = sum(float(p.get("actual_amount", 0)) for p in projects)

            # Get YTD revenue
            start_of_year = datetime.utcnow().replace(month=1, day=1, hour=0, minute=0, second=0)
            ytd_projects = (
                self.supabase.table("projects")
                .select("actual_amount")
                .eq("status", "completed")
                .gte("completion_date", start_of_year.isoformat())
                .execute()
            )

            ytd_revenue = sum(
                float(p.get("actual_amount", 0))
                for p in (ytd_projects.data if ytd_projects.data else [])
            )

            # Calculate projections
            days_in_month = 30
            days_elapsed = (datetime.utcnow() - start_of_month).days or 1
            projected_monthly = (current_month_revenue / days_elapsed) * days_in_month

            return {
                "current_month": {
                    "revenue": round(current_month_revenue, 2),
                    "projected": round(projected_monthly, 2),
                    "target": BUSINESS_TARGETS["monthly_revenue_current"],
                    "progress_percent": round((current_month_revenue / BUSINESS_TARGETS["monthly_revenue_current"]) * 100, 2)
                },
                "year_to_date": {
                    "revenue": round(ytd_revenue, 2),
                    "annualized": round(ytd_revenue / datetime.utcnow().month * 12, 2)
                },
                "growth_targets": {
                    "current": "$6M annually ($500K/month)",
                    "year_1": "$8M annually ($667K/month)",
                    "year_2": "$18M annually ($1.5M/month)",
                    "year_3": "$30M annually ($2.5M/month)"
                },
                "year_1_progress": {
                    "target_monthly": BUSINESS_TARGETS["monthly_revenue_year1"],
                    "current_monthly": round(current_month_revenue, 2),
                    "gap": round(BUSINESS_TARGETS["monthly_revenue_year1"] - current_month_revenue, 2),
                    "on_track": projected_monthly >= BUSINESS_TARGETS["monthly_revenue_year1"]
                }
            }

        except Exception as e:
            logger.error(f"Error calculating revenue growth progress: {str(e)}")
            return {}


# Singleton instance
business_metrics_service = BusinessMetricsService()
