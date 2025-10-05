# Component Library: Reflex CRM Components

## Overview

The iSwitch Roofs CRM component library provides a comprehensive set of reusable UI components built with Reflex framework. These components follow consistent design patterns, implement business logic, and provide professional user interfaces for all CRM operations.

## Component Categories

### 1. Dashboard Components
### 2. Lead Management Components
### 3. Project Management Components
### 4. Appointment Components
### 5. Analytics Components
### 6. Settings Components
### 7. Modal Components
### 8. Utility Components

---

## 1. Dashboard Components

### KPI Cards (`metrics.py`)

**Purpose:** Display key performance indicators with real-time data

```python
def kpi_card(title: str, value: str, color_scheme: str = "blue") -> rx.Component:
    """Professional KPI card component"""
    return rx.card(
        rx.vstack(
            rx.text(title, size="2", color="gray"),
            rx.text(value, size="6", weight="bold", color=color_scheme),
            align_items="center",
            spacing="1"
        ),
        size="2",
        width="100%"
    )

# Usage Example
kpi_card("Total Leads", AppState.metrics.total_leads.to_string(), "blue")
kpi_card("Hot Leads", AppState.hot_leads.length().to_string(), "orange")
kpi_card("Conversion Rate", f"{AppState.metrics.conversion_rate:.1f}%", "green")
```

**Features:**
- Responsive design with consistent sizing
- Color-coded for different metric types
- Real-time data binding with AppState
- Professional typography and spacing

### Navigation Cards (`dashboard.py`)

**Purpose:** Quick navigation to main system modules

```python
def navigation_card(title: str, description: str, icon: str, href: str, color_scheme: str) -> rx.Component:
    """Navigation card for dashboard module access"""
    return rx.card(
        rx.vstack(
            rx.icon(icon, size=32, color=color_scheme),
            rx.heading(title, size="4"),
            rx.text(description, size="2", color="gray", text_align="center"),
            rx.link(
                rx.button(f"Open {title}", color_scheme=color_scheme, size="2"),
                href=href
            ),
            align_items="center",
            spacing="3"
        ),
        size="3",
        height="200px"
    )

# Usage Examples
navigation_card("Kanban Board", "Manage leads with drag & drop", "layout_grid", "/kanban", "blue")
navigation_card("Analytics", "Performance insights & reports", "bar_chart", "/analytics", "purple")
```

---

## 2. Lead Management Components

### Lead Card (`kanban/lead_card.py`)

**Purpose:** Display individual lead information in Kanban board

```python
def lead_card(lead: Lead) -> rx.Component:
    """Draggable lead card with comprehensive information"""
    return rx.card(
        rx.vstack(
            # Header with name and score
            rx.hstack(
                rx.vstack(
                    rx.text(f"{lead.first_name} {lead.last_name}", weight="bold", size="3"),
                    rx.text(f"{lead.email}", size="2", color="gray"),
                    align_items="start",
                    spacing="1"
                ),
                rx.spacer(),
                rx.badge(f"{lead.lead_score}", color_scheme=get_score_color(lead.lead_score)),
                justify="between",
                width="100%"
            ),

            # Contact information
            rx.vstack(
                rx.text(f"📞 {lead.phone}", size="2"),
                rx.text(f"📍 {lead.location or 'Not specified'}", size="2"),
                rx.text(f"📊 Source: {lead.source}", size="2"),
                align_items="start",
                spacing="1",
                width="100%"
            ),

            # Action buttons
            rx.hstack(
                rx.button(
                    rx.icon("phone", size=16),
                    "Call",
                    size="1",
                    variant="outline",
                    on_click=lambda: AppState.initiate_call(lead.phone)
                ),
                rx.button(
                    rx.icon("mail", size=16),
                    "Email",
                    size="1",
                    variant="outline",
                    on_click=lambda: AppState.open_email_composer(lead.email)
                ),
                rx.button(
                    rx.icon("edit", size=16),
                    "Edit",
                    size="1",
                    variant="solid",
                    on_click=lambda: AppState.open_lead_detail_modal(lead.id)
                ),
                spacing="2",
                width="100%"
            ),

            spacing="3",
            width="100%"
        ),

        # Drag and drop attributes
        class_name="lead-card",
        draggable="true",
        data_lead_id=lead.id,
        data_lead_status=lead.status,

        size="2",
        width="100%",
        margin_bottom="3"
    )

def get_score_color(score: int) -> str:
    """Get color scheme based on lead score"""
    if score >= 80:
        return "red"      # Hot
    elif score >= 60:
        return "orange"   # Warm
    elif score >= 40:
        return "blue"     # Cool
    else:
        return "gray"     # Cold
```

