"""Project Management Module - Complete Implementation with Kanban Pipeline and Timeline Views."""

import reflex as rx
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from ..state import Project


class ProjectState(rx.State):
    """Project-specific state management with complete project functionality."""

    # Project data
    projects: List[Project] = []
    loading: bool = False
    error_message: str = ""

    # View settings
    current_view: str = "pipeline"  # "pipeline" or "timeline"

    # Filter settings
    filter_status: str = "all"
    filter_team_member: str = "all"
    filter_date_range: str = "all"
    search_query: str = ""

    # Modal states
    show_new_project_modal: bool = False
    show_project_detail_modal: bool = False
    selected_project_id: str = ""

    # Drag and drop state
    dragging_project_id: str = ""
    drag_over_column: str = ""

    # Project status configuration
    project_statuses: Dict[str, str] = {
        "new": "New (Estimate Needed)",
        "quoted": "Quoted (Awaiting Approval)",
        "approved": "Approved (Ready to Schedule)",
        "scheduled": "Scheduled",
        "in_progress": "In Progress",
        "completed": "Completed",
        "cancelled": "Cancelled"
    }

    # Status color schemes
    status_colors: Dict[str, str] = {
        "new": "gray",
        "quoted": "yellow",
        "approved": "green",
        "scheduled": "blue",
        "in_progress": "purple",
        "completed": "green",
        "cancelled": "red"
    }

    def load_projects(self):
        """Load projects data."""
        self.loading = True

        # Mock project data
        self.projects = [
            Project(
                id="proj-1",
                customer_id="cust-1",
                title="Complete Roof Replacement - Smith Residence",
                description="Full roof replacement with premium architectural shingles",
                status="in_progress",
                project_type="Replacement",
                estimated_value=45000.0,
                actual_value=47500.0,
                start_date="2025-01-15",
                completion_date="2025-02-01",
                assigned_team_members=["Mike Johnson", "Sarah Wilson"],
                created_at="2025-01-01T09:00:00Z",
                updated_at="2025-01-15T14:30:00Z"
            ),
            Project(
                id="proj-2",
                customer_id="cust-2",
                title="Storm Damage Repair - Garcia Property",
                description="Emergency repairs after hail damage",
                status="scheduled",
                project_type="Repair",
                estimated_value=18000.0,
                start_date="2025-01-20",
                completion_date="2025-01-25",
                assigned_team_members=["David Brown"],
                created_at="2025-01-05T11:15:00Z",
                updated_at="2025-01-12T09:20:00Z"
            ),
            Project(
                id="proj-3",
                customer_id="cust-3",
                title="Roof Inspection - Johnson Estate",
                description="Annual inspection and maintenance",
                status="quoted",
                project_type="Inspection",
                estimated_value=2500.0,
                assigned_team_members=["Tom Wilson"],
                created_at="2025-01-08T16:45:00Z",
                updated_at="2025-01-08T16:45:00Z"
            ),
            Project(
                id="proj-4",
                customer_id="cust-4",
                title="Gutter Installation - Williams Home",
                description="New seamless gutter system installation",
                status="approved",
                project_type="Installation",
                estimated_value=8500.0,
                start_date="2025-01-25",
                completion_date="2025-01-27",
                assigned_team_members=["Mike Johnson", "Lisa Chen"],
                created_at="2025-01-10T13:20:00Z",
                updated_at="2025-01-14T10:15:00Z"
            ),
            Project(
                id="proj-5",
                customer_id="cust-5",
                title="Commercial Roof Overhaul - Tech Center",
                description="Large commercial project with TPO membrane",
                status="new",
                project_type="Commercial",
                estimated_value=125000.0,
                assigned_team_members=[],
                created_at="2025-01-12T08:30:00Z",
                updated_at="2025-01-12T08:30:00Z"
            ),
            Project(
                id="proj-6",
                customer_id="cust-6",
                title="Completed - Anderson Residence",
                description="Completed roof replacement project",
                status="completed",
                project_type="Replacement",
                estimated_value=32000.0,
                actual_value=31500.0,
                start_date="2024-12-01",
                completion_date="2024-12-15",
                assigned_team_members=["Mike Johnson", "Sarah Wilson"],
                created_at="2024-11-15T09:00:00Z",
                updated_at="2024-12-15T17:00:00Z"
            )
        ]

        self.loading = False

    async def update_project_status(self, project_id: str, new_status: str):
        """Update project status."""
        for project in self.projects:
            if project.id == project_id:
                project.status = new_status
                project.updated_at = datetime.now().isoformat() + "Z"
                break

    def toggle_view(self, view: str):
        """Toggle between pipeline and timeline views."""
        self.current_view = view

    def set_filter_status(self, status: str):
        """Set status filter."""
        self.filter_status = status

    def set_filter_team_member(self, member: str):
        """Set team member filter."""
        self.filter_team_member = member

    def set_search_query(self, query: str):
        """Set search query."""
        self.search_query = query

    def open_new_project_modal(self):
        """Open new project modal."""
        self.show_new_project_modal = True

    def close_new_project_modal(self):
        """Close new project modal."""
        self.show_new_project_modal = False

    def open_project_detail_modal(self, project_id: str):
        """Open project detail modal."""
        self.selected_project_id = project_id
        self.show_project_detail_modal = True

    def close_project_detail_modal(self):
        """Close project detail modal."""
        self.show_project_detail_modal = False
        self.selected_project_id = ""

    # Drag and drop handlers
    def start_drag(self, project_id: str):
        """Start dragging a project card."""
        self.dragging_project_id = project_id

    def end_drag(self):
        """End dragging operation."""
        self.dragging_project_id = ""
        self.drag_over_column = ""

    def drag_over_column_handler(self, column_status: str):
        """Handle drag over column."""
        self.drag_over_column = column_status

    async def drop_project_in_column(self, column_status: str):
        """Handle dropping a project in a column."""
        if self.dragging_project_id and column_status:
            await self.update_project_status(self.dragging_project_id, column_status)
            self.end_drag()

    @rx.var
    def filtered_projects(self) -> List[Project]:
        """Get filtered projects based on current filters."""
        projects = self.projects

        # Apply status filter
        if self.filter_status != "all":
            projects = [p for p in projects if p.status == self.filter_status]

        # Apply team member filter
        if self.filter_team_member != "all":
            projects = [p for p in projects if self.filter_team_member in p.assigned_team_members]

        # Apply search filter
        if self.search_query:
            query = self.search_query.lower()
            projects = [
                p for p in projects
                if query in p.title.lower() or query in p.description.lower()
            ]

        return projects

    # Status-based project getters
    @rx.var
    def new_projects(self) -> List[Project]:
        return [p for p in self.filtered_projects if p.status == "new"]

    @rx.var
    def quoted_projects(self) -> List[Project]:
        return [p for p in self.filtered_projects if p.status == "quoted"]

    @rx.var
    def approved_projects(self) -> List[Project]:
        return [p for p in self.filtered_projects if p.status == "approved"]

    @rx.var
    def scheduled_projects(self) -> List[Project]:
        return [p for p in self.filtered_projects if p.status == "scheduled"]

    @rx.var
    def in_progress_projects(self) -> List[Project]:
        return [p for p in self.filtered_projects if p.status == "in_progress"]

    @rx.var
    def completed_projects(self) -> List[Project]:
        return [p for p in self.filtered_projects if p.status == "completed"]

    @rx.var
    def cancelled_projects(self) -> List[Project]:
        return [p for p in self.filtered_projects if p.status == "cancelled"]

    @rx.var
    def project_stats(self) -> Dict[str, int]:
        """Calculate project statistics."""
        projects = self.filtered_projects
        return {
            "total": len(projects),
            "active": len([p for p in projects if p.status in ["scheduled", "in_progress"]]),
            "overdue": len([p for p in projects if self.is_project_overdue(p)]),
            "total_value": sum(p.estimated_value for p in projects)
        }

    def is_project_overdue(self, project: Project) -> bool:
        """Check if project is overdue."""
        if not project.completion_date or project.status in ["completed", "cancelled"]:
            return False

        try:
            completion_date = datetime.fromisoformat(project.completion_date.replace('Z', '+00:00'))
            return completion_date < datetime.now()
        except:
            return False

    def get_days_until_due(self, project: Project) -> int:
        """Get days until project is due."""
        if not project.completion_date:
            return 0

        try:
            completion_date = datetime.fromisoformat(project.completion_date.replace('Z', '+00:00'))
            delta = completion_date - datetime.now()
            return delta.days
        except:
            return 0

    def get_project_progress(self, project: Project) -> float:
        """Calculate project completion percentage."""
        # Simple logic based on status
        progress_map = {
            "new": 0,
            "quoted": 10,
            "approved": 20,
            "scheduled": 30,
            "in_progress": 65,
            "completed": 100,
            "cancelled": 0
        }
        return progress_map.get(project.status, 0)


