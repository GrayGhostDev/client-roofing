"""User profile component - Complete user profile management interface."""

import reflex as rx
from .settings_state import settings_state


def profile_photo_section() -> rx.Component:
    """Profile photo upload and management section."""
    return rx.vstack(
        rx.text("Profile Photo", size="3", weight="bold"),
        rx.hstack(
            rx.cond(
                settings_state.user_profile.profile_photo_url != "",
                rx.avatar(
                    src=settings_state.user_profile.profile_photo_url,
                    fallback=f"{settings_state.user_profile.first_name[:1]}{settings_state.user_profile.last_name[:1]}",
                    size="7"
                ),
                rx.avatar(
                    fallback=f"{settings_state.user_profile.first_name[:1]}{settings_state.user_profile.last_name[:1]}",
                    size="7"
                )
            ),
            rx.vstack(
                rx.button(
                    rx.hstack(
                        rx.icon("upload", size=16),
                        rx.text("Upload New Photo"),
                        spacing="2"
                    ),
                    variant="outline",
                    size="2"
                ),
                rx.button(
                    "Remove Photo",
                    variant="ghost",
                    color_scheme="red",
                    size="1"
                ),
                rx.text("JPG, PNG or GIF. Max size 2MB.", size="1", color="gray"),
                spacing="2",
                align="start"
            ),
            spacing="4",
            align="center"
        ),
        spacing="3",
        align="start",
        width="100%"
    )


def personal_information_section() -> rx.Component:
    """Personal information form section."""
    return rx.vstack(
        rx.text("Personal Information", size="4", weight="bold"),

        # Name fields
        rx.hstack(
            rx.vstack(
                rx.text("First Name", size="2", weight="medium"),
                rx.input(
                    value=settings_state.user_profile.first_name,
                    placeholder="First name",
                    width="100%"
                ),
                spacing="1",
                width="100%"
            ),
            rx.vstack(
                rx.text("Last Name", size="2", weight="medium"),
                rx.input(
                    value=settings_state.user_profile.last_name,
                    placeholder="Last name",
                    width="100%"
                ),
                spacing="1",
                width="100%"
            ),
            spacing="4",
            width="100%"
        ),

        # Email field with verification status
        rx.vstack(
            rx.hstack(
                rx.text("Email Address", size="2", weight="medium"),
                rx.cond(
                    settings_state.user_profile.email_verified,
                    rx.badge("Verified", color_scheme="green", variant="solid"),
                    rx.badge("Unverified", color_scheme="red", variant="solid")
                ),
                spacing="2",
                align="center"
            ),
            rx.hstack(
                rx.input(
                    value=settings_state.user_profile.email,
                    placeholder="email@company.com",
                    width="100%"
                ),
                rx.cond(
                    settings_state.user_profile.email_verified == False,
                    rx.button(
                        "Verify",
                        size="2",
                        variant="outline"
                    ),
                    rx.fragment()
                ),
                spacing="2",
                width="100%"
            ),
            spacing="1",
            width="100%"
        ),

        # Phone field with verification status
        rx.vstack(
            rx.hstack(
                rx.text("Phone Number", size="2", weight="medium"),
                rx.cond(
                    settings_state.user_profile.phone_verified,
                    rx.badge("Verified", color_scheme="green", variant="solid"),
                    rx.badge("Unverified", color_scheme="red", variant="solid")
                ),
                spacing="2",
                align="center"
            ),
            rx.hstack(
                rx.input(
                    value=settings_state.user_profile.phone,
                    placeholder="(248) 555-0123",
                    width="100%"
                ),
                rx.cond(
                    settings_state.user_profile.phone_verified == False,
                    rx.button(
                        "Verify",
                        size="2",
                        variant="outline"
                    ),
                    rx.fragment()
                ),
                spacing="2",
                width="100%"
            ),
            spacing="1",
            width="100%"
        ),

        # Bio field
        rx.vstack(
            rx.text("Bio", size="2", weight="medium"),
            rx.text_area(
                value=settings_state.user_profile.bio,
                placeholder="Tell us about yourself...",
                height="100px",
                width="100%"
            ),
            spacing="1",
            width="100%"
        ),

        spacing="4",
        align="start",
        width="100%"
    )


