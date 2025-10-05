"""Integrations component - Complete integrations and API management interface."""

import reflex as rx
from .settings_state import settings_state


def api_management_section() -> rx.Component:
    """API keys and management section."""
    return rx.vstack(
        rx.text("API Management", size="4", weight="bold"),
        rx.text("Manage API keys and external service connections", size="2", color="gray"),

        # Generate new API key
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text("iSwitch Roofs API Key", size="3", weight="medium"),
                        rx.text("Use this key to access the iSwitch Roofs API", size="2", color="gray"),
                        spacing="1",
                        align="start"
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.hstack(
                            rx.icon("key", size=14),
                            rx.text("Generate New Key"),
                            spacing="2"
                        ),
                        variant="outline",
                        size="2"
                    ),
                    align="center",
                    width="100%"
                ),

                rx.hstack(
                    rx.input(
                        value="sk_live_xxxx...xxxx1234",
                        width="100%",
                        type="password",
                        read_only=True
                    ),
                    rx.button(
                        rx.icon("copy", size=14),
                        variant="ghost",
                        size="2"
                    ),
                    rx.button(
                        rx.icon("eye", size=14),
                        variant="ghost",
                        size="2"
                    ),
                    spacing="2",
                    width="100%"
                ),

                rx.text(
                    "⚠️ Keep your API key secure. Anyone with this key can access your account.",
                    size="1",
                    color="red"
                ),

                spacing="3"
            ),
            padding="4",
            width="100%"
        ),

        # Third-party API keys
        rx.vstack(
            rx.text("Third-Party API Keys", size="3", weight="medium"),
            rx.text("Store API keys for external services", size="2", color="gray"),

            rx.vstack(
                # Google Maps API
                rx.hstack(
                    rx.vstack(
                        rx.text("Google Maps API", size="2", weight="medium"),
                        rx.text("For address validation and mapping", size="1", color="gray"),
                        spacing="1",
                        align="start",
                        flex="1"
                    ),
                    rx.hstack(
                        rx.input(
                            placeholder="Enter Google Maps API key",
                            type="password",
                            width="300px"
                        ),
                        rx.button(
                            "Save",
                            size="2",
                            variant="outline"
                        ),
                        spacing="2"
                    ),
                    align="center",
                    width="100%",
                    padding="3",
                    border_radius="6px",
                    border="1px solid",
                    border_color="gray.3"
                ),

                # Weather API
                rx.hstack(
                    rx.vstack(
                        rx.text("Weather API", size="2", weight="medium"),
                        rx.text("For weather-based project scheduling", size="1", color="gray"),
                        spacing="1",
                        align="start",
                        flex="1"
                    ),
                    rx.hstack(
                        rx.input(
                            placeholder="Enter Weather API key",
                            type="password",
                            width="300px"
                        ),
                        rx.button(
                            "Save",
                            size="2",
                            variant="outline"
                        ),
                        spacing="2"
                    ),
                    align="center",
                    width="100%",
                    padding="3",
                    border_radius="6px",
                    border="1px solid",
                    border_color="gray.3"
                ),

                # Stripe API
                rx.hstack(
                    rx.vstack(
                        rx.text("Stripe API", size="2", weight="medium"),
                        rx.text("For payment processing", size="1", color="gray"),
                        spacing="1",
                        align="start",
                        flex="1"
                    ),
                    rx.hstack(
                        rx.input(
                            placeholder="Enter Stripe API key",
                            type="password",
                            width="300px"
                        ),
                        rx.button(
                            "Save",
                            size="2",
                            variant="outline"
                        ),
                        spacing="2"
                    ),
                    align="center",
                    width="100%",
                    padding="3",
                    border_radius="6px",
                    border="1px solid",
                    border_color="gray.3"
                ),

                spacing="2",
                width="100%"
            ),

            spacing="3",
            width="100%"
        ),

        spacing="6",
        width="100%"
    )