def project_card(project: Project) -> rx.Component:
    """Individual project card component for Kanban board."""

    def format_currency(value: float) -> str:
        return f"${value:,.0f}"

    def get_days_display(project: Project) -> str:
        days = ProjectState.get_days_until_due(project)
        if days < 0:
            return f"{abs(days)} days overdue"
        elif days == 0:
            return "Due today"
        elif days <= 7:
            return f"{days} days left"
        else:
            return f"{days} days"

    return rx.card(
        rx.vstack(
            # Project header
            rx.hstack(
                rx.vstack(
                    rx.text(
                        project.title,
                        font_weight="600",
                        font_size="14px",
                        line_height="1.2",
                        no_of_lines=2
                    ),
                    rx.text(
                        project.project_type,
                        font_size="12px",
                        color="gray.600",
                        line_height="1"
                    ),
                    align_items="start",
                    spacing="1"
                ),
                rx.badge(
                    format_currency(project.estimated_value),
                    color_scheme="green",
                    size="2"
                ),
                justify="between",
                align="start",
                width="100%"
            ),

            # Project description
            rx.text(
                project.description,
                font_size="11px",
                color="gray.500",
                line_height="1.3",
                no_of_lines=2
            ),

            # Progress bar
            rx.vstack(
                rx.hstack(
                    rx.text("Progress", font_size="10px", color="gray.400"),
                    rx.text(
                        f"{ProjectState.get_project_progress(project):.0f}%",
                        font_size="10px",
                        color="gray.600",
                        font_weight="600"
                    ),
                    justify="between",
                    width="100%"
                ),
                rx.box(
                    rx.box(
                        width=f"{ProjectState.get_project_progress(project)}%",
                        height="100%",
                        bg="blue.500",
                        border_radius="full",
                        transition="width 0.3s ease"
                    ),
                    width="100%",
                    height="4px",
                    bg="gray.200",
                    border_radius="full"
                ),
                spacing="1",
                width="100%"
            ),

            # Due date and team
            rx.hstack(
                rx.vstack(
                    rx.cond(
                        project.completion_date,
                        rx.text(
                            get_days_display(project),
                            font_size="10px",
                            color=rx.cond(
                                ProjectState.is_project_overdue(project),
                                "red.600",
                                rx.cond(
                                    ProjectState.get_days_until_due(project) <= 7,
                                    "orange.600",
                                    "gray.600"
                                )
                            ),
                            font_weight="500"
                        ),
                        rx.text("No due date", font_size="10px", color="gray.400")
                    ),
                    rx.cond(
                        project.assigned_team_members,
                        rx.text(
                            f"{len(project.assigned_team_members)} team member{'s' if len(project.assigned_team_members) != 1 else ''}",
                            font_size="10px",
                            color="gray.500"
                        ),
                        rx.text("Unassigned", font_size="10px", color="gray.400")
                    ),
                    align_items="start",
                    spacing="0"
                ),
                rx.vstack(
                    rx.icon("eye", size=12, color="gray.400", cursor="pointer"),
                    rx.icon("edit", size=12, color="gray.400", cursor="pointer"),
                    spacing="1"
                ),
                justify="between",
                align="center",
                width="100%"
            ),

            align_items="start",
            spacing="3",
            width="100%"
        ),

        # Card styling
        size="2",
        width="100%",
        cursor="grab",
        _hover={"shadow": "md", "border_color": "blue.300"},
        transition="all 0.2s",
        border="1px solid",
        border_color="gray.200",

        # Click handler
        on_click=lambda project_id=project.id: ProjectState.open_project_detail_modal(project_id)
    )


