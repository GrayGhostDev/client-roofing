"""Comprehensive Appointment List component with search, filters, and table functionality."""

import reflex as rx
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from ..state import AppState, Appointment


def appointments_table_header() -> rx.Component:
    """Table header with sortable columns."""
    return rx.table_header(
        rx.table_row(
            rx.table_column_header_cell(
                rx.hstack(
                    "Date & Time",
                    rx.button(
                        rx.icon("arrow-up-down", size=12),
                        size="1",
                        variant="ghost",
                        on_click=lambda: AppState.sort_appointments("scheduled_date")
                    ),
                    spacing="1",
                    align="center"
                )
            ),
            rx.table_column_header_cell("Customer"),
            rx.table_column_header_cell("Location"),
            rx.table_column_header_cell("Type"),
            rx.table_column_header_cell("Team Member"),
            rx.table_column_header_cell(
                rx.hstack(
                    "Status",
                    rx.button(
                        rx.icon("arrow-up-down", size=12),
                        size="1",
                        variant="ghost",
                        on_click=lambda: AppState.sort_appointments("status")
                    ),
                    spacing="1",
                    align="center"
                )
            ),
            rx.table_column_header_cell("Actions")
        )
    )


def appointment_table_row(appointment: Appointment) -> rx.Component:
    """Individual appointment table row."""
    return rx.table_row(
        # Date & Time
        rx.table_cell(
            rx.vstack(
                rx.text(
                    appointment.scheduled_date.split('T')[0] if 'T' in appointment.scheduled_date else appointment.scheduled_date,
                    size="2",
                    weight="medium"
                ),
                rx.text(
                    appointment.scheduled_date.split('T')[1][:5] if 'T' in appointment.scheduled_date else "All Day",
                    size="1",
                    color="gray"
                ),
                rx.text(
                    f"{appointment.duration_minutes}min",
                    size="1",
                    color="gray"
                ),
                align="start",
                spacing="1"
            )
        ),

        # Customer
        rx.table_cell(
            rx.vstack(
                rx.text(
                    appointment.title,
                    size="2",
                    weight="medium"
                ),
                rx.text(
                    appointment.entity_id,  # Customer ID - would be replaced with customer name lookup
                    size="1",
                    color="gray"
                ),
                align="start",
                spacing="1"
            )
        ),

        # Location
        rx.table_cell(
            rx.vstack(
                rx.text(
                    appointment.location or "Virtual Meeting",
                    size="2"
                ),
                rx.cond(
                    appointment.is_virtual,
                    rx.hstack(
                        rx.icon("video", size=12, color="blue"),
                        rx.text("Virtual", size="1", color="blue"),
                        spacing="1"
                    ),
                    rx.hstack(
                        rx.icon("map-pin", size=12, color="green"),
                        rx.text("On-site", size="1", color="green"),
                        spacing="1"
                    )
                ),
                align="start",
                spacing="1"
            )
        ),

        # Type
        rx.table_cell(
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
                            rx.cond(
                                appointment.appointment_type == "emergency",
                                "red",
                                "purple"
                            )
                        )
                    )
                )
            )
        ),

        # Team Member
        rx.table_cell(
            rx.vstack(
                rx.text(
                    appointment.assigned_to,
                    size="2"
                ),
                rx.text(
                    "View schedule",
                    size="1",
                    color="blue",
                    cursor="pointer",
                    on_click=lambda: AppState.view_team_member_schedule(appointment.assigned_to)
                ),
                align="start",
                spacing="1"
            )
        ),

        # Status
        rx.table_cell(
            rx.vstack(
                rx.badge(
                    appointment.status,
                    color_scheme=rx.cond(
                        appointment.status == "confirmed",
                        "green",
                        rx.cond(
                            appointment.status == "scheduled",
                            "blue",
                            rx.cond(
                                appointment.status == "in_progress",
                                "orange",
                                rx.cond(
                                    appointment.status == "completed",
                                    "purple",
                                    rx.cond(
                                        appointment.status == "cancelled",
                                        "red",
                                        "gray"
                                    )
                                )
                            )
                        )
                    )
                ),
                rx.cond(
                    appointment.confirmed_by_customer,
                    rx.text("✓ Confirmed", size="1", color="green"),
                    rx.text("Pending", size="1", color="gray")
                ),
                align="start",
                spacing="1"
            )
        ),

        # Actions
        rx.table_cell(
            rx.hstack(
                rx.button(
                    rx.icon("eye", size=14),
                    size="2",
                    variant="outline",
                    on_click=lambda: AppState.open_appointment_detail_modal(appointment.id)
                ),
                rx.button(
                    rx.icon("edit", size=14),
                    size="2",
                    variant="outline",
                    on_click=lambda: AppState.edit_appointment(appointment.id)
                ),
                rx.popover(
                    rx.popover_trigger(
                        rx.button(
                            rx.icon("more-horizontal", size=14),
                            size="2",
                            variant="outline"
                        )
                    ),
                    rx.popover_content(
                        rx.vstack(
                            rx.button(
                                rx.icon("check", size=14),
                                "Confirm",
                                width="100%",
                                variant="ghost",
                                on_click=lambda: AppState.confirm_appointment(appointment.id)
                            ),
                            rx.button(
                                rx.icon("calendar", size=14),
                                "Reschedule",
                                width="100%",
                                variant="ghost",
                                on_click=lambda: AppState.reschedule_appointment(appointment.id)
                            ),
                            rx.button(
                                rx.icon("bell", size=14),
                                "Send Reminder",
                                width="100%",
                                variant="ghost",
                                on_click=lambda: AppState.send_appointment_reminder(appointment.id)
                            ),
                            rx.button(
                                rx.icon("map", size=14),
                                "Directions",
                                width="100%",
                                variant="ghost",
                                on_click=lambda: AppState.get_directions(appointment.location)
                            ),
                            rx.separator(),
                            rx.button(
                                rx.icon("x", size=14),
                                "Cancel",
                                width="100%",
                                variant="ghost",
                                color="red",
                                on_click=lambda: AppState.cancel_appointment(appointment.id)
                            ),
                            spacing="1",
                            width="150px"
                        ),
                        padding="2"
                    )
                ),
                spacing="1"
            )
        ),

        # Make row selectable
        cursor="pointer",
        _hover={"bg": "var(--gray-2)"},
        on_click=lambda: AppState.toggle_appointment_selection(appointment.id)
    )


