"""Kanban board components for lead management."""

# Import kanban components from the kanban package
from .kanban import kanban_board, kanban_board_page

# Export the page function that the app needs
__all__ = [
    "kanban_board",
    "kanban_board_page"
]