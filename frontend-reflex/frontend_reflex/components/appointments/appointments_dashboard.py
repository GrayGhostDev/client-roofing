"""Comprehensive Appointments Dashboard component with full functionality."""

import reflex as rx
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from ..state import AppState, Appointment


def appointment_summary_widget() -> rx.Component:
    """Widget showing appointment statistics."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("calendar-days", size=20, color="blue"),
                rx.heading("Appointments Summary", size="4"),
                justify="start",
                align="center",
                spacing="2"
            ),
            rx.grid(
                # Today's appointments
                rx.vstack(
                    rx.text("Today", size="2", color="gray"),
                    rx.heading(
                        AppState.get_todays_appointments_count,
                        size="6",
                        color="blue"
                    ),
                    rx.text("appointments", size="1", color="gray"),
                    align="center",
                    spacing="1"
                ),
                # This week's appointments
                rx.vstack(
                    rx.text("This Week", size="2", color="gray"),
                    rx.heading(
                        AppState.get_week_appointments_count,
                        size="6",
                        color="green"
                    ),
                    rx.text("scheduled", size="1", color="gray"),
                    align="center",
                    spacing="1"
                ),
                # Pending confirmations
                rx.vstack(
                    rx.text("Pending", size="2", color="gray"),
                    rx.heading(
                        AppState.get_pending_confirmations_count,
                        size="6",
                        color="yellow"
                    ),
                    rx.text("confirmations", size="1", color="gray"),
                    align="center",
                    spacing="1"
                ),
                # Completed this month
                rx.vstack(
                    rx.text("Completed", size="2", color="gray"),
                    rx.heading(
                        AppState.get_completed_month_count,
                        size="6",
                        color="purple"
                    ),
                    rx.text("this month", size="1", color="gray"),
                    align="center",
                    spacing="1"
                ),
                columns="4",
                spacing="4",
                width="100%"
            ),
            spacing="4",
            width="100%"
        ),
        padding="6",
        width="100%"
    )


def appointment_quick_actions() -> rx.Component:
    """Quick action buttons for appointments."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("zap", size=20, color="orange"),
                rx.heading("Quick Actions", size="4"),
                justify="start",
                align="center",
                spacing="2"
            ),
            rx.hstack(
                rx.button(
                    rx.icon("plus", size=16),
                    "New Appointment",
                    color_scheme="blue",
                    on_click=AppState.open_appointment_modal
                ),
                rx.button(
                    rx.icon("calendar", size=16),
                    "Today's Schedule",
                    variant="outline",
                    on_click=AppState.show_todays_schedule
                ),
                rx.button(
                    rx.icon("printer", size=16),
                    "Print Schedule",
                    variant="outline",
                    on_click=AppState.print_schedule
                ),
                rx.button(
                    rx.icon("download", size=16),
                    "Export CSV",
                    variant="outline",
                    on_click=AppState.export_appointments
                ),
                spacing="2",
                wrap="wrap"
            ),
            spacing="4",
            width="100%"
        ),
        padding="6",
        width="100%"
    )


