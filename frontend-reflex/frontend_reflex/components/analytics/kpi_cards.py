"""KPI cards component - Interactive KPI metrics with real data integration."""

import reflex as rx
from ..analytics import analytics_kpis

def kpi_cards_section() -> rx.Component:
    """Interactive KPI cards with live data."""
    return analytics_kpis()