def appointments_search_and_filters() -> rx.Component:
    """Search bar and filter controls."""
    return rx.card(
        rx.vstack(
            # Search bar
            rx.hstack(
                rx.input(
                    placeholder="Search appointments by customer, location, or type...",
                    value=AppState.appointment_search_query,
                    on_change=AppState.set_appointment_search_query,
                    width="400px"
                ),
                rx.button(
                    rx.icon("search", size=16),
                    "Search",
                    on_click=AppState.search_appointments
                ),
                rx.button(
                    rx.icon("x", size=16),
                    "Clear",
                    variant="outline",
                    on_click=AppState.clear_appointment_search
                ),
                spacing="2",
                align="center"
            ),

            # Filter controls
            rx.hstack(
                rx.select(
                    ["all", "today", "tomorrow", "this_week", "next_week", "this_month"],
                    placeholder="Date Range",
                    value=AppState.appointment_date_filter,
                    on_change=AppState.set_appointment_date_filter,
                    size="2"
                ),
                rx.select(
                    ["all", "estimate", "installation", "inspection", "follow_up", "emergency"],
                    placeholder="Type",
                    value=AppState.appointment_type_filter,
                    on_change=AppState.set_appointment_type_filter,
                    size="2"
                ),
                rx.select(
                    ["all", "scheduled", "confirmed", "in_progress", "completed", "cancelled"],
                    placeholder="Status",
                    value=AppState.appointment_status_filter,
                    on_change=AppState.set_appointment_status_filter,
                    size="2"
                ),
                rx.select(
                    AppState.get_team_member_options,
                    placeholder="Team Member",
                    value=AppState.appointment_assigned_to_filter,
                    on_change=AppState.set_appointment_assigned_to_filter,
                    size="2"
                ),
                rx.button(
                    rx.icon("filter-x", size=16),
                    "Clear Filters",
                    variant="outline",
                    on_click=AppState.clear_appointment_filters
                ),
                spacing="2",
                align="center",
                wrap="wrap"
            ),

            spacing="4",
            width="100%"
        ),
        padding="4",
        width="100%"
    )


