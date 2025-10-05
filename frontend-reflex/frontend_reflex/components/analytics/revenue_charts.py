"""Revenue charts component - Interactive revenue analytics with trend visualization."""

import reflex as rx
from ..analytics import revenue_trends_chart

def revenue_charts_section() -> rx.Component:
    """Interactive revenue charts with trend analysis."""
    return revenue_trends_chart()
