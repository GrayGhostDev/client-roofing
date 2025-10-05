"""Security component - Complete security settings and policies interface."""

import reflex as rx
from .settings_state import settings_state


def password_policy_section() -> rx.Component:
    """Password policy configuration section."""
    return rx.vstack(
        rx.text("Password Policy", size="4", weight="bold"),
        rx.text("Configure password requirements for all users", size="2", color="gray"),

        rx.vstack(
            # Minimum length
            rx.hstack(
                rx.vstack(
                    rx.text("Minimum password length", size="2", weight="medium"),
                    rx.text("Require passwords to be at least this many characters", size="1", color="gray"),
                    spacing="1",
                    align="start",
                    flex="1"
                ),
                rx.hstack(
                    rx.input(
                        value=str(settings_state.security_settings.password_policy["min_length"]),
                        type="number",
                        width="80px",
                        min=6,
                        max=128
                    ),
                    rx.text("characters", size="2", color="gray"),
                    spacing="2",
                    align="center"
                ),
                align="center",
                width="100%",
                padding="3",
                border_radius="6px",
                border="1px solid",
                border_color="gray.3"
            ),

            # Character requirements
            rx.vstack(
                rx.text("Character Requirements", size="2", weight="medium"),

                rx.hstack(
                    rx.checkbox(
                        checked=settings_state.security_settings.password_policy["require_uppercase"],
                        size="2"
                    ),
                    rx.text("Require uppercase letters (A-Z)", size="2"),
                    spacing="2",
                    align="center",
                    width="100%"
                ),

                rx.hstack(
                    rx.checkbox(
                        checked=settings_state.security_settings.password_policy["require_lowercase"],
                        size="2"
                    ),
                    rx.text("Require lowercase letters (a-z)", size="2"),
                    spacing="2",
                    align="center",
                    width="100%"
                ),

                rx.hstack(
                    rx.checkbox(
                        checked=settings_state.security_settings.password_policy["require_numbers"],
                        size="2"
                    ),
                    rx.text("Require numbers (0-9)", size="2"),
                    spacing="2",
                    align="center",
                    width="100%"
                ),

                rx.hstack(
                    rx.checkbox(
                        checked=settings_state.security_settings.password_policy["require_special_chars"],
                        size="2"
                    ),
                    rx.text("Require special characters (!@#$%^&*)", size="2"),
                    spacing="2",
                    align="center",
                    width="100%"
                ),

                spacing="2",
                width="100%"
            ),

            # Password history
            rx.hstack(
                rx.vstack(
                    rx.text("Password history", size="2", weight="medium"),
                    rx.text("Prevent reusing recent passwords", size="1", color="gray"),
                    spacing="1",
                    align="start",
                    flex="1"
                ),
                rx.hstack(
                    rx.input(
                        value=str(settings_state.security_settings.password_policy["password_history"]),
                        type="number",
                        width="80px",
                        min=0,
                        max=24
                    ),
                    rx.text("passwords", size="2", color="gray"),
                    spacing="2",
                    align="center"
                ),
                align="center",
                width="100%",
                padding="3",
                border_radius="6px",
                border="1px solid",
                border_color="gray.3"
            ),

            spacing="3",
            width="100%"
        ),

        # Password strength indicator
        rx.vstack(
            rx.text("Test Password Strength", size="3", weight="medium"),
            rx.text("Test if a password meets your current policy", size="2", color="gray"),

            rx.vstack(
                rx.input(
                    placeholder="Type a password to test...",
                    type="password",
                    width="100%"
                ),

                rx.hstack(
                    rx.text("Strength:", size="2"),
                    rx.progress(
                        value=75,
                        max=100,
                        width="200px",
                        color_scheme="green"
                    ),
                    rx.text("Strong", size="2", weight="medium", color="green"),
                    spacing="2",
                    align="center"
                ),

                rx.vstack(
                    rx.hstack(
                        rx.icon("check", size=14, color="green"),
                        rx.text("At least 8 characters", size="1"),
                        spacing="2"
                    ),
                    rx.hstack(
                        rx.icon("check", size=14, color="green"),
                        rx.text("Contains uppercase letter", size="1"),
                        spacing="2"
                    ),
                    rx.hstack(
                        rx.icon("check", size=14, color="green"),
                        rx.text("Contains lowercase letter", size="1"),
                        spacing="2"
                    ),
                    rx.hstack(
                        rx.icon("x", size=14, color="red"),
                        rx.text("Contains number", size="1"),
                        spacing="2"
                    ),
                    spacing="1",
                    align="start"
                ),

                spacing="2",
                width="100%"
            ),

            spacing="2",
            width="100%"
        ),

        spacing="6",
        width="100%"
    )


