"""Comprehensive Appointment Detail Modal with tabs, actions, and status tracking."""

import reflex as rx
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from ..state import AppState, Appointment


def appointment_overview_tab() -> rx.Component:
    """Overview tab showing all appointment information."""
    return rx.vstack(
        # Status and basic info
        rx.hstack(
            rx.vstack(
                rx.text("Status", size="2", color="gray"),
                rx.badge(
                    AppState.selected_appointment.status,
                    color_scheme=rx.cond(
                        AppState.selected_appointment.status == "confirmed",
                        "green",
                        rx.cond(
                            AppState.selected_appointment.status == "scheduled",
                            "blue",
                            rx.cond(
                                AppState.selected_appointment.status == "in_progress",
                                "orange",
                                rx.cond(
                                    AppState.selected_appointment.status == "completed",
                                    "purple",
                                    rx.cond(
                                        AppState.selected_appointment.status == "cancelled",
                                        "red",
                                        "gray"
                                    )
                                )
                            )
                        )
                    ),
                    size="2"
                ),
                align="start",
                spacing="1"
            ),
            rx.vstack(
                rx.text("Type", size="2", color="gray"),
                rx.badge(
                    AppState.selected_appointment.appointment_type,
                    color_scheme=rx.cond(
                        AppState.selected_appointment.appointment_type == "estimate",
                        "blue",
                        rx.cond(
                            AppState.selected_appointment.appointment_type == "installation",
                            "green",
                            rx.cond(
                                AppState.selected_appointment.appointment_type == "inspection",
                                "yellow",
                                "purple"
                            )
                        )
                    ),
                    size="2"
                ),
                align="start",
                spacing="1"
            ),
            rx.vstack(
                rx.text("Duration", size="2", color="gray"),
                rx.text(
                    f"{AppState.selected_appointment.duration_minutes} minutes",
                    size="2",
                    weight="medium"
                ),
                align="start",
                spacing="1"
            ),
            rx.vstack(
                rx.text("Assigned To", size="2", color="gray"),
                rx.text(
                    AppState.selected_appointment.assigned_to,
                    size="2",
                    weight="medium"
                ),
                align="start",
                spacing="1"
            ),
            spacing="6",
            align="start",
            width="100%"
        ),

        rx.separator(),

        # Date and time info
        rx.grid(
            rx.vstack(
                rx.text("Scheduled Date", size="2", color="gray"),
                rx.text(
                    AppState.selected_appointment.scheduled_date.split('T')[0] if 'T' in AppState.selected_appointment.scheduled_date else AppState.selected_appointment.scheduled_date,
                    size="3",
                    weight="bold"
                ),
                align="start",
                spacing="1"
            ),
            rx.vstack(
                rx.text("Time", size="2", color="gray"),
                rx.text(
                    AppState.selected_appointment.scheduled_date.split('T')[1][:5] if 'T' in AppState.selected_appointment.scheduled_date else "All Day",
                    size="3",
                    weight="bold"
                ),
                align="start",
                spacing="1"
            ),
            rx.vstack(
                rx.text("End Time", size="2", color="gray"),
                rx.text(
                    AppState.selected_appointment.end_time or "Calculated",
                    size="3",
                    weight="bold"
                ),
                align="start",
                spacing="1"
            ),
            columns="3",
            spacing="4",
            width="100%"
        ),

        rx.separator(),

        # Location and meeting info
        rx.vstack(
            rx.text("Location & Meeting", size="3", weight="bold"),
            rx.hstack(
                rx.cond(
                    AppState.selected_appointment.is_virtual,
                    rx.vstack(
                        rx.hstack(
                            rx.icon("video", size=16, color="blue"),
                            rx.text("Virtual Meeting", size="2", color="blue"),
                            spacing="2",
                            align="center"
                        ),
                        rx.cond(
                            AppState.selected_appointment.meeting_url,
                            rx.hstack(
                                rx.text("Meeting URL:", size="2", color="gray"),
                                rx.link(
                                    "Join Meeting",
                                    href=AppState.selected_appointment.meeting_url,
                                    target="_blank",
                                    color="blue"
                                ),
                                spacing="2"
                            ),
                            rx.text("No meeting URL provided", size="2", color="gray")
                        ),
                        align="start",
                        spacing="2"
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.icon("map-pin", size=16, color="green"),
                            rx.text("On-site Meeting", size="2", color="green"),
                            spacing="2",
                            align="center"
                        ),
                        rx.hstack(
                            rx.text("Location:", size="2", color="gray"),
                            rx.text(
                                AppState.selected_appointment.location or "No location specified",
                                size="2"
                            ),
                            spacing="2"
                        ),
                        rx.button(
                            rx.icon("navigation", size=16),
                            "Get Directions",
                            variant="outline",
                            on_click=lambda: AppState.get_directions(AppState.selected_appointment.location)
                        ),
                        align="start",
                        spacing="2"
                    )
                ),
                width="100%"
            ),
            align="start",
            spacing="3",
            width="100%"
        ),

        rx.separator(),

        # Description and notes
        rx.cond(
            AppState.selected_appointment.description,
            rx.vstack(
                rx.text("Description", size="2", color="gray"),
                rx.text(
                    AppState.selected_appointment.description,
                    size="2"
                ),
                align="start",
                spacing="2",
                width="100%"
            ),
            rx.fragment()
        ),

        rx.cond(
            AppState.selected_appointment.preparation_notes,
            rx.vstack(
                rx.text("Preparation Notes", size="2", color="gray"),
                rx.text(
                    AppState.selected_appointment.preparation_notes,
                    size="2"
                ),
                align="start",
                spacing="2",
                width="100%"
            ),
            rx.fragment()
        ),

        rx.cond(
            AppState.selected_appointment.outcome_notes,
            rx.vstack(
                rx.text("Outcome Notes", size="2", color="gray"),
                rx.text(
                    AppState.selected_appointment.outcome_notes,
                    size="2"
                ),
                align="start",
                spacing="2",
                width="100%"
            ),
            rx.fragment()
        ),

        spacing="4",
        width="100%"
    )


