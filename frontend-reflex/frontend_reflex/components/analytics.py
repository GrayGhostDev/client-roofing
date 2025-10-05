"""
Comprehensive Analytics Dashboard - Interactive charts and visualizations
for the iSwitch Roofs CRM system with real-time data integration.
"""

import reflex as rx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..dashboard_state import DashboardState, DashboardMetrics


class AnalyticsState(rx.State):
    """Analytics-specific state management for chart data and filtering."""

    # Date range filtering
    date_range: str = "30d"  # 7d, 30d, 90d, 12m
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    # Chart data loading states
    loading_charts: bool = False
    chart_error: str = ""

    # Chart data
    lead_funnel_data: List[Dict[str, Any]] = [
        {"stage": "Leads", "count": 150, "percentage": 100},
        {"stage": "Qualified", "count": 105, "percentage": 70},
        {"stage": "Appointments", "count": 75, "percentage": 50},
        {"stage": "Estimates", "count": 45, "percentage": 30},
        {"stage": "Closed", "count": 22, "percentage": 15},
    ]

    revenue_trend_data: List[Dict[str, Any]] = [
        {"month": "Jan", "revenue": 45000, "target": 50000, "projects": 15},
        {"month": "Feb", "revenue": 52000, "target": 50000, "projects": 18},
        {"month": "Mar", "revenue": 48000, "target": 55000, "projects": 16},
        {"month": "Apr", "revenue": 61000, "target": 55000, "projects": 22},
        {"month": "May", "revenue": 58000, "target": 60000, "projects": 19},
        {"month": "Jun", "revenue": 71000, "target": 60000, "projects": 25},
    ]

    lead_sources_data: List[Dict[str, Any]] = [
        {"source": "Google Ads", "leads": 45, "percentage": 30, "cost": 3200},
        {"source": "Facebook", "leads": 35, "percentage": 23, "cost": 1800},
        {"source": "Referrals", "leads": 40, "percentage": 27, "cost": 800},
        {"source": "Website", "leads": 20, "percentage": 13, "cost": 500},
        {"source": "Other", "leads": 10, "percentage": 7, "cost": 200},
    ]

    team_performance_data: List[Dict[str, Any]] = [
        {"name": "Sarah Johnson", "leads": 28, "conversions": 12, "revenue": 58000},
        {"name": "Mike Chen", "leads": 35, "conversions": 15, "revenue": 72000},
        {"name": "Lisa Rodriguez", "leads": 22, "conversions": 9, "revenue": 45000},
        {"name": "David Kim", "leads": 31, "conversions": 14, "revenue": 69000},
    ]

    project_status_data: List[Dict[str, Any]] = [
        {"status": "Planning", "count": 8, "percentage": 20},
        {"status": "In Progress", "count": 15, "percentage": 37.5},
        {"status": "Materials", "count": 5, "percentage": 12.5},
        {"status": "Completion", "count": 12, "percentage": 30},
    ]

    response_time_data: List[Dict[str, Any]] = [
        {"day": "Mon", "avg_response": 2.1, "target": 2.0},
        {"day": "Tue", "avg_response": 1.8, "target": 2.0},
        {"day": "Wed", "avg_response": 2.4, "target": 2.0},
        {"day": "Thu", "avg_response": 1.9, "target": 2.0},
        {"day": "Fri", "avg_response": 2.2, "target": 2.0},
        {"day": "Sat", "avg_response": 3.1, "target": 2.0},
        {"day": "Sun", "avg_response": 2.8, "target": 2.0},
    ]

    def set_date_range(self, range_value: str):
        """Set the date range for analytics filtering."""
        self.date_range = range_value
        # In real implementation, this would trigger data reload

    def refresh_chart_data(self):
        """Refresh all chart data from backend API."""
        self.loading_charts = True
        # In real implementation, make API calls here
        # For now, simulate loading delay
        self.loading_charts = False

    def export_data(self, chart_type: str):
        """Export chart data to CSV/Excel."""
        # Implementation would generate downloadable file
        pass


def kpi_metric_card(title: str, value: str, change: str, trend: str, icon: str) -> rx.Component:
    """Individual KPI metric card component."""
    trend_color = "green" if trend == "up" else "red" if trend == "down" else "gray"
    trend_icon = "trending_up" if trend == "up" else "trending_down" if trend == "down" else "trending_flat"

    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon(icon, size=24, color="blue"),
                rx.spacer(),
                rx.icon(trend_icon, size=16, color=trend_color),
                width="100%",
                align="center",
            ),
            rx.text(title, size="2", color="gray", weight="medium"),
            rx.text(value, size="6", weight="bold"),
            rx.text(change, size="2", color=trend_color, weight="medium"),
            spacing="2",
            align="start",
        ),
        width="100%",
        padding="4",
    )


