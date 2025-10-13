"""
Project Performance Page
Track project progress, completion rates, and profitability
"""

import streamlit as st
import pandas as pd
from utils.visualization import (
    create_kpi_cards,
    create_bar_chart,
    create_gauge_chart,
    format_currency,
    export_to_csv
)


def render():
    """Render the project performance page"""
    st.title("🏗️ Project Performance")
    st.markdown("Monitor project progress, completion rates, and profitability metrics")

    start_date, end_date = st.session_state.date_range

    # Show demo data notice
    st.info("📊 Displaying demo project data - Connect to CRM backend for real-time project tracking")

    # Project KPIs
    st.subheader("📊 Project Metrics")

    project_kpis = [
        {'label': 'Active Projects', 'value': 34, 'delta': 5},
        {'label': 'Completed Projects', 'value': 28, 'delta': 4},
        {'label': 'On-Time Completion', 'value': '92%', 'delta': '3%'},
        {'label': 'Project Revenue', 'value': format_currency(850000), 'delta': format_currency(120000)}
    ]

    create_kpi_cards(project_kpis)

    st.divider()

    # Project status and performance
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Projects by Status")

        status_data = pd.DataFrame([
            {'status': 'Planning', 'count': 8},
            {'status': 'In Progress', 'count': 18},
            {'status': 'Quality Check', 'count': 5},
            {'status': 'Completed', 'count': 28},
            {'status': 'On Hold', 'count': 3}
        ])

        fig = create_bar_chart(
            data=status_data,
            x='status',
            y='count',
            title="Project Status Distribution",
            color='status'
        )
        st.plotly_chart(fig)

    with col2:
        st.subheader("⚡ Completion Rate")

        fig_gauge = create_gauge_chart(
            value=92,
            title="On-Time Completion Rate",
            max_value=100,
            thresholds={'low': 70, 'medium': 85, 'high': 95}
        )
        st.plotly_chart(fig_gauge)

        st.metric("Avg Project Duration", "14 days")
        st.metric("Customer Satisfaction", "4.8/5.0")

    st.divider()

    # Project details table
    st.subheader("📋 Active Projects")

    projects_data = pd.DataFrame([
        {
            'id': 'P001',
            'customer': 'Acme Corp',
            'type': 'Commercial Roof',
            'status': 'In Progress',
            'progress': 65,
            'value': '$85,000',
            'start_date': '2025-09-15',
            'due_date': '2025-10-15'
        },
        {
            'id': 'P002',
            'customer': 'Smith Residence',
            'type': 'Residential Repair',
            'status': 'Quality Check',
            'progress': 95,
            'value': '$15,000',
            'start_date': '2025-10-01',
            'due_date': '2025-10-10'
        },
        {
            'id': 'P003',
            'customer': 'Tech Park Plaza',
            'type': 'Commercial Install',
            'status': 'In Progress',
            'progress': 45,
            'value': '$125,000',
            'start_date': '2025-09-20',
            'due_date': '2025-11-01'
        },
        {
            'id': 'P004',
            'customer': 'Johnson Home',
            'type': 'Residential Roof',
            'status': 'Planning',
            'progress': 15,
            'value': '$25,000',
            'start_date': '2025-10-05',
            'due_date': '2025-10-25'
        },
        {
            'id': 'P005',
            'customer': 'Retail Center',
            'type': 'Commercial Repair',
            'status': 'In Progress',
            'progress': 78,
            'value': '$55,000',
            'start_date': '2025-09-25',
            'due_date': '2025-10-18'
        }
    ])

    st.dataframe(
        projects_data,
        hide_index=True,
        column_config={
            'progress': st.column_config.ProgressColumn(
                'Progress',
                min_value=0,
                max_value=100,
                format='%d%%'
            )
        }
    )

    # Profitability analysis
    st.divider()
    st.subheader("💰 Profitability Analysis")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Project Value", format_currency(305000))
    with col2:
        st.metric("Avg Profit Margin", "28%")
    with col3:
        st.metric("Material Costs", format_currency(195000))
    with col4:
        st.metric("Labor Costs", format_currency(75000))

    # Export
    st.divider()
    col1, col2 = st.columns([1, 3])

    with col1:
        export_to_csv(projects_data, "project_performance")


# Execute the render function
if __name__ == "__main__" or "streamlit" in globals():
    # Initialize session state for date range if not exists
    if 'date_range' not in st.session_state:
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        st.session_state.date_range = (start_date, end_date)

    render()
