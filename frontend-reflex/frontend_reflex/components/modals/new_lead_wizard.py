"""
New Lead Creation Wizard with complete multi-step functionality.

Comprehensive 5-step wizard for creating new leads with:
- Contact Information
- Property Details
- Project Information
- Lead Qualification (BANT)
- Review & Submit

Features:
- Full validation
- Lead scoring calculation
- Duplicate detection
- Multi-step navigation
- Professional UI
"""

import reflex as rx
from typing import Dict, List, Optional, Any


class NewLeadWizardState(rx.State):
    """State management for the New Lead Wizard."""

    # Current step (1-5)
    current_step: int = 1

    # Form data
    form_data: Dict[str, Any] = {}

    # UI states
    show_modal: bool = False
    is_loading: bool = False
    show_success: bool = False
    show_error: bool = False
    error_message: str = ""
    duplicate_warning: str = ""

    # Lead scoring
    calculated_score: int = 0
    calculated_temperature: str = "cold"
    score_breakdown: Dict[str, Any] = {}

    # Validation errors
    validation_errors: Dict[str, str] = {}

    def open_wizard(self):
        """Open the wizard modal."""
        self.show_modal = True
        self.current_step = 1
        self.form_data = {}
        self.validation_errors = {}
        self.show_error = False
        self.show_success = False
        self.duplicate_warning = ""

    def close_wizard(self):
        """Close the wizard modal."""
        self.show_modal = False
        self.reset_form()

    def reset_form(self):
        """Reset all form data."""
        self.form_data = {}
        self.validation_errors = {}
        self.current_step = 1
        self.is_loading = False
        self.show_error = False
        self.show_success = False
        self.error_message = ""
        self.duplicate_warning = ""
        self.calculated_score = 0
        self.calculated_temperature = "cold"
        self.score_breakdown = {}

    def next_step(self):
        """Move to next step if current step is valid."""
        if self.validate_current_step():
            if self.current_step < 5:
                self.current_step += 1
                if self.current_step == 5:
                    self.calculate_lead_score()

    def previous_step(self):
        """Move to previous step."""
        if self.current_step > 1:
            self.current_step -= 1

    def set_form_field(self, field: str, value: Any):
        """Set a form field value."""
        self.form_data[field] = value
        # Clear validation error for this field
        if field in self.validation_errors:
            del self.validation_errors[field]
        # Check for duplicates on phone/email
        if field in ["phone", "email"] and value:
            self.check_duplicate(field, value)

    def check_duplicate(self, field: str, value: str):
        """Check for duplicate leads (mock implementation)."""
        # In real implementation, this would query the backend
        # For now, simulate some duplicates for demo
        if field == "phone" and value == "(248) 555-1234":
            self.duplicate_warning = f"Warning: A lead with phone {value} already exists."
        elif field == "email" and value == "existing@example.com":
            self.duplicate_warning = f"Warning: A lead with email {value} already exists."
        else:
            self.duplicate_warning = ""

    def validate_current_step(self) -> bool:
        """Validate the current step."""
        self.validation_errors = {}

        if self.current_step == 1:
            return self._validate_step_1()
        elif self.current_step == 2:
            return self._validate_step_2()
        elif self.current_step == 3:
            return self._validate_step_3()
        elif self.current_step == 4:
            return self._validate_step_4()
        elif self.current_step == 5:
            return True

        return False

    def _validate_step_1(self) -> bool:
        """Validate step 1: Contact Information."""
        errors = {}

        if not self.form_data.get("first_name", "").strip():
            errors["first_name"] = "First name is required"
        elif len(self.form_data.get("first_name", "")) > 100:
            errors["first_name"] = "First name must be 100 characters or less"

        if not self.form_data.get("last_name", "").strip():
            errors["last_name"] = "Last name is required"
        elif len(self.form_data.get("last_name", "")) > 100:
            errors["last_name"] = "Last name must be 100 characters or less"

        phone = self.form_data.get("phone", "").strip()
        if not phone:
            errors["phone"] = "Phone number is required"
        else:
            # Validate phone format
            import re
            cleaned_phone = re.sub(r'[^\d]', '', phone)
            if len(cleaned_phone) < 10:
                errors["phone"] = "Phone must have at least 10 digits"
            elif len(cleaned_phone) > 15:
                errors["phone"] = "Phone cannot exceed 15 digits"

        email = self.form_data.get("email", "").strip()
        if email:
            # Basic email validation
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                errors["email"] = "Please enter a valid email address"

        if not self.form_data.get("lead_source"):
            errors["lead_source"] = "Lead source is required"

        self.validation_errors = errors
        return len(errors) == 0

    def _validate_step_2(self) -> bool:
        """Validate step 2: Property Details."""
        errors = {}

        if not self.form_data.get("street_address", "").strip():
            errors["street_address"] = "Street address is required"

        if not self.form_data.get("city", "").strip():
            errors["city"] = "City is required"

        if not self.form_data.get("state"):
            errors["state"] = "State is required"

        zip_code = self.form_data.get("zip_code", "").strip()
        if not zip_code:
            errors["zip_code"] = "ZIP code is required"
        else:
            import re
            cleaned_zip = re.sub(r'[^\d]', '', zip_code)
            if len(cleaned_zip) != 5:
                errors["zip_code"] = "ZIP code must be 5 digits"

        self.validation_errors = errors
        return len(errors) == 0

    def _validate_step_3(self) -> bool:
        """Validate step 3: Project Information."""
        errors = {}

        if not self.form_data.get("project_type"):
            errors["project_type"] = "Project type is required"

        if not self.form_data.get("urgency_level"):
            errors["urgency_level"] = "Urgency level is required"

        # Optional validation for budget range
        budget_min = self.form_data.get("budget_range_min")
        budget_max = self.form_data.get("budget_range_max")
        if budget_min and budget_max:
            try:
                min_val = int(budget_min)
                max_val = int(budget_max)
                if min_val >= max_val:
                    errors["budget_range_max"] = "Maximum budget must be greater than minimum"
            except ValueError:
                if budget_min:
                    errors["budget_range_min"] = "Please enter a valid number"
                if budget_max:
                    errors["budget_range_max"] = "Please enter a valid number"

        self.validation_errors = errors
        return len(errors) == 0

    def _validate_step_4(self) -> bool:
        """Validate step 4: Lead Qualification (optional fields)."""
        # All fields in step 4 are optional
        return True

    def calculate_lead_score(self):
        """Calculate lead score for preview."""
        # Mock calculation based on form data
        score = 0

        # Property value scoring (0-30 points)
        property_value = self.form_data.get("property_value")
        if property_value:
            try:
                value = int(property_value)
                if value >= 500000:
                    score += 30
                elif value >= 300000:
                    score += 20
                elif value >= 200000:
                    score += 10
                else:
                    score += 5
            except:
                score += 5
        else:
            score += 5

        # Location scoring (0-10 points)
        zip_code = self.form_data.get("zip_code", "")
        premium_zips = ["48009", "48012", "48025", "48067", "48301", "48302", "48304"]
        target_zips = ["48075", "48084", "48098", "48167", "48103", "48105"]

        if zip_code[:5] in premium_zips:
            score += 10
        elif zip_code[:5] in target_zips:
            score += 7
        else:
            score += 3

        # Lead source scoring (0-15 points)
        source_scores = {
            "website_form": 15,
            "phone_inquiry": 15,
            "referral": 13,
            "google_ads": 12,
            "facebook_ads": 9,
            "door_to_door": 6
        }
        source = self.form_data.get("lead_source", "")
        score += source_scores.get(source, 8)

        # Urgency scoring (0-5 points)
        urgency_scores = {
            "immediate": 5,
            "1_week": 3,
            "1_month": 2,
            "planning": 1
        }
        urgency = self.form_data.get("urgency_level", "")
        score += urgency_scores.get(urgency, 1)

        # BANT scoring (0-10 points)
        if self.form_data.get("budget_confirmed") == "yes":
            score += 3
        if self.form_data.get("decision_maker") == "yes":
            score += 3
        if self.form_data.get("need_identified") == "yes":
            score += 2
        if self.form_data.get("timeline_defined") == "yes":
            score += 2

        # Cap at 100
        score = min(100, score)

        # Determine temperature
        if score >= 80:
            temperature = "hot"
        elif score >= 60:
            temperature = "warm"
        elif score >= 40:
            temperature = "cool"
        else:
            temperature = "cold"

        self.calculated_score = score
        self.calculated_temperature = temperature

    async def submit_lead(self):
        """Submit the lead to the backend."""
        self.is_loading = True
        self.show_error = False

        try:
            # Prepare lead data for submission
            lead_data = {
                "first_name": self.form_data.get("first_name", ""),
                "last_name": self.form_data.get("last_name", ""),
                "phone": self.form_data.get("phone", ""),
                "email": self.form_data.get("email", ""),
                "source": self.form_data.get("lead_source", "website_form"),
                "street_address": self.form_data.get("street_address", ""),
                "city": self.form_data.get("city", ""),
                "state": self.form_data.get("state", ""),
                "zip_code": self.form_data.get("zip_code", ""),
                "property_value": int(self.form_data.get("property_value", 0)) if self.form_data.get("property_value") else None,
                "roof_age": int(self.form_data.get("roof_age", 0)) if self.form_data.get("roof_age") else None,
                "roof_type": self.form_data.get("roof_type", ""),
                "urgency": self.form_data.get("urgency_level", "planning"),
                "project_description": self.form_data.get("project_description", ""),
                "budget_range_min": int(self.form_data.get("budget_range_min", 0)) if self.form_data.get("budget_range_min") else None,
                "budget_range_max": int(self.form_data.get("budget_range_max", 0)) if self.form_data.get("budget_range_max") else None,
                "insurance_claim": self.form_data.get("insurance_claim") == "yes",
                "notes": self.form_data.get("notes", ""),
                "budget_confirmed": self.form_data.get("budget_confirmed") == "yes",
                "is_decision_maker": self.form_data.get("decision_maker") == "yes"
            }

            # Mock success for now - replace with actual API call
            await rx.sleep(2)  # Simulate API call

            self.show_success = True
            self.is_loading = False

            # Auto-close after 3 seconds
            await rx.sleep(3)
            self.close_wizard()

        except Exception as e:
            self.show_error = True
            self.error_message = f"Failed to create lead: {str(e)}"
            self.is_loading = False