def session_security_section() -> rx.Component:
    """Session security configuration section."""
    return rx.vstack(
        rx.text("Session Security", size="4", weight="bold"),
        rx.text("Configure session timeouts and security", size="2", color="gray"),

        rx.vstack(
            # Session timeout
            rx.hstack(
                rx.vstack(
                    rx.text("Session timeout", size="2", weight="medium"),
                    rx.text("Automatically log out inactive users", size="1", color="gray"),
                    spacing="1",
                    align="start",
                    flex="1"
                ),
                rx.hstack(
                    rx.input(
                        value=str(settings_state.security_settings.session_timeout_minutes),
                        type="number",
                        width="100px",
                        min=15,
                        max=1440
                    ),
                    rx.text("minutes", size="2", color="gray"),
                    spacing="2",
                    align="center"
                ),
                align="center",
                width="100%",
                padding="3",
                border_radius="6px",
                border="1px solid",
                border_color="gray.3"
            ),

            # Concurrent sessions
            rx.hstack(
                rx.vstack(
                    rx.text("Maximum concurrent sessions", size="2", weight="medium"),
                    rx.text("Limit number of simultaneous logins", size="1", color="gray"),
                    spacing="1",
                    align="start",
                    flex="1"
                ),
                rx.hstack(
                    rx.input(
                        value="3",
                        type="number",
                        width="80px",
                        min=1,
                        max=10
                    ),
                    rx.text("sessions", size="2", color="gray"),
                    spacing="2",
                    align="center"
                ),
                align="center",
                width="100%",
                padding="3",
                border_radius="6px",
                border="1px solid",
                border_color="gray.3"
            ),

            spacing="3",
            width="100%"
        ),

        # Security options
        rx.vstack(
            rx.text("Security Options", size="3", weight="medium"),

            rx.vstack(
                rx.hstack(
                    rx.checkbox(
                        checked=True,
                        size="2"
                    ),
                    rx.text("Force logout on password change", size="2"),
                    spacing="2",
                    align="center",
                    width="100%"
                ),

                rx.hstack(
                    rx.checkbox(
                        checked=True,
                        size="2"
                    ),
                    rx.text("Log security events", size="2"),
                    spacing="2",
                    align="center",
                    width="100%"
                ),

                rx.hstack(
                    rx.checkbox(
                        checked=False,
                        size="2"
                    ),
                    rx.text("Require two-factor authentication for all users", size="2"),
                    spacing="2",
                    align="center",
                    width="100%"
                ),

                spacing="2",
                width="100%"
            ),

            spacing="2",
            width="100%"
        ),

        spacing="6",
        width="100%"
    )


