"""Notification settings component - Complete notification preferences interface."""

import reflex as rx
from .settings_state import settings_state


def email_notification_section() -> rx.Component:
    """Email notification preferences section."""
    return rx.vstack(
        rx.text("Email Notifications", size="4", weight="bold"),
        rx.text("Configure when you want to receive email notifications", size="2", color="gray"),

        rx.vstack(
            *[
                rx.hstack(
                    rx.vstack(
                        rx.text(category.replace("_", " ").title(), size="2", weight="medium"),
                        rx.text(
                            {
                                "new_leads": "Get notified when new leads are created",
                                "appointment_reminders": "Reminders for upcoming appointments",
                                "status_changes": "Updates when lead/project status changes",
                                "team_messages": "Messages from team members",
                                "system_updates": "System maintenance and feature updates",
                                "performance_reports": "Weekly and monthly performance summaries"
                            }.get(category, "Notification description"),
                            size="1",
                            color="gray"
                        ),
                        spacing="1",
                        align="start",
                        flex="1"
                    ),
                    rx.spacer(),
                    rx.vstack(
                        rx.switch(
                            checked=settings_state.notification_preferences.email_notifications[category]["enabled"],
                            size="2"
                        ),
                        rx.cond(
                            settings_state.notification_preferences.email_notifications[category]["enabled"],
                            rx.select.root(
                                rx.select.trigger(
                                    rx.select.value(
                                        placeholder=settings_state.notification_preferences.email_notifications[category]["frequency"].title()
                                    ),
                                    width="120px",
                                    size="1"
                                ),
                                rx.select.content(
                                    rx.select.item("Instant", value="instant"),
                                    rx.select.item("Hourly", value="hourly"),
                                    rx.select.item("Daily", value="daily"),
                                    rx.select.item("Weekly", value="weekly")
                                )
                            ),
                            rx.fragment()
                        ),
                        spacing="2",
                        align="center"
                    ),
                    align="center",
                    width="100%",
                    padding="4",
                    border_radius="8px",
                    border="1px solid",
                    border_color="gray.3"
                )
                for category in settings_state.notification_preferences.email_notifications.keys()
            ],
            spacing="3",
            width="100%"
        ),

        # Email digest settings
        rx.vstack(
            rx.text("Email Digest", size="3", weight="medium"),
            rx.text("Combine multiple notifications into a single digest email", size="2", color="gray"),

            rx.hstack(
                rx.text("Send daily digest at", size="2"),
                rx.input(
                    value="08:00",
                    type="time",
                    width="100px",
                    size="2"
                ),
                spacing="2",
                align="center"
            ),

            rx.checkbox(
                "Include performance metrics in digest",
                checked=True,
                size="2"
            ),

            spacing="2",
            width="100%"
        ),

        spacing="6",
        width="100%"
    )


def sms_notification_section() -> rx.Component:
    """SMS notification preferences section."""
    return rx.vstack(
        rx.text("SMS Notifications", size="4", weight="bold"),
        rx.text("Configure SMS alerts for critical notifications", size="2", color="gray"),

        # SMS verification status
        rx.callout(
            rx.hstack(
                rx.icon("smartphone", size=16),
                rx.vstack(
                    rx.text("SMS notifications require phone verification", size="2", weight="medium"),
                    rx.cond(
                        settings_state.user_profile.phone_verified,
                        rx.text("Your phone number is verified", size="1", color="green"),
                        rx.hstack(
                            rx.text("Your phone number is not verified", size="1", color="red"),
                            rx.button("Verify Now", size="1", variant="outline"),
                            spacing="2"
                        )
                    ),
                    spacing="1",
                    align="start"
                ),
                spacing="2",
                align="center"
            ),
            color_scheme="blue" if settings_state.user_profile.phone_verified else "amber",
            size="1"
        ),

        rx.vstack(
            *[
                rx.hstack(
                    rx.vstack(
                        rx.text(category.replace("_", " ").title(), size="2", weight="medium"),
                        rx.text(
                            {
                                "critical_alerts": "System failures, security issues",
                                "lead_responses": "New lead responses and inquiries",
                                "appointment_confirmations": "Appointment confirmations and changes",
                                "urgent_messages": "High priority team messages"
                            }.get(category, "SMS notification type"),
                            size="1",
                            color="gray"
                        ),
                        spacing="1",
                        align="start",
                        flex="1"
                    ),
                    rx.spacer(),
                    rx.switch(
                        checked=settings_state.notification_preferences.sms_notifications[category],
                        size="2",
                        disabled=not settings_state.user_profile.phone_verified
                    ),
                    align="center",
                    width="100%",
                    padding="4",
                    border_radius="8px",
                    border="1px solid",
                    border_color="gray.3"
                )
                for category in settings_state.notification_preferences.sms_notifications.keys()
            ],
            spacing="3",
            width="100%"
        ),

        # SMS rate limiting
        rx.vstack(
            rx.text("SMS Rate Limiting", size="3", weight="medium"),
            rx.text("Prevent SMS spam with automatic rate limiting", size="2", color="gray"),

            rx.hstack(
                rx.text("Maximum SMS per hour:", size="2"),
                rx.input(
                    value="10",
                    type="number",
                    width="80px",
                    size="2"
                ),
                spacing="2",
                align="center"
            ),

            spacing="2",
            width="100%"
        ),

        spacing="6",
        width="100%"
    )


