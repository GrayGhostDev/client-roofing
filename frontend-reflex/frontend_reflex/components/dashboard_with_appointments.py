"""Enhanced Dashboard with Appointment Integration Example."""

import reflex as rx
from ..state import AppState
from .metrics import metrics_cards
from .alerts import alerts_sidebar
from .leads import leads_table, hot_leads_widget, follow_up_reminders_widget
from .appointments import (
    appointment_summary_widget,
    upcoming_appointments_widget,
    todays_schedule_widget,
    appointment_alerts_widget,
    appointment_modal,
    appointment_detail_modal
)


def enhanced_dashboard_header() -> rx.Component:
    """Dashboard header with appointment quick actions."""
    return rx.hstack(
        rx.vstack(
            rx.heading("iSwitch Roofs CRM Dashboard", size="6"),
            rx.hstack(
                rx.text("Last updated:", size="2", color="gray"),
                rx.text(AppState.last_update, size="2", weight="bold"),
                rx.cond(
                    AppState.websocket_connected,
                    rx.hstack(
                        rx.icon("wifi", size=14, color="green"),
                        rx.text("Live", size="1", color="green"),
                        spacing="1"
                    ),
                    rx.hstack(
                        rx.icon("wifi_off", size=14, color="red"),
                        rx.text("Offline", size="1", color="red"),
                        spacing="1"
                    )
                ),
                spacing="2",
                align_items="center"
            ),
            align_items="start",
            spacing="1"
        ),
        rx.spacer(),
        rx.hstack(
            # Quick appointment button
            rx.button(
                rx.icon("calendar_plus", size=16),
                "New Appointment",
                on_click=AppState.open_appointment_modal,
                color_scheme="teal",
                size="2"
            ),
            rx.button(
                rx.icon("refresh_cw", size=16),
                "Refresh",
                on_click=AppState.refresh_data,
                loading=AppState.loading,
                size="2"
            ),
            rx.button(
                rx.icon("settings", size=16),
                "Settings",
                variant="outline",
                size="2"
            ),
            spacing="2"
        ),
        justify="between",
        align_items="center",
        width="100%",
        padding_bottom="4"
    )


def enhanced_dashboard_content() -> rx.Component:
    """Enhanced dashboard content with appointment widgets."""
    return rx.vstack(
        # Metrics cards (existing)
        metrics_cards(),

        # Main content grid with appointments
        rx.grid(
            # Left column - Leads and main content
            rx.vstack(
                leads_table(),
                spacing="4",
                width="100%"
            ),

            # Middle column - Project and appointment widgets
            rx.vstack(
                appointment_summary_widget(),
                todays_schedule_widget(),
                spacing="4",
                width="100%"
            ),

            # Right column - Hot leads and appointment alerts
            rx.vstack(
                hot_leads_widget(),
                upcoming_appointments_widget(),
                appointment_alerts_widget(),
                follow_up_reminders_widget(),
                spacing="4",
                width="100%"
            ),

            columns="3",
            spacing="6",
            width="100%"
        ),

        spacing="6",
        width="100%"
    )


def enhanced_dashboard_page() -> rx.Component:
    """Complete enhanced dashboard page with appointment integration."""
    return rx.container(
        # Error/success messages
        rx.cond(
            AppState.error_message != "",
            rx.callout(
                AppState.error_message,
                icon="triangle_alert",
                color_scheme="red",
                size="1",
                margin_bottom="4"
            )
        ),

        rx.cond(
            AppState.bulk_operation_success_message != "",
            rx.callout(
                AppState.bulk_operation_success_message,
                icon="check_check",
                color_scheme="green",
                size="1",
                margin_bottom="4"
            )
        ),

        # Main layout
        rx.grid(
            # Main content area
            rx.vstack(
                enhanced_dashboard_header(),
                enhanced_dashboard_content(),
                spacing="4",
                width="100%",
                height="100vh",
                overflow_y="auto"
            ),

            # Alerts sidebar
            rx.card(
                alerts_sidebar(),
                width="350px",
                height="100vh",
                padding="0"
            ),

            columns="1fr 350px",
            gap="6",
            width="100%",
            height="100vh"
        ),

        # Appointment modals
        appointment_modal(),
        appointment_detail_modal(),

        # Auto-refresh data on page load
        on_mount=AppState.load_dashboard_data,
        size="4",
        padding="4"
    )


def appointment_quick_view() -> rx.Component:
    """Quick appointment view widget for integration anywhere."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("calendar", size=16, color="blue"),
                rx.text("Quick Schedule", size="3", weight="bold"),
                rx.spacer(),
                rx.button(
                    rx.icon("plus", size=12),
                    on_click=AppState.open_appointment_modal,
                    variant="ghost",
                    size="1"
                ),
                justify="between",
                align_items="center",
                width="100%"
            ),

            # Today's count
            rx.hstack(
                rx.text("Today:", size="2", weight="bold"),
                rx.text(f"{len(AppState.get_todays_appointments())}", size="3", color="blue"),
                rx.text("appointments", size="2", color="gray"),
                spacing="2"
            ),

            # Next appointment
            rx.cond(
                len(AppState.get_upcoming_appointments()) > 0,
                rx.vstack(
                    rx.text("Next:", size="2", weight="bold"),
                    rx.text(
                        lambda: AppState.get_upcoming_appointments()[0].title if AppState.get_upcoming_appointments() else "None",
                        size="2"
                    ),
                    rx.text(
                        lambda: AppState.get_upcoming_appointments()[0].scheduled_date if AppState.get_upcoming_appointments() else "",
                        size="1",
                        color="gray"
                    ),
                    spacing="1",
                    align_items="start"
                ),
                rx.text("No upcoming appointments", size="2", color="gray")
            ),

            spacing="3",
            align_items="start"
        ),
        size="2",
        width="100%"
    )