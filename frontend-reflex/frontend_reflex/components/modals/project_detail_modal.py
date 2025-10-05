"""Project detail modal component - Enhanced project details with tabbed interface."""

import reflex as rx
from ...components.projects_module import project_detail_modal

def project_detail_modal_enhanced() -> rx.Component:
    """Enhanced project detail modal with full functionality."""
    return project_detail_modal()

# Keep backward compatibility
def project_detail_modal() -> rx.Component:
    """Enhanced project detail modal with tabs and full project information."""
    return project_detail_modal_enhanced()