### Kanban Column (`kanban/kanban_column.py`)

**Purpose:** Status column container for Kanban board

```python
def kanban_column(title: str, status: str, leads: list[Lead], color_scheme: str) -> rx.Component:
    """Kanban column with drag-and-drop functionality"""
    return rx.vstack(
        # Column header
        rx.hstack(
            rx.heading(title, size="4"),
            rx.badge(
                rx.text(leads.length().to_string()),
                color_scheme=color_scheme
            ),
            justify="between",
            width="100%"
        ),

        # Drop zone
        rx.box(
            # Lead cards
            rx.cond(
                leads.length() > 0,
                rx.vstack(
                    rx.foreach(leads, lead_card),
                    spacing="2",
                    width="100%"
                ),
                rx.text(
                    "No leads",
                    color="gray",
                    text_align="center",
                    padding="4"
                )
            ),

            # Drop zone styling and data attributes
            class_name="drop-zone",
            data_drop_status=status,
            min_height="400px",
            width="300px",
            padding="3",
            border_radius="md"
        ),

        spacing="3",
        width="300px"
    )
```

---

## 3. Project Management Components

### Project Card (`projects/project_card.py`)

**Purpose:** Display project information in pipeline view

```python
def project_card(project: Project) -> rx.Component:
    """Professional project card with status and financial information"""
    return rx.card(
        rx.vstack(
            # Project header
            rx.hstack(
                rx.vstack(
                    rx.text(project.name, weight="bold", size="3"),
                    rx.text(f"Customer: {project.customer_name}", size="2", color="gray"),
                    align_items="start",
                    spacing="1"
                ),
                rx.spacer(),
                rx.badge(project.status.replace("_", " ").title(), color_scheme=get_project_status_color(project.status)),
                justify="between",
                width="100%"
            ),

            # Financial information
            rx.hstack(
                rx.vstack(
                    rx.text("Estimated Value", size="1", color="gray"),
                    rx.text(f"${project.estimated_value:,.0f}", size="2", weight="bold"),
                    align_items="start",
                    spacing="1"
                ),
                rx.spacer(),
                rx.vstack(
                    rx.text("Start Date", size="1", color="gray"),
                    rx.text(project.start_date.strftime("%m/%d/%Y") if project.start_date else "TBD", size="2"),
                    align_items="end",
                    spacing="1"
                ),
                justify="between",
                width="100%"
            ),

            # Progress indicator
            rx.cond(
                project.progress > 0,
                rx.vstack(
                    rx.text(f"Progress: {project.progress}%", size="2"),
                    rx.progress(value=project.progress, color_scheme="blue"),
                    spacing="1",
                    width="100%"
                ),
                rx.box()
            ),

            # Action buttons
            rx.hstack(
                rx.button(
                    rx.icon("eye", size=16),
                    "View",
                    size="1",
                    variant="outline",
                    on_click=lambda: AppState.open_project_detail_modal(project.id)
                ),
                rx.button(
                    rx.icon("edit", size=16),
                    "Edit",
                    size="1",
                    variant="solid",
                    on_click=lambda: AppState.open_project_edit_modal(project.id)
                ),
                spacing="2",
                width="100%"
            ),

            spacing="3",
            width="100%"
        ),

        # Drag and drop attributes
        class_name="project-card",
        draggable="true",
        data_project_id=project.id,
        data_project_status=project.status,

        size="2",
        width="100%",
        margin_bottom="3"
    )

def get_project_status_color(status: str) -> str:
    """Get color scheme based on project status"""
    status_colors = {
        "planning": "blue",
        "approved": "green",
        "in_progress": "orange",
        "installation": "purple",
        "inspection": "yellow",
        "completed": "green",
        "cancelled": "red"
    }
    return status_colors.get(status, "gray")
```