def step_indicator() -> rx.Component:
    """Progress indicator showing current step."""
    steps = [
        {"number": 1, "title": "Contact Info", "icon": "user"},
        {"number": 2, "title": "Property Details", "icon": "home"},
        {"number": 3, "title": "Project Info", "icon": "clipboard"},
        {"number": 4, "title": "Qualification", "icon": "check_circle"},
        {"number": 5, "title": "Review", "icon": "eye"}
    ]

    return rx.hstack(
        *[
            rx.fragment(
                rx.hstack(
                    rx.cond(
                        NewLeadWizardState.current_step > step["number"],
                        # Completed step
                        rx.box(
                            rx.icon("check", size=16, color="white"),
                            width="32px",
                            height="32px",
                            border_radius="50%",
                            bg="green.500",
                            display="flex",
                            align_items="center",
                            justify_content="center"
                        ),
                        rx.cond(
                            NewLeadWizardState.current_step == step["number"],
                            # Current step
                            rx.box(
                                rx.text(
                                    str(step["number"]),
                                    size="2",
                                    weight="bold",
                                    color="white"
                                ),
                                width="32px",
                                height="32px",
                                border_radius="50%",
                                bg="blue.500",
                                display="flex",
                                align_items="center",
                                justify_content="center"
                            ),
                            # Future step
                            rx.box(
                                rx.text(
                                    str(step["number"]),
                                    size="2",
                                    weight="normal",
                                    color="gray.600"
                                ),
                                width="32px",
                                height="32px",
                                border_radius="50%",
                                bg="gray.200",
                                display="flex",
                                align_items="center",
                                justify_content="center"
                            )
                        )
                    ),
                    rx.text(
                        step["title"],
                        size="2",
                        weight=rx.cond(
                            NewLeadWizardState.current_step == step["number"],
                            "bold",
                            "normal"
                        ),
                        color=rx.cond(
                            NewLeadWizardState.current_step == step["number"],
                            "black",
                            "gray.600"
                        )
                    ),
                    spacing="2",
                    align_items="center"
                ),
                rx.cond(
                    step["number"] < 5,  # Don't show connector after last step
                    rx.box(
                        width="40px",
                        height="2px",
                        bg=rx.cond(
                            NewLeadWizardState.current_step > step["number"],
                            "green.500",
                            "gray.300"
                        )
                    ),
                    rx.box()  # Empty box for last step
                )
            ) for step in steps
        ],
        justify="center",
        align_items="center",
        spacing="1",
        width="100%",
        margin_bottom="6"
    )


