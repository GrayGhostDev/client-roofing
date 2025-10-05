# Appointment Management System

## Overview

The Appointment Management System is a comprehensive calendar and scheduling solution integrated into the iSwitch Roofs CRM. It provides full appointment lifecycle management with calendar integration, real-time scheduling, and seamless integration with leads, customers, and projects.

## Features

### 📅 Calendar Views
- **Month View**: Traditional monthly calendar grid with appointments
- **Week View**: Weekly schedule with detailed time slots (8 AM - 6 PM)
- **Day View**: Detailed daily schedule with hourly time slots (6 AM - 10 PM)
- **List View**: Table format with filtering and summary statistics

### 🗓️ Appointment Management
- **Create/Edit Appointments**: Comprehensive form with all appointment details
- **Appointment Types**:
  - Initial Consultation
  - Roof Inspection
  - Quote Presentation
  - Contract Signing
  - Project Kickoff
  - Site Visit
  - Progress Check
  - Final Walkthrough
  - Follow-up Meeting
  - Emergency Inspection

- **Status Tracking**:
  - Scheduled
  - Confirmed
  - In Progress
  - Completed
  - Cancelled
  - No Show

### 🔗 Entity Integration
- **Link to Leads**: Schedule appointments for lead nurturing
- **Link to Customers**: Customer service and follow-up appointments
- **Link to Projects**: Project-related meetings and inspections

### 🏠 Location & Virtual Meetings
- **Physical Locations**: Support for on-site appointments with full addresses
- **Virtual Meetings**: Support for online meetings with URL links
- **Location Validation**: Clear indication of appointment type

### 👥 Team Assignment
- **Team Member Assignment**: Assign appointments to specific team members
- **Availability Tracking**: Integration with team member schedules
- **Workload Distribution**: Visual representation of team assignment

### 🔔 Notifications & Reminders
- **Reminder System**: Automated reminders for upcoming appointments
- **Confirmation Tracking**: Customer confirmation status tracking
- **Status Updates**: Real-time status change notifications

## Technical Architecture

### Data Model

```python
class Appointment(rx.Base):
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
```

### State Management

The appointment system adds comprehensive state management to `AppState`:

#### Core State Variables
- `appointments: List[Appointment] = []` - All appointments
- `selected_appointment_id: Optional[str] = None` - Currently selected appointment
- `appointment_modal_open: bool = False` - Modal visibility state
- `calendar_view_mode: str = "month"` - Current calendar view
- `calendar_selected_date: str = ""` - Selected date in calendar

#### Filtering and Search
- `appointment_type_filter: str = "all"` - Filter by appointment type
- `appointment_status_filter: str = "all"` - Filter by status
- `appointment_assigned_to_filter: str = "all"` - Filter by team member
- `appointment_search_query: str = ""` - Search query

### Component Structure

```
components/appointments/
├── __init__.py                     # Package exports
├── appointment_calendar.py         # Main calendar component
├── appointment_modal.py            # Create/edit appointment modal
├── appointment_list.py             # List view with filtering
├── appointment_detail_modal.py     # Appointment details view
├── appointments_dashboard.py       # Dashboard integration
└── dashboard_with_appointments.py  # Enhanced dashboard example
```

### API Integration

The system integrates with backend APIs for:
- `GET /api/appointments` - Load appointments
- `POST /api/appointments` - Create new appointment
- `PATCH /api/appointments/{id}` - Update appointment
- `DELETE /api/appointments/{id}` - Delete appointment

## Usage Examples

### Basic Integration

```python
from .components.appointments import appointments_dashboard

# Add to your app
app.add_page(appointments_dashboard, route="/appointments")
```

### Dashboard Widget Integration

```python
from .components.appointments import (
    appointment_summary_widget,
    upcoming_appointments_widget,
    todays_schedule_widget
)

def dashboard():
    return rx.grid(
        main_content(),
        rx.vstack(
            appointment_summary_widget(),
            upcoming_appointments_widget(),
            spacing="4"
        ),
        columns="2"
    )
```