### Project Timeline (`projects/project_timeline.py`)

**Purpose:** Gantt chart visualization for project scheduling

```python
def project_timeline_view() -> rx.Component:
    """Project timeline with Gantt chart visualization"""
    return rx.vstack(
        # Timeline header
        rx.hstack(
            rx.heading("Project Timeline", size="5"),
            rx.spacer(),
            rx.hstack(
                rx.select(
                    ["This Month", "Next Month", "This Quarter", "Next Quarter"],
                    value=AppState.timeline_period,
                    on_change=AppState.set_timeline_period,
                    size="2"
                ),
                rx.button(
                    rx.icon("refresh_cw", size=16),
                    "Refresh",
                    on_click=AppState.refresh_timeline,
                    size="2"
                ),
                spacing="2"
            ),
            justify="between",
            width="100%"
        ),

        # Timeline chart
        rx.box(
            # Simplified Gantt chart representation
            rx.vstack(
                rx.foreach(
                    AppState.timeline_projects,
                    lambda project: project_timeline_row(project)
                ),
                spacing="2",
                width="100%"
            ),
            width="100%",
            overflow_x="auto"
        ),

        spacing="4",
        width="100%"
    )

def project_timeline_row(project: Project) -> rx.Component:
    """Individual project row in timeline"""
    return rx.hstack(
        # Project info
        rx.vstack(
            rx.text(project.name, weight="bold", size="2"),
            rx.text(f"Customer: {project.customer_name}", size="1", color="gray"),
            align_items="start",
            spacing="1",
            width="200px"
        ),

        # Timeline bar (simplified representation)
        rx.box(
            rx.progress(
                value=project.progress,
                color_scheme=get_project_status_color(project.status)
            ),
            width="400px"
        ),

        # Dates
        rx.vstack(
            rx.text(project.start_date.strftime("%m/%d") if project.start_date else "TBD", size="1"),
            rx.text(project.end_date.strftime("%m/%d") if project.end_date else "TBD", size="1"),
            align_items="center",
            spacing="1",
            width="80px"
        ),

        justify="start",
        width="100%",
        padding="2",
        border="1px solid var(--gray-6)",
        border_radius="md"
    )
```

---

## 4. Appointment Components

### Appointment Calendar (`appointments/appointment_calendar.py`)

**Purpose:** Multi-view calendar interface for appointment management

```python
def appointment_calendar() -> rx.Component:
    """Multi-view calendar with appointment display"""
    return rx.vstack(
        # Calendar header with view controls
        rx.hstack(
            rx.heading("Calendar", size="5"),
            rx.spacer(),
            rx.hstack(
                rx.select(
                    ["Month", "Week", "Day", "List"],
                    value=AppState.calendar_view,
                    on_change=AppState.set_calendar_view,
                    size="2"
                ),
                rx.button(
                    rx.icon("chevron_left", size=16),
                    size="2",
                    on_click=AppState.previous_period
                ),
                rx.text(AppState.current_period_label, size="3", weight="bold"),
                rx.button(
                    rx.icon("chevron_right", size=16),
                    size="2",
                    on_click=AppState.next_period
                ),
                rx.button(
                    rx.icon("plus", size=16),
                    "New Appointment",
                    size="2",
                    on_click=AppState.open_new_appointment_modal
                ),
                spacing="2"
            ),
            justify="between",
            width="100%"
        ),

        # Calendar view
        rx.cond(
            AppState.calendar_view == "Month",
            month_calendar_view(),
            rx.cond(
                AppState.calendar_view == "Week",
                week_calendar_view(),
                rx.cond(
                    AppState.calendar_view == "Day",
                    day_calendar_view(),
                    list_calendar_view()
                )
            )
        ),

        spacing="4",
        width="100%"
    )
```

### Appointment Card (`appointments/appointment_card.py`)

**Purpose:** Display appointment information in various views

