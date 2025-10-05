"""
Dashboard Components Following Official Reflex Patterns
Implements proper component composition, state integration, and event handling
"""

import reflex as rx
from ..dashboard_state import DashboardState
from ..utils.pusher_client import pusher_init_component, pusher_connection_status, pusher_event_listeners


def dashboard_header() -> rx.Component:
    """Dashboard header with title, status, and controls."""
    return rx.hstack(
        # Title section
        rx.vstack(
            rx.heading("iSwitch Roofs CRM Dashboard", size="6"),
            rx.hstack(
                rx.text("Last updated:", size="2", color="gray"),
                rx.text(DashboardState.last_update_relative, size="2", weight="bold"),
                # Real-time connection status using Pusher
                pusher_connection_status(),
                spacing="2",
                align_items="center"
            ),
            align_items="start",
            spacing="1"
        ),
        rx.spacer(),

        # Control buttons
        rx.hstack(
            rx.button(
                rx.icon("refresh_cw", size=16),
                "Refresh",
                on_click=DashboardState.refresh_data,
                loading=DashboardState.loading,
                size="2",
                variant="outline"
            ),
            rx.button(
                rx.icon("bell", size=16),
                rx.cond(
                    DashboardState.alert_count > 0,
                    rx.badge(
                        DashboardState.alert_count,
                        color_scheme="red",
                        variant="solid",
                        size="1"
                    ),
                    rx.text("")
                ),
                on_click=DashboardState.toggle_alerts_sidebar,
                size="2",
                variant="outline"
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


def metrics_card(title: str, value_key: str, icon: str, color: str) -> rx.Component:
    """Individual metrics card component."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon(icon, size=20, color=color),
                rx.text(title, size="2", color="gray"),
                justify="between",
                width="100%"
            ),
            rx.text(
                DashboardState.metrics_formatted[value_key],
                size="6",
                weight="bold",
                color=color
            ),
            align_items="start",
            spacing="2"
        ),
        size="2",
        width="100%"
    )


def metrics_grid() -> rx.Component:
    """Main metrics grid following official patterns."""
    return rx.grid(
        metrics_card("Total Leads", "total_leads", "users", "blue"),
        metrics_card("Hot Leads", "hot_leads", "flame", "red"),
        metrics_card("Qualified Leads", "qualified_leads", "check", "green"),
        metrics_card("Conversion Rate", "conversion_rate", "trending_up", "purple"),
        metrics_card("Monthly Revenue", "monthly_revenue", "dollar_sign", "emerald"),
        metrics_card("Active Projects", "active_projects", "folder_open", "orange"),
        metrics_card("Pending Appointments", "pending_appointments", "calendar", "teal"),
        metrics_card("Avg Response Time", "response_time", "clock", "indigo"),
        columns="4",
        spacing="3",
        width="100%"
    )


def activity_card(activity) -> rx.Component:
    """Individual activity card component."""
    priority_colors = {
        "low": "gray",
        "normal": "blue",
        "high": "orange",
        "urgent": "red"
    }

    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.text(activity.title, size="3", weight="bold"),
                    rx.spacer(),
                    rx.badge(
                        activity.type.title(),
                        color_scheme=priority_colors.get(activity.priority, "blue"),
                        variant="soft",
                        size="1"
                    ),
                    width="100%"
                ),
                rx.text(activity.description, size="2", color="gray"),
                rx.text(activity.timestamp, size="1", color="slate"),
                align_items="start",
                spacing="1"
            ),
            width="100%"
        ),
        size="1",
        width="100%"
    )


def recent_activity_panel() -> rx.Component:
    """Recent activity panel using rx.foreach for dynamic rendering."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Recent Activity", size="4"),
                rx.spacer(),
                rx.button(
                    rx.icon("external_link", size=14),
                    "View All",
                    variant="ghost",
                    size="1"
                ),
                width="100%"
            ),
            rx.divider(),
            rx.cond(
                DashboardState.recent_activities.length() > 0,
                rx.vstack(
                    rx.foreach(
                        DashboardState.recent_activities,
                        activity_card
                    ),
                    spacing="2",
                    width="100%"
                ),
                rx.center(
                    rx.text("No recent activity", color="gray"),
                    padding="4"
                )
            ),
            spacing="3",
            width="100%"
        ),
        size="3",
        width="100%",
        height="400px"
    )


