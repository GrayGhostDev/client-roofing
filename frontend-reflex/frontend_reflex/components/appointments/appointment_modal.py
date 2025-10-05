"""Comprehensive Appointment Modal component with complete scheduling form and validation."""

import reflex as rx
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from ..state import AppState, Appointment


def customer_selection_section() -> rx.Component:
    """Customer selection with search and new customer creation."""
    return rx.vstack(
        rx.text("Customer Information", size="3", weight="bold"),

        # Customer search/select
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text("Select Customer", size="2", weight="medium"),
                    rx.select(
                        AppState.get_customer_options,
                        placeholder="Search or select customer...",
                        value=AppState.appointment_form_customer_id,
                        on_change=AppState.set_appointment_form_customer_id,
                        width="300px"
                    ),
                    align="start",
                    spacing="2"
                ),
                rx.text("or", size="2", color="gray", padding="2"),
                rx.button(
                    rx.icon("plus", size=16),
                    "New Customer",
                    variant="outline",
                    on_click=AppState.open_new_customer_modal
                ),
                align="end",
                spacing="3"
            ),

            # Selected customer details
            rx.cond(
                AppState.selected_appointment_customer,
                rx.card(
                    rx.vstack(
                        rx.text("Selected Customer", size="2", weight="bold"),
                        rx.hstack(
                            rx.vstack(
                                rx.text("Name", size="1", color="gray"),
                                rx.text(
                                    AppState.selected_appointment_customer.first_name + " " + AppState.selected_appointment_customer.last_name,
                                    size="2",
                                    weight="medium"
                                ),
                                align="start",
                                spacing="1"
                            ),
                            rx.vstack(
                                rx.text("Phone", size="1", color="gray"),
                                rx.text(
                                    AppState.selected_appointment_customer.phone,
                                    size="2"
                                ),
                                align="start",
                                spacing="1"
                            ),
                            rx.vstack(
                                rx.text("Address", size="1", color="gray"),
                                rx.text(
                                    AppState.selected_appointment_customer.address,
                                    size="2"
                                ),
                                align="start",
                                spacing="1"
                            ),
                            spacing="4",
                            align="start"
                        ),
                        spacing="3",
                        width="100%"
                    ),
                    padding="3",
                    bg="green.1",
                    border="1px solid var(--green-6)"
                ),
                rx.fragment()
            ),

            spacing="3",
            width="100%"
        ),
        spacing="3",
        width="100%"
    )


def appointment_scheduling_section() -> rx.Component:
    """Appointment date, time, and duration selection."""
    return rx.vstack(
        rx.text("Scheduling", size="3", weight="bold"),

        rx.grid(
            # Date selection
            rx.vstack(
                rx.text("Date", size="2", weight="medium"),
                rx.input(
                    type="date",
                    value=AppState.appointment_form_date,
                    on_change=AppState.set_appointment_form_date,
                    min=datetime.now().strftime("%Y-%m-%d")
                ),
                rx.cond(
                    AppState.appointment_form_date_error,
                    rx.text(
                        AppState.appointment_form_date_error,
                        size="1",
                        color="red"
                    ),
                    rx.fragment()
                ),
                align="start",
                spacing="2"
            ),

            # Time selection
            rx.vstack(
                rx.text("Time", size="2", weight="medium"),
                rx.select(
                    AppState.get_available_time_slots,
                    placeholder="Select time...",
                    value=AppState.appointment_form_time,
                    on_change=AppState.set_appointment_form_time
                ),
                rx.cond(
                    AppState.appointment_form_time_error,
                    rx.text(
                        AppState.appointment_form_time_error,
                        size="1",
                        color="red"
                    ),
                    rx.fragment()
                ),
                align="start",
                spacing="2"
            ),

            # Duration selection
            rx.vstack(
                rx.text("Duration", size="2", weight="medium"),
                rx.select(
                    ["30", "60", "90", "120", "150", "180", "240"],
                    placeholder="Select duration...",
                    value=str(AppState.appointment_form_duration),
                    on_change=AppState.set_appointment_form_duration
                ),
                rx.text("minutes", size="1", color="gray"),
                align="start",
                spacing="2"
            ),

            columns="3",
            spacing="4",
            width="100%"
        ),

        # Availability check
        rx.cond(
            AppState.appointment_scheduling_conflict,
            rx.card(
                rx.hstack(
                    rx.icon("alert-triangle", size=16, color="red"),
                    rx.vstack(
                        rx.text("Scheduling Conflict", size="2", weight="bold", color="red"),
                        rx.text(
                            AppState.appointment_scheduling_conflict_message,
                            size="1"
                        ),
                        rx.text("Please choose a different time.", size="1"),
                        align="start",
                        spacing="1"
                    ),
                    spacing="2",
                    align="start"
                ),
                padding="3",
                bg="red.1",
                border="1px solid var(--red-6)"
            ),
            rx.cond(
                AppState.appointment_time_available,
                rx.card(
                    rx.hstack(
                        rx.icon("check", size=16, color="green"),
                        rx.text("Time slot available", size="2", color="green"),
                        spacing="2",
                        align="center"
                    ),
                    padding="3",
                    bg="green.1",
                    border="1px solid var(--green-6)"
                ),
                rx.fragment()
            )
        ),

        spacing="3",
        width="100%"
    )