def upcoming_appointments_widget() -> rx.Component:
    """Widget showing the next 5 upcoming appointments."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("clock", size=20, color="green"),
                rx.heading("Upcoming Appointments", size="4"),
                rx.spacer(),
                rx.link(
                    "View All",
                    href="/appointments?view=list",
                    size="2",
                    color="blue"
                ),
                justify="between",
                align="center",
                width="100%"
            ),
            rx.cond(
                AppState.get_upcoming_appointments,
                rx.vstack(
                    rx.foreach(
                        AppState.get_upcoming_appointments,
                        lambda appointment: rx.hstack(
                            rx.vstack(
                                rx.text(
                                    appointment.scheduled_date,
                                    size="2",
                                    weight="bold"
                                ),
                                rx.text(
                                    f"{appointment.duration_minutes} min",
                                    size="1",
                                    color="gray"
                                ),
                                align="start",
                                spacing="1"
                            ),
                            rx.vstack(
                                rx.text(
                                    appointment.title,
                                    size="2",
                                    weight="medium"
                                ),
                                rx.text(
                                    appointment.location or "Virtual",
                                    size="1",
                                    color="gray"
                                ),
                                align="start",
                                spacing="1",
                                flex="1"
                            ),
                            rx.badge(
                                appointment.appointment_type,
                                color_scheme=rx.cond(
                                    appointment.appointment_type == "estimate",
                                    "blue",
                                    rx.cond(
                                        appointment.appointment_type == "installation",
                                        "green",
                                        rx.cond(
                                            appointment.appointment_type == "inspection",
                                            "yellow",
                                            "purple"
                                        )
                                    )
                                )
                            ),
                            justify="between",
                            align="center",
                            width="100%",
                            padding="3",
                            border="1px solid var(--gray-6)",
                            border_radius="md",
                            _hover={"bg": "var(--gray-2)"},
                            cursor="pointer",
                            on_click=lambda: AppState.open_appointment_detail_modal(appointment.id)
                        )
                    ),
                    spacing="2",
                    width="100%"
                ),
                rx.text(
                    "No upcoming appointments",
                    size="2",
                    color="gray",
                    text_align="center"
                )
            ),
            spacing="4",
            width="100%"
        ),
        padding="6",
        width="100%",
        max_height="400px"
    )


def todays_schedule_widget() -> rx.Component:
    """Widget showing today's detailed schedule."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("calendar-check", size=20, color="purple"),
                rx.heading("Today's Schedule", size="4"),
                rx.text(
                    datetime.now().strftime("%B %d, %Y"),
                    size="2",
                    color="gray"
                ),
                justify="start",
                align="center",
                spacing="2"
            ),
            rx.cond(
                AppState.get_todays_appointments,
                rx.vstack(
                    rx.foreach(
                        AppState.get_todays_appointments,
                        lambda appointment: rx.hstack(
                            rx.vstack(
                                rx.text(
                                    appointment.scheduled_date.split('T')[1][:5] if 'T' in appointment.scheduled_date else appointment.scheduled_date,
                                    size="2",
                                    weight="bold",
                                    color="blue"
                                ),
                                rx.text(
                                    f"{appointment.duration_minutes}m",
                                    size="1",
                                    color="gray"
                                ),
                                align="center",
                                spacing="1",
                                min_width="60px"
                            ),
                            rx.divider(orientation="vertical", height="40px"),
                            rx.vstack(
                                rx.text(
                                    appointment.title,
                                    size="2",
                                    weight="medium"
                                ),
                                rx.hstack(
                                    rx.badge(
                                        appointment.status,
                                        color_scheme=rx.cond(
                                            appointment.status == "confirmed",
                                            "green",
                                            rx.cond(
                                                appointment.status == "scheduled",
                                                "blue",
                                                "gray"
                                            )
                                        ),
                                        size="1"
                                    ),
                                    rx.text(
                                        appointment.assigned_to,
                                        size="1",
                                        color="gray"
                                    ),
                                    spacing="2"
                                ),
                                align="start",
                                spacing="1",
                                flex="1"
                            ),
                            justify="start",
                            align="center",
                            width="100%",
                            padding="3",
                            border="1px solid var(--gray-6)",
                            border_radius="md",
                            _hover={"bg": "var(--gray-2)"},
                            cursor="pointer",
                            on_click=lambda: AppState.open_appointment_detail_modal(appointment.id)
                        )
                    ),
                    spacing="2",
                    width="100%"
                ),
                rx.vstack(
                    rx.icon("calendar-x", size=32, color="gray"),
                    rx.text("No appointments today", size="2", color="gray"),
                    rx.text("Time to catch up on other tasks!", size="1", color="gray"),
                    align="center",
                    spacing="2"
                )
            ),
            spacing="4",
            width="100%"
        ),
        padding="6",
        width="100%",
        max_height="400px"
    )


