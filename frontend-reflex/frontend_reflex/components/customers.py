"""Customer management components for CRM dashboard - Full Reflex implementation."""

import reflex as rx
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import asyncio
import httpx


class Customer(rx.Base):
    """Customer data model for frontend."""
    id: str
    first_name: str
    last_name: str
    phone: str
    email: Optional[str] = None
    address: str
    property_type: str = "residential"
    created_at: str
    lifetime_value: float = 0.0
    total_projects: int = 0
    last_project_date: Optional[str] = None
    customer_status: str = "active"  # active, inactive, churned
    notes: Optional[str] = None
    converted_from_lead_id: Optional[str] = None


class Project(rx.Base):
    """Project data model for customer project history."""
    id: str
    customer_id: str
    name: str
    description: str
    status: str
    value: float
    start_date: str
    end_date: Optional[str] = None
    created_at: str


class CustomerFormData(rx.Base):
    """Form data model for customer add/edit operations."""
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    property_type: str = "residential"
    notes: str = ""


class CustomerState(rx.State):
    """
    Customer management state following proper Reflex patterns.
    Manages all customer data, operations, and UI state.
    """

    # Core state
    loading: bool = False
    error_message: str = ""
    success_message: str = ""
    last_refresh: str = ""

    # Customer data
    customers: List[Customer] = []
    filtered_customers: List[Customer] = []
    selected_customer: Optional[Customer] = None
    customer_projects: List[Project] = []

    # Filter and search state
    status_filter: str = "all"
    search_query: str = ""
    current_page: int = 1
    items_per_page: int = 20

    # UI state
    show_add_modal: bool = False
    show_edit_modal: bool = False
    show_detail_modal: bool = False
    show_confirm_delete: bool = False

    # Form state
    form_data: CustomerFormData = CustomerFormData()
    form_errors: Dict[str, str] = {}

    # Backend configuration
    backend_url: str = "http://localhost:8001"

    def load_customers(self):
        """Load customers data from backend API."""
        self.loading = True
        self.error_message = ""

        try:
            # For now, use mock data - replace with actual API call
            mock_customers = [
                Customer(
                    id="1",
                    first_name="John",
                    last_name="Doe",
                    phone="(555) 123-4567",
                    email="john.doe@email.com",
                    address="123 Main St, Birmingham, MI 48009",
                    property_type="residential",
                    customer_status="active",
                    lifetime_value=45000.0,
                    total_projects=3,
                    last_project_date="2024-01-15",
                    created_at="2023-06-15",
                    notes="Premium client, prefers morning appointments"
                ),
                Customer(
                    id="2",
                    first_name="Jane",
                    last_name="Smith",
                    phone="(555) 987-6543",
                    email="jane.smith@email.com",
                    address="456 Oak Ave, Bloomfield Hills, MI 48304",
                    property_type="residential",
                    customer_status="active",
                    lifetime_value=32000.0,
                    total_projects=2,
                    last_project_date="2024-01-10",
                    created_at="2023-09-20",
                    notes="Insurance claim specialist contact"
                ),
                Customer(
                    id="3",
                    first_name="Bob",
                    last_name="Johnson",
                    phone="(555) 456-7890",
                    email="bob.johnson@email.com",
                    address="789 Pine Rd, Troy, MI 48084",
                    property_type="commercial",
                    customer_status="inactive",
                    lifetime_value=12000.0,
                    total_projects=1,
                    last_project_date="2023-08-15",
                    created_at="2023-05-10",
                    notes="Seasonal maintenance customer"
                ),
                Customer(
                    id="4",
                    first_name="Alice",
                    last_name="Williams",
                    phone="(555) 321-9876",
                    email="alice.williams@email.com",
                    address="321 Cedar St, West Bloomfield, MI 48322",
                    property_type="residential",
                    customer_status="active",
                    lifetime_value=67000.0,
                    total_projects=4,
                    last_project_date="2024-02-20",
                    created_at="2022-11-05",
                    notes="High-value customer, multiple properties"
                ),
                Customer(
                    id="5",
                    first_name="Mike",
                    last_name="Davis",
                    phone="(555) 654-3210",
                    email="mike.davis@email.com",
                    address="654 Maple Dr, Rochester Hills, MI 48309",
                    property_type="residential",
                    customer_status="churned",
                    lifetime_value=8500.0,
                    total_projects=1,
                    last_project_date="2022-12-03",
                    created_at="2022-10-15",
                    notes="Service issues resolved, potential re-engagement"
                )
            ]

            self.customers = mock_customers
            self.apply_filters()
            self.last_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        except Exception as e:
            self.error_message = f"Failed to load customers: {str(e)}"
        finally:
            self.loading = False

    def apply_filters(self):
        """Apply current filters to customer list."""
        filtered = self.customers

        # Apply status filter
        if self.status_filter != "all":
            filtered = [c for c in filtered if c.customer_status == self.status_filter]

        # Apply search filter
        if self.search_query:
            query = self.search_query.lower()
            filtered = [
                c for c in filtered
                if (query in c.first_name.lower() or
                    query in c.last_name.lower() or
                    query in c.phone or
                    (c.email and query in c.email.lower()) or
                    query in c.address.lower())
            ]

        self.filtered_customers = filtered

    def set_status_filter(self, status: str):
        """Set status filter and refresh results."""
        self.status_filter = status
        self.current_page = 1
        self.apply_filters()

    def set_search_query(self, query: str):
        """Set search query and refresh results."""
        self.search_query = query
        self.current_page = 1
        self.apply_filters()

    def open_add_modal(self):
        """Open add customer modal."""
        self.form_data = CustomerFormData()
        self.form_errors = {}
        self.show_add_modal = True

    def close_add_modal(self):
        """Close add customer modal."""
        self.show_add_modal = False
        self.form_errors = {}

    def open_edit_modal(self, customer_id: str):
        """Open edit customer modal."""
        customer = next((c for c in self.customers if c.id == customer_id), None)
        if customer:
            self.form_data = CustomerFormData(
                first_name=customer.first_name,
                last_name=customer.last_name,
                phone=customer.phone,
                email=customer.email or "",
                address=customer.address,
                property_type=customer.property_type,
                notes=customer.notes or ""
            )
            self.selected_customer = customer
            self.form_errors = {}
            self.show_edit_modal = True

    def close_edit_modal(self):
        """Close edit customer modal."""
        self.show_edit_modal = False
        self.selected_customer = None
        self.form_errors = {}

    def open_detail_modal(self, customer_id: str):
        """Open customer detail modal."""
        customer = next((c for c in self.customers if c.id == customer_id), None)
        if customer:
            self.selected_customer = customer
            self.load_customer_projects(customer_id)
            self.show_detail_modal = True

    def close_detail_modal(self):
        """Close customer detail modal."""
        self.show_detail_modal = False
        self.selected_customer = None
        self.customer_projects = []

    def load_customer_projects(self, customer_id: str):
        """Load projects for a specific customer."""
        # Mock project data - replace with actual API call
        mock_projects = [
            Project(
                id="p1",
                customer_id=customer_id,
                name="Residential Roof Replacement",
                description="Complete roof replacement with premium shingles",
                status="completed",
                value=25000.0,
                start_date="2024-01-01",
                end_date="2024-01-15",
                created_at="2023-12-15"
            ),
            Project(
                id="p2",
                customer_id=customer_id,
                name="Gutter Installation",
                description="Custom gutter system installation",
                status="completed",
                value=8500.0,
                start_date="2023-11-01",
                end_date="2023-11-05",
                created_at="2023-10-20"
            )
        ]
        self.customer_projects = [p for p in mock_projects if p.customer_id == customer_id]

    def validate_form(self) -> bool:
        """Validate customer form data."""
        errors = {}

        if not self.form_data.first_name.strip():
            errors["first_name"] = "First name is required"

        if not self.form_data.last_name.strip():
            errors["last_name"] = "Last name is required"

        if not self.form_data.phone.strip():
            errors["phone"] = "Phone number is required"
        elif len(self.form_data.phone.strip()) < 10:
            errors["phone"] = "Please enter a valid phone number"

        if not self.form_data.address.strip():
            errors["address"] = "Address is required"

        self.form_errors = errors
        return len(errors) == 0

    def save_customer(self):
        """Save new customer."""
        if not self.validate_form():
            return

        try:
            # Create new customer - replace with actual API call
            new_customer = Customer(
                id=f"customer_{len(self.customers) + 1}",
                first_name=self.form_data.first_name.strip(),
                last_name=self.form_data.last_name.strip(),
                phone=self.form_data.phone.strip(),
                email=self.form_data.email.strip() if self.form_data.email.strip() else None,
                address=self.form_data.address.strip(),
                property_type=self.form_data.property_type,
                customer_status="active",
                created_at=datetime.now().strftime("%Y-%m-%d"),
                notes=self.form_data.notes.strip() if self.form_data.notes.strip() else None
            )

            self.customers.append(new_customer)
            self.apply_filters()
            self.close_add_modal()
            self.success_message = "Customer added successfully"

        except Exception as e:
            self.error_message = f"Failed to save customer: {str(e)}"

    def update_customer(self):
        """Update existing customer."""
        if not self.validate_form() or not self.selected_customer:
            return

        try:
            # Update customer - replace with actual API call
            for i, customer in enumerate(self.customers):
                if customer.id == self.selected_customer.id:
                    updated_customer = Customer(
                        **{**customer.dict(),
                           "first_name": self.form_data.first_name.strip(),
                           "last_name": self.form_data.last_name.strip(),
                           "phone": self.form_data.phone.strip(),
                           "email": self.form_data.email.strip() if self.form_data.email.strip() else None,
                           "address": self.form_data.address.strip(),
                           "property_type": self.form_data.property_type,
                           "notes": self.form_data.notes.strip() if self.form_data.notes.strip() else None}
                    )
                    self.customers[i] = updated_customer
                    break

            self.apply_filters()
            self.close_edit_modal()
            self.success_message = "Customer updated successfully"

        except Exception as e:
            self.error_message = f"Failed to update customer: {str(e)}"

    def delete_customer(self, customer_id: str):
        """Delete customer after confirmation."""
        try:
            # Delete customer - replace with actual API call
            self.customers = [c for c in self.customers if c.id != customer_id]
            self.apply_filters()
            self.success_message = "Customer deleted successfully"

        except Exception as e:
            self.error_message = f"Failed to delete customer: {str(e)}"

    def call_customer(self, phone: str):
        """Initiate phone call to customer."""
        # This would integrate with a phone system
        self.success_message = f"Initiating call to {phone}"

    def email_customer(self, email: str):
        """Open email client for customer."""
        if email:
            self.success_message = f"Opening email to {email}"

    def clear_messages(self):
        """Clear success and error messages."""
        self.success_message = ""
        self.error_message = ""

    # Form field setters
    def set_first_name(self, value: str):
        """Set first name in form data."""
        self.form_data.first_name = value

    def set_last_name(self, value: str):
        """Set last name in form data."""
        self.form_data.last_name = value

    def set_phone(self, value: str):
        """Set phone in form data."""
        self.form_data.phone = value

    def set_email(self, value: str):
        """Set email in form data."""
        self.form_data.email = value

    def set_address(self, value: str):
        """Set address in form data."""
        self.form_data.address = value

    def set_property_type(self, value: str):
        """Set property type in form data."""
        self.form_data.property_type = value

    def set_notes(self, value: str):
        """Set notes in form data."""
        self.form_data.notes = value

    @rx.var
    def total_customers(self) -> int:
        """Total number of customers."""
        return len(self.customers)

    @rx.var
    def active_customers(self) -> int:
        """Number of active customers."""
        return len([c for c in self.customers if c.customer_status == "active"])

    @rx.var
    def total_lifetime_value(self) -> float:
        """Total lifetime value of all customers."""
        return sum(c.lifetime_value for c in self.customers)

    @rx.var
    def filtered_count(self) -> int:
        """Number of customers after filters."""
        return len(self.filtered_customers)

    @rx.var
    def total_pages(self) -> int:
        """Total number of pages for pagination."""
        return max(1, (len(self.filtered_customers) + self.items_per_page - 1) // self.items_per_page)

    @rx.var
    def paginated_customers(self) -> List[Customer]:
        """Current page of customers."""
        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        return self.filtered_customers[start_idx:end_idx]

    def next_page(self):
        """Go to next page."""
        if self.current_page < self.total_pages:
            self.current_page += 1

    def prev_page(self):
        """Go to previous page."""
        if self.current_page > 1:
            self.current_page -= 1

    def goto_page(self, page: int):
        """Go to specific page."""
        if 1 <= page <= self.total_pages:
            self.current_page = page


def customer_status_badge(status: str) -> rx.Component:
    """Status badge for customer status."""
    return rx.match(
        status,
        ("active", rx.badge("Active", color_scheme="green", size="1")),
        ("inactive", rx.badge("Inactive", color_scheme="gray", size="1")),
        ("churned", rx.badge("Churned", color_scheme="red", size="1")),
        rx.badge(status, color_scheme="gray", size="1")
    )


def customer_form_modal(state: CustomerState, is_edit: bool = False) -> rx.Component:
    """Customer add/edit form modal."""
    title = "Edit Customer" if is_edit else "Add New Customer"

    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(title),
            rx.form(
                rx.vstack(
                    # Name fields
                    rx.hstack(
                        rx.vstack(
                            rx.text("First Name *", size="2", weight="bold"),
                            rx.input(
                                value=state.form_data.first_name,
                                on_change=state.set_first_name,
                                placeholder="Enter first name",
                                size="2"
                            ),
                            rx.cond(
                                state.form_errors.get("first_name"),
                                rx.text(
                                    state.form_errors.get("first_name"),
                                    color="red",
                                    size="1"
                                )
                            ),
                            width="100%"
                        ),
                        rx.vstack(
                            rx.text("Last Name *", size="2", weight="bold"),
                            rx.input(
                                value=state.form_data.last_name,
                                on_change=state.set_last_name,
                                placeholder="Enter last name",
                                size="2"
                            ),
                            rx.cond(
                                state.form_errors.get("last_name"),
                                rx.text(
                                    state.form_errors.get("last_name"),
                                    color="red",
                                    size="1"
                                )
                            ),
                            width="100%"
                        ),
                        spacing="3",
                        width="100%"
                    ),

                    # Contact fields
                    rx.hstack(
                        rx.vstack(
                            rx.text("Phone *", size="2", weight="bold"),
                            rx.input(
                                value=state.form_data.phone,
                                on_change=state.set_phone,
                                placeholder="(555) 123-4567",
                                size="2"
                            ),
                            rx.cond(
                                state.form_errors.get("phone"),
                                rx.text(
                                    state.form_errors.get("phone"),
                                    color="red",
                                    size="1"
                                )
                            ),
                            width="100%"
                        ),
                        rx.vstack(
                            rx.text("Email", size="2", weight="bold"),
                            rx.input(
                                value=state.form_data.email,
                                on_change=state.set_email,
                                placeholder="email@example.com",
                                type="email",
                                size="2"
                            ),
                            width="100%"
                        ),
                        spacing="3",
                        width="100%"
                    ),

                    # Address field
                    rx.vstack(
                        rx.text("Address *", size="2", weight="bold"),
                        rx.input(
                            value=state.form_data.address,
                            on_change=state.set_address,
                            placeholder="123 Main St, City, State ZIP",
                            size="2"
                        ),
                        rx.cond(
                            state.form_errors.get("address"),
                            rx.text(
                                state.form_errors.get("address"),
                                color="red",
                                size="1"
                            )
                        ),
                        width="100%"
                    ),

                    # Property type
                    rx.vstack(
                        rx.text("Property Type", size="2", weight="bold"),
                        rx.select(
                            ["residential", "commercial", "industrial"],
                            value=state.form_data.property_type,
                            on_change=state.set_property_type,
                            size="2"
                        ),
                        width="100%"
                    ),

                    # Notes field
                    rx.vstack(
                        rx.text("Notes", size="2", weight="bold"),
                        rx.text_area(
                            value=state.form_data.notes,
                            on_change=state.set_notes,
                            placeholder="Additional notes...",
                            rows="3",
                            width="100%"
                        ),
                        width="100%"
                    ),

                    # Action buttons
                    rx.hstack(
                        rx.dialog.close(
                            rx.button(
                                "Cancel",
                                variant="soft",
                                color_scheme="gray",
                                size="2"
                            )
                        ),
                        rx.button(
                            "Save Customer" if not is_edit else "Update Customer",
                            type="submit",
                            color_scheme="green",
                            size="2"
                        ),
                        spacing="2",
                        justify="end",
                        width="100%"
                    ),

                    spacing="4",
                    width="100%"
                ),
                on_submit=state.update_customer if is_edit else state.save_customer,
                width="100%"
            ),
            max_width="500px"
        ),
        open=state.show_edit_modal if is_edit else state.show_add_modal
    )


