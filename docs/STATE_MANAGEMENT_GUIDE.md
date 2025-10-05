# State Management Guide: Reflex CRM AppState

## Overview

The iSwitch Roofs CRM frontend uses a centralized state management pattern with Reflex's reactive state system. The entire application state is managed through a single `AppState` class that provides type-safe, reactive data management with automatic UI updates.

## AppState Architecture

### Core Structure

```python
class AppState(rx.State):
    """Centralized state management for the entire CRM application"""

    # Core Entity Data
    leads: list[Lead] = []
    customers: list[Customer] = []
    projects: list[Project] = []
    appointments: list[Appointment] = []
    team_members: list[TeamMember] = []

    # UI State Management
    loading: bool = False
    error_message: str = ""
    success_message: str = ""

    # Modal and Navigation State
    lead_detail_modal_open: bool = False
    new_lead_modal_open: bool = False
    selected_lead_id: str = ""

    # Filter and Search State
    lead_status_filter: str = "all"
    lead_search_query: str = ""
    date_filter_start: str = ""
    date_filter_end: str = ""
```

## Data Management Patterns

### 1. Entity Management

#### Lead Management
```python
class AppState(rx.State):
    leads: list[Lead] = []

    async def load_leads(self):
        """Load all leads from API"""
        try:
            self.loading = True
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE_URL}/api/leads/")
                response.raise_for_status()
                self.leads = [Lead(**lead) for lead in response.json()]
        except Exception as e:
            self.error_message = f"Failed to load leads: {str(e)}"
        finally:
            self.loading = False

    async def create_lead(self, lead_data: dict):
        """Create new lead"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/api/leads/",
                    json=lead_data
                )
                response.raise_for_status()
                new_lead = Lead(**response.json())
                self.leads.append(new_lead)
                self.success_message = "Lead created successfully"
        except Exception as e:
            self.error_message = f"Failed to create lead: {str(e)}"
```

#### Project Management
```python
async def handle_project_status_change(self, project_id: str, new_status: str):
    """Handle project status changes from drag-and-drop"""
    try:
        # Update local state immediately for responsive UI
        for project in self.projects:
            if project.id == project_id:
                project.status = new_status
                break

        # Sync with backend
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{API_BASE_URL}/api/projects/{project_id}/status",
                json={"status": new_status}
            )
            response.raise_for_status()

    except Exception as e:
        # Revert local change on error
        await self.load_projects()
        self.error_message = f"Failed to update project: {str(e)}"
```

### 2. Computed Properties

#### Filtered and Derived Data
```python
@rx.computed_var
def filtered_leads(self) -> list[Lead]:
    """Filter leads based on current filter settings"""
    filtered = self.leads

    # Status filter
    if self.lead_status_filter != "all":
        filtered = [l for l in filtered if l.status == self.lead_status_filter]

    # Search query
    if self.lead_search_query:
        query = self.lead_search_query.lower()
        filtered = [
            l for l in filtered
            if query in f"{l.first_name} {l.last_name} {l.email}".lower()
        ]

    return filtered

@rx.computed_var
def hot_leads(self) -> list[Lead]:
    """Get all hot leads (score >= 80)"""
    return [lead for lead in self.leads if lead.lead_score >= 80]

@rx.computed_var
def leads_by_status(self) -> dict[str, list[Lead]]:
    """Group leads by status for Kanban board"""
    statuses = ["new", "contacted", "qualified", "proposal", "negotiation", "won", "lost", "unresponsive"]
    return {
        status: [lead for lead in self.leads if lead.status == status]
        for status in statuses
    }
```

#### Metrics and Analytics
```python
@rx.computed_var
def metrics(self) -> dict:
    """Calculate dashboard metrics"""
    total_leads = len(self.leads)
    hot_leads_count = len(self.hot_leads)

    # Conversion rate calculation
    won_leads = len([l for l in self.leads if l.status == "won"])
    conversion_rate = (won_leads / total_leads * 100) if total_leads > 0 else 0

    return {
        "total_leads": total_leads,
        "hot_leads": hot_leads_count,
        "conversion_rate": conversion_rate,
        "won_leads": won_leads
    }

@rx.computed_var
def revenue_metrics(self) -> dict:
    """Calculate revenue-related metrics"""
    pipeline_value = sum(p.estimated_value for p in self.projects if p.status != "cancelled")
    completed_revenue = sum(p.actual_value for p in self.projects if p.status == "completed")

    return {
        "pipeline_value": pipeline_value,
        "completed_revenue": completed_revenue,
        "average_project_value": completed_revenue / len(self.projects) if self.projects else 0
    }
```

