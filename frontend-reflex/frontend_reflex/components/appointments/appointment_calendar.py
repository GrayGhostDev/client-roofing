"""Comprehensive Appointment Calendar component with multiple views and full functionality."""

import reflex as rx
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta, calendar
from ..state import AppState, Appointment


def calendar_header() -> rx.Component:
    """Calendar header with navigation and view controls."""
    return rx.hstack(
        rx.hstack(
            rx.button(
                rx.icon("chevron-left", size=16),
                variant="outline",
                on_click=AppState.navigate_calendar_previous
            ),
            rx.text(
                AppState.calendar_display_date,
                size="4",
                weight="bold"
            ),
            rx.button(
                rx.icon("chevron-right", size=16),
                variant="outline",
                on_click=AppState.navigate_calendar_next
            ),
            rx.button(
                "Today",
                variant="outline",
                on_click=AppState.go_to_today
            ),
            spacing="2",
            align="center"
        ),
        rx.spacer(),
        rx.hstack(
            rx.select(
                ["month", "week", "day", "list"],
                value=AppState.calendar_view_mode,
                on_change=AppState.set_calendar_view_mode,
                size="2"
            ),
            rx.popover(
                rx.popover_trigger(
                    rx.button(
                        rx.icon("filter", size=16),
                        "Filters",
                        variant="outline"
                    )
                ),
                rx.popover_content(
                    rx.vstack(
                        rx.text("Filter Appointments", size="3", weight="bold"),
                        rx.select(
                            ["all", "estimate", "installation", "inspection", "follow_up", "emergency"],
                            placeholder="Appointment Type",
                            value=AppState.appointment_type_filter,
                            on_change=AppState.set_appointment_type_filter
                        ),
                        rx.select(
                            ["all", "scheduled", "confirmed", "in_progress", "completed", "cancelled"],
                            placeholder="Status",
                            value=AppState.appointment_status_filter,
                            on_change=AppState.set_appointment_status_filter
                        ),
                        rx.select(
                            AppState.get_team_member_options,
                            placeholder="Team Member",
                            value=AppState.appointment_assigned_to_filter,
                            on_change=AppState.set_appointment_assigned_to_filter
                        ),
                        rx.hstack(
                            rx.button(
                                "Clear Filters",
                                size="2",
                                variant="outline",
                                on_click=AppState.clear_appointment_filters
                            ),
                            rx.button(
                                "Apply",
                                size="2",
                                on_click=AppState.apply_appointment_filters
                            ),
                            spacing="2"
                        ),
                        spacing="3",
                        width="300px"
                    ),
                    padding="4"
                )
            ),
            spacing="2"
        ),
        justify="between",
        align="center",
        width="100%",
        padding="4"
    )