def access_control_section() -> rx.Component:
    """Access control and IP restrictions section."""
    return rx.vstack(
        rx.text("Access Control", size="4", weight="bold"),
        rx.text("Manage IP restrictions and access controls", size="2", color="gray"),

        # IP Whitelist
        rx.vstack(
            rx.text("IP Whitelist", size="3", weight="medium"),
            rx.text("Restrict access to specific IP addresses", size="2", color="gray"),

            rx.hstack(
                rx.input(
                    placeholder="Enter IP address (e.g., 192.168.1.100)",
                    width="300px"
                ),
                rx.button(
                    rx.hstack(
                        rx.icon("plus", size=14),
                        rx.text("Add IP"),
                        spacing="2"
                    ),
                    variant="outline",
                    size="2"
                ),
                spacing="2",
                align="center"
            ),

            rx.cond(
                len(settings_state.security_settings.ip_whitelist) > 0,
                rx.vstack(
                    *[
                        rx.hstack(
                            rx.text(ip, size="2", weight="medium"),
                            rx.spacer(),
                            rx.button(
                                rx.icon("x", size=14),
                                size="1",
                                variant="ghost",
                                color_scheme="red"
                            ),
                            align="center",
                            width="100%",
                            padding="2",
                            border_radius="4px",
                            border="1px solid",
                            border_color="gray.3"
                        )
                        for ip in settings_state.security_settings.ip_whitelist
                    ],
                    spacing="2",
                    width="100%"
                ),
                rx.text("No IP addresses whitelisted. All IPs are allowed.", size="2", color="gray", style={"font-style": "italic"})
            ),

            spacing="3",
            width="100%"
        ),

        # Failed login protection
        rx.vstack(
            rx.text("Failed Login Protection", size="3", weight="medium"),
            rx.text("Protect against brute force attacks", size="2", color="gray"),

            rx.hstack(
                rx.text("Block IP after", size="2"),
                rx.input(
                    value="5",
                    type="number",
                    width="80px",
                    min=3,
                    max=20
                ),
                rx.text("failed attempts", size="2", color="gray"),
                spacing="2",
                align="center"
            ),

            rx.hstack(
                rx.text("Block duration", size="2"),
                rx.input(
                    value="30",
                    type="number",
                    width="80px",
                    min=5,
                    max=1440
                ),
                rx.text("minutes", size="2", color="gray"),
                spacing="2",
                align="center"
            ),

            spacing="3",
            width="100%"
        ),

        spacing="6",
        width="100%"
    )


