"""Appointment management components - Complete implementation with full functionality."""

from .appointment_calendar import appointment_calendar
from .appointment_modal import appointment_modal
from .appointment_list import appointment_list
from .appointment_detail_modal import appointment_detail_modal
from .appointments_dashboard import (
    appointments_dashboard,
    appointment_summary_widget,
    upcoming_appointments_widget,
    todays_schedule_widget,
    appointment_alerts_widget,
    appointment_quick_actions,
    team_availability_widget
)

__all__ = [
    # Main components
    "appointments_dashboard",
    "appointment_calendar",
    "appointment_list",
    "appointment_modal",
    "appointment_detail_modal",

    # Dashboard widgets
    "appointment_summary_widget",
    "upcoming_appointments_widget",
    "todays_schedule_widget",
    "appointment_alerts_widget",
    "appointment_quick_actions",
    "team_availability_widget"
]