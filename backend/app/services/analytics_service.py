"""
Analytics Service for iSwitch Roofs CRM
Version: 1.0.0
Date: 2025-01-04

Comprehensive analytics engine with KPI calculations, forecasting,
and real-time metrics broadcasting via Pusher.

Features:
- Real-time KPI calculations with caching
- Revenue forecasting with time-series analysis
- Lead funnel analytics
- Team performance scoring
- Customer lifetime value (LTV) calculations
- Conversion rate optimization metrics
- Pusher integration for live dashboard updates
"""

import os
import logging
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import statistics
from decimal import Decimal
import hashlib

# Data analysis
import numpy as np
from scipy import stats

# Caching
import redis
from functools import lru_cache

# Database
from app.config import get_supabase_client, get_redis_client

# Real-time updates
from app.utils.pusher_client import get_pusher_service

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Metric type enumeration"""
    LEADS = "leads"
    REVENUE = "revenue"
    CONVERSION = "conversion"
    PERFORMANCE = "performance"
    CUSTOMER = "customer"
    OPERATIONAL = "operational"


class TimeFrame(str, Enum):
    """Time frame enumeration for analytics"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    MTD = "month_to_date"
    QTD = "quarter_to_date"
    YTD = "year_to_date"


class AnalyticsService:
    """
    Service for calculating and broadcasting analytics metrics.

    Provides comprehensive KPI calculations, forecasting, and real-time
    updates via Pusher for dashboard synchronization.
    """

    def __init__(self):
        """Initialize analytics service"""
        self._supabase = None
        self._redis = None
        self._pusher = None

        # Cache configuration
        self.cache_ttl = {
            'realtime': 30,      # 30 seconds for real-time metrics
            'standard': 300,     # 5 minutes for standard metrics
            'historical': 3600,  # 1 hour for historical data
        }

        # KPI thresholds and targets
        self.kpi_targets = {
            'lead_response_time': 120,  # 2 minutes
            'conversion_rate': 25.0,    # 25%
            'avg_deal_size': 45000,     # $45k
            'customer_satisfaction': 4.5, # 4.5 stars
            'monthly_revenue': 1000000,  # $1M
            'lead_velocity': 10,         # 10% growth
        }

        # Scoring weights for performance calculations
        self.performance_weights = {
            'conversion_rate': 0.3,
            'response_time': 0.2,
            'deal_value': 0.2,
            'activity_level': 0.15,
            'customer_satisfaction': 0.15,
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

    def calculate_kpis(self, timeframe: TimeFrame = TimeFrame.MTD) -> Dict[str, Any]:
        """
        Calculate all key performance indicators

        Args:
            timeframe: Time period for calculations

        Returns:
            Dictionary of KPI metrics
        """
        try:
            # Check cache first
            cache_key = f"analytics:kpis:{timeframe}"
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data

            # Get date range
            start_date, end_date = self._get_date_range(timeframe)

            # Calculate individual KPI categories
            lead_metrics = self._calculate_lead_metrics(start_date, end_date)
            revenue_metrics = self._calculate_revenue_metrics(start_date, end_date)
            conversion_metrics = self._calculate_conversion_metrics(start_date, end_date)
            operational_metrics = self._calculate_operational_metrics(start_date, end_date)
            customer_metrics = self._calculate_customer_metrics(start_date, end_date)

            # Combine all metrics
            kpis = {
                'timestamp': datetime.utcnow().isoformat(),
                'timeframe': timeframe,
                'leads': lead_metrics,
                'revenue': revenue_metrics,
                'conversion': conversion_metrics,
                'operational': operational_metrics,
                'customers': customer_metrics,
                'summary': self._calculate_summary_metrics(
                    lead_metrics, revenue_metrics, conversion_metrics
                ),
            }

            # Cache the results
            self._cache_data(cache_key, kpis, self.cache_ttl['standard'])

            # Broadcast real-time update
            self._broadcast_metrics_update(kpis)

            return kpis

        except Exception as e:
            logger.error(f"Error calculating KPIs: {str(e)}")
            return {}

    def _calculate_lead_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate lead-related metrics"""
        try:
            # Get leads for period
            leads_result = self.supabase.table('leads').select(
                'id', 'created_at', 'temperature', 'lead_score', 'source',
                'assigned_to', 'status', 'response_time_minutes'
            ).gte('created_at', start_date.isoformat()).lte('created_at', end_date.isoformat()).execute()

            leads = leads_result.data if leads_result.data else []

            # Calculate metrics
            total_leads = len(leads)
            hot_leads = len([l for l in leads if l.get('temperature') == 'hot'])
            warm_leads = len([l for l in leads if l.get('temperature') == 'warm'])
            cold_leads = len([l for l in leads if l.get('temperature') == 'cold'])

            # Average response time
            response_times = [l['response_time_minutes'] for l in leads if l.get('response_time_minutes')]
            avg_response_time = statistics.mean(response_times) if response_times else 0

            # Lead sources distribution
            sources = {}
            for lead in leads:
                source = lead.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1

            # Lead velocity (growth rate)
            prev_start = start_date - (end_date - start_date)
            prev_leads = self.supabase.table('leads').select('id').gte('created_at', prev_start.isoformat()).lt('created_at', start_date.isoformat()).execute()

            prev_count = len(prev_leads.data) if prev_leads.data else 0
            lead_velocity = ((total_leads - prev_count) / max(prev_count, 1)) * 100 if prev_count else 0

            # Average lead score
            lead_scores = [l.get('lead_score', 0) for l in leads]
            avg_lead_score = statistics.mean(lead_scores) if lead_scores else 0

            return {
                'total': total_leads,
                'hot': hot_leads,
                'warm': warm_leads,
                'cold': cold_leads,
                'avg_response_time': round(avg_response_time, 2),
                'avg_lead_score': round(avg_lead_score, 2),
                'lead_velocity': round(lead_velocity, 2),
                'sources': sources,
                'daily_average': round(total_leads / max((end_date - start_date).days, 1), 2),
            }

        except Exception as e:
            logger.error(f"Error calculating lead metrics: {str(e)}")
            return {}

    def _calculate_revenue_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate revenue-related metrics"""
        try:
            # Get projects for period
            projects_result = self.supabase.table('projects').select(
                'id', 'created_at', 'quoted_amount', 'actual_amount',
                'status', 'project_type', 'margin_percentage'
            ).gte('created_at', start_date.isoformat()).lte('created_at', end_date.isoformat()).execute()

            projects = projects_result.data if projects_result.data else []

            # Revenue calculations
            total_quoted = sum(float(p.get('quoted_amount', 0)) for p in projects)
            total_actual = sum(float(p.get('actual_amount', 0)) for p in projects if p.get('status') == 'completed')

            # Pipeline value (in progress projects)
            pipeline_value = sum(
                float(p.get('quoted_amount', 0))
                for p in projects
                if p.get('status') in ['approved', 'in_progress']
            )

            # Average deal size
            completed_projects = [p for p in projects if p.get('status') == 'completed']
            avg_deal_size = (
                statistics.mean([float(p.get('actual_amount', 0)) for p in completed_projects])
                if completed_projects else 0
            )

            # Margin analysis
            margins = [
                float(p.get('margin_percentage', 0))
                for p in completed_projects
                if p.get('margin_percentage')
            ]
            avg_margin = statistics.mean(margins) if margins else 0

            # Revenue forecast (simple linear projection)
            days_elapsed = (datetime.utcnow() - start_date).days
            days_in_period = (end_date - start_date).days
            if days_elapsed > 0:
                daily_revenue = total_actual / days_elapsed
                projected_revenue = daily_revenue * days_in_period
            else:
                projected_revenue = 0

            # Revenue by project type
            revenue_by_type = {}
            for p in completed_projects:
                ptype = p.get('project_type', 'unknown')
                revenue_by_type[ptype] = revenue_by_type.get(ptype, 0) + float(p.get('actual_amount', 0))

            return {
                'total_quoted': round(total_quoted, 2),
                'total_actual': round(total_actual, 2),
                'pipeline_value': round(pipeline_value, 2),
                'avg_deal_size': round(avg_deal_size, 2),
                'avg_margin': round(avg_margin, 2),
                'projected_revenue': round(projected_revenue, 2),
                'revenue_by_type': revenue_by_type,
                'total_projects': len(projects),
                'completed_projects': len(completed_projects),
            }

        except Exception as e:
            logger.error(f"Error calculating revenue metrics: {str(e)}")
            return {}

    def _calculate_conversion_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate conversion funnel metrics"""
        try:
            # Get leads and their outcomes
            leads_result = self.supabase.table('leads').select(
                'id', 'created_at', 'status', 'converted_to_customer_at',
                'temperature', 'source'
            ).gte('created_at', start_date.isoformat()).lte('created_at', end_date.isoformat()).execute()

            leads = leads_result.data if leads_result.data else []

            # Conversion counts
            total_leads = len(leads)
            qualified_leads = len([l for l in leads if l.get('status') in ['qualified', 'converted']])
            converted_leads = len([l for l in leads if l.get('status') == 'converted'])

            # Conversion rates
            qualification_rate = (qualified_leads / max(total_leads, 1)) * 100
            conversion_rate = (converted_leads / max(total_leads, 1)) * 100
            qualified_to_customer = (converted_leads / max(qualified_leads, 1)) * 100

            # Conversion by temperature
            conversion_by_temp = {}
            for temp in ['hot', 'warm', 'cold']:
                temp_leads = [l for l in leads if l.get('temperature') == temp]
                temp_converted = [l for l in temp_leads if l.get('status') == 'converted']
                conversion_by_temp[temp] = round(
                    (len(temp_converted) / max(len(temp_leads), 1)) * 100, 2
                )

            # Conversion by source
            conversion_by_source = {}
            sources = set(l.get('source', 'unknown') for l in leads)
            for source in sources:
                source_leads = [l for l in leads if l.get('source') == source]
                source_converted = [l for l in source_leads if l.get('status') == 'converted']
                conversion_by_source[source] = {
                    'rate': round((len(source_converted) / max(len(source_leads), 1)) * 100, 2),
                    'count': len(source_converted),
                }

            # Average conversion time
            conversion_times = []
            for lead in leads:
                if lead.get('converted_to_customer_at'):
                    created = datetime.fromisoformat(lead['created_at'])
                    converted = datetime.fromisoformat(lead['converted_to_customer_at'])
                    days = (converted - created).days
                    conversion_times.append(days)

            avg_conversion_time = statistics.mean(conversion_times) if conversion_times else 0

            return {
                'total_leads': total_leads,
                'qualified_leads': qualified_leads,
                'converted_leads': converted_leads,
                'qualification_rate': round(qualification_rate, 2),
                'conversion_rate': round(conversion_rate, 2),
                'qualified_to_customer': round(qualified_to_customer, 2),
                'conversion_by_temperature': conversion_by_temp,
                'conversion_by_source': conversion_by_source,
                'avg_conversion_days': round(avg_conversion_time, 2),
            }

        except Exception as e:
            logger.error(f"Error calculating conversion metrics: {str(e)}")
            return {}

    def _calculate_operational_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate operational efficiency metrics"""
        try:
            # Get appointments
            appointments_result = self.supabase.table('appointments').select(
                'id', 'status', 'scheduled_start', 'appointment_type'
            ).gte('scheduled_start', start_date.isoformat()).lte('scheduled_start', end_date.isoformat()).execute()

            appointments = appointments_result.data if appointments_result.data else []

            # Appointment metrics
            total_appointments = len(appointments)
            completed_appointments = len([a for a in appointments if a.get('status') == 'completed'])
            cancelled_appointments = len([a for a in appointments if a.get('status') == 'cancelled'])
            no_show_appointments = len([a for a in appointments if a.get('status') == 'no_show'])

            appointment_completion_rate = (completed_appointments / max(total_appointments, 1)) * 100

            # Get interactions
            interactions_result = self.supabase.table('interactions').select(
                'id', 'interaction_type', 'created_at'
            ).gte('created_at', start_date.isoformat()).lte('created_at', end_date.isoformat()).execute()

            interactions = interactions_result.data if interactions_result.data else []

            # Interaction breakdown
            interaction_types = {}
            for interaction in interactions:
                itype = interaction.get('interaction_type', 'unknown')
                interaction_types[itype] = interaction_types.get(itype, 0) + 1

            # Activity rate (interactions per day)
            days_in_period = max((end_date - start_date).days, 1)
            daily_activity_rate = len(interactions) / days_in_period

            # Team productivity (get team metrics)
            team_result = self.supabase.table('team_members').select(
                'id', 'name', 'role'
            ).execute()

            team_members = team_result.data if team_result.data else []
            active_team_members = len(team_members)

            # Average activities per team member
            avg_activities_per_member = len(interactions) / max(active_team_members, 1)

            return {
                'total_appointments': total_appointments,
                'appointment_completion_rate': round(appointment_completion_rate, 2),
                'cancelled_appointments': cancelled_appointments,
                'no_show_rate': round((no_show_appointments / max(total_appointments, 1)) * 100, 2),
                'total_interactions': len(interactions),
                'interaction_types': interaction_types,
                'daily_activity_rate': round(daily_activity_rate, 2),
                'active_team_members': active_team_members,
                'avg_activities_per_member': round(avg_activities_per_member, 2),
            }

        except Exception as e:
            logger.error(f"Error calculating operational metrics: {str(e)}")
            return {}

    def _calculate_customer_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate customer-related metrics"""
        try:
            # Get customers created in period
            customers_result = self.supabase.table('customers').select(
                'id', 'created_at', 'lifetime_value', 'referral_source'
            ).gte('created_at', start_date.isoformat()).lte('created_at', end_date.isoformat()).execute()

            customers = customers_result.data if customers_result.data else []
            new_customers = len(customers)

            # Get all customers for total count
            all_customers = self.supabase.table('customers').select('id').execute()
            total_customers = len(all_customers.data) if all_customers.data else 0

            # Customer lifetime value
            ltv_values = [float(c.get('lifetime_value', 0)) for c in customers if c.get('lifetime_value')]
            avg_ltv = statistics.mean(ltv_values) if ltv_values else 0

            # Referral analysis
            referral_sources = {}
            for customer in customers:
                source = customer.get('referral_source', 'direct')
                referral_sources[source] = referral_sources.get(source, 0) + 1

            # Get reviews
            reviews_result = self.supabase.table('reviews').select(
                'id', 'rating', 'created_at'
            ).gte('created_at', start_date.isoformat()).lte('created_at', end_date.isoformat()).execute()

            reviews = reviews_result.data if reviews_result.data else []

            # Review metrics
            ratings = [r.get('rating', 0) for r in reviews]
            avg_rating = statistics.mean(ratings) if ratings else 0

            # Net Promoter Score (simplified)
            promoters = len([r for r in reviews if r.get('rating', 0) >= 4])
            detractors = len([r for r in reviews if r.get('rating', 0) <= 2])
            nps = ((promoters - detractors) / max(len(reviews), 1)) * 100 if reviews else 0

            # Customer acquisition cost (CAC) - simplified
            # Would need marketing spend data for accurate CAC
            estimated_cac = 500  # Placeholder value

            return {
                'new_customers': new_customers,
                'total_customers': total_customers,
                'avg_lifetime_value': round(avg_ltv, 2),
                'referral_sources': referral_sources,
                'total_reviews': len(reviews),
                'avg_rating': round(avg_rating, 2),
                'net_promoter_score': round(nps, 2),
                'customer_acquisition_cost': estimated_cac,
                'ltv_to_cac_ratio': round(avg_ltv / max(estimated_cac, 1), 2) if avg_ltv else 0,
            }

        except Exception as e:
            logger.error(f"Error calculating customer metrics: {str(e)}")
            return {}

    def _calculate_summary_metrics(self, leads: Dict, revenue: Dict, conversion: Dict) -> Dict:
        """Calculate summary KPIs and health scores"""
        try:
            # Overall health score (0-100)
            health_components = []

            # Lead response time component
            avg_response = leads.get('avg_response_time', 0)
            response_score = max(0, 100 - (avg_response - self.kpi_targets['lead_response_time']))
            health_components.append(response_score * 0.2)

            # Conversion rate component
            conv_rate = conversion.get('conversion_rate', 0)
            conv_target = self.kpi_targets['conversion_rate']
            conv_score = min(100, (conv_rate / conv_target) * 100)
            health_components.append(conv_score * 0.3)

            # Revenue component
            actual_revenue = revenue.get('total_actual', 0)
            revenue_target = self.kpi_targets['monthly_revenue']
            revenue_score = min(100, (actual_revenue / revenue_target) * 100)
            health_components.append(revenue_score * 0.3)

            # Deal size component
            avg_deal = revenue.get('avg_deal_size', 0)
            deal_target = self.kpi_targets['avg_deal_size']
            deal_score = min(100, (avg_deal / deal_target) * 100)
            health_components.append(deal_score * 0.2)

            overall_health = sum(health_components)

            # Trend analysis
            lead_velocity = leads.get('lead_velocity', 0)
            growth_trend = 'increasing' if lead_velocity > 5 else 'decreasing' if lead_velocity < -5 else 'stable'

            return {
                'overall_health_score': round(overall_health, 2),
                'growth_trend': growth_trend,
                'lead_velocity': lead_velocity,
                'conversion_efficiency': round(conv_rate, 2),
                'revenue_achievement': round((actual_revenue / revenue_target) * 100, 2),
                'key_alerts': self._generate_alerts(leads, revenue, conversion),
            }

        except Exception as e:
            logger.error(f"Error calculating summary metrics: {str(e)}")
            return {}

    def _generate_alerts(self, leads: Dict, revenue: Dict, conversion: Dict) -> List[Dict]:
        """Generate alerts based on KPI thresholds"""
        alerts = []

        # Check lead response time
        if leads.get('avg_response_time', 0) > self.kpi_targets['lead_response_time']:
            alerts.append({
                'type': 'warning',
                'metric': 'response_time',
                'message': f"Average response time ({leads['avg_response_time']} min) exceeds target ({self.kpi_targets['lead_response_time']} min)",
            })

        # Check conversion rate
        if conversion.get('conversion_rate', 0) < self.kpi_targets['conversion_rate']:
            alerts.append({
                'type': 'warning',
                'metric': 'conversion_rate',
                'message': f"Conversion rate ({conversion['conversion_rate']}%) below target ({self.kpi_targets['conversion_rate']}%)",
            })

        # Check revenue
        if revenue.get('total_actual', 0) < revenue.get('projected_revenue', 0) * 0.8:
            alerts.append({
                'type': 'alert',
                'metric': 'revenue',
                'message': "Actual revenue tracking 20% below projection",
            })

        return alerts

    def calculate_team_performance(self, team_member_id: str, timeframe: TimeFrame = TimeFrame.MTD) -> Dict:
        """
        Calculate individual team member performance metrics

        Args:
            team_member_id: Team member ID
            timeframe: Time period for calculations

        Returns:
            Performance metrics dictionary
        """
        try:
            start_date, end_date = self._get_date_range(timeframe)

            # Get team member's leads
            leads_result = self.supabase.table('leads').select(
                'id', 'status', 'response_time_minutes', 'lead_score'
            ).eq('assigned_to', team_member_id).gte('created_at', start_date.isoformat()).lte('created_at', end_date.isoformat()).execute()

            leads = leads_result.data if leads_result.data else []

            # Calculate conversion metrics
            total_leads = len(leads)
            converted_leads = len([l for l in leads if l.get('status') == 'converted'])
            conversion_rate = (converted_leads / max(total_leads, 1)) * 100

            # Average response time
            response_times = [l['response_time_minutes'] for l in leads if l.get('response_time_minutes')]
            avg_response_time = statistics.mean(response_times) if response_times else 0

            # Get projects
            projects_result = self.supabase.table('projects').select(
                'id', 'quoted_amount', 'actual_amount', 'status'
            ).eq('sales_rep_id', team_member_id).gte('created_at', start_date.isoformat()).lte('created_at', end_date.isoformat()).execute()

            projects = projects_result.data if projects_result.data else []

            # Revenue metrics
            total_quoted = sum(float(p.get('quoted_amount', 0)) for p in projects)
            total_closed = sum(
                float(p.get('actual_amount', 0))
                for p in projects
                if p.get('status') == 'completed'
            )

            # Get activities
            interactions_result = self.supabase.table('interactions').select(
                'id', 'interaction_type'
            ).eq('team_member_id', team_member_id).gte('created_at', start_date.isoformat()).lte('created_at', end_date.isoformat()).execute()

            total_activities = len(interactions_result.data) if interactions_result.data else 0

            # Calculate performance score
            performance_score = self._calculate_performance_score({
                'conversion_rate': conversion_rate,
                'avg_response_time': avg_response_time,
                'total_revenue': total_closed,
                'total_activities': total_activities,
            })

            return {
                'team_member_id': team_member_id,
                'timeframe': timeframe,
                'leads': {
                    'total': total_leads,
                    'converted': converted_leads,
                    'conversion_rate': round(conversion_rate, 2),
                    'avg_response_time': round(avg_response_time, 2),
                },
                'revenue': {
                    'total_quoted': round(total_quoted, 2),
                    'total_closed': round(total_closed, 2),
                    'avg_deal_size': round(total_closed / max(converted_leads, 1), 2),
                },
                'activities': {
                    'total': total_activities,
                    'daily_average': round(total_activities / max((end_date - start_date).days, 1), 2),
                },
                'performance_score': round(performance_score, 2),
                'rank': self._get_team_member_rank(team_member_id, performance_score),
            }

        except Exception as e:
            logger.error(f"Error calculating team performance: {str(e)}")
            return {}

    def _calculate_performance_score(self, metrics: Dict) -> float:
        """Calculate weighted performance score"""
        score = 0

        # Conversion rate component (0-30 points)
        conv_rate = metrics.get('conversion_rate', 0)
        conv_score = min(30, (conv_rate / self.kpi_targets['conversion_rate']) * 30)
        score += conv_score

        # Response time component (0-20 points)
        response_time = metrics.get('avg_response_time', 999)
        response_score = max(0, 20 - ((response_time - self.kpi_targets['lead_response_time']) / 10))
        score += response_score

        # Revenue component (0-30 points)
        revenue = metrics.get('total_revenue', 0)
        revenue_score = min(30, (revenue / 100000) * 30)  # Scale to 100k baseline
        score += revenue_score

        # Activity component (0-20 points)
        activities = metrics.get('total_activities', 0)
        activity_score = min(20, (activities / 100) * 20)  # Scale to 100 activities baseline
        score += activity_score

        return min(100, score)

    def _get_team_member_rank(self, team_member_id: str, score: float) -> int:
        """Get team member rank based on performance score"""
        # This would compare against other team members
        # For now, return a placeholder
        return 1

    def forecast_revenue(self, months_ahead: int = 3) -> Dict:
        """
        Forecast revenue using time-series analysis

        Args:
            months_ahead: Number of months to forecast

        Returns:
            Forecast data with predictions and confidence intervals
        """
        try:
            # Get historical revenue data (last 12 months)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=365)

            # Get monthly revenue data
            monthly_revenue = []
            current_date = start_date

            while current_date < end_date:
                month_end = current_date + timedelta(days=30)

                projects = self.supabase.table('projects').select(
                    'actual_amount'
                ).eq('status', 'completed').gte('completed_at', current_date.isoformat()).lt('completed_at', month_end.isoformat()).execute()

                month_revenue = sum(
                    float(p.get('actual_amount', 0))
                    for p in (projects.data if projects.data else [])
                )
                monthly_revenue.append(month_revenue)
                current_date = month_end

            # Simple linear regression for forecasting
            if len(monthly_revenue) >= 3:
                x = np.arange(len(monthly_revenue))
                y = np.array(monthly_revenue)

                # Calculate trend
                slope, intercept = np.polyfit(x, y, 1)

                # Generate forecasts
                forecasts = []
                for i in range(1, months_ahead + 1):
                    forecast_x = len(monthly_revenue) + i
                    forecast_value = slope * forecast_x + intercept

                    # Add some uncertainty (simplified)
                    std_dev = np.std(y)
                    confidence_interval = std_dev * 1.96  # 95% confidence

                    forecasts.append({
                        'month': i,
                        'forecast': round(max(0, forecast_value), 2),
                        'lower_bound': round(max(0, forecast_value - confidence_interval), 2),
                        'upper_bound': round(forecast_value + confidence_interval, 2),
                    })

                # Calculate growth rate
                growth_rate = (slope / np.mean(y)) * 100 if np.mean(y) > 0 else 0

                return {
                    'historical_data': monthly_revenue[-6:],  # Last 6 months
                    'forecasts': forecasts,
                    'trend': 'increasing' if slope > 0 else 'decreasing',
                    'growth_rate': round(growth_rate, 2),
                    'confidence_level': 95,
                }
            else:
                return {
                    'error': 'Insufficient historical data for forecasting',
                    'historical_data': monthly_revenue,
                }

        except Exception as e:
            logger.error(f"Error forecasting revenue: {str(e)}")
            return {'error': str(e)}

    def get_lead_funnel(self, timeframe: TimeFrame = TimeFrame.MTD) -> Dict:
        """
        Get lead funnel analytics

        Args:
            timeframe: Time period for analysis

        Returns:
            Funnel metrics with conversion rates between stages
        """
        try:
            start_date, end_date = self._get_date_range(timeframe)

            # Get all leads in timeframe
            leads = self.supabase.table('leads').select(
                'id', 'status', 'created_at', 'temperature'
            ).gte('created_at', start_date.isoformat()).lte('created_at', end_date.isoformat()).execute()

            leads_data = leads.data if leads.data else []

            # Define funnel stages
            funnel_stages = {
                'new': 0,
                'contacted': 0,
                'qualified': 0,
                'proposal': 0,
                'negotiation': 0,
                'converted': 0,
            }

            # Count leads in each stage
            for lead in leads_data:
                status = lead.get('status', 'new')
                if status in funnel_stages:
                    funnel_stages[status] += 1

            # Calculate conversion rates between stages
            stage_order = ['new', 'contacted', 'qualified', 'proposal', 'negotiation', 'converted']
            conversions = {}

            for i in range(len(stage_order) - 1):
                from_stage = stage_order[i]
                to_stage = stage_order[i + 1]

                from_count = funnel_stages[from_stage]
                to_count = funnel_stages[to_stage]

                conversion_rate = (to_count / max(from_count, 1)) * 100
                conversions[f"{from_stage}_to_{to_stage}"] = round(conversion_rate, 2)

            # Overall conversion rate
            overall_conversion = (funnel_stages['converted'] / max(funnel_stages['new'], 1)) * 100

            # Breakdown by temperature
            temperature_breakdown = {}
            for temp in ['hot', 'warm', 'cold']:
                temp_leads = [l for l in leads_data if l.get('temperature') == temp]
                temp_converted = [l for l in temp_leads if l.get('status') == 'converted']
                temperature_breakdown[temp] = {
                    'total': len(temp_leads),
                    'converted': len(temp_converted),
                    'rate': round((len(temp_converted) / max(len(temp_leads), 1)) * 100, 2),
                }

            return {
                'timeframe': timeframe,
                'stages': funnel_stages,
                'conversions': conversions,
                'overall_conversion_rate': round(overall_conversion, 2),
                'temperature_breakdown': temperature_breakdown,
                'total_leads': len(leads_data),
                'bottlenecks': self._identify_bottlenecks(conversions),
            }

        except Exception as e:
            logger.error(f"Error getting lead funnel: {str(e)}")
            return {}

    def _identify_bottlenecks(self, conversions: Dict) -> List[str]:
        """Identify bottlenecks in the conversion funnel"""
        bottlenecks = []

        for stage, rate in conversions.items():
            if rate < 50:  # Less than 50% conversion is considered a bottleneck
                bottlenecks.append({
                    'stage': stage.replace('_to_', ' → '),
                    'conversion_rate': rate,
                    'severity': 'high' if rate < 25 else 'medium',
                })

        return bottlenecks

    def get_realtime_metrics(self) -> Dict:
        """
        Get real-time metrics for dashboard

        Returns:
            Current real-time metrics
        """
        try:
            # Check cache for real-time data
            cache_key = "analytics:realtime"
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data

            # Get current day metrics
            today = datetime.utcnow().replace(hour=0, minute=0, second=0)

            # Today's leads
            leads_today = self.supabase.table('leads').select('id').gte('created_at', today.isoformat()).execute()

            # Today's revenue
            projects_today = self.supabase.table('projects').select('quoted_amount').gte('created_at', today.isoformat()).execute()

            revenue_today = sum(
                float(p.get('quoted_amount', 0))
                for p in (projects_today.data if projects_today.data else [])
            )

            # Active users (from team activity)
            active_users = self.supabase.table('team_members').select('id').eq('is_active', True).execute()

            # Current appointments
            appointments_today = self.supabase.table('appointments').select('id').gte('scheduled_start', today.isoformat()).lt('scheduled_start', (today + timedelta(days=1)).isoformat()).execute()

            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'leads_today': len(leads_today.data) if leads_today.data else 0,
                'revenue_today': round(revenue_today, 2),
                'active_users': len(active_users.data) if active_users.data else 0,
                'appointments_today': len(appointments_today.data) if appointments_today.data else 0,
                'current_time': datetime.utcnow().strftime('%I:%M %p'),
            }

            # Cache for 30 seconds
            self._cache_data(cache_key, metrics, self.cache_ttl['realtime'])

            # Broadcast update
            self._broadcast_realtime_update(metrics)

            return metrics

        except Exception as e:
            logger.error(f"Error getting realtime metrics: {str(e)}")
            return {}

    def _get_date_range(self, timeframe: TimeFrame) -> Tuple[datetime, datetime]:
        """Get start and end dates for a timeframe"""
        now = datetime.utcnow()

        if timeframe == TimeFrame.DAILY:
            start = now.replace(hour=0, minute=0, second=0)
            end = now
        elif timeframe == TimeFrame.WEEKLY:
            start = now - timedelta(days=7)
            end = now
        elif timeframe == TimeFrame.MONTHLY:
            start = now - timedelta(days=30)
            end = now
        elif timeframe == TimeFrame.QUARTERLY:
            start = now - timedelta(days=90)
            end = now
        elif timeframe == TimeFrame.YEARLY:
            start = now - timedelta(days=365)
            end = now
        elif timeframe == TimeFrame.MTD:
            start = now.replace(day=1, hour=0, minute=0, second=0)
            end = now
        elif timeframe == TimeFrame.QTD:
            quarter = (now.month - 1) // 3
            start = now.replace(month=quarter * 3 + 1, day=1, hour=0, minute=0, second=0)
            end = now
        elif timeframe == TimeFrame.YTD:
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0)
            end = now
        else:
            start = now - timedelta(days=30)
            end = now

        return start, end

    def _get_cached_data(self, key: str) -> Optional[Dict]:
        """Get data from Redis cache"""
        try:
            if self.redis_client:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
        except Exception as e:
            logger.error(f"Error getting cached data: {str(e)}")
        return None

    def _cache_data(self, key: str, data: Dict, ttl: int):
        """Cache data in Redis"""
        try:
            if self.redis_client:
                self.redis_client.setex(key, ttl, json.dumps(data))
        except Exception as e:
            logger.error(f"Error caching data: {str(e)}")

    def _broadcast_metrics_update(self, metrics: Dict):
        """Broadcast metrics update via Pusher"""
        try:
            if self.pusher_service.is_available():
                self.pusher_service.broadcast_metrics_update(metrics)
                logger.info("Broadcasting metrics update via Pusher")
        except Exception as e:
            logger.error(f"Error broadcasting metrics: {str(e)}")

    def _broadcast_realtime_update(self, metrics: Dict):
        """Broadcast real-time metrics via Pusher"""
        try:
            if self.pusher_service.is_available():
                self.pusher_service.trigger(
                    'analytics',
                    'realtime:update',
                    metrics
                )
                logger.info("Broadcasting realtime update via Pusher")
        except Exception as e:
            logger.error(f"Error broadcasting realtime update: {str(e)}")


# Create singleton instance
analytics_service = AnalyticsService()