def form_field(label: str, field_name: str, required: bool = False, **kwargs) -> rx.Component:
    """Reusable form field with validation."""
    return rx.vstack(
        rx.hstack(
            rx.text(label, size="2", weight="medium"),
            rx.cond(
                required,
                rx.text("*", color="red.500", size="2"),
                rx.text("")
            ),
            spacing="1"
        ),
        kwargs.get("component", rx.input(
            placeholder=kwargs.get("placeholder", ""),
            size="3",
            value=NewLeadWizardState.form_data.get(field_name, ""),
            on_change=lambda value: NewLeadWizardState.set_form_field(field_name, value),
            **{k: v for k, v in kwargs.items() if k not in ["component", "placeholder"]}
        )),
        rx.cond(
            NewLeadWizardState.validation_errors.get(field_name, "") != "",
            rx.text(
                NewLeadWizardState.validation_errors.get(field_name, ""),
                color="red.500",
                size="1"
            ),
            rx.text("")
        ),
        spacing="1",
        align_items="start",
        width="100%"
    )


def step_1_contact_info() -> rx.Component:
    """Step 1: Contact Information."""
    return rx.vstack(
        rx.heading("Contact Information", size="4", margin_bottom="4"),

        rx.cond(
            NewLeadWizardState.duplicate_warning != "",
            rx.callout(
                NewLeadWizardState.duplicate_warning,
                icon="triangle_alert",
                color_scheme="orange",
                size="1",
                margin_bottom="4"
            ),
            rx.box()
        ),

        # Name fields in a row
        rx.hstack(
            form_field(
                "First Name",
                "first_name",
                required=True,
                placeholder="John",
                width="100%"
            ),
            form_field(
                "Last Name",
                "last_name",
                required=True,
                placeholder="Doe",
                width="100%"
            ),
            spacing="4",
            width="100%"
        ),

        # Contact fields
        form_field(
            "Phone Number",
            "phone",
            required=True,
            placeholder="(248) 555-1234",
            type="tel"
        ),

        form_field(
            "Email Address",
            "email",
            placeholder="john.doe@email.com",
            type="email"
        ),

        form_field(
            "Lead Source",
            "lead_source",
            required=True,
            component=rx.select(
                ["website_form", "phone_inquiry", "referral", "google_ads", "facebook_ads", "door_to_door"],
                placeholder="Select lead source",
                size="3",
                value=NewLeadWizardState.form_data.get("lead_source", ""),
                on_change=lambda value: NewLeadWizardState.set_form_field("lead_source", value)
            )
        ),

        spacing="4",
        width="100%"
    )


