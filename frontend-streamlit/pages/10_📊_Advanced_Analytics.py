"""
Advanced Analytics Dashboard

Provides advanced business intelligence including:
- Revenue forecasting with ML
- Lead quality heat maps
- Conversion funnel analysis
- Customer lifetime value distribution
- Churn risk scoring
- Marketing channel attribution
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from utils.auth import require_auth
from utils.api_client import get_api_base_url

# Require authentication
require_auth()

# API base URL
API_BASE = get_api_base_url()

st.title("📊 Advanced Analytics Dashboard")
st.markdown("*Powered by Machine Learning & Predictive Analytics*")

# Create tabs for different analytics
tabs = st.tabs([
    "📈 Revenue Forecast",
    "🔥 Lead Quality Heatmap",
    "🎯 Conversion Funnel",
    "💰 CLV Distribution",
    "⚠️ Churn Risk",
    "📢 Marketing Attribution"
])

# ============================================================================
# TAB 1: REVENUE FORECAST
# ============================================================================
with tabs[0]:
    st.header("📈 Revenue Forecasting")
    st.markdown("**AI-powered 30-day revenue predictions with confidence intervals**")

    col1, col2 = st.columns([3, 1])

    with col2:
        days_ahead = st.slider("Days to Forecast", 7, 90, 30)
        confidence_level = st.select_slider(
            "Confidence Level",
            options=[0.80, 0.90, 0.95, 0.99],
            value=0.95,
            format_func=lambda x: f"{int(x*100)}%"
        )

        if st.button("Generate Forecast", type="primary"):
            with st.spinner("Generating forecast..."):
                try:
                    response = requests.get(
                        f"{API_BASE}/api/advanced-analytics/revenue/forecast",
                        params={
                            'days_ahead': days_ahead,
                            'confidence_level': confidence_level
                        }
                    )

                    if response.status_code == 200:
                        data = response.json()
                        st.session_state['forecast_data'] = data
                        st.success("✅ Forecast generated!")
                    else:
                        st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Failed to generate forecast: {str(e)}")

    with col1:
        if 'forecast_data' in st.session_state:
            data = st.session_state['forecast_data']

            # Display summary metrics
            summary = data.get('summary', {})
            col_a, col_b, col_c, col_d = st.columns(4)

            with col_a:
                st.metric(
                    "Total Forecast",
                    f"${summary.get('total_forecast_revenue', 0):,.0f}",
                    f"{summary.get('growth_rate_percent', 0):+.1f}%"
                )

            with col_b:
                st.metric(
                    "Avg Daily Revenue",
                    f"${summary.get('average_daily_revenue', 0):,.0f}"
                )

            with col_c:
                st.metric(
                    "Historical Avg",
                    f"${summary.get('historical_average', 0):,.0f}"
                )

            with col_d:
                st.metric(
                    "Forecast Period",
                    f"{summary.get('forecast_period_days', 0)} days"
                )

            # Create forecast chart
            forecast_df = pd.DataFrame(data['forecast'])
            forecast_df['date'] = pd.to_datetime(forecast_df['date'])

            fig = go.Figure()

            # Add main prediction line
            fig.add_trace(go.Scatter(
                x=forecast_df['date'],
                y=forecast_df['predicted_revenue'],
                mode='lines+markers',
                name='Predicted Revenue',
                line=dict(color='#1f77b4', width=3)
            ))

            # Add confidence interval
            fig.add_trace(go.Scatter(
                x=forecast_df['date'].tolist() + forecast_df['date'].tolist()[::-1],
                y=forecast_df['upper_bound'].tolist() + forecast_df['lower_bound'].tolist()[::-1],
                fill='toself',
                fillcolor='rgba(31, 119, 180, 0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                name=f'{int(confidence_level*100)}% Confidence Interval',
                showlegend=True
            ))

            fig.update_layout(
                title=f"{days_ahead}-Day Revenue Forecast",
                xaxis_title="Date",
                yaxis_title="Revenue ($)",
                hovermode='x unified',
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

            # Show forecast table
            with st.expander("📋 View Forecast Data"):
                st.dataframe(
                    forecast_df.style.format({
                        'predicted_revenue': '${:,.0f}',
                        'lower_bound': '${:,.0f}',
                        'upper_bound': '${:,.0f}'
                    }),
                    use_container_width=True
                )

        else:
            st.info("👆 Click 'Generate Forecast' to see predictions")

# ============================================================================
# TAB 2: LEAD QUALITY HEATMAP
# ============================================================================
with tabs[1]:
    st.header("🔥 Lead Quality Heatmap")
    st.markdown("**Identify high-quality lead sources and segments**")

    col1, col2 = st.columns([3, 1])

    with col2:
        segment_by = st.selectbox(
            "Segment By",
            options=['source', 'zip_code', 'property_value'],
            format_func=lambda x: {
                'source': 'Lead Source',
                'zip_code': 'Zip Code',
                'property_value': 'Property Value'
            }[x]
        )

        if st.button("Generate Heatmap", type="primary"):
            with st.spinner("Analyzing lead quality..."):
                try:
                    response = requests.get(
                        f"{API_BASE}/api/advanced-analytics/leads/quality-heatmap",
                        params={'segment_by': segment_by}
                    )

                    if response.status_code == 200:
                        data = response.json()
                        st.session_state['heatmap_data'] = data
                        st.success("✅ Heatmap generated!")
                    else:
                        st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Failed to generate heatmap: {str(e)}")

    with col1:
        if 'heatmap_data' in st.session_state:
            data = st.session_state['heatmap_data']
            summary = data.get('summary', {})

            # Display summary
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Total Leads", f"{summary.get('total_leads', 0):,}")
            with col_b:
                st.metric("Segments Analyzed", summary.get('segments', 0))
            with col_c:
                best_segment = summary.get('best_segment', 'N/A')
                st.metric("Best Segment", best_segment)

            # Create heatmap
            heatmap_df = pd.DataFrame(data['heatmap'])

            if not heatmap_df.empty:
                # Quality score heatmap
                fig = px.bar(
                    heatmap_df,
                    x='segment',
                    y='quality_score',
                    color='quality_tier',
                    title=f"Lead Quality by {segment_by.replace('_', ' ').title()}",
                    labels={'segment': segment_by.replace('_', ' ').title(), 'quality_score': 'Quality Score'},
                    color_discrete_map={
                        'excellent': '#00cc66',
                        'good': '#66b3ff',
                        'fair': '#ffcc00',
                        'poor': '#ff6666'
                    },
                    height=400
                )

                st.plotly_chart(fig, use_container_width=True)

                # Detailed table
                st.subheader("📊 Segment Performance")
                st.dataframe(
                    heatmap_df.style.format({
                        'conversion_rate': '{:.1f}%',
                        'avg_contact_quality': '{:.1f}',
                        'quality_score': '{:.1f}'
                    }).background_gradient(subset=['quality_score'], cmap='RdYlGn'),
                    use_container_width=True
                )

        else:
            st.info("👆 Click 'Generate Heatmap' to analyze lead quality")

# ============================================================================
# TAB 3: CONVERSION FUNNEL
# ============================================================================
with tabs[2]:
    st.header("🎯 Conversion Funnel Analysis")
    st.markdown("**Track lead progression and identify drop-off points**")

    if st.button("Analyze Funnel", type="primary"):
        with st.spinner("Analyzing conversion funnel..."):
            try:
                response = requests.get(f"{API_BASE}/api/advanced-analytics/conversion/funnel")

                if response.status_code == 200:
                    data = response.json()
                    st.session_state['funnel_data'] = data
                    st.success("✅ Funnel analyzed!")
                else:
                    st.error(f"Error: {response.json().get('error', 'Unknown error')}")
            except Exception as e:
                st.error(f"Failed to analyze funnel: {str(e)}")

    if 'funnel_data' in st.session_state:
        data = st.session_state['funnel_data']
        summary = data.get('summary', {})

        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Leads", f"{summary.get('total_leads', 0):,}")
        with col2:
            st.metric("Won Leads", f"{summary.get('won_leads', 0):,}")
        with col3:
            st.metric("Conversion Rate", f"{summary.get('overall_conversion_rate', 0):.1f}%")
        with col4:
            biggest_drop = summary.get('biggest_drop_off_stage', 'N/A')
            st.metric("Biggest Drop-off", biggest_drop)

        # Create funnel visualization
        funnel_df = pd.DataFrame(data['funnel'])

        fig = go.Figure(go.Funnel(
            y=funnel_df['stage'],
            x=funnel_df['count'],
            textposition="inside",
            textinfo="value+percent initial",
            marker=dict(
                color=['#4CAF50', '#8BC34A', '#CDDC39', '#FFEB3B', '#FFC107', '#FF9800']
            )
        ))

        fig.update_layout(
            title="Lead Conversion Funnel",
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

        # Detailed funnel table
        st.subheader("📊 Funnel Stage Details")
        st.dataframe(
            funnel_df.style.format({
                'conversion_rate': '{:.1f}%',
                'drop_off_rate': '{:.1f}%'
            }).background_gradient(subset=['drop_off_rate'], cmap='Reds_r'),
            use_container_width=True
        )

    else:
        st.info("👆 Click 'Analyze Funnel' to see conversion data")

# ============================================================================
# TAB 4: CLV DISTRIBUTION
# ============================================================================
with tabs[3]:
    st.header("💰 Customer Lifetime Value Distribution")
    st.markdown("**Understand customer value segments**")

    if st.button("Analyze CLV", type="primary"):
        with st.spinner("Analyzing customer lifetime value..."):
            try:
                response = requests.get(f"{API_BASE}/api/advanced-analytics/customers/clv-distribution")

                if response.status_code == 200:
                    data = response.json()
                    st.session_state['clv_data'] = data
                    st.success("✅ CLV analyzed!")
                else:
                    st.error(f"Error: {response.json().get('error', 'Unknown error')}")
            except Exception as e:
                st.error(f"Failed to analyze CLV: {str(e)}")

    if 'clv_data' in st.session_state:
        data = st.session_state['clv_data']
        summary = data.get('summary', {})

        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Customers", f"{summary.get('total_customers', 0):,}")
        with col2:
            st.metric("Avg CLV", f"${summary.get('avg_clv', 0):,.0f}")
        with col3:
            st.metric("Median CLV", f"${summary.get('median_clv', 0):,.0f}")
        with col4:
            st.metric("Highest CLV", f"${summary.get('highest_clv', 0):,.0f}")

        # Create CLV distribution chart
        distribution = data.get('distribution', [])

        if distribution and len(distribution) > 0:
            clv_df = pd.DataFrame(distribution)

            # Check if required columns exist
            if 'bucket' in clv_df.columns and 'customer_count' in clv_df.columns:
                fig = px.bar(
                    clv_df,
                    x='bucket',
                    y='customer_count',
                    title="Customer Lifetime Value Distribution",
                    labels={'bucket': 'CLV Bucket', 'customer_count': 'Number of Customers'},
                    text='percentage' if 'percentage' in clv_df.columns else None,
                    color='customer_count',
                    color_continuous_scale='Viridis'
                )

                fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                fig.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 Distribution data structure not available")
        else:
            st.info("📊 No distribution data available yet. Add more customer data to see CLV distribution.")

        # CLV table
        if distribution and len(distribution) > 0:
            st.subheader("📊 CLV Segments")
            clv_df = pd.DataFrame(distribution)

            # Format columns that exist
            format_dict = {}
            if 'percentage' in clv_df.columns:
                format_dict['percentage'] = '{:.1f}%'
            if 'min_value' in clv_df.columns:
                format_dict['min_value'] = '${:,.0f}'
            if 'max_value' in clv_df.columns:
                format_dict['max_value'] = '${:,.0f}'

            if format_dict:
                st.dataframe(
                    clv_df.style.format(format_dict),
                    use_container_width=True
                )
            else:
                st.dataframe(clv_df, use_container_width=True)

    else:
        st.info("👆 Click 'Analyze CLV' to see customer value distribution")

# ============================================================================
# TAB 5: CHURN RISK
# ============================================================================
with tabs[4]:
    st.header("⚠️ Churn Risk Analysis")
    st.markdown("**Identify at-risk customers and prevent churn**")

    if st.button("Analyze Churn Risk", type="primary"):
        with st.spinner("Analyzing churn risk..."):
            try:
                response = requests.get(f"{API_BASE}/api/advanced-analytics/customers/churn-risk")

                if response.status_code == 200:
                    data = response.json()
                    st.session_state['churn_data'] = data
                    st.success("✅ Churn risk analyzed!")
                else:
                    st.error(f"Error: {response.json().get('error', 'Unknown error')}")
            except Exception as e:
                st.error(f"Failed to analyze churn risk: {str(e)}")

    if 'churn_data' in st.session_state:
        data = st.session_state['churn_data']
        summary = data.get('summary', {})

        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Customers", f"{summary.get('total_customers', 0):,}")
        with col2:
            high_risk = summary.get('high_risk_count', 0)
            st.metric("High Risk", high_risk, delta=f"{summary.get('high_risk_percentage', 0):.1f}%")
        with col3:
            st.metric("Medium Risk", summary.get('medium_risk_count', 0))
        with col4:
            st.metric("Low Risk", summary.get('low_risk_count', 0))

        # At-risk customers table
        churn_df = pd.DataFrame(data['churn_analysis'])

        if not churn_df.empty:
            st.subheader("🚨 High-Risk Customers")

            # Filter and display high-risk customers
            high_risk_df = churn_df[churn_df['risk_category'] == 'high'].head(10)

            if not high_risk_df.empty:
                st.dataframe(
                    high_risk_df[['customer_name', 'days_since_last_project', 'churn_risk_score', 'recommended_action']].style.format({
                        'churn_risk_score': '{:.1f}',
                        'days_since_last_project': '{:.0f} days'
                    }).background_gradient(subset=['churn_risk_score'], cmap='Reds'),
                    use_container_width=True
                )
            else:
                st.info("No high-risk customers found")

            # Churn risk distribution
            st.subheader("📊 Risk Distribution")
            risk_counts = churn_df['risk_category'].value_counts()

            fig = px.pie(
                values=risk_counts.values,
                names=risk_counts.index,
                title="Customer Risk Distribution",
                color=risk_counts.index,
                color_discrete_map={'high': '#ff4444', 'medium': '#ffbb33', 'low': '#00C851'}
            )

            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("👆 Click 'Analyze Churn Risk' to identify at-risk customers")

# ============================================================================
# TAB 6: MARKETING ATTRIBUTION
# ============================================================================
with tabs[5]:
    st.header("📢 Marketing Channel Attribution")
    st.markdown("**Measure channel effectiveness and ROI**")

    if st.button("Analyze Attribution", type="primary"):
        with st.spinner("Analyzing marketing channels..."):
            try:
                response = requests.get(f"{API_BASE}/api/advanced-analytics/marketing/attribution")

                if response.status_code == 200:
                    data = response.json()
                    st.session_state['attribution_data'] = data
                    st.success("✅ Attribution analyzed!")
                else:
                    st.error(f"Error: {response.json().get('error', 'Unknown error')}")
            except Exception as e:
                st.error(f"Failed to analyze attribution: {str(e)}")

    if 'attribution_data' in st.session_state:
        data = st.session_state['attribution_data']
        summary = data.get('summary', {})

        # Display summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Leads", f"{summary.get('total_leads', 0):,}")
        with col2:
            st.metric("Total Channels", summary.get('total_channels', 0))
        with col3:
            st.metric("Est. Revenue", f"${summary.get('total_estimated_revenue', 0):,.0f}")

        # Channel performance
        attribution_df = pd.DataFrame(data['attribution'])

        if not attribution_df.empty:
            # Channel effectiveness chart
            fig = px.scatter(
                attribution_df,
                x='conversion_rate',
                y='revenue_per_lead',
                size='total_leads',
                color='effectiveness_score',
                hover_data=['channel', 'converted_leads'],
                title="Channel Performance Matrix",
                labels={
                    'conversion_rate': 'Conversion Rate (%)',
                    'revenue_per_lead': 'Revenue per Lead ($)',
                    'effectiveness_score': 'Effectiveness Score'
                },
                color_continuous_scale='Viridis'
            )

            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

            # Detailed channel table
            st.subheader("📊 Channel Performance Details")
            st.dataframe(
                attribution_df.style.format({
                    'conversion_rate': '{:.1f}%',
                    'estimated_revenue': '${:,.0f}',
                    'revenue_per_lead': '${:,.0f}',
                    'effectiveness_score': '{:.1f}'
                }).background_gradient(subset=['effectiveness_score'], cmap='Greens'),
                use_container_width=True
            )

    else:
        st.info("👆 Click 'Analyze Attribution' to see channel performance")

# Footer
st.markdown("---")
st.markdown("*Advanced Analytics powered by ML models and predictive algorithms*")