def appointment_customer_tab() -> rx.Component:
    """Customer information and details tab."""
    return rx.vstack(
        rx.cond(
            AppState.appointment_customer_details,
            rx.vstack(
                # Customer basic info
                rx.hstack(
                    rx.avatar(
                        fallback=AppState.appointment_customer_details.first_name[0] + AppState.appointment_customer_details.last_name[0],
                        size="5"
                    ),
                    rx.vstack(
                        rx.text(
                            AppState.appointment_customer_details.first_name + " " + AppState.appointment_customer_details.last_name,
                            size="4",
                            weight="bold"
                        ),
                        rx.text(
                            AppState.appointment_customer_details.customer_status,
                            size="2",
                            color="gray"
                        ),
                        align="start",
                        spacing="1"
                    ),
                    spacing="3",
                    align="center"
                ),

                rx.separator(),

                # Contact information
                rx.grid(
                    rx.vstack(
                        rx.text("Phone", size="2", color="gray"),
                        rx.hstack(
                            rx.text(
                                AppState.appointment_customer_details.phone,
                                size="2"
                            ),
                            rx.button(
                                rx.icon("phone", size=14),
                                size="2",
                                variant="outline",
                                on_click=lambda: AppState.call_customer(AppState.appointment_customer_details.phone)
                            ),
                            spacing="2",
                            align="center"
                        ),
                        align="start",
                        spacing="1"
                    ),
                    rx.vstack(
                        rx.text("Email", size="2", color="gray"),
                        rx.hstack(
                            rx.text(
                                AppState.appointment_customer_details.email or "No email",
                                size="2"
                            ),
                            rx.cond(
                                AppState.appointment_customer_details.email,
                                rx.button(
                                    rx.icon("mail", size=14),
                                    size="2",
                                    variant="outline",
                                    on_click=lambda: AppState.email_customer(AppState.appointment_customer_details.email)
                                ),
                                rx.fragment()
                            ),
                            spacing="2",
                            align="center"
                        ),
                        align="start",
                        spacing="1"
                    ),
                    columns="2",
                    spacing="4",
                    width="100%"
                ),

                # Address
                rx.vstack(
                    rx.text("Address", size="2", color="gray"),
                    rx.text(
                        AppState.appointment_customer_details.address,
                        size="2"
                    ),
                    align="start",
                    spacing="1",
                    width="100%"
                ),

                rx.separator(),

                # Customer stats
                rx.grid(
                    rx.vstack(
                        rx.text("Lifetime Value", size="2", color="gray"),
                        rx.text(
                            f"${AppState.appointment_customer_details.lifetime_value:,.2f}",
                            size="3",
                            weight="bold",
                            color="green"
                        ),
                        align="center",
                        spacing="1"
                    ),
                    rx.vstack(
                        rx.text("Total Projects", size="2", color="gray"),
                        rx.text(
                            str(AppState.appointment_customer_details.total_projects),
                            size="3",
                            weight="bold"
                        ),
                        align="center",
                        spacing="1"
                    ),
                    rx.vstack(
                        rx.text("Last Project", size="2", color="gray"),
                        rx.text(
                            AppState.appointment_customer_details.last_project_date or "None",
                            size="3",
                            weight="bold"
                        ),
                        align="center",
                        spacing="1"
                    ),
                    columns="3",
                    spacing="4",
                    width="100%"
                ),

                # Notes
                rx.cond(
                    AppState.appointment_customer_details.notes,
                    rx.vstack(
                        rx.text("Customer Notes", size="2", color="gray"),
                        rx.text(
                            AppState.appointment_customer_details.notes,
                            size="2"
                        ),
                        align="start",
                        spacing="2",
                        width="100%"
                    ),
                    rx.fragment()
                ),

                spacing="4",
                width="100%"
            ),
            rx.vstack(
                rx.text("Loading customer details...", size="2", color="gray"),
                align="center",
                spacing="2"
            )
        ),
        width="100%"
    )