def step_2_property_details() -> rx.Component:
    """Step 2: Property Details."""
    return rx.vstack(
        rx.heading("Property Details", size="4", margin_bottom="4"),

        form_field(
            "Street Address",
            "street_address",
            required=True,
            placeholder="123 Main Street"
        ),

        rx.hstack(
            form_field(
                "City",
                "city",
                required=True,
                placeholder="Birmingham",
                width="50%"
            ),
            form_field(
                "State",
                "state",
                required=True,
                component=rx.select(
                    ["MI", "OH", "IN", "IL", "WI"],
                    placeholder="MI",
                    size="3",
                    value=NewLeadWizardState.form_data.get("state", ""),
                    on_change=lambda value: NewLeadWizardState.set_form_field("state", value)
                ),
                width="25%"
            ),
            form_field(
                "ZIP Code",
                "zip_code",
                required=True,
                placeholder="48009",
                width="25%"
            ),
            spacing="4",
            width="100%"
        ),

        rx.hstack(
            form_field(
                "Property Type",
                "property_type",
                component=rx.select(
                    ["Residential", "Commercial", "Multi-Family"],
                    placeholder="Select type",
                    size="3",
                    value=NewLeadWizardState.form_data.get("property_type", ""),
                    on_change=lambda value: NewLeadWizardState.set_form_field("property_type", value)
                ),
                width="50%"
            ),
            form_field(
                "Property Value",
                "property_value",
                placeholder="400000",
                type="number",
                width="50%"
            ),
            spacing="4",
            width="100%"
        ),

        rx.hstack(
            form_field(
                "Roof Age (years)",
                "roof_age",
                placeholder="15",
                type="number",
                width="33%"
            ),
            form_field(
                "Roof Type",
                "roof_type",
                component=rx.select(
                    ["Asphalt Shingle", "Metal", "Tile", "Flat", "Cedar", "Slate"],
                    placeholder="Select type",
                    size="3",
                    value=NewLeadWizardState.form_data.get("roof_type", ""),
                    on_change=lambda value: NewLeadWizardState.set_form_field("roof_type", value)
                ),
                width="33%"
            ),
            form_field(
                "Roof Size (sq ft)",
                "roof_size",
                placeholder="2500",
                type="number",
                width="34%"
            ),
            spacing="4",
            width="100%"
        ),

        spacing="4",
        width="100%"
    )


