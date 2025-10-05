"""Global state management for the iSwitch Roofs CRM dashboard."""

import reflex as rx
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import asyncio
import httpx


class Lead(rx.Base):
    """Lead data model for frontend."""
    id: str
    first_name: str
    last_name: str
    phone: str
    email: Optional[str] = None
    source: str
    status: str
    temperature: Optional[str] = None
    lead_score: int = 0
    created_at: str
    next_follow_up_date: Optional[str] = None
    assigned_to: Optional[str] = None
    address: Optional[str] = None
    estimated_value: Optional[float] = 0.0
    notes: Optional[str] = None


class Customer(rx.Base):
    """Customer data model for frontend."""
    id: str
    first_name: str
    last_name: str
    phone: str
    email: Optional[str] = None
    address: str
    property_type: str
    created_at: str
    lifetime_value: float = 0.0
    total_projects: int = 0
    last_project_date: Optional[str] = None
    customer_status: str = "active"  # active, inactive, churned
    notes: Optional[str] = None
    converted_from_lead_id: Optional[str] = None


class Project(rx.Base):
    """Project data model for frontend."""
    id: str
    customer_id: str
    title: str
    description: str
    status: str
    project_type: str
    estimated_value: float
    actual_value: Optional[float] = None
    start_date: Optional[str] = None
    completion_date: Optional[str] = None
    assigned_team_members: List[str] = []
    created_at: str
    updated_at: str


class Interaction(rx.Base):
    """Interaction data model for frontend."""
    id: str
    entity_type: str  # lead or customer
    entity_id: str
    interaction_type: str  # call, email, meeting, note
    subject: str
    content: str
    created_at: str
    created_by: str
    follow_up_date: Optional[str] = None


class Alert(rx.Base):
    """Alert data model for frontend."""
    id: str
    title: str
    message: str
    alert_type: str
    priority: str
    created_at: str
    acknowledged: bool = False
    related_entity_id: Optional[str] = None


class Appointment(rx.Base):
    """Appointment data model for frontend."""
    id: str
    title: str
    description: Optional[str] = None
    appointment_type: str  # consultation, inspection, project_work, follow_up, estimate
    status: str  # scheduled, confirmed, in_progress, completed, cancelled, no_show
    scheduled_date: str
    duration_minutes: int
    end_time: Optional[str] = None
    entity_type: str  # lead, customer, project
    entity_id: str
    assigned_to: str  # team member ID
    location: Optional[str] = None
    is_virtual: bool = False
    meeting_url: Optional[str] = None
    preparation_notes: Optional[str] = None
    outcome_notes: Optional[str] = None
    reminder_sent: bool = False
    confirmed_by_customer: bool = False
    created_at: str
    updated_at: str


class DashboardMetrics(rx.Base):
    """Dashboard metrics data model."""
    total_leads: int = 0
    hot_leads: int = 0
    conversion_rate: float = 0.0
    monthly_revenue: float = 0.0
    avg_response_time: float = 0.0
    pipeline_value: float = 0.0


class TeamMember(rx.Base):
    """Team member data model for frontend."""
    id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    role: str  # admin, manager, sales_rep, installer
    status: str  # active, inactive, pending
    permissions: List[str] = []
    created_at: str
    last_login: Optional[str] = None


class UserSettings(rx.Base):
    """User settings data model."""
    user_id: str
    notification_preferences: Dict[str, bool] = {}
    dashboard_layout: Dict[str, Any] = {}
    timezone: str = "America/Detroit"
    theme: str = "light"