def push_notification_section() -> rx.Component:
    """Push notification preferences section."""
    return rx.vstack(
        rx.text("Push Notifications", size="4", weight="bold"),
        rx.text("Configure browser and mobile push notifications", size="2", color="gray"),

        # Desktop notifications
        rx.vstack(
            rx.text("Desktop Notifications", size="3", weight="medium"),

            rx.hstack(
                rx.vstack(
                    rx.text("Browser notifications", size="2"),
                    rx.text("Show notifications in your browser", size="1", color="gray"),
                    spacing="1",
                    align="start",
                    flex="1"
                ),
                rx.spacer(),
                rx.switch(
                    checked=settings_state.notification_preferences.push_notifications["desktop_enabled"],
                    size="2"
                ),
                align="center",
                width="100%"
            ),

            rx.hstack(
                rx.vstack(
                    rx.text("Sound alerts", size="2"),
                    rx.text("Play notification sounds", size="1", color="gray"),
                    spacing="1",
                    align="start",
                    flex="1"
                ),
                rx.spacer(),
                rx.switch(
                    checked=settings_state.notification_preferences.push_notifications["sound_alerts"],
                    size="2",
                    disabled=not settings_state.notification_preferences.push_notifications["desktop_enabled"]
                ),
                align="center",
                width="100%"
            ),

            spacing="3",
            width="100%"
        ),

        # Mobile notifications
        rx.vstack(
            rx.text("Mobile Notifications", size="3", weight="medium"),

            rx.hstack(
                rx.vstack(
                    rx.text("Mobile push notifications", size="2"),
                    rx.text("Receive notifications on your mobile device", size="1", color="gray"),
                    spacing="1",
                    align="start",
                    flex="1"
                ),
                rx.spacer(),
                rx.switch(
                    checked=settings_state.notification_preferences.push_notifications["mobile_enabled"],
                    size="2"
                ),
                align="center",
                width="100%"
            ),

            spacing="3",
            width="100%"
        ),

        # Quiet hours
        rx.vstack(
            rx.text("Quiet Hours", size="3", weight="medium"),
            rx.text("Disable notifications during specified hours", size="2", color="gray"),

            rx.hstack(
                rx.text("From", size="2"),
                rx.input(
                    value=settings_state.notification_preferences.push_notifications["quiet_hours_start"],
                    type="time",
                    width="100px",
                    size="2"
                ),
                rx.text("to", size="2"),
                rx.input(
                    value=settings_state.notification_preferences.push_notifications["quiet_hours_end"],
                    type="time",
                    width="100px",
                    size="2"
                ),
                spacing="2",
                align="center"
            ),

            rx.checkbox(
                "Apply quiet hours to weekends only",
                checked=False,
                size="2"
            ),

            spacing="2",
            width="100%"
        ),

        spacing="6",
        width="100%"
    )


def alert_rules_section() -> rx.Component:
    """Custom alert rules section."""
    return rx.vstack(
        rx.text("Custom Alert Rules", size="4", weight="bold"),
        rx.text("Set up custom conditions for notifications", size="2", color="gray"),

        # Add new rule button
        rx.button(
            rx.hstack(
                rx.icon("plus", size=16),
                rx.text("Create Alert Rule"),
                spacing="2"
            ),
            variant="outline",
            size="2"
        ),

        # Sample alert rules
        rx.vstack(
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.text("High Value Lead Alert", size="2", weight="bold"),
                            rx.text("Notify when lead value exceeds $50,000", size="1", color="gray"),
                            spacing="1",
                            align="start"
                        ),
                        rx.spacer(),
                        rx.hstack(
                            rx.badge("Active", color_scheme="green"),
                            rx.button(
                                rx.icon("settings", size=14),
                                size="1",
                                variant="ghost"
                            ),
                            rx.button(
                                rx.icon("trash-2", size=14),
                                size="1",
                                variant="ghost",
                                color_scheme="red"
                            ),
                            spacing="2"
                        ),
                        align="center",
                        width="100%"
                    ),

                    rx.hstack(
                        rx.text("Channels:", size="1", color="gray"),
                        rx.badge("Email", size="1", variant="outline"),
                        rx.badge("SMS", size="1", variant="outline"),
                        rx.badge("Push", size="1", variant="outline"),
                        spacing="2",
                        align="center"
                    ),

                    spacing="2",
                    align="start"
                ),
                padding="4"
            ),

            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.text("Lead Response Overdue", size="2", weight="bold"),
                            rx.text("Alert when lead hasn't been contacted within 5 minutes", size="1", color="gray"),
                            spacing="1",
                            align="start"
                        ),
                        rx.spacer(),
                        rx.hstack(
                            rx.badge("Active", color_scheme="green"),
                            rx.button(
                                rx.icon("settings", size=14),
                                size="1",
                                variant="ghost"
                            ),
                            rx.button(
                                rx.icon("trash-2", size=14),
                                size="1",
                                variant="ghost",
                                color_scheme="red"
                            ),
                            spacing="2"
                        ),
                        align="center",
                        width="100%"
                    ),

                    rx.hstack(
                        rx.text("Channels:", size="1", color="gray"),
                        rx.badge("SMS", size="1", variant="outline"),
                        rx.badge("Push", size="1", variant="outline"),
                        spacing="2",
                        align="center"
                    ),

                    spacing="2",
                    align="start"
                ),
                padding="4"
            ),

            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.text("Weekly Performance Summary", size="2", weight="bold"),
                            rx.text("Send performance summary every Monday at 9 AM", size="1", color="gray"),
                            spacing="1",
                            align="start"
                        ),
                        rx.spacer(),
                        rx.hstack(
                            rx.badge("Active", color_scheme="green"),
                            rx.button(
                                rx.icon("settings", size=14),
                                size="1",
                                variant="ghost"
                            ),
                            rx.button(
                                rx.icon("trash-2", size=14),
                                size="1",
                                variant="ghost",
                                color_scheme="red"
                            ),
                            spacing="2"
                        ),
                        align="center",
                        width="100%"
                    ),

                    rx.hstack(
                        rx.text("Channels:", size="1", color="gray"),
                        rx.badge("Email", size="1", variant="outline"),
                        spacing="2",
                        align="center"
                    ),

                    spacing="2",
                    align="start"
                ),
                padding="4"
            ),

            spacing="3",
            width="100%"
        ),

        spacing="6",
        width="100%"
    )