def account_settings_section() -> rx.Component:
    """Account settings and security section."""
    return rx.vstack(
        rx.text("Account Settings", size="4", weight="bold"),

        # Username
        rx.vstack(
            rx.text("Username", size="2", weight="medium"),
            rx.input(
                value=settings_state.user_profile.username,
                placeholder="username",
                width="100%"
            ),
            spacing="1",
            width="100%"
        ),

        # Password change
        rx.vstack(
            rx.text("Change Password", size="2", weight="medium"),
            rx.vstack(
                rx.input(
                    type="password",
                    placeholder="Current password",
                    width="100%"
                ),
                rx.input(
                    type="password",
                    placeholder="New password",
                    width="100%"
                ),
                rx.input(
                    type="password",
                    placeholder="Confirm new password",
                    width="100%"
                ),
                spacing="2",
                width="100%"
            ),
            spacing="1",
            width="100%"
        ),

        # Two-factor authentication
        rx.vstack(
            rx.hstack(
                rx.text("Two-Factor Authentication", size="2", weight="medium"),
                rx.switch(
                    checked=settings_state.user_profile.two_factor_enabled,
                    size="2"
                ),
                spacing="2",
                align="center",
                width="100%",
                justify="between"
            ),
            rx.text(
                "Add an extra layer of security to your account",
                size="1",
                color="gray"
            ),
            spacing="1",
            width="100%"
        ),

        # Session management
        rx.vstack(
            rx.text("Active Sessions", size="2", weight="medium"),
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text("Current Session - Chrome on Mac", size="2", weight="medium"),
                        rx.text("Detroit, MI • Last active: 2 minutes ago", size="1", color="gray"),
                        spacing="1",
                        align="start"
                    ),
                    rx.spacer(),
                    rx.badge("Current", color_scheme="green"),
                    align="center",
                    width="100%"
                ),
                rx.hstack(
                    rx.vstack(
                        rx.text("Mobile App - iPhone", size="2", weight="medium"),
                        rx.text("Detroit, MI • Last active: 1 hour ago", size="1", color="gray"),
                        spacing="1",
                        align="start"
                    ),
                    rx.spacer(),
                    rx.button("Revoke", size="1", variant="outline", color_scheme="red"),
                    align="center",
                    width="100%"
                ),
                spacing="3",
                width="100%"
            ),
            rx.button(
                "Revoke All Other Sessions",
                variant="outline",
                color_scheme="red",
                size="2"
            ),
            spacing="2",
            width="100%"
        ),

        spacing="4",
        align="start",
        width="100%"
    )


def preferences_section() -> rx.Component:
    """User preferences section."""
    return rx.vstack(
        rx.text("Preferences", size="4", weight="bold"),

        # Language selection
        rx.vstack(
            rx.text("Language", size="2", weight="medium"),
            rx.select.root(
                rx.select.trigger(
                    rx.select.value(placeholder="English"),
                    width="100%"
                ),
                rx.select.content(
                    rx.select.item("English", value="en"),
                    rx.select.item("Spanish", value="es"),
                    rx.select.item("French", value="fr")
                )
            ),
            spacing="1",
            width="100%"
        ),

        # Timezone
        rx.vstack(
            rx.text("Timezone", size="2", weight="medium"),
            rx.select.root(
                rx.select.trigger(
                    rx.select.value(placeholder="America/Detroit"),
                    width="100%"
                ),
                rx.select.content(
                    rx.select.item("Eastern Time", value="America/Detroit"),
                    rx.select.item("Central Time", value="America/Chicago"),
                    rx.select.item("Mountain Time", value="America/Denver"),
                    rx.select.item("Pacific Time", value="America/Los_Angeles")
                )
            ),
            spacing="1",
            width="100%"
        ),

        # Date format
        rx.vstack(
            rx.text("Date Format", size="2", weight="medium"),
            rx.select.root(
                rx.select.trigger(
                    rx.select.value(placeholder="MM/DD/YYYY"),
                    width="100%"
                ),
                rx.select.content(
                    rx.select.item("MM/DD/YYYY", value="MM/DD/YYYY"),
                    rx.select.item("DD/MM/YYYY", value="DD/MM/YYYY"),
                    rx.select.item("YYYY-MM-DD", value="YYYY-MM-DD")
                )
            ),
            spacing="1",
            width="100%"
        ),

        # Number format
        rx.vstack(
            rx.text("Number Format", size="2", weight="medium"),
            rx.select.root(
                rx.select.trigger(
                    rx.select.value(placeholder="US (1,234.56)"),
                    width="100%"
                ),
                rx.select.content(
                    rx.select.item("US (1,234.56)", value="US"),
                    rx.select.item("European (1.234,56)", value="EU"),
                    rx.select.item("International (1 234,56)", value="INTL")
                )
            ),
            spacing="1",
            width="100%"
        ),

        # Theme selection
        rx.vstack(
            rx.text("Theme", size="2", weight="medium"),
            rx.hstack(
                rx.button(
                    rx.vstack(
                        rx.icon("sun", size=20),
                        rx.text("Light", size="1"),
                        spacing="2"
                    ),
                    variant="outline" if settings_state.user_profile.theme != "light" else "solid",
                    color_scheme="blue" if settings_state.user_profile.theme == "light" else "gray",
                    height="60px",
                    width="80px"
                ),
                rx.button(
                    rx.vstack(
                        rx.icon("moon", size=20),
                        rx.text("Dark", size="1"),
                        spacing="2"
                    ),
                    variant="outline" if settings_state.user_profile.theme != "dark" else "solid",
                    color_scheme="blue" if settings_state.user_profile.theme == "dark" else "gray",
                    height="60px",
                    width="80px"
                ),
                rx.button(
                    rx.vstack(
                        rx.icon("monitor", size=20),
                        rx.text("Auto", size="1"),
                        spacing="2"
                    ),
                    variant="outline" if settings_state.user_profile.theme != "auto" else "solid",
                    color_scheme="blue" if settings_state.user_profile.theme == "auto" else "gray",
                    height="60px",
                    width="80px"
                ),
                spacing="2"
            ),
            spacing="2",
            width="100%"
        ),

        spacing="4",
        align="start",
        width="100%"
    )