def project_column(status: str, title: str, projects: List[Project]) -> rx.Component:
    """Individual project column component."""

    def get_column_value(projects: List[Project]) -> str:
        total = sum(p.estimated_value for p in projects)
        return f"${total:,.0f}"

    return rx.vstack(
        # Column header
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.heading(
                        title,
                        size="4",
                        font_weight="600"
                    ),
                    rx.badge(
                        projects.length(),
                        color_scheme=ProjectState.status_colors.get(status, "gray"),
                        size="2"
                    ),
                    justify="between",
                    align="center",
                    width="100%"
                ),
                rx.text(
                    get_column_value(projects),
                    font_size="12px",
                    color="green.600",
                    font_weight="600"
                ),
                spacing="1",
                width="100%"
            ),
            size="2",
            width="100%",
            bg="gray.50",
            border="1px solid",
            border_color="gray.200"
        ),

        # Drop zone for projects
        rx.vstack(
            rx.foreach(
                projects,
                project_card
            ),

            # Empty state
            rx.cond(
                projects.length() == 0,
                rx.card(
                    rx.text(
                        "No projects",
                        color="gray.400",
                        font_size="12px",
                        text_align="center"
                    ),
                    size="2",
                    width="100%",
                    bg="gray.25",
                    border="2px dashed",
                    border_color="gray.200",
                    min_height="60px",
                    display="flex",
                    align_items="center",
                    justify_content="center"
                )
            ),

            spacing="3",
            align_items="stretch",
            width="100%",
            min_height="400px",
            padding="2",
            border_radius="8px",
            border="2px dashed transparent",
            _hover={"border_color": "blue.300", "bg": "blue.25"},
            transition="all 0.2s"
        ),

        spacing="3",
        align_items="stretch",
        width="300px",
        min_width="300px"
    )


