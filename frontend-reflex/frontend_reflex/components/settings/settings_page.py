"""Settings page component - Complete settings interface with tabbed navigation."""

import reflex as rx
from .settings_state import settings_state
from .user_profile import user_profile_section
from .team_management import team_management_section
from .system_settings import system_settings_section
from .notification_settings import notification_settings_section
from .integrations import integrations_section
from .security import security_section


def settings_header() -> rx.Component:
    """Settings page header with breadcrumbs and action buttons."""
    return rx.vstack(
        # Breadcrumb navigation
        rx.hstack(
            rx.link(
                rx.text("Dashboard", size="2", color="gray"),
                href="/dashboard"
            ),
            rx.text(" / ", size="2", color="gray"),
            rx.text("Settings", size="2", weight="medium"),
            spacing="1",
            align="center"
        ),

        # Header with title and actions
        rx.hstack(
            rx.vstack(
                rx.heading("Settings", size="6", weight="bold"),
                rx.text("Manage your account, team, and system preferences", size="3", color="gray"),
                spacing="1",
                align="start"
            ),

            rx.spacer(),

            # Action buttons
            rx.hstack(
                rx.cond(
                    settings_state.has_unsaved_changes,
                    rx.hstack(
                        rx.button(
                            "Cancel Changes",
                            variant="outline",
                            color_scheme="gray",
                            on_click=lambda: None  # Handle cancel
                        ),
                        rx.button(
                            rx.cond(
                                settings_state.saving,
                                rx.hstack(
                                    rx.spinner(size="1"),
                                    rx.text("Saving..."),
                                    spacing="2"
                                ),
                                "Save Changes"
                            ),
                            color_scheme="blue",
                            loading=settings_state.saving,
                            on_click=lambda: None  # Handle save
                        ),
                        spacing="2"
                    ),
                    rx.fragment()
                ),

                # Search functionality
                rx.input(
                    placeholder="Search settings...",
                    value=settings_state.search_query,
                    width="200px",
                    on_change=lambda val: None  # Handle search
                ),
                spacing="3"
            ),
            width="100%",
            justify="between",
            align="center"
        ),

        # Unsaved changes indicator
        rx.cond(
            settings_state.has_unsaved_changes,
            rx.callout(
                rx.hstack(
                    rx.icon("info", size=16),
                    rx.text("You have unsaved changes", size="2"),
                    spacing="2"
                ),
                color_scheme="amber",
                size="1"
            ),
            rx.fragment()
        ),

        spacing="4",
        width="100%"
    )


def settings_tabs() -> rx.Component:
    """Settings navigation tabs."""
    tabs = [
        {"id": "profile", "label": "User Profile", "icon": "user"},
        {"id": "team", "label": "Team", "icon": "users"},
        {"id": "system", "label": "System", "icon": "settings"},
        {"id": "notifications", "label": "Notifications", "icon": "bell"},
        {"id": "integrations", "label": "Integrations", "icon": "plug"},
        {"id": "security", "label": "Security", "icon": "shield"}
    ]

    return rx.hstack(
        *[
            rx.button(
                rx.hstack(
                    rx.icon(tab["icon"], size=16),
                    rx.text(tab["label"], size="2"),
                    spacing="2"
                ),
                variant="ghost" if settings_state.active_tab != tab["id"] else "solid",
                color_scheme="blue" if settings_state.active_tab == tab["id"] else "gray",
                size="2",
                on_click=lambda tab_id=tab["id"]: setattr(settings_state, 'active_tab', tab_id)
            )
            for tab in tabs
        ],
        spacing="1",
        width="100%",
        wrap="wrap"
    )


def settings_content() -> rx.Component:
    """Dynamic settings content based on active tab."""
    return rx.box(
        rx.cond(
            settings_state.active_tab == "profile",
            user_profile_section(),
            rx.cond(
                settings_state.active_tab == "team",
                team_management_section(),
                rx.cond(
                    settings_state.active_tab == "system",
                    system_settings_section(),
                    rx.cond(
                        settings_state.active_tab == "notifications",
                        notification_settings_section(),
                        rx.cond(
                            settings_state.active_tab == "integrations",
                            integrations_section(),
                            rx.cond(
                                settings_state.active_tab == "security",
                                security_section(),
                                rx.text("Settings section not found", size="3", color="red")
                            )
                        )
                    )
                )
            )
        ),
        width="100%"
    )


def recent_activity_sidebar() -> rx.Component:
    """Recent activity sidebar."""
    return rx.vstack(
        rx.vstack(
            rx.heading("Recent Changes", size="4", weight="medium"),
            rx.text("Track your recent settings modifications", size="2", color="gray"),
            spacing="2"
        ),

        rx.vstack(
            *[
                rx.vstack(
                    rx.hstack(
                        rx.text(change["user"], size="2", weight="medium"),
                        rx.spacer(),
                        rx.text(
                            change["timestamp"][:10],  # Show just date
                            size="1",
                            color="gray"
                        ),
                        width="100%"
                    ),
                    rx.text(change["action"], size="2", weight="medium"),
                    rx.text(change["details"], size="2", color="gray"),
                    spacing="1",
                    align="start",
                    padding="3",
                    border_radius="6px",
                    border="1px solid",
                    border_color="gray.3",
                    width="100%"
                )
                for change in settings_state.recent_changes[:5]
            ],
            spacing="2",
            width="100%"
        ),

        rx.link(
            rx.button(
                "View All Activity",
                variant="outline",
                size="2",
                width="100%"
            ),
            href="/settings/activity"
        ),

        spacing="4",
        width="100%"
    )


def settings_page() -> rx.Component:
    """Main settings page layout."""
    return rx.vstack(
        settings_header(),

        # Main content area
        rx.hstack(
            # Left side - Settings content
            rx.vstack(
                settings_tabs(),

                rx.divider(),

                # Loading state
                rx.cond(
                    settings_state.loading,
                    rx.center(
                        rx.vstack(
                            rx.spinner(size="3"),
                            rx.text("Loading settings...", size="2", color="gray"),
                            spacing="3"
                        ),
                        height="400px",
                        width="100%"
                    ),
                    settings_content()
                ),

                # Error message
                rx.cond(
                    settings_state.error_message != "",
                    rx.callout(
                        rx.hstack(
                            rx.icon("x-circle", size=16),
                            rx.text(settings_state.error_message, size="2"),
                            spacing="2"
                        ),
                        color_scheme="red",
                        size="1"
                    ),
                    rx.fragment()
                ),

                # Success message
                rx.cond(
                    settings_state.success_message != "",
                    rx.callout(
                        rx.hstack(
                            rx.icon("check-circle", size=16),
                            rx.text(settings_state.success_message, size="2"),
                            spacing="2"
                        ),
                        color_scheme="green",
                        size="1"
                    ),
                    rx.fragment()
                ),

                spacing="4",
                width="100%",
                flex="1"
            ),

            # Right side - Recent activity
            recent_activity_sidebar(),

            spacing="6",
            width="100%",
            align="start"
        ),

        spacing="6",
        width="100%",
        padding="6"
    )


def settings_page_wrapper() -> rx.Component:
    """Settings page wrapper with proper layout."""
    return rx.container(
        settings_page(),
        max_width="1400px",
        padding="0"
    )