def appointment_history_tab() -> rx.Component:
    """Appointment history and previous appointments."""
    return rx.vstack(
        rx.text("Appointment History", size="3", weight="bold"),

        rx.cond(
            AppState.customer_appointment_history,
            rx.vstack(
                rx.foreach(
                    AppState.customer_appointment_history,
                    lambda apt: rx.card(
                        rx.hstack(
                            rx.vstack(
                                rx.text(
                                    apt.scheduled_date.split('T')[0] if 'T' in apt.scheduled_date else apt.scheduled_date,
                                    size="2",
                                    weight="bold"
                                ),
                                rx.text(
                                    apt.scheduled_date.split('T')[1][:5] if 'T' in apt.scheduled_date else "All Day",
                                    size="1",
                                    color="gray"
                                ),
                                align="start",
                                spacing="1",
                                min_width="80px"
                            ),
                            rx.vstack(
                                rx.text(
                                    apt.title,
                                    size="2",
                                    weight="medium"
                                ),
                                rx.text(
                                    apt.appointment_type,
                                    size="1",
                                    color="gray"
                                ),
                                align="start",
                                spacing="1",
                                flex="1"
                            ),
                            rx.badge(
                                apt.status,
                                color_scheme=rx.cond(
                                    apt.status == "completed",
                                    "green",
                                    rx.cond(
                                        apt.status == "cancelled",
                                        "red",
                                        "blue"
                                    )
                                )
                            ),
                            justify="between",
                            align="center",
                            width="100%"
                        ),
                        padding="3",
                        margin="2"
                    )
                ),
                spacing="2",
                width="100%"
            ),
            rx.text("No previous appointments", size="2", color="gray", text_align="center")
        ),

        spacing="3",
        width="100%"
    )