def activity_section() -> rx.Component:
    """Account activity and history section."""
    return rx.vstack(
        rx.text("Account Activity", size="4", weight="bold"),

        # Last login info
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text("Last Login", size="2", weight="medium"),
                    rx.text(
                        f"October 5, 2024 at 10:30 AM",
                        size="2",
                        color="gray"
                    ),
                    spacing="1",
                    align="start"
                ),
                rx.spacer(),
                rx.icon("check-circle", size=16, color="green"),
                align="center",
                width="100%"
            ),
            spacing="2",
            width="100%"
        ),

        # Recent actions
        rx.vstack(
            rx.text("Recent Actions", size="2", weight="medium"),
            rx.vstack(
                rx.hstack(
                    rx.text("Updated profile photo", size="2"),
                    rx.spacer(),
                    rx.text("2 hours ago", size="1", color="gray"),
                    width="100%"
                ),
                rx.hstack(
                    rx.text("Changed password", size="2"),
                    rx.spacer(),
                    rx.text("1 day ago", size="1", color="gray"),
                    width="100%"
                ),
                rx.hstack(
                    rx.text("Enabled two-factor authentication", size="2"),
                    rx.spacer(),
                    rx.text("3 days ago", size="1", color="gray"),
                    width="100%"
                ),
                spacing="2",
                width="100%"
            ),
            spacing="2",
            width="100%"
        ),

        # Account statistics
        rx.vstack(
            rx.text("Account Statistics", size="2", weight="medium"),
            rx.grid(
                rx.card(
                    rx.vstack(
                        rx.text("Profile Completion", size="1", color="gray"),
                        rx.text("85%", size="4", weight="bold"),
                        spacing="1"
                    ),
                    padding="3"
                ),
                rx.card(
                    rx.vstack(
                        rx.text("Login Streak", size="1", color="gray"),
                        rx.text("12 days", size="4", weight="bold"),
                        spacing="1"
                    ),
                    padding="3"
                ),
                rx.card(
                    rx.vstack(
                        rx.text("Member Since", size="1", color="gray"),
                        rx.text("June 2023", size="4", weight="bold"),
                        spacing="1"
                    ),
                    padding="3"
                ),
                columns="3",
                spacing="3",
                width="100%"
            ),
            spacing="2",
            width="100%"
        ),

        spacing="4",
        align="start",
        width="100%"
    )


def user_profile_section() -> rx.Component:
    """Complete user profile management section."""
    return rx.vstack(
        # Profile photo section
        profile_photo_section(),

        rx.divider(),

        # Two-column layout for main content
        rx.hstack(
            # Left column
            rx.vstack(
                personal_information_section(),
                rx.divider(),
                account_settings_section(),
                spacing="6",
                width="100%",
                flex="1"
            ),

            # Right column
            rx.vstack(
                preferences_section(),
                rx.divider(),
                activity_section(),
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


def user_profile_page() -> rx.Component:
    """User profile page wrapper."""
    return rx.container(
        rx.vstack(
            rx.heading("User Profile", size="6", weight="bold"),
            rx.text("Manage your personal information and account settings", size="3", color="gray"),
            user_profile_section(),
            spacing="6",
            align="stretch"
        ),
        max_width="1200px",
        padding="4"
    )