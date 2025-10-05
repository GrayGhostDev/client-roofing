"""Project pipeline component - Enhanced Kanban-style pipeline view."""

import reflex as rx
from ...components.projects_module import project_pipeline_view

def project_pipeline() -> rx.Component:
    """Enhanced project pipeline with full Kanban functionality."""
    return project_pipeline_view()