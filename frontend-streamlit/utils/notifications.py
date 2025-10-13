"""
Toast Notification System for Streamlit
Version: 1.0.0
Date: 2025-10-09

Provides toast notifications for real-time events using streamlit-extras.
"""

import streamlit as st
from streamlit_extras.let_it_rain import rain
from typing import Optional, Dict, Any


def show_toast(
    message: str,
    icon: str = "ℹ️",
    duration: int = 3,
    type: str = "info"
):
    """
    Display a toast notification

    Args:
        message: Message to display
        icon: Emoji icon
        duration: Display duration in seconds
        type: Toast type (success, info, warning, error)
    """
    # Streamlit doesn't have native toasts, so we use st.toast (if available in newer versions)
    # or display as a temporary message

    if hasattr(st, 'toast'):
        st.toast(f"{icon} {message}", icon=icon)
    else:
        # Fallback: Use colored message
        if type == "success":
            st.success(f"{icon} {message}")
        elif type == "error":
            st.error(f"{icon} {message}")
        elif type == "warning":
            st.warning(f"{icon} {message}")
        else:
            st.info(f"{icon} {message}")


def show_lead_notification(lead_data: Dict[str, Any]):
    """
    Show notification for new lead

    Args:
        lead_data: Lead data from Pusher event
    """
    name = lead_data.get("name", "Unknown")
    source = lead_data.get("source", "Unknown")
    temperature = lead_data.get("temperature", "unknown")

    # Choose icon based on temperature
    icon = {
        "hot": "🔥",
        "warm": "⭐",
        "cool": "❄️",
        "cold": "🧊"
    }.get(temperature, "📋")

    message = f"New {temperature} lead: {name} from {source}"

    show_toast(message, icon=icon, type="success")


def show_appointment_notification(appointment_data: Dict[str, Any]):
    """
    Show notification for new appointment

    Args:
        appointment_data: Appointment data from Pusher event
    """
    appointment_type = appointment_data.get("appointment_type", "appointment")
    scheduled_datetime = appointment_data.get("scheduled_datetime", "")

    # Format datetime
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(scheduled_datetime.replace('Z', '+00:00'))
        time_str = dt.strftime('%b %d at %I:%M %p')
    except:
        time_str = "upcoming"

    message = f"New {appointment_type} scheduled for {time_str}"

    show_toast(message, icon="📅", type="info")


def show_project_status_notification(project_data: Dict[str, Any]):
    """
    Show notification for project status change

    Args:
        project_data: Project data from Pusher event
    """
    new_status = project_data.get("new_status", "unknown")
    project_id = project_data.get("project_id", "")

    # Choose icon based on status
    icon = {
        "planning": "📋",
        "in_progress": "🔨",
        "on_hold": "⏸️",
        "completed": "✅",
        "cancelled": "❌"
    }.get(new_status, "📊")

    message = f"Project {project_id[:8]}... status: {new_status}"

    show_toast(message, icon=icon, type="success" if new_status == "completed" else "info")


def show_alert_notification(alert_data: Dict[str, Any]):
    """
    Show critical alert notification

    Args:
        alert_data: Alert data from Pusher event
    """
    title = alert_data.get("title", "Alert")
    message = alert_data.get("message", "")

    full_message = f"{title}: {message}" if message else title

    show_toast(full_message, icon="⚠️", type="error")


def show_customer_notification(customer_data: Dict[str, Any], event_type: str = "created"):
    """
    Show notification for customer events

    Args:
        customer_data: Customer data from Pusher event
        event_type: Event type (created, updated)
    """
    name = customer_data.get("name", "Unknown")
    segment = customer_data.get("segment", "")

    if event_type == "created":
        icon = "👤"
        message = f"New customer: {name}"
        if segment:
            message += f" ({segment})"
    else:
        icon = "🔄"
        message = f"Customer updated: {name}"

    show_toast(message, icon=icon, type="success")


def show_conversion_notification(lead_id: str, customer_id: str):
    """
    Show notification for lead conversion

    Args:
        lead_id: Lead ID
        customer_id: Customer ID
    """
    message = "🎉 Lead converted to customer!"

    show_toast(message, icon="🎉", type="success")

    # Add celebration animation
    if hasattr(st, 'balloons'):
        st.balloons()


def notification_preferences_sidebar():
    """
    Add notification preferences to sidebar
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔔 Notifications")

    # Initialize preferences in session state
    if "notification_prefs" not in st.session_state:
        st.session_state.notification_prefs = {
            "enabled": True,
            "sound": False,
            "leads": True,
            "customers": True,
            "projects": True,
            "appointments": True,
            "alerts": True
        }

    prefs = st.session_state.notification_prefs

    # Enable/disable all notifications
    prefs["enabled"] = st.sidebar.checkbox(
        "Enable notifications",
        value=prefs["enabled"],
        help="Show toast notifications for real-time events"
    )

    if prefs["enabled"]:
        # Notification filters
        with st.sidebar.expander("Notification Types", expanded=False):
            prefs["leads"] = st.checkbox("📋 Leads", value=prefs["leads"])
            prefs["customers"] = st.checkbox("👥 Customers", value=prefs["customers"])
            prefs["projects"] = st.checkbox("📊 Projects", value=prefs["projects"])
            prefs["appointments"] = st.checkbox("📅 Appointments", value=prefs["appointments"])
            prefs["alerts"] = st.checkbox("⚠️ Alerts", value=prefs["alerts"])

    return prefs


def process_pusher_event(channel: str, event: str, data: Dict[str, Any]):
    """
    Process Pusher event and show appropriate notification

    Args:
        channel: Channel name (leads, customers, etc.)
        event: Event name (lead:created, etc.)
        data: Event data
    """
    # Get notification preferences
    prefs = st.session_state.get("notification_prefs", {"enabled": True})

    if not prefs.get("enabled", True):
        return

    # Route to appropriate notification handler
    if channel == "leads" and prefs.get("leads", True):
        if event == "lead:created":
            show_lead_notification(data)
        elif event == "lead:converted":
            show_conversion_notification(data.get("lead_id", ""), data.get("customer_id", ""))

    elif channel == "customers" and prefs.get("customers", True):
        if event == "customer:created":
            show_customer_notification(data, "created")
        elif event == "customer:updated":
            show_customer_notification(data, "updated")

    elif channel == "projects" and prefs.get("projects", True):
        if event == "project:status_changed":
            show_project_status_notification(data)
        elif event == "project:created":
            show_toast("New project created", icon="📊", type="success")

    elif channel == "appointments" and prefs.get("appointments", True):
        if event == "appointment:created":
            show_appointment_notification(data)

    elif channel == "analytics":
        if event == "alert" and prefs.get("alerts", True):
            show_alert_notification(data)
