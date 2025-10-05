"""Team performance component - Interactive team analytics and performance tracking."""

import reflex as rx
from ..analytics import team_performance_chart

def team_performance_section() -> rx.Component:
    """Interactive team performance analytics with individual metrics."""
    return team_performance_chart()
