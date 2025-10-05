"""System settings component - Complete system configuration interface."""

import reflex as rx
from .settings_state import settings_state


def business_information_section() -> rx.Component:
    """Business information configuration section."""
    return rx.vstack(
        rx.text("Business Information", size="4", weight="bold"),

        # Logo upload
        rx.vstack(
            rx.text("Company Logo", size="3", weight="medium"),
            rx.hstack(
                rx.cond(
                    settings_state.business_info.logo_url != "",
                    rx.image(
                        src=settings_state.business_info.logo_url,
                        width="80px",
                        height="80px",
                        object_fit="contain",
                        border="1px solid",
                        border_color="gray.3",
                        border_radius="6px"
                    ),
                    rx.box(
                        rx.icon("building", size=40, color="gray"),
                        width="80px",
                        height="80px",
                        border="2px dashed",
                        border_color="gray.3",
                        border_radius="6px",
                        display="flex",
                        align_items="center",
                        justify_content="center"
                    )
                ),
                rx.vstack(
                    rx.button(
                        rx.hstack(
                            rx.icon("upload", size=16),
                            rx.text("Upload Logo"),
                            spacing="2"
                        ),
                        variant="outline",
                        size="2"
                    ),
                    rx.button(
                        "Remove Logo",
                        variant="ghost",
                        color_scheme="red",
                        size="1"
                    ),
                    rx.text("PNG, JPG or SVG. Max size 5MB.", size="1", color="gray"),
                    spacing="2",
                    align="start"
                ),
                spacing="4",
                align="center"
            ),
            spacing="2",
            width="100%"
        ),

        # Company details
        rx.hstack(
            rx.vstack(
                rx.text("Company Name", size="2", weight="medium"),
                rx.input(
                    value=settings_state.business_info.company_name,
                    placeholder="Company name",
                    width="100%"
                ),
                spacing="1",
                width="100%"
            ),
            rx.vstack(
                rx.text("Website", size="2", weight="medium"),
                rx.input(
                    value=settings_state.business_info.website,
                    placeholder="https://company.com",
                    width="100%"
                ),
                spacing="1",
                width="100%"
            ),
            spacing="4",
            width="100%"
        ),

        # Address
        rx.vstack(
            rx.text("Business Address", size="2", weight="medium"),
            rx.text_area(
                value=settings_state.business_info.business_address,
                placeholder="Full business address",
                height="80px",
                width="100%"
            ),
            spacing="1",
            width="100%"
        ),

        # Contact information
        rx.hstack(
            rx.vstack(
                rx.text("Primary Phone", size="2", weight="medium"),
                rx.input(
                    value=settings_state.business_info.phone_primary,
                    placeholder="(248) 555-ROOF",
                    width="100%"
                ),
                spacing="1",
                width="100%"
            ),
            rx.vstack(
                rx.text("Secondary Phone", size="2", weight="medium"),
                rx.input(
                    value=settings_state.business_info.phone_secondary,
                    placeholder="(248) 555-0100",
                    width="100%"
                ),
                spacing="1",
                width="100%"
            ),
            spacing="4",
            width="100%"
        ),

        rx.hstack(
            rx.vstack(
                rx.text("Primary Email", size="2", weight="medium"),
                rx.input(
                    value=settings_state.business_info.email_primary,
                    placeholder="info@company.com",
                    width="100%"
                ),
                spacing="1",
                width="100%"
            ),
            rx.vstack(
                rx.text("Support Email", size="2", weight="medium"),
                rx.input(
                    value=settings_state.business_info.email_support,
                    placeholder="support@company.com",
                    width="100%"
                ),
                spacing="1",
                width="100%"
            ),
            spacing="4",
            width="100%"
        ),

        # Business identifiers
        rx.hstack(
            rx.vstack(
                rx.text("License Number", size="2", weight="medium"),
                rx.input(
                    value=settings_state.business_info.license_number,
                    placeholder="MI-2101234567",
                    width="100%"
                ),
                spacing="1",
                width="100%"
            ),
            rx.vstack(
                rx.text("Tax ID", size="2", weight="medium"),
                rx.input(
                    value=settings_state.business_info.tax_id,
                    placeholder="12-3456789",
                    width="100%"
                ),
                spacing="1",
                width="100%"
            ),
            rx.vstack(
                rx.text("Established Year", size="2", weight="medium"),
                rx.input(
                    value=str(settings_state.business_info.established_year),
                    placeholder="2018",
                    width="100%"
                ),
                spacing="1",
                width="100%"
            ),
            spacing="4",
            width="100%"
        ),

        spacing="4",
        width="100%"
    )