### Programmatic Appointment Creation

```python
# Open appointment modal with pre-filled date
AppState.open_appointment_modal_with_date("2024-01-15", "10:00")

# Create appointment from lead
AppState.update_appointment_form_data("entity_type", "lead")
AppState.update_appointment_form_data("entity_id", lead_id)
AppState.open_appointment_modal()
```

## Key Methods

### Calendar Navigation
- `navigate_calendar(direction: str)` - Navigate forward/backward
- `go_to_today()` - Jump to current date
- `set_calendar_view_mode(mode: str)` - Change view mode

### Appointment Management
- `open_appointment_modal()` - Open creation modal
- `submit_new_appointment()` - Create new appointment
- `update_appointment_status(id, status)` - Update status
- `cancel_appointment(id, reason)` - Cancel appointment

### Data Filtering
- `filter_appointments()` - Apply current filters
- `get_appointments_by_date(date)` - Get appointments for specific date
- `get_upcoming_appointments()` - Get future appointments
- `get_todays_appointments()` - Get today's appointments
- `get_overdue_appointments()` - Get overdue appointments

## Widget Components

### Summary Widget
Displays appointment statistics and quick actions:
- Total appointments count
- Today's appointments
- Upcoming appointments
- Overdue appointments

### Today's Schedule Widget
Shows detailed schedule for current day:
- Time-ordered appointment list
- Appointment types and locations
- Quick access to appointment details

### Upcoming Appointments Widget
Displays next 5 upcoming appointments:
- Date and time information
- Appointment titles and types
- Status indicators

### Appointment Alerts Widget
Shows critical appointment notifications:
- Overdue appointments
- Unconfirmed appointments
- Status change alerts

## Customization

### Adding New Appointment Types

1. Update the appointment type list in `appointment_modal.py`:
```python
appointment_types = [
    "initial_consultation",
    "roof_inspection",
    "your_new_type",  # Add here
    # ... existing types
]
```

2. Update backend enum to match

### Custom Calendar Styling

Calendar views can be customized through the component styling:

```python
# Custom time slot styling
rx.box(
    # Your appointment content
    style={
        "cursor": "pointer",
        "&:hover": {
            "background_color": "var(--your-color)"
        }
    }
)
```

### Integration with External Calendars

The system supports integration with:
- Google Calendar (via google_calendar_event_id field)
- Outlook Calendar (via outlook_calendar_event_id field)
- Any iCal-compatible system

## Performance Considerations

### Caching
- Uses `@rx.var(cache=True)` for computed properties
- Filters are cached until data changes
- Calendar views are optimized for large datasets

### Memory Management
- Appointments are loaded on-demand
- Large appointment lists use pagination
- Old appointments can be archived

### Real-time Updates
- WebSocket integration for live updates
- Optimistic UI updates for better UX
- Conflict resolution for concurrent edits

## Security

### Access Control
- Team member-based access restrictions
- Role-based appointment visibility
- Secure API endpoints with authentication

### Data Validation
- Input sanitization on all forms
- Date validation (no past dates for new appointments)
- Duration limits and business hour enforcement

## Testing

The appointment system includes comprehensive test coverage:
- Unit tests for state management
- Integration tests for API calls
- Component testing for UI interactions
- End-to-end testing for user workflows

## Future Enhancements

### Planned Features
- Recurring appointment support
- Advanced conflict detection
- Weather integration for outdoor appointments
- Mobile app notifications
- Customer self-scheduling portal
- Advanced analytics and reporting

### API Extensions
- Bulk appointment operations
- Advanced filtering and search
- Export capabilities (CSV, iCal)
- Integration webhooks

## Support

For implementation questions or customization needs:
1. Check the component documentation
2. Review the state management methods
3. Examine the integration examples
4. Test with the provided demo data

The appointment system is designed to be flexible and extensible while providing a robust foundation for scheduling and calendar management in the roofing CRM.