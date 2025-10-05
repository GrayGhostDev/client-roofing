"""Project card component - Enhanced drag-and-drop cards with full project information."""

import reflex as rx
from ...components.projects_module import project_card
from ...state import Project

def draggable_project_card(project: Project) -> rx.Component:
    """Enhanced draggable project card for pipeline view."""
    return project_card(project)


def project_card_skeleton() -> rx.Component:
    """Loading skeleton for project cards."""
    return rx.card(
        rx.vstack(
            rx.skeleton(height="1.5rem", width="80%"),
            rx.skeleton(height="1rem", width="60%"),
            rx.skeleton(height="0.5rem", width="100%"),
            rx.skeleton(height="0.5rem", width="40%"),
            rx.skeleton(height="1rem", width="70%"),
            spacing="2"
        ),
        size="2",
        width="100%"
    )