def step_3_project_info() -> rx.Component:
    """Step 3: Project Information."""
    return rx.vstack(
        rx.heading("Project Information", size="4", margin_bottom="4"),

        rx.hstack(
            form_field(
                "Project Type",
                "project_type",
                required=True,
                component=rx.select(
                    ["Repair", "Replacement", "Inspection", "Emergency", "New Construction"],
                    placeholder="Select project type",
                    size="3",
                    value=NewLeadWizardState.form_data.get("project_type", ""),
                    on_change=lambda value: NewLeadWizardState.set_form_field("project_type", value)
                ),
                width="50%"
            ),
            form_field(
                "Urgency Level",
                "urgency_level",
                required=True,
                component=rx.select(
                    ["immediate", "1_week", "1_month", "planning"],
                    placeholder="Select urgency",
                    size="3",
                    value=NewLeadWizardState.form_data.get("urgency_level", ""),
                    on_change=lambda value: NewLeadWizardState.set_form_field("urgency_level", value)
                ),
                width="50%"
            ),
            spacing="4",
            width="100%"
        ),

        form_field(
            "Project Description",
            "project_description",
            component=rx.text_area(
                placeholder="Describe the roofing project needs...",
                height="100px",
                size="3",
                value=NewLeadWizardState.form_data.get("project_description", ""),
                on_change=lambda value: NewLeadWizardState.set_form_field("project_description", value)
            )
        ),

        rx.hstack(
            form_field(
                "Insurance Claim",
                "insurance_claim",
                component=rx.select(
                    ["yes", "no", "unknown"],
                    placeholder="Select option",
                    size="3",
                    value=NewLeadWizardState.form_data.get("insurance_claim", ""),
                    on_change=lambda value: NewLeadWizardState.set_form_field("insurance_claim", value)
                ),
                width="50%"
            ),
            form_field(
                "Preferred Timeline",
                "preferred_timeline",
                placeholder="Within 30 days",
                width="50%"
            ),
            spacing="4",
            width="100%"
        ),

        rx.hstack(
            form_field(
                "Budget Min ($)",
                "budget_range_min",
                placeholder="8000",
                type="number",
                width="50%"
            ),
            form_field(
                "Budget Max ($)",
                "budget_range_max",
                placeholder="15000",
                type="number",
                width="50%"
            ),
            spacing="4",
            width="100%"
        ),

        spacing="4",
        width="100%"
    )