def third_party_connections_section() -> rx.Component:
    """Third-party service connections section."""
    return rx.vstack(
        rx.text("Third-Party Connections", size="4", weight="bold"),
        rx.text("Connect and manage external services", size="2", color="gray"),

        # CRM Integrations
        rx.vstack(
            rx.text("CRM Systems", size="3", weight="medium"),

            rx.grid(
                # Salesforce
                rx.card(
                    rx.vstack(
                        rx.hstack(
                            rx.image(
                                src="https://logo.clearbit.com/salesforce.com",
                                width="40px",
                                height="40px"
                            ),
                            rx.vstack(
                                rx.text("Salesforce", size="2", weight="bold"),
                                rx.badge("Not Connected", color_scheme="gray"),
                                spacing="1",
                                align="start"
                            ),
                            spacing="3",
                            align="center"
                        ),
                        rx.text(
                            "Sync leads and opportunities with Salesforce CRM",
                            size="1",
                            color="gray"
                        ),
                        rx.button(
                            "Connect",
                            color_scheme="blue",
                            size="2",
                            width="100%"
                        ),
                        spacing="3"
                    ),
                    padding="4"
                ),

                # HubSpot
                rx.card(
                    rx.vstack(
                        rx.hstack(
                            rx.image(
                                src="https://logo.clearbit.com/hubspot.com",
                                width="40px",
                                height="40px"
                            ),
                            rx.vstack(
                                rx.text("HubSpot", size="2", weight="bold"),
                                rx.badge("Connected", color_scheme="green"),
                                spacing="1",
                                align="start"
                            ),
                            spacing="3",
                            align="center"
                        ),
                        rx.text(
                            "Marketing automation and lead management",
                            size="1",
                            color="gray"
                        ),
                        rx.hstack(
                            rx.button(
                                "Settings",
                                variant="outline",
                                size="2",
                                flex="1"
                            ),
                            rx.button(
                                "Disconnect",
                                color_scheme="red",
                                variant="outline",
                                size="2",
                                flex="1"
                            ),
                            spacing="2",
                            width="100%"
                        ),
                        spacing="3"
                    ),
                    padding="4"
                ),

                columns="2",
                spacing="4",
                width="100%"
            ),

            spacing="3",
            width="100%"
        ),

        # Communication Tools
        rx.vstack(
            rx.text("Communication Tools", size="3", weight="medium"),

            rx.grid(
                # Twilio
                rx.card(
                    rx.vstack(
                        rx.hstack(
                            rx.image(
                                src="https://logo.clearbit.com/twilio.com",
                                width="40px",
                                height="40px"
                            ),
                            rx.vstack(
                                rx.text("Twilio", size="2", weight="bold"),
                                rx.badge("Connected", color_scheme="green"),
                                spacing="1",
                                align="start"
                            ),
                            spacing="3",
                            align="center"
                        ),
                        rx.text(
                            "SMS and voice communications",
                            size="1",
                            color="gray"
                        ),
                        rx.hstack(
                            rx.button(
                                "Settings",
                                variant="outline",
                                size="2",
                                flex="1"
                            ),
                            rx.button(
                                "Disconnect",
                                color_scheme="red",
                                variant="outline",
                                size="2",
                                flex="1"
                            ),
                            spacing="2",
                            width="100%"
                        ),
                        spacing="3"
                    ),
                    padding="4"
                ),

                # Mailchimp
                rx.card(
                    rx.vstack(
                        rx.hstack(
                            rx.image(
                                src="https://logo.clearbit.com/mailchimp.com",
                                width="40px",
                                height="40px"
                            ),
                            rx.vstack(
                                rx.text("Mailchimp", size="2", weight="bold"),
                                rx.badge("Not Connected", color_scheme="gray"),
                                spacing="1",
                                align="start"
                            ),
                            spacing="3",
                            align="center"
                        ),
                        rx.text(
                            "Email marketing and newsletters",
                            size="1",
                            color="gray"
                        ),
                        rx.button(
                            "Connect",
                            color_scheme="blue",
                            size="2",
                            width="100%"
                        ),
                        spacing="3"
                    ),
                    padding="4"
                ),

                columns="2",
                spacing="4",
                width="100%"
            ),

            spacing="3",
            width="100%"
        ),

        # Accounting Software
        rx.vstack(
            rx.text("Accounting Software", size="3", weight="medium"),

            rx.grid(
                # QuickBooks
                rx.card(
                    rx.vstack(
                        rx.hstack(
                            rx.image(
                                src="https://logo.clearbit.com/quickbooks.intuit.com",
                                width="40px",
                                height="40px"
                            ),
                            rx.vstack(
                                rx.text("QuickBooks", size="2", weight="bold"),
                                rx.badge("Connected", color_scheme="green"),
                                spacing="1",
                                align="start"
                            ),
                            spacing="3",
                            align="center"
                        ),
                        rx.text(
                            "Invoice and payment management",
                            size="1",
                            color="gray"
                        ),
                        rx.hstack(
                            rx.button(
                                "Settings",
                                variant="outline",
                                size="2",
                                flex="1"
                            ),
                            rx.button(
                                "Disconnect",
                                color_scheme="red",
                                variant="outline",
                                size="2",
                                flex="1"
                            ),
                            spacing="2",
                            width="100%"
                        ),
                        spacing="3"
                    ),
                    padding="4"
                ),

                # Xero
                rx.card(
                    rx.vstack(
                        rx.hstack(
                            rx.image(
                                src="https://logo.clearbit.com/xero.com",
                                width="40px",
                                height="40px"
                            ),
                            rx.vstack(
                                rx.text("Xero", size="2", weight="bold"),
                                rx.badge("Not Connected", color_scheme="gray"),
                                spacing="1",
                                align="start"
                            ),
                            spacing="3",
                            align="center"
                        ),
                        rx.text(
                            "Cloud-based accounting",
                            size="1",
                            color="gray"
                        ),
                        rx.button(
                            "Connect",
                            color_scheme="blue",
                            size="2",
                            width="100%"
                        ),
                        spacing="3"
                    ),
                    padding="4"
                ),

                columns="2",
                spacing="4",
                width="100%"
            ),

            spacing="3",
            width="100%"
        ),

        spacing="6",
        width="100%"
    )


