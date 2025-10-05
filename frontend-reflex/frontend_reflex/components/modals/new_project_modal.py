"""New project modal component - Enhanced project creation with form validation."""

import reflex as rx
from ...components.projects_module import new_project_modal

def new_project_modal_enhanced() -> rx.Component:
    """Enhanced new project modal with full functionality."""
    return new_project_modal()

# Keep backward compatibility
def new_project_modal() -> rx.Component:
    """Enhanced new project modal with form validation and creation."""
    return new_project_modal_enhanced()