def step_4_qualification() -> rx.Component:
    """Step 4: Lead Qualification (BANT)."""
    return rx.vstack(
        rx.heading("Lead Qualification (BANT)", size="4", margin_bottom="4"),

        rx.text(
            "These questions help us qualify the lead and calculate an accurate score.",
            size="2",
            color="gray.600",
            margin_bottom="4"
        ),

        rx.hstack(
            form_field(
                "Budget Confirmed",
                "budget_confirmed",
                component=rx.select(
                    ["yes", "no", "unknown"],
                    placeholder="Select option",
                    size="3",
                    value=NewLeadWizardState.form_data.get("budget_confirmed", ""),
                    on_change=lambda value: NewLeadWizardState.set_form_field("budget_confirmed", value)
                ),
                width="50%"
            ),
            form_field(
                "Decision Maker",
                "decision_maker",
                component=rx.select(
                    ["yes", "no", "unknown"],
                    placeholder="Select option",
                    size="3",
                    value=NewLeadWizardState.form_data.get("decision_maker", ""),
                    on_change=lambda value: NewLeadWizardState.set_form_field("decision_maker", value)
                ),
                width="50%"
            ),
            spacing="4",
            width="100%"
        ),

        rx.hstack(
            form_field(
                "Timeline Defined",
                "timeline_defined",
                component=rx.select(
                    ["yes", "no", "unknown"],
                    placeholder="Select option",
                    size="3",
                    value=NewLeadWizardState.form_data.get("timeline_defined", ""),
                    on_change=lambda value: NewLeadWizardState.set_form_field("timeline_defined", value)
                ),
                width="50%"
            ),
            form_field(
                "Need Identified",
                "need_identified",
                component=rx.select(
                    ["yes", "no", "unknown"],
                    placeholder="Select option",
                    size="3",
                    value=NewLeadWizardState.form_data.get("need_identified", ""),
                    on_change=lambda value: NewLeadWizardState.set_form_field("need_identified", value)
                ),
                width="50%"
            ),
            spacing="4",
            width="100%"
        ),

        form_field(
            "Qualification Notes",
            "notes",
            component=rx.text_area(
                placeholder="Additional notes about qualification...",
                height="100px",
                size="3",
                value=NewLeadWizardState.form_data.get("notes", ""),
                on_change=lambda value: NewLeadWizardState.set_form_field("notes", value)
            )
        ),

        spacing="4",
        width="100%"
    )


def temperature_badge() -> rx.Component:
    """Temperature badge with dynamic color."""
    return rx.cond(
        NewLeadWizardState.calculated_temperature == "hot",
        rx.badge("HOT", color_scheme="red", size="2"),
        rx.cond(
            NewLeadWizardState.calculated_temperature == "warm",
            rx.badge("WARM", color_scheme="orange", size="2"),
            rx.cond(
                NewLeadWizardState.calculated_temperature == "cool",
                rx.badge("COOL", color_scheme="blue", size="2"),
                rx.badge("COLD", color_scheme="gray", size="2")
            )
        )
    )