def analytics_kpis() -> rx.Component:
    """KPI metrics row for analytics dashboard."""
    return rx.grid(
        kpi_metric_card(
            "Total Revenue",
            DashboardState.metrics_formatted["monthly_revenue"],
            "+12.5% vs last month",
            "up",
            "dollar_sign"
        ),
        kpi_metric_card(
            "Lead Conversion",
            DashboardState.metrics_formatted["conversion_rate"],
            "+3.2% vs last month",
            "up",
            "target"
        ),
        kpi_metric_card(
            "Active Projects",
            DashboardState.metrics_formatted["active_projects"],
            "+2 vs last week",
            "up",
            "briefcase"
        ),
        kpi_metric_card(
            "Avg Response Time",
            DashboardState.metrics_formatted["response_time"],
            "-0.3min vs target",
            "down",
            "clock"
        ),
        columns="4",
        spacing="4",
        width="100%",
    )


def lead_conversion_funnel() -> rx.Component:
    """Lead conversion funnel chart component."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Lead Conversion Funnel", size="4"),
                rx.spacer(),
                rx.button(
                    rx.icon("download", size=16),
                    "Export",
                    variant="outline",
                    size="2",
                    on_click=AnalyticsState.export_data("funnel")
                ),
                width="100%",
                align="center",
            ),
            rx.recharts.bar_chart(
                rx.recharts.bar(
                    data_key="count",
                    fill="#8884d8",
                ),
                rx.recharts.x_axis(data_key="stage"),
                rx.recharts.y_axis(),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                rx.recharts.tooltip(),
                rx.recharts.legend(),
                data=AnalyticsState.lead_funnel_data,
                width="100%",
                height=300,
            ),
            spacing="4",
            width="100%",
        ),
        width="100%",
        padding="4",
    )


def revenue_trends_chart() -> rx.Component:
    """Revenue trends line chart component."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Revenue Trends", size="4"),
                rx.spacer(),
                rx.button(
                    rx.icon("download", size=16),
                    "Export",
                    variant="outline",
                    size="2",
                    on_click=AnalyticsState.export_data("revenue")
                ),
                width="100%",
                align="center",
            ),
            rx.recharts.line_chart(
                rx.recharts.line(
                    data_key="revenue",
                    stroke="#8884d8",
                    stroke_width=2,
                ),
                rx.recharts.line(
                    data_key="target",
                    stroke="#82ca9d",
                    stroke_width=2,
                    stroke_dasharray="5 5",
                ),
                rx.recharts.x_axis(data_key="month"),
                rx.recharts.y_axis(),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                rx.recharts.tooltip(),
                rx.recharts.legend(),
                data=AnalyticsState.revenue_trend_data,
                width="100%",
                height=300,
            ),
            spacing="4",
            width="100%",
        ),
        width="100%",
        padding="4",
    )


def lead_sources_chart() -> rx.Component:
    """Lead sources pie chart component."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Lead Sources", size="4"),
                rx.spacer(),
                rx.button(
                    rx.icon("download", size=16),
                    "Export",
                    variant="outline",
                    size="2",
                    on_click=AnalyticsState.export_data("sources")
                ),
                width="100%",
                align="center",
            ),
            rx.recharts.pie_chart(
                rx.recharts.pie(
                    data=AnalyticsState.lead_sources_data,
                    data_key="leads",
                    name_key="source",
                    cx="50%",
                    cy="50%",
                    outer_radius=80,
                    fill="#8884d8",
                    label=True,
                ),
                rx.recharts.tooltip(),
                rx.recharts.legend(),
                width="100%",
                height=300,
            ),
            spacing="4",
            width="100%",
        ),
        width="100%",
        padding="4",
    )


def team_performance_chart() -> rx.Component:
    """Team performance bar chart component."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Team Performance", size="4"),
                rx.spacer(),
                rx.button(
                    rx.icon("download", size=16),
                    "Export",
                    variant="outline",
                    size="2",
                    on_click=AnalyticsState.export_data("team")
                ),
                width="100%",
                align="center",
            ),
            rx.recharts.bar_chart(
                rx.recharts.bar(
                    data_key="conversions",
                    fill="#8884d8",
                    name="Conversions",
                ),
                rx.recharts.bar(
                    data_key="leads",
                    fill="#82ca9d",
                    name="Leads",
                ),
                rx.recharts.x_axis(data_key="name"),
                rx.recharts.y_axis(),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                rx.recharts.tooltip(),
                rx.recharts.legend(),
                data=AnalyticsState.team_performance_data,
                width="100%",
                height=300,
            ),
            spacing="4",
            width="100%",
        ),
        width="100%",
        padding="4",
    )