def webhooks_section() -> rx.Component:
    """Webhooks configuration section."""
    return rx.vstack(
        rx.text("Webhooks", size="4", weight="bold"),
        rx.text("Configure webhooks to receive real-time notifications", size="2", color="gray"),

        # Add webhook button
        rx.button(
            rx.hstack(
                rx.icon("plus", size=16),
                rx.text("Add Webhook"),
                spacing="2"
            ),
            color_scheme="blue",
            size="2"
        ),

        # Webhook list
        rx.vstack(
            # Sample webhooks
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.text("Lead Created", size="2", weight="bold"),
                            rx.text("https://api.example.com/webhooks/leads", size="2", color="gray"),
                            rx.text("Triggers when a new lead is created", size="1", color="gray"),
                            spacing="1",
                            align="start"
                        ),
                        rx.spacer(),
                        rx.hstack(
                            rx.badge("Active", color_scheme="green"),
                            rx.button(
                                rx.icon("settings", size=14),
                                size="1",
                                variant="ghost"
                            ),
                            rx.button(
                                rx.icon("trash-2", size=14),
                                size="1",
                                variant="ghost",
                                color_scheme="red"
                            ),
                            spacing="2"
                        ),
                        align="center",
                        width="100%"
                    ),

                    rx.hstack(
                        rx.text("Events:", size="1", color="gray"),
                        rx.badge("lead.created", size="1", variant="outline"),
                        rx.badge("lead.updated", size="1", variant="outline"),
                        spacing="2",
                        align="center"
                    ),

                    rx.hstack(
                        rx.text("Last delivery:", size="1", color="gray"),
                        rx.text("2 minutes ago", size="1", weight="medium"),
                        rx.badge("200", color_scheme="green", size="1"),
                        spacing="2",
                        align="center"
                    ),

                    spacing="2",
                    align="start"
                ),
                padding="4"
            ),

            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.text("Project Status Update", size="2", weight="bold"),
                            rx.text("https://api.example.com/webhooks/projects", size="2", color="gray"),
                            rx.text("Triggers when project status changes", size="1", color="gray"),
                            spacing="1",
                            align="start"
                        ),
                        rx.spacer(),
                        rx.hstack(
                            rx.badge("Inactive", color_scheme="gray"),
                            rx.button(
                                rx.icon("settings", size=14),
                                size="1",
                                variant="ghost"
                            ),
                            rx.button(
                                rx.icon("trash-2", size=14),
                                size="1",
                                variant="ghost",
                                color_scheme="red"
                            ),
                            spacing="2"
                        ),
                        align="center",
                        width="100%"
                    ),

                    rx.hstack(
                        rx.text("Events:", size="1", color="gray"),
                        rx.badge("project.status_changed", size="1", variant="outline"),
                        rx.badge("project.completed", size="1", variant="outline"),
                        spacing="2",
                        align="center"
                    ),

                    rx.hstack(
                        rx.text("Last delivery:", size="1", color="gray"),
                        rx.text("1 day ago", size="1", weight="medium"),
                        rx.badge("404", color_scheme="red", size="1"),
                        spacing="2",
                        align="center"
                    ),

                    spacing="2",
                    align="start"
                ),
                padding="4"
            ),

            spacing="3",
            width="100%"
        ),

        # Webhook testing
        rx.vstack(
            rx.text("Webhook Testing", size="3", weight="medium"),
            rx.text("Test your webhooks with sample data", size="2", color="gray"),

            rx.hstack(
                rx.select.root(
                    rx.select.trigger(
                        rx.select.value(placeholder="Select webhook"),
                        width="200px"
                    ),
                    rx.select.content(
                        rx.select.item("Lead Created", value="lead_created"),
                        rx.select.item("Project Status Update", value="project_status")
                    )
                ),
                rx.button(
                    "Send Test",
                    variant="outline",
                    size="2"
                ),
                spacing="2",
                align="center"
            ),

            spacing="2",
            width="100%"
        ),

        spacing="6",
        width="100%"
    )