def appointments_bulk_actions() -> rx.Component:
    """Bulk action controls for selected appointments."""
    return rx.cond(
        AppState.selected_appointments_count > 0,
        rx.card(
            rx.hstack(
                rx.text(
                    f"{AppState.selected_appointments_count} appointments selected",
                    size="2",
                    weight="medium"
                ),
                rx.spacer(),
                rx.hstack(
                    rx.button(
                        rx.icon("check", size=16),
                        "Confirm All",
                        variant="outline",
                        on_click=AppState.bulk_confirm_appointments
                    ),
                    rx.button(
                        rx.icon("bell", size=16),
                        "Send Reminders",
                        variant="outline",
                        on_click=AppState.bulk_send_reminders
                    ),
                    rx.button(
                        rx.icon("download", size=16),
                        "Export Selected",
                        variant="outline",
                        on_click=AppState.export_selected_appointments
                    ),
                    rx.button(
                        rx.icon("trash", size=16),
                        "Cancel Selected",
                        variant="outline",
                        color="red",
                        on_click=AppState.bulk_cancel_appointments
                    ),
                    spacing="2"
                ),
                justify="between",
                align="center",
                width="100%"
            ),
            padding="3",
            bg="blue.1",
            border="1px solid var(--blue-6)"
        ),
        rx.fragment()
    )