```python
def appointment_card(appointment: Appointment) -> rx.Component:
    """Professional appointment card with action buttons"""
    return rx.card(
        rx.vstack(
            # Appointment header
            rx.hstack(
                rx.vstack(
                    rx.text(appointment.title, weight="bold", size="3"),
                    rx.text(f"Type: {appointment.appointment_type.replace('_', ' ').title()}", size="2", color="gray"),
                    align_items="start",
                    spacing="1"
                ),
                rx.spacer(),
                rx.badge(
                    appointment.status.title(),
                    color_scheme=get_appointment_status_color(appointment.status)
                ),
                justify="between",
                width="100%"
            ),

            # Time and location
            rx.vstack(
                rx.hstack(
                    rx.icon("clock", size=16),
                    rx.text(
                        appointment.scheduled_start.strftime("%I:%M %p") if appointment.scheduled_start else "Time TBD",
                        size="2"
                    ),
                    spacing="2"
                ),
                rx.hstack(
                    rx.icon("map_pin", size=16),
                    rx.text(appointment.location or "Location TBD", size="2"),
                    spacing="2"
                ),
                rx.hstack(
                    rx.icon("user", size=16),
                    rx.text(f"Assigned: {appointment.team_member_name or 'Unassigned'}", size="2"),
                    spacing="2"
                ),
                align_items="start",
                spacing="2",
                width="100%"
            ),

            # Customer/Lead information
            rx.cond(
                appointment.customer_id,
                rx.text(f"Customer: {appointment.customer_name}", size="2", color="blue"),
                rx.text(f"Lead: {appointment.lead_name}", size="2", color="orange")
            ),

            # Action buttons
            rx.hstack(
                rx.button(
                    rx.icon("eye", size=16),
                    "View",
                    size="1",
                    variant="outline",
                    on_click=lambda: AppState.open_appointment_detail_modal(appointment.id)
                ),
                rx.button(
                    rx.icon("edit", size=16),
                    "Edit",
                    size="1",
                    variant="solid",
                    on_click=lambda: AppState.open_appointment_edit_modal(appointment.id)
                ),
                rx.cond(
                    appointment.status == "scheduled",
                    rx.button(
                        rx.icon("calendar", size=16),
                        "Reschedule",
                        size="1",
                        variant="outline",
                        on_click=lambda: AppState.open_reschedule_modal(appointment.id)
                    ),
                    rx.box()
                ),
                spacing="2",
                width="100%"
            ),

            spacing="3",
            width="100%"
        ),
        size="2",
        width="100%"
    )

def get_appointment_status_color(status: str) -> str:
    """Get color scheme based on appointment status"""
    status_colors = {
        "scheduled": "blue",
        "confirmed": "green",
        "completed": "green",
        "cancelled": "red",
        "no_show": "orange",
        "rescheduled": "yellow"
    }
    return status_colors.get(status, "gray")
```

---

## 5. Analytics Components

### KPI Cards (`analytics/kpi_cards.py`)

**Purpose:** Display key performance indicators for analytics dashboard

```python
def analytics_kpi_grid() -> rx.Component:
    """Grid of KPI cards for analytics dashboard"""
    return rx.grid(
        # Revenue metrics
        analytics_kpi_card(
            "Total Revenue",
            f"${AppState.revenue_metrics.total_revenue:,.0f}",
            "green",
            "dollar_sign",
            AppState.revenue_trend
        ),
        analytics_kpi_card(
            "Pipeline Value",
            f"${AppState.revenue_metrics.pipeline_value:,.0f}",
            "blue",
            "trending_up",
            AppState.pipeline_trend
        ),
        analytics_kpi_card(
            "Conversion Rate",
            f"{AppState.conversion_metrics.overall_rate:.1f}%",
            "purple",
            "target",
            AppState.conversion_trend
        ),
        analytics_kpi_card(
            "Avg Project Value",
            f"${AppState.revenue_metrics.avg_project_value:,.0f}",
            "orange",
            "bar_chart",
            AppState.avg_value_trend
        ),

        columns="4",
        spacing="4",
        width="100%"
    )

def analytics_kpi_card(title: str, value: str, color_scheme: str, icon: str, trend: float) -> rx.Component:
    """Enhanced KPI card with trend indicator"""
    return rx.card(
        rx.vstack(
            # Header with icon
            rx.hstack(
                rx.icon(icon, size=24, color=color_scheme),
                rx.spacer(),
                trend_indicator(trend),
                justify="between",
                width="100%"
            ),

            # Value
            rx.text(value, size="6", weight="bold", color=color_scheme),

            # Title
            rx.text(title, size="2", color="gray", text_align="center"),

            spacing="2",
            align_items="center",
            width="100%"
        ),
        size="3",
        width="100%"
    )

def trend_indicator(trend: float) -> rx.Component:
    """Trend arrow indicator"""
    if trend > 0:
        return rx.hstack(
            rx.icon("trending_up", size=16, color="green"),
            rx.text(f"+{trend:.1f}%", size="1", color="green"),
            spacing="1"
        )
    elif trend < 0:
        return rx.hstack(
            rx.icon("trending_down", size=16, color="red"),
            rx.text(f"{trend:.1f}%", size="1", color="red"),
            spacing="1"
        )
    else:
        return rx.hstack(
            rx.icon("minus", size=16, color="gray"),
            rx.text("0%", size="1", color="gray"),
            spacing="1"
        )
```

