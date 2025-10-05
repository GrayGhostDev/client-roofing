"""Kanban column component - Static components with JavaScript functionality."""

import reflex as rx

def kanban_column() -> rx.Component:
    """Static kanban column structure."""
    return rx.vstack(
        rx.text("Column", size="4", weight="bold"),
        rx.text("Column data will be loaded here", size="3", color="gray"),
        spacing="4",
        width="100%"
    )