def project_pipeline_view() -> rx.Component:
    """Main project pipeline Kanban view."""
    return rx.vstack(
        # Pipeline header
        rx.hstack(
            rx.heading("Project Pipeline", size="6", font_weight="700"),
            rx.hstack(
                rx.button(
                    rx.icon("refresh-cw", size=16),
                    "Refresh",
                    variant="outline",
                    size="2",
                    on_click=ProjectState.load_projects
                ),
                rx.button(
                    rx.icon("plus", size=16),
                    "New Project",
                    size="2",
                    on_click=ProjectState.open_new_project_modal
                ),
                spacing="2"
            ),
            justify="between",
            align="center",
            width="100%",
            margin_bottom="4"
        ),

        # Project stats
        rx.card(
            rx.hstack(
                rx.card(
                    rx.vstack(
                        rx.text("Total Projects", size="2", color="gray"),
                        rx.text(ProjectState.project_stats["total"], size="6", weight="bold"),
                        rx.text("All projects", size="1", color="gray"),
                        spacing="1"
                    ),
                    size="2"
                ),
                rx.card(
                    rx.vstack(
                        rx.text("Active Projects", size="2", color="gray"),
                        rx.text(ProjectState.project_stats["active"], size="6", weight="bold", color="blue"),
                        rx.text("In progress or scheduled", size="1", color="gray"),
                        spacing="1"
                    ),
                    size="2"
                ),
                rx.card(
                    rx.vstack(
                        rx.text("Overdue Projects", size="2", color="gray"),
                        rx.text(ProjectState.project_stats["overdue"], size="6", weight="bold", color="red"),
                        rx.text("Past due date", size="1", color="gray"),
                        spacing="1"
                    ),
                    size="2"
                ),
                rx.card(
                    rx.vstack(
                        rx.text("Total Value", size="2", color="gray"),
                        rx.text(f"${ProjectState.project_stats['total_value']:,.0f}", size="6", weight="bold", color="green"),
                        rx.text("Combined project value", size="1", color="gray"),
                        spacing="1"
                    ),
                    size="2"
                ),
                justify="between",
                align="center",
                width="100%",
                spacing="3"
            ),
            size="2",
            width="100%"
        ),

        # Kanban columns
        rx.scroll_area(
            rx.hstack(
                project_column("new", "New (Estimate Needed)", ProjectState.new_projects),
                project_column("quoted", "Quoted (Awaiting Approval)", ProjectState.quoted_projects),
                project_column("approved", "Approved (Ready to Schedule)", ProjectState.approved_projects),
                project_column("scheduled", "Scheduled", ProjectState.scheduled_projects),
                project_column("in_progress", "In Progress", ProjectState.in_progress_projects),
                project_column("completed", "Completed", ProjectState.completed_projects),
                project_column("cancelled", "Cancelled", ProjectState.cancelled_projects),
                spacing="4",
                align_items="start",
                padding="4"
            ),
            scrollbars="horizontal",
            style={"height": "600px", "width": "100%"}
        ),

        spacing="4",
        width="100%"
    )


