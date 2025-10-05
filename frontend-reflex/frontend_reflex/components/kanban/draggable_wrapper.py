"""Custom HTML5 drag-and-drop wrapper component for Reflex."""

import reflex as rx
from typing import Any, Dict, Optional, Union


class DraggableWrapper(rx.Component):
    """Custom component that adds HTML5 drag-and-drop capabilities to any Reflex component."""

    library = None
    tag = "div"

    # Drag and drop props
    draggable: rx.Var[bool] = True
    drag_data: rx.Var[Dict[str, Any]] = {}
    on_drag_start: rx.EventHandler = None
    on_drag_end: rx.EventHandler = None

    # Styling props
    cursor: rx.Var[str] = "move"
    user_select: rx.Var[str] = "none"
    transition: rx.Var[str] = "all 0.2s ease"

    def get_event_triggers(self) -> Dict[str, Any]:
        """Define the event triggers for the component."""
        return {
            **super().get_event_triggers(),
            "on_drag_start": lambda e: [],
            "on_drag_end": lambda e: [],
        }

    def _get_custom_code(self) -> str:
        """Generate custom JavaScript for drag functionality."""
        return """
        const handleDragStart = (event) => {
            const element = event.currentTarget;
            const dragData = JSON.parse(element.dataset.dragData || '{}');

            // Set drag data
            event.dataTransfer.setData('text/plain', JSON.stringify(dragData));
            event.dataTransfer.effectAllowed = 'move';

            // Visual feedback
            element.style.opacity = '0.5';
            element.style.transform = 'scale(0.95)';

            // Custom event
            if (window.onLeadDragStart) {
                window.onLeadDragStart(dragData);
            }
        };

        const handleDragEnd = (event) => {
            const element = event.currentTarget;

            // Reset visual feedback
            element.style.opacity = '1';
            element.style.transform = 'scale(1)';

            // Custom event
            if (window.onLeadDragEnd) {
                window.onLeadDragEnd();
            }
        };

        // Attach event listeners
        this.addEventListener('dragstart', handleDragStart);
        this.addEventListener('dragend', handleDragEnd);
        """


class DropZoneWrapper(rx.Component):
    """Custom component that adds HTML5 drop zone capabilities to any Reflex component."""

    library = None
    tag = "div"

    # Drop zone props
    drop_target_status: rx.Var[str] = ""
    accept_drops: rx.Var[bool] = True
    on_drop: rx.EventHandler = None

    # Visual feedback props
    highlight_color: rx.Var[str] = "var(--accent-3)"
    border_color: rx.Var[str] = "var(--accent-8)"

    def get_event_triggers(self) -> Dict[str, Any]:
        """Define the event triggers for the component."""
        return {
            **super().get_event_triggers(),
            "on_drop": lambda e: [],
            "on_drag_over": lambda e: [],
            "on_drag_enter": lambda e: [],
            "on_drag_leave": lambda e: [],
        }

    def _get_custom_code(self) -> str:
        """Generate custom JavaScript for drop functionality."""
        return """
        const handleDragOver = (event) => {
            event.preventDefault();
            event.dataTransfer.dropEffect = 'move';
        };

        const handleDragEnter = (event) => {
            event.preventDefault();
            const element = event.currentTarget;
            const targetStatus = element.dataset.dropTargetStatus;

            if (targetStatus) {
                element.style.backgroundColor = element.dataset.highlightColor || 'var(--accent-3)';
                element.style.borderColor = element.dataset.borderColor || 'var(--accent-8)';
                element.style.borderWidth = '2px';
                element.style.borderStyle = 'dashed';
            }
        };

        const handleDragLeave = (event) => {
            const element = event.currentTarget;
            const relatedTarget = event.relatedTarget;

            // Only remove highlight if we're actually leaving the drop zone
            if (!element.contains(relatedTarget)) {
                element.style.backgroundColor = 'transparent';
                element.style.borderColor = 'initial';
                element.style.borderWidth = 'initial';
                element.style.borderStyle = 'initial';
            }
        };

        const handleDrop = (event) => {
            event.preventDefault();
            const element = event.currentTarget;
            const targetStatus = element.dataset.dropTargetStatus;

            // Reset visual feedback
            element.style.backgroundColor = 'transparent';
            element.style.borderColor = 'initial';
            element.style.borderWidth = 'initial';
            element.style.borderStyle = 'initial';

            try {
                const dragData = JSON.parse(event.dataTransfer.getData('text/plain'));

                if (dragData && targetStatus && dragData.status !== targetStatus) {
                    // Custom drop handler
                    if (window.onLeadDrop) {
                        window.onLeadDrop(dragData, targetStatus);
                    }

                    console.log(`Dropped lead ${dragData.id} to status ${targetStatus}`);
                }
            } catch (error) {
                console.error('Error handling drop:', error);
            }
        };

        // Attach event listeners
        this.addEventListener('dragover', handleDragOver);
        this.addEventListener('dragenter', handleDragEnter);
        this.addEventListener('dragleave', handleDragLeave);
        this.addEventListener('drop', handleDrop);
        """


# Factory functions for easy usage
def draggable_component(
    component: rx.Component,
    drag_data: Dict[str, Any],
    **props
) -> DraggableWrapper:
    """Wrap any component to make it draggable with HTML5 drag-and-drop."""
    return DraggableWrapper.create(
        component,
        drag_data=drag_data,
        data_drag_data=rx.Var.create(str(drag_data)),
        **props
    )


def drop_zone_component(
    component: rx.Component,
    target_status: str,
    **props
) -> DropZoneWrapper:
    """Wrap any component to make it a drop zone with HTML5 drag-and-drop."""
    return DropZoneWrapper.create(
        component,
        drop_target_status=target_status,
        data_drop_target_status=target_status,
        data_highlight_color=props.get("highlight_color", "var(--accent-3)"),
        data_border_color=props.get("border_color", "var(--accent-8)"),
        **props
    )