def appointment_details_section() -> rx.Component:
    """Appointment type, team member, and other details."""
    return rx.vstack(
        rx.text("Appointment Details", size="3", weight="bold"),

        rx.grid(
            # Appointment type
            rx.vstack(
                rx.text("Type", size="2", weight="medium"),
                rx.select(
                    [
                        "consultation",
                        "inspection",
                        "estimate",
                        "project_work",
                        "follow_up"
                    ],
                    placeholder="Select type...",
                    value=AppState.appointment_form_type,
                    on_change=AppState.set_appointment_form_type
                ),
                align="start",
                spacing="2"
            ),

            # Team member assignment
            rx.vstack(
                rx.text("Assign to", size="2", weight="medium"),
                rx.select(
                    AppState.get_available_team_members,
                    placeholder="Select team member...",
                    value=AppState.appointment_form_assigned_to,
                    on_change=AppState.set_appointment_form_assigned_to
                ),
                rx.cond(
                    AppState.selected_team_member_availability,
                    rx.text(
                        AppState.selected_team_member_availability,
                        size="1",
                        color="green"
                    ),
                    rx.fragment()
                ),
                align="start",
                spacing="2"
            ),

            columns="2",
            spacing="4",
            width="100%"
        ),

        # Title/Subject
        rx.vstack(
            rx.text("Title", size="2", weight="medium"),
            rx.input(
                placeholder="Appointment title or subject...",
                value=AppState.appointment_form_title,
                on_change=AppState.set_appointment_form_title,
                width="100%"
            ),
            align="start",
            spacing="2",
            width="100%"
        ),

        # Description
        rx.vstack(
            rx.text("Description", size="2", weight="medium"),
            rx.text_area(
                placeholder="Additional notes or description...",
                value=AppState.appointment_form_description,
                on_change=AppState.set_appointment_form_description,
                width="100%",
                height="80px"
            ),
            align="start",
            spacing="2",
            width="100%"
        ),

        spacing="3",
        width="100%"
    )


