"""Lead detail modal component - Static components with JavaScript functionality."""

import reflex as rx


def lead_detail_modal() -> rx.Component:
    """Static lead detail modal structure."""
    return rx.fragment(
        # Modal content (initially hidden)
        rx.box(
            rx.box(
                rx.box(
                    rx.hstack(
                        rx.icon("user", size=20),
                        "Lead Details",
                        spacing="2",
                        align_items="center"
                    ),
                    margin_bottom="4"
                ),

                rx.text(
                    "Lead details will be loaded here",
                    size="3",
                    color="gray",
                    margin_bottom="4"
                ),

                # Close button
                rx.button(
                    "Close",
                    variant="outline",
                    size="2",
                    id="close-lead-detail"
                ),

                padding="6",
                bg="white",
                border_radius="12px",
                box_shadow="0 10px 25px rgba(0, 0, 0, 0.15)",
                max_width="600px",
                width="100%"
            ),
            position="fixed",
            top="50%",
            left="50%",
            transform="translate(-50%, -50%)",
            z_index="1000",
            id="lead-detail-modal",
            style={"display": "none"}
        ),

        # Backdrop
        rx.box(
            position="fixed",
            top="0",
            left="0",
            width="100vw",
            height="100vh",
            bg="rgba(0, 0, 0, 0.5)",
            z_index="999",
            id="lead-detail-backdrop",
            style={"display": "none"}
        )
    )