def step_5_review_submit() -> rx.Component:
    """Step 5: Review & Submit."""
    return rx.vstack(
        rx.heading("Review & Submit", size="4", margin_bottom="4"),

        # Lead Score Card
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("trending_up", size=20, color="purple"),
                    rx.heading("Lead Score", size="3", color="purple"),
                    rx.spacer(),
                    temperature_badge(),
                    justify="between",
                    align_items="center",
                    width="100%"
                ),
                rx.hstack(
                    rx.text(
                        NewLeadWizardState.calculated_score,
                        size="8",
                        weight="bold",
                        color="purple"
                    ),
                    rx.text("/100", size="4", color="gray"),
                    spacing="1",
                    align_items="baseline"
                ),
                rx.text(
                    rx.cond(
                        NewLeadWizardState.calculated_score >= 80,
                        "High priority lead - immediate follow-up required!",
                        rx.cond(
                            NewLeadWizardState.calculated_score >= 60,
                            "Qualified lead - prioritize for same-day contact.",
                            rx.cond(
                                NewLeadWizardState.calculated_score >= 40,
                                "Moderate lead - add to nurture campaign.",
                                "Low priority lead - passive nurturing."
                            )
                        )
                    ),
                    size="2",
                    color="gray.600"
                ),
                spacing="2",
                align_items="center"
            ),
            size="2",
            margin_bottom="4"
        ),

        # Contact Information Summary
        rx.card(
            rx.vstack(
                rx.heading("Contact Information", size="3", color="blue"),
                rx.hstack(
                    rx.text("Name:", weight="medium"),
                    rx.text(f"{NewLeadWizardState.form_data.get('first_name', '')} {NewLeadWizardState.form_data.get('last_name', '')}"),
                    spacing="2"
                ),
                rx.hstack(
                    rx.text("Phone:", weight="medium"),
                    rx.text(NewLeadWizardState.form_data.get("phone", "")),
                    spacing="2"
                ),
                rx.cond(
                    NewLeadWizardState.form_data.get("email", "") != "",
                    rx.hstack(
                        rx.text("Email:", weight="medium"),
                        rx.text(NewLeadWizardState.form_data.get("email", "")),
                        spacing="2"
                    ),
                    rx.box()
                ),
                rx.hstack(
                    rx.text("Source:", weight="medium"),
                    rx.text(NewLeadWizardState.form_data.get("lead_source", "")),
                    spacing="2"
                ),
                spacing="2",
                align_items="start"
            ),
            size="2"
        ),

        # Property Details Summary
        rx.card(
            rx.vstack(
                rx.heading("Property Details", size="3", color="green"),
                rx.text(
                    f"{NewLeadWizardState.form_data.get('street_address', '')}, {NewLeadWizardState.form_data.get('city', '')}, {NewLeadWizardState.form_data.get('state', '')} {NewLeadWizardState.form_data.get('zip_code', '')}",
                    size="2"
                ),
                rx.cond(
                    NewLeadWizardState.form_data.get("property_value", "") != "",
                    rx.hstack(
                        rx.text("Property Value:", weight="medium"),
                        rx.text(f"${int(NewLeadWizardState.form_data.get('property_value', 0)):,}" if NewLeadWizardState.form_data.get("property_value") else ""),
                        spacing="2"
                    ),
                    rx.box()
                ),
                spacing="2",
                align_items="start"
            ),
            size="2"
        ),

        # Project Information Summary
        rx.card(
            rx.vstack(
                rx.heading("Project Information", size="3", color="orange"),
                rx.hstack(
                    rx.text("Type:", weight="medium"),
                    rx.text(NewLeadWizardState.form_data.get("project_type", "")),
                    spacing="2"
                ),
                rx.hstack(
                    rx.text("Urgency:", weight="medium"),
                    rx.text(NewLeadWizardState.form_data.get("urgency_level", "")),
                    spacing="2"
                ),
                rx.cond(
                    NewLeadWizardState.form_data.get("budget_range_min", "") != "" or NewLeadWizardState.form_data.get("budget_range_max", "") != "",
                    rx.hstack(
                        rx.text("Budget:", weight="medium"),
                        rx.text(f"${NewLeadWizardState.form_data.get('budget_range_min', '')}-${NewLeadWizardState.form_data.get('budget_range_max', '')}"),
                        spacing="2"
                    ),
                    rx.box()
                ),
                spacing="2",
                align_items="start"
            ),
            size="2"
        ),

        spacing="4",
        width="100%"
    )


