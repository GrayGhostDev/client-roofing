"""
Dashboard Service for iSwitch Roofs CRM
Version: 1.0.0

Comprehensive dashboard configuration and management service
for creating dynamic, role-based analytics dashboards.

Features:
- Role-based dashboard templates
- Dynamic widget configuration
- Real-time data binding
- Custom chart configurations
- Responsive layout management
- Dashboard sharing and permissions
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from app.config import get_redis_client, get_supabase_client
from app.models.analytics import (
    AnalyticsTimeframe,
    ChartConfiguration,
    ChartType,
    FilterConfiguration,
)
from app.services.enhanced_analytics_service import enhanced_analytics_service

logger = logging.getLogger(__name__)


class DashboardRole(str, Enum):
    """Dashboard role types"""

    EXECUTIVE = "executive"
    SALES_MANAGER = "sales_manager"
    SALES_REP = "sales_rep"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    TECHNICIAN = "technician"


class WidgetType(str, Enum):
    """Widget types for dashboard"""

    KPI_CARD = "kpi_card"
    CHART = "chart"
    TABLE = "table"
    FUNNEL = "funnel"
    GAUGE = "gauge"
    MAP = "map"
    CALENDAR = "calendar"
    ALERT_LIST = "alert_list"
    LEADERBOARD = "leaderboard"
    WEATHER = "weather"


@dataclass
class WidgetConfig:
    """Widget configuration data class"""

    widget_id: str
    widget_type: WidgetType
    title: str
    data_source: str
    chart_config: ChartConfiguration | None = None
    filters: list[FilterConfiguration] | None = None
    refresh_interval: int = 300  # seconds
    size: dict[str, int] = None  # {"width": 6, "height": 4}
    position: dict[str, int] = None  # {"x": 0, "y": 0}


class DashboardService:
    """
    Service for managing dashboard configurations and layouts
    """

    def __init__(self):
        """Initialize dashboard service"""
        self._supabase = None
        self._redis = None

        # Cache TTL for dashboard configurations
        self.cache_ttl = 3600  # 1 hour

        # Default widget configurations by role
        self.role_templates = self._initialize_role_templates()

        # Chart color schemes
        self.color_schemes = {
            "primary": ["#3B82F6", "#8B5CF6", "#EF4444", "#F59E0B", "#10B981"],
            "success": ["#059669", "#34D399", "#6EE7B7", "#A7F3D0", "#D1FAE5"],
            "warning": ["#D97706", "#F59E0B", "#FBBF24", "#FDE68A", "#FEF3C7"],
            "danger": ["#DC2626", "#EF4444", "#F87171", "#FCA5A5", "#FEE2E2"],
            "roofing": ["#8B4513", "#A0522D", "#CD853F", "#D2B48C", "#DEB887"],
        }

    @property
    def supabase(self):
        """Lazy load Supabase client"""
        if self._supabase is None:
            self._supabase = get_supabase_client()
        return self._supabase

    @property
    def redis_client(self):
        """Lazy load Redis client"""
        if self._redis is None:
            self._redis = get_redis_client()
        return self._redis

    def create_dashboard_for_role(
        self, role: DashboardRole, user_id: str, dashboard_name: str | None = None
    ) -> dict[str, Any]:
        """
        Create a dashboard configuration for a specific role

        Args:
            role: User role for dashboard template
            user_id: User ID creating the dashboard
            dashboard_name: Custom dashboard name

        Returns:
            Dashboard configuration dictionary
        """
        try:
            # Get role template
            template = self.role_templates.get(role, self.role_templates[DashboardRole.SALES_REP])

            # Create dashboard configuration
            dashboard_config = {
                "id": f"{role}_{user_id}_{int(datetime.utcnow().timestamp())}",
                "name": dashboard_name or template["name"],
                "description": template["description"],
                "role": role,
                "created_by": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "layout": template["layout"],
                "widgets": self._build_widgets_for_role(role),
                "default_timeframe": template["default_timeframe"],
                "auto_refresh_seconds": template.get("auto_refresh_seconds", 300),
                "is_public": False,
                "allowed_roles": [role],
            }

            # Save to database (would implement actual database save)
            self._save_dashboard_config(dashboard_config)

            return {
                "success": True,
                "dashboard": dashboard_config,
            }

        except Exception as e:
            logger.error(f"Error creating dashboard for role {role}: {str(e)}")
            return {"error": str(e)}

    def get_dashboard_data(
        self, dashboard_id: str, timeframe: AnalyticsTimeframe = AnalyticsTimeframe.MTD
    ) -> dict[str, Any]:
        """
        Get complete dashboard data with all widgets populated

        Args:
            dashboard_id: Dashboard identifier
            timeframe: Data timeframe

        Returns:
            Complete dashboard with data
        """
        try:
            # Get dashboard configuration
            dashboard_config = self._get_dashboard_config(dashboard_id)
            if not dashboard_config:
                return {"error": "Dashboard not found"}

            # Get data for each widget
            widget_data = {}
            widgets = dashboard_config.get("widgets", [])

            for widget in widgets:
                widget_id = widget["widget_id"]
                try:
                    data = self._get_widget_data(widget, timeframe)
                    widget_data[widget_id] = data
                except Exception as e:
                    logger.error(f"Error loading widget {widget_id}: {str(e)}")
                    widget_data[widget_id] = {"error": str(e)}

            # Combine dashboard config with data
            dashboard_response = {
                "dashboard_config": dashboard_config,
                "widget_data": widget_data,
                "timeframe": timeframe,
                "last_updated": datetime.utcnow().isoformat(),
                "next_update": (
                    datetime.utcnow()
                    + timedelta(seconds=dashboard_config.get("auto_refresh_seconds", 300))
                ).isoformat(),
            }

            return dashboard_response

        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            return {"error": str(e)}

    def _initialize_role_templates(self) -> dict[DashboardRole, dict]:
        """Initialize dashboard templates for different roles"""
        return {
            DashboardRole.EXECUTIVE: {
                "name": "Executive Dashboard",
                "description": "High-level business overview and KPIs",
                "default_timeframe": AnalyticsTimeframe.MTD,
                "auto_refresh_seconds": 300,
                "layout": {
                    "type": "grid",
                    "columns": 12,
                    "rows": 8,
                    "gap": 16,
                },
                "widget_types": [
                    "business_health_score",
                    "revenue_summary",
                    "lead_trends",
                    "conversion_funnel",
                    "team_performance_summary",
                    "alerts_summary",
                    "forecast_chart",
                    "geographic_performance",
                ],
            },
            DashboardRole.SALES_MANAGER: {
                "name": "Sales Manager Dashboard",
                "description": "Sales team performance and pipeline management",
                "default_timeframe": AnalyticsTimeframe.MTD,
                "auto_refresh_seconds": 180,
                "layout": {
                    "type": "grid",
                    "columns": 12,
                    "rows": 10,
                    "gap": 16,
                },
                "widget_types": [
                    "sales_kpis",
                    "team_leaderboard",
                    "conversion_funnel",
                    "pipeline_value",
                    "lead_source_performance",
                    "appointment_calendar",
                    "response_time_gauge",
                    "quota_tracking",
                ],
            },
            DashboardRole.SALES_REP: {
                "name": "Sales Representative Dashboard",
                "description": "Individual performance and daily activities",
                "default_timeframe": AnalyticsTimeframe.WEEKLY,
                "auto_refresh_seconds": 120,
                "layout": {
                    "type": "grid",
                    "columns": 12,
                    "rows": 8,
                    "gap": 16,
                },
                "widget_types": [
                    "personal_kpis",
                    "my_leads",
                    "my_appointments",
                    "my_pipeline",
                    "activity_tracker",
                    "goal_progress",
                    "recent_interactions",
                ],
            },
            DashboardRole.MARKETING: {
                "name": "Marketing Dashboard",
                "description": "Marketing performance and ROI analysis",
                "default_timeframe": AnalyticsTimeframe.MTD,
                "auto_refresh_seconds": 300,
                "layout": {
                    "type": "grid",
                    "columns": 12,
                    "rows": 8,
                    "gap": 16,
                },
                "widget_types": [
                    "marketing_roi",
                    "channel_performance",
                    "lead_source_analysis",
                    "cost_per_lead",
                    "campaign_effectiveness",
                    "attribution_analysis",
                    "lead_quality_trends",
                ],
            },
            DashboardRole.OPERATIONS: {
                "name": "Operations Dashboard",
                "description": "Project management and operational efficiency",
                "default_timeframe": AnalyticsTimeframe.WEEKLY,
                "auto_refresh_seconds": 240,
                "layout": {
                    "type": "grid",
                    "columns": 12,
                    "rows": 8,
                    "gap": 16,
                },
                "widget_types": [
                    "project_status",
                    "crew_schedule",
                    "material_costs",
                    "project_profitability",
                    "weather_alerts",
                    "equipment_utilization",
                    "safety_metrics",
                ],
            },
        }

    def _build_widgets_for_role(self, role: DashboardRole) -> list[dict]:
        """Build widget configurations for a specific role"""
        template = self.role_templates[role]
        widgets = []

        widget_builders = {
            "business_health_score": self._build_business_health_widget,
            "revenue_summary": self._build_revenue_summary_widget,
            "lead_trends": self._build_lead_trends_widget,
            "conversion_funnel": self._build_conversion_funnel_widget,
            "team_performance_summary": self._build_team_performance_widget,
            "alerts_summary": self._build_alerts_widget,
            "forecast_chart": self._build_forecast_widget,
            "sales_kpis": self._build_sales_kpis_widget,
            "team_leaderboard": self._build_team_leaderboard_widget,
            "pipeline_value": self._build_pipeline_widget,
            "lead_source_performance": self._build_lead_source_widget,
            "appointment_calendar": self._build_appointment_calendar_widget,
            "response_time_gauge": self._build_response_time_widget,
            "personal_kpis": self._build_personal_kpis_widget,
            "my_leads": self._build_my_leads_widget,
            "marketing_roi": self._build_marketing_roi_widget,
            "channel_performance": self._build_channel_performance_widget,
            "project_status": self._build_project_status_widget,
            "weather_alerts": self._build_weather_alerts_widget,
        }

        for widget_type in template["widget_types"]:
            if widget_type in widget_builders:
                widget = widget_builders[widget_type](role)
                if widget:
                    widgets.append(widget)

        return widgets

    def _build_business_health_widget(self, role: DashboardRole) -> dict:
        """Build business health score widget"""
        return {
            "widget_id": "business_health_score",
            "widget_type": WidgetType.GAUGE.value,
            "title": "Business Health Score",
            "data_source": "enhanced_analytics.roofing_kpis",
            "data_path": "period_summary.business_health_score",
            "chart_config": {
                "chart_type": ChartType.GAUGE.value,
                "min_value": 0,
                "max_value": 100,
                "thresholds": [
                    {"value": 30, "color": "#EF4444", "label": "Critical"},
                    {"value": 60, "color": "#F59E0B", "label": "Warning"},
                    {"value": 80, "color": "#10B981", "label": "Good"},
                    {"value": 100, "color": "#059669", "label": "Excellent"},
                ],
            },
            "size": {"width": 4, "height": 3},
            "position": {"x": 0, "y": 0},
            "refresh_interval": 300,
        }

    def _build_revenue_summary_widget(self, role: DashboardRole) -> dict:
        """Build revenue summary widget"""
        return {
            "widget_id": "revenue_summary",
            "widget_type": WidgetType.KPI_CARD.value,
            "title": "Revenue Summary",
            "data_source": "enhanced_analytics.roofing_kpis",
            "data_path": "revenue.revenue_summary",
            "chart_config": {
                "display_fields": [
                    {"field": "total_revenue", "label": "Total Revenue", "format": "currency"},
                    {"field": "pipeline_value", "label": "Pipeline Value", "format": "currency"},
                    {
                        "field": "completed_projects",
                        "label": "Completed Projects",
                        "format": "number",
                    },
                ],
                "color_scheme": "success",
            },
            "size": {"width": 4, "height": 3},
            "position": {"x": 4, "y": 0},
            "refresh_interval": 300,
        }

    def _build_lead_trends_widget(self, role: DashboardRole) -> dict:
        """Build lead trends chart widget"""
        return {
            "widget_id": "lead_trends",
            "widget_type": WidgetType.CHART.value,
            "title": "Lead Trends",
            "data_source": "analytics.trends",
            "query_params": {"metric": "leads", "interval": "daily", "period": 30},
            "chart_config": {
                "chart_type": ChartType.LINE.value,
                "x_axis": "date",
                "y_axis": "value",
                "color_scheme": "primary",
                "show_grid": True,
                "show_legend": True,
                "smooth_curve": True,
            },
            "size": {"width": 8, "height": 4},
            "position": {"x": 0, "y": 3},
            "refresh_interval": 300,
        }

    def _build_conversion_funnel_widget(self, role: DashboardRole) -> dict:
        """Build conversion funnel widget"""
        return {
            "widget_id": "conversion_funnel",
            "widget_type": WidgetType.FUNNEL.value,
            "title": "Conversion Funnel",
            "data_source": "enhanced_analytics.conversion_funnel",
            "chart_config": {
                "chart_type": ChartType.FUNNEL.value,
                "stages": [
                    {"name": "Leads", "field": "new"},
                    {"name": "Contacted", "field": "contacted"},
                    {"name": "Qualified", "field": "qualified"},
                    {"name": "Appointments", "field": "appointment_scheduled"},
                    {"name": "Inspections", "field": "inspection_completed"},
                    {"name": "Quotes", "field": "quote_sent"},
                    {"name": "Won", "field": "won"},
                ],
                "color_scheme": "primary",
                "show_percentages": True,
            },
            "size": {"width": 6, "height": 5},
            "position": {"x": 8, "y": 3},
            "refresh_interval": 300,
        }

    def _build_team_performance_widget(self, role: DashboardRole) -> dict:
        """Build team performance summary widget"""
        return {
            "widget_id": "team_performance",
            "widget_type": WidgetType.TABLE.value,
            "title": "Team Performance",
            "data_source": "enhanced_analytics.team_performance",
            "chart_config": {
                "columns": [
                    {"field": "name", "label": "Name", "sortable": True},
                    {"field": "conversion_rate", "label": "Conversion %", "format": "percentage"},
                    {"field": "revenue_generated", "label": "Revenue", "format": "currency"},
                    {"field": "performance_score", "label": "Score", "format": "number"},
                ],
                "sortable": True,
                "paginated": True,
                "max_rows": 10,
            },
            "size": {"width": 6, "height": 4},
            "position": {"x": 0, "y": 7},
            "refresh_interval": 300,
        }

    def _build_team_leaderboard_widget(self, role: DashboardRole) -> dict:
        """Build team leaderboard widget"""
        return {
            "widget_id": "team_leaderboard",
            "widget_type": WidgetType.LEADERBOARD.value,
            "title": "Team Leaderboard",
            "data_source": "enhanced_analytics.team_performance",
            "chart_config": {
                "rank_by": "performance_score",
                "display_fields": [
                    {"field": "name", "label": "Name"},
                    {"field": "performance_score", "label": "Score", "format": "number"},
                    {"field": "conversion_rate", "label": "Conversion %", "format": "percentage"},
                ],
                "max_entries": 10,
                "show_badges": True,
            },
            "size": {"width": 4, "height": 6},
            "position": {"x": 8, "y": 0},
            "refresh_interval": 180,
        }

    def _build_response_time_widget(self, role: DashboardRole) -> dict:
        """Build response time gauge widget"""
        return {
            "widget_id": "response_time_gauge",
            "widget_type": WidgetType.GAUGE.value,
            "title": "Avg Response Time",
            "data_source": "enhanced_analytics.roofing_kpis",
            "data_path": "leads.response_performance.avg_response_time_minutes",
            "chart_config": {
                "chart_type": ChartType.GAUGE.value,
                "min_value": 0,
                "max_value": 60,
                "unit": "minutes",
                "thresholds": [
                    {"value": 2, "color": "#059669", "label": "Excellent"},
                    {"value": 15, "color": "#10B981", "label": "Good"},
                    {"value": 30, "color": "#F59E0B", "label": "Warning"},
                    {"value": 60, "color": "#EF4444", "label": "Critical"},
                ],
            },
            "size": {"width": 3, "height": 3},
            "position": {"x": 0, "y": 6},
            "refresh_interval": 120,
        }

    def _build_marketing_roi_widget(self, role: DashboardRole) -> dict:
        """Build marketing ROI widget"""
        return {
            "widget_id": "marketing_roi",
            "widget_type": WidgetType.CHART.value,
            "title": "Marketing ROI by Channel",
            "data_source": "enhanced_analytics.marketing_roi",
            "chart_config": {
                "chart_type": ChartType.BAR.value,
                "x_axis": "channel",
                "y_axis": "roi_percentage",
                "color_scheme": "primary",
                "show_grid": True,
                "show_legend": False,
                "horizontal": True,
            },
            "size": {"width": 6, "height": 4},
            "position": {"x": 0, "y": 0},
            "refresh_interval": 300,
        }

    def _build_weather_alerts_widget(self, role: DashboardRole) -> dict:
        """Build weather alerts widget"""
        return {
            "widget_id": "weather_alerts",
            "widget_type": WidgetType.WEATHER.value,
            "title": "Weather & Storm Alerts",
            "data_source": "enhanced_analytics.weather_correlation",
            "chart_config": {
                "show_current_conditions": True,
                "show_storm_alerts": True,
                "show_impact_forecast": True,
                "zip_codes": ["48302", "48375", "48084"],  # Key service areas
            },
            "size": {"width": 4, "height": 3},
            "position": {"x": 8, "y": 0},
            "refresh_interval": 600,  # 10 minutes
        }

    def _build_personal_kpis_widget(self, role: DashboardRole) -> dict:
        """Build personal KPIs widget for sales reps"""
        return {
            "widget_id": "personal_kpis",
            "widget_type": WidgetType.KPI_CARD.value,
            "title": "My Performance",
            "data_source": "enhanced_analytics.team_performance",
            "filter_by_user": True,
            "chart_config": {
                "display_fields": [
                    {"field": "leads_assigned", "label": "Leads Assigned", "format": "number"},
                    {
                        "field": "conversion_rate",
                        "label": "Conversion Rate",
                        "format": "percentage",
                    },
                    {
                        "field": "revenue_generated",
                        "label": "Revenue Generated",
                        "format": "currency",
                    },
                    {
                        "field": "performance_score",
                        "label": "Performance Score",
                        "format": "number",
                    },
                ],
                "color_scheme": "primary",
                "show_targets": True,
            },
            "size": {"width": 6, "height": 3},
            "position": {"x": 0, "y": 0},
            "refresh_interval": 180,
        }

    def _build_my_leads_widget(self, role: DashboardRole) -> dict:
        """Build my leads widget for sales reps"""
        return {
            "widget_id": "my_leads",
            "widget_type": WidgetType.TABLE.value,
            "title": "My Active Leads",
            "data_source": "leads",
            "filter_by_user": True,
            "chart_config": {
                "columns": [
                    {"field": "name", "label": "Name", "sortable": True},
                    {"field": "status", "label": "Status", "format": "badge"},
                    {"field": "temperature", "label": "Temperature", "format": "badge"},
                    {"field": "created_at", "label": "Created", "format": "date"},
                    {"field": "next_follow_up", "label": "Next Follow-up", "format": "datetime"},
                ],
                "sortable": True,
                "filterable": True,
                "max_rows": 15,
                "actions": ["view", "edit", "call"],
            },
            "size": {"width": 12, "height": 5},
            "position": {"x": 0, "y": 3},
            "refresh_interval": 120,
        }

    def _build_alerts_widget(self, role: DashboardRole) -> dict:
        """Build alerts summary widget"""
        return {
            "widget_id": "alerts_summary",
            "widget_type": WidgetType.ALERT_LIST.value,
            "title": "Business Alerts",
            "data_source": "enhanced_analytics.business_alerts",
            "chart_config": {
                "max_alerts": 10,
                "show_by_level": True,
                "auto_dismiss": False,
                "groupable": True,
            },
            "size": {"width": 4, "height": 4},
            "position": {"x": 8, "y": 7},
            "refresh_interval": 60,
        }

    def _build_forecast_widget(self, role: DashboardRole) -> dict:
        """Build revenue forecast widget"""
        return {
            "widget_id": "forecast_chart",
            "widget_type": WidgetType.CHART.value,
            "title": "Revenue Forecast",
            "data_source": "enhanced_analytics.revenue_forecast",
            "query_params": {"months_ahead": 6},
            "chart_config": {
                "chart_type": ChartType.AREA.value,
                "x_axis": "date",
                "y_axis": "forecast",
                "show_confidence_bands": True,
                "color_scheme": "success",
                "show_grid": True,
                "show_legend": True,
            },
            "size": {"width": 8, "height": 4},
            "position": {"x": 0, "y": 11},
            "refresh_interval": 3600,  # 1 hour
        }

    def _build_pipeline_widget(self, role: DashboardRole) -> dict:
        """Build pipeline value widget"""
        return {
            "widget_id": "pipeline_value",
            "widget_type": WidgetType.KPI_CARD.value,
            "title": "Sales Pipeline",
            "data_source": "enhanced_analytics.roofing_kpis",
            "data_path": "revenue.revenue_summary.pipeline_value",
            "chart_config": {
                "display_fields": [
                    {"field": "pipeline_value", "label": "Total Pipeline", "format": "currency"},
                    {"field": "active_projects", "label": "Active Projects", "format": "number"},
                    {"field": "avg_deal_size", "label": "Avg Deal Size", "format": "currency"},
                ],
                "color_scheme": "warning",
            },
            "size": {"width": 4, "height": 3},
            "position": {"x": 4, "y": 3},
            "refresh_interval": 300,
        }

    def _build_lead_source_widget(self, role: DashboardRole) -> dict:
        """Build lead source performance widget"""
        return {
            "widget_id": "lead_source_performance",
            "widget_type": WidgetType.CHART.value,
            "title": "Lead Source Performance",
            "data_source": "enhanced_analytics.roofing_kpis",
            "data_path": "leads.source_performance",
            "chart_config": {
                "chart_type": ChartType.PIE.value,
                "value_field": "count",
                "label_field": "source",
                "color_scheme": "primary",
                "show_legend": True,
                "show_percentages": True,
            },
            "size": {"width": 4, "height": 4},
            "position": {"x": 8, "y": 6},
            "refresh_interval": 300,
        }

    def _build_appointment_calendar_widget(self, role: DashboardRole) -> dict:
        """Build appointment calendar widget"""
        return {
            "widget_id": "appointment_calendar",
            "widget_type": WidgetType.CALENDAR.value,
            "title": "Appointment Calendar",
            "data_source": "appointments",
            "chart_config": {
                "view_type": "week",
                "show_team_appointments": True,
                "show_personal_appointments": True,
                "color_by": "appointment_type",
                "interactive": True,
            },
            "size": {"width": 8, "height": 5},
            "position": {"x": 0, "y": 10},
            "refresh_interval": 300,
        }

    def _build_channel_performance_widget(self, role: DashboardRole) -> dict:
        """Build marketing channel performance widget"""
        return {
            "widget_id": "channel_performance",
            "widget_type": WidgetType.CHART.value,
            "title": "Channel Performance",
            "data_source": "enhanced_analytics.marketing_roi",
            "chart_config": {
                "chart_type": ChartType.BAR.value,
                "x_axis": "channel",
                "y_axis": "conversion_rate",
                "color_scheme": "primary",
                "show_grid": True,
                "show_data_labels": True,
            },
            "size": {"width": 6, "height": 4},
            "position": {"x": 6, "y": 0},
            "refresh_interval": 300,
        }

    def _build_project_status_widget(self, role: DashboardRole) -> dict:
        """Build project status widget"""
        return {
            "widget_id": "project_status",
            "widget_type": WidgetType.TABLE.value,
            "title": "Active Projects",
            "data_source": "projects",
            "chart_config": {
                "columns": [
                    {"field": "name", "label": "Project", "sortable": True},
                    {"field": "status", "label": "Status", "format": "badge"},
                    {"field": "progress", "label": "Progress", "format": "progress"},
                    {"field": "completion_date", "label": "Due Date", "format": "date"},
                ],
                "filters": [{"field": "status", "values": ["scheduled", "in_progress"]}],
                "sortable": True,
                "max_rows": 10,
            },
            "size": {"width": 8, "height": 5},
            "position": {"x": 0, "y": 0},
            "refresh_interval": 300,
        }

    def _get_widget_data(
        self, widget_config: dict, timeframe: AnalyticsTimeframe
    ) -> dict[str, Any]:
        """Get data for a specific widget"""
        try:
            data_source = widget_config.get("data_source")

            if data_source == "enhanced_analytics.roofing_kpis":
                kpis = enhanced_analytics_service.calculate_roofing_kpis(timeframe)
                data_path = widget_config.get("data_path")
                if data_path:
                    # Navigate to specific data path
                    data = kpis
                    for path_part in data_path.split("."):
                        data = data.get(path_part, {})
                    return data
                return kpis

            elif data_source == "enhanced_analytics.conversion_funnel":
                # Get funnel data (would implement actual funnel service call)
                return {"stages": {}, "conversion_rates": {}}

            elif data_source == "enhanced_analytics.revenue_forecast":
                months_ahead = widget_config.get("query_params", {}).get("months_ahead", 3)
                return enhanced_analytics_service.enhanced_revenue_forecast(months_ahead)

            elif data_source == "enhanced_analytics.team_performance":
                # Get team performance data (would implement actual service call)
                return []

            elif data_source == "enhanced_analytics.marketing_roi":
                # Get marketing ROI data (would implement actual service call)
                return {}

            elif data_source == "enhanced_analytics.business_alerts":
                kpis = enhanced_analytics_service.calculate_roofing_kpis(timeframe)
                return kpis.get("alerts", [])

            elif data_source == "analytics.trends":
                # Get trends data (would implement actual service call)
                return {"trend_data": []}

            else:
                # Handle other data sources (leads, appointments, projects, etc.)
                return {"message": f"Data source {data_source} not implemented"}

        except Exception as e:
            logger.error(f"Error getting widget data: {str(e)}")
            return {"error": str(e)}

    def _get_dashboard_config(self, dashboard_id: str) -> dict | None:
        """Get dashboard configuration from cache or database"""
        try:
            # Check cache first
            cache_key = f"dashboard_config:{dashboard_id}"
            if self.redis_client:
                cached_config = self.redis_client.get(cache_key)
                if cached_config:
                    return json.loads(cached_config)

            # Get from database (would implement actual database query)
            # For now, return a mock configuration
            return {
                "id": dashboard_id,
                "name": "Executive Dashboard",
                "widgets": [],
                "auto_refresh_seconds": 300,
            }

        except Exception as e:
            logger.error(f"Error getting dashboard config: {str(e)}")
            return None

    def _save_dashboard_config(self, dashboard_config: dict):
        """Save dashboard configuration to database and cache"""
        try:
            # Save to database (would implement actual database save)
            dashboard_id = dashboard_config["id"]

            # Cache the configuration
            if self.redis_client:
                cache_key = f"dashboard_config:{dashboard_id}"
                self.redis_client.setex(
                    cache_key, self.cache_ttl, json.dumps(dashboard_config, default=str)
                )

        except Exception as e:
            logger.error(f"Error saving dashboard config: {str(e)}")

    def get_available_widgets(self) -> dict[str, Any]:
        """Get list of available widget types and configurations"""
        return {
            "widget_types": [wt.value for wt in WidgetType],
            "chart_types": [ct.value for ct in ChartType],
            "color_schemes": list(self.color_schemes.keys()),
            "data_sources": [
                "enhanced_analytics.roofing_kpis",
                "enhanced_analytics.conversion_funnel",
                "enhanced_analytics.revenue_forecast",
                "enhanced_analytics.team_performance",
                "enhanced_analytics.marketing_roi",
                "leads",
                "customers",
                "projects",
                "appointments",
                "interactions",
            ],
        }

    def customize_widget(
        self, dashboard_id: str, widget_id: str, customizations: dict
    ) -> dict[str, Any]:
        """Customize a widget configuration"""
        try:
            dashboard_config = self._get_dashboard_config(dashboard_id)
            if not dashboard_config:
                return {"error": "Dashboard not found"}

            # Find and update widget
            widgets = dashboard_config.get("widgets", [])
            for widget in widgets:
                if widget.get("widget_id") == widget_id:
                    widget.update(customizations)
                    break
            else:
                return {"error": "Widget not found"}

            # Save updated configuration
            self._save_dashboard_config(dashboard_config)

            return {"success": True, "widget": widget}

        except Exception as e:
            logger.error(f"Error customizing widget: {str(e)}")
            return {"error": str(e)}


# Create singleton instance
dashboard_service = DashboardService()