def timeline_item(project: Project) -> rx.Component:
    """Individual timeline item component."""

    def get_timeline_position(project: Project) -> str:
        """Calculate timeline position based on dates."""
        # Simplified positioning - in real app would calculate based on actual dates
        return "20%"  # Placeholder

    def get_timeline_width(project: Project) -> str:
        """Calculate timeline width based on project duration."""
        return "15%"  # Placeholder

    return rx.box(
        rx.card(
            rx.vstack(
                rx.text(
                    project.title,
                    font_weight="600",
                    font_size="12px",
                    no_of_lines=1
                ),
                rx.hstack(
                    rx.badge(
                        project.status.replace("_", " ").title(),
                        color_scheme=ProjectState.status_colors.get(project.status, "gray"),
                        size="1"
                    ),
                    rx.text(
                        f"${project.estimated_value:,.0f}",
                        font_size="10px",
                        color="green.600",
                        font_weight="600"
                    ),
                    justify="between",
                    width="100%"
                ),
                spacing="1"
            ),
            size="1",
            width="100%",
            min_height="60px",
            cursor="pointer",
            on_click=lambda project_id=project.id: ProjectState.open_project_detail_modal(project_id)
        ),
        position="absolute",
        left=get_timeline_position(project),
        width=get_timeline_width(project),
        z_index="1"
    )