### 3. UI State Management

#### Modal Management
```python
def open_lead_detail_modal(self, lead_id: str):
    """Open lead detail modal for specific lead"""
    self.selected_lead_id = lead_id
    self.lead_detail_modal_open = True

def close_lead_detail_modal(self):
    """Close lead detail modal"""
    self.lead_detail_modal_open = False
    self.selected_lead_id = ""

@rx.computed_var
def selected_lead(self) -> Optional[Lead]:
    """Get currently selected lead"""
    if not self.selected_lead_id:
        return None
    return next((l for l in self.leads if l.id == self.selected_lead_id), None)
```

#### Filter Management
```python
def set_lead_status_filter(self, status: str):
    """Update lead status filter"""
    self.lead_status_filter = status

def set_lead_search_query(self, query: str):
    """Update search query"""
    self.lead_search_query = query

def clear_filters(self):
    """Reset all filters to default"""
    self.lead_status_filter = "all"
    self.lead_search_query = ""
    self.date_filter_start = ""
    self.date_filter_end = ""
```

## Advanced State Patterns

### 1. Optimistic Updates

```python
async def handle_lead_drop(self, lead_id: str, new_status: str):
    """Handle drag-and-drop with optimistic updates"""
    # Store original state for rollback
    original_lead = next((l for l in self.leads if l.id == lead_id), None)
    if not original_lead:
        return

    original_status = original_lead.status

    try:
        # Optimistic update - change UI immediately
        original_lead.status = new_status

        # Sync with backend
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{API_BASE_URL}/api/leads/{lead_id}",
                json={"status": new_status}
            )
            response.raise_for_status()

    except Exception as e:
        # Rollback on error
        original_lead.status = original_status
        self.error_message = f"Failed to update lead: {str(e)}"
```

### 2. Batch Operations

```python
async def bulk_assign_leads(self, lead_ids: list[str], team_member_id: str):
    """Assign multiple leads to a team member"""
    try:
        self.loading = True

        # Batch API call
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/leads/bulk-assign",
                json={
                    "lead_ids": lead_ids,
                    "team_member_id": team_member_id
                }
            )
            response.raise_for_status()

        # Update local state
        for lead in self.leads:
            if lead.id in lead_ids:
                lead.assigned_to = team_member_id

        self.success_message = f"Assigned {len(lead_ids)} leads successfully"

    except Exception as e:
        self.error_message = f"Failed to assign leads: {str(e)}"
    finally:
        self.loading = False
```

### 3. Real-time Updates

```python
async def handle_realtime_update(self, update_type: str, data: dict):
    """Handle real-time updates from WebSocket/Pusher"""
    if update_type == "lead_created":
        new_lead = Lead(**data)
        self.leads.append(new_lead)

    elif update_type == "lead_updated":
        lead_id = data["id"]
        for i, lead in enumerate(self.leads):
            if lead.id == lead_id:
                self.leads[i] = Lead(**data)
                break

    elif update_type == "lead_deleted":
        lead_id = data["id"]
        self.leads = [l for l in self.leads if l.id != lead_id]
```

## State Validation and Error Handling

### 1. Data Validation

```python
def validate_lead_data(self, lead_data: dict) -> bool:
    """Validate lead data before API calls"""
    required_fields = ["first_name", "last_name", "email", "phone"]

    for field in required_fields:
        if not lead_data.get(field):
            self.error_message = f"Required field missing: {field}"
            return False

    # Email validation
    email = lead_data.get("email", "")
    if "@" not in email or "." not in email:
        self.error_message = "Invalid email format"
        return False

    return True
```

### 2. Error State Management

```python
def clear_messages(self):
    """Clear all status messages"""
    self.error_message = ""
    self.success_message = ""

def set_error(self, message: str):
    """Set error message and clear success"""
    self.error_message = message
    self.success_message = ""

def set_success(self, message: str):
    """Set success message and clear error"""
    self.success_message = message
    self.error_message = ""
```

## Performance Optimization

### 1. Selective Loading

```python
async def load_dashboard_data(self):
    """Load only essential data for dashboard"""
    await asyncio.gather(
        self.load_recent_leads(),
        self.load_metrics(),
        self.load_alerts()
    )

async def load_recent_leads(self):
    """Load only recent leads for dashboard display"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/api/leads/",
                params={"limit": 10, "sort": "created_at:desc"}
            )
            response.raise_for_status()
            self.recent_leads = [Lead(**lead) for lead in response.json()]
    except Exception as e:
        self.error_message = f"Failed to load recent leads: {str(e)}"
```

### 2. Computed Property Caching

