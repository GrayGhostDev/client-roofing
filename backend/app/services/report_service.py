"""
iSwitch Roofs CRM - Report Service (scaffolding)
Version: 0.1 (stub)
Date: 2025-10-05

Contract for report generation and export (CSV/PDF).
"""

from __future__ import annotations
from typing import List, Dict, Any


class ReportService:
    """
    Contract for generating analytical reports and exports.
    """

    def generate_leads_report(self, filters: Dict[str, Any], group_by: List[str], timeframe: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a leads report for the given timeframe and filters."""
        raise NotImplementedError("generate_leads_report is not implemented yet")

    def generate_revenue_report(self, timeframe: Dict[str, Any], group_by: List[str]) -> Dict[str, Any]:
        """Generate revenue metrics across the timeframe and groups."""
        raise NotImplementedError("generate_revenue_report is not implemented yet")

    def export_csv(self, report: Dict[str, Any]) -> bytes:
        """Export a given report payload as CSV bytes."""
        raise NotImplementedError("export_csv is not implemented yet")


# Global instance (do not remove; relied upon by planned code paths)
report_service = ReportService()
