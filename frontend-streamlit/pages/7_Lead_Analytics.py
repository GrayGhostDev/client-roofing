"""
Lead Analytics Page
Detailed lead analysis and tracking
"""

import streamlit as st
import pandas as pd
from utils.api_client import get_api_client
from utils.visualization import (
    create_kpi_cards,
    create_bar_chart,
    create_line_chart,
    create_pie_chart,
    format_currency,
    export_to_csv,
    export_to_excel
)


def render():
    """Render the lead analytics page"""
    st.title("🎯 Lead Analytics")
    st.markdown("Comprehensive lead tracking and conversion analysis")

    # Get date range
    start_date, end_date = st.session_state.date_range
    api = get_api_client()

    # Try to fetch real data from API
    try:
        leads_from_api = api.get_leads(start_date=start_date, end_date=end_date)
        if leads_from_api and len(leads_from_api) > 0:
            st.success(f"✅ Loaded {len(leads_from_api)} leads from API")
        else:
            st.info("📊 Displaying demo data - Connect to CRM backend for real-time lead analytics")
    except Exception as e:
        st.info("📊 Displaying demo data - Connect to CRM backend for real-time lead analytics")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox(
            "Lead Status",
            ["All", "New", "Contacted", "Qualified", "Quoted", "Converted", "Lost"]
        )
    with col2:
        source_filter = st.selectbox(
            "Lead Source",
            ["All", "Website", "Referral", "Social Media", "Direct", "Other"]
        )
    with col3:
        score_filter = st.select_slider(
            "Lead Score Range",
            options=["All", "0-25", "26-50", "51-75", "76-100"],
            value="All"
        )

    st.divider()

    # Lead Statistics KPIs
    st.subheader("📊 Lead Performance Metrics")

    lead_kpis = [
        {'label': 'Total Leads', 'value': 245, 'delta': 18},
        {'label': 'Hot Leads', 'value': 67, 'delta': 5},
        {'label': 'Conversion Rate', 'value': '27.3%', 'delta': '2.1%'},
        {'label': 'Avg Lead Value', 'value': format_currency(23500), 'delta': format_currency(1200)}
    ]

    create_kpi_cards(lead_kpis)

    st.divider()

    # Two column layout
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Leads by Status")

        status_data = pd.DataFrame([
            {'status': 'New', 'count': 45},
            {'status': 'Contacted', 'count': 38},
            {'status': 'Qualified', 'count': 52},
            {'status': 'Quoted', 'count': 35},
            {'status': 'Converted', 'count': 42},
            {'status': 'Lost', 'count': 33}
        ])

        fig_status = create_bar_chart(
            data=status_data,
            x='status',
            y='count',
            title="Lead Distribution by Status",
            color='status'
        )
        st.plotly_chart(fig_status)

    with col2:
        st.subheader("🌐 Leads by Source")

        source_data = pd.DataFrame([
            {'source': 'Website', 'count': 89},
            {'source': 'Referral', 'count': 67},
            {'source': 'Social Media', 'count': 45},
            {'source': 'Direct', 'count': 28},
            {'source': 'Other', 'count': 16}
        ])

        fig_source = create_pie_chart(
            data=source_data,
            values='count',
            names='source',
            title="Lead Source Distribution"
        )
        st.plotly_chart(fig_source)

    st.divider()

    # Lead trend over time
    st.subheader("📊 Lead Acquisition Trend")

    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    trend_data = pd.DataFrame({
        'date': date_range,
        'new_leads': [5 + (i % 7) for i in range(len(date_range))],
        'qualified_leads': [3 + (i % 5) for i in range(len(date_range))],
        'converted_leads': [1 + (i % 3) for i in range(len(date_range))]
    })

    trend_melted = trend_data.melt(
        id_vars=['date'],
        value_vars=['new_leads', 'qualified_leads', 'converted_leads'],
        var_name='status',
        value_name='count'
    )

    fig_trend = create_line_chart(
        data=trend_melted,
        x='date',
        y='count',
        title="Daily Lead Activity",
        color='status'
    )
    st.plotly_chart(fig_trend)

    st.divider()

    # Lead details table
    st.subheader("📋 Lead Details")

    leads_data = pd.DataFrame([
        {
            'id': 'L001',
            'name': 'John Smith',
            'source': 'Website',
            'status': 'Qualified',
            'score': 85,
            'value': '$28,500',
            'created': '2025-10-01',
            'last_contact': '2025-10-05'
        },
        {
            'id': 'L002',
            'name': 'Mary Johnson',
            'source': 'Referral',
            'status': 'Quoted',
            'score': 92,
            'value': '$35,000',
            'created': '2025-09-28',
            'last_contact': '2025-10-04'
        },
        {
            'id': 'L003',
            'name': 'Robert Williams',
            'source': 'Social Media',
            'status': 'New',
            'score': 65,
            'value': '$18,000',
            'created': '2025-10-05',
            'last_contact': '2025-10-05'
        },
        {
            'id': 'L004',
            'name': 'Patricia Brown',
            'source': 'Direct',
            'status': 'Contacted',
            'score': 78,
            'value': '$22,000',
            'created': '2025-10-02',
            'last_contact': '2025-10-05'
        },
        {
            'id': 'L005',
            'name': 'Michael Davis',
            'source': 'Website',
            'status': 'Converted',
            'score': 95,
            'value': '$42,000',
            'created': '2025-09-25',
            'last_contact': '2025-10-03'
        }
    ])

    # Search and filter
    search = st.text_input("🔍 Search leads", placeholder="Search by name, ID, or source...")

    if search:
        leads_data = leads_data[
            leads_data.apply(lambda row: search.lower() in str(row).lower(), axis=1)
        ]

    st.dataframe(
        leads_data,
        hide_index=True,
        column_config={
            'score': st.column_config.ProgressColumn(
                'Score',
                min_value=0,
                max_value=100,
                format='%d'
            ),
            'value': st.column_config.TextColumn('Est. Value')
        }
    )

    # Lead insights
    st.divider()
    st.subheader("💡 Key Insights")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("**Best Performing Source**\nWebsite leads have the highest conversion rate at 32%")

    with col2:
        st.warning("**Attention Needed**\n33 leads haven't been contacted in 3+ days")

    with col3:
        st.success("**Top Opportunity**\n5 high-value leads ready for quotes")

    # Export options
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        export_to_csv(leads_data, "lead_analytics")

    with col2:
        export_to_excel(leads_data, "lead_analytics")

    with col3:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()


# Execute the render function
if __name__ == "__main__" or "streamlit" in globals():
    # Initialize session state for date range if not exists
    if 'date_range' not in st.session_state:
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        st.session_state.date_range = (start_date, end_date)

    render()