def appointment_documents_tab() -> rx.Component:
    """Documents, estimates, and photos related to the appointment."""
    return rx.vstack(
        rx.hstack(
            rx.text("Documents & Files", size="3", weight="bold"),
            rx.spacer(),
            rx.button(
                rx.icon("upload", size=16),
                "Upload File",
                variant="outline",
                on_click=AppState.upload_appointment_file
            ),
            justify="between",
            align="center",
            width="100%"
        ),

        # Document categories
        rx.tabs_root(
            rx.tabs_list(
                rx.tabs_trigger("Estimates", value="estimates"),
                rx.tabs_trigger("Photos", value="photos"),
                rx.tabs_trigger("Contracts", value="contracts"),
                rx.tabs_trigger("Other", value="other")
            ),

            # Estimates tab
            rx.tabs_content(
                rx.cond(
                    AppState.appointment_estimates,
                    rx.vstack(
                        rx.foreach(
                            AppState.appointment_estimates,
                            lambda doc: rx.card(
                                rx.hstack(
                                    rx.icon("file-text", size=20, color="blue"),
                                    rx.vstack(
                                        rx.text(doc["name"], size="2", weight="medium"),
                                        rx.text(f"${doc['amount']:,.2f}", size="1", color="green"),
                                        rx.text(doc["date"], size="1", color="gray"),
                                        align="start",
                                        spacing="1"
                                    ),
                                    rx.spacer(),
                                    rx.hstack(
                                        rx.button(
                                            rx.icon("eye", size=14),
                                            size="2",
                                            variant="outline"
                                        ),
                                        rx.button(
                                            rx.icon("download", size=14),
                                            size="2",
                                            variant="outline"
                                        ),
                                        spacing="2"
                                    ),
                                    justify="between",
                                    align="center",
                                    width="100%"
                                ),
                                padding="3"
                            )
                        ),
                        spacing="2",
                        width="100%"
                    ),
                    rx.text("No estimates available", size="2", color="gray", text_align="center")
                ),
                value="estimates"
            ),

            # Photos tab
            rx.tabs_content(
                rx.cond(
                    AppState.appointment_photos,
                    rx.grid(
                        rx.foreach(
                            AppState.appointment_photos,
                            lambda photo: rx.card(
                                rx.vstack(
                                    rx.image(
                                        src=photo["thumbnail"],
                                        alt=photo["name"],
                                        width="100px",
                                        height="100px",
                                        object_fit="cover",
                                        border_radius="md"
                                    ),
                                    rx.text(photo["name"], size="1", text_align="center"),
                                    spacing="2",
                                    align="center"
                                ),
                                padding="3",
                                cursor="pointer",
                                on_click=lambda: AppState.view_photo(photo["id"])
                            )
                        ),
                        columns="4",
                        spacing="3",
                        width="100%"
                    ),
                    rx.text("No photos available", size="2", color="gray", text_align="center")
                ),
                value="photos"
            ),

            # Contracts tab
            rx.tabs_content(
                rx.text("Contracts section", size="2", color="gray", text_align="center"),
                value="contracts"
            ),

            # Other documents tab
            rx.tabs_content(
                rx.text("Other documents section", size="2", color="gray", text_align="center"),
                value="other"
            ),

            value="estimates",
            width="100%"
        ),

        spacing="4",
        width="100%"
    )