def operating_hours_section() -> rx.Component:
    """Operating hours configuration section."""
    return rx.vstack(
        rx.text("Business Hours", size="4", weight="bold"),
        rx.text("Set your standard operating hours for each day", size="2", color="gray"),

        rx.vstack(
            *[
                rx.hstack(
                    rx.hstack(
                        rx.switch(
                            checked=settings_state.operating_settings.business_hours[day]["enabled"],
                            size="2"
                        ),
                        rx.text(day.capitalize(), size="2", weight="medium", width="100px"),
                        spacing="2",
                        align="center"
                    ),
                    rx.cond(
                        settings_state.operating_settings.business_hours[day]["enabled"],
                        rx.hstack(
                            rx.input(
                                value=settings_state.operating_settings.business_hours[day]["start"],
                                placeholder="09:00",
                                width="80px",
                                type="time"
                            ),
                            rx.text("to", size="2", color="gray"),
                            rx.input(
                                value=settings_state.operating_settings.business_hours[day]["end"],
                                placeholder="17:00",
                                width="80px",
                                type="time"
                            ),
                            spacing="2",
                            align="center"
                        ),
                        rx.text("Closed", size="2", color="gray")
                    ),
                    spacing="4",
                    align="center",
                    width="100%",
                    padding="3",
                    border_radius="6px",
                    border="1px solid",
                    border_color="gray.3"
                )
                for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            ],
            spacing="2",
            width="100%"
        ),

        # Holidays management
        rx.vstack(
            rx.hstack(
                rx.text("Company Holidays", size="3", weight="medium"),
                rx.button(
                    rx.hstack(
                        rx.icon("plus", size=14),
                        rx.text("Add Holiday"),
                        spacing="2"
                    ),
                    size="1",
                    variant="outline"
                ),
                spacing="4",
                align="center"
            ),
            rx.vstack(
                *[
                    rx.hstack(
                        rx.text(holiday["name"], size="2", weight="medium"),
                        rx.spacer(),
                        rx.text(holiday["date"], size="2", color="gray"),
                        rx.button(
                            rx.icon("x", size=14),
                            size="1",
                            variant="ghost",
                            color_scheme="red"
                        ),
                        align="center",
                        width="100%",
                        padding="2",
                        border_radius="4px",
                        border="1px solid",
                        border_color="gray.2"
                    )
                    for holiday in settings_state.operating_settings.holidays
                ] if settings_state.operating_settings.holidays else [
                    rx.text("No holidays configured", size="2", color="gray", style={"font-style": "italic"})
                ],
                spacing="1",
                width="100%"
            ),
            spacing="2",
            width="100%"
        ),

        spacing="4",
        width="100%"
    )


def lead_management_section() -> rx.Component:
    """Lead management settings section."""
    return rx.vstack(
        rx.text("Lead Management", size="4", weight="bold"),

        # Response time target
        rx.hstack(
            rx.vstack(
                rx.text("Response Time Target", size="2", weight="medium"),
                rx.text("Maximum time to respond to new leads", size="1", color="gray"),
                spacing="1"
            ),
            rx.hstack(
                rx.input(
                    value=str(settings_state.operating_settings.lead_response_target_minutes),
                    width="80px",
                    type="number"
                ),
                rx.text("minutes", size="2", color="gray"),
                spacing="2",
                align="center"
            ),
            spacing="4",
            align="center",
            width="100%"
        ),

        # Auto-assignment settings
        rx.vstack(
            rx.hstack(
                rx.text("Auto-Assignment", size="3", weight="medium"),
                rx.switch(
                    checked=settings_state.operating_settings.auto_assignment_enabled,
                    size="2"
                ),
                spacing="2",
                align="center"
            ),
            rx.cond(
                settings_state.operating_settings.auto_assignment_enabled,
                rx.vstack(
                    rx.vstack(
                        rx.text("Assignment Method", size="2", weight="medium"),
                        rx.select.root(
                            rx.select.trigger(
                                rx.select.value(placeholder="Round Robin"),
                                width="200px"
                            ),
                            rx.select.content(
                                rx.select.item("Round Robin", value="round_robin"),
                                rx.select.item("Territory Based", value="territory"),
                                rx.select.item("Skill Based", value="skill_based")
                            )
                        ),
                        spacing="1"
                    ),
                    rx.hstack(
                        rx.checkbox(
                            checked=settings_state.operating_settings.auto_assignment_rules["consider_workload"],
                            spacing="2"
                        ),
                        rx.text("Consider current workload", size="2"),
                        spacing="2",
                        align="center"
                    ),
                    rx.hstack(
                        rx.checkbox(
                            checked=settings_state.operating_settings.auto_assignment_rules["consider_availability"],
                            spacing="2"
                        ),
                        rx.text("Consider availability hours", size="2"),
                        spacing="2",
                        align="center"
                    ),
                    spacing="3",
                    width="100%"
                ),
                rx.fragment()
            ),
            spacing="2",
            width="100%"
        ),

        spacing="4",
        width="100%"
    )