def appointment_location_section() -> rx.Component:
    """Location and meeting settings."""
    return rx.vstack(
        rx.text("Location & Meeting", size="3", weight="bold"),

        # Virtual vs On-site
        rx.vstack(
            rx.text("Meeting Type", size="2", weight="medium"),
            rx.radio_group(
                rx.vstack(
                    rx.radio("On-site", value="onsite"),
                    rx.radio("Virtual", value="virtual"),
                    spacing="2"
                ),
                value=AppState.appointment_form_meeting_type,
                on_change=AppState.set_appointment_form_meeting_type
            ),
            align="start",
            spacing="2"
        ),

        # Location details
        rx.cond(
            AppState.appointment_form_meeting_type == "onsite",
            rx.vstack(
                rx.text("Location", size="2", weight="medium"),
                rx.input(
                    placeholder="Enter address or location...",
                    value=AppState.appointment_form_location,
                    on_change=AppState.set_appointment_form_location,
                    width="100%"
                ),
                rx.hstack(
                    rx.button(
                        rx.icon("map-pin", size=16),
                        "Use Customer Address",
                        variant="outline",
                        on_click=AppState.use_customer_address
                    ),
                    rx.button(
                        rx.icon("map", size=16),
                        "Validate Address",
                        variant="outline",
                        on_click=AppState.validate_appointment_address
                    ),
                    spacing="2"
                ),
                align="start",
                spacing="2",
                width="100%"
            ),
            rx.vstack(
                rx.text("Meeting URL", size="2", weight="medium"),
                rx.input(
                    placeholder="Enter meeting URL (Zoom, Teams, etc.)...",
                    value=AppState.appointment_form_meeting_url,
                    on_change=AppState.set_appointment_form_meeting_url,
                    width="100%"
                ),
                rx.button(
                    rx.icon("video", size=16),
                    "Generate Meeting URL",
                    variant="outline",
                    on_click=AppState.generate_meeting_url
                ),
                align="start",
                spacing="2",
                width="100%"
            )
        ),

        spacing="3",
        width="100%"
    )


def appointment_reminders_section() -> rx.Component:
    """Reminder and notification settings."""
    return rx.vstack(
        rx.text("Reminders & Notifications", size="3", weight="bold"),

        rx.grid(
            # Reminder settings
            rx.vstack(
                rx.text("Send Reminders", size="2", weight="medium"),
                rx.checkbox_group(
                    rx.vstack(
                        rx.checkbox("Email", value="email"),
                        rx.checkbox("SMS", value="sms"),
                        rx.checkbox("Phone Call", value="phone"),
                        spacing="2"
                    ),
                    value=AppState.appointment_form_reminder_methods,
                    on_change=AppState.set_appointment_form_reminder_methods
                ),
                align="start",
                spacing="2"
            ),

            # Reminder timing
            rx.vstack(
                rx.text("Reminder Schedule", size="2", weight="medium"),
                rx.select(
                    [
                        "1 hour before",
                        "2 hours before",
                        "4 hours before",
                        "1 day before",
                        "2 days before"
                    ],
                    placeholder="When to send...",
                    value=AppState.appointment_form_reminder_timing,
                    on_change=AppState.set_appointment_form_reminder_timing
                ),
                align="start",
                spacing="2"
            ),

            columns="2",
            spacing="4",
            width="100%"
        ),

        # Customer confirmation required
        rx.checkbox(
            "Require customer confirmation",
            checked=AppState.appointment_form_require_confirmation,
            on_change=AppState.set_appointment_form_require_confirmation
        ),

        spacing="3",
        width="100%"
    )


def appointment_preparation_section() -> rx.Component:
    """Preparation notes and checklist."""
    return rx.vstack(
        rx.text("Preparation", size="3", weight="bold"),

        rx.vstack(
            rx.text("Preparation Notes", size="2", weight="medium"),
            rx.text_area(
                placeholder="What needs to be prepared for this appointment?",
                value=AppState.appointment_form_preparation_notes,
                on_change=AppState.set_appointment_form_preparation_notes,
                width="100%",
                height="80px"
            ),
            align="start",
            spacing="2",
            width="100%"
        ),

        # Pre-appointment checklist
        rx.vstack(
            rx.text("Pre-appointment Checklist", size="2", weight="medium"),
            rx.checkbox_group(
                rx.vstack(
                    rx.checkbox("Review customer history", value="review_history"),
                    rx.checkbox("Prepare materials/tools", value="prepare_materials"),
                    rx.checkbox("Confirm directions", value="confirm_directions"),
                    rx.checkbox("Send reminder to customer", value="send_reminder"),
                    spacing="2"
                ),
                value=AppState.appointment_form_preparation_checklist,
                on_change=AppState.set_appointment_form_preparation_checklist
            ),
            align="start",
            spacing="2"
        ),

        spacing="3",
        width="100%"
    )


