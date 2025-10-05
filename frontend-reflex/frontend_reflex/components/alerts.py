"""Alert components for real-time notifications - Static components with JavaScript functionality."""

import reflex as rx


def alert_card_static() -> rx.Component:
    """Static alert card component template."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("bell", size=16, color="orange"),
                rx.text("Alert Title", weight="bold", size="2"),
                rx.badge("high", color_scheme="red", size="1"),
                justify="between",
                align_items="center",
                width="100%"
            ),
            rx.text("Alert message content", size="2", color="gray"),
            rx.text("2 minutes ago", size="1", color="gray"),
            spacing="2",
            width="100%"
        ),
        size="1",
        width="100%",
        margin_bottom="2"
    )


def alerts_sidebar() -> rx.Component:
    """Static alerts sidebar structure - data loaded via JavaScript."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("bell", size=20, color="orange"),
                rx.heading("Alerts", size="3"),
                rx.badge(
                    rx.text("0", id="alerts-count"),
                    color_scheme="red"
                ),
                spacing="2",
                align_items="center"
            ),
            rx.divider(),

            # Loading state
            rx.vstack(
                rx.text("Loading alerts...", id="alerts-loading", size="2", color="gray"),
                spacing="2",
                width="100%"
            ),

            # Alerts list (hidden initially)
            rx.vstack(
                id="alerts-list",
                spacing="2",
                width="100%",
                style={"display": "none"}
            ),

            # Empty state (hidden initially)
            rx.text("No alerts", id="alerts-empty", size="2", color="gray", style={"display": "none"}),

            spacing="3",
            width="100%"
        ),
        size="2",
        width="300px",
        height="500px",
        overflow_y="auto"
    )