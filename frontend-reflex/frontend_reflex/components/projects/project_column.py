"""Project column component - Enhanced Kanban columns with drag-drop functionality."""

import reflex as rx
from typing import List
from ...components.projects_module import project_column
from ...state import Project

def project_column_enhanced(status: str, title: str, projects: List[Project]) -> rx.Component:
    """Enhanced project column with full Kanban functionality."""
    return project_column(status, title, projects)


def project_column_skeleton() -> rx.Component:
    """Loading skeleton for project columns."""
    return rx.vstack(
        # Header skeleton
        rx.card(
            rx.vstack(
                rx.skeleton(height="1.5rem", width="60%"),
                rx.skeleton(height="1rem", width="40%"),
                spacing="1"
            ),
            size="2",
            width="100%"
        ),

        # Card skeletons
        rx.vstack(
            rx.card(
                rx.vstack(
                    rx.skeleton(height="1.5rem", width="80%"),
                    rx.skeleton(height="1rem", width="60%"),
                    rx.skeleton(height="0.5rem", width="100%"),
                    rx.skeleton(height="1rem", width="70%"),
                    spacing="2"
                ),
                size="2",
                width="100%"
            ),
            rx.card(
                rx.vstack(
                    rx.skeleton(height="1.5rem", width="75%"),
                    rx.skeleton(height="1rem", width="65%"),
                    rx.skeleton(height="0.5rem", width="90%"),
                    rx.skeleton(height="1rem", width="60%"),
                    spacing="2"
                ),
                size="2",
                width="100%"
            ),
            spacing="3",
            width="100%"
        ),

        spacing="3",
        align_items="stretch",
        width="300px",
        min_width="300px"
    )