def audit_logging_section() -> rx.Component:
    """Audit logging configuration section."""
    return rx.vstack(
        rx.text("Audit Logging", size="4", weight="bold"),
        rx.text("Configure security event logging and retention", size="2", color="gray"),

        # Log retention
        rx.hstack(
            rx.vstack(
                rx.text("Log retention period", size="2", weight="medium"),
                rx.text("How long to keep audit logs", size="1", color="gray"),
                spacing="1",
                align="start",
                flex="1"
            ),
            rx.hstack(
                rx.input(
                    value=str(settings_state.security_settings.audit_log_retention_days),
                    type="number",
                    width="100px",
                    min=7,
                    max=2555
                ),
                rx.text("days", size="2", color="gray"),
                spacing="2",
                align="center"
            ),
            align="center",
            width="100%",
            padding="3",
            border_radius="6px",
            border="1px solid",
            border_color="gray.3"
        ),

        # Events to log
        rx.vstack(
            rx.text("Events to Log", size="3", weight="medium"),

            rx.vstack(
                rx.hstack(
                    rx.checkbox(checked=True, size="2"),
                    rx.text("User login/logout", size="2"),
                    spacing="2",
                    align="center",
                    width="100%"
                ),

                rx.hstack(
                    rx.checkbox(checked=True, size="2"),
                    rx.text("Password changes", size="2"),
                    spacing="2",
                    align="center",
                    width="100%"
                ),

                rx.hstack(
                    rx.checkbox(checked=True, size="2"),
                    rx.text("Failed login attempts", size="2"),
                    spacing="2",
                    align="center",
                    width="100%"
                ),

                rx.hstack(
                    rx.checkbox(checked=True, size="2"),
                    rx.text("Data exports", size="2"),
                    spacing="2",
                    align="center",
                    width="100%"
                ),

                rx.hstack(
                    rx.checkbox(checked=False, size="2"),
                    rx.text("All data modifications", size="2"),
                    spacing="2",
                    align="center",
                    width="100%"
                ),

                spacing="2",
                width="100%"
            ),

            spacing="2",
            width="100%"
        ),

        # Recent security events
        rx.vstack(
            rx.text("Recent Security Events", size="3", weight="medium"),
            rx.text("Last 10 security-related events", size="2", color="gray"),

            rx.vstack(
                *[
                    rx.hstack(
                        rx.icon(icon, size=14, color=color),
                        rx.vstack(
                            rx.text(event, size="2", weight="medium"),
                            rx.text(f"{user} • {time}", size="1", color="gray"),
                            spacing="1",
                            align="start"
                        ),
                        rx.spacer(),
                        rx.badge(status, color_scheme=status_color, size="1"),
                        align="center",
                        width="100%",
                        padding="3",
                        border_radius="6px",
                        border="1px solid",
                        border_color="gray.2"
                    )
                    for event, user, time, status, status_color, icon, color in [
                        ("Successful login", "john.manager@iswitchroofs.com", "2 minutes ago", "Success", "green", "check-circle", "green"),
                        ("Password changed", "sarah.johnson@iswitchroofs.com", "1 hour ago", "Success", "green", "key", "blue"),
                        ("Failed login attempt", "unknown@attacker.com", "3 hours ago", "Blocked", "red", "x-circle", "red"),
                        ("Data export", "emily.chen@iswitchroofs.com", "1 day ago", "Success", "green", "download", "blue"),
                        ("Two-factor enabled", "mike.rodriguez@iswitchroofs.com", "2 days ago", "Success", "green", "shield", "green")
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


def data_protection_section() -> rx.Component:
    """Data protection and retention policies section."""
    return rx.vstack(
        rx.text("Data Protection", size="4", weight="bold"),
        rx.text("Configure data retention and privacy policies", size="2", color="gray"),

        # Data retention policies
        rx.vstack(
            rx.text("Data Retention Policies", size="3", weight="medium"),
            rx.text("How long different types of data are kept", size="2", color="gray"),

            rx.vstack(
                *[
                    rx.hstack(
                        rx.text(data_type.replace("_", " ").title(), size="2", weight="medium", width="150px"),
                        rx.input(
                            value=str(days),
                            type="number",
                            width="100px",
                            min=30
                        ),
                        rx.text("days", size="2", color="gray"),
                        spacing="3",
                        align="center",
                        width="100%",
                        padding="2",
                        border_radius="4px",
                        border="1px solid",
                        border_color="gray.3"
                    )
                    for data_type, days in settings_state.security_settings.data_retention_policy.items()
                ],
                spacing="2",
                width="100%"
            ),

            spacing="2",
            width="100%"
        ),

        # Data encryption
        rx.vstack(
            rx.text("Data Encryption", size="3", weight="medium"),

            rx.vstack(
                rx.hstack(
                    rx.icon("shield-check", size=16, color="green"),
                    rx.text("Data at rest encryption", size="2"),
                    rx.spacer(),
                    rx.badge("Enabled", color_scheme="green"),
                    align="center",
                    width="100%"
                ),

                rx.hstack(
                    rx.icon("shield-check", size=16, color="green"),
                    rx.text("Data in transit encryption (TLS)", size="2"),
                    rx.spacer(),
                    rx.badge("Enabled", color_scheme="green"),
                    align="center",
                    width="100%"
                ),

                rx.hstack(
                    rx.icon("shield-check", size=16, color="green"),
                    rx.text("Database encryption", size="2"),
                    rx.spacer(),
                    rx.badge("Enabled", color_scheme="green"),
                    align="center",
                    width="100%"
                ),

                spacing="2",
                width="100%"
            ),

            spacing="2",
            width="100%"
        ),

        # Privacy controls
        rx.vstack(
            rx.text("Privacy Controls", size="3", weight="medium"),

            rx.vstack(
                rx.hstack(
                    rx.checkbox(checked=True, size="2"),
                    rx.text("Anonymize exported data", size="2"),
                    spacing="2",
                    align="center",
                    width="100%"
                ),

                rx.hstack(
                    rx.checkbox(checked=True, size="2"),
                    rx.text("Require consent for data collection", size="2"),
                    spacing="2",
                    align="center",
                    width="100%"
                ),

                rx.hstack(
                    rx.checkbox(checked=False, size="2"),
                    rx.text("Enable data subject access requests", size="2"),
                    spacing="2",
                    align="center",
                    width="100%"
                ),

                spacing="2",
                width="100%"
            ),

            spacing="2",
            width="100%"
        ),

        spacing="6",
        width="100%"
    )


def security_section() -> rx.Component:
    """Complete security settings section."""
    return rx.vstack(
        # Two-column layout
        rx.hstack(
            # Left column
            rx.vstack(
                password_policy_section(),
                rx.divider(),
                session_security_section(),
                rx.divider(),
                access_control_section(),
                spacing="6",
                width="100%",
                flex="1"
            ),

            # Right column
            rx.vstack(
                audit_logging_section(),
                rx.divider(),
                data_protection_section(),
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