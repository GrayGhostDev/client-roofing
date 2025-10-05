"""
Enhanced Analytics Service for iSwitch Roofs CRM
Version: 2.0.0
Date: 2025-01-05

Advanced analytics engine with comprehensive business intelligence,
roofing industry-specific metrics, and predictive analytics.

Features:
- Roofing industry KPIs and benchmarks
- Weather impact correlation analysis
- Seasonal trend forecasting
- Customer lifetime value optimization
- Marketing ROI attribution modeling
- Team performance optimization
- Predictive lead scoring enhancement
- Real-time business intelligence alerts
"""

import json
import logging
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

# Advanced analytics
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Database and caching
from app.config import get_redis_client, get_supabase_client
from app.models.analytics import (
    AnalyticsTimeframe,
)

# Real-time updates
from app.utils.pusher_client import get_pusher_service

logger = logging.getLogger(__name__)


@dataclass
class RoofingBenchmarks:
    """Industry benchmarks for roofing businesses"""

    # Lead metrics
    avg_response_time_minutes: float = 15.0
    target_conversion_rate: float = 25.0
    excellent_conversion_rate: float = 35.0

    # Revenue metrics
    avg_project_value: float = 25000.0
    premium_project_value: float = 45000.0
    target_gross_margin: float = 40.0

    # Operational metrics
    target_appointment_show_rate: float = 85.0
    target_customer_satisfaction: float = 4.5
    target_nps_score: float = 70.0

    # Seasonal factors
    peak_season_multiplier: float = 1.4  # Spring/Summer boost
    storm_season_multiplier: float = 2.0  # Storm response boost
    winter_slowdown_factor: float = 0.6  # Winter reduction


@dataclass
class WeatherFactors:
    """Weather impact factors for roofing business"""

    # Weather conditions that drive leads
    hail_lead_multiplier: float = 3.0
    storm_lead_multiplier: float = 2.5
    wind_damage_threshold_mph: float = 50.0

    # Work disruption factors
    rain_disruption_factor: float = 0.3
    snow_disruption_factor: float = 0.1
    extreme_cold_threshold: float = 20.0  # Fahrenheit

    # Seasonal patterns
    spring_peak_factor: float = 1.3
    summer_work_factor: float = 1.2
    fall_rush_factor: float = 1.1
    winter_emergency_factor: float = 0.4


