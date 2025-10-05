"""Appointments page for the iSwitch Roofs CRM - Static components with JavaScript functionality."""

import reflex as rx


def appointments_page() -> rx.Component:
    """Appointments management page."""
    return rx.container(
        rx.color_mode.button(position="top-right"),

        # Navigation breadcrumb
        rx.hstack(
            rx.link(
                rx.button(
                    rx.icon("arrow_left", size=16),
                    "Back to Dashboard",
                    variant="ghost",
                    size="2"
                ),
                href="/"
            ),
            rx.text("/", color="gray"),
            rx.text("Appointments", weight="bold"),
            spacing="2",
            align_items="center",
            margin_bottom="4"
        ),

        # Error message (hidden by default)
        rx.callout(
            "Failed to load appointments",
            id="appointments-error-message",
            icon="circle_alert",
            color_scheme="red",
            size="2",
            margin_bottom="4",
            style={"display": "none"}
        ),

        # Success message (hidden by default)
        rx.callout(
            "Operation completed successfully",
            id="appointments-success-message",
            icon="check_check",
            color_scheme="green",
            size="2",
            margin_bottom="4",
            style={"display": "none"}
        ),

        # Main appointments content
        rx.vstack(
            rx.heading("Appointment Management", size="5"),

            # Calendar view placeholder
            rx.card(
                rx.vstack(
                    rx.text("Calendar View", size="4", weight="bold"),
                    rx.text("Appointment calendar will be loaded here", size="3", color="gray"),
                    spacing="4",
                    align_items="center",
                    padding="8"
                ),
                size="2",
                width="100%",
                margin_bottom="4"
            ),

            # Appointments list placeholder
            rx.card(
                rx.vstack(
                    rx.text("Upcoming Appointments", size="4", weight="bold"),
                    rx.text("Appointments list will be loaded here", size="3", color="gray"),
                    spacing="4",
                    align_items="center",
                    padding="8"
                ),
                size="2",
                width="100%"
            ),

            spacing="4",
            width="100%"
        ),

        # JavaScript initialization
        rx.script("""
            document.addEventListener('DOMContentLoaded', function() {
                console.log('Appointments page loaded - ready for API integration');
                // Future: Load appointments data from API
            });
        """),

        size="4",
        padding="4"
    )