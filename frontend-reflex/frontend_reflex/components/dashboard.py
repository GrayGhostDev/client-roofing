"""Main dashboard page component."""

import reflex as rx
from ..state import AppState
from .metrics import metrics_cards
from .alerts import alerts_sidebar
from .leads import leads_table_static, hot_leads_widget_static, follow_up_reminders_widget_static


def dashboard_header() -> rx.Component:
    """Dashboard header with title and refresh controls."""
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


def dashboard_content() -> rx.Component:
    """Main dashboard content area."""
    return rx.vstack(
        # Metrics cards
        metrics_cards(),
        # Main content grid
        rx.grid(
            # Left column - Leads and widgets
            rx.vstack(
                leads_table(),
                spacing="4",
                width="100%"
            ),
            # Right column - Widgets and alerts
            rx.vstack(
                hot_leads_widget(),
                follow_up_reminders_widget(),
                spacing="4",
                width="100%"
            ),
            columns="2",
            spacing="6",
            width="100%"
        ),
        spacing="6",
        width="100%"
    )


def dashboard_page() -> rx.Component:
    """Complete dashboard page with layout."""
    return rx.container(
        rx.cond(
            AppState.error_message != "",
            rx.callout(
                AppState.error_message,
                icon="triangle_alert",
                color_scheme="red",
                size="1",
                margin_bottom="4"
            ),
            rx.text("")
        ),
        rx.grid(
            # Main content area
            rx.vstack(
                dashboard_header(),
                dashboard_content(),
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
        # Auto-refresh data on page load
        on_mount=AppState.load_dashboard_data,
        size="4",
        padding="4"
    )