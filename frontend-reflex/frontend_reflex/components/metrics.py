"""Dashboard metrics components - Static components with JavaScript functionality."""

import reflex as rx


def metric_card(
    title: str,
    value: str,
    icon: str,
    color: str = "blue",
    change: str = "+0%",
    trend: str = "up"
) -> rx.Component:
    """Metric card component."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon(icon, size=20, color=color),
                rx.text(title, size="2", color="gray"),
                justify="between",
                align_items="center",
                width="100%"
            ),
            rx.hstack(
                rx.text(value, size="6", weight="bold"),
                rx.badge(
                    change,
                    color_scheme="green" if trend == "up" else "red",
                    size="1"
                ),
                justify="between",
                align_items="end",
                width="100%"
            ),
            spacing="2",
            width="100%"
        ),
        size="2",
        width="100%"
    )


def metrics_cards() -> rx.Component:
    """Static metrics cards structure - data loaded via JavaScript."""
    return rx.grid(
        metric_card(
            title="Total Leads",
            value="0",
            icon="users",
            color="blue",
            change="+0%",
            trend="up"
        ),
        metric_card(
            title="Active Projects",
            value="0",
            icon="briefcase",
            color="green",
            change="+0%",
            trend="up"
        ),
        metric_card(
            title="Revenue (MTD)",
            value="$0",
            icon="dollar_sign",
            color="purple",
            change="+0%",
            trend="up"
        ),
        metric_card(
            title="Conversion Rate",
            value="0%",
            icon="trending_up",
            color="orange",
            change="+0%",
            trend="up"
        ),
        columns={"base": "1", "md": "2", "lg": "4"},
        spacing="4",
        width="100%",
        margin_bottom="6",
        id="metrics-cards"
    )