def alert_item(alert) -> rx.Component:
    """Individual alert item component."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.cond(
                    alert.type == "error",
                    rx.icon("circle_alert", size=16, color="red"),
                    rx.cond(
                        alert.type == "warning",
                        rx.icon("triangle_alert", size=16, color="orange"),
                        rx.icon("info", size=16, color="blue")
                    )
                ),
                rx.text(alert.title, size="2", weight="bold"),
                rx.spacer(),
                rx.button(
                    rx.icon("x", size=12),
                    on_click=lambda: DashboardState.acknowledge_alert(alert.id),
                    variant="ghost",
                    size="1"
                ),
                width="100%"
            ),
            rx.text(alert.message, size="1", color="gray"),
            rx.text(alert.created_at, size="1", color="slate"),
            align_items="start",
            spacing="1"
        ),
        size="1",
        width="100%"
    )


def alerts_sidebar() -> rx.Component:
    """Alerts sidebar using official sidebar patterns."""
    return rx.cond(
        DashboardState.alerts_sidebar_open,
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.heading("Alerts", size="4"),
                    rx.spacer(),
                    rx.button(
                        rx.icon("x", size=14),
                        on_click=DashboardState.toggle_alerts_sidebar,
                        variant="ghost",
                        size="1"
                    ),
                    width="100%"
                ),
                rx.divider(),
                rx.cond(
                    DashboardState.alerts.length() > 0,
                    rx.vstack(
                        rx.foreach(
                            DashboardState.alerts,
                            alert_item
                        ),
                        spacing="2",
                        width="100%"
                    ),
                    rx.center(
                        rx.text("No alerts", color="gray"),
                        padding="4"
                    )
                ),
                spacing="3",
                width="100%"
            ),
            width="350px",
            height="100vh",
            padding="4"
        ),
        rx.text("")  # Hidden state
    )


def quick_action_card(title: str, description: str, icon: str, color: str, route: str) -> rx.Component:
    """Quick action card component."""
    return rx.card(
        rx.vstack(
            rx.icon(icon, size=32, color=color),
            rx.heading(title, size="4"),
            rx.text(description, size="2", color="gray", text_align="center"),
            rx.link(
                rx.button(f"Open {title}", color_scheme=color, size="2"),
                href=route
            ),
            align_items="center",
            spacing="3"
        ),
        size="3",
        height="200px",
        width="100%"
    )


def quick_actions_grid() -> rx.Component:
    """Quick actions navigation grid."""
    return rx.grid(
        quick_action_card(
            "Kanban Board",
            "Manage leads with drag & drop",
            "layout_grid",
            "blue",
            "/kanban"
        ),
        quick_action_card(
            "Lead Management",
            "Advanced table view with filtering",
            "users",
            "green",
            "/leads"
        ),
        quick_action_card(
            "Customer Management",
            "Customer profiles and project history",
            "user_check",
            "blue",
            "/customers"
        ),
        quick_action_card(
            "Project Management",
            "Track projects through the pipeline",
            "folder_open",
            "orange",
            "/projects"
        ),
        quick_action_card(
            "Appointments",
            "Schedule and manage appointments",
            "calendar",
            "teal",
            "/appointments"
        ),
        quick_action_card(
            "Analytics",
            "Performance insights & reports",
            "bar_chart",
            "purple",
            "/analytics"
        ),
        columns="3",
        spacing="4",
        width="100%"
    )


def error_banner() -> rx.Component:
    """Error message banner."""
    return rx.cond(
        DashboardState.error_message != "",
        rx.callout(
            rx.hstack(
                rx.text(DashboardState.error_message),
                rx.spacer(),
                rx.button(
                    rx.icon("x", size=12),
                    on_click=DashboardState.clear_error,
                    variant="ghost",
                    size="1"
                ),
                width="100%"
            ),
            icon="triangle_alert",
            color_scheme="red",
            size="1",
            margin_bottom="4"
        ),
        rx.text("")
    )


def dashboard_layout() -> rx.Component:
    """Complete dashboard layout following official patterns with Pusher integration."""
    return rx.container(
        # Pusher initialization and event listeners
        pusher_init_component(),
        pusher_event_listeners(),

        # Error banner
        error_banner(),

        # Main layout grid
        rx.hstack(
            # Main content area
            rx.vstack(
                dashboard_header(),
                metrics_grid(),

                # Content grid
                rx.grid(
                    recent_activity_panel(),
                    quick_actions_grid(),
                    columns="1fr 2fr",
                    spacing="6",
                    width="100%"
                ),
                spacing="6",
                width="100%"
            ),

            # Alerts sidebar
            alerts_sidebar(),

            spacing="6",
            width="100%",
            height="100vh"
        ),

        # Initialize data on mount
        on_mount=DashboardState.load_dashboard_data,
        size="4",
        padding="4"
    )