def team_availability_widget() -> rx.Component:
    """Widget showing team member availability overview."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("users", size=20, color="indigo"),
                rx.heading("Team Availability", size="4"),
                justify="start",
                align="center",
                spacing="2"
            ),
            rx.grid(
                rx.foreach(
                    AppState.get_team_availability,
                    lambda member: rx.vstack(
                        rx.avatar(
                            fallback=member["initials"],
                            size="3"
                        ),
                        rx.text(
                            member["name"],
                            size="2",
                            weight="medium",
                            text_align="center"
                        ),
                        rx.badge(
                            member["status"],
                            color_scheme=rx.cond(
                                member["status"] == "available",
                                "green",
                                rx.cond(
                                    member["status"] == "busy",
                                    "red",
                                    "yellow"
                                )
                            ),
                            size="1"
                        ),
                        rx.text(
                            f"{member['appointments_today']} today",
                            size="1",
                            color="gray"
                        ),
                        align="center",
                        spacing="2",
                        padding="3",
                        border="1px solid var(--gray-6)",
                        border_radius="md"
                    )
                ),
                columns="2",
                spacing="3",
                width="100%"
            ),
            spacing="4",
            width="100%"
        ),
        padding="6",
        width="100%"
    )


def appointment_alerts_widget() -> rx.Component:
    """Widget showing appointment-related alerts and reminders."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("bell", size=20, color="red"),
                rx.heading("Alerts & Reminders", size="4"),
                justify="start",
                align="center",
                spacing="2"
            ),
            rx.cond(
                AppState.get_appointment_alerts,
                rx.vstack(
                    rx.foreach(
                        AppState.get_appointment_alerts,
                        lambda alert: rx.hstack(
                            rx.icon(
                                rx.cond(
                                    alert["type"] == "overdue",
                                    "alert-circle",
                                    rx.cond(
                                        alert["type"] == "confirmation",
                                        "clock",
                                        "info"
                                    )
                                ),
                                size=16,
                                color=rx.cond(
                                    alert["priority"] == "high",
                                    "red",
                                    rx.cond(
                                        alert["priority"] == "medium",
                                        "yellow",
                                        "blue"
                                    )
                                )
                            ),
                            rx.vstack(
                                rx.text(
                                    alert["message"],
                                    size="2",
                                    weight="medium"
                                ),
                                rx.text(
                                    alert["time"],
                                    size="1",
                                    color="gray"
                                ),
                                align="start",
                                spacing="1",
                                flex="1"
                            ),
                            rx.button(
                                "Action",
                                size="1",
                                variant="outline",
                                on_click=lambda: AppState.handle_alert_action(alert["id"])
                            ),
                            justify="between",
                            align="center",
                            width="100%",
                            padding="3",
                            border_radius="md",
                            bg=rx.cond(
                                alert["priority"] == "high",
                                "var(--red-2)",
                                "var(--gray-2)"
                            )
                        )
                    ),
                    spacing="2",
                    width="100%"
                ),
                rx.text(
                    "No alerts at this time",
                    size="2",
                    color="gray",
                    text_align="center"
                )
            ),
            spacing="4",
            width="100%"
        ),
        padding="6",
        width="100%",
        max_height="300px"
    )


def appointments_dashboard() -> rx.Component:
    """Main appointments dashboard with comprehensive functionality."""
    return rx.vstack(
        # Header with navigation
        rx.hstack(
            rx.vstack(
                rx.heading("Appointments Dashboard", size="6"),
                rx.text(
                    f"Today is {datetime.now().strftime('%A, %B %d, %Y')}",
                    size="2",
                    color="gray"
                ),
                align="start",
                spacing="1"
            ),
            rx.spacer(),
            rx.hstack(
                rx.select(
                    ["month", "week", "day", "list"],
                    value=AppState.calendar_view_mode,
                    on_change=AppState.set_calendar_view_mode,
                    size="2"
                ),
                rx.button(
                    rx.icon("refresh-cw", size=16),
                    "Refresh",
                    variant="outline",
                    on_click=AppState.refresh_appointments
                ),
                spacing="2"
            ),
            justify="between",
            align="center",
            width="100%",
            padding_bottom="4"
        ),

        # Statistics and Quick Actions Row
        rx.grid(
            appointment_summary_widget(),
            appointment_quick_actions(),
            columns="2",
            spacing="6",
            width="100%"
        ),

        # Main Content Grid
        rx.grid(
            # Left column
            rx.vstack(
                upcoming_appointments_widget(),
                team_availability_widget(),
                spacing="6",
                width="100%"
            ),
            # Right column
            rx.vstack(
                todays_schedule_widget(),
                appointment_alerts_widget(),
                spacing="6",
                width="100%"
            ),
            columns="2",
            spacing="6",
            width="100%"
        ),

        # Calendar View Section
        rx.cond(
            AppState.calendar_view_mode != "list",
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.heading("Calendar View", size="4"),
                        rx.spacer(),
                        rx.hstack(
                            rx.button(
                                rx.icon("chevron-left", size=16),
                                variant="outline",
                                on_click=AppState.navigate_calendar_previous
                            ),
                            rx.text(
                                AppState.calendar_display_date,
                                size="2",
                                weight="medium"
                            ),
                            rx.button(
                                rx.icon("chevron-right", size=16),
                                variant="outline",
                                on_click=AppState.navigate_calendar_next
                            ),
                            spacing="2"
                        ),
                        justify="between",
                        align="center",
                        width="100%"
                    ),
                    # Calendar component will be imported from appointment_calendar.py
                    rx.box(
                        "Calendar view will be rendered here",
                        height="400px",
                        bg="var(--gray-2)",
                        border_radius="md",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        color="gray"
                    ),
                    spacing="4",
                    width="100%"
                ),
                padding="6",
                width="100%"
            ),
            rx.fragment()
        ),

        spacing="6",
        width="100%",
        padding="4"
    )