def customer_detail_modal(state: CustomerState) -> rx.Component:
    """Customer detail view modal with project history."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Customer Details"),
            rx.cond(
                state.selected_customer,
                rx.vstack(
                    # Customer info
                    rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.vstack(
                                    rx.heading(
                                        f"{state.selected_customer.first_name} {state.selected_customer.last_name}",
                                        size="4"
                                    ),
                                    rx.text(state.selected_customer.address, color="gray"),
                                    align_items="start",
                                    spacing="1"
                                ),
                                rx.spacer(),
                                customer_status_badge(state.selected_customer.customer_status),
                                width="100%",
                                align_items="start"
                            ),

                            rx.divider(),

                            rx.hstack(
                                rx.vstack(
                                    rx.text("Phone", size="2", weight="bold"),
                                    rx.hstack(
                                        rx.icon("phone", size=16),
                                        rx.text(state.selected_customer.phone, size="2"),
                                        spacing="1"
                                    ),
                                    align_items="start",
                                    spacing="1"
                                ),
                                rx.vstack(
                                    rx.text("Email", size="2", weight="bold"),
                                    rx.hstack(
                                        rx.icon("mail", size=16),
                                        rx.text(
                                            rx.cond(state.selected_customer.email, state.selected_customer.email, "Not provided"),
                                            size="2"
                                        ),
                                        spacing="1"
                                    ),
                                    align_items="start",
                                    spacing="1"
                                ),
                                spacing="6",
                                width="100%"
                            ),

                            rx.hstack(
                                rx.vstack(
                                    rx.text("Lifetime Value", size="2", weight="bold"),
                                    rx.text(
                                        f"${state.selected_customer.lifetime_value:,.2f}",
                                        size="2",
                                        color="green",
                                        weight="bold"
                                    ),
                                    align_items="start",
                                    spacing="1"
                                ),
                                rx.vstack(
                                    rx.text("Total Projects", size="2", weight="bold"),
                                    rx.text(
                                        str(state.selected_customer.total_projects),
                                        size="2"
                                    ),
                                    align_items="start",
                                    spacing="1"
                                ),
                                rx.vstack(
                                    rx.text("Customer Since", size="2", weight="bold"),
                                    rx.text(
                                        state.selected_customer.created_at,
                                        size="2"
                                    ),
                                    align_items="start",
                                    spacing="1"
                                ),
                                spacing="6",
                                width="100%"
                            ),

                            rx.cond(
                                state.selected_customer.notes,
                                rx.vstack(
                                    rx.text("Notes", size="2", weight="bold"),
                                    rx.text(
                                        state.selected_customer.notes,
                                        size="2",
                                        color="gray"
                                    ),
                                    align_items="start",
                                    spacing="1",
                                    width="100%"
                                )
                            ),

                            spacing="3",
                            width="100%"
                        ),
                        size="2"
                    ),

                    # Project history
                    rx.card(
                        rx.vstack(
                            rx.heading("Project History", size="3"),
                            rx.cond(
                                state.customer_projects,
                                rx.vstack(
                                    rx.foreach(
                                        state.customer_projects,
                                        lambda project: rx.card(
                                            rx.vstack(
                                                rx.hstack(
                                                    rx.text(
                                                        project.name,
                                                        weight="bold",
                                                        size="2"
                                                    ),
                                                    rx.spacer(),
                                                    rx.badge(
                                                        project.status.title(),
                                                        color_scheme=rx.cond(project.status == "completed", "green", "blue")
                                                    ),
                                                    width="100%"
                                                ),
                                                rx.text(
                                                    project.description,
                                                    color="gray",
                                                    size="2"
                                                ),
                                                rx.hstack(
                                                    rx.text(
                                                        f"${project.value:,.2f}",
                                                        color="green",
                                                        weight="bold"
                                                    ),
                                                    rx.text("•", color="gray"),
                                                    rx.text(
                                                        rx.cond(
                                                            project.end_date,
                                                            f"{project.start_date} to {project.end_date}",
                                                            f"{project.start_date} to Present"
                                                        ),
                                                        color="gray",
                                                        size="2"
                                                    ),
                                                    spacing="2"
                                                ),
                                                spacing="2",
                                                align_items="start",
                                                width="100%"
                                            ),
                                            size="1"
                                        )
                                    ),
                                    spacing="2",
                                    width="100%"
                                ),
                                rx.text(
                                    "No projects found for this customer.",
                                    color="gray",
                                    size="2"
                                )
                            ),
                            spacing="3",
                            width="100%"
                        ),
                        size="2"
                    ),

                    # Action buttons
                    rx.hstack(
                        rx.button(
                            rx.icon("phone", size=16),
                            "Call",
                            on_click=lambda: state.call_customer(state.selected_customer.phone),
                            color_scheme="green",
                            size="2"
                        ),
                        rx.cond(
                            state.selected_customer.email,
                            rx.button(
                                rx.icon("mail", size=16),
                                "Email",
                                on_click=lambda: state.email_customer(state.selected_customer.email),
                                color_scheme="blue",
                                size="2"
                            )
                        ),
                        rx.button(
                            rx.icon("pencil", size=16),
                            "Edit",
                            on_click=lambda: state.open_edit_modal(state.selected_customer.id),
                            variant="soft",
                            size="2"
                        ),
                        rx.dialog.close(
                            rx.button(
                                "Close",
                                variant="soft",
                                color_scheme="gray",
                                size="2"
                            )
                        ),
                        spacing="2",
                        justify="end",
                        width="100%"
                    ),

                    spacing="4",
                    width="100%"
                ),
                rx.text("No customer selected", color="gray")
            ),
            max_width="600px",
            max_height="80vh"
        ),
        open=state.show_detail_modal
    )


def customers_table(state: CustomerState) -> rx.Component:
    """Customer table with proper Reflex patterns."""
    return rx.vstack(
        # Header with controls
        rx.hstack(
            rx.heading("Customer Management", size="5"),
            rx.spacer(),
            rx.hstack(
                rx.select(
                    ["all", "active", "inactive", "churned"],
                    value=state.status_filter,
                    on_change=state.set_status_filter,
                    placeholder="Filter by status",
                    size="2"
                ),
                rx.input(
                    value=state.search_query,
                    on_change=state.set_search_query,
                    placeholder="Search customers...",
                    size="2"
                ),
                rx.button(
                    rx.icon("plus", size=16),
                    "New Customer",
                    on_click=state.open_add_modal,
                    color_scheme="green",
                    size="2"
                ),
                spacing="2"
            ),
            justify="between",
            align_items="center",
            width="100%",
            margin_bottom="4"
        ),

        # Summary stats
        rx.hstack(
            rx.card(
                rx.vstack(
                    rx.text("Total Customers", size="2", color="gray"),
                    rx.text(state.total_customers, size="6", weight="bold"),
                    rx.text("All time", size="1", color="slate"),
                    align_items="start",
                    spacing="1"
                ),
                size="2",
                width="100%"
            ),
            rx.card(
                rx.vstack(
                    rx.text("Active Customers", size="2", color="gray"),
                    rx.text(state.active_customers, size="6", weight="bold"),
                    rx.text("Currently active", size="1", color="slate"),
                    align_items="start",
                    spacing="1"
                ),
                size="2",
                width="100%"
            ),
            rx.card(
                rx.vstack(
                    rx.text("Total Lifetime Value", size="2", color="gray"),
                    rx.text(f"${state.total_lifetime_value:,.0f}", size="6", weight="bold"),
                    rx.text("Combined value", size="1", color="slate"),
                    align_items="start",
                    spacing="1"
                ),
                size="2",
                width="100%"
            ),
            rx.card(
                rx.vstack(
                    rx.text("Showing", size="2", color="gray"),
                    rx.text(state.filtered_count, size="6", weight="bold"),
                    rx.text("After filters", size="1", color="slate"),
                    align_items="start",
                    spacing="1"
                ),
                size="2",
                width="100%"
            ),
            spacing="4",
            margin_bottom="4"
        ),

        # Messages
        rx.cond(
            state.success_message,
            rx.callout(
                state.success_message,
                icon="check",
                color_scheme="green",
                size="2",
                margin_bottom="4"
            )
        ),

        rx.cond(
            state.error_message,
            rx.callout(
                state.error_message,
                icon="circle_alert",
                color_scheme="red",
                size="2",
                margin_bottom="4"
            )
        ),

        # Loading state
        rx.cond(
            state.loading,
            rx.card(
                rx.vstack(
                    rx.spinner(size="3"),
                    rx.text("Loading customers...", size="3", color="gray"),
                    spacing="3",
                    align_items="center",
                    padding="8"
                ),
                size="2",
                width="100%"
            ),
            # Main table
            rx.card(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Customer"),
                            rx.table.column_header_cell("Contact"),
                            rx.table.column_header_cell("Status"),
                            rx.table.column_header_cell("Lifetime Value"),
                            rx.table.column_header_cell("Projects"),
                            rx.table.column_header_cell("Last Project"),
                            rx.table.column_header_cell("Actions"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            state.paginated_customers,
                            lambda customer: rx.table.row(
                                rx.table.cell(
                                    rx.vstack(
                                        rx.text(
                                            f"{customer.first_name} {customer.last_name}",
                                            weight="bold",
                                            size="2"
                                        ),
                                        rx.text(
                                            customer.address,
                                            color="gray",
                                            size="1"
                                        ),
                                        align_items="start",
                                        spacing="1"
                                    )
                                ),
                                rx.table.cell(
                                    rx.vstack(
                                        rx.text(customer.phone, size="2"),
                                        rx.text(
                                            rx.cond(customer.email, customer.email, "-"),
                                            color="gray",
                                            size="1"
                                        ),
                                        align_items="start",
                                        spacing="1"
                                    )
                                ),
                                rx.table.cell(
                                    customer_status_badge(customer.customer_status)
                                ),
                                rx.table.cell(
                                    rx.text(
                                        f"${customer.lifetime_value:,.0f}",
                                        weight="bold",
                                        color="green"
                                    )
                                ),
                                rx.table.cell(
                                    rx.text(str(customer.total_projects))
                                ),
                                rx.table.cell(
                                    rx.text(
                                        rx.cond(customer.last_project_date, customer.last_project_date, "-"),
                                        color="gray"
                                    )
                                ),
                                rx.table.cell(
                                    rx.hstack(
                                        rx.button(
                                            rx.icon("phone", size=14),
                                            on_click=lambda customer_phone=customer.phone: state.call_customer(customer_phone),
                                            size="1",
                                            variant="soft",
                                            color_scheme="green"
                                        ),
                                        rx.cond(
                                            customer.email,
                                            rx.button(
                                                rx.icon("mail", size=14),
                                                on_click=lambda customer_email=customer.email: state.email_customer(customer_email),
                                                size="1",
                                                variant="soft",
                                                color_scheme="blue"
                                            )
                                        ),
                                        rx.button(
                                            rx.icon("eye", size=14),
                                            on_click=lambda customer_id=customer.id: state.open_detail_modal(customer_id),
                                            size="1",
                                            variant="soft"
                                        ),
                                        rx.button(
                                            rx.icon("pencil", size=14),
                                            on_click=lambda customer_id=customer.id: state.open_edit_modal(customer_id),
                                            size="1",
                                            variant="soft"
                                        ),
                                        spacing="1"
                                    )
                                )
                            )
                        )
                    ),
                    size="2",
                    width="100%"
                ),
                size="2",
                width="100%"
            )
        ),

        # Pagination
        rx.cond(
            state.total_pages > 1,
            rx.hstack(
                rx.button(
                    rx.icon("chevron_left", size=16),
                    "Previous",
                    on_click=state.prev_page,
                    disabled=state.current_page == 1,
                    variant="soft",
                    size="2"
                ),
                rx.text(
                    f"Page {state.current_page} of {state.total_pages}",
                    size="2"
                ),
                rx.button(
                    "Next",
                    rx.icon("chevron_right", size=16),
                    on_click=state.next_page,
                    disabled=state.current_page == state.total_pages,
                    variant="soft",
                    size="2"
                ),
                spacing="2",
                justify="center",
                margin_top="4"
            )
        ),

        spacing="4",
        width="100%"
    )


def customers_list_page() -> rx.Component:
    """Complete customers list page with proper Reflex state management."""
    return rx.container(
        rx.color_mode.button(position="top-right"),

        # Navigation breadcrumb
        rx.hstack(
            rx.link(
                rx.button(
                    rx.icon("arrow_left", size=16),
                    "Back to Dashboard",
                    variant="ghost",
                    size="2"
                ),
                href="/"
            ),
            rx.text("/", color="gray"),
            rx.text("Customer Management", weight="bold"),
            spacing="2",
            align_items="center",
            margin_bottom="4"
        ),

        # Main content
        customers_table(CustomerState),

        # Modals
        customer_form_modal(CustomerState, is_edit=False),
        customer_form_modal(CustomerState, is_edit=True),
        customer_detail_modal(CustomerState),

        # Auto-load data on page mount
        on_mount=CustomerState.load_customers,

        # Clear messages on click
        on_click=CustomerState.clear_messages,

        size="4",
        padding="4"
    )


# Alias for backward compatibility
customers_page = customers_list_page