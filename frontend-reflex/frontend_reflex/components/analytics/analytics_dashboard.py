"""Analytics dashboard component - Comprehensive analytics with interactive charts."""

import reflex as rx
from ..analytics import analytics_dashboard_static

def analytics_dashboard() -> rx.Component:
    """Full analytics dashboard with charts and visualizations."""
    return analytics_dashboard_static()