def appointment_communication_tab() -> rx.Component:
    """Communication history and notes."""
    return rx.vstack(
        rx.hstack(
            rx.text("Communication History", size="3", weight="bold"),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=16),
                "Add Note",
                variant="outline",
                on_click=AppState.add_appointment_note
            ),
            justify="between",
            align="center",
            width="100%"
        ),

        # Communication timeline
        rx.cond(
            AppState.appointment_communications,
            rx.vstack(
                rx.foreach(
                    AppState.appointment_communications,
                    lambda comm: rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.avatar(
                                    fallback=comm["author_initials"],
                                    size="2"
                                ),
                                rx.vstack(
                                    rx.hstack(
                                        rx.text(comm["author"], size="2", weight="medium"),
                                        rx.text(comm["timestamp"], size="1", color="gray"),
                                        spacing="2"
                                    ),
                                    rx.badge(comm["type"], size="1"),
                                    align="start",
                                    spacing="1"
                                ),
                                spacing="3",
                                align="start",
                                width="100%"
                            ),
                            rx.text(comm["content"], size="2"),
                            spacing="2",
                            width="100%"
                        ),
                        padding="3",
                        margin="2"
                    )
                ),
                spacing="2",
                width="100%"
            ),
            rx.text("No communication history", size="2", color="gray", text_align="center")
        ),

        # Quick communication actions
        rx.card(
            rx.vstack(
                rx.text("Quick Actions", size="2", weight="bold"),
                rx.hstack(
                    rx.button(
                        rx.icon("phone", size=16),
                        "Call Customer",
                        variant="outline",
                        on_click=AppState.call_appointment_customer
                    ),
                    rx.button(
                        rx.icon("mail", size=16),
                        "Send Email",
                        variant="outline",
                        on_click=AppState.email_appointment_customer
                    ),
                    rx.button(
                        rx.icon("message-square", size=16),
                        "Send SMS",
                        variant="outline",
                        on_click=AppState.sms_appointment_customer
                    ),
                    spacing="2",
                    wrap="wrap"
                ),
                spacing="3",
                width="100%"
            ),
            padding="3"
        ),

        spacing="4",
        width="100%"
    )


def appointment_detail_actions() -> rx.Component:
    """Action buttons for the appointment."""
    return rx.hstack(
        # Status actions
        rx.cond(
            AppState.selected_appointment.status == "scheduled",
            rx.hstack(
                rx.button(
                    rx.icon("check", size=16),
                    "Confirm",
                    color_scheme="green",
                    on_click=lambda: AppState.confirm_appointment(AppState.selected_appointment.id)
                ),
                rx.button(
                    rx.icon("calendar", size=16),
                    "Reschedule",
                    variant="outline",
                    on_click=lambda: AppState.reschedule_appointment(AppState.selected_appointment.id)
                ),
                spacing="2"
            ),
            rx.cond(
                AppState.selected_appointment.status == "confirmed",
                rx.hstack(
                    rx.button(
                        rx.icon("play", size=16),
                        "Start",
                        color_scheme="blue",
                        on_click=lambda: AppState.start_appointment(AppState.selected_appointment.id)
                    ),
                    rx.button(
                        rx.icon("calendar", size=16),
                        "Reschedule",
                        variant="outline",
                        on_click=lambda: AppState.reschedule_appointment(AppState.selected_appointment.id)
                    ),
                    spacing="2"
                ),
                rx.cond(
                    AppState.selected_appointment.status == "in_progress",
                    rx.hstack(
                        rx.button(
                            rx.icon("check-circle", size=16),
                            "Mark Complete",
                            color_scheme="green",
                            on_click=lambda: AppState.complete_appointment(AppState.selected_appointment.id)
                        ),
                        spacing="2"
                    ),
                    rx.fragment()
                )
            )
        ),

        rx.spacer(),

        # General actions
        rx.hstack(
            rx.button(
                rx.icon("edit", size=16),
                "Edit",
                variant="outline",
                on_click=lambda: AppState.edit_appointment(AppState.selected_appointment.id)
            ),
            rx.button(
                rx.icon("bell", size=16),
                "Send Reminder",
                variant="outline",
                on_click=lambda: AppState.send_appointment_reminder(AppState.selected_appointment.id)
            ),
            rx.button(
                rx.icon("navigation", size=16),
                "Directions",
                variant="outline",
                on_click=lambda: AppState.get_directions(AppState.selected_appointment.location)
            ),
            rx.button(
                rx.icon("x", size=16),
                "Cancel",
                variant="outline",
                color="red",
                on_click=lambda: AppState.cancel_appointment_with_reason(AppState.selected_appointment.id)
            ),
            spacing="2"
        ),

        justify="between",
        align="center",
        width="100%",
        padding="4"
    )


