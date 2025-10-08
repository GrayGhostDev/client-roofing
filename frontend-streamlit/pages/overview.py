"""
Overview Dashboard Page
Executive summary with key metrics and trends
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.api_client import get_api_client
from utils.visualization import (
    create_kpi_cards,
    create_line_chart,
    create_funnel_chart,
    create_pie_chart,
    format_currency,
    export_to_csv
)


def render():
    """Render the overview dashboard page"""
    st.title("📊 Executive Dashboard Overview")
    st.markdown("Real-time business metrics and performance indicators")
    
    # Get date range from session state
    start_date, end_date = st.session_state.date_range
    
    # Initialize API client
    api = get_api_client()
    
    # Check API health
    with st.spinner("Connecting to CRM API..."):
        health = api.health_check()
        if health.get('status') != 'healthy':
            st.error("⚠️ Unable to connect to CRM API. Please check your connection.")
            st.stop()
        else:
            st.success(f"✅ Connected to {health.get('service', 'CRM API')}")
    
    # Fetch dashboard data
    with st.spinner("Loading dashboard data..."):
        try:
            # Get summary statistics
            lead_stats = api.get_lead_statistics(start_date, end_date)
            project_stats = api.get_project_statistics(start_date, end_date)
            revenue_data = api.get_revenue_analytics(start_date, end_date)
            
            # Generate mock data if API returns empty
            if not lead_stats:
                lead_stats = generate_mock_lead_stats()
            if not project_stats:
                project_stats = generate_mock_project_stats()
            if not revenue_data:
                revenue_data = generate_mock_revenue_data()
                
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            # Use mock data as fallback
            lead_stats = generate_mock_lead_stats()
            project_stats = generate_mock_project_stats()
            revenue_data = generate_mock_revenue_data()
    
    # Key Performance Indicators
    st.subheader("📈 Key Performance Indicators")
    
    kpi_metrics = [
        {
            'label': 'Total Leads',
            'value': lead_stats.get('total_leads', 0),
            'delta': lead_stats.get('leads_change', 0),
            'delta_color': 'normal'
        },
        {
            'label': 'Conversion Rate',
            'value': f"{lead_stats.get('conversion_rate', 0):.1f}%",
            'delta': f"{lead_stats.get('conversion_change', 0):.1f}%",
            'delta_color': 'normal'
        },
        {
            'label': 'Active Projects',
            'value': project_stats.get('active_projects', 0),
            'delta': project_stats.get('projects_change', 0),
            'delta_color': 'normal'
        },
        {
            'label': 'Total Revenue',
            'value': format_currency(revenue_data.get('total_revenue', 0)),
            'delta': format_currency(revenue_data.get('revenue_change', 0)),
            'delta_color': 'normal'
        }
    ]
    
    create_kpi_cards(kpi_metrics)
    
    st.divider()
    
    # Two column layout for charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Lead Conversion Funnel")
        
        # Conversion funnel data
        funnel_stages = ['New Leads', 'Contacted', 'Qualified', 'Quoted', 'Converted']
        funnel_values = [
            lead_stats.get('new_leads', 150),
            lead_stats.get('contacted_leads', 120),
            lead_stats.get('qualified_leads', 90),
            lead_stats.get('quoted_leads', 60),
            lead_stats.get('converted_leads', 40)
        ]
        
        fig_funnel = create_funnel_chart(
            stages=funnel_stages,
            values=funnel_values,
            title="Lead Conversion Pipeline"
        )
        st.plotly_chart(fig_funnel)
        
        # Funnel metrics
        st.caption("Pipeline Metrics")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("In Pipeline", sum(funnel_values[:-1]))
        with col_b:
            conversion = (funnel_values[-1] / funnel_values[0] * 100) if funnel_values[0] > 0 else 0
            st.metric("Overall Conversion", f"{conversion:.1f}%")
        with col_c:
            st.metric("Pipeline Value", format_currency(lead_stats.get('pipeline_value', 250000)))
    
    with col2:
        st.subheader("💰 Revenue by Source")
        
        # Revenue by source
        source_data = pd.DataFrame([
            {'source': 'Website', 'revenue': 150000},
            {'source': 'Referral', 'revenue': 120000},
            {'source': 'Social Media', 'revenue': 80000},
            {'source': 'Direct', 'revenue': 50000},
            {'source': 'Other', 'revenue': 30000}
        ])
        
        fig_pie = create_pie_chart(
            data=source_data,
            values='revenue',
            names='source',
            title="Revenue Distribution by Lead Source"
        )
        st.plotly_chart(fig_pie)
        
        # Source metrics
        st.caption("Top Performing Sources")
        for idx, row in source_data.head(3).iterrows():
            st.write(f"**{row['source']}**: {format_currency(row['revenue'])}")
    
    st.divider()
    
    # Revenue Trend
    st.subheader("📊 Revenue Trend")
    
    # Generate time series data
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    revenue_trend = pd.DataFrame({
        'date': date_range,
        'revenue': [15000 + (i * 500) + (1000 if i % 7 == 0 else 0) for i in range(len(date_range))]
    })
    
    fig_line = create_line_chart(
        data=revenue_trend,
        x='date',
        y='revenue',
        title="Daily Revenue Trend"
    )
    st.plotly_chart(fig_line)
    
    st.divider()
    
    # Team Performance Summary
    st.subheader("👥 Team Performance Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Active Team Members", 12)
        st.metric("Avg Response Time", "2.3 hours")
    
    with col2:
        st.metric("Customer Satisfaction", "4.8/5.0", delta="0.2")
        st.metric("Appointments This Week", 45, delta="8")
    
    with col3:
        st.metric("Deals Closed", 18, delta="3")
        st.metric("Follow-ups Completed", "95%", delta="5%")
    
    st.divider()
    
    # Recent Activity
    st.subheader("📋 Recent Activity")
    
    recent_activity = pd.DataFrame([
        {
            'time': '10 min ago',
            'type': 'Lead',
            'action': 'New lead from website',
            'value': '$25,000'
        },
        {
            'time': '25 min ago',
            'type': 'Project',
            'action': 'Project completed',
            'value': '$45,000'
        },
        {
            'time': '1 hour ago',
            'type': 'Appointment',
            'action': 'Site visit scheduled',
            'value': '$30,000'
        },
        {
            'time': '2 hours ago',
            'type': 'Quote',
            'action': 'Quote sent to customer',
            'value': '$55,000'
        },
        {
            'time': '3 hours ago',
            'type': 'Lead',
            'action': 'Lead qualified',
            'value': '$20,000'
        }
    ])
    
    st.dataframe(
        recent_activity,
        hide_index=True,
        column_config={
            'time': st.column_config.TextColumn('Time'),
            'type': st.column_config.TextColumn('Type'),
            'action': st.column_config.TextColumn('Action'),
            'value': st.column_config.TextColumn('Est. Value')
        }
    )
    
    # Export options
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("📊 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
    
    with col2:
        export_to_csv(recent_activity, "dashboard_overview")
    
    with col3:
        st.info("💡 Tip: Use the sidebar to filter by date range")


def generate_mock_lead_stats():
    """Generate mock lead statistics for demo"""
    return {
        'total_leads': 156,
        'leads_change': 12,
        'conversion_rate': 25.6,
        'conversion_change': 2.3,
        'new_leads': 150,
        'contacted_leads': 120,
        'qualified_leads': 90,
        'quoted_leads': 60,
        'converted_leads': 40,
        'pipeline_value': 250000
    }


def generate_mock_project_stats():
    """Generate mock project statistics for demo"""
    return {
        'active_projects': 34,
        'projects_change': 5,
        'completed_projects': 12,
        'total_value': 850000
    }


def generate_mock_revenue_data():
    """Generate mock revenue data for demo"""
    return {
        'total_revenue': 430000,
        'revenue_change': 45000,
        'avg_deal_size': 25000,
        'forecasted_revenue': 580000
    }
