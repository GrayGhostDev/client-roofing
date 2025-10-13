"""
Advanced Analytics Engine for ML Predictions

Provides sophisticated analytics capabilities including:
- Revenue forecasting with confidence intervals
- Lead quality heatmaps by segment
- Conversion funnel analysis
- Customer lifetime value distributions
- Churn risk scoring
- Marketing channel attribution
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.lead_sqlalchemy import Lead
from app.models.project_sqlalchemy import Project
from app.models.customer_sqlalchemy import Customer
from app.models.interaction_sqlalchemy import Interaction
from app.database import get_db


class AdvancedAnalytics:
    """Advanced analytics engine for business intelligence."""

    def __init__(self, db: Session):
        self.db = db

    async def get_revenue_forecast(
        self,
        days_ahead: int = 30,
        confidence_level: float = 0.95
    ) -> Dict:
        """
        Generate revenue forecast using historical data and trends.

        Args:
            days_ahead: Number of days to forecast
            confidence_level: Confidence interval (0.0-1.0)

        Returns:
            Dict with forecast data including confidence intervals
        """
        # Get historical revenue data (last 90 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)

        # Query daily revenue
        daily_revenue = (
            self.db.query(
                func.date(Project.created_at).label('date'),
                func.sum(Project.final_amount).label('revenue'),
                func.count(Project.id).label('count')
            )
            .filter(
                and_(
                    Project.created_at >= start_date,
                    Project.created_at <= end_date,
                    Project.status.in_(['completed', 'in_progress']),
                    Project.final_amount.isnot(None)
                )
            )
            .group_by(func.date(Project.created_at))
            .order_by(func.date(Project.created_at))
            .all()
        )

        # Convert to pandas for time series analysis (extract only date and revenue)
        df = pd.DataFrame([(row[0], row[1]) for row in daily_revenue], columns=['date', 'revenue'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')

        # Fill missing dates with 0 revenue
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        df = df.reindex(date_range, fill_value=0)

        # Calculate trend using moving average
        df['ma_7'] = df['revenue'].rolling(window=7).mean()
        df['ma_30'] = df['revenue'].rolling(window=30).mean()

        # Simple linear regression for trend
        X = np.arange(len(df)).reshape(-1, 1)
        y = df['revenue'].values

        # Calculate trend line
        from sklearn.linear_model import LinearRegression
        model = LinearRegression()
        model.fit(X, y)

        # Forecast future values
        future_X = np.arange(len(df), len(df) + days_ahead).reshape(-1, 1)
        forecast = model.predict(future_X)

        # Calculate confidence intervals based on historical variance
        residuals = y - model.predict(X)
        std_error = np.std(residuals)
        z_score = 1.96 if confidence_level == 0.95 else 2.576  # 95% or 99%

        confidence_interval = z_score * std_error

        # Generate forecast dates
        forecast_dates = pd.date_range(
            start=end_date + timedelta(days=1),
            periods=days_ahead,
            freq='D'
        )

        # Build forecast response
        forecast_data = []
        for i, date in enumerate(forecast_dates):
            forecast_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'predicted_revenue': max(0, float(forecast[i])),
                'lower_bound': max(0, float(forecast[i] - confidence_interval)),
                'upper_bound': float(forecast[i] + confidence_interval),
                'confidence_level': confidence_level
            })

        # Calculate summary statistics
        total_forecast = sum(f['predicted_revenue'] for f in forecast_data)
        avg_daily = total_forecast / days_ahead

        # Historical average for comparison
        historical_avg = float(df['revenue'].mean())
        growth_rate = ((avg_daily - historical_avg) / historical_avg * 100) if historical_avg > 0 else 0

        return {
            'forecast': forecast_data,
            'summary': {
                'total_forecast_revenue': round(total_forecast, 2),
                'average_daily_revenue': round(avg_daily, 2),
                'historical_average': round(historical_avg, 2),
                'growth_rate_percent': round(growth_rate, 2),
                'confidence_level': confidence_level,
                'forecast_period_days': days_ahead
            },
            'metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'historical_days': 90,
                'model_type': 'linear_regression',
                'data_points': len(df)
            }
        }

    async def get_lead_quality_heatmap(
        self,
        segment_by: str = 'source'
    ) -> Dict:
        """
        Generate lead quality heatmap by various segments.

        Args:
            segment_by: Segmentation dimension (source, zip_code, property_value)

        Returns:
            Dict with heatmap data
        """
        # Query leads with conversion status
        leads_query = (
            self.db.query(Lead)
            .filter(Lead.created_at >= datetime.utcnow() - timedelta(days=90))
        )

        leads = leads_query.all()

        if not leads:
            return {
                'heatmap': [],
                'summary': {
                    'total_leads': 0,
                    'segments': 0
                }
            }

        # Convert to DataFrame for analysis
        df = pd.DataFrame([{
            'id': lead.id,
            'source': lead.source or 'unknown',
            'zip_code': lead.zip_code or 'unknown',
            'property_value': self._categorize_property_value(lead.property_value or 0),
            'lead_quality': lead.lead_score or 50,  # Use lead_score as quality metric (0-100)
            'status': lead.status,
            'converted': 1 if lead.status in ['qualified', 'quote_sent', 'won'] else 0
        } for lead in leads])

        # Group by segment
        if segment_by not in df.columns:
            segment_by = 'source'

        # Calculate quality metrics by segment
        heatmap_data = []
        segments = df[segment_by].unique()

        for segment in segments:
            segment_df = df[df[segment_by] == segment]

            total_leads = len(segment_df)
            converted_leads = segment_df['converted'].sum()
            conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
            avg_quality = segment_df['lead_quality'].mean()

            # Quality score (0-100)
            quality_score = (conversion_rate * 0.7 + avg_quality * 0.3)

            heatmap_data.append({
                'segment': str(segment),
                'total_leads': int(total_leads),
                'converted_leads': int(converted_leads),
                'conversion_rate': round(conversion_rate, 2),
                'avg_lead_quality': round(avg_quality, 2),
                'quality_score': round(quality_score, 2),
                'quality_tier': self._get_quality_tier(quality_score)
            })

        # Sort by quality score
        heatmap_data.sort(key=lambda x: x['quality_score'], reverse=True)

        return {
            'heatmap': heatmap_data,
            'summary': {
                'total_leads': len(df),
                'segments': len(segments),
                'segment_by': segment_by,
                'best_segment': heatmap_data[0]['segment'] if heatmap_data else None,
                'worst_segment': heatmap_data[-1]['segment'] if heatmap_data else None
            },
            'metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'period_days': 90
            }
        }

    async def get_conversion_funnel(self) -> Dict:
        """
        Generate conversion funnel analytics showing drop-off at each stage.

        Returns:
            Dict with funnel data and conversion rates
        """
        # Define funnel stages
        stages = [
            ('new', 'New Lead'),
            ('contacted', 'Contacted'),
            ('qualified', 'Qualified'),
            ('quote_sent', 'Quote Sent'),
            ('negotiation', 'Negotiation'),
            ('won', 'Won')
        ]

        # Get leads in last 90 days
        start_date = datetime.utcnow() - timedelta(days=90)

        funnel_data = []
        previous_count = None

        for stage_key, stage_name in stages:
            count = (
                self.db.query(func.count(Lead.id))
                .filter(
                    and_(
                        Lead.created_at >= start_date,
                        Lead.status == stage_key
                    )
                )
                .scalar()
            )

            # For later stages, also count leads that progressed past this stage
            if stage_key != 'new':
                progressed_count = (
                    self.db.query(func.count(Lead.id))
                    .filter(
                        and_(
                            Lead.created_at >= start_date,
                            Lead.status.in_([s[0] for s in stages if stages.index((s[0], s[1])) > stages.index((stage_key, stage_name))])
                        )
                    )
                    .scalar()
                )
                count += progressed_count

            # Calculate conversion rate
            conversion_rate = (count / previous_count * 100) if previous_count else 100
            drop_off = previous_count - count if previous_count else 0
            drop_off_rate = (drop_off / previous_count * 100) if previous_count else 0

            funnel_data.append({
                'stage': stage_name,
                'stage_key': stage_key,
                'count': int(count),
                'conversion_rate': round(conversion_rate, 2),
                'drop_off': int(drop_off),
                'drop_off_rate': round(drop_off_rate, 2)
            })

            previous_count = count

        # Calculate overall metrics
        total_leads = funnel_data[0]['count'] if funnel_data else 0
        won_leads = funnel_data[-1]['count'] if funnel_data else 0
        overall_conversion = (won_leads / total_leads * 100) if total_leads > 0 else 0

        return {
            'funnel': funnel_data,
            'summary': {
                'total_leads': total_leads,
                'won_leads': won_leads,
                'overall_conversion_rate': round(overall_conversion, 2),
                'biggest_drop_off_stage': max(funnel_data, key=lambda x: x['drop_off_rate'])['stage'] if funnel_data else None
            },
            'metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'period_days': 90
            }
        }

    async def get_clv_distribution(self) -> Dict:
        """
        Calculate customer lifetime value distribution across segments.

        Returns:
            Dict with CLV distribution data
        """
        # Get all customers with completed projects
        customers = (
            self.db.query(Customer)
            .join(Project, Customer.id == Project.customer_id)
            .filter(Project.status == 'completed')
            .all()
        )

        if not customers:
            return {
                'distribution': [],
                'summary': {
                    'total_customers': 0,
                    'avg_clv': 0
                }
            }

        # Calculate CLV for each customer
        clv_data = []
        for customer in customers:
            # Sum all project values
            total_value = (
                self.db.query(func.sum(Project.final_amount))
                .filter(
                    and_(
                        Project.customer_id == customer.id,
                        Project.status == 'completed',
                        Project.final_amount.isnot(None)
                    )
                )
                .scalar() or 0
            )

            # Count projects
            project_count = (
                self.db.query(func.count(Project.id))
                .filter(
                    and_(
                        Project.customer_id == customer.id,
                        Project.status == 'completed'
                    )
                )
                .scalar() or 0
            )

            clv_data.append({
                'customer_id': customer.id,
                'total_value': float(total_value),
                'project_count': int(project_count),
                'avg_project_value': float(total_value / project_count) if project_count > 0 else 0
            })

        # Create distribution buckets
        clv_values = [c['total_value'] for c in clv_data]

        buckets = [
            (0, 10000, '$0-10K'),
            (10000, 25000, '$10K-25K'),
            (25000, 45000, '$25K-45K'),
            (45000, 75000, '$45K-75K'),
            (75000, float('inf'), '$75K+')
        ]

        distribution = []
        for min_val, max_val, label in buckets:
            count = sum(1 for v in clv_values if min_val <= v < max_val)
            percentage = (count / len(clv_values) * 100) if clv_values else 0

            distribution.append({
                'bucket': label,
                'min_value': min_val,
                'max_value': max_val if max_val != float('inf') else None,
                'customer_count': count,
                'percentage': round(percentage, 2)
            })

        # Calculate summary statistics
        avg_clv = np.mean(clv_values) if clv_values else 0
        median_clv = np.median(clv_values) if clv_values else 0
        top_10_percent = np.percentile(clv_values, 90) if clv_values else 0

        return {
            'distribution': distribution,
            'summary': {
                'total_customers': len(customers),
                'avg_clv': round(avg_clv, 2),
                'median_clv': round(median_clv, 2),
                'top_10_percent_threshold': round(top_10_percent, 2),
                'highest_clv': round(max(clv_values), 2) if clv_values else 0
            },
            'metadata': {
                'generated_at': datetime.utcnow().isoformat()
            }
        }

    async def get_churn_risk_analysis(self) -> Dict:
        """
        Analyze churn risk for existing customers.

        Returns:
            Dict with churn risk scores and predictions
        """
        # Get active customers (with projects in last 3 years)
        three_years_ago = datetime.utcnow() - timedelta(days=1095)

        customers = (
            self.db.query(Customer)
            .join(Project, Customer.id == Project.customer_id)
            .filter(Project.created_at >= three_years_ago)
            .distinct()
            .all()
        )

        churn_analysis = []

        for customer in customers:
            # Get customer's project history
            projects = (
                self.db.query(Project)
                .filter(Project.customer_id == customer.id)
                .order_by(Project.created_at.desc())
                .all()
            )

            if not projects:
                continue

            # Calculate churn indicators
            last_project_date = projects[0].created_at
            days_since_last = (datetime.utcnow() - last_project_date).days
            project_count = len(projects)

            # Average time between projects
            if project_count > 1:
                project_dates = [p.created_at for p in projects]
                intervals = [(project_dates[i] - project_dates[i+1]).days
                           for i in range(len(project_dates)-1)]
                avg_interval = np.mean(intervals)
            else:
                avg_interval = 365  # Assume yearly if only one project

            # Churn risk score (0-100, higher = more risk)
            # Based on: time since last project vs average interval
            risk_multiplier = days_since_last / avg_interval if avg_interval > 0 else 1
            churn_risk = min(100, risk_multiplier * 50)

            # Risk category
            if churn_risk >= 75:
                risk_category = 'high'
            elif churn_risk >= 50:
                risk_category = 'medium'
            else:
                risk_category = 'low'

            churn_analysis.append({
                'customer_id': customer.id,
                'customer_name': f"{customer.first_name} {customer.last_name}",
                'days_since_last_project': days_since_last,
                'project_count': project_count,
                'avg_days_between_projects': round(avg_interval, 0),
                'churn_risk_score': round(churn_risk, 2),
                'risk_category': risk_category,
                'recommended_action': self._get_churn_action(risk_category)
            })

        # Sort by risk score (highest first)
        churn_analysis.sort(key=lambda x: x['churn_risk_score'], reverse=True)

        # Calculate summary
        high_risk = sum(1 for c in churn_analysis if c['risk_category'] == 'high')
        medium_risk = sum(1 for c in churn_analysis if c['risk_category'] == 'medium')
        low_risk = sum(1 for c in churn_analysis if c['risk_category'] == 'low')

        return {
            'churn_analysis': churn_analysis[:50],  # Top 50 at-risk customers
            'summary': {
                'total_customers': len(churn_analysis),
                'high_risk_count': high_risk,
                'medium_risk_count': medium_risk,
                'low_risk_count': low_risk,
                'high_risk_percentage': round(high_risk / len(churn_analysis) * 100, 2) if churn_analysis else 0
            },
            'metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'analysis_period_days': 1095
            }
        }

    async def get_marketing_attribution(self) -> Dict:
        """
        Analyze marketing channel attribution and effectiveness.

        Returns:
            Dict with attribution data by channel
        """
        # Get leads from last 90 days
        start_date = datetime.utcnow() - timedelta(days=90)

        leads = (
            self.db.query(Lead)
            .filter(Lead.created_at >= start_date)
            .all()
        )

        if not leads:
            return {
                'attribution': [],
                'summary': {
                    'total_leads': 0,
                    'total_channels': 0
                }
            }

        # Group by source (channel)
        df = pd.DataFrame([{
            'source': lead.source or 'unknown',
            'status': lead.status,
            'converted': 1 if lead.status in ['won'] else 0,
            'estimated_value': lead.property_value or 0
        } for lead in leads])

        attribution = []

        for source in df['source'].unique():
            source_df = df[df['source'] == source]

            total_leads = len(source_df)
            converted = source_df['converted'].sum()
            conversion_rate = (converted / total_leads * 100) if total_leads > 0 else 0

            # Estimated revenue from this channel
            estimated_revenue = source_df[source_df['converted'] == 1]['estimated_value'].sum()

            attribution.append({
                'channel': str(source),
                'total_leads': int(total_leads),
                'converted_leads': int(converted),
                'conversion_rate': round(conversion_rate, 2),
                'estimated_revenue': round(float(estimated_revenue), 2),
                'revenue_per_lead': round(float(estimated_revenue / total_leads), 2) if total_leads > 0 else 0,
                'effectiveness_score': round(conversion_rate * (estimated_revenue / 1000), 2)
            })

        # Sort by effectiveness score
        attribution.sort(key=lambda x: x['effectiveness_score'], reverse=True)

        return {
            'attribution': attribution,
            'summary': {
                'total_leads': len(df),
                'total_channels': len(attribution),
                'best_channel': attribution[0]['channel'] if attribution else None,
                'total_estimated_revenue': round(sum(a['estimated_revenue'] for a in attribution), 2)
            },
            'metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'period_days': 90
            }
        }

    # Helper methods
    def _categorize_property_value(self, value: float) -> str:
        """Categorize property value into tiers."""
        if value >= 500000:
            return 'premium_500k+'
        elif value >= 350000:
            return 'upper_350k-500k'
        elif value >= 250000:
            return 'mid_250k-350k'
        elif value >= 150000:
            return 'entry_150k-250k'
        else:
            return 'basic_<150k'

    def _get_quality_tier(self, score: float) -> str:
        """Get quality tier from score."""
        if score >= 80:
            return 'excellent'
        elif score >= 60:
            return 'good'
        elif score >= 40:
            return 'fair'
        else:
            return 'poor'

    def _get_churn_action(self, risk_category: str) -> str:
        """Get recommended action for churn risk."""
        actions = {
            'high': 'Immediate outreach - offer maintenance package or discount',
            'medium': 'Schedule check-in call within 2 weeks',
            'low': 'Add to quarterly newsletter and monitoring list'
        }
        return actions.get(risk_category, 'Monitor')
