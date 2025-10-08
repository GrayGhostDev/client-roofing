"""
Custom Reports Page
Create and export custom reports with flexible filtering
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from utils.visualization import (
    create_bar_chart,
    create_line_chart,
    create_pie_chart,
    format_currency,
    export_to_csv,
    export_to_excel
)


def render():
    """Render the custom reports page"""
    st.title("📈 Custom Reports")
    st.markdown("Build custom reports with flexible filtering and export options")
    
    # Report builder
    st.subheader("🔧 Report Builder")
    
    col1, col2 = st.columns(2)
    
    with col1:
        report_type = st.selectbox(
            "Report Type",
            [
                "Executive Summary",
                "Lead Performance",
                "Sales Activity",
                "Project Status",
                "Revenue Analysis",
                "Team Performance",
                "Custom Query"
            ]
        )
    
    with col2:
        report_format = st.selectbox(
            "Export Format",
            ["PDF", "Excel", "CSV", "JSON"]
        )
    
    st.divider()
    
    # Filters
    with st.expander("🔍 Advanced Filters", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            metric_filter = st.multiselect(
                "Metrics to Include",
                ["Revenue", "Leads", "Conversions", "Projects", "Team Activity"],
                default=["Revenue", "Leads"]
            )
        
        with col2:
            groupby_filter = st.selectbox(
                "Group By",
                ["Date", "Source", "Team Member", "Status", "Customer Type"]
            )
        
        with col3:
            aggregation = st.selectbox(
                "Aggregation",
                ["Sum", "Average", "Count", "Min", "Max"]
            )
        
        # Additional filters
        col1, col2 = st.columns(2)
        
        with col1:
            include_charts = st.checkbox("Include Visualizations", value=True)
        
        with col2:
            include_summary = st.checkbox("Include Summary Statistics", value=True)
    
    st.divider()
    
    # Generate report preview
    if st.button("🔍 Generate Preview", type="primary"):
        with st.spinner("Generating report..."):
            generate_report_preview(report_type, metric_filter, groupby_filter)
    
    st.divider()
    
    # Saved reports
    st.subheader("📁 Saved Reports")
    
    saved_reports = pd.DataFrame([
        {
            'name': 'Weekly Executive Summary',
            'type': 'Executive Summary',
            'created': '2025-10-01',
            'last_run': '2025-10-06',
            'frequency': 'Weekly'
        },
        {
            'name': 'Monthly Revenue Report',
            'type': 'Revenue Analysis',
            'created': '2025-09-15',
            'last_run': '2025-10-01',
            'frequency': 'Monthly'
        },
        {
            'name': 'Lead Conversion Analysis',
            'type': 'Lead Performance',
            'created': '2025-09-20',
            'last_run': '2025-10-05',
            'frequency': 'Bi-weekly'
        },
        {
            'name': 'Team Performance Review',
            'type': 'Team Performance',
            'created': '2025-09-10',
            'last_run': '2025-10-03',
            'frequency': 'Monthly'
        }
    ])
    
    st.dataframe(
        saved_reports,
        hide_index=True,
        column_config={
            'name': st.column_config.TextColumn('Report Name'),
            'type': st.column_config.TextColumn('Type'),
            'created': st.column_config.DateColumn('Created'),
            'last_run': st.column_config.DateColumn('Last Run'),
            'frequency': st.column_config.TextColumn('Frequency')
        }
    )
    
    # Quick actions
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("▶️ Run Selected"):
            st.success("Report generated successfully!")
    
    with col2:
        if st.button("📅 Schedule"):
            st.info("Schedule report dialog")
    
    with col3:
        if st.button("✏️ Edit"):
            st.info("Edit report configuration")
    
    with col4:
        if st.button("🗑️ Delete"):
            st.warning("Confirm deletion")
    
    st.divider()
    
    # Report templates
    st.subheader("📋 Report Templates")
    
    templates = [
        {
            'name': 'Executive Dashboard',
            'description': 'High-level metrics for C-suite',
            'metrics': 'Revenue, Conversion Rate, Project Status'
        },
        {
            'name': 'Sales Pipeline',
            'description': 'Detailed lead and opportunity tracking',
            'metrics': 'Leads by Stage, Win Rate, Average Deal Size'
        },
        {
            'name': 'Project Performance',
            'description': 'Project health and completion metrics',
            'metrics': 'On-time Rate, Budget vs Actual, Quality Scores'
        },
        {
            'name': 'Team Productivity',
            'description': 'Individual and team performance',
            'metrics': 'Activity Levels, Response Times, Conversions'
        }
    ]
    
    cols = st.columns(2)
    for idx, template in enumerate(templates):
        with cols[idx % 2]:
            with st.container(border=True):
                st.subheader(template['name'])
                st.caption(template['description'])
                st.write(f"**Includes:** {template['metrics']}")
                if st.button(f"Use Template", key=f"template_{idx}"):
                    st.success(f"Template '{template['name']}' loaded!")
    
    st.divider()
    
    # Scheduled reports
    st.subheader("📅 Scheduled Reports")
    
    st.info("""
    **Automated Report Delivery**
    - Configure reports to run automatically
    - Deliver via email or save to cloud storage
    - Set custom schedules (daily, weekly, monthly)
    - Include multiple recipients
    """)
    
    if st.button("➕ Add Scheduled Report"):
        st.success("Schedule configuration wizard opened")


def generate_report_preview(report_type: str, metrics: list, groupby: str):
    """Generate a preview of the selected report"""
    st.success(f"✅ Report generated: {report_type}")
    
    # Sample data based on report type
    if report_type == "Executive Summary":
        st.subheader("Executive Summary Report")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Revenue", format_currency(850000))
        with col2:
            st.metric("New Leads", 245)
        with col3:
            st.metric("Conversion Rate", "27.3%")
        with col4:
            st.metric("Active Projects", 34)
        
        # Chart
        data = pd.DataFrame({
            'month': ['Jul', 'Aug', 'Sep', 'Oct'],
            'revenue': [650000, 720000, 790000, 850000]
        })
        
        fig = create_bar_chart(
            data=data,
            x='month',
            y='revenue',
            title="Monthly Revenue Trend",
            color='month'
        )
        st.plotly_chart(fig)
    
    elif report_type == "Lead Performance":
        st.subheader("Lead Performance Report")
        
        leads_data = pd.DataFrame([
            {'source': 'Website', 'leads': 89, 'conversions': 24, 'rate': '27%'},
            {'source': 'Referral', 'leads': 67, 'conversions': 22, 'rate': '33%'},
            {'source': 'Social', 'leads': 45, 'conversions': 10, 'rate': '22%'},
            {'source': 'Direct', 'leads': 28, 'conversions': 8, 'rate': '29%'}
        ])
        
        st.dataframe(leads_data, hide_index=True)
        
        fig = create_pie_chart(
            data=leads_data,
            values='leads',
            names='source',
            title="Lead Distribution by Source"
        )
        st.plotly_chart(fig)
    
    else:
        st.info(f"Preview for {report_type} with metrics: {', '.join(metrics)}")
        st.write(f"Grouped by: {groupby}")
    
    # Export options
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sample_data = pd.DataFrame({'metric': ['Revenue', 'Leads'], 'value': [850000, 245]})
        export_to_csv(sample_data, "custom_report")
    
    with col2:
        export_to_excel(sample_data, "custom_report")
    
    with col3:
        if st.button("📧 Email Report"):
            st.success("Report sent via email!")