def appointment_block(appointment: Appointment) -> rx.Component:
    """Individual appointment block for calendar views."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(
                    appointment.title,
                    size="1",
                    weight="bold",
                    color="white"
                ),
                rx.spacer(),
                rx.cond(
                    appointment.status == "confirmed",
                    rx.icon("check", size=12, color="white"),
                    rx.cond(
                        appointment.status == "cancelled",
                        rx.icon("x", size=12, color="white"),
                        rx.fragment()
                    )
                ),
                width="100%"
            ),
            rx.text(
                f"{appointment.duration_minutes}min",
                size="1",
                color="white",
                opacity="0.8"
            ),
            rx.text(
                appointment.assigned_to,
                size="1",
                color="white",
                opacity="0.7"
            ),
            spacing="1",
            width="100%"
        ),
        bg=rx.cond(
            appointment.appointment_type == "estimate",
            "blue.7",
            rx.cond(
                appointment.appointment_type == "installation",
                "green.7",
                rx.cond(
                    appointment.appointment_type == "inspection",
                    "yellow.7",
                    rx.cond(
                        appointment.appointment_type == "emergency",
                        "red.7",
                        "purple.7"
                    )
                )
            )
        ),
        border_radius="md",
        padding="2",
        margin="1px 0",
        cursor="pointer",
        _hover={"opacity": "0.8"},
        on_click=lambda: AppState.open_appointment_detail_modal(appointment.id)
    )


def month_view() -> rx.Component:
    """Monthly calendar grid view."""
    return rx.vstack(
        # Days of week header
        rx.grid(
            rx.foreach(
                ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
                lambda day: rx.text(
                    day,
                    size="2",
                    weight="bold",
                    text_align="center",
                    color="gray"
                )
            ),
            columns="7",
            spacing="0",
            width="100%",
            border_bottom="1px solid var(--gray-6)",
            padding_bottom="2"
        ),
        # Calendar grid
        rx.grid(
            rx.foreach(
                AppState.get_calendar_days,
                lambda day: rx.box(
                    rx.vstack(
                        rx.text(
                            day["date"],
                            size="2",
                            weight="bold",
                            color=rx.cond(
                                day["is_today"],
                                "blue",
                                rx.cond(
                                    day["is_other_month"],
                                    "gray.5",
                                    "black"
                                )
                            )
                        ),
                        rx.foreach(
                            day["appointments"],
                            appointment_block
                        ),
                        spacing="1",
                        width="100%",
                        height="120px",
                        align="start"
                    ),
                    border="1px solid var(--gray-4)",
                    border_radius="md",
                    padding="2",
                    min_height="120px",
                    bg=rx.cond(
                        day["is_today"],
                        "blue.1",
                        "white"
                    ),
                    _hover={"bg": "var(--gray-1)"},
                    cursor="pointer",
                    on_click=lambda: AppState.select_calendar_date(day["full_date"])
                )
            ),
            columns="7",
            spacing="1",
            width="100%"
        ),
        spacing="2",
        width="100%"
    )


def week_view() -> rx.Component:
    """Weekly calendar view with hourly time slots."""
    return rx.hstack(
        # Time column
        rx.vstack(
            rx.text("Time", size="2", weight="bold", height="40px"),
            rx.foreach(
                AppState.get_business_hours,
                lambda hour: rx.text(
                    hour,
                    size="1",
                    color="gray",
                    height="60px",
                    display="flex",
                    align_items="center"
                )
            ),
            spacing="0",
            min_width="80px",
            align="start"
        ),
        # Days columns
        rx.hstack(
            rx.foreach(
                AppState.get_week_days,
                lambda day: rx.vstack(
                    # Day header
                    rx.vstack(
                        rx.text(
                            day["day_name"],
                            size="2",
                            weight="bold"
                        ),
                        rx.text(
                            day["date"],
                            size="1",
                            color="gray"
                        ),
                        align="center",
                        height="40px",
                        justify="center",
                        bg=rx.cond(
                            day["is_today"],
                            "blue.1",
                            "transparent"
                        ),
                        border_radius="md"
                    ),
                    # Hour slots
                    rx.vstack(
                        rx.foreach(
                            day["hour_slots"],
                            lambda slot: rx.box(
                                rx.foreach(
                                    slot["appointments"],
                                    appointment_block
                                ),
                                height="60px",
                                border="1px solid var(--gray-3)",
                                padding="1",
                                position="relative",
                                _hover={"bg": "var(--gray-1)"},
                                cursor="pointer",
                                on_click=lambda: AppState.create_appointment_at_slot(slot["datetime"])
                            )
                        ),
                        spacing="0",
                        width="100%"
                    ),
                    spacing="0",
                    width="150px"
                )
            ),
            spacing="1"
        ),
        spacing="2",
        width="100%",
        overflow_x="auto"
    )


def day_view() -> rx.Component:
    """Single day detailed view with 15-minute intervals."""
    return rx.vstack(
        # Day header
        rx.hstack(
            rx.text(
                AppState.calendar_selected_date,
                size="4",
                weight="bold"
            ),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    rx.icon("plus", size=16),
                    "New Appointment",
                    color_scheme="blue",
                    on_click=AppState.open_appointment_modal
                ),
                rx.button(
                    "Print Day",
                    variant="outline",
                    on_click=AppState.print_day_schedule
                ),
                spacing="2"
            ),
            justify="between",
            align="center",
            width="100%",
            padding="4",
            border_bottom="1px solid var(--gray-6)"
        ),
        # Time slots
        rx.hstack(
            # Time column
            rx.vstack(
                rx.foreach(
                    AppState.get_day_time_slots,
                    lambda slot: rx.text(
                        slot["time"],
                        size="1",
                        color="gray",
                        height="40px",
                        display="flex",
                        align_items="center"
                    )
                ),
                spacing="0",
                min_width="80px",
                align="start"
            ),
            # Appointments column
            rx.vstack(
                rx.foreach(
                    AppState.get_day_time_slots,
                    lambda slot: rx.box(
                        rx.foreach(
                            slot["appointments"],
                            lambda appointment: rx.box(
                                appointment_block(appointment),
                                height=f"{appointment.duration_minutes}px",
                                position="absolute",
                                width="90%"
                            )
                        ),
                        height="40px",
                        border="1px solid var(--gray-3)",
                        position="relative",
                        _hover={"bg": "var(--gray-1)"},
                        cursor="pointer",
                        on_click=lambda: AppState.create_appointment_at_slot(slot["datetime"])
                    )
                ),
                spacing="0",
                width="100%",
                flex="1"
            ),
            spacing="2",
            width="100%",
            align="start"
        ),
        spacing="0",
        width="100%",
        height="600px",
        overflow_y="auto"
    )


def list_view() -> rx.Component:
    """List view of appointments with search and filters."""
    return rx.vstack(
        # Search and filters
        rx.hstack(
            rx.input(
                placeholder="Search appointments...",
                value=AppState.appointment_search_query,
                on_change=AppState.set_appointment_search_query,
                width="300px"
            ),
            rx.select(
                ["all", "today", "tomorrow", "this_week", "next_week"],
                placeholder="Time Range",
                on_change=AppState.set_appointment_date_filter
            ),
            rx.button(
                rx.icon("search", size=16),
                "Search",
                on_click=AppState.search_appointments
            ),
            spacing="2",
            align="center"
        ),
        # Appointments list
        rx.vstack(
            rx.foreach(
                AppState.get_filtered_appointments,
                lambda appointment: rx.card(
                    rx.hstack(
                        rx.vstack(
                            rx.text(
                                appointment.scheduled_date,
                                size="2",
                                weight="bold"
                            ),
                            rx.text(
                                f"{appointment.duration_minutes} minutes",
                                size="1",
                                color="gray"
                            ),
                            align="start",
                            spacing="1",
                            min_width="120px"
                        ),
                        rx.vstack(
                            rx.text(
                                appointment.title,
                                size="3",
                                weight="bold"
                            ),
                            rx.text(
                                appointment.description or "No description",
                                size="2",
                                color="gray"
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
                        rx.vstack(
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
                                )
                            ),
                            rx.text(
                                appointment.assigned_to,
                                size="1",
                                color="gray"
                            ),
                            align="end",
                            spacing="2"
                        ),
                        rx.vstack(
                            rx.button(
                                rx.icon("eye", size=16),
                                size="2",
                                variant="outline",
                                on_click=lambda: AppState.open_appointment_detail_modal(appointment.id)
                            ),
                            rx.button(
                                rx.icon("edit", size=16),
                                size="2",
                                variant="outline",
                                on_click=lambda: AppState.edit_appointment(appointment.id)
                            ),
                            spacing="1"
                        ),
                        justify="between",
                        align="center",
                        width="100%"
                    ),
                    padding="4",
                    margin="2",
                    _hover={"bg": "var(--gray-1)"}
                )
            ),
            spacing="2",
            width="100%"
        ),
        spacing="4",
        width="100%"
    )


def calendar_legend() -> rx.Component:
    """Legend showing appointment type colors."""
    return rx.card(
        rx.vstack(
            rx.heading("Legend", size="3"),
            rx.grid(
                rx.hstack(
                    rx.box(
                        width="16px",
                        height="16px",
                        bg="blue.7",
                        border_radius="md"
                    ),
                    rx.text("Estimate", size="2"),
                    spacing="2",
                    align="center"
                ),
                rx.hstack(
                    rx.box(
                        width="16px",
                        height="16px",
                        bg="green.7",
                        border_radius="md"
                    ),
                    rx.text("Installation", size="2"),
                    spacing="2",
                    align="center"
                ),
                rx.hstack(
                    rx.box(
                        width="16px",
                        height="16px",
                        bg="yellow.7",
                        border_radius="md"
                    ),
                    rx.text("Inspection", size="2"),
                    spacing="2",
                    align="center"
                ),
                rx.hstack(
                    rx.box(
                        width="16px",
                        height="16px",
                        bg="purple.7",
                        border_radius="md"
                    ),
                    rx.text("Follow-up", size="2"),
                    spacing="2",
                    align="center"
                ),
                rx.hstack(
                    rx.box(
                        width="16px",
                        height="16px",
                        bg="red.7",
                        border_radius="md"
                    ),
                    rx.text("Emergency", size="2"),
                    spacing="2",
                    align="center"
                ),
                columns="1",
                spacing="2"
            ),
            spacing="3"
        ),
        padding="4",
        width="200px"
    )


def appointment_calendar() -> rx.Component:
    """Main appointment calendar component with multiple view modes."""
    return rx.vstack(
        # Calendar header with controls
        calendar_header(),

        # Main calendar content based on view mode
        rx.hstack(
            # Calendar view
            rx.box(
                rx.cond(
                    AppState.calendar_view_mode == "month",
                    month_view(),
                    rx.cond(
                        AppState.calendar_view_mode == "week",
                        week_view(),
                        rx.cond(
                            AppState.calendar_view_mode == "day",
                            day_view(),
                            list_view()
                        )
                    )
                ),
                flex="1",
                min_height="500px"
            ),

            # Legend (only show for calendar views, not list)
            rx.cond(
                AppState.calendar_view_mode != "list",
                calendar_legend(),
                rx.fragment()
            ),

            spacing="4",
            align="start",
            width="100%"
        ),

        spacing="0",
        width="100%"
    )