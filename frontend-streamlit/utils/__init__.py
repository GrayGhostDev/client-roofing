"""
Utility modules for iSwitch Roofs CRM Dashboard.

This package contains helper modules for API communication and data visualization.
"""

from .api_client import get_api_client, APIClient
from .visualization import (
    create_metric_card,
    create_kpi_cards,
    create_line_chart,
    create_bar_chart,
    create_pie_chart,
    create_funnel_chart,
    create_gauge_chart,
    create_heatmap,
    format_currency,
    format_percentage,
    export_to_csv,
    export_to_excel,
)

__all__ = [
    "get_api_client",
    "APIClient",
    "create_metric_card",
    "create_kpi_cards",
    "create_line_chart",
    "create_bar_chart",
    "create_pie_chart",
    "create_funnel_chart",
    "create_gauge_chart",
    "create_heatmap",
    "format_currency",
    "format_percentage",
    "export_to_csv",
    "export_to_excel",
]