def service_areas_section() -> rx.Component:
    """Service areas configuration section."""
    return rx.vstack(
        rx.text("Service Areas", size="4", weight="bold"),
        rx.text("Manage ZIP codes and regions you serve", size="2", color="gray"),

        rx.vstack(
            rx.hstack(
                rx.input(
                    placeholder="Enter ZIP code (e.g., 48009)",
                    width="200px"
                ),
                rx.button(
                    rx.hstack(
                        rx.icon("plus", size=14),
                        rx.text("Add ZIP"),
                        spacing="2"
                    ),
                    size="2",
                    variant="outline"
                ),
                spacing="2",
                align="center"
            ),

            # Current service areas
            rx.vstack(
                rx.text(f"{len(settings_state.business_info.service_areas)} ZIP codes configured", size="2", weight="medium"),
                rx.box(
                    rx.hstack(
                        *[
                            rx.badge(
                                rx.hstack(
                                    rx.text(zip_code, size="1"),
                                    rx.button(
                                        rx.icon("x", size=10),
                                        size="1",
                                        variant="ghost",
                                        padding="1"
                                    ),
                                    spacing="1"
                                ),
                                variant="outline",
                                size="1"
                            )
                            for zip_code in settings_state.business_info.service_areas[:20]  # Show first 20
                        ],
                        spacing="1",
                        wrap="wrap"
                    ),
                    max_height="150px",
                    overflow="auto",
                    width="100%",
                    padding="3",
                    border="1px solid",
                    border_color="gray.3",
                    border_radius="6px"
                ),
                spacing="2",
                width="100%"
            ),
            spacing="3",
            width="100%"
        ),

        spacing="4",
        width="100%"
    )


def lead_scoring_section() -> rx.Component:
    """Lead scoring configuration section."""
    return rx.vstack(
        rx.text("Lead Scoring Configuration", size="4", weight="bold"),
        rx.text("Configure lead scoring thresholds and weights", size="2", color="gray"),

        # Score thresholds
        rx.vstack(
            rx.text("Score Thresholds", size="3", weight="medium"),
            rx.grid(
                rx.vstack(
                    rx.text("Hot (🔥)", size="2", weight="medium", color="red"),
                    rx.input(
                        value=str(settings_state.scoring_config.score_thresholds["hot"]),
                        width="80px",
                        type="number"
                    ),
                    rx.text("points+", size="1", color="gray"),
                    spacing="1",
                    align="center"
                ),
                rx.vstack(
                    rx.text("Warm (🌡️)", size="2", weight="medium", color="orange"),
                    rx.input(
                        value=str(settings_state.scoring_config.score_thresholds["warm"]),
                        width="80px",
                        type="number"
                    ),
                    rx.text("points+", size="1", color="gray"),
                    spacing="1",
                    align="center"
                ),
                rx.vstack(
                    rx.text("Cool (❄️)", size="2", weight="medium", color="blue"),
                    rx.input(
                        value=str(settings_state.scoring_config.score_thresholds["cool"]),
                        width="80px",
                        type="number"
                    ),
                    rx.text("points+", size="1", color="gray"),
                    spacing="1",
                    align="center"
                ),
                rx.vstack(
                    rx.text("Cold (🧊)", size="2", weight="medium", color="gray"),
                    rx.input(
                        value=str(settings_state.scoring_config.score_thresholds["cold"]),
                        width="80px",
                        type="number"
                    ),
                    rx.text("points+", size="1", color="gray"),
                    spacing="1",
                    align="center"
                ),
                columns="4",
                spacing="4",
                width="100%"
            ),
            spacing="2",
            width="100%"
        ),

        # Scoring weights
        rx.vstack(
            rx.text("Scoring Weights", size="3", weight="medium"),
            rx.text("Configure how different factors contribute to the lead score", size="2", color="gray"),
            rx.vstack(
                *[
                    rx.hstack(
                        rx.text(factor.replace("_", " ").title(), size="2", weight="medium", width="200px"),
                        rx.input(
                            value=str(int(weight * 100)),
                            width="80px",
                            type="number"
                        ),
                        rx.text("%", size="2", color="gray"),
                        rx.slider(
                            value=[weight * 100],
                            max=50,
                            step=1,
                            width="200px"
                        ),
                        spacing="3",
                        align="center",
                        width="100%"
                    )
                    for factor, weight in settings_state.scoring_config.scoring_weights.items()
                ],
                spacing="3",
                width="100%"
            ),
            spacing="2",
            width="100%"
        ),

        spacing="4",
        width="100%"
    )


