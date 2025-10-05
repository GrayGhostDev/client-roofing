"""Settings components - Complete settings management system."""

import reflex as rx
from .settings.settings_page import settings_page_wrapper
from .settings.settings_state import settings_state


def settings_page_static() -> rx.Component:
    """Static settings page structure - replaced with comprehensive implementation."""
    return settings_page_wrapper()


def settings_page() -> rx.Component:
    """Complete settings page with full functionality."""
    return settings_page_wrapper()


# Aliases for backward compatibility
settings_dashboard = settings_page