class EnhancedAnalyticsService:
    """
    Enhanced analytics service with roofing industry intelligence
    """

    def __init__(self):
        """Initialize enhanced analytics service"""
        self._supabase = None
        self._redis = None
        self._pusher = None

        # Industry benchmarks and factors
        self.benchmarks = RoofingBenchmarks()
        self.weather_factors = WeatherFactors()

        # Cache configuration
        self.cache_ttl = {
            "realtime": 30,  # 30 seconds
            "standard": 300,  # 5 minutes
            "historical": 3600,  # 1 hour
            "forecasts": 7200,  # 2 hours
            "weather": 1800,  # 30 minutes
        }

        # KPI calculation weights for composite scores
        self.kpi_weights = {
            "business_health": {
                "conversion_rate": 0.25,
                "response_time": 0.20,
                "customer_satisfaction": 0.20,
                "revenue_growth": 0.20,
                "operational_efficiency": 0.15,
            },
            "team_performance": {
                "conversion_rate": 0.30,
                "response_time": 0.25,
                "activity_level": 0.20,
                "customer_feedback": 0.15,
                "quota_achievement": 0.10,
            },
            "marketing_effectiveness": {
                "cost_per_lead": 0.30,
                "conversion_rate": 0.25,
                "roi": 0.25,
                "lead_quality": 0.20,
            },
        }

    @property
    def supabase(self):
        """Lazy load Supabase client"""
        if self._supabase is None:
            self._supabase = get_supabase_client()
        return self._supabase

    @property
    def redis_client(self):
        """Lazy load Redis client"""
        if self._redis is None:
            self._redis = get_redis_client()
        return self._redis

    @property
    def pusher_service(self):
        """Lazy load Pusher service"""
        if self._pusher is None:
            self._pusher = get_pusher_service()
        return self._pusher

    # Enhanced KPI Calculations

    def calculate_roofing_kpis(
        self, timeframe: AnalyticsTimeframe = AnalyticsTimeframe.MTD
    ) -> dict[str, Any]:
        """
        Calculate roofing industry-specific KPIs

        Args:
            timeframe: Analysis timeframe

        Returns:
            Comprehensive KPI metrics with industry benchmarks
        """
        try:
            cache_key = f"enhanced_analytics:roofing_kpis:{timeframe}"
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data

            start_date, end_date = self._get_date_range(timeframe)

            # Calculate core business metrics
            lead_metrics = self._calculate_enhanced_lead_metrics(start_date, end_date)
            revenue_metrics = self._calculate_enhanced_revenue_metrics(start_date, end_date)
            operational_metrics = self._calculate_enhanced_operational_metrics(start_date, end_date)
            customer_metrics = self._calculate_enhanced_customer_metrics(start_date, end_date)
            seasonal_metrics = self._calculate_seasonal_metrics(start_date, end_date)
            weather_metrics = self._calculate_weather_impact_metrics(start_date, end_date)

            # Calculate composite health scores
            business_health_score = self._calculate_business_health_score(
                lead_metrics, revenue_metrics, operational_metrics, customer_metrics
            )

            # Generate insights and recommendations
            insights = self._generate_business_insights(
                lead_metrics,
                revenue_metrics,
                operational_metrics,
                customer_metrics,
                seasonal_metrics,
                weather_metrics,
            )

            # Create comprehensive KPI response
            kpis = {
                "timestamp": datetime.utcnow().isoformat(),
                "timeframe": timeframe,
                "period_summary": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days_in_period": (end_date - start_date).days,
                    "business_health_score": business_health_score,
                },
                "leads": lead_metrics,
                "revenue": revenue_metrics,
                "operations": operational_metrics,
                "customers": customer_metrics,
                "seasonal": seasonal_metrics,
                "weather_impact": weather_metrics,
                "insights": insights,
                "benchmarks": self._get_industry_benchmarks(),
                "alerts": self._generate_intelligent_alerts(
                    lead_metrics, revenue_metrics, operational_metrics
                ),
            }

            # Cache results
            self._cache_data(cache_key, kpis, self.cache_ttl["standard"])

            # Broadcast update
            self._broadcast_enhanced_metrics_update(kpis)

            return kpis

        except Exception as e:
            logger.error(f"Error calculating roofing KPIs: {str(e)}")
            return {}

    def _calculate_enhanced_lead_metrics(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Calculate enhanced lead metrics with roofing industry insights"""
        try:
            # Get leads with enhanced data
            leads_result = (
                self.supabase.table("leads")
                .select(
                    "id",
                    "created_at",
                    "temperature",
                    "lead_score",
                    "source",
                    "assigned_to",
                    "status",
                    "response_time_minutes",
                    "urgency",
                    "property_value",
                    "roof_age",
                    "insurance_claim",
                    "zip_code",
                )
                .gte("created_at", start_date.isoformat())
                .lte("created_at", end_date.isoformat())
                .execute()
            )

            leads = leads_result.data if leads_result.data else []

            # Basic metrics
            total_leads = len(leads)
            hot_leads = len([l for l in leads if l.get("temperature") == "hot"])
            warm_leads = len([l for l in leads if l.get("temperature") == "warm"])
            cold_leads = len([l for l in leads if l.get("temperature") == "cold"])

            # Response time analysis
            response_times = [
                l["response_time_minutes"] for l in leads if l.get("response_time_minutes")
            ]
            avg_response_time = statistics.mean(response_times) if response_times else 0
            response_within_2min = len([t for t in response_times if t <= 2])
            response_rate_2min = (response_within_2min / max(len(response_times), 1)) * 100

            # Lead quality analysis
            high_value_leads = len([l for l in leads if l.get("property_value", 0) > 500000])
            insurance_leads = len([l for l in leads if l.get("insurance_claim")])
            urgent_leads = len([l for l in leads if l.get("urgency") == "immediate"])

            # Source performance
            source_performance = {}
            for lead in leads:
                source = lead.get("source", "unknown")
                if source not in source_performance:
                    source_performance[source] = {"count": 0, "hot_count": 0, "converted": 0}
                source_performance[source]["count"] += 1
                if lead.get("temperature") == "hot":
                    source_performance[source]["hot_count"] += 1
                if lead.get("status") == "won":
                    source_performance[source]["converted"] += 1

            # Calculate source quality scores
            for source in source_performance:
                data = source_performance[source]
                total = data["count"]
                hot_rate = (data["hot_count"] / max(total, 1)) * 100
                conversion_rate = (data["converted"] / max(total, 1)) * 100
                quality_score = (hot_rate * 0.4) + (conversion_rate * 0.6)
                source_performance[source]["quality_score"] = round(quality_score, 2)
                source_performance[source]["hot_rate"] = round(hot_rate, 2)
                source_performance[source]["conversion_rate"] = round(conversion_rate, 2)

            # Geographic analysis
            zip_performance = {}
            for lead in leads:
                zip_code = lead.get("zip_code")
                if zip_code:
                    if zip_code not in zip_performance:
                        zip_performance[zip_code] = {"count": 0, "avg_property_value": 0}
                    zip_performance[zip_code]["count"] += 1
                    if lead.get("property_value"):
                        zip_performance[zip_code]["avg_property_value"] += lead["property_value"]

            # Calculate average property values by zip
            for zip_code in zip_performance:
                count = zip_performance[zip_code]["count"]
                if count > 0:
                    zip_performance[zip_code]["avg_property_value"] = round(
                        zip_performance[zip_code]["avg_property_value"] / count, 2
                    )

            # Lead velocity and trends
            prev_period_start = start_date - (end_date - start_date)
            prev_leads = (
                self.supabase.table("leads")
                .select("id")
                .gte("created_at", prev_period_start.isoformat())
                .lt("created_at", start_date.isoformat())
                .execute()
            )

            prev_count = len(prev_leads.data) if prev_leads.data else 0
            lead_velocity = ((total_leads - prev_count) / max(prev_count, 1)) * 100

            # Lead scoring analysis
            lead_scores = [l.get("lead_score", 0) for l in leads]
            avg_lead_score = statistics.mean(lead_scores) if lead_scores else 0
            high_score_leads = len([s for s in lead_scores if s >= 80])

            return {
                "totals": {
                    "total_leads": total_leads,
                    "hot_leads": hot_leads,
                    "warm_leads": warm_leads,
                    "cold_leads": cold_leads,
                    "high_value_leads": high_value_leads,
                    "insurance_leads": insurance_leads,
                    "urgent_leads": urgent_leads,
                },
                "quality": {
                    "avg_lead_score": round(avg_lead_score, 2),
                    "high_score_leads": high_score_leads,
                    "high_score_percentage": round(
                        (high_score_leads / max(total_leads, 1)) * 100, 2
                    ),
                    "hot_lead_percentage": round((hot_leads / max(total_leads, 1)) * 100, 2),
                },
                "response_performance": {
                    "avg_response_time_minutes": round(avg_response_time, 2),
                    "response_within_2min_count": response_within_2min,
                    "response_within_2min_rate": round(response_rate_2min, 2),
                    "benchmark_comparison": self._compare_to_benchmark(
                        avg_response_time, self.benchmarks.avg_response_time_minutes, "lower_better"
                    ),
                },
                "source_performance": source_performance,
                "geographic_analysis": zip_performance,
                "trends": {
                    "lead_velocity": round(lead_velocity, 2),
                    "daily_average": round(total_leads / max((end_date - start_date).days, 1), 2),
                    "growth_trend": (
                        "increasing"
                        if lead_velocity > 5
                        else "decreasing" if lead_velocity < -5 else "stable"
                    ),
                },
                "industry_context": {
                    "insurance_lead_percentage": round(
                        (insurance_leads / max(total_leads, 1)) * 100, 2
                    ),
                    "high_value_percentage": round(
                        (high_value_leads / max(total_leads, 1)) * 100, 2
                    ),
                    "urgent_percentage": round((urgent_leads / max(total_leads, 1)) * 100, 2),
                },
            }

        except Exception as e:
            logger.error(f"Error calculating enhanced lead metrics: {str(e)}")
            return {}

    def _calculate_enhanced_revenue_metrics(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Calculate enhanced revenue metrics with profitability analysis"""
        try:
            # Get projects with enhanced data
            projects_result = (
                self.supabase.table("projects")
                .select(
                    "id",
                    "created_at",
                    "quote_amount",
                    "final_amount",
                    "status",
                    "project_type",
                    "roof_material",
                    "roof_size_sqft",
                    "is_insurance_claim",
                    "completion_date",
                    "customer_id",
                    "city",
                    "state",
                )
                .gte("created_at", start_date.isoformat())
                .lte("created_at", end_date.isoformat())
                .execute()
            )

            projects = projects_result.data if projects_result.data else []

            # Revenue calculations
            total_quoted = sum(float(p.get("quote_amount", 0)) for p in projects)
            completed_projects = [p for p in projects if p.get("status") == "completed"]
            total_revenue = sum(float(p.get("final_amount", 0)) for p in completed_projects)

            # Pipeline analysis
            active_projects = [
                p for p in projects if p.get("status") in ["scheduled", "in_progress"]
            ]
            pipeline_value = sum(float(p.get("quote_amount", 0)) for p in active_projects)

            # Project type analysis
            revenue_by_type = {}
            projects_by_type = {}
            for project in completed_projects:
                ptype = project.get("project_type", "unknown")
                revenue = float(project.get("final_amount", 0))

                if ptype not in revenue_by_type:
                    revenue_by_type[ptype] = 0
                    projects_by_type[ptype] = 0

                revenue_by_type[ptype] += revenue
                projects_by_type[ptype] += 1

            # Calculate average project values by type
            avg_by_type = {}
            for ptype in revenue_by_type:
                if projects_by_type[ptype] > 0:
                    avg_by_type[ptype] = round(revenue_by_type[ptype] / projects_by_type[ptype], 2)

            # Insurance vs. retail analysis
            insurance_projects = [p for p in completed_projects if p.get("is_insurance_claim")]
            retail_projects = [p for p in completed_projects if not p.get("is_insurance_claim")]

            insurance_revenue = sum(float(p.get("final_amount", 0)) for p in insurance_projects)
            retail_revenue = sum(float(p.get("final_amount", 0)) for p in retail_projects)

            avg_insurance_value = (
                (insurance_revenue / max(len(insurance_projects), 1)) if insurance_projects else 0
            )
            avg_retail_value = (
                (retail_revenue / max(len(retail_projects), 1)) if retail_projects else 0
            )

            # Material analysis
            material_performance = {}
            for project in completed_projects:
                material = project.get("roof_material", "unknown")
                revenue = float(project.get("final_amount", 0))

                if material not in material_performance:
                    material_performance[material] = {"revenue": 0, "count": 0}

                material_performance[material]["revenue"] += revenue
                material_performance[material]["count"] += 1

            # Calculate material averages
            for material in material_performance:
                data = material_performance[material]
                data["avg_project_value"] = round(data["revenue"] / max(data["count"], 1), 2)

            # Growth analysis
            prev_period_start = start_date - (end_date - start_date)
            prev_projects = (
                self.supabase.table("projects")
                .select("final_amount")
                .eq("status", "completed")
                .gte("completion_date", prev_period_start.isoformat())
                .lt("completion_date", start_date.isoformat())
                .execute()
            )

            prev_revenue = sum(
                float(p.get("final_amount", 0))
                for p in (prev_projects.data if prev_projects.data else [])
            )
            revenue_growth = (
                ((total_revenue - prev_revenue) / max(prev_revenue, 1)) * 100 if prev_revenue else 0
            )

            # Project size analysis
            project_sizes = [
                float(p.get("final_amount", 0)) for p in completed_projects if p.get("final_amount")
            ]

            size_distribution = {
                "under_15k": len([s for s in project_sizes if s < 15000]),
                "15k_to_30k": len([s for s in project_sizes if 15000 <= s < 30000]),
                "30k_to_50k": len([s for s in project_sizes if 30000 <= s < 50000]),
                "50k_to_100k": len([s for s in project_sizes if 50000 <= s < 100000]),
                "over_100k": len([s for s in project_sizes if s >= 100000]),
            }

            # Performance metrics
            avg_deal_size = statistics.mean(project_sizes) if project_sizes else 0
            median_deal_size = statistics.median(project_sizes) if project_sizes else 0

            # Quote-to-close ratio
            quote_to_close_ratio = (len(completed_projects) / max(len(projects), 1)) * 100

            return {
                "revenue_summary": {
                    "total_quoted": round(total_quoted, 2),
                    "total_revenue": round(total_revenue, 2),
                    "pipeline_value": round(pipeline_value, 2),
                    "completed_projects": len(completed_projects),
                    "active_projects": len(active_projects),
                },
                "project_performance": {
                    "avg_deal_size": round(avg_deal_size, 2),
                    "median_deal_size": round(median_deal_size, 2),
                    "quote_to_close_ratio": round(quote_to_close_ratio, 2),
                    "benchmark_comparison": self._compare_to_benchmark(
                        avg_deal_size, self.benchmarks.avg_project_value, "higher_better"
                    ),
                },
                "revenue_by_type": revenue_by_type,
                "avg_by_type": avg_by_type,
                "projects_by_type": projects_by_type,
                "insurance_vs_retail": {
                    "insurance_revenue": round(insurance_revenue, 2),
                    "retail_revenue": round(retail_revenue, 2),
                    "insurance_projects": len(insurance_projects),
                    "retail_projects": len(retail_projects),
                    "avg_insurance_value": round(avg_insurance_value, 2),
                    "avg_retail_value": round(avg_retail_value, 2),
                    "insurance_percentage": round(
                        (len(insurance_projects) / max(len(completed_projects), 1)) * 100, 2
                    ),
                },
                "material_performance": material_performance,
                "size_distribution": size_distribution,
                "growth_metrics": {
                    "revenue_growth_percentage": round(revenue_growth, 2),
                    "growth_trend": (
                        "increasing"
                        if revenue_growth > 10
                        else "decreasing" if revenue_growth < -10 else "stable"
                    ),
                },
                "forecasting": {
                    "monthly_run_rate": round(
                        total_revenue / max((end_date - start_date).days / 30, 1), 2
                    ),
                    "projected_annual": round(
                        total_revenue * (365 / max((end_date - start_date).days, 1)), 2
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Error calculating enhanced revenue metrics: {str(e)}")
            return {}

    def _calculate_seasonal_metrics(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Calculate seasonal trends and patterns"""
        try:
            # Determine current season
            current_month = datetime.utcnow().month
            if current_month in [3, 4, 5]:
                season = "spring"
                seasonal_factor = self.weather_factors.spring_peak_factor
            elif current_month in [6, 7, 8]:
                season = "summer"
                seasonal_factor = self.weather_factors.summer_work_factor
            elif current_month in [9, 10, 11]:
                season = "fall"
                seasonal_factor = self.weather_factors.fall_rush_factor
            else:
                season = "winter"
                seasonal_factor = self.weather_factors.winter_emergency_factor

            # Get historical data for same period in previous years
            historical_data = []
            for year_offset in range(1, 4):  # Last 3 years
                hist_start = start_date.replace(year=start_date.year - year_offset)
                hist_end = end_date.replace(year=end_date.year - year_offset)

                hist_leads = (
                    self.supabase.table("leads")
                    .select("id")
                    .gte("created_at", hist_start.isoformat())
                    .lte("created_at", hist_end.isoformat())
                    .execute()
                )

                hist_projects = (
                    self.supabase.table("projects")
                    .select("final_amount")
                    .eq("status", "completed")
                    .gte("completion_date", hist_start.isoformat())
                    .lte("completion_date", hist_end.isoformat())
                    .execute()
                )

                hist_lead_count = len(hist_leads.data) if hist_leads.data else 0
                hist_revenue = sum(
                    float(p.get("final_amount", 0))
                    for p in (hist_projects.data if hist_projects.data else [])
                )

                historical_data.append(
                    {
                        "year": hist_start.year,
                        "leads": hist_lead_count,
                        "revenue": hist_revenue,
                    }
                )

            # Calculate seasonal averages
            if historical_data:
                avg_seasonal_leads = statistics.mean([d["leads"] for d in historical_data])
                avg_seasonal_revenue = statistics.mean([d["revenue"] for d in historical_data])
            else:
                avg_seasonal_leads = 0
                avg_seasonal_revenue = 0

            # Current period performance
            current_leads = (
                self.supabase.table("leads")
                .select("id")
                .gte("created_at", start_date.isoformat())
                .lte("created_at", end_date.isoformat())
                .execute()
            )

            current_projects = (
                self.supabase.table("projects")
                .select("final_amount")
                .eq("status", "completed")
                .gte("completion_date", start_date.isoformat())
                .lte("completion_date", end_date.isoformat())
                .execute()
            )

            current_lead_count = len(current_leads.data) if current_leads.data else 0
            current_revenue = sum(
                float(p.get("final_amount", 0))
                for p in (current_projects.data if current_projects.data else [])
            )

            # Calculate seasonal performance vs. historical
            seasonal_lead_performance = (
                (current_lead_count / max(avg_seasonal_leads, 1)) * 100 if avg_seasonal_leads else 0
            )
            seasonal_revenue_performance = (
                (current_revenue / max(avg_seasonal_revenue, 1)) * 100
                if avg_seasonal_revenue
                else 0
            )

            return {
                "current_season": season,
                "seasonal_factor": seasonal_factor,
                "historical_averages": {
                    "leads": round(avg_seasonal_leads, 2),
                    "revenue": round(avg_seasonal_revenue, 2),
                },
                "current_performance": {
                    "leads": current_lead_count,
                    "revenue": round(current_revenue, 2),
                },
                "seasonal_comparison": {
                    "lead_performance_vs_historical": round(seasonal_lead_performance, 2),
                    "revenue_performance_vs_historical": round(seasonal_revenue_performance, 2),
                },
                "historical_data": historical_data,
                "seasonality_insights": self._generate_seasonality_insights(
                    season, seasonal_lead_performance, seasonal_revenue_performance
                ),
            }

        except Exception as e:
            logger.error(f"Error calculating seasonal metrics: {str(e)}")
            return {}

    def _calculate_weather_impact_metrics(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Calculate weather impact on business performance"""
        try:
            # This would integrate with weather API in production
            # For now, we'll create a simplified analysis

            # Get leads with date correlation for weather analysis
            leads_by_day = {}
            current_date = start_date

            while current_date <= end_date:
                day_leads = (
                    self.supabase.table("leads")
                    .select("id", "urgency", "insurance_claim")
                    .gte("created_at", current_date.isoformat())
                    .lt("created_at", (current_date + timedelta(days=1)).isoformat())
                    .execute()
                )

                lead_count = len(day_leads.data) if day_leads.data else 0
                emergency_leads = len(
                    [l for l in (day_leads.data or []) if l.get("urgency") == "immediate"]
                )
                insurance_leads = len(
                    [l for l in (day_leads.data or []) if l.get("insurance_claim")]
                )

                leads_by_day[current_date.isoformat()[:10]] = {
                    "total_leads": lead_count,
                    "emergency_leads": emergency_leads,
                    "insurance_leads": insurance_leads,
                }

                current_date += timedelta(days=1)

            # Calculate weather impact indicators
            total_emergency_leads = sum(day["emergency_leads"] for day in leads_by_day.values())
            total_insurance_leads = sum(day["insurance_leads"] for day in leads_by_day.values())
            total_leads = sum(day["total_leads"] for day in leads_by_day.values())

            emergency_percentage = (total_emergency_leads / max(total_leads, 1)) * 100
            insurance_percentage = (total_insurance_leads / max(total_leads, 1)) * 100

            # Identify potential storm days (high emergency + insurance leads)
            potential_storm_days = []
            for date_str, data in leads_by_day.items():
                storm_indicator = data["emergency_leads"] + (data["insurance_leads"] * 2)
                if storm_indicator >= 3:  # Threshold for storm day
                    potential_storm_days.append(
                        {
                            "date": date_str,
                            "storm_indicator_score": storm_indicator,
                            "total_leads": data["total_leads"],
                            "emergency_leads": data["emergency_leads"],
                            "insurance_leads": data["insurance_leads"],
                        }
                    )

            return {
                "weather_indicators": {
                    "emergency_lead_percentage": round(emergency_percentage, 2),
                    "insurance_lead_percentage": round(insurance_percentage, 2),
                    "potential_storm_days": len(potential_storm_days),
                },
                "storm_impact_analysis": {
                    "storm_days_identified": potential_storm_days,
                    "avg_storm_day_leads": (
                        statistics.mean([d["total_leads"] for d in potential_storm_days])
                        if potential_storm_days
                        else 0
                    ),
                },
                "daily_breakdown": leads_by_day,
                "weather_recommendations": self._generate_weather_recommendations(
                    emergency_percentage, insurance_percentage
                ),
            }

        except Exception as e:
            logger.error(f"Error calculating weather impact metrics: {str(e)}")
            return {}

    def _calculate_business_health_score(
        self,
        lead_metrics: dict,
        revenue_metrics: dict,
        operational_metrics: dict,
        customer_metrics: dict,
    ) -> float:
        """Calculate overall business health score (0-100)"""
        try:
            components = []

            # Conversion rate component (25%)
            conv_rate = lead_metrics.get("quality", {}).get("hot_lead_percentage", 0)
            conv_score = min(100, (conv_rate / self.benchmarks.target_conversion_rate) * 100)
            components.append(conv_score * 0.25)

            # Response time component (20%)
            response_time = lead_metrics.get("response_performance", {}).get(
                "avg_response_time_minutes", 999
            )
            response_score = max(
                0, 100 - ((response_time - self.benchmarks.avg_response_time_minutes) * 2)
            )
            components.append(response_score * 0.20)

            # Revenue growth component (20%)
            revenue_growth = revenue_metrics.get("growth_metrics", {}).get(
                "revenue_growth_percentage", 0
            )
            growth_score = min(
                100, max(0, 50 + revenue_growth)
            )  # 0% growth = 50 points, +50% = 100 points
            components.append(growth_score * 0.20)

            # Deal size component (20%)
            avg_deal = revenue_metrics.get("project_performance", {}).get("avg_deal_size", 0)
            deal_score = min(100, (avg_deal / self.benchmarks.avg_project_value) * 100)
            components.append(deal_score * 0.20)

            # Operational efficiency component (15%)
            quote_to_close = revenue_metrics.get("project_performance", {}).get(
                "quote_to_close_ratio", 0
            )
            efficiency_score = min(100, quote_to_close * 4)  # 25% close rate = 100 points
            components.append(efficiency_score * 0.15)

            return round(sum(components), 2)

        except Exception as e:
            logger.error(f"Error calculating business health score: {str(e)}")
            return 0.0

    def _generate_business_insights(
        self,
        lead_metrics: dict,
        revenue_metrics: dict,
        operational_metrics: dict,
        customer_metrics: dict,
        seasonal_metrics: dict,
        weather_metrics: dict,
    ) -> list[dict]:
        """Generate actionable business insights"""
        insights = []

        try:
            # Lead response time insight
            avg_response = lead_metrics.get("response_performance", {}).get(
                "avg_response_time_minutes", 0
            )
            if avg_response > self.benchmarks.avg_response_time_minutes:
                insights.append(
                    {
                        "type": "improvement_opportunity",
                        "category": "lead_management",
                        "title": "Response Time Optimization",
                        "description": f"Average response time ({avg_response:.1f} min) exceeds industry benchmark ({self.benchmarks.avg_response_time_minutes} min)",
                        "impact": "high",
                        "recommendation": "Implement automated lead alerts and response tracking to achieve 2-minute response time target",
                        "potential_benefit": "Up to 78% increase in conversion rates with faster response times",
                    }
                )

            # Revenue opportunity insight
            avg_deal = revenue_metrics.get("project_performance", {}).get("avg_deal_size", 0)
            if avg_deal < self.benchmarks.premium_project_value:
                insights.append(
                    {
                        "type": "revenue_opportunity",
                        "category": "pricing",
                        "title": "Premium Market Opportunity",
                        "description": f"Average deal size (${avg_deal:,.0f}) indicates opportunity for premium market penetration",
                        "impact": "high",
                        "recommendation": "Focus on properties valued >$500K and implement premium service packages",
                        "potential_benefit": f"Target ${self.benchmarks.premium_project_value:,.0f} average project value",
                    }
                )

            # Seasonal insight
            seasonal_performance = seasonal_metrics.get("seasonal_comparison", {}).get(
                "lead_performance_vs_historical", 0
            )
            current_season = seasonal_metrics.get("current_season", "")
            if seasonal_performance < 90:  # Below 90% of historical performance
                insights.append(
                    {
                        "type": "seasonal_alert",
                        "category": "marketing",
                        "title": f"{current_season.title()} Performance Below Historical Average",
                        "description": f"Current {current_season} performance is {seasonal_performance:.1f}% of historical average",
                        "impact": "medium",
                        "recommendation": f"Increase marketing efforts and adjust for {current_season} seasonal patterns",
                        "potential_benefit": "Alignment with historical seasonal performance patterns",
                    }
                )

            # Weather impact insight
            emergency_percentage = weather_metrics.get("weather_indicators", {}).get(
                "emergency_lead_percentage", 0
            )
            if emergency_percentage > 15:  # High emergency leads indicate storm activity
                insights.append(
                    {
                        "type": "opportunity",
                        "category": "storm_response",
                        "title": "Storm Response Opportunity",
                        "description": f"High emergency leads ({emergency_percentage:.1f}%) indicate storm activity",
                        "impact": "high",
                        "recommendation": "Activate storm response protocol and emergency inspection teams",
                        "potential_benefit": "Capture increased demand from weather-related damage",
                    }
                )

            # Insurance claim insight
            insurance_percentage = revenue_metrics.get("insurance_vs_retail", {}).get(
                "insurance_percentage", 0
            )
            if insurance_percentage < 30:  # Low insurance work
                insights.append(
                    {
                        "type": "business_development",
                        "category": "partnerships",
                        "title": "Insurance Partnership Opportunity",
                        "description": f"Insurance claims represent only {insurance_percentage:.1f}% of projects",
                        "impact": "medium",
                        "recommendation": "Develop stronger relationships with insurance adjusters and agents",
                        "potential_benefit": "Insurance claims typically have higher success rates and faster decisions",
                    }
                )

            return insights

        except Exception as e:
            logger.error(f"Error generating business insights: {str(e)}")
            return []

    def _generate_intelligent_alerts(
        self, lead_metrics: dict, revenue_metrics: dict, operational_metrics: dict
    ) -> list[dict]:
        """Generate intelligent business alerts"""
        alerts = []

        try:
            # Critical response time alert
            avg_response = lead_metrics.get("response_performance", {}).get(
                "avg_response_time_minutes", 0
            )
            if avg_response > 30:  # Critical threshold
                alerts.append(
                    {
                        "level": "critical",
                        "type": "response_time",
                        "title": "Critical Response Time Alert",
                        "message": f"Average response time ({avg_response:.1f} minutes) is critically high",
                        "action_required": "Immediate attention needed for lead response process",
                        "impact": "Significant lead conversion loss",
                    }
                )

            # Revenue trend alert
            revenue_growth = revenue_metrics.get("growth_metrics", {}).get(
                "revenue_growth_percentage", 0
            )
            if revenue_growth < -20:  # 20% decline
                alerts.append(
                    {
                        "level": "warning",
                        "type": "revenue_decline",
                        "title": "Revenue Decline Alert",
                        "message": f"Revenue declined {abs(revenue_growth):.1f}% compared to previous period",
                        "action_required": "Review marketing and sales processes",
                        "impact": "Business growth and profitability concern",
                    }
                )

            # Lead quality alert
            hot_percentage = lead_metrics.get("quality", {}).get("hot_lead_percentage", 0)
            if hot_percentage < 10:  # Low hot lead percentage
                alerts.append(
                    {
                        "level": "warning",
                        "type": "lead_quality",
                        "title": "Lead Quality Alert",
                        "message": f"Only {hot_percentage:.1f}% of leads are classified as hot",
                        "action_required": "Review lead scoring and qualification criteria",
                        "impact": "Lower conversion rates and longer sales cycles",
                    }
                )

            return alerts

        except Exception as e:
            logger.error(f"Error generating intelligent alerts: {str(e)}")
            return []

    # Enhanced Forecasting

    def enhanced_revenue_forecast(self, months_ahead: int = 6) -> dict[str, Any]:
        """
        Enhanced revenue forecasting with seasonal adjustments and weather factors
        """
        try:
            cache_key = f"enhanced_analytics:revenue_forecast:{months_ahead}"
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data

            # Get 24 months of historical data for better forecasting
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=730)  # 24 months

            # Collect monthly revenue data
            monthly_data = []
            current_date = start_date

            while current_date < end_date:
                month_end = current_date + timedelta(days=30)

                projects = (
                    self.supabase.table("projects")
                    .select("final_amount", "completion_date")
                    .eq("status", "completed")
                    .gte("completion_date", current_date.isoformat())
                    .lt("completion_date", month_end.isoformat())
                    .execute()
                )

                month_revenue = sum(
                    float(p.get("final_amount", 0))
                    for p in (projects.data if projects.data else [])
                )

                monthly_data.append(
                    {
                        "date": current_date,
                        "revenue": month_revenue,
                        "month": current_date.month,
                    }
                )

                current_date = month_end

            if len(monthly_data) < 6:
                return {"error": "Insufficient historical data for enhanced forecasting"}

            # Create DataFrame for analysis
            df = pd.DataFrame(monthly_data)
            df["month_num"] = range(len(df))

            # Calculate seasonal factors
            seasonal_factors = {}
            for month in range(1, 13):
                month_revenues = [d["revenue"] for d in monthly_data if d["month"] == month]
                if month_revenues:
                    seasonal_factors[month] = statistics.mean(month_revenues)
                else:
                    seasonal_factors[month] = 0

            avg_monthly_revenue = (
                statistics.mean(seasonal_factors.values()) if seasonal_factors.values() else 0
            )

            # Normalize seasonal factors
            for month in seasonal_factors:
                if avg_monthly_revenue > 0:
                    seasonal_factors[month] = seasonal_factors[month] / avg_monthly_revenue
                else:
                    seasonal_factors[month] = 1.0

            # Fit trend model
            X = np.array(df["month_num"]).reshape(-1, 1)
            y = np.array(df["revenue"])

            model = LinearRegression()
            model.fit(X, y)

            # Generate forecasts
            forecasts = []
            base_month_num = len(monthly_data)

            for i in range(1, months_ahead + 1):
                forecast_month_num = base_month_num + i
                forecast_date = end_date + timedelta(days=30 * i)
                forecast_month = forecast_date.month

                # Base forecast from trend
                base_forecast = model.predict([[forecast_month_num]])[0]

                # Apply seasonal adjustment
                seasonal_factor = seasonal_factors.get(forecast_month, 1.0)
                seasonal_forecast = base_forecast * seasonal_factor

                # Apply weather/industry factors
                weather_factor = self._get_weather_factor_for_month(forecast_month)
                final_forecast = seasonal_forecast * weather_factor

                # Calculate confidence intervals
                recent_errors = []
                for j in range(max(0, len(monthly_data) - 6), len(monthly_data)):
                    predicted = model.predict([[j]])[0]
                    actual = monthly_data[j]["revenue"]
                    recent_errors.append(abs(predicted - actual))

                std_error = statistics.stdev(recent_errors) if len(recent_errors) > 1 else 0

                forecasts.append(
                    {
                        "month": i,
                        "date": forecast_date.strftime("%Y-%m"),
                        "forecast": round(max(0, final_forecast), 2),
                        "base_trend": round(base_forecast, 2),
                        "seasonal_factor": round(seasonal_factor, 3),
                        "weather_factor": round(weather_factor, 3),
                        "confidence_interval": {
                            "lower": round(max(0, final_forecast - (1.96 * std_error)), 2),
                            "upper": round(final_forecast + (1.96 * std_error), 2),
                        },
                    }
                )

            # Calculate forecast accuracy metrics
            if len(monthly_data) >= 12:
                # Test on last 6 months
                test_data = monthly_data[-6:]
                train_data = monthly_data[:-6]

                # Retrain on subset
                train_df = pd.DataFrame(train_data)
                train_X = np.array(range(len(train_data))).reshape(-1, 1)
                train_y = np.array([d["revenue"] for d in train_data])

                test_model = LinearRegression()
                test_model.fit(train_X, train_y)

                # Predict test period
                predictions = []
                actuals = []
                for j, test_point in enumerate(test_data):
                    pred = test_model.predict([[len(train_data) + j]])[0]
                    predictions.append(pred)
                    actuals.append(test_point["revenue"])

                mae = mean_absolute_error(actuals, predictions)
                rmse = np.sqrt(mean_squared_error(actuals, predictions))

                accuracy_metrics = {
                    "mae": round(mae, 2),
                    "rmse": round(rmse, 2),
                    "mape": round(
                        np.mean(
                            np.abs(
                                (np.array(actuals) - np.array(predictions))
                                / np.maximum(np.array(actuals), 1)
                            )
                        )
                        * 100,
                        2,
                    ),
                }
            else:
                accuracy_metrics = {"note": "Insufficient data for accuracy validation"}

            result = {
                "forecasts": forecasts,
                "historical_data": [
                    {"date": d["date"].strftime("%Y-%m"), "revenue": d["revenue"]}
                    for d in monthly_data[-12:]
                ],
                "seasonal_factors": seasonal_factors,
                "trend_analysis": {
                    "slope": round(model.coef_[0], 2),
                    "intercept": round(model.intercept_, 2),
                    "direction": "increasing" if model.coef_[0] > 0 else "decreasing",
                },
                "accuracy_metrics": accuracy_metrics,
                "total_forecast": round(sum(f["forecast"] for f in forecasts), 2),
                "confidence_level": 95,
                "methodology": "Linear regression with seasonal and weather adjustments",
            }

            # Cache for 2 hours
            self._cache_data(cache_key, result, self.cache_ttl["forecasts"])

            return result

        except Exception as e:
            logger.error(f"Error in enhanced revenue forecast: {str(e)}")
            return {"error": str(e)}

    def _get_weather_factor_for_month(self, month: int) -> float:
        """Get weather adjustment factor for a given month"""
        if month in [3, 4, 5]:  # Spring - peak roofing season
            return self.weather_factors.spring_peak_factor
        elif month in [6, 7, 8]:  # Summer - ideal work conditions
            return self.weather_factors.summer_work_factor
        elif month in [9, 10, 11]:  # Fall - last chance before winter
            return self.weather_factors.fall_rush_factor
        else:  # Winter - emergency work only
            return self.weather_factors.winter_emergency_factor

    # Helper Methods

    def _get_date_range(self, timeframe: AnalyticsTimeframe) -> tuple[datetime, datetime]:
        """Get start and end dates for a timeframe"""
        now = datetime.utcnow()

        if timeframe == AnalyticsTimeframe.DAILY:
            start = now.replace(hour=0, minute=0, second=0)
            end = now
        elif timeframe == AnalyticsTimeframe.WEEKLY:
            start = now - timedelta(days=7)
            end = now
        elif timeframe == AnalyticsTimeframe.MONTHLY:
            start = now - timedelta(days=30)
            end = now
        elif timeframe == AnalyticsTimeframe.QUARTERLY:
            start = now - timedelta(days=90)
            end = now
        elif timeframe == AnalyticsTimeframe.YEARLY:
            start = now - timedelta(days=365)
            end = now
        elif timeframe == AnalyticsTimeframe.MTD:
            start = now.replace(day=1, hour=0, minute=0, second=0)
            end = now
        elif timeframe == AnalyticsTimeframe.QTD:
            quarter = (now.month - 1) // 3
            start = now.replace(month=quarter * 3 + 1, day=1, hour=0, minute=0, second=0)
            end = now
        elif timeframe == AnalyticsTimeframe.YTD:
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0)
            end = now
        else:
            start = now - timedelta(days=30)
            end = now

        return start, end

    def _compare_to_benchmark(
        self, value: float, benchmark: float, direction: str
    ) -> dict[str, Any]:
        """Compare a value to industry benchmark"""
        if direction == "higher_better":
            percentage = (value / max(benchmark, 1)) * 100
            status = (
                "excellent"
                if percentage >= 120
                else "good" if percentage >= 100 else "below_target"
            )
        else:  # lower_better
            percentage = (benchmark / max(value, 1)) * 100
            status = (
                "excellent"
                if percentage >= 120
                else "good" if percentage >= 100 else "needs_improvement"
            )

        return {
            "value": round(value, 2),
            "benchmark": round(benchmark, 2),
            "percentage_of_benchmark": round(percentage, 2),
            "status": status,
            "variance": round(value - benchmark, 2),
        }

    def _get_industry_benchmarks(self) -> dict[str, Any]:
        """Get roofing industry benchmarks for comparison"""
        return {
            "response_time_minutes": self.benchmarks.avg_response_time_minutes,
            "conversion_rate_percentage": self.benchmarks.target_conversion_rate,
            "avg_project_value": self.benchmarks.avg_project_value,
            "premium_project_value": self.benchmarks.premium_project_value,
            "gross_margin_percentage": self.benchmarks.target_gross_margin,
            "customer_satisfaction": self.benchmarks.target_customer_satisfaction,
            "nps_score": self.benchmarks.target_nps_score,
            "appointment_show_rate": self.benchmarks.target_appointment_show_rate,
        }

    def _generate_seasonality_insights(
        self, season: str, lead_performance: float, revenue_performance: float
    ) -> list[str]:
        """Generate insights based on seasonal performance"""
        insights = []

        if season == "spring" and lead_performance < 90:
            insights.append(
                "Spring is peak roofing season - consider increasing marketing investment"
            )

        if season == "summer" and revenue_performance < 85:
            insights.append("Summer offers optimal work conditions - focus on project completion")

        if season == "fall" and lead_performance > 110:
            insights.append("Strong fall performance indicates good winter preparation opportunity")

        if season == "winter" and lead_performance > 80:
            insights.append(
                "Above-average winter lead generation suggests emergency/insurance opportunities"
            )

        return insights

    def _generate_weather_recommendations(
        self, emergency_percentage: float, insurance_percentage: float
    ) -> list[str]:
        """Generate weather-based business recommendations"""
        recommendations = []

        if emergency_percentage > 20:
            recommendations.append("High emergency leads - activate storm response protocol")
            recommendations.append("Consider expanding emergency inspection capacity")

        if insurance_percentage > 40:
            recommendations.append("Strong insurance activity - prioritize adjuster relationships")
            recommendations.append("Focus on insurance claim documentation and support")

        if emergency_percentage < 5 and insurance_percentage < 10:
            recommendations.append("Low weather-related activity - focus on proactive marketing")
            recommendations.append("Good time for maintenance and improvement projects")

        return recommendations

    def _get_cached_data(self, key: str) -> dict | None:
        """Get data from Redis cache"""
        try:
            if self.redis_client:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
        except Exception as e:
            logger.error(f"Error getting cached data: {str(e)}")
        return None

    def _cache_data(self, key: str, data: dict, ttl: int):
        """Cache data in Redis"""
        try:
            if self.redis_client:
                self.redis_client.setex(key, ttl, json.dumps(data, default=str))
        except Exception as e:
            logger.error(f"Error caching data: {str(e)}")

    def _broadcast_enhanced_metrics_update(self, metrics: dict):
        """Broadcast enhanced metrics update via Pusher"""
        try:
            if self.pusher_service.is_available():
                self.pusher_service.trigger(
                    "enhanced-analytics",
                    "metrics:update",
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "business_health_score": metrics.get("period_summary", {}).get(
                            "business_health_score"
                        ),
                        "key_metrics": {
                            "total_leads": metrics.get("leads", {})
                            .get("totals", {})
                            .get("total_leads", 0),
                            "total_revenue": metrics.get("revenue", {})
                            .get("revenue_summary", {})
                            .get("total_revenue", 0),
                            "conversion_rate": metrics.get("leads", {})
                            .get("quality", {})
                            .get("hot_lead_percentage", 0),
                        },
                        "alerts_count": len(metrics.get("alerts", [])),
                    },
                )
                logger.info("Broadcasting enhanced metrics update via Pusher")
        except Exception as e:
            logger.error(f"Error broadcasting enhanced metrics: {str(e)}")


# Create singleton instance
enhanced_analytics_service = EnhancedAnalyticsService()