def notification_history_section() -> rx.Component:
    """Notification history and testing section."""
    return rx.vstack(
        rx.text("Notification History & Testing", size="4", weight="bold"),

        # Test notifications
        rx.vstack(
            rx.text("Test Notifications", size="3", weight="medium"),
            rx.text("Send test notifications to verify your settings", size="2", color="gray"),

            rx.hstack(
                rx.button(
                    rx.hstack(
                        rx.icon("mail", size=14),
                        rx.text("Test Email"),
                        spacing="2"
                    ),
                    variant="outline",
                    size="2"
                ),
                rx.button(
                    rx.hstack(
                        rx.icon("smartphone", size=14),
                        rx.text("Test SMS"),
                        spacing="2"
                    ),
                    variant="outline",
                    size="2",
                    disabled=not settings_state.user_profile.phone_verified
                ),
                rx.button(
                    rx.hstack(
                        rx.icon("bell", size=14),
                        rx.text("Test Push"),
                        spacing="2"
                    ),
                    variant="outline",
                    size="2"
                ),
                spacing="2"
            ),

            spacing="2",
            width="100%"
        ),

        # Recent notifications
        rx.vstack(
            rx.text("Recent Notifications", size="3", weight="medium"),
            rx.text("Last 10 notifications sent to you", size="2", color="gray"),

            rx.vstack(
                *[
                    rx.hstack(
                        rx.icon("mail", size=14, color="blue"),
                        rx.vstack(
                            rx.text(f"New lead: {name}", size="2", weight="medium"),
                            rx.text(f"Sent {time} ago", size="1", color="gray"),
                            spacing="1",
                            align="start"
                        ),
                        rx.spacer(),
                        rx.badge("Email", variant="outline", size="1"),
                        align="center",
                        width="100%",
                        padding="3",
                        border_radius="6px",
                        border="1px solid",
                        border_color="gray.2"
                    )
                    for name, time in [
                        ("Sarah Johnson - Roof Repair", "5 minutes"),
                        ("Mike Davis - Full Replacement", "1 hour"),
                        ("Jennifer Wilson - Inspection", "3 hours"),
                        ("Robert Brown - Gutter Cleaning", "1 day"),
                        ("Lisa Taylor - Emergency Repair", "2 days")
                    ]
                ],
                spacing="2",
                width="100%",
                max_height="300px",
                overflow="auto"
            ),

            spacing="2",
            width="100%"
        ),

        spacing="6",
        width="100%"
    )


def notification_settings_section() -> rx.Component:
    """Complete notification settings section."""
    return rx.vstack(
        # Two-column layout
        rx.hstack(
            # Left column
            rx.vstack(
                email_notification_section(),
                rx.divider(),
                sms_notification_section(),
                spacing="6",
                width="100%",
                flex="1"
            ),

            # Right column
            rx.vstack(
                push_notification_section(),
                rx.divider(),
                alert_rules_section(),
                rx.divider(),
                notification_history_section(),
                spacing="6",
                width="100%",
                flex="1"
            ),

            spacing="8",
            width="100%",
            align="start"
        ),

        spacing="6",
        width="100%"
    )


def notification_settings_page() -> rx.Component:
    """Notification settings page wrapper."""
    return rx.container(
        rx.vstack(
            rx.heading("Notification Settings", size="6", weight="bold"),
            rx.text("Configure how and when you receive notifications", size="3", color="gray"),
            notification_settings_section(),
            spacing="6",
            align="stretch"
        ),
        max_width="1400px",
        padding="4"
    )