### Conversion Funnel (`analytics/conversion_funnel.py`)

**Purpose:** Visualize sales funnel with conversion rates

```python
def conversion_funnel() -> rx.Component:
    """Sales funnel visualization with conversion rates"""
    return rx.vstack(
        rx.heading("Sales Conversion Funnel", size="4"),

        # Funnel stages
        rx.vstack(
            rx.foreach(
                AppState.funnel_stages,
                lambda stage: funnel_stage(stage)
            ),
            spacing="2",
            width="100%"
        ),

        # Funnel metrics
        funnel_metrics_summary(),

        spacing="4",
        width="100%"
    )

def funnel_stage(stage: dict) -> rx.Component:
    """Individual funnel stage with metrics"""
    return rx.hstack(
        # Stage info
        rx.vstack(
            rx.text(stage["name"], weight="bold", size="3"),
            rx.text(f"{stage['count']} leads", size="2", color="gray"),
            align_items="start",
            spacing="1",
            width="200px"
        ),

        # Visual funnel representation
        rx.box(
            rx.progress(
                value=stage["percentage"],
                color_scheme="blue",
                size="3"
            ),
            width=f"{stage['percentage']}%",
            min_width="100px",
            max_width="600px"
        ),

        # Conversion rate
        rx.vstack(
            rx.text(f"{stage['percentage']:.1f}%", weight="bold", size="2"),
            rx.text("of total", size="1", color="gray"),
            align_items="center",
            spacing="1",
            width="80px"
        ),

        justify="start",
        width="100%",
        padding="3",
        border="1px solid var(--gray-6)",
        border_radius="md"
    )
```

---

## 6. Modal Components

### Lead Detail Modal (`modals/lead_detail_modal.py`)

**Purpose:** Comprehensive lead information display and editing

```python
def lead_detail_modal() -> rx.Component:
    """Multi-tab lead detail modal"""
    return rx.dialog.root(
        rx.dialog.content(
            # Modal header
            rx.dialog.title(
                rx.hstack(
                    rx.text(f"{AppState.selected_lead.first_name} {AppState.selected_lead.last_name}"),
                    rx.spacer(),
                    rx.badge(
                        f"Score: {AppState.selected_lead.lead_score}",
                        color_scheme=get_score_color(AppState.selected_lead.lead_score)
                    ),
                    justify="between",
                    width="100%"
                )
            ),

            # Tab navigation
            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger("Overview", value="overview"),
                    rx.tabs.trigger("Interactions", value="interactions"),
                    rx.tabs.trigger("Files", value="files"),
                    rx.tabs.trigger("History", value="history"),
                ),

                # Tab content
                rx.tabs.content(
                    lead_overview_tab(),
                    value="overview"
                ),
                rx.tabs.content(
                    lead_interactions_tab(),
                    value="interactions"
                ),
                rx.tabs.content(
                    lead_files_tab(),
                    value="files"
                ),
                rx.tabs.content(
                    lead_history_tab(),
                    value="history"
                ),

                default_value="overview",
                width="100%"
            ),

            # Modal footer
            rx.hstack(
                rx.button(
                    "Convert to Customer",
                    color_scheme="green",
                    on_click=AppState.convert_lead_to_customer
                ),
                rx.spacer(),
                rx.button("Close", on_click=AppState.close_lead_detail_modal),
                justify="between",
                width="100%"
            ),

            max_width="800px",
            width="90vw",
            height="80vh"
        ),
        open=AppState.lead_detail_modal_open
    )
```

