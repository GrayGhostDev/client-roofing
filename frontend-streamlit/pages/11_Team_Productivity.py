"""
Team Productivity Page
Monitor team performance, activity, and efficiency metrics
"""

import streamlit as st
import pandas as pd
from utils.visualization import (
    create_kpi_cards,
    create_bar_chart,
    create_heatmap,
    export_to_csv
)


def render():
    """Render the team productivity page"""
    st.title("👥 Team Productivity")
    st.markdown("Track team performance, activity levels, and efficiency metrics")

    # Show demo data notice
    st.info("📊 Displaying demo team data - Connect to CRM backend for real-time team analytics")

    # Team KPIs
    st.subheader("📊 Team Performance Metrics")

    team_kpis = [
        {'label': 'Active Team Members', 'value': 12, 'delta': 2},
        {'label': 'Avg Response Time', 'value': '2.3 hours', 'delta': '-0.5 hours'},
        {'label': 'Tasks Completed', 'value': 156, 'delta': 18},
        {'label': 'Team Efficiency', 'value': '87%', 'delta': '5%'}
    ]

    create_kpi_cards(team_kpis)

    st.divider()

    # Individual performance
    st.subheader("🏆 Individual Performance")

    team_data = pd.DataFrame([
        {
            'name': 'John Smith',
            'role': 'Sales Rep',
            'leads_handled': 45,
            'conversions': 12,
            'revenue': '$285,000',
            'satisfaction': 4.9
        },
        {
            'name': 'Mary Johnson',
            'role': 'Project Manager',
            'leads_handled': 38,
            'conversions': 15,
            'revenue': '$425,000',
            'satisfaction': 4.8
        },
        {
            'name': 'Robert Williams',
            'role': 'Sales Rep',
            'leads_handled': 52,
            'conversions': 14,
            'revenue': '$330,000',
            'satisfaction': 4.7
        },
        {
            'name': 'Patricia Brown',
            'role': 'Account Manager',
            'leads_handled': 41,
            'conversions': 10,
            'revenue': '$245,000',
            'satisfaction': 4.9
        },
        {
            'name': 'Michael Davis',
            'role': 'Sales Rep',
            'leads_handled': 48,
            'conversions': 13,
            'revenue': '$310,000',
            'satisfaction': 4.8
        }
    ])

    st.dataframe(
        team_data,
        hide_index=True,
        column_config={
            'satisfaction': st.column_config.NumberColumn(
                'Satisfaction',
                format='%.1f ⭐'
            )
        }
    )

    st.divider()

    # Performance charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Conversions by Team Member")

        fig = create_bar_chart(
            data=team_data,
            x='name',
            y='conversions',
            title="Team Conversion Performance",
            color='name'
        )
        st.plotly_chart(fig)

    with col2:
        st.subheader("📈 Leads Handled")

        fig = create_bar_chart(
            data=team_data,
            x='name',
            y='leads_handled',
            title="Lead Distribution Across Team",
            color='name'
        )
        st.plotly_chart(fig)

    st.divider()

    # Activity metrics
    st.subheader("⚡ Activity Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Calls Made", 245, delta=28)
        st.metric("Emails Sent", 456, delta=45)

    with col2:
        st.metric("Appointments Set", 89, delta=12)
        st.metric("Quotes Sent", 67, delta=8)

    with col3:
        st.metric("Follow-ups", 134, delta=15)
        st.metric("Site Visits", 42, delta=5)

    with col4:
        st.metric("Contracts Signed", 24, delta=4)
        st.metric("Customer Meetings", 56, delta=7)

    # Team insights
    st.divider()
    st.subheader("💡 Team Insights")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.success("**Top Performer**\nMary Johnson leads in revenue with $425K")

    with col2:
        st.info("**Most Active**\nRobert Williams handled 52 leads this period")

    with col3:
        st.warning("**Training Opportunity**\nSchedule advanced sales training for team")

    # Export
    st.divider()
    export_to_csv(team_data, "team_productivity")


# Execute the render function
if __name__ == "__main__" or "streamlit" in globals():
    # Initialize session state for date range if not exists
    if 'date_range' not in st.session_state:
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        st.session_state.date_range = (start_date, end_date)

    render()
