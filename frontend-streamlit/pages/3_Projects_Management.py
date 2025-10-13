"""
iSwitch Roofs CRM - Projects Management Page
Real-time project tracking with revenue analytics and premium market insights
Version: 2.0.0
Date: 2025-10-09
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.api_client import get_api_client
from utils.realtime import (
    auto_refresh,
    display_last_updated,
    create_realtime_indicator,
    show_connection_status,
    display_data_source_badge
)
from utils.charts import create_kpi_card
from utils.pusher_script import inject_pusher_script, pusher_status_indicator
from utils.notifications import notification_preferences_sidebar
import plotly.express as px
import plotly.graph_objects as go

# Page config
# Initialize API client
api_client = get_api_client()

# Auto-refresh every 30 seconds
auto_refresh(interval_ms=30000, key="projects_refresh")

# Inject Pusher real-time client (subscribes to projects and customers channels)
inject_pusher_script(channels=['projects', 'customers'], debug=False)

# Custom CSS
st.markdown("""
    <style>
    .kanban-column {
        padding: 15px;
        border-radius: 10px;
        background-color: #f5f5f5;
        min-height: 400px;
        margin-bottom: 20px;
    }
    .project-card {
        padding: 15px;
        border-radius: 8px;
        background-color: white;
        border-left: 4px solid #667eea;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .status-planning { border-left-color: #9c27b0; }
    .status-in-progress { border-left-color: #2196f3; }
    .status-on-hold { border-left-color: #ff9800; }
    .status-completed { border-left-color: #4caf50; }
    .status-cancelled { border-left-color: #f44336; }
    .premium-project-badge {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: white;
        padding: 3px 10px;
        border-radius: 15px;
        font-size: 0.8em;
        font-weight: bold;
        display: inline-block;
        margin-left: 5px;
    }
    .large-deal-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 3px 10px;
        border-radius: 15px;
        font-size: 0.8em;
        font-weight: bold;
        display: inline-block;
        margin-left: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("🏗️ Project Management")
st.markdown("Real-time project tracking with revenue analytics")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    # Connection status
    show_connection_status(api_client)
    create_realtime_indicator(active=True)
    display_last_updated(key="projects_last_updated")

    # Pusher status and notification preferences
    pusher_status_indicator()
    notification_preferences_sidebar()

    st.markdown("---")
    st.header("🔍 Filters")

    # Status filter
    status_options = [
        "All", "Planning", "In Progress",
        "On Hold", "Completed", "Cancelled"
    ]
    status_filter = st.selectbox("Status", status_options)

    # Priority filter
    priority_options = ["All", "Low", "Medium", "High", "Critical"]
    priority_filter = st.selectbox("Priority", priority_options)

    # Project value filter
    st.subheader("Project Value")
    value_range = st.slider(
        "Value range ($)",
        0, 500000, (0, 500000),
        step=10000,
        format="$%d"
    )

    # Market segment filter
    st.subheader("Market Segment")
    segment_options = ["All", "Premium ($35K+)", "Large ($20K+)", "Standard"]
    segment_filter = st.selectbox("Segment", segment_options)

    st.markdown("---")

    # Quick actions
    st.subheader("Quick Actions")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

    if st.button("📥 Export Report", use_container_width=True):
        st.info("Export functionality coming soon!")

    if st.button("📊 Generate Report", use_container_width=True):
        st.info("Report generation coming soon!")

# Search bar
search_query = st.text_input(
    "🔍 Search projects by name, customer, or address...",
    ""
)

# Premium market thresholds
PREMIUM_THRESHOLD = 35000  # Ultra-premium and professional avg
LARGE_DEAL_THRESHOLD = 20000

def get_project_segment(value: float) -> str:
    """Determine project segment based on value"""
    if value >= PREMIUM_THRESHOLD:
        return "premium"
    elif value >= LARGE_DEAL_THRESHOLD:
        return "large"
    return "standard"

def get_segment_badge(value: float) -> str:
    """Get HTML badge for project segment"""
    segment = get_project_segment(value)
    if segment == "premium":
        return '<span class="premium-project-badge">⭐ Premium</span>'
    elif segment == "large":
        return '<span class="large-deal-badge">💼 Large Deal</span>'
    return ""

# Fetch projects data
try:
    response = api_client.get_projects()

    if response and 'data' in response:
        projects_data = response['data']
        display_data_source_badge("live")
    else:
        projects_data = []
        display_data_source_badge("demo")

    if projects_data:
        df = pd.DataFrame(projects_data)

        # Add segment classification
        df['segment'] = df['value'].apply(get_project_segment)

        # Apply filters
        if status_filter != "All":
            df = df[df['status'] == status_filter.lower().replace(" ", "_")]

        if priority_filter != "All":
            df = df[df.get('priority', 'medium') == priority_filter.lower()]

        # Value filter
        df = df[(df['value'] >= value_range[0]) & (df['value'] <= value_range[1])]

        # Segment filter
        if segment_filter != "All":
            if segment_filter == "Premium ($35K+)":
                df = df[df['segment'] == 'premium']
            elif segment_filter == "Large ($20K+)":
                df = df[df['segment'] == 'large']
            elif segment_filter == "Standard":
                df = df[df['segment'] == 'standard']

        if search_query:
            search_mask = (
                df['name'].str.contains(search_query, case=False, na=False) |
                df.get('customer_name', pd.Series(dtype=str)).str.contains(
                    search_query, case=False, na=False
                ) |
                df.get('description', pd.Series(dtype=str)).str.contains(
                    search_query, case=False, na=False
                )
            )
            df = df[search_mask]

        # Calculate metrics
        total_projects = len(df)
        active_count = len(df[df['status'] == 'in_progress'])
        total_value = df['value'].sum()
        completed_count = len(df[df['status'] == 'completed'])
        completion_rate = (
            (completed_count / total_projects * 100) if total_projects > 0 else 0
        )

        # Revenue by status
        revenue_by_status = df.groupby('status')['value'].sum().to_dict()
        planning_revenue = revenue_by_status.get('planning', 0)
        in_progress_revenue = revenue_by_status.get('in_progress', 0)
        completed_revenue = revenue_by_status.get('completed', 0)

        # Premium project metrics
        premium_projects = len(df[df['segment'] == 'premium'])
        premium_revenue = df[df['segment'] == 'premium']['value'].sum()
        premium_avg = (
            premium_revenue / premium_projects if premium_projects > 0 else 0
        )

    else:
        display_data_source_badge("demo")
        st.info("📊 No project data available - Displaying demo metrics")
        total_projects = 0
        active_count = 0
        total_value = 0
        completion_rate = 0
        planning_revenue = 0
        in_progress_revenue = 0
        completed_revenue = 0
        premium_projects = 0
        premium_revenue = 0
        premium_avg = 0

except Exception as e:
    display_data_source_badge("demo")
    st.warning("⚠️ Backend connection unavailable - Displaying demo metrics")
    st.info(f"💡 Error: {str(e)}")
    total_projects = 0
    active_count = 0
    total_value = 0
    completion_rate = 0
    planning_revenue = 0
    in_progress_revenue = 0
    completed_revenue = 0
    premium_projects = 0
    premium_revenue = 0
    premium_avg = 0

# Top metrics with KPI cards
st.header("📊 Project Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    create_kpi_card(
        label="Total Projects",
        value=total_projects,
        format_func=lambda x: f"{int(x)}",
        color="#667eea"
    )

with col2:
    create_kpi_card(
        label="Active Projects",
        value=active_count,
        delta=f"{active_count}/{total_projects} active",
        format_func=lambda x: f"{int(x)}",
        color="#2196f3"
    )

with col3:
    create_kpi_card(
        label="Total Value",
        value=total_value,
        format_func=lambda x: f"${x:,.0f}",
        color="#764ba2"
    )

with col4:
    create_kpi_card(
        label="Completion Rate",
        value=completion_rate,
        format_func=lambda x: f"{x:.1f}%",
        color="#4caf50"
    )

st.markdown("---")

# Revenue breakdown by status
st.header("💰 Revenue by Project Status")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.subheader("📋 Planning")
    st.metric("Revenue Pipeline", f"${planning_revenue:,.0f}")
    planning_count = len(df[df['status'] == 'planning']) if 'df' in locals() else 0
    st.markdown(f"**Projects:** {planning_count}")

with col2:
    st.subheader("🔨 In Progress")
    st.metric("Active Revenue", f"${in_progress_revenue:,.0f}")
    in_prog_count = (
        len(df[df['status'] == 'in_progress']) if 'df' in locals() else 0
    )
    st.markdown(f"**Projects:** {in_prog_count}")

with col3:
    st.subheader("✅ Completed")
    st.metric("Realized Revenue", f"${completed_revenue:,.0f}")
    comp_count = len(df[df['status'] == 'completed']) if 'df' in locals() else 0
    st.markdown(f"**Projects:** {comp_count}")

with col4:
    st.subheader("⭐ Premium")
    st.metric("Premium Projects", premium_projects)
    st.markdown(f"**Revenue:** ${premium_revenue:,.0f}")
    st.markdown(f"**Avg Deal:** ${premium_avg:,.0f}")

st.markdown("---")

# View mode selector
view_mode = st.radio(
    "View Mode",
    ["📊 Kanban Board", "📋 List View", "📈 Analytics", "📅 Timeline"],
    horizontal=True
)

st.markdown("---")

# Display based on view mode
if 'df' in locals() and not df.empty:
    if view_mode == "📊 Kanban Board":
        st.subheader("Kanban Board")

        # Add new project button
        if st.button("➕ Add New Project", type="primary"):
            st.session_state['show_new_project_form'] = True

        # Create Kanban columns
        statuses = [
            ("planning", "📋 Planning"),
            ("in_progress", "🔨 In Progress"),
            ("on_hold", "⏸️ On Hold"),
            ("completed", "✅ Completed"),
            ("cancelled", "❌ Cancelled")
        ]

        cols = st.columns(len(statuses))

        for idx, (status_key, status_label) in enumerate(statuses):
            with cols[idx]:
                st.markdown(f"### {status_label}")

                # Filter projects by status
                status_projects = df[df['status'] == status_key]

                # Display count and total value
                status_value = status_projects['value'].sum()
                st.caption(f"{len(status_projects)} projects | ${status_value:,.0f}")

                if not status_projects.empty:
                    for _, project in status_projects.iterrows():
                        segment_badge = get_segment_badge(project['value'])

                        st.markdown(f"""
                        <div class='project-card status-{status_key}'>
                            <strong>{project['name']}</strong>{segment_badge}<br>
                            <small>{project.get('customer_name', 'Unknown')}</small><br>
                            💰 ${project.get('value', 0):,.0f}<br>
                            📅 {project.get('start_date', 'TBD')}
                        </div>
                        """, unsafe_allow_html=True)

                        if st.button(
                            "View Details",
                            key=f"view_{project['id']}",
                            use_container_width=True
                        ):
                            st.session_state['selected_project_id'] = project['id']
                            st.rerun()
                else:
                    st.info("No projects")

    elif view_mode == "📋 List View":
        st.subheader("Project List")

        # Add new project button
        if st.button("➕ Add New Project", type="primary"):
            st.session_state['show_new_project_form'] = True

        # Sort by value descending
        df_sorted = df.sort_values('value', ascending=False)

        # Display projects as expandable list
        for idx, project in df_sorted.iterrows():
            status_icon = {
                'planning': '📋',
                'in_progress': '🔨',
                'on_hold': '⏸️',
                'completed': '✅',
                'cancelled': '❌'
            }.get(project.get('status', 'planning'), '📋')

            segment_badge = get_segment_badge(project['value'])
            status_display = project.get('status', 'planning').replace('_', ' ').title()

            with st.expander(
                f"{status_icon} {project['name']} - "
                f"${project.get('value', 0):,.0f} - {status_display}"
            ):
                # Display segment badge
                if segment_badge:
                    st.markdown(segment_badge, unsafe_allow_html=True)

                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.write(
                        f"**Customer:** "
                        f"{project.get('customer_name', 'Unknown')}"
                    )
                    st.write(f"**Value:** ${project.get('value', 0):,.2f}")
                    st.write(f"**Start Date:** {project.get('start_date', 'TBD')}")
                    st.write(f"**End Date:** {project.get('end_date', 'TBD')}")

                with col2:
                    st.write(
                        f"**Priority:** "
                        f"{project.get('priority', 'medium').title()}"
                    )
                    st.write(f"**Progress:** {project.get('progress', 0)}%")
                    st.write(f"**Created:** {project.get('created_at', 'N/A')}")
                    st.write(f"**Updated:** {project.get('updated_at', 'N/A')}")

                with col3:
                    if st.button(
                        "View Full Details",
                        key=f"details_{project['id']}"
                    ):
                        st.session_state['selected_project_id'] = project['id']
                        st.rerun()

                    if st.button("Edit", key=f"edit_{project['id']}"):
                        st.session_state['edit_project_id'] = project['id']

                    if st.button("Timeline", key=f"timeline_{project['id']}"):
                        st.info("Timeline view coming soon!")

                if project.get('description'):
                    st.write(f"**Description:** {project['description']}")

    elif view_mode == "📈 Analytics":
        st.subheader("Project Analytics")

        col1, col2 = st.columns(2)

        with col1:
            # Status distribution
            if 'status' in df.columns:
                status_counts = df['status'].value_counts()
                fig = px.pie(
                    values=status_counts.values,
                    names=[s.replace('_', ' ').title() for s in status_counts.index],
                    title="Projects by Status",
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Segment distribution
            if 'segment' in df.columns:
                segment_counts = df['segment'].value_counts()
                segment_labels = {
                    'premium': 'Premium ($35K+)',
                    'large': 'Large ($20K+)',
                    'standard': 'Standard'
                }
                segment_names = [
                    segment_labels.get(s, s) for s in segment_counts.index
                ]
                fig = px.pie(
                    values=segment_counts.values,
                    names=segment_names,
                    title="Projects by Market Segment",
                    hole=0.4,
                    color_discrete_sequence=['#FFD700', '#667eea', '#4CAF50']
                )
                st.plotly_chart(fig, use_container_width=True)

        # Revenue by status
        st.subheader("Revenue Distribution by Status")
        revenue_by_status = df.groupby('status')['value'].sum().reset_index()
        revenue_by_status['status_label'] = revenue_by_status['status'].apply(
            lambda x: x.replace('_', ' ').title()
        )

        fig = px.bar(
            revenue_by_status,
            x='status_label',
            y='value',
            title="Total Revenue by Project Status",
            labels={'status_label': 'Status', 'value': 'Revenue ($)'},
            color='value',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig, use_container_width=True)

        # Average deal size by segment
        st.subheader("Average Deal Size by Segment")
        avg_by_segment = df.groupby('segment')['value'].mean().reset_index()
        avg_by_segment['segment_label'] = avg_by_segment['segment'].map({
            'premium': 'Premium ($35K+)',
            'large': 'Large ($20K+)',
            'standard': 'Standard'
        })

        fig = px.bar(
            avg_by_segment,
            x='segment_label',
            y='value',
            title="Average Deal Size by Market Segment",
            labels={'segment_label': 'Segment', 'value': 'Avg Deal Size ($)'},
            color='value',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)

        # Top projects
        st.subheader("Top 10 Projects by Value")
        top_projects = df.nlargest(10, 'value')[[
            'name', 'customer_name', 'value', 'status', 'segment'
        ]]
        top_projects['segment'] = top_projects['segment'].map({
            'premium': 'Premium',
            'large': 'Large',
            'standard': 'Standard'
        })
        st.dataframe(top_projects, use_container_width=True, hide_index=True)

    elif view_mode == "📅 Timeline":
        st.subheader("Project Timeline")
        st.info("Timeline view will show project Gantt chart - coming soon!")

        # For now, show a simple list sorted by start date
        if 'start_date' in df.columns:
            df_sorted = df.sort_values('start_date')

            for _, project in df_sorted.iterrows():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                with col1:
                    st.write(f"**{project['name']}**")
                with col2:
                    st.write(f"Start: {project.get('start_date', 'TBD')}")
                with col3:
                    st.write(f"End: {project.get('end_date', 'TBD')}")
                with col4:
                    progress = project.get('progress', 0)
                    st.progress(progress / 100 if progress else 0)
else:
    st.info("No projects found. Create your first project to get started!")
    if st.button("➕ Add New Project", type="primary"):
        st.session_state['show_new_project_form'] = True

# New Project Form
if st.session_state.get('show_new_project_form', False):
    st.markdown("---")
    st.subheader("➕ Create New Project")

    with st.form("new_project_form"):
        col1, col2 = st.columns(2)

        with col1:
            project_name = st.text_input("Project Name *")
            customer_id = st.text_input(
                "Customer ID *",
                help="Enter the customer ID for this project"
            )
            start_date = st.date_input("Start Date *")
            end_date = st.date_input("Target End Date")

        with col2:
            project_value = st.number_input(
                "Project Value ($) *",
                min_value=0,
                step=1000
            )
            status = st.selectbox(
                "Status",
                ["Planning", "In Progress", "On Hold", "Completed", "Cancelled"]
            )
            priority = st.selectbox(
                "Priority",
                ["Low", "Medium", "High", "Critical"]
            )

        description = st.text_area("Project Description")

        # Show estimated segment
        if project_value > 0:
            segment = get_project_segment(project_value)
            segment_display = {
                'premium': '⭐ Premium ($35K+)',
                'large': '💼 Large Deal ($20K+)',
                'standard': '✓ Standard'
            }
            st.info(f"**Estimated Segment:** {segment_display[segment]}")

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button(
                "Create Project",
                type="primary",
                use_container_width=True
            )
        with col2:
            if st.form_submit_button("Cancel", use_container_width=True):
                st.session_state['show_new_project_form'] = False
                st.rerun()

        if submitted:
            if not all([project_name, customer_id, start_date, project_value]):
                st.error("Please fill in all required fields marked with *")
            else:
                try:
                    project_data = {
                        "name": project_name,
                        "customer_id": customer_id,
                        "value": project_value,
                        "status": status.lower().replace(" ", "_"),
                        "priority": priority.lower(),
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat() if end_date else None,
                        "description": description
                    }

                    response = api_client.create_project(project_data)

                    if response:
                        st.success("✅ Project created successfully!")
                        st.session_state['show_new_project_form'] = False
                        st.rerun()
                    else:
                        st.error("Failed to create project. Please try again.")
                except Exception as e:
                    st.error(f"Error creating project: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
### 🎯 Project Management Features
- ✅ **Real-Time Updates**: Live project data with 30-second refresh
- ✅ **Revenue Analytics**: Track revenue by project status and segment
- ✅ **Premium Classification**: Automatic project segmentation ($35K+ premium)
- ✅ **Kanban Board**: Visual project pipeline management
- ✅ **Performance Metrics**: Completion rates and revenue tracking

### 💰 Revenue Growth Targets
- **Planning Pipeline**: Projects in design and estimation phase
- **Active Revenue**: In-progress projects generating cash flow
- **Realized Revenue**: Completed projects contributing to growth
- **Premium Focus**: Target $35K+ average deals for premium markets
""")