---

## 7. Utility Components

### Loading States

```python
def loading_spinner(message: str = "Loading...") -> rx.Component:
    """Consistent loading spinner with message"""
    return rx.center(
        rx.vstack(
            rx.spinner(size="3"),
            rx.text(message, size="2", color="gray"),
            spacing="3"
        ),
        height="200px",
        width="100%"
    )

def skeleton_card() -> rx.Component:
    """Skeleton loading card"""
    return rx.card(
        rx.vstack(
            rx.skeleton(height="20px", width="60%"),
            rx.skeleton(height="16px", width="80%"),
            rx.skeleton(height="16px", width="40%"),
            spacing="2"
        ),
        size="2",
        width="100%"
    )
```

### Error States

```python
def error_message(message: str) -> rx.Component:
    """Consistent error message display"""
    return rx.callout(
        message,
        icon="triangle_alert",
        color_scheme="red",
        size="2",
        width="100%"
    )

def success_message(message: str) -> rx.Component:
    """Consistent success message display"""
    return rx.callout(
        message,
        icon="check_circle",
        color_scheme="green",
        size="2",
        width="100%"
    )
```

### Data Tables

```python
def data_table(headers: list[str], data: list[dict], actions: list[dict] = None) -> rx.Component:
    """Reusable data table component"""
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                *[rx.table.column_header_cell(header) for header in headers],
                *([rx.table.column_header_cell("Actions")] if actions else [])
            )
        ),
        rx.table.body(
            rx.foreach(
                data,
                lambda item: rx.table.row(
                    *[rx.table.cell(item[key]) for key in headers.lower().replace(" ", "_")],
                    *([rx.table.cell(
                        rx.hstack(
                            *[rx.button(action["label"], on_click=action["handler"]) for action in actions],
                            spacing="2"
                        )
                    )] if actions else [])
                )
            )
        ),
        width="100%"
    )
```

## Component Usage Patterns

### 1. Consistent Props Pattern

All components follow consistent prop patterns:

```python
def component_template(
    # Required props first
    title: str,
    data: Any,

    # Optional props with defaults
    size: str = "2",
    color_scheme: str = "blue",
    width: str = "100%",

    # Event handlers
    on_click: callable = None,
    on_change: callable = None
) -> rx.Component:
    """Template for consistent component structure"""
    pass
```

### 2. State Integration Pattern

```python
def stateful_component() -> rx.Component:
    """Component with AppState integration"""
    return rx.cond(
        AppState.loading,
        loading_spinner(),
        rx.cond(
            AppState.error_message != "",
            error_message(AppState.error_message),
            actual_component_content()
        )
    )
```

### 3. Responsive Design Pattern

```python
def responsive_component() -> rx.Component:
    """Component with responsive design"""
    return rx.grid(
        *items,
        columns=rx.breakpoints(base="1", sm="2", md="3", lg="4"),
        spacing="4",
        width="100%"
    )
```

## Testing Components

### Component Testing Examples

```python
def test_kpi_card():
    """Test KPI card rendering"""
    card = kpi_card("Test Metric", "100", "blue")
    rendered = card.render()
    assert "Test Metric" in rendered
    assert "100" in rendered

def test_lead_card_with_high_score():
    """Test lead card with high score shows correct color"""
    lead = Lead(first_name="John", last_name="Doe", lead_score=85)
    card = lead_card(lead)
    rendered = card.render()
    assert "red" in rendered  # High score should be red badge
```

## Best Practices

### 1. Component Design
- **Single Responsibility** - Each component has one clear purpose
- **Reusability** - Components work in multiple contexts
- **Consistency** - Follow established design patterns
- **Accessibility** - Include proper ARIA labels and keyboard navigation

### 2. State Integration
- **Reactive Updates** - Components automatically update with state changes
- **Error Handling** - Graceful handling of loading and error states
- **Performance** - Efficient rendering with conditional logic

### 3. Documentation
- **Clear Props** - Document all component parameters
- **Usage Examples** - Provide real-world usage examples
- **Testing** - Include test examples for complex components

---

**Document Version:** 1.0
**Last Updated:** January 17, 2025
**Author:** Development Team
**Review Status:** Complete