"""
iSwitch Roofs CRM - Appointments & Scheduling Page
Real-time appointment management with calendar view and reminder system
Version: 2.0.0
Date: 2025-10-09
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
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
import calendar

# Page config
# Initialize API client
api_client = get_api_client()

# Auto-refresh every 30 seconds
auto_refresh(interval_ms=30000, key="appointments_refresh")

# Inject Pusher real-time client (subscribes to appointments, team, leads channels)
inject_pusher_script(channels=['appointments', 'team', 'leads'], debug=False)

# Custom CSS
st.markdown("""
    <style>
    .appointment-card {
        padding: 12px;
        border-radius: 8px;
        background-color: white;
        border-left: 4px solid #667eea;
        margin-bottom: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .type-inspection { border-left-color: #2196f3; }
    .type-consultation { border-left-color: #9c27b0; }
    .type-followup { border-left-color: #ff9800; }
    .type-installation { border-left-color: #4caf50; }
    .type-maintenance { border-left-color: #607d8b; }

    .calendar-day {
        border: 1px solid #ddd;
        padding: 8px;
        min-height: 80px;
        background-color: white;
        border-radius: 4px;
    }
    .calendar-day-header {
        font-weight: bold;
        text-align: center;
        padding: 8px;
        background-color: #667eea;
        color: white;
    }
    .status-scheduled { background-color: #e3f2fd; }
    .status-confirmed { background-color: #e8f5e9; }
    .status-completed { background-color: #f1f8e9; }
    .status-cancelled { background-color: #ffebee; }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("📅 Appointments & Scheduling")
st.markdown("Real-time appointment management with automated reminders")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    # Connection status
    show_connection_status(api_client)
    create_realtime_indicator(active=True)
    display_last_updated(key="appointments_last_updated")

    # Pusher status and notification preferences
    pusher_status_indicator()
    notification_preferences_sidebar()

    st.markdown("---")
    st.header("🔍 Filters")

    # View type
    view_type = st.selectbox("View Type", ["Calendar", "List", "Schedule"])

    # Status filter
    status_options = [
        "All", "Scheduled", "Confirmed",
        "Completed", "Cancelled", "No-Show"
    ]
    status_filter = st.selectbox("Status", status_options)

    # Appointment type filter
    type_options = [
        "All", "Inspection", "Consultation",
        "Follow-up", "Installation", "Maintenance"
    ]
    type_filter = st.selectbox("Type", type_options)

    # Date range
    st.subheader("Date Range")
    date_start = st.date_input("From", value=datetime.now())
    date_end = st.date_input("To", value=datetime.now() + timedelta(days=30))

    # Technician filter (if available)
    st.subheader("Technician")
    technician_filter = st.selectbox(
        "Assigned To",
        ["All", "Unassigned", "John Doe", "Jane Smith", "Mike Johnson"]
    )

    st.markdown("---")

    # Quick actions
    st.subheader("Quick Actions")
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

    if st.button("📥 Export Schedule", use_container_width=True):
        st.info("Export functionality coming soon!")

    if st.button("📧 Send Reminders", use_container_width=True):
        st.info("Reminder system coming soon!")

# Search bar
search_query = st.text_input(
    "🔍 Search appointments by customer name, address, or notes...",
    ""
)

# Fetch appointments data
try:
    response = api_client.get_appointments()

    if response and 'data' in response:
        appointments_data = response['data']
        display_data_source_badge("live")
    else:
        appointments_data = []
        display_data_source_badge("demo")

    if appointments_data:
        df = pd.DataFrame(appointments_data)

        # Apply filters
        if status_filter != "All":
            df = df[df['status'] == status_filter.lower()]

        if type_filter != "All":
            df = df[df.get('type', 'inspection') == type_filter.lower()]

        if technician_filter != "All":
            if technician_filter == "Unassigned":
                df = df[df.get('technician').isna() | (df.get('technician') == '')]
            else:
                df = df[df.get('technician') == technician_filter]

        # Date range filter
        if 'scheduled_date' in df.columns:
            df['date_obj'] = pd.to_datetime(df['scheduled_date']).dt.date
            df = df[
                (df['date_obj'] >= date_start) &
                (df['date_obj'] <= date_end)
            ]

        if search_query:
            search_mask = (
                df.get('customer_name', pd.Series(dtype=str)).str.contains(
                    search_query, case=False, na=False
                ) |
                df.get('notes', pd.Series(dtype=str)).str.contains(
                    search_query, case=False, na=False
                ) |
                df.get('address', pd.Series(dtype=str)).str.contains(
                    search_query, case=False, na=False
                )
            )
            df = df[search_mask]

        # Calculate metrics
        total_appointments = len(df)
        today = datetime.now().date()
        today_count = len(df[df.get('date_obj') == today]) if 'date_obj' in df.columns else 0

        # This week
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        week_count = len(
            df[
                (df.get('date_obj') >= week_start) &
                (df.get('date_obj') <= week_end)
            ]
        ) if 'date_obj' in df.columns else 0

        confirmed_count = len(df[df['status'] == 'confirmed'])
        completed_count = len(df[df['status'] == 'completed'])
        completion_rate = (
            (completed_count / total_appointments * 100)
            if total_appointments > 0 else 0
        )

    else:
        display_data_source_badge("demo")
        st.info("📊 No appointment data available - Displaying demo metrics")
        total_appointments = 0
        today_count = 0
        week_count = 0
        confirmed_count = 0
        completion_rate = 0

except Exception as e:
    display_data_source_badge("demo")
    st.warning("⚠️ Backend connection unavailable - Displaying demo metrics")
    st.info(f"💡 Error: {str(e)}")
    total_appointments = 0
    today_count = 0
    week_count = 0
    confirmed_count = 0
    completion_rate = 0

# Top metrics with KPI cards
st.header("📊 Appointment Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    create_kpi_card(
        label="Today's Appointments",
        value=today_count,
        format_func=lambda x: f"{int(x)}",
        color="#2196f3"
    )

with col2:
    create_kpi_card(
        label="This Week",
        value=week_count,
        format_func=lambda x: f"{int(x)}",
        color="#667eea"
    )

with col3:
    create_kpi_card(
        label="Confirmed",
        value=confirmed_count,
        delta=f"{confirmed_count}/{total_appointments} total",
        format_func=lambda x: f"{int(x)}",
        color="#4caf50"
    )

with col4:
    create_kpi_card(
        label="Completion Rate",
        value=completion_rate,
        format_func=lambda x: f"{x:.1f}%",
        color="#764ba2"
    )

st.markdown("---")

# Add new appointment button
if st.button("➕ Schedule New Appointment", type="primary"):
    st.session_state['show_new_appointment_form'] = True

st.markdown("---")

# Display based on view type
if 'df' in locals() and not df.empty:
    if view_type == "Calendar":
        st.subheader("📅 Calendar View")

        # Month/Year selector
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            selected_month = st.selectbox(
                "Month",
                range(1, 13),
                index=datetime.now().month - 1,
                format_func=lambda x: calendar.month_name[x]
            )
        with col2:
            selected_year = st.selectbox("Year", range(2023, 2027), index=2)
        with col3:
            if st.button("Today"):
                selected_month = datetime.now().month
                selected_year = datetime.now().year
                st.rerun()

        # Generate calendar
        cal = calendar.monthcalendar(selected_year, selected_month)

        # Display calendar header
        cols = st.columns(7)
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for idx, day_name in enumerate(day_names):
            cols[idx].markdown(
                f"<div class='calendar-day-header'>{day_name}</div>",
                unsafe_allow_html=True
            )

        # Display calendar days with appointments
        for week in cal:
            cols = st.columns(7)
            for idx, day in enumerate(week):
                if day == 0:
                    cols[idx].markdown(
                        "<div class='calendar-day'></div>",
                        unsafe_allow_html=True
                    )
                else:
                    # Get appointments for this day
                    day_date = datetime(selected_year, selected_month, day).date()
                    day_appointments = df[
                        df.get('date_obj') == day_date
                    ] if 'date_obj' in df.columns else pd.DataFrame()

                    with cols[idx]:
                        # Highlight today
                        today_class = (
                            " style='background-color: #fffde7;'"
                            if day_date == datetime.now().date() else ""
                        )
                        st.markdown(
                            f"<div class='calendar-day'{today_class}>"
                            f"<strong>{day}</strong>",
                            unsafe_allow_html=True
                        )
                        if not day_appointments.empty:
                            st.caption(f"{len(day_appointments)} apt(s)")
                            for _, apt in day_appointments.head(2).iterrows():
                                st.caption(
                                    f"• {apt.get('scheduled_time', 'TBD')[:5]}"
                                )
                        st.markdown("</div>", unsafe_allow_html=True)

    elif view_type == "List":
        st.subheader("📋 Appointment List")

        # Sort by date and time
        if 'scheduled_date' in df.columns:
            df_sorted = df.sort_values(['scheduled_date', 'scheduled_time'])
        else:
            df_sorted = df

        # Display appointments
        for idx, appointment in df_sorted.iterrows():
            type_class = f"type-{appointment.get('type', 'inspection')}"
            status_emoji = {
                'scheduled': '📅',
                'confirmed': '✅',
                'completed': '✔️',
                'cancelled': '❌',
                'no-show': '⚠️'
            }.get(appointment.get('status', 'scheduled'), '📅')

            with st.expander(
                f"{status_emoji} {appointment.get('customer_name', 'Unknown')} - "
                f"{appointment.get('scheduled_date', 'TBD')} "
                f"{appointment.get('scheduled_time', '')[:5]}"
            ):
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.write(
                        f"**Customer:** "
                        f"{appointment.get('customer_name', 'Unknown')}"
                    )
                    st.write(
                        f"**Type:** "
                        f"{appointment.get('type', 'inspection').title()}"
                    )
                    st.write(
                        f"**Date:** "
                        f"{appointment.get('scheduled_date', 'TBD')}"
                    )
                    st.write(
                        f"**Time:** "
                        f"{appointment.get('scheduled_time', 'TBD')}"
                    )

                with col2:
                    st.write(
                        f"**Status:** "
                        f"{appointment.get('status', 'scheduled').title()}"
                    )
                    st.write(
                        f"**Technician:** "
                        f"{appointment.get('technician', 'Unassigned')}"
                    )
                    st.write(
                        f"**Duration:** "
                        f"{appointment.get('duration', 60)} minutes"
                    )
                    st.write(
                        f"**Address:** "
                        f"{appointment.get('address', 'N/A')}"
                    )

                with col3:
                    if appointment.get('status') == 'scheduled':
                        if st.button(
                            "Confirm",
                            key=f"confirm_{appointment['id']}"
                        ):
                            st.info("Confirmation feature coming soon!")

                    if st.button(
                        "Reschedule",
                        key=f"reschedule_{appointment['id']}"
                    ):
                        st.info("Reschedule feature coming soon!")

                    if st.button("Cancel", key=f"cancel_{appointment['id']}"):
                        st.warning("Cancel feature coming soon!")

                if appointment.get('notes'):
                    st.write(f"**Notes:** {appointment['notes']}")

    elif view_type == "Schedule":
        st.subheader("🕐 Daily Schedule")

        # Date selector
        selected_date = st.date_input("Select Date", value=datetime.now())

        # Filter appointments for selected date
        day_appointments = df[
            df.get('date_obj') == selected_date
        ] if 'date_obj' in df.columns else pd.DataFrame()

        if not day_appointments.empty:
            st.info(
                f"📅 {len(day_appointments)} appointment(s) on "
                f"{selected_date.strftime('%A, %B %d, %Y')}"
            )

            # Sort by time
            if 'scheduled_time' in day_appointments.columns:
                day_appointments = day_appointments.sort_values('scheduled_time')

            # Create timeline view
            for hour in range(8, 19):  # 8 AM to 7 PM
                st.markdown(f"### {hour:02d}:00")

                # Find appointments at this hour
                hour_appointments = day_appointments[
                    day_appointments.get('scheduled_time', '').str.startswith(
                        f"{hour:02d}:"
                    )
                ] if 'scheduled_time' in day_appointments.columns else pd.DataFrame()

                if not hour_appointments.empty:
                    for _, apt in hour_appointments.iterrows():
                        type_class = f"type-{apt.get('type', 'inspection')}"
                        status_badge = apt.get('status', 'scheduled').title()

                        st.markdown(f"""
                        <div class='appointment-card {type_class}'>
                            <strong>{apt.get('scheduled_time', 'TBD')[:5]} -
                            {apt.get('customer_name', 'Unknown')}</strong>
                            <span style='float: right;
                            background-color: #e3f2fd;
                            padding: 2px 8px;
                            border-radius: 12px;
                            font-size: 0.85em;'>
                            {status_badge}</span><br>
                            {apt.get('type', 'inspection').title()} |
                            {apt.get('duration', 60)} min<br>
                            📍 {apt.get('address', 'N/A')}<br>
                            👤 {apt.get('technician', 'Unassigned')}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.caption("No appointments")

                st.markdown("---")
        else:
            st.info(f"No appointments scheduled for {selected_date}")
else:
    st.info("No appointments found. Schedule your first appointment!")
    if st.button("➕ Schedule New Appointment", type="primary", key="empty_state"):
        st.session_state['show_new_appointment_form'] = True

# New Appointment Form
if st.session_state.get('show_new_appointment_form', False):
    st.markdown("---")
    st.subheader("➕ Schedule New Appointment")

    with st.form("new_appointment_form"):
        col1, col2 = st.columns(2)

        with col1:
            customer_id = st.text_input(
                "Customer ID *",
                help="Enter the customer or lead ID"
            )
            appointment_type = st.selectbox(
                "Type *",
                [
                    "Inspection", "Consultation", "Follow-up",
                    "Installation", "Maintenance"
                ]
            )
            appointment_date = st.date_input("Date *")
            appointment_time = st.time_input("Time *", value=time(9, 0))

        with col2:
            duration = st.number_input(
                "Duration (minutes) *",
                min_value=15,
                max_value=480,
                value=60,
                step=15
            )
            technician = st.selectbox(
                "Assign To",
                ["Unassigned", "John Doe", "Jane Smith", "Mike Johnson"]
            )
            address = st.text_input("Address *")
            status = st.selectbox("Status", ["Scheduled", "Confirmed"])

        notes = st.text_area(
            "Notes",
            placeholder="Add any special instructions or notes..."
        )

        # Reminder options
        st.subheader("Reminders")
        col1, col2 = st.columns(2)
        with col1:
            email_reminder = st.checkbox("Send email reminder", value=True)
        with col2:
            sms_reminder = st.checkbox("Send SMS reminder", value=False)

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button(
                "Schedule Appointment",
                type="primary",
                use_container_width=True
            )
        with col2:
            if st.form_submit_button("Cancel", use_container_width=True):
                st.session_state['show_new_appointment_form'] = False
                st.rerun()

        if submitted:
            required_fields = [
                customer_id,
                appointment_type,
                appointment_date,
                appointment_time,
                address
            ]
            if not all(required_fields):
                st.error("Please fill in all required fields marked with *")
            else:
                try:
                    appointment_data = {
                        "customer_id": customer_id,
                        "type": appointment_type.lower(),
                        "scheduled_date": appointment_date.isoformat(),
                        "scheduled_time": appointment_time.strftime("%H:%M"),
                        "duration": duration,
                        "technician": (
                            technician if technician != "Unassigned" else None
                        ),
                        "address": address,
                        "status": status.lower(),
                        "notes": notes,
                        "email_reminder": email_reminder,
                        "sms_reminder": sms_reminder
                    }

                    response = api_client.create_appointment(appointment_data)

                    if response:
                        st.success("✅ Appointment scheduled successfully!")
                        st.session_state['show_new_appointment_form'] = False
                        st.rerun()
                    else:
                        st.error("Failed to schedule appointment. Please try again.")
                except Exception as e:
                    st.error(f"Error scheduling appointment: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
### 🎯 Appointment Management Features
- ✅ **Real-Time Updates**: Live appointment data with 30-second refresh
- ✅ **Calendar View**: Visual monthly calendar with appointment counts
- ✅ **Daily Schedule**: Hour-by-hour timeline for efficient planning
- ✅ **Reminder System**: Automated email and SMS reminders (coming soon)
- ✅ **Status Tracking**: Monitor scheduled, confirmed, and completed appointments

### 💡 Best Practices
- **Confirm appointments** 24 hours in advance to reduce no-shows
- **Send reminders** via email and SMS for better attendance
- **Allow buffer time** between appointments for travel
- **Track technician availability** to optimize scheduling
- **Use appointment types** to categorize and filter appointments
- **Add detailed notes** for better preparation and communication
""")
