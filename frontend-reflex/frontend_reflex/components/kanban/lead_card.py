"""Kanban lead card component - Static components with JavaScript functionality."""

import reflex as rx

def lead_card() -> rx.Component:
    """Static lead card structure."""
    return rx.card(
        rx.text("Lead Card", size="3", weight="bold"),
        rx.text("Lead details will be loaded here", size="2", color="gray"),
        size="2"
    )