class AppState(rx.Base):
    """Main application data model - no WebSocket state management.

    This class now serves as a pure data container without rx.State
    reactive functionality, eliminating all WebSocket connections.
    Real-time updates are handled exclusively through Pusher.
    """

    # Authentication
    is_authenticated: bool = False
    user_name: str = ""
    user_role: str = ""

    # Dashboard data
    leads: List[Lead] = []
    customers: List[Customer] = []
    projects: List[Project] = []
    interactions: List[Interaction] = []
    alerts: List[Alert] = []
    appointments: List[Appointment] = []
    metrics: DashboardMetrics = DashboardMetrics()

    # UI state
    loading: bool = False
    error_message: str = ""
    selected_lead_id: Optional[str] = None
    alerts_unread_count: int = 0

    # Filters and search
    lead_status_filter: str = "all"
    lead_temperature_filter: str = "all"
    search_query: str = ""

    # Advanced filtering
    date_range_start: str = ""
    date_range_end: str = ""
    source_filter: List[str] = []
    assigned_user_filter: str = "all"
    score_range_min: int = 0
    score_range_max: int = 100

    # Sorting
    sort_field: str = "created_at"
    sort_direction: str = "desc"  # "asc" or "desc"

    # Bulk operations
    selected_lead_ids: List[str] = []
    select_all_leads: bool = False

    # Pagination
    page_size: int = 25
    current_page: int = 1

    # Modal state
    selected_lead_modal_open: bool = False
    lead_form_modal_open: bool = False
    lead_detail_modal_open: bool = False
    new_lead_wizard_open: bool = False

    # New Lead Wizard state
    new_lead_wizard_step: int = 1
    new_lead_form_data: Dict[str, Any] = {}
    new_lead_step_valid: List[bool] = [False, False, False, False]

    # Team members for assignment
    team_members: List[Dict[str, Any]] = []

    # Success/error feedback
    lead_creation_success: bool = False
    lead_creation_message: str = ""

    # Advanced filters UI state
    advanced_filters_open: bool = False

    # Lead detail state
    selected_lead_detail: Optional[Lead] = None
    lead_detail_active_tab: str = "overview"

    # Customer management state
    selected_customer_id: Optional[str] = None
    selected_customer_detail: Optional[Customer] = None
    customer_detail_modal_open: bool = False
    customer_detail_active_tab: str = "overview"
    customer_projects: List[Project] = []
    customer_interactions: List[Interaction] = []

    # Customer filters
    customer_status_filter: str = "all"
    customer_search_query: str = ""

    # Customer form state
    customer_form_modal_open: bool = False
    customer_form_data: Dict[str, Any] = {}
    customer_form_editing: bool = False

    # Project management state
    selected_project_id: Optional[str] = None
    selected_project_detail: Optional[Project] = None
    project_detail_modal_open: bool = False
    project_status_filter: str = "all"
    project_search_query: str = ""

    # New Project Modal state
    new_project_modal_open: bool = False
    new_project_form_data: Dict[str, Any] = {}
    project_creation_success: bool = False
    project_creation_message: str = ""
    project_form_active_tab: str = "project_info"

    # Form state (legacy - now using wizard)
    new_lead_form_step: int = 1
    form_validation_errors: Dict[str, str] = {}

    # Bulk operations state
    bulk_operation_in_progress: bool = False
    bulk_action_type: str = ""
    bulk_operation_success_message: str = ""
    bulk_confirm_dialog_open: bool = False
    bulk_confirm_action: str = ""
    bulk_confirm_message: str = ""

    # Backend API configuration
    api_base_url: str = "http://localhost:8001"  # Flask Backend API URL

    # Pusher real-time connection state
    pusher_connected: bool = False
    pusher_config: Dict[str, Any] = {}
    last_update: str = ""

    # ================ SETTINGS STATE VARIABLES ================

    # Settings navigation
    settings_active_tab: str = "profile"

    # Team management
    team_members: List[TeamMember] = []
    selected_team_member_id: Optional[str] = None
    team_member_modal_open: bool = False

    # User settings
    user_settings: Optional[UserSettings] = None

    # Settings form state
    settings_loading: bool = False
    settings_saving: bool = False
    settings_success_message: str = ""
    settings_error_message: str = ""
    settings_unsaved_changes: bool = False

    # ================ TIMELINE STATE VARIABLES ================

    # Timeline view configuration
    timeline_view_mode: str = "gantt"  # gantt, calendar, resource
    timeline_date_range: str = "month"  # week, month, quarter
    timeline_start_date: str = ""
    timeline_end_date: str = ""

    # Timeline filters
    timeline_show_overdue: bool = False
    timeline_show_this_week: bool = False
    timeline_show_high_priority: bool = False
    timeline_show_unassigned: bool = False

    # ================ APPOINTMENT STATE VARIABLES ================

    # Appointment UI state
    selected_appointment_id: Optional[str] = None
    appointment_modal_open: bool = False
    appointment_detail_modal_open: bool = False
    calendar_view_mode: str = "month"  # month, week, day, list
    calendar_selected_date: str = ""

    # Appointment form state
    appointment_form_data: Dict[str, Any] = {}
    appointment_form_editing: bool = False
    appointment_creation_success: bool = False
    appointment_creation_message: str = ""

    # Calendar navigation
    calendar_current_date: str = ""
    calendar_view_date: str = ""

    # Appointment filters
    appointment_type_filter: str = "all"
    appointment_status_filter: str = "all"
    appointment_assigned_to_filter: str = "all"
    appointment_search_query: str = ""

    async def load_dashboard_data(self):
        """Load initial dashboard data from backend API."""
        self.loading = True
        self.error_message = ""

        try:
            async with httpx.AsyncClient() as client:
                # Load leads
                leads_response = await client.get(f"{self.api_base_url}/api/leads")
                if leads_response.status_code == 200:
                    leads_data = leads_response.json()
                    self.leads = [Lead(**lead) for lead in leads_data.get("leads", [])]

                # Load alerts
                alerts_response = await client.get(f"{self.api_base_url}/api/alerts")
                if alerts_response.status_code == 200:
                    alerts_data = alerts_response.json()
                    self.alerts = [Alert(**alert) for alert in alerts_data.get("alerts", [])]
                    self.alerts_unread_count = len([a for a in self.alerts if not a.acknowledged])

                # Load metrics
                metrics_response = await client.get(f"{self.api_base_url}/api/analytics/dashboard")
                if metrics_response.status_code == 200:
                    metrics_data = metrics_response.json()
                    self.metrics = DashboardMetrics(**metrics_data)

                # Load customers
                customers_response = await client.get(f"{self.api_base_url}/api/customers")
                if customers_response.status_code == 200:
                    customers_data = customers_response.json()
                    self.customers = [Customer(**customer) for customer in customers_data.get("customers", [])]

                # Load projects
                projects_response = await client.get(f"{self.api_base_url}/api/projects")
                if projects_response.status_code == 200:
                    projects_data = projects_response.json()
                    self.projects = [Project(**project) for project in projects_data.get("projects", [])]

                # Load appointments
                appointments_response = await client.get(f"{self.api_base_url}/api/appointments")
                if appointments_response.status_code == 200:
                    appointments_data = appointments_response.json()
                    self.appointments = [Appointment(**appointment) for appointment in appointments_data.get("appointments", [])]

                # Load team members
                await self.load_team_members()

                self.last_update = datetime.now().strftime("%H:%M:%S")

        except Exception as e:
            self.error_message = f"Failed to load dashboard data: {str(e)}"
        finally:
            self.loading = False

    async def load_team_members(self):
        """Load team members for assignment dropdown."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_base_url}/api/team")
                if response.status_code == 200:
                    team_data = response.json()
                    self.team_members = team_data.get("team_members", [])
        except Exception as e:
            # Fallback to hardcoded team members if API fails
            self.team_members = [
                {"id": "1", "name": "John Doe", "role": "Sales Representative"},
                {"id": "2", "name": "Jane Smith", "role": "Sales Manager"},
                {"id": "3", "name": "Mike Johnson", "role": "Lead Specialist"}
            ]

    def filter_leads(self) -> List[Lead]:
        """Filter leads based on current filters and search query."""
        from datetime import datetime
        filtered = self.leads

        # Apply status filter
        if self.lead_status_filter != "all":
            filtered = [lead for lead in filtered if lead.status == self.lead_status_filter]

        # Apply temperature filter
        if self.lead_temperature_filter != "all":
            filtered = [lead for lead in filtered if lead.temperature == self.lead_temperature_filter]

        # Apply search query
        if self.search_query:
            query = self.search_query.lower()
            filtered = [
                lead for lead in filtered
                if query in lead.first_name.lower()
                or query in lead.last_name.lower()
                or query in lead.phone
                or (lead.email and query in lead.email.lower())
            ]

        # Apply date range filter
        if self.date_range_start and self.date_range_start.strip():
            try:
                start_date = datetime.strptime(self.date_range_start, "%Y-%m-%d").date()
                filtered = [
                    lead for lead in filtered
                    if datetime.fromisoformat(lead.created_at.replace('Z', '+00:00')).date() >= start_date
                ]
            except (ValueError, AttributeError):
                pass

        if self.date_range_end and self.date_range_end.strip():
            try:
                end_date = datetime.strptime(self.date_range_end, "%Y-%m-%d").date()
                filtered = [
                    lead for lead in filtered
                    if datetime.fromisoformat(lead.created_at.replace('Z', '+00:00')).date() <= end_date
                ]
            except (ValueError, AttributeError):
                pass

        # Apply source filter
        if self.source_filter:
            filtered = [lead for lead in filtered if lead.source in self.source_filter]

        # Apply assigned user filter
        if self.assigned_user_filter != "all":
            filtered = [lead for lead in filtered if lead.assigned_to == self.assigned_user_filter]

        # Apply score range filter
        filtered = [
            lead for lead in filtered
            if self.score_range_min <= lead.lead_score <= self.score_range_max
        ]

        return filtered

    def get_urgent_alerts(self) -> List[Alert]:
        """Get high-priority unacknowledged alerts."""
        return [
            alert for alert in self.alerts
            if not alert.acknowledged and alert.priority in ["high", "critical"]
        ]

    def set_lead_status_filter(self, status: str):
        """Set the lead status filter."""
        self.lead_status_filter = status

    def set_lead_temperature_filter(self, temperature: str):
        """Set the lead temperature filter."""
        self.lead_temperature_filter = temperature

    def set_search_query(self, query: str):
        """Set the search query."""
        self.search_query = query

    # Advanced filtering methods
    def set_date_range_start(self, date: str):
        """Set the start date for filtering."""
        self.date_range_start = date

    def set_date_range_end(self, date: str):
        """Set the end date for filtering."""
        self.date_range_end = date


    def toggle_source_filter(self, source: str):
        """Toggle a source in the filter list."""
        if source in self.source_filter:
            self.source_filter.remove(source)
        else:
            self.source_filter.append(source)

    def set_assigned_user_filter(self, user: str):
        """Set the assigned user filter."""
        self.assigned_user_filter = user


    def set_score_range_min(self, value: int):
        """Set minimum score range."""
        self.score_range_min = value

    def set_score_range_max(self, value: int):
        """Set maximum score range."""
        self.score_range_max = value

    def set_score_range_min_str(self, value: str):
        """Set minimum score range from string."""
        try:
            self.score_range_min = int(value) if value else 0
        except (ValueError, TypeError):
            self.score_range_min = 0

    def set_score_range_max_str(self, value: str):
        """Set maximum score range from string."""
        try:
            self.score_range_max = int(value) if value else 100
        except (ValueError, TypeError):
            self.score_range_max = 100

    def set_date_range_preset(self, preset: str):
        """Set date range based on preset."""
        from datetime import datetime, timedelta

        today = datetime.now().date()

        if preset == "today":
            self.date_range_start = today.isoformat()
            self.date_range_end = today.isoformat()
        elif preset == "this_week":
            # Monday of this week
            start_of_week = today - timedelta(days=today.weekday())
            self.date_range_start = start_of_week.isoformat()
            self.date_range_end = today.isoformat()
        elif preset == "this_month":
            # First day of this month
            start_of_month = today.replace(day=1)
            self.date_range_start = start_of_month.isoformat()
            self.date_range_end = today.isoformat()
        elif preset == "last_30_days":
            # 30 days ago
            thirty_days_ago = today - timedelta(days=30)
            self.date_range_start = thirty_days_ago.isoformat()
            self.date_range_end = today.isoformat()
        elif preset == "clear":
            self.date_range_start = ""
            self.date_range_end = ""

    def clear_all_filters(self):
        """Clear all applied filters."""
        self.lead_status_filter = "all"
        self.lead_temperature_filter = "all"
        self.search_query = ""
        self.date_range_start = ""
        self.date_range_end = ""
        self.source_filter = []
        self.assigned_user_filter = "all"
        self.score_range_min = 0
        self.score_range_max = 100

    def toggle_advanced_filters(self):
        """Toggle the advanced filters panel visibility."""
        self.advanced_filters_open = not self.advanced_filters_open

    def select_lead(self, lead_id: str):
        """Select a lead for detailed view."""
        self.selected_lead_id = lead_id

    async def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.api_base_url}/api/alerts/{alert_id}/acknowledge"
                )
                if response.status_code == 200:
                    # Update local state
                    for alert in self.alerts:
                        if alert.id == alert_id:
                            alert.acknowledged = True
                            break
                    self.alerts_unread_count = len([a for a in self.alerts if not a.acknowledged])
        except Exception as e:
            self.error_message = f"Failed to acknowledge alert: {str(e)}"

    async def refresh_data(self):
        """Refresh dashboard data."""
        await self.load_dashboard_data()

    def get_lead_by_id(self, lead_id: str) -> Optional[Lead]:
        """Get a lead by ID."""
        for lead in self.leads:
            if lead.id == lead_id:
                return lead
        return None

    def get_leads_by_status(self, status: str) -> List[Lead]:
        """Get leads by status."""
        return [lead for lead in self.leads if lead.status == status]

    def get_hot_leads(self) -> List[Lead]:
        """Get hot leads (temperature = hot or score >= 80)."""
        return [
            lead for lead in self.leads
            if lead.temperature == "hot" or lead.lead_score >= 80
        ]

    def get_overdue_follow_ups(self) -> List[Lead]:
        """Get leads with overdue follow-ups."""
        now = datetime.now()
        overdue = []

        for lead in self.leads:
            if lead.next_follow_up_date:
                try:
                    follow_up_date = datetime.fromisoformat(lead.next_follow_up_date.replace('Z', '+00:00'))
                    if follow_up_date < now:
                        overdue.append(lead)
                except ValueError:
                    continue

        return overdue

    # Sorting and filtering methods
    def set_sort_field(self, field: str):
        """Set the sort field and toggle direction if same field."""
        if self.sort_field == field:
            self.sort_direction = "asc" if self.sort_direction == "desc" else "desc"
        else:
            self.sort_field = field
            self.sort_direction = "asc"

    def toggle_lead_selection(self, lead_id: str):
        """Toggle a lead's selection state."""
        if lead_id in self.selected_lead_ids:
            self.selected_lead_ids.remove(lead_id)
        else:
            self.selected_lead_ids.append(lead_id)

    def toggle_select_all_leads(self):
        """Toggle select all leads."""
        self.select_all_leads = not self.select_all_leads
        if self.select_all_leads:
            # Select all filtered leads
            filtered_leads = self.filter_leads()
            self.selected_lead_ids = [lead.id for lead in filtered_leads]
        else:
            self.selected_lead_ids = []

    def clear_selection(self):
        """Clear all selected leads."""
        self.selected_lead_ids = []
        self.select_all_leads = False

    def set_page_size(self, size: int):
        """Set the number of leads per page."""
        self.page_size = size
        self.current_page = 1  # Reset to first page

    def set_page_size_str(self, size: str):
        """Set the number of leads per page from string."""
        try:
            self.page_size = int(size) if size else 25
            self.current_page = 1  # Reset to first page
        except (ValueError, TypeError):
            self.page_size = 25
            self.current_page = 1

    def set_current_page(self, page: int):
        """Set the current page."""
        self.current_page = page

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def filtered_sorted_leads(self) -> List[Lead]:
        """Get filtered and sorted leads with caching for performance."""
        # Start with filtered leads
        filtered = self.filter_leads()

        # Apply sorting
        if self.sort_field == "name":
            filtered = sorted(filtered, key=lambda x: f"{x.first_name} {x.last_name}",
                            reverse=(self.sort_direction == "desc"))
        elif self.sort_field == "created_at":
            filtered = sorted(filtered, key=lambda x: x.created_at,
                            reverse=(self.sort_direction == "desc"))
        elif self.sort_field == "lead_score":
            filtered = sorted(filtered, key=lambda x: x.lead_score,
                            reverse=(self.sort_direction == "desc"))
        elif self.sort_field == "status":
            filtered = sorted(filtered, key=lambda x: x.status,
                            reverse=(self.sort_direction == "desc"))

        return filtered

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def paginated_leads(self) -> List[Lead]:
        """Get the current page of leads."""
        filtered_sorted = self.filtered_sorted_leads
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        return filtered_sorted[start_idx:end_idx]

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        total_leads = len(self.filtered_sorted_leads)
        return max(1, (total_leads + self.page_size - 1) // self.page_size)

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def pagination_info(self) -> str:
        """Get pagination info string."""
        filtered_sorted = self.filtered_sorted_leads
        total_leads = len(filtered_sorted)
        start_idx = (self.current_page - 1) * self.page_size + 1
        end_idx = min(self.current_page * self.page_size, total_leads)
        return f"Showing {start_idx}-{end_idx} of {total_leads} leads"

    async def bulk_update_lead_status(self, new_status: str):
        """Update status for all selected leads."""
        if not self.selected_lead_ids:
            self.error_message = "No leads selected"
            return

        updates = [{"id": lead_id, "status": new_status} for lead_id in self.selected_lead_ids]
        await self.bulk_update_leads(updates)
        self.clear_selection()

    async def bulk_delete_leads(self):
        """Delete all selected leads."""
        if not self.selected_lead_ids:
            self.error_message = "No leads selected"
            return

        self.bulk_operation_in_progress = True
        try:
            async with httpx.AsyncClient() as client:
                for lead_id in self.selected_lead_ids:
                    response = await client.delete(f"{self.api_base_url}/api/leads/{lead_id}")
                    if response.status_code != 200:
                        self.error_message = f"Failed to delete lead {lead_id}"
                        return

                # Remove from local state
                self.leads = [lead for lead in self.leads if lead.id not in self.selected_lead_ids]
                count = len(self.selected_lead_ids)
                self.clear_selection()
                self.last_update = datetime.now().strftime("%H:%M:%S")
                self.bulk_operation_success_message = f"Successfully deleted {count} leads"
                self.error_message = ""

        except Exception as e:
            self.error_message = f"Failed to delete leads: {str(e)}"
        finally:
            self.bulk_operation_in_progress = False

    async def bulk_export_leads(self, format: str = "csv"):
        """Export selected leads to CSV or Excel format."""
        if not self.selected_lead_ids:
            self.error_message = "No leads selected for export"
            return

        self.bulk_operation_in_progress = True
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/api/leads/bulk-export",
                    json={
                        "lead_ids": self.selected_lead_ids,
                        "format": format
                    }
                )

                if response.status_code == 200:
                    # The response should contain the file data or download URL
                    count = len(self.selected_lead_ids)
                    self.bulk_operation_success_message = f"Successfully exported {count} leads to {format.upper()}"
                    self.error_message = ""
                    # In a real implementation, this would trigger a file download
                    # For now, we'll just show success message
                else:
                    self.error_message = f"Failed to export leads: {response.status_code}"

        except Exception as e:
            self.error_message = f"Failed to export leads: {str(e)}"
        finally:
            self.bulk_operation_in_progress = False

    async def bulk_assign_leads(self, team_member: str):
        """Assign selected leads to a team member."""
        if not self.selected_lead_ids:
            self.error_message = "No leads selected for assignment"
            return

        if not team_member or team_member == "":
            self.error_message = "Please select a team member"
            return

        self.bulk_operation_in_progress = True
        try:
            updates = [{"id": lead_id, "assigned_to": team_member} for lead_id in self.selected_lead_ids]
            await self.bulk_update_leads(updates)

            count = len(self.selected_lead_ids)
            self.bulk_operation_success_message = f"Successfully assigned {count} leads to {team_member}"
            self.clear_selection()
            self.error_message = ""

        except Exception as e:
            self.error_message = f"Failed to assign leads: {str(e)}"
        finally:
            self.bulk_operation_in_progress = False

    def open_bulk_confirm_dialog(self, action: str, message: str):
        """Open confirmation dialog for bulk operations."""
        self.bulk_confirm_action = action
        self.bulk_confirm_message = message
        self.bulk_confirm_dialog_open = True

    def close_bulk_confirm_dialog(self):
        """Close confirmation dialog."""
        self.bulk_confirm_dialog_open = False
        self.bulk_confirm_action = ""
        self.bulk_confirm_message = ""

    async def confirm_bulk_action(self):
        """Execute the confirmed bulk action."""
        action = self.bulk_confirm_action
        self.close_bulk_confirm_dialog()

        if action == "delete":
            await self.bulk_delete_leads()
        elif action.startswith("assign_"):
            team_member = action.replace("assign_", "")
            await self.bulk_assign_leads(team_member)
        elif action.startswith("status_"):
            status = action.replace("status_", "")
            await self.bulk_update_lead_status(status)

    def clear_bulk_messages(self):
        """Clear bulk operation messages."""
        self.bulk_operation_success_message = ""
        self.error_message = ""

    # Modal state management
    def open_lead_detail_modal(self, lead_id: str):
        """Open lead detail modal for specific lead."""
        self.selected_lead_id = lead_id
        self.selected_lead_detail = self.get_lead_by_id(lead_id)
        self.selected_lead_modal_open = True

    def close_lead_detail_modal(self):
        """Close lead detail modal."""
        self.selected_lead_modal_open = False
        self.selected_lead_id = None
        self.selected_lead_detail = None

    def set_lead_detail_tab(self, tab: str):
        """Set the active tab in the lead detail modal."""
        self.lead_detail_active_tab = tab

    def open_lead_form_modal(self):
        """Open new lead form modal."""
        self.lead_form_modal_open = True
        self.new_lead_form_data = {}
        self.form_validation_errors = {}

    def close_lead_form_modal(self):
        """Close new lead form modal."""
        self.lead_form_modal_open = False
        self.new_lead_form_data = {}
        self.form_validation_errors = {}

    # New Lead Wizard management
    async def open_new_lead_wizard(self):
        """Open the new lead creation wizard."""
        self.new_lead_wizard_open = True
        self.new_lead_wizard_step = 1
        self.new_lead_form_data = {}
        self.new_lead_step_valid = [False, False, False, False]
        self.lead_creation_success = False
        self.lead_creation_message = ""

        # Load team members if not already loaded
        if not self.team_members:
            await self.load_team_members()

    def close_new_lead_wizard(self):
        """Close the new lead creation wizard."""
        self.new_lead_wizard_open = False
        self.new_lead_wizard_step = 1
        self.new_lead_form_data = {}
        self.new_lead_step_valid = [False, False, False, False]

    def next_wizard_step(self):
        """Move to the next step in the wizard."""
        if self.new_lead_wizard_step < 4 and self.new_lead_step_valid[self.new_lead_wizard_step - 1]:
            self.new_lead_wizard_step += 1

    def prev_wizard_step(self):
        """Move to the previous step in the wizard."""
        if self.new_lead_wizard_step > 1:
            self.new_lead_wizard_step -= 1

    def go_to_wizard_step(self, step: int):
        """Go directly to a specific wizard step."""
        if 1 <= step <= 4:
            self.new_lead_wizard_step = step

    def update_wizard_form_data(self, field: str, value: Any):
        """Update form data for the wizard."""
        self.new_lead_form_data[field] = value
        self.validate_current_step()

    def validate_current_step(self):
        """Validate the current step and update step validity."""
        step = self.new_lead_wizard_step

        if step == 1:  # Contact Information
            required_fields = ["first_name", "last_name", "phone"]
            self.new_lead_step_valid[0] = all(
                field in self.new_lead_form_data and
                self.new_lead_form_data[field].strip()
                for field in required_fields
            )
        elif step == 2:  # Lead Details
            required_fields = ["address", "property_type"]
            self.new_lead_step_valid[1] = all(
                field in self.new_lead_form_data and
                self.new_lead_form_data[field].strip()
                for field in required_fields
            )
        elif step == 3:  # Source & Assignment
            required_fields = ["source", "temperature"]
            self.new_lead_step_valid[2] = all(
                field in self.new_lead_form_data and
                self.new_lead_form_data[field].strip()
                for field in required_fields
            )
        elif step == 4:  # Review & Submit
            # All previous steps must be valid
            self.new_lead_step_valid[3] = all(self.new_lead_step_valid[:3])

    async def submit_new_lead(self):
        """Submit the new lead to the backend."""
        if not all(self.new_lead_step_valid):
            self.error_message = "Please complete all required fields before submitting."
            self.lead_creation_success = False
            return

        self.loading = True
        try:
            # Create the lead payload
            lead_data = {
                "first_name": self.new_lead_form_data.get("first_name", ""),
                "last_name": self.new_lead_form_data.get("last_name", ""),
                "phone": self.new_lead_form_data.get("phone", ""),
                "email": self.new_lead_form_data.get("email", ""),
                "address": self.new_lead_form_data.get("address", ""),
                "property_type": self.new_lead_form_data.get("property_type", ""),
                "project_description": self.new_lead_form_data.get("project_description", ""),
                "source": self.new_lead_form_data.get("source", ""),
                "temperature": self.new_lead_form_data.get("temperature", ""),
                "status": "new"
            }

            # Only include assigned_to if a specific team member was selected
            assigned_to = self.new_lead_form_data.get("assigned_to", "")
            if assigned_to and assigned_to != "Auto-assign":
                lead_data["assigned_to"] = assigned_to

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/api/leads",
                    json=lead_data
                )

                if response.status_code == 201:
                    lead_response_data = response.json()

                    # Handle auto-assignment if requested
                    if assigned_to == "Auto-assign":
                        try:
                            auto_assign_response = await client.post(
                                f"{self.api_base_url}/api/team/auto-assign",
                                json={"lead_id": lead_response_data.get("id")}
                            )
                            if auto_assign_response.status_code == 200:
                                assign_data = auto_assign_response.json()
                                assigned_member = assign_data.get("assigned_to", "Unknown")
                                self.lead_creation_message = f"Lead created successfully and auto-assigned to {assigned_member}!"
                            else:
                                self.lead_creation_message = "Lead created successfully but auto-assignment failed."
                        except Exception:
                            self.lead_creation_message = "Lead created successfully but auto-assignment failed."
                    else:
                        full_name = f"{lead_data['first_name']} {lead_data['last_name']}"
                        self.lead_creation_message = f"Lead '{full_name}' created successfully with score: {lead_response_data.get('lead_score', 'N/A')}"

                    self.lead_creation_success = True
                    self.error_message = ""

                    # Close wizard after a brief delay to show success message
                    await asyncio.sleep(1.5)
                    self.close_new_lead_wizard()
                    await self.load_dashboard_data()

                else:
                    self.error_message = f"Failed to create lead: {response.text}"
                    self.lead_creation_success = False

        except Exception as e:
            self.error_message = f"Error creating lead: {str(e)}"
            self.lead_creation_success = False
        finally:
            self.loading = False

    # Customer management methods
    async def load_customer_details(self, customer_id: str):
        """Load detailed customer information including projects and interactions."""
        try:
            async with httpx.AsyncClient() as client:
                # Load customer details
                customer_response = await client.get(f"{self.api_base_url}/api/customers/{customer_id}")
                if customer_response.status_code == 200:
                    customer_data = customer_response.json()
                    self.selected_customer_detail = Customer(**customer_data)

                # Load customer projects
                projects_response = await client.get(f"{self.api_base_url}/api/customers/{customer_id}/projects")
                if projects_response.status_code == 200:
                    projects_data = projects_response.json()
                    self.customer_projects = [Project(**project) for project in projects_data.get("projects", [])]

                # Load customer interactions
                interactions_response = await client.get(f"{self.api_base_url}/api/customers/{customer_id}/interactions")
                if interactions_response.status_code == 200:
                    interactions_data = interactions_response.json()
                    self.customer_interactions = [Interaction(**interaction) for interaction in interactions_data.get("interactions", [])]

        except Exception as e:
            self.error_message = f"Failed to load customer details: {str(e)}"

    def open_customer_detail_modal(self, customer_id: str):
        """Open customer detail modal and load data."""
        self.selected_customer_id = customer_id
        self.customer_detail_modal_open = True
        self.customer_detail_active_tab = "overview"

    def close_customer_detail_modal(self):
        """Close customer detail modal."""
        self.customer_detail_modal_open = False
        self.selected_customer_id = None
        self.selected_customer_detail = None
        self.customer_projects = []
        self.customer_interactions = []

    def set_customer_detail_tab(self, tab: str):
        """Set active tab in customer detail modal."""
        self.customer_detail_active_tab = tab

    def filter_customers(self) -> List[Customer]:
        """Filter customers based on search and status filters."""
        filtered = self.customers

        # Apply status filter
        if self.customer_status_filter != "all":
            filtered = [customer for customer in filtered if customer.customer_status == self.customer_status_filter]

        # Apply search query
        if self.customer_search_query:
            query = self.customer_search_query.lower()
            filtered = [
                customer for customer in filtered
                if query in customer.first_name.lower()
                or query in customer.last_name.lower()
                or query in customer.phone
                or (customer.email and query in customer.email.lower())
                or query in customer.address.lower()
            ]

        return filtered

    def set_customer_status_filter(self, status: str):
        """Set customer status filter."""
        self.customer_status_filter = status

    def set_customer_search_query(self, query: str):
        """Set customer search query."""
        self.customer_search_query = query

    async def request_customer_review(self, customer_id: str):
        """Send review request to customer."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.api_base_url}/api/customers/{customer_id}/request-review")
                if response.status_code == 200:
                    self.bulk_operation_success_message = "Review request sent successfully"
                    self.error_message = ""
                else:
                    self.error_message = "Failed to send review request"
        except Exception as e:
            self.error_message = f"Failed to send review request: {str(e)}"

    def open_customer_form_modal(self):
        """Open customer form modal for new customer."""
        self.customer_form_modal_open = True
        self.customer_form_editing = False
        self.customer_form_data = {}

    def close_customer_form_modal(self):
        """Close customer form modal."""
        self.customer_form_modal_open = False
        self.customer_form_data = {}
        self.customer_form_editing = False

    def update_customer_form_data(self, field: str, value: Any):
        """Update customer form data."""
        self.customer_form_data[field] = value

    async def submit_customer_form(self):
        """Submit customer form (create or update)."""
        if not self.customer_form_data.get("first_name") or not self.customer_form_data.get("last_name"):
            self.error_message = "First name and last name are required"
            return

        if not self.customer_form_data.get("phone"):
            self.error_message = "Phone number is required"
            return

        if not self.customer_form_data.get("address"):
            self.error_message = "Address is required"
            return

        self.loading = True
        try:
            async with httpx.AsyncClient() as client:
                if self.customer_form_editing:
                    # Update existing customer
                    response = await client.put(
                        f"{self.api_base_url}/api/customers/{self.selected_customer_id}",
                        json=self.customer_form_data
                    )
                else:
                    # Create new customer
                    response = await client.post(
                        f"{self.api_base_url}/api/customers",
                        json=self.customer_form_data
                    )

                if response.status_code in [200, 201]:
                    self.close_customer_form_modal()
                    await self.load_dashboard_data()
                    self.bulk_operation_success_message = "Customer saved successfully"
                    self.error_message = ""
                else:
                    self.error_message = f"Failed to save customer: {response.text}"

        except Exception as e:
            self.error_message = f"Error saving customer: {str(e)}"
        finally:
            self.loading = False

    # Form handling methods
    def update_form_field(self, field: str, value: str):
        """Update form field value."""
        self.new_lead_form_data[field] = value
        # Clear validation error when field is updated
        if field in self.form_validation_errors:
            del self.form_validation_errors[field]

    def validate_lead_form(self) -> bool:
        """Validate the new lead form data."""
        errors = {}

        # Required field validation
        if not self.new_lead_form_data.get("first_name", "").strip():
            errors["first_name"] = "First name is required"

        if not self.new_lead_form_data.get("last_name", "").strip():
            errors["last_name"] = "Last name is required"

        if not self.new_lead_form_data.get("phone", "").strip():
            errors["phone"] = "Phone number is required"

        if not self.new_lead_form_data.get("source", "").strip():
            errors["source"] = "Lead source is required"

        # Email validation (if provided)
        email = self.new_lead_form_data.get("email", "").strip()
        if email and "@" not in email:
            errors["email"] = "Invalid email format"

        self.form_validation_errors = errors
        return len(errors) == 0


    # Helper methods
    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def available_sources(self) -> List[str]:
        """Get unique sources from current leads for filter options."""
        sources = set()
        for lead in self.leads:
            if lead.source:
                sources.add(lead.source)
        return sorted(list(sources))

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def team_member_options(self) -> List[str]:
        """Get team member names for assignment dropdown."""
        options = ["Auto-assign", "Unassigned"]
        for member in self.team_members:
            if member.get("name"):
                options.append(member["name"])
        return options

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def available_users(self) -> List[str]:
        """Get unique assigned users for filter options."""
        users = set()
        for lead in self.leads:
            if lead.assigned_to:
                users.add(lead.assigned_to)
        return sorted(list(users))

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def available_users_with_all(self) -> List[str]:
        """Get available users with 'all' option."""
        return ["all"] + self.available_users

    # Kanban lead filtering by status
    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def new_leads(self) -> List[Lead]:
        """Get leads with 'new' status."""
        return [lead for lead in self.leads if lead.status == "new"]

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def contacted_leads(self) -> List[Lead]:
        """Get leads with 'contacted' status."""
        return [lead for lead in self.leads if lead.status == "contacted"]

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def qualified_leads(self) -> List[Lead]:
        """Get leads with 'qualified' status."""
        return [lead for lead in self.leads if lead.status == "qualified"]

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def appointment_scheduled_leads(self) -> List[Lead]:
        """Get leads with 'appointment_scheduled' status."""
        return [lead for lead in self.leads if lead.status == "appointment_scheduled"]

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def inspection_completed_leads(self) -> List[Lead]:
        """Get leads with 'inspection_completed' status."""
        return [lead for lead in self.leads if lead.status == "inspection_completed"]

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def quote_sent_leads(self) -> List[Lead]:
        """Get leads with 'quote_sent' status."""
        return [lead for lead in self.leads if lead.status == "quote_sent"]

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def negotiation_leads(self) -> List[Lead]:
        """Get leads with 'negotiation' status."""
        return [lead for lead in self.leads if lead.status == "negotiation"]

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def won_leads(self) -> List[Lead]:
        """Get leads with 'won' status."""
        return [lead for lead in self.leads if lead.status == "won"]

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def lost_leads(self) -> List[Lead]:
        """Get leads with 'lost' status."""
        return [lead for lead in self.leads if lead.status == "lost"]

    # Kanban-specific methods
    async def update_lead_status(self, lead_id: str, new_status: str):
        """Update a lead's status from Kanban board drag and drop."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.api_base_url}/api/leads/{lead_id}",
                    json={"status": new_status}
                )
                if response.status_code == 200:
                    # Update local state optimistically
                    for lead in self.leads:
                        if lead.id == lead_id:
                            lead.status = new_status
                            break
                    self.last_update = datetime.now().strftime("%H:%M:%S")
                else:
                    self.error_message = f"Failed to update lead status: {response.status_code}"
        except Exception as e:
            self.error_message = f"Failed to update lead status: {str(e)}"

    def get_leads_by_status(self, status: str) -> List[Lead]:
        """Get leads filtered by status for Kanban columns."""
        return [lead for lead in self.leads if lead.status == status]

    def get_kanban_stats(self) -> Dict[str, int]:
        """Get statistics for Kanban board columns."""
        stats = {}
        statuses = ["new", "contacted", "qualified", "appointment_scheduled",
                   "inspection_completed", "quote_sent", "negotiation", "won", "lost", "nurture"]

        for status in statuses:
            stats[status] = len([lead for lead in self.leads if lead.status == status])

        return stats

    async def bulk_update_leads(self, lead_updates: List[Dict[str, str]]):
        """Bulk update multiple leads (useful for batch operations)."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.api_base_url}/api/leads/bulk-update",
                    json={"updates": lead_updates}
                )
                if response.status_code == 200:
                    # Refresh leads data after bulk update
                    await self.load_dashboard_data()
                else:
                    self.error_message = f"Failed to bulk update leads: {response.status_code}"
        except Exception as e:
            self.error_message = f"Failed to bulk update leads: {str(e)}"

    def get_lead_transition_history(self, lead_id: str) -> List[Dict]:
        """Get status transition history for a lead (for audit trail)."""
        # This would typically come from the backend
        # For now, return a placeholder
        return []

    async def create_new_lead(self, lead_data: Dict):
        """Create a new lead from Kanban board."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/api/leads",
                    json=lead_data
                )
                if response.status_code == 201:
                    new_lead_data = response.json()
                    new_lead = Lead(**new_lead_data)
                    self.leads.append(new_lead)
                    self.last_update = datetime.now().strftime("%H:%M:%S")
                    return new_lead
                else:
                    self.error_message = f"Failed to create lead: {response.status_code}"
                    return None
        except Exception as e:
            self.error_message = f"Failed to create lead: {str(e)}"
            return None

    async def handle_lead_drop(self, target_status: str, item: dict):
        """Handle lead drop from rxe.dnd.drop_target."""
        if item and "id" in item and target_status:
            lead_id = item["id"]
            current_status = item.get("status")

            # Only update if status actually changed
            if current_status != target_status:
                await self.update_lead_status(lead_id, target_status)

    # @rx.event - Removed to eliminate WebSocket dependencies
    async def handle_lead_status_change(self, lead_id: str, new_status: str):
        """Handle lead status change from drag and drop events."""
        await self.update_lead_status(lead_id, new_status)

    def create_lead_status_update_handler(self):
        """Create a JavaScript-callable handler for lead status updates."""
        return rx.script("""
            // Create global function to handle lead status updates from drag and drop
            window.updateLeadStatus = function(leadId, newStatus) {
                // Trigger Reflex state update
                console.log('Calling Reflex to update lead:', leadId, 'to status:', newStatus);

                // Call the Reflex event handler
                if (window.processEvent) {
                    window.processEvent('handle_lead_status_change', {
                        'lead_id': leadId,
                        'new_status': newStatus
                    });
                } else {
                    // Fallback to page refresh if event handler not available
                    window.location.reload();
                }
            };
        """)

    # ================ PROJECT MANAGEMENT METHODS ================

    async def load_projects(self):
        """Load projects from backend API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_base_url}/api/projects")
                if response.status_code == 200:
                    projects_data = response.json()
                    self.projects = [Project(**project) for project in projects_data.get("projects", [])]
                    self.last_update = datetime.now().strftime("%H:%M:%S")
                else:
                    self.error_message = f"Failed to load projects: {response.status_code}"
        except Exception as e:
            self.error_message = f"Failed to load projects: {str(e)}"

    async def update_project_status(self, project_id: str, new_status: str):
        """Update a project's status from Kanban board drag and drop."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.api_base_url}/api/projects/{project_id}",
                    json={"status": new_status}
                )
                if response.status_code == 200:
                    # Update local state optimistically
                    for project in self.projects:
                        if project.id == project_id:
                            project.status = new_status
                            break
                    self.last_update = datetime.now().strftime("%H:%M:%S")
                else:
                    self.error_message = f"Failed to update project status: {response.status_code}"
        except Exception as e:
            self.error_message = f"Failed to update project status: {str(e)}"

    async def create_new_project(self, project_data: Dict):
        """Create a new project from Kanban board."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/api/projects",
                    json=project_data
                )
                if response.status_code == 201:
                    new_project_data = response.json()
                    new_project = Project(**new_project_data)
                    self.projects.append(new_project)
                    self.last_update = datetime.now().strftime("%H:%M:%S")
                    return new_project
                else:
                    self.error_message = f"Failed to create project: {response.status_code}"
                    return None
        except Exception as e:
            self.error_message = f"Failed to create project: {str(e)}"
            return None

    async def handle_project_drop(self, target_status: str, item: dict):
        """Handle project drop from rxe.dnd.drop_target."""
        if item and "id" in item and target_status:
            project_id = item["id"]
            current_status = item.get("status")

            # Only update if status actually changed
            if current_status != target_status:
                await self.update_project_status(project_id, target_status)

    def filter_projects(self) -> List[Project]:
        """Filter projects based on current filters and search query."""
        filtered = self.projects

        # Apply status filter
        if self.project_status_filter != "all":
            filtered = [project for project in filtered if project.status == self.project_status_filter]

        # Apply search query
        if self.project_search_query:
            query = self.project_search_query.lower()
            filtered = [
                project for project in filtered
                if query in project.title.lower()
                or query in project.description.lower()
                or query in project.project_type.lower()
                or query in project.customer_id.lower()
            ]

        return filtered

    def set_project_status_filter(self, status: str):
        """Set the project status filter."""
        self.project_status_filter = status

    def set_project_search_query(self, query: str):
        """Set the project search query."""
        self.project_search_query = query

    def get_project_by_id(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        for project in self.projects:
            if project.id == project_id:
                return project
        return None

    def get_projects_by_status(self, status: str) -> List[Project]:
        """Get projects by status."""
        return [project for project in self.projects if project.status == status]

    def get_project_kanban_stats(self) -> Dict[str, int]:
        """Get statistics for Project Kanban board columns."""
        stats = {}
        statuses = ["planning", "approved", "in_progress", "installation", "inspection", "completed", "cancelled"]

        for status in statuses:
            stats[status] = len([project for project in self.projects if project.status == status])

        return stats

    # Project computed properties for filtering by status (similar to lead management)
    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def planning_projects(self) -> List[Project]:
        """Get projects with 'planning' status."""
        return [project for project in self.projects if project.status == "planning"]

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def approved_projects(self) -> List[Project]:
        """Get projects with 'approved' status."""
        return [project for project in self.projects if project.status == "approved"]

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def in_progress_projects(self) -> List[Project]:
        """Get projects with 'in_progress' status."""
        return [project for project in self.projects if project.status == "in_progress"]

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def installation_projects(self) -> List[Project]:
        """Get projects with 'installation' status."""
        return [project for project in self.projects if project.status == "installation"]

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def inspection_projects(self) -> List[Project]:
        """Get projects with 'inspection' status."""
        return [project for project in self.projects if project.status == "inspection"]

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def completed_projects(self) -> List[Project]:
        """Get projects with 'completed' status."""
        return [project for project in self.projects if project.status == "completed"]

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def cancelled_projects(self) -> List[Project]:
        """Get projects with 'cancelled' status."""
        return [project for project in self.projects if project.status == "cancelled"]

    # Project modal management
    def open_project_detail_modal(self, project_id: str):
        """Open project detail modal for specific project."""
        self.selected_project_id = project_id
        self.selected_project_detail = self.get_project_by_id(project_id)
        self.project_detail_modal_open = True

    def close_project_detail_modal(self):
        """Close project detail modal."""
        self.project_detail_modal_open = False
        self.selected_project_id = None
        self.selected_project_detail = None

    # @rx.event - Removed to eliminate WebSocket dependencies
    async def handle_project_status_change(self, project_id: str, new_status: str):
        """Handle project status change from drag and drop events."""
        await self.update_project_status(project_id, new_status)

    # ================ NEW PROJECT MODAL METHODS ================

    async def open_new_project_modal(self):
        """Open the new project creation modal."""
        self.new_project_modal_open = True
        self.new_project_form_data = {"assigned_team_members": []}
        self.project_creation_success = False
        self.project_creation_message = ""
        self.project_form_active_tab = "project_info"
        self.error_message = ""

        # Load team members and customers if not already loaded
        if not self.team_members:
            await self.load_team_members()

    def close_new_project_modal(self):
        """Close the new project creation modal."""
        self.new_project_modal_open = False
        self.new_project_form_data = {}
        self.project_creation_success = False
        self.project_creation_message = ""
        self.project_form_active_tab = "project_info"

    def update_project_form_data(self, field: str, value: Any):
        """Update project form data."""
        self.new_project_form_data[field] = value

    def set_project_form_tab(self, tab: str):
        """Set the active tab in the project form."""
        self.project_form_active_tab = tab

    def toggle_project_team_member(self, member_id: str):
        """Toggle team member assignment for the project."""
        assigned_members = self.new_project_form_data.get("assigned_team_members", [])
        if member_id in assigned_members:
            assigned_members.remove(member_id)
        else:
            assigned_members.append(member_id)
        self.new_project_form_data["assigned_team_members"] = assigned_members

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def customer_options(self) -> List[str]:
        """Get customer options for the dropdown."""
        options = ["new_customer"]  # Option to create new customer
        for customer in self.customers:
            full_name = f"{customer.first_name} {customer.last_name}"
            options.append(f"{customer.id}|{full_name}")
        return options

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def customer_select_options(self) -> List[str]:
        """Get customer select options with better display text."""
        options = ["new_customer"]  # This will be displayed as the key
        for customer in self.customers:
            full_name = f"{customer.first_name} {customer.last_name}"
            # Use ID|Name format for the value, but just name for display in some contexts
            options.append(f"{customer.id}|{full_name}")
        return options

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def selected_customer_name(self) -> str:
        """Get the selected customer's name for display."""
        customer_id = self.new_project_form_data.get("customer_id", "")
        if customer_id and customer_id != "new_customer":
            # Extract the name part from "id|name" format
            if "|" in customer_id:
                return customer_id.split("|", 1)[1]
        return ""

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def assigned_team_members_display(self) -> str:
        """Get formatted display of assigned team members."""
        assigned_ids = self.new_project_form_data.get("assigned_team_members", [])
        if not assigned_ids:
            return ""

        assigned_names = []
        for member in self.team_members:
            if member.get("id", "") in assigned_ids:
                assigned_names.append(member.get("name", "Unknown"))

        return ", ".join(assigned_names)

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def project_form_valid(self) -> bool:
        """Check if the project form is valid for submission."""
        # Required fields
        if not self.new_project_form_data.get("title", "").strip():
            return False

        if not self.new_project_form_data.get("project_type", "").strip():
            return False

        if not self.new_project_form_data.get("customer_id", "").strip():
            return False

        if not self.new_project_form_data.get("estimated_value", "").strip():
            return False

        # If creating new customer, validate customer fields
        if self.new_project_form_data.get("customer_id", "") == "new_customer":
            if not self.new_project_form_data.get("customer_first_name", "").strip():
                return False
            if not self.new_project_form_data.get("customer_last_name", "").strip():
                return False
            if not self.new_project_form_data.get("customer_phone", "").strip():
                return False
            if not self.new_project_form_data.get("customer_address", "").strip():
                return False

        # Validate estimated value is a number
        try:
            float(self.new_project_form_data.get("estimated_value", "0"))
        except (ValueError, TypeError):
            return False

        return True

    async def submit_new_project(self):
        """Submit the new project to the backend."""
        if not self.project_form_valid:
            self.error_message = "Please complete all required fields before submitting."
            self.project_creation_success = False
            return

        self.loading = True
        try:
            # Handle customer creation if needed
            customer_id = self.new_project_form_data.get("customer_id", "")
            actual_customer_id = customer_id

            if customer_id == "new_customer":
                # Create new customer first
                customer_data = {
                    "first_name": self.new_project_form_data.get("customer_first_name", ""),
                    "last_name": self.new_project_form_data.get("customer_last_name", ""),
                    "phone": self.new_project_form_data.get("customer_phone", ""),
                    "email": self.new_project_form_data.get("customer_email", ""),
                    "address": self.new_project_form_data.get("customer_address", ""),
                    "property_type": "Residential"  # Default
                }

                async with httpx.AsyncClient() as client:
                    customer_response = await client.post(
                        f"{self.api_base_url}/api/customers",
                        json=customer_data
                    )

                    if customer_response.status_code == 201:
                        customer_result = customer_response.json()
                        actual_customer_id = customer_result.get("id")
                    else:
                        self.error_message = f"Failed to create customer: {customer_response.text}"
                        self.project_creation_success = False
                        return
            else:
                # Extract actual customer ID from "id|name" format
                if "|" in customer_id:
                    actual_customer_id = customer_id.split("|", 1)[0]

            # Create the project payload
            project_data = {
                "title": self.new_project_form_data.get("title", ""),
                "description": self.new_project_form_data.get("description", ""),
                "project_type": self.new_project_form_data.get("project_type", ""),
                "customer_id": actual_customer_id,
                "estimated_value": float(self.new_project_form_data.get("estimated_value", "0")),
                "status": "planning",  # Default initial status
                "assigned_team_members": self.new_project_form_data.get("assigned_team_members", [])
            }

            # Add optional fields if provided
            if self.new_project_form_data.get("start_date", ""):
                project_data["start_date"] = self.new_project_form_data.get("start_date", "")

            if self.new_project_form_data.get("completion_date", ""):
                project_data["completion_date"] = self.new_project_form_data.get("completion_date", "")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/api/projects",
                    json=project_data
                )

                if response.status_code == 201:
                    project_response_data = response.json()

                    project_title = project_data['title']
                    estimated_value = project_data['estimated_value']
                    self.project_creation_message = f"Project '{project_title}' created successfully with estimated value: ${estimated_value:,.2f}"

                    self.project_creation_success = True
                    self.error_message = ""

                    # Close modal after a brief delay to show success message
                    await asyncio.sleep(1.5)
                    self.close_new_project_modal()
                    await self.load_dashboard_data()

                else:
                    self.error_message = f"Failed to create project: {response.text}"
                    self.project_creation_success = False

        except Exception as e:
            self.error_message = f"Error creating project: {str(e)}"
            self.project_creation_success = False
        finally:
            self.loading = False

    # ================ TIMELINE MANAGEMENT METHODS ================

    def set_timeline_view_mode(self, mode: str):
        """Set the timeline view mode (gantt, calendar, resource)."""
        if mode in ["gantt", "calendar", "resource"]:
            self.timeline_view_mode = mode

    def set_timeline_date_range(self, range_type: str):
        """Set the timeline date range (week, month, quarter)."""
        if range_type in ["week", "month", "quarter"]:
            self.timeline_date_range = range_type

    def toggle_timeline_filter(self, filter_name: str):
        """Toggle timeline filter options."""
        if filter_name == "overdue":
            self.timeline_show_overdue = not self.timeline_show_overdue
        elif filter_name == "this_week":
            self.timeline_show_this_week = not self.timeline_show_this_week
        elif filter_name == "high_priority":
            self.timeline_show_high_priority = not self.timeline_show_high_priority
        elif filter_name == "unassigned":
            self.timeline_show_unassigned = not self.timeline_show_unassigned

    def navigate_timeline(self, direction: str):
        """Navigate timeline forward or backward."""
        from datetime import datetime, timedelta, date

        today = date.today()

        if self.timeline_date_range == "week":
            delta = timedelta(weeks=1)
        elif self.timeline_date_range == "month":
            delta = timedelta(days=30)  # Approximate
        elif self.timeline_date_range == "quarter":
            delta = timedelta(days=90)  # Approximate
        else:
            delta = timedelta(days=7)

        if direction == "forward":
            # Move timeline forward
            pass  # Implementation would update timeline_start_date/end_date
        elif direction == "backward":
            # Move timeline backward
            pass  # Implementation would update timeline_start_date/end_date

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def filtered_timeline_projects(self) -> List[Project]:
        """Get projects filtered for timeline view."""
        from datetime import datetime, date, timedelta

        filtered = self.projects

        # Apply timeline-specific filters
        if self.timeline_show_overdue:
            # Filter for overdue projects
            today = date.today()
            filtered = [
                p for p in filtered
                if p.completion_date and
                datetime.fromisoformat(p.completion_date).date() < today and
                p.status not in ["completed", "cancelled"]
            ]

        if self.timeline_show_this_week:
            # Filter for projects with activity this week
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)

            filtered = [
                p for p in filtered
                if (p.start_date and week_start <= datetime.fromisoformat(p.start_date).date() <= week_end) or
                   (p.completion_date and week_start <= datetime.fromisoformat(p.completion_date).date() <= week_end)
            ]

        if self.timeline_show_high_priority:
            # Filter for high priority projects (assuming we add priority field)
            filtered = [p for p in filtered if hasattr(p, 'priority') and p.priority == 'high']

        if self.timeline_show_unassigned:
            # Filter for unassigned projects
            filtered = [p for p in filtered if not p.assigned_team_members]

        return filtered

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def timeline_stats(self) -> dict:
        """Calculate timeline statistics."""
        from datetime import datetime, date, timedelta

        projects = self.filtered_timeline_projects
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        stats = {
            "total_projects": len(projects),
            "active_projects": len([p for p in projects if p.status in ["approved", "in_progress", "installation"]]),
            "overdue_projects": 0,
            "this_week_projects": 0,
            "total_value": sum(p.estimated_value for p in projects if p.estimated_value)
        }

        # Calculate overdue projects
        for project in projects:
            if (project.completion_date and
                datetime.fromisoformat(project.completion_date).date() < today and
                project.status not in ["completed", "cancelled"]):
                stats["overdue_projects"] += 1

        # Calculate this week projects
        for project in projects:
            if (project.start_date and
                week_start <= datetime.fromisoformat(project.start_date).date() <= week_end) or \
               (project.completion_date and
                week_start <= datetime.fromisoformat(project.completion_date).date() <= week_end):
                stats["this_week_projects"] += 1

        return stats

    def calculate_project_timeline_position(self, project: Project) -> dict:
        """Calculate project position and width for timeline visualization."""
        from datetime import datetime, date, timedelta

        # Get timeline bounds
        today = date.today()

        if self.timeline_date_range == "week":
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif self.timeline_date_range == "month":
            start_date = today.replace(day=1)
            next_month = start_date.replace(month=start_date.month + 1) if start_date.month < 12 else start_date.replace(year=start_date.year + 1, month=1)
            end_date = next_month - timedelta(days=1)
        else:  # quarter
            quarter = (today.month - 1) // 3 + 1
            start_date = today.replace(month=(quarter - 1) * 3 + 1, day=1)
            end_month = quarter * 3
            end_date = start_date.replace(month=end_month)
            next_month = end_date.replace(month=end_date.month + 1) if end_date.month < 12 else end_date.replace(year=end_date.year + 1, month=1)
            end_date = next_month - timedelta(days=1)

        timeline_days = (end_date - start_date).days + 1

        # Project dates
        proj_start = datetime.fromisoformat(project.start_date).date() if project.start_date else start_date
        proj_end = datetime.fromisoformat(project.completion_date).date() if project.completion_date else proj_start + timedelta(days=7)

        # Clamp to timeline bounds
        proj_start = max(proj_start, start_date)
        proj_end = min(proj_end, end_date)

        # Calculate position and width as percentages
        start_offset = (proj_start - start_date).days
        project_duration = (proj_end - proj_start).days + 1

        left_percent = (start_offset / timeline_days) * 100
        width_percent = (project_duration / timeline_days) * 100

        return {
            "left": f"{left_percent:.1f}%",
            "width": f"{width_percent:.1f}%",
            "start_date": proj_start.isoformat(),
            "end_date": proj_end.isoformat(),
            "duration_days": project_duration
        }

    # ================ APPOINTMENT MANAGEMENT METHODS ================

    async def load_appointments(self):
        """Load appointments from backend API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_base_url}/api/appointments")
                if response.status_code == 200:
                    appointments_data = response.json()
                    self.appointments = [Appointment(**appointment) for appointment in appointments_data.get("appointments", [])]
                    self.last_update = datetime.now().strftime("%H:%M:%S")
                else:
                    self.error_message = f"Failed to load appointments: {response.status_code}"
        except Exception as e:
            self.error_message = f"Failed to load appointments: {str(e)}"

    def filter_appointments(self) -> List[Appointment]:
        """Filter appointments based on current filters and search query."""
        filtered = self.appointments

        # Apply type filter
        if self.appointment_type_filter != "all":
            filtered = [appointment for appointment in filtered if appointment.appointment_type == self.appointment_type_filter]

        # Apply status filter
        if self.appointment_status_filter != "all":
            filtered = [appointment for appointment in filtered if appointment.status == self.appointment_status_filter]

        # Apply assigned to filter
        if self.appointment_assigned_to_filter != "all":
            filtered = [appointment for appointment in filtered if appointment.assigned_to == self.appointment_assigned_to_filter]

        # Apply search query
        if self.appointment_search_query:
            query = self.appointment_search_query.lower()
            filtered = [
                appointment for appointment in filtered
                if query in appointment.title.lower()
                or (appointment.description and query in appointment.description.lower())
                or (appointment.location and query in appointment.location.lower())
            ]

        return filtered

    def get_appointments_by_date(self, date: str) -> List[Appointment]:
        """Get appointments for a specific date."""
        from datetime import datetime
        filtered = self.filter_appointments()
        target_date = datetime.fromisoformat(date).date()

        return [
            appointment for appointment in filtered
            if datetime.fromisoformat(appointment.scheduled_date.replace('Z', '+00:00')).date() == target_date
        ]

    def get_appointments_by_status(self, status: str) -> List[Appointment]:
        """Get appointments by status."""
        return [appointment for appointment in self.appointments if appointment.status == status]

    def get_upcoming_appointments(self) -> List[Appointment]:
        """Get upcoming appointments (future and not cancelled)."""
        from datetime import datetime
        now = datetime.now()
        return [
            appointment for appointment in self.appointments
            if datetime.fromisoformat(appointment.scheduled_date.replace('Z', '+00:00')) > now
            and appointment.status not in ["cancelled", "completed"]
        ]

    def get_todays_appointments(self) -> List[Appointment]:
        """Get today's appointments."""
        from datetime import datetime, date
        today = date.today()
        return [
            appointment for appointment in self.appointments
            if datetime.fromisoformat(appointment.scheduled_date.replace('Z', '+00:00')).date() == today
        ]

    def get_overdue_appointments(self) -> List[Appointment]:
        """Get overdue appointments."""
        from datetime import datetime
        now = datetime.now()
        return [
            appointment for appointment in self.appointments
            if datetime.fromisoformat(appointment.scheduled_date.replace('Z', '+00:00')) < now
            and appointment.status not in ["completed", "cancelled", "no_show"]
        ]

    # Calendar view management
    def set_calendar_view_mode(self, mode: str):
        """Set the calendar view mode."""
        if mode in ["month", "week", "day", "list"]:
            self.calendar_view_mode = mode

    def set_calendar_selected_date(self, date: str):
        """Set the selected date in calendar."""
        self.calendar_selected_date = date

    def navigate_calendar(self, direction: str):
        """Navigate calendar forward or backward."""
        from datetime import datetime, timedelta, date

        if not self.calendar_view_date:
            self.calendar_view_date = date.today().isoformat()

        current_date = datetime.fromisoformat(self.calendar_view_date).date()

        if self.calendar_view_mode == "day":
            delta = timedelta(days=1)
        elif self.calendar_view_mode == "week":
            delta = timedelta(weeks=1)
        elif self.calendar_view_mode == "month":
            if direction == "forward":
                if current_date.month == 12:
                    new_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    new_date = current_date.replace(month=current_date.month + 1)
            else:  # backward
                if current_date.month == 1:
                    new_date = current_date.replace(year=current_date.year - 1, month=12)
                else:
                    new_date = current_date.replace(month=current_date.month - 1)
            self.calendar_view_date = new_date.isoformat()
            return
        else:
            delta = timedelta(days=1)

        if direction == "forward":
            new_date = current_date + delta
        else:  # backward
            new_date = current_date - delta

        self.calendar_view_date = new_date.isoformat()

    def go_to_today(self):
        """Navigate calendar to today."""
        from datetime import date
        self.calendar_view_date = date.today().isoformat()
        self.calendar_selected_date = date.today().isoformat()

    # Appointment form management
    def open_appointment_modal(self):
        """Open new appointment creation modal."""
        from datetime import datetime
        self.appointment_modal_open = True
        self.appointment_form_editing = False
        self.appointment_form_data = {
            "scheduled_date": datetime.now().strftime("%Y-%m-%dT%H:%M"),
            "duration_minutes": 60,
            "appointment_type": "initial_consultation",
            "status": "scheduled",
            "is_virtual": False
        }
        self.appointment_creation_success = False
        self.appointment_creation_message = ""

    def open_appointment_modal_with_date(self, date: str, time: str = "09:00"):
        """Open appointment modal with pre-selected date and time."""
        self.appointment_modal_open = True
        self.appointment_form_editing = False
        self.appointment_form_data = {
            "scheduled_date": f"{date}T{time}",
            "duration_minutes": 60,
            "appointment_type": "initial_consultation",
            "status": "scheduled",
            "is_virtual": False
        }
        self.appointment_creation_success = False
        self.appointment_creation_message = ""

    def close_appointment_modal(self):
        """Close appointment creation modal."""
        self.appointment_modal_open = False
        self.appointment_form_data = {}
        self.appointment_form_editing = False

    def open_appointment_detail_modal(self, appointment_id: str):
        """Open appointment detail modal."""
        self.selected_appointment_id = appointment_id
        self.appointment_detail_modal_open = True

    def close_appointment_detail_modal(self):
        """Close appointment detail modal."""
        self.appointment_detail_modal_open = False
        self.selected_appointment_id = None

    def update_appointment_form_data(self, field: str, value: Any):
        """Update appointment form data."""
        self.appointment_form_data[field] = value

    def get_appointment_by_id(self, appointment_id: str) -> Optional[Appointment]:
        """Get an appointment by ID."""
        for appointment in self.appointments:
            if appointment.id == appointment_id:
                return appointment
        return None

    async def submit_new_appointment(self):
        """Submit new appointment to backend."""
        if not self.appointment_form_data.get("title"):
            self.error_message = "Appointment title is required"
            return

        if not self.appointment_form_data.get("scheduled_date"):
            self.error_message = "Scheduled date is required"
            return

        if not self.appointment_form_data.get("assigned_to"):
            self.error_message = "Please assign a team member"
            return

        self.loading = True
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/api/appointments",
                    json=self.appointment_form_data
                )

                if response.status_code == 201:
                    appointment_data = response.json()
                    self.appointment_creation_message = f"Appointment '{self.appointment_form_data.get('title')}' created successfully"
                    self.appointment_creation_success = True
                    self.error_message = ""

                    # Refresh appointments
                    await self.load_appointments()

                    # Close modal after brief delay
                    await asyncio.sleep(1.5)
                    self.close_appointment_modal()
                else:
                    self.error_message = f"Failed to create appointment: {response.text}"
                    self.appointment_creation_success = False

        except Exception as e:
            self.error_message = f"Error creating appointment: {str(e)}"
            self.appointment_creation_success = False
        finally:
            self.loading = False

    async def update_appointment_status(self, appointment_id: str, new_status: str):
        """Update appointment status."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.api_base_url}/api/appointments/{appointment_id}",
                    json={"status": new_status}
                )
                if response.status_code == 200:
                    # Update local state
                    for appointment in self.appointments:
                        if appointment.id == appointment_id:
                            appointment.status = new_status
                            break
                    self.last_update = datetime.now().strftime("%H:%M:%S")
                else:
                    self.error_message = f"Failed to update appointment status: {response.status_code}"
        except Exception as e:
            self.error_message = f"Failed to update appointment status: {str(e)}"

    async def cancel_appointment(self, appointment_id: str, reason: str = ""):
        """Cancel an appointment."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.api_base_url}/api/appointments/{appointment_id}",
                    json={
                        "status": "cancelled",
                        "cancellation_reason": reason
                    }
                )
                if response.status_code == 200:
                    # Update local state
                    for appointment in self.appointments:
                        if appointment.id == appointment_id:
                            appointment.status = "cancelled"
                            break
                    self.last_update = datetime.now().strftime("%H:%M:%S")
                    self.bulk_operation_success_message = "Appointment cancelled successfully"
                else:
                    self.error_message = f"Failed to cancel appointment: {response.status_code}"
        except Exception as e:
            self.error_message = f"Failed to cancel appointment: {str(e)}"

    # Filter setters
    def set_appointment_type_filter(self, appointment_type: str):
        """Set appointment type filter."""
        self.appointment_type_filter = appointment_type

    def set_appointment_status_filter(self, status: str):
        """Set appointment status filter."""
        self.appointment_status_filter = status

    def set_appointment_assigned_to_filter(self, assigned_to: str):
        """Set appointment assigned to filter."""
        self.appointment_assigned_to_filter = assigned_to

    def set_appointment_search_query(self, query: str):
        """Set appointment search query."""
        self.appointment_search_query = query

    # Computed properties for calendar views
    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def calendar_month_appointments(self) -> List[Appointment]:
        """Get appointments for the current calendar month view."""
        from datetime import datetime, date

        if not self.calendar_view_date:
            view_date = date.today()
        else:
            view_date = datetime.fromisoformat(self.calendar_view_date).date()

        filtered = self.filter_appointments()

        return [
            appointment for appointment in filtered
            if datetime.fromisoformat(appointment.scheduled_date.replace('Z', '+00:00')).date().month == view_date.month
            and datetime.fromisoformat(appointment.scheduled_date.replace('Z', '+00:00')).date().year == view_date.year
        ]

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def calendar_week_appointments(self) -> List[Appointment]:
        """Get appointments for the current calendar week view."""
        from datetime import datetime, date, timedelta

        if not self.calendar_view_date:
            view_date = date.today()
        else:
            view_date = datetime.fromisoformat(self.calendar_view_date).date()

        # Get start of week (Monday)
        start_of_week = view_date - timedelta(days=view_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        filtered = self.filter_appointments()

        return [
            appointment for appointment in filtered
            if start_of_week <= datetime.fromisoformat(appointment.scheduled_date.replace('Z', '+00:00')).date() <= end_of_week
        ]

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def calendar_day_appointments(self) -> List[Appointment]:
        """Get appointments for the current calendar day view."""
        if not self.calendar_view_date:
            from datetime import date
            target_date = date.today().isoformat()
        else:
            target_date = self.calendar_view_date

        return self.get_appointments_by_date(target_date)

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def appointment_types_list(self) -> List[str]:
        """Get unique appointment types for filter options."""
        types = set()
        for appointment in self.appointments:
            types.add(appointment.appointment_type)
        return sorted(list(types))

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def appointment_statuses_list(self) -> List[str]:
        """Get unique appointment statuses for filter options."""
        statuses = set()
        for appointment in self.appointments:
            statuses.add(appointment.status)
        return sorted(list(statuses))

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def entity_options_for_appointments(self) -> List[str]:
        """Get entity options (leads, customers, projects) for appointment assignment."""
        options = []

        # Add leads
        for lead in self.leads:
            options.append(f"lead|{lead.id}|{lead.first_name} {lead.last_name}")

        # Add customers
        for customer in self.customers:
            options.append(f"customer|{customer.id}|{customer.first_name} {customer.last_name}")

        # Add projects
        for project in self.projects:
            options.append(f"project|{project.id}|{project.title}")

        return options

    # ================ ANALYTICS STATE VARIABLES ================

    # Analytics data
    analytics_data: Dict[str, Any] = {}
    analytics_loading: bool = False
    analytics_date_range: str = "last_30_days"
    analytics_selected_metric: str = ""
    analytics_view_mode: str = "overview"  # overview, detailed, team
    analytics_error_message: str = ""

    # KPI data
    kpi_data: Dict[str, Any] = {}
    conversion_funnel_data: Dict[str, Any] = {}
    revenue_data: Dict[str, Any] = {}
    team_performance_data: Dict[str, Any] = {}

    # Analytics filters
    analytics_start_date: str = ""
    analytics_end_date: str = ""
    analytics_lead_source_filter: str = "all"
    analytics_team_member_filter: str = "all"
    analytics_project_type_filter: str = "all"

    async def load_analytics_data(self):
        """Load analytics data from backend API."""
        self.analytics_loading = True
        self.analytics_error_message = ""

        try:
            async with httpx.AsyncClient() as client:
                # Set date range parameters
                params = {
                    "date_range": self.analytics_date_range
                }

                if self.analytics_start_date:
                    params["start_date"] = self.analytics_start_date
                if self.analytics_end_date:
                    params["end_date"] = self.analytics_end_date
                if self.analytics_lead_source_filter != "all":
                    params["lead_source"] = self.analytics_lead_source_filter
                if self.analytics_team_member_filter != "all":
                    params["team_member"] = self.analytics_team_member_filter
                if self.analytics_project_type_filter != "all":
                    params["project_type"] = self.analytics_project_type_filter

                # Load KPI data
                kpi_response = await client.get(f"{self.api_base_url}/api/analytics/kpis", params=params)
                if kpi_response.status_code == 200:
                    self.kpi_data = kpi_response.json()

                # Load conversion funnel data
                funnel_response = await client.get(f"{self.api_base_url}/api/analytics/conversion-funnel", params=params)
                if funnel_response.status_code == 200:
                    self.conversion_funnel_data = funnel_response.json()

                # Load revenue data
                revenue_response = await client.get(f"{self.api_base_url}/api/analytics/revenue", params=params)
                if revenue_response.status_code == 200:
                    self.revenue_data = revenue_response.json()

                # Load team performance data
                team_response = await client.get(f"{self.api_base_url}/api/analytics/team-performance", params=params)
                if team_response.status_code == 200:
                    self.team_performance_data = team_response.json()

                # Combine all data
                self.analytics_data = {
                    "kpis": self.kpi_data,
                    "conversion_funnel": self.conversion_funnel_data,
                    "revenue": self.revenue_data,
                    "team_performance": self.team_performance_data
                }

                self.last_update = datetime.now().strftime("%H:%M:%S")

        except Exception as e:
            self.analytics_error_message = f"Failed to load analytics data: {str(e)}"
        finally:
            self.analytics_loading = False

    def set_analytics_date_range(self, date_range: str):
        """Set analytics date range."""
        self.analytics_date_range = date_range

    def set_analytics_view_mode(self, view_mode: str):
        """Set analytics view mode."""
        self.analytics_view_mode = view_mode

    def set_analytics_start_date(self, date: str):
        """Set analytics start date."""
        self.analytics_start_date = date

    def set_analytics_end_date(self, date: str):
        """Set analytics end date."""
        self.analytics_end_date = date

    def set_analytics_lead_source_filter(self, source: str):
        """Set analytics lead source filter."""
        self.analytics_lead_source_filter = source

    def set_analytics_team_member_filter(self, member: str):
        """Set analytics team member filter."""
        self.analytics_team_member_filter = member

    def set_analytics_project_type_filter(self, project_type: str):
        """Set analytics project type filter."""
        self.analytics_project_type_filter = project_type

    def toggle_analytics_metric(self, metric: str):
        """Toggle selected analytics metric."""
        if self.analytics_selected_metric == metric:
            self.analytics_selected_metric = ""
        else:
            self.analytics_selected_metric = metric

    # Analytics computed properties
    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def analytics_kpi_summary(self) -> Dict[str, Any]:
        """Get KPI summary for dashboard cards."""
        if not self.kpi_data:
            return {
                "business_health_score": 0,
                "total_revenue": 0,
                "pipeline_value": 0,
                "avg_deal_size": 0,
                "total_leads": 0,
                "avg_response_time": 0,
                "conversion_rate": 0,
                "active_team_members": 0,
                "active_projects": 0,
                "completion_rate": 0
            }

        return self.kpi_data.get("summary", {})

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def analytics_conversion_stages(self) -> List[Dict[str, Any]]:
        """Get conversion funnel stages data."""
        if not self.conversion_funnel_data:
            return []

        return self.conversion_funnel_data.get("stages", [])

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def analytics_revenue_trends(self) -> List[Dict[str, Any]]:
        """Get revenue trend data."""
        if not self.revenue_data:
            return []

        return self.revenue_data.get("trends", [])

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def analytics_team_leaderboard(self) -> List[Dict[str, Any]]:
        """Get team performance leaderboard."""
        if not self.team_performance_data:
            return []

        return self.team_performance_data.get("leaderboard", [])

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def analytics_available_sources(self) -> List[str]:
        """Get available lead sources for filtering."""
        sources = ["all"]
        for lead in self.leads:
            if lead.source and lead.source not in sources:
                sources.append(lead.source)
        return sources

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def analytics_available_team_members(self) -> List[str]:
        """Get available team members for filtering."""
        members = ["all"]
        for member in self.team_members:
            if member.get("name") and member["name"] not in members:
                members.append(member["name"])
        return members

    # @rx.var(cache=True) - Removed to eliminate WebSocket dependencies
    def analytics_available_project_types(self) -> List[str]:
        """Get available project types for filtering."""
        types = ["all"]
        for project in self.projects:
            if project.project_type and project.project_type not in types:
                types.append(project.project_type)
        return types

    async def export_analytics_report(self, report_type: str = "pdf"):
        """Export analytics report."""
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "date_range": self.analytics_date_range,
                    "format": report_type
                }

                if self.analytics_start_date:
                    params["start_date"] = self.analytics_start_date
                if self.analytics_end_date:
                    params["end_date"] = self.analytics_end_date

                response = await client.post(
                    f"{self.api_base_url}/api/analytics/export",
                    params=params
                )

                if response.status_code == 200:
                    self.bulk_operation_success_message = f"Analytics report exported successfully as {report_type.upper()}"
                else:
                    self.analytics_error_message = f"Failed to export report: {response.status_code}"

        except Exception as e:
            self.analytics_error_message = f"Failed to export report: {str(e)}"

    def clear_analytics_filters(self):
        """Clear all analytics filters."""
        self.analytics_start_date = ""
        self.analytics_end_date = ""
        self.analytics_lead_source_filter = "all"
        self.analytics_team_member_filter = "all"
        self.analytics_project_type_filter = "all"
        self.analytics_date_range = "last_30_days"

    # ================ SETTINGS METHODS ================

    def set_settings_active_tab(self, tab: str) -> None:
        """Set the active settings tab."""
        self.settings_active_tab = tab
        self.settings_success_message = ""
        self.settings_error_message = ""

    def toggle_team_member_modal(self) -> None:
        """Toggle team member modal."""
        self.team_member_modal_open = not self.team_member_modal_open
        if not self.team_member_modal_open:
            self.selected_team_member_id = None

    def select_team_member_for_edit(self, member_id: str) -> None:
        """Select a team member for editing."""
        self.selected_team_member_id = member_id
        self.team_member_modal_open = True

    async def load_settings_data(self) -> None:
        """Load all settings data from backend."""
        self.settings_loading = True
        self.settings_error_message = ""

        try:
            # Simulate API call to load team members
            await asyncio.sleep(1)

            # Load sample team members
            sample_members = [
                TeamMember(
                    id="tm_1",
                    first_name="John",
                    last_name="Smith",
                    email="john.smith@iswitchroofs.com",
                    phone="(248) 555-0123",
                    role="admin",
                    status="active",
                    permissions=["leads", "customers", "projects", "team", "settings"],
                    created_at="2024-01-15T10:30:00",
                    last_login="2024-10-05T09:15:00"
                ),
                TeamMember(
                    id="tm_2",
                    first_name="Sarah",
                    last_name="Johnson",
                    email="sarah.johnson@iswitchroofs.com",
                    phone="(248) 555-0124",
                    role="manager",
                    status="active",
                    permissions=["leads", "customers", "projects"],
                    created_at="2024-01-20T14:20:00",
                    last_login="2024-10-05T08:45:00"
                ),
                TeamMember(
                    id="tm_3",
                    first_name="Mike",
                    last_name="Wilson",
                    email="mike.wilson@iswitchroofs.com",
                    phone="(248) 555-0125",
                    role="sales_rep",
                    status="active",
                    permissions=["leads", "customers"],
                    created_at="2024-02-01T11:10:00",
                    last_login="2024-10-04T16:30:00"
                )
            ]
            self.team_members = sample_members

            # Load user settings
            self.user_settings = UserSettings(
                user_id="current_user",
                notification_preferences={
                    "email_new_leads": True,
                    "email_appointments": True,
                    "sms_urgent_alerts": True,
                    "push_notifications": True
                },
                dashboard_layout={"layout": "default"},
                timezone="America/Detroit",
                theme="light"
            )

        except Exception as e:
            self.settings_error_message = f"Error loading settings: {str(e)}"
        finally:
            self.settings_loading = False

    async def save_team_member(self, member_data: Dict[str, Any]) -> None:
        """Save team member data."""
        self.settings_saving = True
        self.settings_error_message = ""

        try:
            await asyncio.sleep(1)  # Simulate API call

            if self.selected_team_member_id:
                # Update existing member
                for i, member in enumerate(self.team_members):
                    if member.id == self.selected_team_member_id:
                        # Update the member with new data
                        updated_member = TeamMember(
                            id=member.id,
                            first_name=member_data.get("first_name", member.first_name),
                            last_name=member_data.get("last_name", member.last_name),
                            email=member_data.get("email", member.email),
                            phone=member_data.get("phone", member.phone),
                            role=member_data.get("role", member.role),
                            status=member_data.get("status", member.status),
                            permissions=member_data.get("permissions", member.permissions),
                            created_at=member.created_at,
                            last_login=member.last_login
                        )
                        self.team_members[i] = updated_member
                        break
                self.settings_success_message = "Team member updated successfully!"
            else:
                # Add new member
                new_member = TeamMember(
                    id=f"tm_{len(self.team_members) + 1}",
                    first_name=member_data["first_name"],
                    last_name=member_data["last_name"],
                    email=member_data["email"],
                    phone=member_data.get("phone"),
                    role=member_data["role"],
                    status=member_data.get("status", "active"),
                    permissions=member_data.get("permissions", []),
                    created_at=datetime.now().isoformat(),
                    last_login=None
                )
                self.team_members.append(new_member)
                self.settings_success_message = "Team member added successfully!"

            self.team_member_modal_open = False
            self.selected_team_member_id = None
            self.settings_unsaved_changes = False

        except Exception as e:
            self.settings_error_message = f"Error saving team member: {str(e)}"
        finally:
            self.settings_saving = False

    async def save_user_profile(self, profile_data: Dict[str, Any]) -> None:
        """Save user profile settings."""
        self.settings_saving = True
        self.settings_error_message = ""

        try:
            await asyncio.sleep(1)  # Simulate API call

            # Update user settings
            if self.user_settings:
                self.user_settings.timezone = profile_data.get("timezone", self.user_settings.timezone)
                self.user_settings.theme = profile_data.get("theme", self.user_settings.theme)
                self.user_settings.dashboard_layout = profile_data.get("dashboard_layout", self.user_settings.dashboard_layout)

            self.settings_success_message = "Profile settings saved successfully!"
            self.settings_unsaved_changes = False

        except Exception as e:
            self.settings_error_message = f"Error saving profile: {str(e)}"
        finally:
            self.settings_saving = False

    async def save_notification_settings(self, notification_data: Dict[str, Any]) -> None:
        """Save notification preferences."""
        self.settings_saving = True
        self.settings_error_message = ""

        try:
            await asyncio.sleep(1)  # Simulate API call

            # Update notification preferences
            if self.user_settings:
                self.user_settings.notification_preferences.update(notification_data)

            self.settings_success_message = "Notification settings saved successfully!"
            self.settings_unsaved_changes = False

        except Exception as e:
            self.settings_error_message = f"Error saving notifications: {str(e)}"
        finally:
            self.settings_saving = False

    # ================ PUSHER REAL-TIME METHODS ================

    async def load_pusher_config(self):
        """Load Pusher configuration from backend."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_base_url}/api/realtime/config")
                if response.status_code == 200:
                    self.pusher_config = response.json()
                    return True
                else:
                    print(f"Failed to load Pusher config: {response.status_code}")
                    return False
        except Exception as e:
            print(f"Error loading Pusher config: {str(e)}")
            return False

    def init_pusher_connection(self):
        """Initialize Pusher connection - JavaScript will handle the actual connection."""
        # This will be called from frontend JavaScript
        # We'll use rx.call_script to execute JavaScript that initializes Pusher
        if self.pusher_config:
            pusher_key = self.pusher_config.get("key", "")
            pusher_cluster = self.pusher_config.get("cluster", "us2")
            auth_endpoint = f"{self.api_base_url}{self.pusher_config.get('authEndpoint', '/api/realtime/auth')}"

            # JavaScript code to initialize Pusher
            js_code = f"""
            if (typeof window !== 'undefined' && window.Pusher) {{
                if (window.pusherClient) {{
                    window.pusherClient.disconnect();
                }}

                window.pusherClient = new Pusher('{pusher_key}', {{
                    cluster: '{pusher_cluster}',
                    authEndpoint: '{auth_endpoint}',
                    auth: {{
                        headers: {{
                            'X-User-ID': 'user-123',
                            'X-User-Name': 'Demo User',
                            'X-User-Email': 'demo@iswitchroofs.com'
                        }}
                    }}
                }});

                // Subscribe to global channel
                const globalChannel = window.pusherClient.subscribe('global');
                globalChannel.bind('notification', function(data) {{
                    console.log('Received notification:', data);
                    // Update Reflex state through custom event
                    window.dispatchEvent(new CustomEvent('pusher-notification', {{ detail: data }}));
                }});

                // Subscribe to leads channel
                const leadsChannel = window.pusherClient.subscribe('leads');
                leadsChannel.bind('lead:created', function(data) {{
                    console.log('New lead created:', data);
                    window.dispatchEvent(new CustomEvent('pusher-lead-created', {{ detail: data }}));
                }});

                leadsChannel.bind('lead:updated', function(data) {{
                    console.log('Lead updated:', data);
                    window.dispatchEvent(new CustomEvent('pusher-lead-updated', {{ detail: data }}));
                }});

                // Connection event handlers
                window.pusherClient.connection.bind('connected', function() {{
                    console.log('Pusher connected successfully');
                    window.dispatchEvent(new CustomEvent('pusher-connected'));
                }});

                window.pusherClient.connection.bind('disconnected', function() {{
                    console.log('Pusher disconnected');
                    window.dispatchEvent(new CustomEvent('pusher-disconnected'));
                }});

                console.log('Pusher client initialized');
            }} else {{
                console.warn('Pusher library not loaded or not in browser environment');
            }}
            """

            return rx.call_script(js_code)
        return rx.call_script("console.warn('Pusher config not loaded');")

    def handle_pusher_connected(self):
        """Handle Pusher connection success."""
        self.pusher_connected = True
        self.last_update = datetime.now().isoformat()

    def handle_pusher_disconnected(self):
        """Handle Pusher disconnection."""
        self.pusher_connected = False

    def handle_pusher_notification(self, data: Dict[str, Any]):
        """Handle incoming Pusher notifications."""
        # This will be called from JavaScript event listeners
        # Add notification to alerts or handle as needed
        self.last_update = datetime.now().isoformat()

    def handle_pusher_lead_created(self, data: Dict[str, Any]):
        """Handle new lead created via Pusher."""
        # Refresh leads data when new lead is created
        asyncio.create_task(self.load_leads())

    def handle_pusher_lead_updated(self, data: Dict[str, Any]):
        """Handle lead update via Pusher."""
        # Refresh leads data when lead is updated
        asyncio.create_task(self.load_leads())

    async def initialize_pusher(self):
        """Initialize Pusher connection - loads config and starts connection."""
        try:
            # Load Pusher configuration from backend
            config_loaded = await self.load_pusher_config()
            if config_loaded:
                # Initialize the Pusher connection via JavaScript
                return self.init_pusher_connection()
            else:
                print("Failed to load Pusher configuration")
                return rx.call_script("console.warn('Failed to load Pusher configuration');")
        except Exception as e:
            print(f"Error initializing Pusher: {str(e)}")
            return rx.call_script(f"console.error('Error initializing Pusher: {str(e)}');")


# ================ GLOBAL STATE INSTANCE ================
# Create a global instance for static data management (no WebSocket)
app_state = AppState()

# ================ DATA MANAGEMENT UTILITIES ================
class DataManager:
    """Utility class for managing application data without WebSocket state."""

    @staticmethod
    def get_state() -> AppState:
        """Get the global state instance."""
        return app_state

    @staticmethod
    def update_state(**kwargs) -> None:
        """Update global state properties."""
        global app_state
        for key, value in kwargs.items():
            if hasattr(app_state, key):
                setattr(app_state, key, value)

    @staticmethod
    def reset_state() -> None:
        """Reset state to default values."""
        global app_state
        app_state = AppState()

# Create data manager instance
data_manager = DataManager()