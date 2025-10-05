# iSwitch Roofs CRM - Settings and Team Management

## Overview

Comprehensive settings and team management pages have been implemented for the roofing CRM system, providing administrative capabilities for system configuration, user management, and team operations.

## Features Implemented

### 1. Main Settings Page (`/settings`)
- **Tab-based navigation**: Profile, Team, System, Notifications
- **Real-time alerts**: Success/error messaging
- **Responsive design**: Optimized for desktop and mobile
- **State management**: Integrated with main AppState

### 2. Team Management
- **Team member listing**: Professional table view with avatars
- **Performance summary**: KPI cards showing team metrics
- **Add/Edit functionality**: Modal-based team member management (placeholder)
- **Role-based access**: Admin, Manager, Sales Rep, Installer roles
- **Status tracking**: Active, Inactive, Pending statuses
- **Analytics integration**: Link to team performance analytics

### 3. User Profile Settings
- **Personal information**: Name, email, phone management
- **Account security**: Password change, two-factor authentication
- **Preferences**: Timezone, theme, dashboard layout
- **Profile picture**: Avatar upload functionality
- **Save functionality**: Profile settings persistence

### 4. System Settings
- **Company information**: Logo, contact details, address
- **Lead management**: Response timeouts, auto-assignment rules
- **Appointment settings**: Buffer times, working hours, durations
- **Third-party integrations**: Google Calendar, Email, SMS services
- **Backup & security**: Data backup, security policies
- **Configuration management**: System-wide settings

### 5. Notification Settings
- **Email notifications**: New leads, updates, appointments
- **SMS notifications**: Urgent alerts, reminders
- **Push notifications**: Real-time updates, browser alerts
- **Notification scheduling**: Quiet hours, frequency limits
- **Message templates**: Customizable notification content
- **Test functionality**: Send test notifications

## Technical Implementation

### File Structure
```
/frontend-reflex/frontend_reflex/components/settings/
├── __init__.py                 # Package initialization
├── settings_page.py           # Main settings page with navigation
├── team_management.py         # Team member management
├── user_profile.py           # User profile settings
├── system_settings.py        # System configuration
└── notification_settings.py  # Notification preferences
```

### Data Models Added to State
```python
class TeamMember(rx.Base):
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
    user_id: str
    notification_preferences: Dict[str, bool] = {}
    dashboard_layout: Dict[str, Any] = {}
    timezone: str = "America/Detroit"
    theme: str = "light"
```

### State Variables Added
```python
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
```

### Methods Added to AppState
- `set_settings_active_tab(tab: str)`: Navigate between settings tabs
- `toggle_team_member_modal()`: Toggle team member modal
- `select_team_member_for_edit(member_id: str)`: Select team member for editing
- `load_settings_data()`: Load all settings data from backend
- `save_team_member(member_data: Dict[str, Any])`: Save team member data
- `save_user_profile(profile_data: Dict[str, Any])`: Save user profile
- `save_notification_settings(notification_data: Dict[str, Any])`: Save notifications

## Routes Added

The settings page is accessible at `/settings` and has been added to the main application routing:

```python
app.add_page(settings_page, route="/settings", title="iSwitch Roofs CRM - Settings")
```

## Dashboard Integration

A new settings card has been added to the main dashboard providing easy access to the settings page:

```python
rx.card(
    rx.vstack(
        rx.icon("settings", size=32, color="gray"),
        rx.heading("Settings", size="4"),
        rx.text("System configuration & team management", size="2", color="gray"),
        rx.link(
            rx.button("Open Settings", color_scheme="gray", size="2"),
            href="/settings"
        ),
        # ...
    )
)
```

## Design Patterns

### 1. Consistent UI Components
- Uses Radix UI components for consistency
- Card-based layout for organized sections
- Icon integration for visual clarity
- Responsive grid layouts

### 2. State Management
- Centralized state in AppState
- Async methods for backend integration
- Loading and error states
- Success feedback

### 3. Security Features
- Role-based access controls
- Password requirements
- Two-factor authentication options
- Activity logging capabilities

### 4. User Experience
- Tab-based navigation
- Contextual help text
- Form validation feedback
- Confirmation dialogs for important actions

## Sample Data

The implementation includes sample team members and settings data for demonstration:

### Team Members
1. **John Smith** - Admin (john.smith@iswitchroofs.com)
2. **Sarah Johnson** - Manager (sarah.johnson@iswitchroofs.com)
3. **Mike Wilson** - Sales Rep (mike.wilson@iswitchroofs.com)

### Default Settings
- **Company**: iSwitch Roofs, Detroit, MI
- **Lead timeout**: 120 seconds
- **Appointment buffer**: 15 minutes
- **Notifications**: Email and SMS enabled
- **Timezone**: America/Detroit

## Future Enhancements

### 1. Form Integration
- Complete form data binding
- Real-time validation
- Auto-save functionality
- Change tracking

### 2. Advanced Team Features
- Permission granularity
- Team hierarchies
- Performance metrics
- Bulk operations

### 3. Integration Features
- API key management
- Webhook configuration
- Third-party sync status
- Integration logs

### 4. Security Enhancements
- Audit logging
- Session management
- IP restrictions
- Password policies

## Usage Instructions

### Accessing Settings
1. Navigate to the main dashboard
2. Click the "Settings" card or go to `/settings`
3. Use the tab navigation to switch between sections

### Managing Team Members
1. Go to Settings → Team tab
2. View team performance summary
3. Click "Add Member" to add new team members
4. Use edit buttons to modify existing members
5. Monitor team analytics via the analytics link

### Configuring Notifications
1. Go to Settings → Notifications tab
2. Toggle email, SMS, and push notification preferences
3. Set quiet hours and frequency limits
4. Customize message templates
5. Test notifications before saving

### System Configuration
1. Go to Settings → System tab
2. Update company information
3. Configure lead management rules
4. Set appointment defaults
5. Manage third-party integrations
6. Configure backup and security settings

## Integration with Backend

The settings system is designed to integrate with the Flask backend API:

- **GET /api/settings**: Load all settings data
- **POST /api/settings/profile**: Save user profile
- **GET /api/team**: Load team members
- **POST /api/team**: Create team member
- **PUT /api/team/{id}**: Update team member
- **POST /api/settings/notifications**: Save notification preferences

## Error Handling

Comprehensive error handling includes:
- Network failure recovery
- Validation error display
- User-friendly error messages
- Retry mechanisms for failed operations

## Accessibility

The settings interface follows accessibility best practices:
- Keyboard navigation support
- Screen reader compatibility
- High contrast support
- Focus management
- ARIA labels and descriptions

This implementation provides a solid foundation for comprehensive settings and team management in the iSwitch Roofs CRM system, with room for future enhancements and integrations.