def financial_settings_section() -> rx.Component:
    """Financial settings configuration section."""
    return rx.vstack(
        rx.text("Financial Settings", size="4", weight="bold"),

        # Currency and formatting
        rx.hstack(
            rx.vstack(
                rx.text("Currency", size="2", weight="medium"),
                rx.select.root(
                    rx.select.trigger(
                        rx.select.value(placeholder="USD ($)"),
                        width="150px"
                    ),
                    rx.select.content(
                        rx.select.item("USD ($)", value="USD"),
                        rx.select.item("CAD ($)", value="CAD"),
                        rx.select.item("EUR (€)", value="EUR")
                    )
                ),
                spacing="1",
                width="100%"
            ),
            rx.vstack(
                rx.text("Tax Rate", size="2", weight="medium"),
                rx.hstack(
                    rx.input(
                        placeholder="6.0",
                        width="80px",
                        type="number"
                    ),
                    rx.text("%", size="2", color="gray"),
                    spacing="2",
                    align="center"
                ),
                spacing="1",
                width="100%"
            ),
            spacing="4",
            width="100%"
        ),

        # Payment terms
        rx.vstack(
            rx.text("Payment Terms", size="3", weight="medium"),
            rx.hstack(
                rx.text("Net", size="2"),
                rx.input(
                    placeholder="30",
                    width="80px",
                    type="number"
                ),
                rx.text("days", size="2", color="gray"),
                spacing="2",
                align="center"
            ),
            spacing="2",
            width="100%"
        ),

        # Default commission structures
        rx.vstack(
            rx.text("Default Commission Structures", size="3", weight="medium"),
            rx.grid(
                rx.card(
                    rx.vstack(
                        rx.text("Sales Rep", size="2", weight="medium"),
                        rx.hstack(
                            rx.input(
                                placeholder="5.5",
                                width="80px",
                                type="number"
                            ),
                            rx.text("%", size="2", color="gray"),
                            spacing="2"
                        ),
                        spacing="2"
                    ),
                    padding="3"
                ),
                rx.card(
                    rx.vstack(
                        rx.text("Manager", size="2", weight="medium"),
                        rx.hstack(
                            rx.input(
                                placeholder="2.0",
                                width="80px",
                                type="number"
                            ),
                            rx.text("%", size="2", color="gray"),
                            spacing="2"
                        ),
                        spacing="2"
                    ),
                    padding="3"
                ),
                rx.card(
                    rx.vstack(
                        rx.text("Tech Bonus", size="2", weight="medium"),
                        rx.hstack(
                            rx.input(
                                placeholder="500",
                                width="80px",
                                type="number"
                            ),
                            rx.text("per project", size="1", color="gray"),
                            spacing="2"
                        ),
                        spacing="2"
                    ),
                    padding="3"
                ),
                columns="3",
                spacing="3",
                width="100%"
            ),
            spacing="2",
            width="100%"
        ),

        spacing="4",
        width="100%"
    )


def system_settings_section() -> rx.Component:
    """Complete system settings section."""
    return rx.vstack(
        # Two-column layout
        rx.hstack(
            # Left column
            rx.vstack(
                business_information_section(),
                rx.divider(),
                operating_hours_section(),
                rx.divider(),
                service_areas_section(),
                spacing="6",
                width="100%",
                flex="1"
            ),

            # Right column
            rx.vstack(
                lead_management_section(),
                rx.divider(),
                lead_scoring_section(),
                rx.divider(),
                financial_settings_section(),
                spacing="6",
                width="100%",
                flex="1"
            ),

            spacing="8",
            width="100%",
            align="start"
        ),

        spacing="6",
        width="100%"
    )


def system_settings_page() -> rx.Component:
    """System settings page wrapper."""
    return rx.container(
        rx.vstack(
            rx.heading("System Settings", size="6", weight="bold"),
            rx.text("Configure your business operations and system preferences", size="3", color="gray"),
            system_settings_section(),
            spacing="6",
            align="stretch"
        ),
        max_width="1400px",
        padding="4"
    )