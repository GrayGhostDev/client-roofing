"""
Snowflake Analytics Dashboard
Demonstrates Snowflake integration capabilities for advanced analytics
Version: 1.0.0
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.snowflake_client import get_snowflake_client, example_create_interactive_chart
from utils.api_client import get_api_client
import plotly.graph_objects as go
import plotly.express as px

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
# Note: Page config is set in Home.py when using st.navigation()
# Individual pages should not call st.set_page_config()

# ============================================================================
# CUSTOM CSS
# ============================================================================
st.markdown("""
    <style>
    .snowflake-header {
        background: linear-gradient(135deg, #29b5e8 0%, #1a73e8 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin-bottom: 30px;
    }

    .metric-card-snowflake {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #1a73e8;
    }

    .connection-badge {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        margin-left: 10px;
    }

    .badge-connected {
        background: #4caf50;
        color: white;
    }

    .badge-disconnected {
        background: #ff9800;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER
# ============================================================================
snowflake_client = get_snowflake_client()

connection_status = "CONNECTED" if snowflake_client.is_connected() else "LOCAL MODE"
badge_class = "badge-connected" if snowflake_client.is_connected() else "badge-disconnected"

st.markdown(f"""
    <div class="snowflake-header">
        <h1>🔷 Snowflake Analytics
            <span class="connection-badge {badge_class}">{connection_status}</span>
        </h1>
        <p style="margin: 5px 0 0 0; opacity: 0.9;">
            Advanced data warehouse analytics and reporting
        </p>
    </div>
""", unsafe_allow_html=True)

# ============================================================================
# CONNECTION STATUS
# ============================================================================
with st.expander("🔌 Connection Information", expanded=False):
    if snowflake_client.is_connected():
        st.success("✅ Connected to Snowflake Data Warehouse")
        st.info("""
        **Active Connection Features:**
        - Direct query execution
        - Real-time data processing
        - Advanced analytics capabilities
        - Scalable data transformations
        """)
    else:
        st.warning("⚠️ Snowflake not available - Running in local mode")
        st.info("""
        **Local Mode:**
        - Using API backend for data
        - Simulated Snowflake features
        - Deploy to Snowflake to enable full features

        **To enable Snowflake:**
        1. Deploy app to Snowflake (streamlit deploy)
        2. Configure Snowflake credentials
        3. Restart application
        """)

# ============================================================================
# EXAMPLE: INTERACTIVE SNOWFLAKE CHART
# ============================================================================
st.markdown("---")
st.header("📊 Interactive Demo: Snowflake Data Visualization")

st.write("""
This example demonstrates Snowflake integration with interactive Streamlit components.
Adjust the slider to see real-time updates.
""")

# Interactive slider
hifives_val = st.slider(
    "Number of high-fives in Q3",
    min_value=0,
    max_value=90,
    value=60,
    help="Use this to enter the number of high-fives you gave in Q3"
)

# Create chart using Snowflake client
example_create_interactive_chart(hifives_val)

# ============================================================================
# CRM ANALYTICS FROM SNOWFLAKE
# ============================================================================
st.markdown("---")
st.header("📈 CRM Analytics")

if snowflake_client.is_connected():
    st.info("🔷 Querying Snowflake data warehouse...")

    # Create tabs for different analytics
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Revenue Trends",
        "🎯 Conversion Funnel",
        "👥 Customer Segmentation",
        "🗺️ Geographic Analysis"
    ])

    # Revenue Trends
    with tab1:
        st.subheader("Revenue Trends (12 Months)")
        revenue_df = snowflake_client.get_revenue_trends(months=12)

        if not revenue_df.empty:
            # Create line chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=revenue_df['MONTH'],
                y=revenue_df['REVENUE'],
                mode='lines+markers',
                name='Revenue',
                line=dict(color='#1a73e8', width=3)
            ))
            fig.update_layout(
                title="Monthly Revenue Trend",
                xaxis_title="Month",
                yaxis_title="Revenue ($)",
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                total_revenue = revenue_df['REVENUE'].sum()
                st.metric("Total Revenue (12M)", f"${total_revenue:,.0f}")
            with col2:
                avg_monthly = revenue_df['REVENUE'].mean()
                st.metric("Avg Monthly Revenue", f"${avg_monthly:,.0f}")
            with col3:
                total_projects = revenue_df['PROJECTS_COMPLETED'].sum()
                st.metric("Projects Completed", f"{total_projects:,.0f}")
        else:
            st.info("No revenue data available")

    # Conversion Funnel
    with tab2:
        st.subheader("Lead-to-Customer Conversion Funnel")
        funnel_df = snowflake_client.get_conversion_funnel()

        if not funnel_df.empty:
            # Create funnel chart
            fig = go.Figure(go.Funnel(
                y=funnel_df['STAGE'],
                x=funnel_df['COUNT'],
                textinfo="value+percent initial",
                marker=dict(color=['#1a73e8', '#4285f4', '#8ab4f8', '#aecbfa', '#c5e1fb'])
            ))
            fig.update_layout(title="Conversion Funnel Analysis")
            st.plotly_chart(fig, use_container_width=True)

            # Display table
            st.dataframe(funnel_df, use_container_width=True)
        else:
            st.info("No funnel data available")

    # Customer Segmentation
    with tab3:
        st.subheader("Customer Lifetime Value Segmentation")
        ltv_df = snowflake_client.get_customer_lifetime_value_analysis()

        if not ltv_df.empty:
            # Create pie chart
            fig = px.pie(
                ltv_df,
                values='CUSTOMER_COUNT',
                names='VALUE_SEGMENT',
                title='Customer Distribution by Value Segment'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Display detailed table
            st.dataframe(ltv_df, use_container_width=True)
        else:
            st.info("No customer segmentation data available")

    # Geographic Analysis
    with tab4:
        st.subheader("Top Markets by Revenue")
        geo_df = snowflake_client.get_geographic_analysis()

        if not geo_df.empty:
            # Create bar chart
            fig = px.bar(
                geo_df.head(10),
                x='CITY',
                y='TOTAL_VALUE',
                color='PREMIUM_COUNT',
                title='Top 10 Cities by Total Customer Value',
                labels={'TOTAL_VALUE': 'Total Value ($)', 'PREMIUM_COUNT': 'Premium Customers'}
            )
            st.plotly_chart(fig, use_container_width=True)

            # Display full table
            st.dataframe(geo_df, use_container_width=True)
        else:
            st.info("No geographic data available")

else:
    # Fallback to API data when Snowflake not available
    st.info("📡 Using API backend (Snowflake not connected)")

    try:
        api_client = get_api_client()

        # Get business metrics from API
        st.subheader("Business Metrics Summary")
        summary = api_client.get_business_summary()

        if summary:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Total Revenue",
                    f"${summary.get('total_revenue', 0):,.0f}",
                    delta=f"{summary.get('revenue_growth', 0):.1f}%"
                )

            with col2:
                st.metric(
                    "Active Projects",
                    summary.get('active_projects', 0),
                    delta=summary.get('project_growth', 0)
                )

            with col3:
                st.metric(
                    "Conversion Rate",
                    f"{summary.get('conversion_rate', 0):.1f}%",
                    delta=f"{summary.get('conversion_change', 0):.1f}%"
                )

            with col4:
                st.metric(
                    "Avg Response Time",
                    f"{summary.get('avg_response_time', 0):.1f} min",
                    delta=f"{summary.get('response_time_change', 0):.1f} min",
                    delta_color="inverse"
                )

        # Marketing ROI
        st.subheader("Marketing Channel Performance")
        roi_data = api_client.get_marketing_roi()
        if roi_data:
            st.json(roi_data)

    except Exception as e:
        st.error(f"Error fetching API data: {str(e)}")
        st.info("Backend API may not be running")

# ============================================================================
# BUSINESS METRICS (PREMIUM MARKET FOCUS)
# ============================================================================
st.markdown("---")
st.header("💎 Premium Market Analysis")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="metric-card-snowflake">
        <h3>Target Market Segments</h3>
        <ul>
            <li><strong>Ultra-Premium:</strong> Top 5% (10,500 properties)</li>
            <li><strong>Professional:</strong> Next 15% (22,900 properties)</li>
            <li><strong>Geographic Focus:</strong> Bloomfield Hills, Birmingham, Grosse Pointe</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-card-snowflake">
        <h3>Performance Targets</h3>
        <ul>
            <li><strong>Response Time:</strong> <2 minutes (78% better conversion)</li>
            <li><strong>Conversion Rate:</strong> 25-35% (vs 8-15% industry)</li>
            <li><strong>Avg Project Value:</strong> $45K (premium segment)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# DEPLOYMENT INSTRUCTIONS
# ============================================================================
st.markdown("---")
with st.expander("📚 Snowflake Deployment Instructions"):
    st.markdown("""
    ## Deploy to Snowflake

    ### 1. Install Snowflake CLI
    ```bash
    pip install snowflake-cli-labs
    snow --version
    ```

    ### 2. Configure Connection
    ```bash
    snow connection add
    # Follow prompts to enter:
    # - Account identifier
    # - Username
    # - Password
    # - Role
    # - Warehouse
    # - Database
    # - Schema
    ```

    ### 3. Create Streamlit App
    ```bash
    snow streamlit deploy \
        --file Home.py \
        --name iswitch_roofs_crm \
        --replace
    ```

    ### 4. Configure Requirements
    Make sure `requirements.txt` includes:
    ```
    snowflake-snowpark-python
    ```

    ### 5. Access Application
    ```
    https://<account>.snowflakecomputing.com/streamlit/<database>/<schema>/<app_name>
    ```

    ### 6. Verify Connection
    The app will automatically detect Snowflake environment and enable advanced features.

    ## Required Snowflake Tables

    ### Leads Table
    ```sql
    CREATE TABLE leads (
        id VARCHAR PRIMARY KEY,
        name VARCHAR,
        email VARCHAR,
        phone VARCHAR,
        source VARCHAR,
        status VARCHAR,
        value DECIMAL(10,2),
        response_time_minutes DECIMAL(5,2),
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    );
    ```

    ### Customers Table
    ```sql
    CREATE TABLE customers (
        id VARCHAR PRIMARY KEY,
        name VARCHAR,
        email VARCHAR,
        phone VARCHAR,
        tier VARCHAR,
        lifetime_value DECIMAL(12,2),
        city VARCHAR,
        zip_code VARCHAR,
        last_contact TIMESTAMP,
        created_at TIMESTAMP
    );
    ```

    ### Projects Table
    ```sql
    CREATE TABLE projects (
        id VARCHAR PRIMARY KEY,
        customer_id VARCHAR,
        name VARCHAR,
        status VARCHAR,
        value DECIMAL(12,2),
        start_date DATE,
        end_date DATE,
        completed_at TIMESTAMP,
        created_at TIMESTAMP
    );
    ```

    ## Useful Resources
    - [Snowflake Streamlit Docs](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)
    - [Snowpark Python API](https://docs.snowflake.com/en/developer-guide/snowpark/python/index)
    - [Streamlit in Snowflake Tutorial](https://quickstarts.snowflake.com/guide/getting_started_with_streamlit)
    """)

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.caption("🔷 Snowflake Analytics Dashboard | iSwitch Roofs CRM v3.0.0")