def project_status_chart() -> rx.Component:
    """Project status donut chart component."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Project Pipeline", size="4"),
                rx.spacer(),
                rx.button(
                    rx.icon("download", size=16),
                    "Export",
                    variant="outline",
                    size="2",
                    on_click=AnalyticsState.export_data("projects")
                ),
                width="100%",
                align="center",
            ),
            rx.recharts.pie_chart(
                rx.recharts.pie(
                    data=AnalyticsState.project_status_data,
                    data_key="count",
                    name_key="status",
                    cx="50%",
                    cy="50%",
                    inner_radius=40,
                    outer_radius=80,
                    fill="#8884d8",
                    label=True,
                ),
                rx.recharts.tooltip(),
                rx.recharts.legend(),
                width="100%",
                height=300,
            ),
            spacing="4",
            width="100%",
        ),
        width="100%",
        padding="4",
    )


def response_times_chart() -> rx.Component:
    """Response times trend chart component."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Response Times", size="4"),
                rx.spacer(),
                rx.button(
                    rx.icon("download", size=16),
                    "Export",
                    variant="outline",
                    size="2",
                    on_click=AnalyticsState.export_data("response")
                ),
                width="100%",
                align="center",
            ),
            rx.recharts.line_chart(
                rx.recharts.line(
                    data_key="avg_response",
                    stroke="#8884d8",
                    stroke_width=2,
                    name="Avg Response",
                ),
                rx.recharts.line(
                    data_key="target",
                    stroke="#ff7300",
                    stroke_width=2,
                    stroke_dasharray="5 5",
                    name="Target",
                ),
                rx.recharts.x_axis(data_key="day"),
                rx.recharts.y_axis(),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                rx.recharts.tooltip(),
                rx.recharts.legend(),
                data=AnalyticsState.response_time_data,
                width="100%",
                height=300,
            ),
            spacing="4",
            width="100%",
        ),
        width="100%",
        padding="4",
    )


def analytics_filters() -> rx.Component:
    """Analytics dashboard filter controls."""
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.text("Date Range", size="2", weight="medium"),
                rx.select(
                    ["Last 7 days", "Last 30 days", "Last 90 days", "Last 12 months"],
                    placeholder="Select period",
                    value=AnalyticsState.date_range,
                    on_change=AnalyticsState.set_date_range,
                ),
                spacing="2",
            ),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    rx.icon("refresh_cw", size=16),
                    "Refresh",
                    variant="outline",
                    loading=AnalyticsState.loading_charts,
                    on_click=AnalyticsState.refresh_chart_data,
                ),
                rx.button(
                    rx.icon("download", size=16),
                    "Export All",
                    variant="outline",
                    on_click=AnalyticsState.export_data("all"),
                ),
                spacing="2",
            ),
            width="100%",
            align="center",
        ),
        width="100%",
        padding="4",
    )


def analytics_dashboard_static() -> rx.Component:
    """
    Comprehensive analytics dashboard with interactive charts,
    real-time data integration, and professional presentation.
    """
    return rx.vstack(
        # Dashboard Header
        rx.hstack(
            rx.heading("Analytics Dashboard", size="6"),
            rx.spacer(),
            rx.badge(
                rx.icon("activity", size=12),
                "Live Data",
                color_scheme="green",
            ),
            width="100%",
            align="center",
        ),

        # Filter Controls
        analytics_filters(),

        # KPI Metrics Row
        analytics_kpis(),

        # Charts Grid - First Row
        rx.grid(
            lead_conversion_funnel(),
            revenue_trends_chart(),
            columns="2",
            spacing="4",
            width="100%",
        ),

        # Charts Grid - Second Row
        rx.grid(
            lead_sources_chart(),
            team_performance_chart(),
            columns="2",
            spacing="4",
            width="100%",
        ),

        # Charts Grid - Third Row
        rx.grid(
            project_status_chart(),
            response_times_chart(),
            columns="2",
            spacing="4",
            width="100%",
        ),

        # Loading State Overlay
        rx.cond(
            AnalyticsState.loading_charts,
            rx.center(
                rx.vstack(
                    rx.spinner(size="3"),
                    rx.text("Loading analytics data...", size="3"),
                    spacing="3",
                ),
                position="fixed",
                top="50%",
                left="50%",
                transform="translate(-50%, -50%)",
                bg="white",
                border="1px solid var(--gray-6)",
                border_radius="8px",
                padding="6",
                z_index="1000",
            ),
        ),

        # Error Message
        rx.cond(
            AnalyticsState.chart_error != "",
            rx.callout.root(
                rx.callout.icon(rx.icon("triangle_alert")),
                rx.callout.text(AnalyticsState.chart_error),
                color_scheme="red",
                width="100%",
            ),
        ),

        spacing="6",
        width="100%",
        padding="4",
    )


def analytics_page() -> rx.Component:
    """Complete analytics page with navigation and controls."""
    return rx.container(
        rx.color_mode.button(position="top-right"),

        # Main Analytics Dashboard
        analytics_dashboard_static(),

        # Real-time update script (placeholder for WebSocket integration)
        rx.script(
            """
            // Real-time analytics updates
            function updateAnalytics() {
                // In production, this would connect to WebSocket
                console.log('Analytics updated:', new Date());
            }

            // Update every 30 seconds
            setInterval(updateAnalytics, 30000);
            """
        ),

        size="4",
        padding="4",
    )


# Aliases for backward compatibility
analytics_dashboard = analytics_page