def appointments_table() -> rx.Component:
    """Main appointments table."""
    return rx.card(
        rx.vstack(
            # Table controls
            rx.hstack(
                rx.text(
                    f"Showing {AppState.filtered_appointments_count} appointments",
                    size="2",
                    color="gray"
                ),
                rx.spacer(),
                rx.hstack(
                    rx.select(
                        ["10", "25", "50", "100"],
                        value=str(AppState.appointments_per_page),
                        on_change=AppState.set_appointments_per_page,
                        size="2"
                    ),
                    rx.text("per page", size="2", color="gray"),
                    rx.button(
                        rx.icon("refresh-cw", size=16),
                        "Refresh",
                        variant="outline",
                        on_click=AppState.refresh_appointments
                    ),
                    spacing="2",
                    align="center"
                ),
                justify="between",
                align="center",
                width="100%"
            ),

            # Table
            rx.cond(
                AppState.get_filtered_appointments,
                rx.vstack(
                    rx.table_root(
                        rx.table_header(
                            rx.table_row(
                                rx.table_column_header_cell(
                                    rx.checkbox(
                                        checked=AppState.all_appointments_selected,
                                        on_change=AppState.toggle_select_all_appointments
                                    )
                                ),
                                rx.table_column_header_cell(
                                    rx.hstack(
                                        "Date & Time",
                                        rx.button(
                                            rx.icon("arrow-up-down", size=12),
                                            size="1",
                                            variant="ghost",
                                            on_click=lambda: AppState.sort_appointments("scheduled_date")
                                        ),
                                        spacing="1",
                                        align="center"
                                    )
                                ),
                                rx.table_column_header_cell("Customer"),
                                rx.table_column_header_cell("Location"),
                                rx.table_column_header_cell("Type"),
                                rx.table_column_header_cell("Team Member"),
                                rx.table_column_header_cell("Status"),
                                rx.table_column_header_cell("Actions")
                            )
                        ),
                        rx.table_body(
                            rx.foreach(
                                AppState.get_paginated_appointments,
                                lambda appointment: rx.table_row(
                                    # Checkbox
                                    rx.table_cell(
                                        rx.checkbox(
                                            checked=AppState.is_appointment_selected(appointment.id),
                                            on_change=lambda: AppState.toggle_appointment_selection(appointment.id)
                                        )
                                    ),

                                    # Date & Time
                                    rx.table_cell(
                                        rx.vstack(
                                            rx.text(
                                                appointment.scheduled_date.split('T')[0] if 'T' in appointment.scheduled_date else appointment.scheduled_date,
                                                size="2",
                                                weight="medium"
                                            ),
                                            rx.text(
                                                appointment.scheduled_date.split('T')[1][:5] if 'T' in appointment.scheduled_date else "All Day",
                                                size="1",
                                                color="gray"
                                            ),
                                            rx.text(
                                                f"{appointment.duration_minutes}min",
                                                size="1",
                                                color="gray"
                                            ),
                                            align="start",
                                            spacing="1"
                                        )
                                    ),

                                    # Customer
                                    rx.table_cell(
                                        rx.vstack(
                                            rx.text(
                                                appointment.title,
                                                size="2",
                                                weight="medium"
                                            ),
                                            rx.text(
                                                appointment.entity_id,
                                                size="1",
                                                color="gray"
                                            ),
                                            align="start",
                                            spacing="1"
                                        )
                                    ),

                                    # Location
                                    rx.table_cell(
                                        rx.vstack(
                                            rx.text(
                                                appointment.location or "Virtual Meeting",
                                                size="2"
                                            ),
                                            rx.cond(
                                                appointment.is_virtual,
                                                rx.hstack(
                                                    rx.icon("video", size=12, color="blue"),
                                                    rx.text("Virtual", size="1", color="blue"),
                                                    spacing="1"
                                                ),
                                                rx.hstack(
                                                    rx.icon("map-pin", size=12, color="green"),
                                                    rx.text("On-site", size="1", color="green"),
                                                    spacing="1"
                                                )
                                            ),
                                            align="start",
                                            spacing="1"
                                        )
                                    ),

                                    # Type
                                    rx.table_cell(
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
                                                        rx.cond(
                                                            appointment.appointment_type == "emergency",
                                                            "red",
                                                            "purple"
                                                        )
                                                    )
                                                )
                                            )
                                        )
                                    ),

                                    # Team Member
                                    rx.table_cell(
                                        rx.text(
                                            appointment.assigned_to,
                                            size="2"
                                        )
                                    ),

                                    # Status
                                    rx.table_cell(
                                        rx.vstack(
                                            rx.badge(
                                                appointment.status,
                                                color_scheme=rx.cond(
                                                    appointment.status == "confirmed",
                                                    "green",
                                                    rx.cond(
                                                        appointment.status == "scheduled",
                                                        "blue",
                                                        rx.cond(
                                                            appointment.status == "in_progress",
                                                            "orange",
                                                            rx.cond(
                                                                appointment.status == "completed",
                                                                "purple",
                                                                rx.cond(
                                                                    appointment.status == "cancelled",
                                                                    "red",
                                                                    "gray"
                                                                )
                                                            )
                                                        )
                                                    )
                                                )
                                            ),
                                            rx.cond(
                                                appointment.confirmed_by_customer,
                                                rx.text("✓ Confirmed", size="1", color="green"),
                                                rx.text("Pending", size="1", color="gray")
                                            ),
                                            align="start",
                                            spacing="1"
                                        )
                                    ),

                                    # Actions
                                    rx.table_cell(
                                        rx.hstack(
                                            rx.button(
                                                rx.icon("eye", size=14),
                                                size="2",
                                                variant="outline",
                                                on_click=lambda: AppState.open_appointment_detail_modal(appointment.id)
                                            ),
                                            rx.button(
                                                rx.icon("edit", size=14),
                                                size="2",
                                                variant="outline",
                                                on_click=lambda: AppState.edit_appointment(appointment.id)
                                            ),
                                            rx.popover(
                                                rx.popover_trigger(
                                                    rx.button(
                                                        rx.icon("more-horizontal", size=14),
                                                        size="2",
                                                        variant="outline"
                                                    )
                                                ),
                                                rx.popover_content(
                                                    rx.vstack(
                                                        rx.button(
                                                            rx.icon("check", size=14),
                                                            "Confirm",
                                                            width="100%",
                                                            variant="ghost",
                                                            on_click=lambda: AppState.confirm_appointment(appointment.id)
                                                        ),
                                                        rx.button(
                                                            rx.icon("calendar", size=14),
                                                            "Reschedule",
                                                            width="100%",
                                                            variant="ghost",
                                                            on_click=lambda: AppState.reschedule_appointment(appointment.id)
                                                        ),
                                                        rx.button(
                                                            rx.icon("bell", size=14),
                                                            "Send Reminder",
                                                            width="100%",
                                                            variant="ghost",
                                                            on_click=lambda: AppState.send_appointment_reminder(appointment.id)
                                                        ),
                                                        rx.separator(),
                                                        rx.button(
                                                            rx.icon("x", size=14),
                                                            "Cancel",
                                                            width="100%",
                                                            variant="ghost",
                                                            color="red",
                                                            on_click=lambda: AppState.cancel_appointment(appointment.id)
                                                        ),
                                                        spacing="1",
                                                        width="150px"
                                                    ),
                                                    padding="2"
                                                )
                                            ),
                                            spacing="1"
                                        )
                                    ),

                                    # Hover effect
                                    _hover={"bg": "var(--gray-2)"},
                                    cursor="pointer"
                                )
                            )
                        ),
                        width="100%",
                        variant="surface"
                    ),

                    # Pagination
                    rx.hstack(
                        rx.text(
                            f"Page {AppState.appointments_current_page} of {AppState.appointments_total_pages}",
                            size="2",
                            color="gray"
                        ),
                        rx.spacer(),
                        rx.hstack(
                            rx.button(
                                rx.icon("chevron-left", size=16),
                                "Previous",
                                variant="outline",
                                disabled=AppState.appointments_current_page == 1,
                                on_click=AppState.previous_appointments_page
                            ),
                            rx.button(
                                "Next",
                                rx.icon("chevron-right", size=16),
                                variant="outline",
                                disabled=AppState.appointments_current_page == AppState.appointments_total_pages,
                                on_click=AppState.next_appointments_page
                            ),
                            spacing="2"
                        ),
                        justify="between",
                        align="center",
                        width="100%",
                        padding_top="4"
                    ),

                    spacing="4",
                    width="100%"
                ),

                # Empty state
                rx.vstack(
                    rx.icon("calendar-x", size=48, color="gray"),
                    rx.text("No appointments found", size="4", weight="medium"),
                    rx.text("Try adjusting your filters or create a new appointment", size="2", color="gray"),
                    rx.button(
                        rx.icon("plus", size=16),
                        "Create Appointment",
                        color_scheme="blue",
                        on_click=AppState.open_appointment_modal
                    ),
                    align="center",
                    spacing="4",
                    padding="12"
                )
            ),

            spacing="4",
            width="100%"
        ),
        padding="4",
        width="100%"
    )


def appointment_list() -> rx.Component:
    """Main appointment list component with comprehensive table functionality."""
    return rx.vstack(
        # Header
        rx.hstack(
            rx.vstack(
                rx.heading("Appointments List", size="6"),
                rx.text("Manage and view all appointments", size="2", color="gray"),
                align="start",
                spacing="1"
            ),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=16),
                "New Appointment",
                color_scheme="blue",
                on_click=AppState.open_appointment_modal
            ),
            justify="between",
            align="center",
            width="100%"
        ),

        # Search and filters
        appointments_search_and_filters(),

        # Bulk actions (conditional)
        appointments_bulk_actions(),

        # Main table
        appointments_table(),

        spacing="6",
        width="100%",
        padding="4"
    )