def appointment_detail_modal() -> rx.Component:
    """Main appointment detail modal with comprehensive information and actions."""
    return rx.dialog(
        rx.dialog_content(
            rx.cond(
                AppState.selected_appointment,
                rx.vstack(
                    # Header
                    rx.hstack(
                        rx.vstack(
                            rx.heading(
                                AppState.selected_appointment.title,
                                size="5"
                            ),
                            rx.text(
                                f"ID: {AppState.selected_appointment.id}",
                                size="1",
                                color="gray"
                            ),
                            align="start",
                            spacing="1"
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

                    # Status timeline
                    rx.card(
                        rx.hstack(
                            rx.vstack(
                                rx.text("Created", size="1", color="gray"),
                                rx.text(
                                    AppState.selected_appointment.created_at.split('T')[0] if 'T' in AppState.selected_appointment.created_at else AppState.selected_appointment.created_at,
                                    size="2",
                                    weight="medium"
                                ),
                                align="center",
                                spacing="1"
                            ),
                            rx.icon("arrow-right", size=16, color="gray"),
                            rx.cond(
                                AppState.selected_appointment.confirmed_by_customer,
                                rx.vstack(
                                    rx.text("Confirmed", size="1", color="gray"),
                                    rx.text("Yes", size="2", weight="medium", color="green"),
                                    align="center",
                                    spacing="1"
                                ),
                                rx.vstack(
                                    rx.text("Confirmed", size="1", color="gray"),
                                    rx.text("Pending", size="2", weight="medium", color="yellow"),
                                    align="center",
                                    spacing="1"
                                )
                            ),
                            rx.icon("arrow-right", size=16, color="gray"),
                            rx.vstack(
                                rx.text("Status", size="1", color="gray"),
                                rx.badge(AppState.selected_appointment.status),
                                align="center",
                                spacing="1"
                            ),
                            justify="center",
                            align="center",
                            spacing="3",
                            width="100%"
                        ),
                        padding="3",
                        bg="blue.1"
                    ),

                    # Tabs with detailed information
                    rx.tabs_root(
                        rx.tabs_list(
                            rx.tabs_trigger("Overview", value="overview"),
                            rx.tabs_trigger("Customer", value="customer"),
                            rx.tabs_trigger("History", value="history"),
                            rx.tabs_trigger("Documents", value="documents"),
                            rx.tabs_trigger("Communication", value="communication")
                        ),

                        # Tab contents
                        rx.tabs_content(
                            appointment_overview_tab(),
                            value="overview",
                            padding="4"
                        ),
                        rx.tabs_content(
                            appointment_customer_tab(),
                            value="customer",
                            padding="4"
                        ),
                        rx.tabs_content(
                            appointment_history_tab(),
                            value="history",
                            padding="4"
                        ),
                        rx.tabs_content(
                            appointment_documents_tab(),
                            value="documents",
                            padding="4"
                        ),
                        rx.tabs_content(
                            appointment_communication_tab(),
                            value="communication",
                            padding="4"
                        ),

                        value=AppState.appointment_detail_active_tab,
                        on_change=AppState.set_appointment_detail_active_tab,
                        width="100%"
                    ),

                    spacing="4",
                    width="100%",
                    max_height="600px",
                    overflow_y="auto"
                ),

                # Loading state
                rx.vstack(
                    rx.spinner(size="3"),
                    rx.text("Loading appointment details...", size="2", color="gray"),
                    align="center",
                    spacing="3"
                )
            ),

            # Actions footer
            appointment_detail_actions(),

            width="900px",
            max_width="95vw"
        ),

        open=AppState.appointment_detail_modal_open,
        on_open_change=AppState.set_appointment_detail_modal_open
    )