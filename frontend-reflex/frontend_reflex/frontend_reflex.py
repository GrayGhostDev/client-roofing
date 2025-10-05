"""iSwitch Roofs CRM Dashboard - Built with Reflex."""

import reflex as rx

from rxconfig import config
# Import the new state-driven dashboard
from .dashboard_state import DashboardState
from .components.dashboard_components import dashboard_layout

# Component imports for other pages
from .components.kanban import kanban_board_page
from .components.leads import leads_list_page
from .components.customers import customers_list_page
from .components.projects_module import projects_list_page, project_timeline_page
from .components.analytics import analytics_page
from .components.settings import settings_page
from .pages.appointments import appointments_page


def index() -> rx.Component:
    """Main dashboard page using official Reflex state management patterns."""
    return rx.container(
        rx.color_mode.button(position="top-right"),
        dashboard_layout(),
        size="4"
    )


def login_page() -> rx.Component:
    """Login page for authentication."""
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.center(
            rx.card(
                rx.vstack(
                    rx.heading("iSwitch Roofs CRM", size="6", text_align="center"),
                    rx.text("Please log in to continue", size="3", text_align="center", color="gray"),
                    rx.vstack(
                        rx.input(
                            placeholder="Username",
                            type="text",
                            width="100%"
                        ),
                        rx.input(
                            placeholder="Password",
                            type="password",
                            width="100%"
                        ),
                        rx.button(
                            "Sign In",
                            width="100%",
                            size="3"
                        ),
                        spacing="3",
                        width="100%"
                    ),
                    spacing="4",
                    width="100%"
                ),
                max_width="400px",
                size="4"
            ),
            height="100vh"
        )
    )


# Configure the app
app = rx.App()

# Add pages with proper state integration
app.add_page(index, route="/", title="iSwitch Roofs CRM - Dashboard")
app.add_page(kanban_board_page, route="/kanban", title="iSwitch Roofs CRM - Kanban Board")
app.add_page(leads_list_page, route="/leads", title="iSwitch Roofs CRM - Lead Management")
app.add_page(customers_list_page, route="/customers", title="iSwitch Roofs CRM - Customer Management")
app.add_page(projects_list_page, route="/projects", title="iSwitch Roofs CRM - Project Management")
app.add_page(project_timeline_page, route="/timeline", title="iSwitch Roofs CRM - Project Timeline")
app.add_page(appointments_page, route="/appointments", title="iSwitch Roofs CRM - Appointments")
app.add_page(analytics_page, route="/analytics", title="iSwitch Roofs CRM - Analytics Dashboard")
app.add_page(settings_page, route="/settings", title="iSwitch Roofs CRM - Settings")
# app.add_page(login_page, route="/login", title="iSwitch Roofs CRM - Login")  # Login page not implemented yet