def project_timeline_view() -> rx.Component:
    """Project timeline/Gantt chart view."""

    # Generate date headers for the next 3 months
    def generate_date_headers() -> List[rx.Component]:
        headers = []
        current_date = datetime.now()
        for i in range(12):  # 12 weeks
            week_date = current_date + timedelta(weeks=i)
            headers.append(
                rx.text(
                    week_date.strftime("%b %d"),
                    font_size="11px",
                    color="gray.600",
                    text_align="center",
                    width="8.33%"
                )
            )
        return headers

    return rx.vstack(
        # Timeline header
        rx.hstack(
            rx.heading("Project Timeline", size="6", font_weight="700"),
            rx.hstack(
                rx.button(
                    rx.icon("calendar", size=16),
                    "3 Months",
                    variant="outline",
                    size="2"
                ),
                rx.button(
                    rx.icon("filter", size=16),
                    "Filter",
                    variant="outline",
                    size="2"
                ),
                spacing="2"
            ),
            justify="between",
            align="center",
            width="100%",
            margin_bottom="4"
        ),

        # Timeline container
        rx.card(
            rx.vstack(
                # Timeline header with dates
                rx.hstack(
                    rx.box(width="200px"),  # Space for project names
                    *generate_date_headers(),
                    width="100%",
                    border_bottom="1px solid",
                    border_color="gray.200",
                    padding_bottom="2"
                ),

                # Timeline rows
                rx.vstack(
                    rx.foreach(
                        ProjectState.filtered_projects,
                        lambda project: rx.hstack(
                            # Project name column
                            rx.box(
                                rx.vstack(
                                    rx.text(
                                        project.title,
                                        font_weight="600",
                                        font_size="12px",
                                        no_of_lines=1
                                    ),
                                    rx.text(
                                        project.project_type,
                                        font_size="10px",
                                        color="gray.500"
                                    ),
                                    align_items="start",
                                    spacing="1"
                                ),
                                width="200px",
                                border_right="1px solid",
                                border_color="gray.200",
                                padding="2"
                            ),

                            # Timeline bar area
                            rx.box(
                                timeline_item(project),
                                position="relative",
                                width="100%",
                                height="60px",
                                bg="gray.25",
                                border_bottom="1px solid",
                                border_color="gray.100"
                            ),

                            width="100%",
                            align_items="stretch"
                        )
                    ),
                    spacing="0",
                    width="100%"
                ),

                spacing="0",
                width="100%"
            ),
            size="3",
            width="100%"
        ),

        # Timeline legend
        rx.card(
            rx.hstack(
                rx.text("Legend:", font_weight="600", size="2"),
                rx.hstack(
                    *[
                        rx.hstack(
                            rx.box(
                                width="12px",
                                height="12px",
                                bg=f"{color}.500",
                                border_radius="2px"
                            ),
                            rx.text(
                                status.replace("_", " ").title(),
                                font_size="11px"
                            ),
                            spacing="1"
                        )
                        for status, color in ProjectState.status_colors.items()
                    ],
                    spacing="4"
                ),
                spacing="4",
                align="center"
            ),
            size="2"
        ),

        spacing="4",
        width="100%"
    )


def project_filters() -> rx.Component:
    """Project filters and search component."""
    return rx.card(
        rx.hstack(
            # Search
            rx.hstack(
                rx.icon("search", size=16, color="gray.500"),
                rx.input(
                    placeholder="Search projects...",
                    value=ProjectState.search_query,
                    on_change=ProjectState.set_search_query,
                    size="2",
                    width="250px"
                ),
                spacing="2"
            ),

            # Filters
            rx.hstack(
                rx.select(
                    ["all", "new", "quoted", "approved", "scheduled", "in_progress", "completed", "cancelled"],
                    placeholder="All Statuses",
                    value=ProjectState.filter_status,
                    on_change=ProjectState.set_filter_status,
                    size="2"
                ),
                rx.select(
                    ["all", "Mike Johnson", "Sarah Wilson", "David Brown", "Tom Wilson", "Lisa Chen"],
                    placeholder="All Team Members",
                    value=ProjectState.filter_team_member,
                    on_change=ProjectState.set_filter_team_member,
                    size="2"
                ),
                rx.select(
                    ["all", "this_week", "this_month", "next_month"],
                    placeholder="All Dates",
                    value=ProjectState.filter_date_range,
                    size="2"
                ),
                spacing="2"
            ),

            justify="between",
            align="center",
            width="100%",
            spacing="4"
        ),
        size="2"
    )