def appointment_modal_footer() -> rx.Component:
    """Modal footer with save/cancel actions."""
    return rx.hstack(
        # Validation status
        rx.cond(
            AppState.appointment_form_has_errors,
            rx.hstack(
                rx.icon("alert-circle", size=16, color="red"),
                rx.text(
                    "Please fix errors before saving",
                    size="2",
                    color="red"
                ),
                spacing="2",
                align="center"
            ),
            rx.cond(
                AppState.appointment_form_valid,
                rx.hstack(
                    rx.icon("check", size=16, color="green"),
                    rx.text(
                        "Ready to save",
                        size="2",
                        color="green"
                    ),
                    spacing="2",
                    align="center"
                ),
                rx.fragment()
            )
        ),

        rx.spacer(),

        # Action buttons
        rx.hstack(
            rx.button(
                "Cancel",
                variant="outline",
                on_click=AppState.cancel_appointment_form
            ),
            rx.button(
                "Save Draft",
                variant="outline",
                on_click=AppState.save_appointment_draft,
                disabled=AppState.appointment_form_has_errors
            ),
            rx.button(
                rx.cond(
                    AppState.appointment_form_editing,
                    "Update Appointment",
                    "Create Appointment"
                ),
                color_scheme="blue",
                loading=AppState.appointment_form_saving,
                on_click=AppState.save_appointment,
                disabled=AppState.appointment_form_has_errors
            ),
            spacing="2"
        ),

        justify="between",
        align="center",
        width="100%",
        padding="4"
    )


def appointment_modal() -> rx.Component:
    """Main appointment modal with comprehensive scheduling form."""
    return rx.dialog(
        rx.dialog_content(
            rx.vstack(
                # Modal header
                rx.hstack(
                    rx.heading(
                        rx.cond(
                            AppState.appointment_form_editing,
                            "Edit Appointment",
                            "New Appointment"
                        ),
                        size="5"
                    ),
                    rx.spacer(),
                    rx.dialog_close(
                        rx.button(
                            rx.icon("x", size=16),
                            variant="ghost"
                        )
                    ),
                    justify="between",
                    align="center",
                    width="100%"
                ),

                # Form content with tabs
                rx.tabs_root(
                    rx.tabs_list(
                        rx.tabs_trigger("Customer", value="customer"),
                        rx.tabs_trigger("Schedule", value="schedule"),
                        rx.tabs_trigger("Details", value="details"),
                        rx.tabs_trigger("Location", value="location"),
                        rx.tabs_trigger("Reminders", value="reminders"),
                        rx.tabs_trigger("Preparation", value="preparation"),
                    ),

                    # Customer tab
                    rx.tabs_content(
                        customer_selection_section(),
                        value="customer",
                        padding="4"
                    ),

                    # Schedule tab
                    rx.tabs_content(
                        appointment_scheduling_section(),
                        value="schedule",
                        padding="4"
                    ),

                    # Details tab
                    rx.tabs_content(
                        appointment_details_section(),
                        value="details",
                        padding="4"
                    ),

                    # Location tab
                    rx.tabs_content(
                        appointment_location_section(),
                        value="location",
                        padding="4"
                    ),

                    # Reminders tab
                    rx.tabs_content(
                        appointment_reminders_section(),
                        value="reminders",
                        padding="4"
                    ),

                    # Preparation tab
                    rx.tabs_content(
                        appointment_preparation_section(),
                        value="preparation",
                        padding="4"
                    ),

                    value=AppState.appointment_form_active_tab,
                    on_change=AppState.set_appointment_form_active_tab,
                    width="100%"
                ),

                spacing="4",
                width="100%",
                max_height="600px",
                overflow_y="auto"
            ),

            # Footer outside scrollable area
            appointment_modal_footer(),

            width="800px",
            max_width="90vw"
        ),

        open=AppState.appointment_modal_open,
        on_open_change=AppState.set_appointment_modal_open
    )