"""Conversion funnel component - Interactive funnel chart with real data."""

import reflex as rx
from ..analytics import lead_conversion_funnel

def conversion_funnel_chart() -> rx.Component:
    """Interactive conversion funnel chart with live data."""
    return lead_conversion_funnel()