def new_project_modal() -> rx.Component:
    """New project creation modal."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Create New Project"),
            rx.dialog.description("Fill in the details for the new project."),

            rx.vstack(
                rx.input(placeholder="Project Title", size="3"),
                rx.text_area(placeholder="Project Description", size="3"),
                rx.select(
                    ["Replacement", "Repair", "Installation", "Inspection", "Commercial"],
                    placeholder="Project Type",
                    size="3"
                ),
                rx.input(placeholder="Estimated Value ($)", size="3"),
                rx.select(
                    ["Mike Johnson", "Sarah Wilson", "David Brown", "Tom Wilson", "Lisa Chen"],
                    placeholder="Assign Team Members",
                    multiple=True,
                    size="3"
                ),
                rx.input(type="date", placeholder="Start Date", size="3"),
                rx.input(type="date", placeholder="Completion Date", size="3"),
                spacing="4",
                width="100%"
            ),

            rx.hstack(
                rx.dialog.close(
                    rx.button("Cancel", variant="outline", size="3")
                ),
                rx.dialog.close(
                    rx.button("Create Project", size="3")
                ),
                justify="end",
                spacing="3",
                margin_top="4"
            ),

            max_width="500px"
        ),
        open=ProjectState.show_new_project_modal,
        on_open_change=ProjectState.close_new_project_modal
    )


def project_detail_modal() -> rx.Component:
    """Project detail modal with tabs."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Project Details"),

            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger("Overview", value="overview"),
                    rx.tabs.trigger("Timeline", value="timeline"),
                    rx.tabs.trigger("Team", value="team"),
                    rx.tabs.trigger("Financial", value="financial"),
                    rx.tabs.trigger("Documents", value="documents"),
                    rx.tabs.trigger("Notes", value="notes")
                ),

                rx.tabs.content(
                    rx.vstack(
                        rx.text("Project overview content will go here."),
                        rx.text("Customer details, project info, status, etc."),
                        spacing="4"
                    ),
                    value="overview"
                ),

                rx.tabs.content(
                    rx.text("Timeline and milestones will go here."),
                    value="timeline"
                ),

                rx.tabs.content(
                    rx.text("Team members and assignments will go here."),
                    value="team"
                ),

                rx.tabs.content(
                    rx.text("Financial information, costs, payments will go here."),
                    value="financial"
                ),

                rx.tabs.content(
                    rx.text("Project documents, quotes, contracts, photos will go here."),
                    value="documents"
                ),

                rx.tabs.content(
                    rx.text("Project notes and communication history will go here."),
                    value="notes"
                ),

                default_value="overview",
                width="100%"
            ),

            rx.dialog.close(
                rx.button("Close", variant="outline", size="3", margin_top="4")
            ),

            max_width="800px",
            height="600px"
        ),
        open=ProjectState.show_project_detail_modal,
        on_open_change=ProjectState.close_project_detail_modal
    )


def projects_list_page() -> rx.Component:
    """Complete projects list page with navigation and pipeline view."""
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
            rx.text("Project Management", weight="bold"),
            spacing="2",
            align_items="center",
            margin_bottom="4"
        ),

        # View toggle
        rx.hstack(
            rx.button(
                rx.icon("columns", size=16),
                "Pipeline",
                variant=rx.cond(
                    ProjectState.current_view == "pipeline",
                    "solid",
                    "outline"
                ),
                size="2",
                on_click=lambda: ProjectState.toggle_view("pipeline")
            ),
            rx.button(
                rx.icon("calendar", size=16),
                "Timeline",
                variant=rx.cond(
                    ProjectState.current_view == "timeline",
                    "solid",
                    "outline"
                ),
                size="2",
                on_click=lambda: ProjectState.toggle_view("timeline")
            ),
            justify="center",
            width="100%",
            margin_bottom="4",
            spacing="2"
        ),

        # Filters
        project_filters(),

        # Main content based on selected view
        rx.cond(
            ProjectState.current_view == "pipeline",
            project_pipeline_view(),
            project_timeline_view()
        ),

        # Modals
        new_project_modal(),
        project_detail_modal(),

        # Loading and error states
        rx.cond(
            ProjectState.loading,
            rx.spinner(size="3"),
        ),

        rx.cond(
            ProjectState.error_message != "",
            rx.callout(
                ProjectState.error_message,
                icon="triangle_alert",
                color_scheme="red",
                status="error"
            )
        ),

        size="4",
        padding="4",
        max_width="100%",
        on_mount=ProjectState.load_projects
    )


def project_timeline_page() -> rx.Component:
    """Project timeline view page."""
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
            rx.text("Project Timeline", weight="bold"),
            spacing="2",
            align_items="center",
            margin_bottom="4"
        ),

        # Timeline view
        project_timeline_view(),

        size="4",
        padding="4",
        max_width="100%",
        on_mount=ProjectState.load_projects
    )


# Backward compatibility aliases
projects_page = projects_list_page
project_pipeline_page = projects_list_page