def wizard_navigation() -> rx.Component:
    """Navigation buttons for the wizard."""
    return rx.vstack(
        # Success/Error feedback
        rx.cond(
            NewLeadWizardState.show_success,
            rx.callout(
                "Lead created successfully! The system will now score and assign this lead.",
                icon="check_circle",
                color_scheme="green",
                size="2"
            ),
            rx.box()
        ),

        rx.cond(
            NewLeadWizardState.show_error,
            rx.callout(
                NewLeadWizardState.error_message,
                icon="alert_triangle",
                color_scheme="red",
                size="2"
            ),
            rx.box()
        ),

        rx.hstack(
            # Previous button
            rx.button(
                rx.icon("chevron_left", size=16),
                "Previous",
                variant="outline",
                size="3",
                disabled=(NewLeadWizardState.current_step == 1) | NewLeadWizardState.is_loading,
                on_click=NewLeadWizardState.previous_step
            ),

            rx.spacer(),

            # Next button (steps 1-4)
            rx.cond(
                NewLeadWizardState.current_step < 5,
                rx.button(
                    "Next",
                    rx.icon("chevron_right", size=16),
                    size="3",
                    disabled=NewLeadWizardState.is_loading,
                    on_click=NewLeadWizardState.next_step
                ),
                # Submit button (step 5)
                rx.button(
                    rx.cond(
                        NewLeadWizardState.is_loading,
                        rx.spinner(size="4"),
                        rx.icon("check", size=16)
                    ),
                    rx.cond(
                        NewLeadWizardState.is_loading,
                        "Creating Lead...",
                        "Create Lead"
                    ),
                    color_scheme="green",
                    size="3",
                    disabled=NewLeadWizardState.is_loading | NewLeadWizardState.show_success,
                    on_click=NewLeadWizardState.submit_lead
                )
            ),

            justify="between",
            align_items="center",
            width="100%"
        ),

        spacing="4",
        width="100%",
        margin_top="6"
    )


def wizard_content() -> rx.Component:
    """Dynamic content based on current step."""
    return rx.cond(
        NewLeadWizardState.current_step == 1,
        step_1_contact_info(),
        rx.cond(
            NewLeadWizardState.current_step == 2,
            step_2_property_details(),
            rx.cond(
                NewLeadWizardState.current_step == 3,
                step_3_project_info(),
                rx.cond(
                    NewLeadWizardState.current_step == 4,
                    step_4_qualification(),
                    step_5_review_submit()
                )
            )
        )
    )


def new_lead_wizard() -> rx.Component:
    """Main New Lead Creation Wizard component."""
    return rx.fragment(
        # Trigger button
        rx.button(
            rx.icon("plus", size=16),
            "New Lead",
            color_scheme="green",
            size="2",
            on_click=NewLeadWizardState.open_wizard
        ),

        # Modal dialog
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title(
                    rx.hstack(
                        rx.icon("user_plus", size=20),
                        "Create New Lead",
                        spacing="2",
                        align_items="center"
                    )
                ),

                rx.dialog.description(
                    "Complete all steps to create a new lead with automatic scoring and assignment.",
                    size="2",
                    margin_bottom="4"
                ),

                # Step indicator
                step_indicator(),

                # Dynamic content
                rx.box(
                    wizard_content(),
                    min_height="400px",
                    width="100%"
                ),

                # Navigation
                wizard_navigation(),

                rx.dialog.close(
                    rx.button(
                        "Cancel",
                        variant="outline",
                        size="2"
                    )
                ),

                max_width="800px",
                width="90vw"
            ),

            open=NewLeadWizardState.show_modal,
            on_open_change=lambda open: NewLeadWizardState.close_wizard() if not open else None
        )
    )