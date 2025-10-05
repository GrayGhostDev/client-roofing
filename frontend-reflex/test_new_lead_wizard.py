#!/usr/bin/env python3
"""
Test script for New Lead Wizard functionality.
Demonstrates the wizard component and validates integration.
"""

import reflex as rx
from frontend_reflex.components.modals.new_lead_wizard import new_lead_wizard, NewLeadWizardState

def test_wizard_page() -> rx.Component:
    """Test page demonstrating the New Lead Wizard."""
    return rx.container(
        rx.vstack(
            # Header
            rx.heading("New Lead Wizard Test Page", size="6", text_align="center"),
            rx.text(
                "Click the 'New Lead' button below to test the 5-step wizard with full validation and scoring.",
                size="3",
                text_align="center",
                color="gray.600"
            ),

            # Wizard component
            rx.center(
                new_lead_wizard(),
                width="100%",
                margin_y="8"
            ),

            # Features list
            rx.card(
                rx.vstack(
                    rx.heading("Wizard Features", size="4"),
                    rx.unordered_list(
                        rx.list_item("5-step multi-form wizard with progress indicator"),
                        rx.list_item("Complete form validation with error messages"),
                        rx.list_item("Duplicate detection (test with phone: (248) 555-1234)"),
                        rx.list_item("Lead scoring calculation (0-100 points)"),
                        rx.list_item("Temperature classification (Hot/Warm/Cool/Cold)"),
                        rx.list_item("Professional UI with loading states"),
                        rx.list_item("Mobile responsive design"),
                        rx.list_item("BANT qualification tracking"),
                        rx.list_item("Data validation and formatting")
                    ),
                    spacing="3",
                    align_items="start"
                ),
                size="2",
                max_width="600px"
            ),

            # Test cases
            rx.card(
                rx.vstack(
                    rx.heading("Test Cases", size="4"),
                    rx.text("Try these scenarios to test different features:", weight="medium"),

                    rx.accordion.root(
                        rx.accordion.item(
                            header=rx.text("High Score Lead (80+ points)", weight="bold", color="red"),
                            content=rx.vstack(
                                rx.text("Property Value: $600,000"),
                                rx.text("ZIP Code: 48009 (Bloomfield Hills)"),
                                rx.text("Source: website_form"),
                                rx.text("Urgency: immediate"),
                                rx.text("All BANT fields: yes"),
                                rx.text("Expected: HOT temperature, 85+ score", style={"font-style": "italic"}),
                                spacing="1",
                                align_items="start"
                            )
                        ),

                        rx.accordion.item(
                            header=rx.text("Medium Score Lead (60-79 points)", weight="bold", color="orange"),
                            content=rx.vstack(
                                rx.text("Property Value: $350,000"),
                                rx.text("ZIP Code: 48075 (Troy)"),
                                rx.text("Source: google_ads"),
                                rx.text("Urgency: 1_month"),
                                rx.text("Some BANT fields: yes"),
                                rx.text("Expected: WARM temperature, 60-70 score", style={"font-style": "italic"}),
                                spacing="1",
                                align_items="start"
                            )
                        ),

                        rx.accordion.item(
                            header=rx.text("Low Score Lead (0-39 points)", weight="bold", color="gray"),
                            content=rx.vstack(
                                rx.text("Property Value: $150,000"),
                                rx.text("ZIP Code: 48000 (other)"),
                                rx.text("Source: door_to_door"),
                                rx.text("Urgency: planning"),
                                rx.text("BANT fields: no/unknown"),
                                rx.text("Expected: COLD temperature, 20-30 score", style={"font-style": "italic"}),
                                spacing="1",
                                align_items="start"
                            )
                        ),

                        rx.accordion.item(
                            header=rx.text("Duplicate Detection Test", weight="bold", color="blue"),
                            content=rx.vstack(
                                rx.text("Phone: (248) 555-1234"),
                                rx.text("Email: existing@example.com"),
                                rx.text("Expected: Orange warning banner appears", style={"font-style": "italic"}),
                                spacing="1",
                                align_items="start"
                            )
                        ),

                        collapsible=True,
                        width="100%"
                    ),

                    spacing="3",
                    align_items="start"
                ),
                size="2",
                max_width="600px"
            ),

            # Status information
            rx.card(
                rx.vstack(
                    rx.heading("Implementation Status", size="4"),
                    rx.hstack(
                        rx.icon("check", color="green"),
                        rx.text("5-step wizard with progress indicator", color="green"),
                        spacing="2"
                    ),
                    rx.hstack(
                        rx.icon("check", color="green"),
                        rx.text("Complete form validation and error handling", color="green"),
                        spacing="2"
                    ),
                    rx.hstack(
                        rx.icon("check", color="green"),
                        rx.text("Lead scoring algorithm (0-100 points)", color="green"),
                        spacing="2"
                    ),
                    rx.hstack(
                        rx.icon("check", color="green"),
                        rx.text("Temperature classification (Hot/Warm/Cool/Cold)", color="green"),
                        spacing="2"
                    ),
                    rx.hstack(
                        rx.icon("check", color="green"),
                        rx.text("Duplicate detection warnings", color="green"),
                        spacing="2"
                    ),
                    rx.hstack(
                        rx.icon("check", color="green"),
                        rx.text("Professional UI with loading states", color="green"),
                        spacing="2"
                    ),
                    rx.hstack(
                        rx.icon("check", color="green"),
                        rx.text("Mobile responsive design", color="green"),
                        spacing="2"
                    ),
                    rx.hstack(
                        rx.icon("check", color="green"),
                        rx.text("Integrated with existing leads component", color="green"),
                        spacing="2"
                    ),
                    spacing="2",
                    align_items="start"
                ),
                size="2",
                max_width="600px"
            ),

            spacing="6",
            align_items="center"
        ),
        size="4"
    )


# Create the app
app = rx.App()

# Add the test page
app.add_page(test_wizard_page, route="/", title="New Lead Wizard Test")

if __name__ == "__main__":
    app.compile()