def import_export_section() -> rx.Component:
    """Data import/export settings section."""
    return rx.vstack(
        rx.text("Data Import/Export", size="4", weight="bold"),
        rx.text("Manage data imports, exports, and backups", size="2", color="gray"),

        # Auto backup settings
        rx.vstack(
            rx.text("Automatic Backups", size="3", weight="medium"),

            rx.hstack(
                rx.vstack(
                    rx.text("Enable automatic backups", size="2"),
                    rx.text("Create daily backups of your data", size="1", color="gray"),
                    spacing="1",
                    align="start",
                    flex="1"
                ),
                rx.spacer(),
                rx.switch(
                    checked=settings_state.integration_settings.import_export_settings["auto_backup_enabled"],
                    size="2"
                ),
                align="center",
                width="100%"
            ),

            rx.cond(
                settings_state.integration_settings.import_export_settings["auto_backup_enabled"],
                rx.vstack(
                    rx.hstack(
                        rx.text("Backup frequency:", size="2"),
                        rx.select.root(
                            rx.select.trigger(
                                rx.select.value(placeholder="Daily"),
                                width="150px"
                            ),
                            rx.select.content(
                                rx.select.item("Daily", value="daily"),
                                rx.select.item("Weekly", value="weekly"),
                                rx.select.item("Monthly", value="monthly")
                            )
                        ),
                        spacing="2",
                        align="center"
                    ),

                    rx.hstack(
                        rx.text("Retention period:", size="2"),
                        rx.input(
                            value="30",
                            type="number",
                            width="80px"
                        ),
                        rx.text("days", size="2", color="gray"),
                        spacing="2",
                        align="center"
                    ),

                    spacing="2",
                    width="100%"
                ),
                rx.fragment()
            ),

            spacing="3",
            width="100%"
        ),

        # Manual export
        rx.vstack(
            rx.text("Manual Export", size="3", weight="medium"),
            rx.text("Export your data in various formats", size="2", color="gray"),

            rx.grid(
                rx.card(
                    rx.vstack(
                        rx.text("Export Leads", size="2", weight="bold"),
                        rx.text("Export all lead data", size="1", color="gray"),
                        rx.hstack(
                            rx.select.root(
                                rx.select.trigger(
                                    rx.select.value(placeholder="CSV"),
                                    width="80px"
                                ),
                                rx.select.content(
                                    rx.select.item("CSV", value="csv"),
                                    rx.select.item("Excel", value="xlsx"),
                                    rx.select.item("JSON", value="json")
                                )
                            ),
                            rx.button(
                                "Export",
                                size="2",
                                flex="1"
                            ),
                            spacing="2",
                            width="100%"
                        ),
                        spacing="2"
                    ),
                    padding="3"
                ),

                rx.card(
                    rx.vstack(
                        rx.text("Export Customers", size="2", weight="bold"),
                        rx.text("Export customer data", size="1", color="gray"),
                        rx.hstack(
                            rx.select.root(
                                rx.select.trigger(
                                    rx.select.value(placeholder="CSV"),
                                    width="80px"
                                ),
                                rx.select.content(
                                    rx.select.item("CSV", value="csv"),
                                    rx.select.item("Excel", value="xlsx"),
                                    rx.select.item("JSON", value="json")
                                )
                            ),
                            rx.button(
                                "Export",
                                size="2",
                                flex="1"
                            ),
                            spacing="2",
                            width="100%"
                        ),
                        spacing="2"
                    ),
                    padding="3"
                ),

                rx.card(
                    rx.vstack(
                        rx.text("Export Projects", size="2", weight="bold"),
                        rx.text("Export project data", size="1", color="gray"),
                        rx.hstack(
                            rx.select.root(
                                rx.select.trigger(
                                    rx.select.value(placeholder="CSV"),
                                    width="80px"
                                ),
                                rx.select.content(
                                    rx.select.item("CSV", value="csv"),
                                    rx.select.item("Excel", value="xlsx"),
                                    rx.select.item("JSON", value="json")
                                )
                            ),
                            rx.button(
                                "Export",
                                size="2",
                                flex="1"
                            ),
                            spacing="2",
                            width="100%"
                        ),
                        spacing="2"
                    ),
                    padding="3"
                ),

                columns="3",
                spacing="3",
                width="100%"
            ),

            spacing="3",
            width="100%"
        ),

        # Data import
        rx.vstack(
            rx.text("Data Import", size="3", weight="medium"),
            rx.text("Import data from external sources", size="2", color="gray"),

            rx.card(
                rx.vstack(
                    rx.text("CSV/Excel Import", size="2", weight="bold"),
                    rx.text("Import leads or customers from spreadsheet files", size="1", color="gray"),

                    rx.hstack(
                        rx.input(
                            type="file",
                            accept=".csv,.xlsx",
                            width="100%"
                        ),
                        rx.button(
                            "Upload",
                            size="2"
                        ),
                        spacing="2",
                        width="100%"
                    ),

                    rx.text(
                        "Supported formats: CSV, Excel (.xlsx)",
                        size="1",
                        color="gray"
                    ),

                    spacing="2"
                ),
                padding="4",
                width="100%"
            ),

            spacing="3",
            width="100%"
        ),

        spacing="6",
        width="100%"
    )


def integrations_section() -> rx.Component:
    """Complete integrations section."""
    return rx.vstack(
        # Two-column layout
        rx.hstack(
            # Left column
            rx.vstack(
                api_management_section(),
                rx.divider(),
                webhooks_section(),
                spacing="6",
                width="100%",
                flex="1"
            ),

            # Right column
            rx.vstack(
                third_party_connections_section(),
                rx.divider(),
                import_export_section(),
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