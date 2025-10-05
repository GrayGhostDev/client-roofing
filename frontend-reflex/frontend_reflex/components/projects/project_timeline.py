"""Project timeline component - Enhanced Gantt chart style timeline view."""

import reflex as rx
from ...components.projects_module import project_timeline_view

def project_timeline() -> rx.Component:
    """Enhanced project timeline with Gantt chart functionality."""
    return project_timeline_view()