```python
@rx.computed_var
def expensive_calculation(self) -> dict:
    """Expensive calculation that's automatically cached"""
    # This will only recalculate when dependencies change
    result = {}
    for lead in self.leads:
        # Complex calculations here
        pass
    return result
```

## State Persistence

### 1. Session Storage

```python
def save_filter_state(self):
    """Save filter state to session storage"""
    filter_state = {
        "status_filter": self.lead_status_filter,
        "search_query": self.lead_search_query,
        "date_start": self.date_filter_start,
        "date_end": self.date_filter_end
    }
    # Implementation would use browser storage

def restore_filter_state(self):
    """Restore filter state from session storage"""
    # Implementation would restore from browser storage
    pass
```

### 2. URL State Synchronization

```python
def sync_url_params(self):
    """Sync state with URL parameters"""
    # Update URL to reflect current filters
    # This allows bookmarking and sharing filtered views
    pass
```

## Testing State Management

### 1. Unit Testing State Methods

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_load_leads():
    """Test lead loading functionality"""
    state = AppState()

    mock_response = AsyncMock()
    mock_response.json.return_value = [
        {"id": "1", "first_name": "John", "last_name": "Doe", "email": "john@example.com"}
    ]
    mock_response.raise_for_status = AsyncMock()

    with patch('httpx.AsyncClient.get', return_value=mock_response):
        await state.load_leads()

    assert len(state.leads) == 1
    assert state.leads[0].first_name == "John"
    assert state.error_message == ""
```

### 2. Computed Property Testing

```python
def test_filtered_leads():
    """Test lead filtering functionality"""
    state = AppState()
    state.leads = [
        Lead(id="1", first_name="John", status="new"),
        Lead(id="2", first_name="Jane", status="contacted"),
        Lead(id="3", first_name="Bob", status="new")
    ]

    state.lead_status_filter = "new"
    filtered = state.filtered_leads

    assert len(filtered) == 2
    assert all(lead.status == "new" for lead in filtered)
```

## Migration and Refactoring

### 1. State Splitting Strategy

For large applications, consider splitting AppState:

```python
class LeadState(rx.State):
    """Dedicated state for lead management"""
    leads: list[Lead] = []
    lead_filters: LeadFilters = LeadFilters()

class ProjectState(rx.State):
    """Dedicated state for project management"""
    projects: list[Project] = []
    project_filters: ProjectFilters = ProjectFilters()

class AppState(LeadState, ProjectState):
    """Main application state inheriting from domain states"""
    # Common UI state only
    loading: bool = False
    error_message: str = ""
```

### 2. State Migration

```python
def migrate_state_v1_to_v2(self, old_state: dict) -> dict:
    """Migrate state format from v1 to v2"""
    # Handle data format changes
    # Update field names, structures, etc.
    return updated_state
```

## Best Practices

### 1. State Organization

- **Group Related Data** - Keep related entities together
- **Separate UI from Data** - Clear distinction between data and UI state
- **Use Computed Properties** - For derived data and calculations
- **Minimize State Mutations** - Prefer immutable updates where possible

### 2. Error Handling

- **Consistent Error Patterns** - Standardized error message handling
- **User-Friendly Messages** - Clear, actionable error messages
- **Graceful Degradation** - App continues working when possible
- **Error Recovery** - Provide ways to retry failed operations

### 3. Performance

- **Lazy Loading** - Load data only when needed
- **Batch Operations** - Combine multiple API calls when possible
- **Optimistic Updates** - Update UI immediately, sync later
- **Computed Property Caching** - Automatic caching for expensive calculations

### 4. Testing

- **Unit Test State Methods** - Test individual state operations
- **Mock API Calls** - Isolate state logic from network dependencies
- **Test Computed Properties** - Verify calculated values
- **Integration Testing** - Test complete user workflows

## Debugging Guide

### 1. Common Issues

**State Not Updating**
- Check if state variable is properly declared
- Verify method is marked as async if needed
- Ensure UI components are properly bound to state

**Performance Issues**
- Profile computed properties for expensive calculations
- Check for unnecessary re-renders
- Optimize API call patterns

**Error Handling**
- Verify try-catch blocks around async operations
- Check error message state updates
- Ensure proper error user feedback

### 2. Debug Tools

```python
def debug_state(self):
    """Debug helper to log current state"""
    print(f"Leads: {len(self.leads)}")
    print(f"Loading: {self.loading}")
    print(f"Error: {self.error_message}")
    print(f"Filters: {self.lead_status_filter}")
```

---

**Document Version:** 1.0
**Last Updated:** January 17, 2025
**Author:** Development Team
**Review Status:** Complete