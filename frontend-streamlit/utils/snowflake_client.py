"""
Snowflake Integration for iSwitch Roofs CRM
Provides seamless connection to Snowflake data warehouse for analytics and reporting
Version: 1.0.0
"""

import streamlit as st
from typing import Optional, Dict, List, Any
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SnowflakeClient:
    """
    Client for Snowflake data warehouse operations
    Handles connections, queries, and data transformations
    """

    def __init__(self):
        """Initialize Snowflake client with session context"""
        self.session = None
        self._connect()

    def _connect(self):
        """Establish connection to Snowflake"""
        try:
            from snowflake.snowpark.context import get_active_session
            self.session = get_active_session()
            logger.info("Successfully connected to Snowflake")
        except Exception as e:
            # Silently fail - Snowflake is optional, show info instead of error
            logger.info("Snowflake not available - using fallback mode")
            # Note: No st.warning here to avoid cluttering UI when Snowflake isn't configured
            self.session = None

    def is_connected(self) -> bool:
        """Check if Snowflake connection is active"""
        return self.session is not None

    def execute_query(self, query: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """
        Execute SQL query and return results as pandas DataFrame

        Args:
            query: SQL query to execute
            params: Optional parameters for parameterized queries

        Returns:
            pd.DataFrame: Query results
        """
        if not self.is_connected():
            logger.warning("Snowflake not connected - returning empty DataFrame")
            return pd.DataFrame()

        try:
            if params:
                # Use parameterized query if params provided
                result = self.session.sql(query, params=params)
            else:
                result = self.session.sql(query)

            return result.to_pandas()
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            st.error(f"Database query error: {str(e)}")
            return pd.DataFrame()

    def create_dataframe(self, data: List[List], schema: List[str]) -> pd.DataFrame:
        """
        Create Snowflake dataframe from data and schema

        Args:
            data: List of rows
            schema: List of column names

        Returns:
            pd.DataFrame: Created dataframe
        """
        if not self.is_connected():
            # Fallback to pandas
            return pd.DataFrame(data, columns=schema)

        try:
            snowflake_df = self.session.create_dataframe(data, schema=schema)
            return snowflake_df.to_pandas()
        except Exception as e:
            logger.error(f"Failed to create dataframe: {str(e)}")
            return pd.DataFrame(data, columns=schema)

    # ========================================================================
    # CRM DATA QUERIES
    # ========================================================================

    def get_leads_summary(self, timeframe: str = 'month') -> pd.DataFrame:
        """
        Get lead summary statistics

        Args:
            timeframe: 'day', 'week', 'month', 'quarter', 'year'

        Returns:
            pd.DataFrame: Lead summary data
        """
        query = """
        SELECT
            status,
            COUNT(*) as count,
            AVG(value) as avg_value,
            SUM(value) as total_value
        FROM leads
        WHERE created_at >= DATEADD(?, -1, CURRENT_DATE())
        GROUP BY status
        ORDER BY count DESC
        """
        return self.execute_query(query, params={'timeframe': timeframe})

    def get_customer_metrics(self) -> pd.DataFrame:
        """Get customer metrics and segmentation"""
        query = """
        SELECT
            tier,
            COUNT(*) as customer_count,
            AVG(lifetime_value) as avg_ltv,
            SUM(lifetime_value) as total_ltv,
            COUNT(CASE WHEN last_contact > DATEADD(month, -1, CURRENT_DATE())
                  THEN 1 END) as active_last_month
        FROM customers
        GROUP BY tier
        ORDER BY avg_ltv DESC
        """
        return self.execute_query(query)

    def get_project_pipeline(self) -> pd.DataFrame:
        """Get project pipeline analysis"""
        query = """
        SELECT
            status,
            COUNT(*) as project_count,
            SUM(value) as total_value,
            AVG(value) as avg_value,
            MIN(start_date) as earliest_start,
            MAX(end_date) as latest_end
        FROM projects
        WHERE status IN ('planned', 'in_progress', 'on_hold')
        GROUP BY status
        ORDER BY
            CASE status
                WHEN 'in_progress' THEN 1
                WHEN 'planned' THEN 2
                WHEN 'on_hold' THEN 3
            END
        """
        return self.execute_query(query)

    def get_revenue_trends(self, months: int = 12) -> pd.DataFrame:
        """
        Get revenue trends over time

        Args:
            months: Number of months to analyze

        Returns:
            pd.DataFrame: Revenue trend data
        """
        query = f"""
        SELECT
            DATE_TRUNC('month', completed_at) as month,
            COUNT(*) as projects_completed,
            SUM(value) as revenue,
            AVG(value) as avg_project_value
        FROM projects
        WHERE status = 'completed'
            AND completed_at >= DATEADD(month, -{months}, CURRENT_DATE())
        GROUP BY DATE_TRUNC('month', completed_at)
        ORDER BY month
        """
        return self.execute_query(query)

    def get_conversion_funnel(self) -> pd.DataFrame:
        """Get lead-to-customer conversion funnel"""
        query = """
        WITH funnel_stages AS (
            SELECT 'Leads Generated' as stage, COUNT(*) as count, 1 as order_idx
            FROM leads
            UNION ALL
            SELECT 'Qualified Leads', COUNT(*), 2
            FROM leads WHERE status = 'qualified'
            UNION ALL
            SELECT 'Appointments Set', COUNT(*), 3
            FROM appointments WHERE status IN ('scheduled', 'completed')
            UNION ALL
            SELECT 'Proposals Sent', COUNT(*), 4
            FROM projects WHERE status IN ('proposal', 'accepted', 'in_progress', 'completed')
            UNION ALL
            SELECT 'Projects Won', COUNT(*), 5
            FROM projects WHERE status IN ('accepted', 'in_progress', 'completed')
        )
        SELECT
            stage,
            count,
            ROUND(100.0 * count / FIRST_VALUE(count) OVER (ORDER BY order_idx), 2) as conversion_rate
        FROM funnel_stages
        ORDER BY order_idx
        """
        return self.execute_query(query)

    # ========================================================================
    # BUSINESS METRICS QUERIES
    # ========================================================================

    def get_premium_market_metrics(self) -> Dict[str, Any]:
        """Get premium market penetration metrics"""
        query = """
        SELECT
            COUNT(CASE WHEN tier = 'Ultra-Premium' THEN 1 END) as ultra_premium_count,
            COUNT(CASE WHEN tier = 'Professional' THEN 1 END) as professional_count,
            AVG(CASE WHEN tier = 'Ultra-Premium' THEN lifetime_value END) as ultra_premium_avg_value,
            AVG(CASE WHEN tier = 'Professional' THEN lifetime_value END) as professional_avg_value,
            SUM(lifetime_value) as total_premium_value
        FROM customers
        WHERE tier IN ('Ultra-Premium', 'Professional')
        """
        df = self.execute_query(query)
        return df.to_dict('records')[0] if not df.empty else {}

    def get_response_time_metrics(self) -> Dict[str, Any]:
        """Get lead response time analysis (2-minute target)"""
        query = """
        SELECT
            COUNT(*) as total_leads,
            COUNT(CASE WHEN response_time_minutes <= 2 THEN 1 END) as within_target,
            AVG(response_time_minutes) as avg_response_time,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_time_minutes) as median_response_time,
            PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY response_time_minutes) as p90_response_time
        FROM leads
        WHERE response_time_minutes IS NOT NULL
            AND created_at >= DATEADD(month, -1, CURRENT_DATE())
        """
        df = self.execute_query(query)
        return df.to_dict('records')[0] if not df.empty else {}

    def get_marketing_roi(self) -> pd.DataFrame:
        """Get marketing channel ROI analysis"""
        query = """
        SELECT
            source as channel,
            COUNT(*) as leads_generated,
            SUM(marketing_cost) as total_cost,
            COUNT(CASE WHEN status = 'converted' THEN 1 END) as conversions,
            SUM(CASE WHEN status = 'converted' THEN project_value ELSE 0 END) as revenue_generated,
            ROUND(
                SUM(CASE WHEN status = 'converted' THEN project_value ELSE 0 END) /
                NULLIF(SUM(marketing_cost), 0),
                2
            ) as roi_ratio
        FROM leads
        WHERE created_at >= DATEADD(month, -3, CURRENT_DATE())
        GROUP BY source
        ORDER BY roi_ratio DESC NULLS LAST
        """
        return self.execute_query(query)

    # ========================================================================
    # ADVANCED ANALYTICS
    # ========================================================================

    def get_customer_lifetime_value_analysis(self) -> pd.DataFrame:
        """Get customer lifetime value segmentation"""
        query = """
        SELECT
            CASE
                WHEN lifetime_value >= 100000 THEN 'Tier 1: $100K+'
                WHEN lifetime_value >= 50000 THEN 'Tier 2: $50K-$100K'
                WHEN lifetime_value >= 25000 THEN 'Tier 3: $25K-$50K'
                ELSE 'Tier 4: <$25K'
            END as value_segment,
            COUNT(*) as customer_count,
            AVG(lifetime_value) as avg_ltv,
            SUM(lifetime_value) as total_value,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percent_of_total
        FROM customers
        GROUP BY
            CASE
                WHEN lifetime_value >= 100000 THEN 'Tier 1: $100K+'
                WHEN lifetime_value >= 50000 THEN 'Tier 2: $50K-$100K'
                WHEN lifetime_value >= 25000 THEN 'Tier 3: $25K-$50K'
                ELSE 'Tier 4: <$25K'
            END
        ORDER BY avg_ltv DESC
        """
        return self.execute_query(query)

    def get_geographic_analysis(self) -> pd.DataFrame:
        """Get geographic market analysis"""
        query = """
        SELECT
            city,
            zip_code,
            COUNT(*) as customer_count,
            SUM(lifetime_value) as total_value,
            AVG(lifetime_value) as avg_customer_value,
            COUNT(CASE WHEN tier IN ('Ultra-Premium', 'Professional') THEN 1 END) as premium_count
        FROM customers
        WHERE city IS NOT NULL
        GROUP BY city, zip_code
        HAVING COUNT(*) >= 3
        ORDER BY total_value DESC
        LIMIT 20
        """
        return self.execute_query(query)

    def get_team_performance_metrics(self) -> pd.DataFrame:
        """Get sales team performance metrics"""
        query = """
        SELECT
            sales_rep,
            COUNT(CASE WHEN status = 'converted' THEN 1 END) as conversions,
            COUNT(*) as total_leads_handled,
            ROUND(100.0 * COUNT(CASE WHEN status = 'converted' THEN 1 END) /
                  NULLIF(COUNT(*), 0), 2) as conversion_rate,
            SUM(CASE WHEN status = 'converted' THEN project_value ELSE 0 END) as total_revenue,
            AVG(response_time_minutes) as avg_response_time
        FROM leads
        WHERE sales_rep IS NOT NULL
            AND created_at >= DATEADD(month, -3, CURRENT_DATE())
        GROUP BY sales_rep
        ORDER BY total_revenue DESC
        """
        return self.execute_query(query)


@st.cache_resource
def get_snowflake_client() -> SnowflakeClient:
    """
    Get cached Snowflake client instance
    Uses Streamlit's caching to maintain single connection
    """
    return SnowflakeClient()


# ============================================================================
# EXAMPLE USAGE FUNCTIONS
# ============================================================================

def example_create_interactive_chart(hifives_val: int = 60):
    """
    Example from Snowflake template - create interactive chart

    Args:
        hifives_val: Value from interactive slider
    """
    client = get_snowflake_client()

    if not client.is_connected():
        st.warning("Snowflake not available - showing demo data")
        # Create demo data
        data = [[50, 25, "Q1"], [20, 35, "Q2"], [hifives_val, 30, "Q3"]]
        df = pd.DataFrame(data, columns=["HIGH_FIVES", "FIST_BUMPS", "QUARTER"])
    else:
        # Create actual Snowflake dataframe
        data = [[50, 25, "Q1"], [20, 35, "Q2"], [hifives_val, 30, "Q3"]]
        df = client.create_dataframe(data, schema=["HIGH_FIVES", "FIST_BUMPS", "QUARTER"])

    # Display chart
    st.subheader("Number of high-fives")
    st.bar_chart(data=df, x="QUARTER", y="HIGH_FIVES")

    st.subheader("Underlying data")
    st.dataframe(df, use_container_width=True)

    return df
