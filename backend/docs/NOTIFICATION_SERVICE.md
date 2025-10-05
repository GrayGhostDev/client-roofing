# Notification Service Documentation

## Overview
The iSwitch Roofs CRM Notification Service provides a unified interface for sending notifications across multiple channels including email (SendGrid), SMS (Twilio), and real-time updates (Pusher). The service includes template management, user preferences, scheduling, and delivery tracking.

## Architecture

### Service Components

```
┌─────────────────────────────────────────────────────────────┐
│                    NotificationService                       │
│                  (Main Orchestrator)                         │
├─────────────────┬────────────────┬──────────────────────────┤
│   EmailService  │   SMSService   │   RealtimeService        │
│   (SendGrid)    │   (Twilio)     │     (Pusher)             │
└─────────────────┴────────────────┴──────────────────────────┘
```

### File Structure
```
backend/app/
├── services/
│   ├── notification.py          # Main notification orchestrator
│   ├── email_service.py         # SendGrid email integration
│   ├── sms_service.py           # Twilio SMS integration
│   └── realtime_service.py      # Pusher real-time events
├── models/
│   └── notification.py          # Notification data models
└── utils/
    └── notification_templates.py # Email/SMS templates
```

## Configuration

### Environment Variables
```bash
# SendGrid Configuration
SENDGRID_API_KEY=your_sendgrid_api_key
FROM_EMAIL=noreply@iswitchroofs.com
COMPANY_NAME=iSwitch Roofs

# Twilio Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+12485551234

# Pusher Configuration
PUSHER_APP_ID=your_pusher_app_id
PUSHER_KEY=your_pusher_key
PUSHER_SECRET=your_pusher_secret
PUSHER_CLUSTER=us2

# Notification Settings
NOTIFICATION_QUIET_HOURS_START=22  # 10 PM
NOTIFICATION_QUIET_HOURS_END=8     # 8 AM
NOTIFICATION_RETRY_ATTEMPTS=3
NOTIFICATION_RETRY_DELAY=60  # seconds
```

## Usage Examples

### 1. Sending a Simple Notification

```python
from app.services.notification import notification_service

# Send notification to a specific user
success, error = notification_service.send_notification(
    type='lead_assigned',
    data={
        'lead_id': 'lead-uuid',
        'lead_name': 'John Doe',
        'lead_score': 85,
        'assigned_to_name': 'Sales Rep'
    },
    recipient_id='user-uuid',
    priority='high'
)
```

### 2. Sending Multi-Channel Notification

```python
# Send via specific channels
success, error = notification_service.send_notification(
    type='appointment_reminder',
    data={
        'appointment_id': 'apt-uuid',
        'customer_name': 'Jane Smith',
        'appointment_time': '2025-01-20 10:00 AM',
        'address': '123 Main St, Birmingham, MI'
    },
    recipient_id='user-uuid',
    channels=['email', 'sms', 'push'],
    priority='high'
)
```

### 3. Scheduling a Notification

```python
from datetime import datetime, timedelta

# Schedule a notification for tomorrow at 9 AM
send_at = datetime.utcnow() + timedelta(days=1)
send_at = send_at.replace(hour=9, minute=0, second=0, microsecond=0)

success, error = notification_service.schedule_notification(
    type='follow_up_reminder',
    data={
        'customer_name': 'John Doe',
        'last_interaction': 'Quote sent',
        'next_action': 'Follow up on quote'
    },
    recipient_id='user-uuid',
    send_at=send_at
)
```

### 4. Sending Bulk Notifications

```python
# Send to multiple recipients
recipients = ['user1-uuid', 'user2-uuid', 'user3-uuid']

for recipient_id in recipients:
    notification_service.send_notification(
        type='team_announcement',
        data={
            'title': 'Team Meeting',
            'message': 'Mandatory team meeting tomorrow at 9 AM',
            'location': 'Conference Room A'
        },
        recipient_id=recipient_id,
        priority='normal'
    )
```

## Notification Types

### Lead Notifications

#### `lead_new`
Triggered when a new lead is created.
```python
data = {
    'lead_id': str,
    'lead_name': str,
    'source': str,
    'phone': str,
    'email': str,
    'score': int
}
```

#### `lead_hot`
Triggered for high-scoring leads (80+).
```python
data = {
    'lead_id': str,
    'lead_name': str,
    'score': int,
    'source': str,
    'urgency': str
}
```

#### `lead_assigned`
Triggered when a lead is assigned to a team member.
```python
data = {
    'lead_id': str,
    'lead_name': str,
    'assigned_to_name': str,
    'lead_score': int
}
```

### Customer Notifications

#### `customer_welcome`
Sent when a lead is converted to customer.
```python
data = {
    'customer_name': str,
    'email': str,
    'phone': str
}
```

#### `customer_project_update`
Sent when a project status changes.
```python
data = {
    'customer_name': str,
    'project_name': str,
    'old_status': str,
    'new_status': str
}
```

### Appointment Notifications

#### `appointment_confirmation`
Sent when an appointment is scheduled.
```python
data = {
    'customer_name': str,
    'appointment_time': str,
    'appointment_type': str,
    'address': str,
    'assigned_to': str
}
```

#### `appointment_reminder`
Sent before appointment (configurable timing).
```python
data = {
    'customer_name': str,
    'appointment_time': str,
    'address': str,
    'phone': str
}
```

### Project Notifications

#### `project_started`
Sent when a project begins.
```python
data = {
    'project_name': str,
    'customer_name': str,
    'start_date': str,
    'estimated_completion': str
}
```

#### `project_completed`
Sent when a project is marked complete.
```python
data = {
    'project_name': str,
    'customer_name': str,
    'completion_date': str
}
```

## Email Templates

### Template Structure
```python
EMAIL_TEMPLATES = {
    "template_key": {
        "subject": "Email subject with {variable}",
        "html": """
        <html>
            <body>
                <h1>Title</h1>
                <p>Content with {variable}</p>
            </body>
        </html>
        """,
        "plain": "Plain text version with {variable}"
    }
}
```

### Available Email Templates
- `lead_new` - New lead notification
- `lead_hot` - Hot lead alert
- `lead_assigned` - Lead assignment notification
- `customer_welcome` - Welcome email for new customers
- `appointment_confirmation` - Appointment confirmation
- `appointment_reminder` - Appointment reminder
- `project_started` - Project start notification
- `project_completed` - Project completion notification
- `review_request` - Review request email
- `quote_sent` - Quote sent to customer
- `invoice_sent` - Invoice sent to customer
- `payment_received` - Payment confirmation

### Customizing Templates
```python
from app.utils.notification_templates import EMAIL_TEMPLATES

# Add custom template
EMAIL_TEMPLATES["custom_template"] = {
    "subject": "Custom Subject",
    "html": "<html>...</html>",
    "plain": "Plain text version"
}
```

## SMS Templates

### Template Structure
```python
SMS_TEMPLATES = {
    "template_key": "SMS message with {variable} - max 160 chars"
}
```

### Available SMS Templates
- `lead_response` - Quick response to new lead
- `appointment_reminder` - Appointment reminder
- `project_update` - Project status update
- `review_request` - Review request
- `payment_reminder` - Payment reminder

## Real-time Events

### Channel Types

#### Public Channels
```python
# Broadcast to all connected clients
realtime_service.trigger_event(
    channel='leads',
    event='lead-created',
    data={'lead': lead_data}
)
```

#### Private Channels
```python
# Send to specific user
realtime_service.trigger_event(
    channel=f'private-user-{user_id}',
    event='notification',
    data={'message': 'Personal notification'}
)
```

#### Presence Channels
```python
# Team collaboration with online status
realtime_service.trigger_event(
    channel=f'presence-team-{team_id}',
    event='team-update',
    data={'update': 'Team message'}
)
```

### Event Types
- `notification` - General notification
- `lead-created` - New lead created
- `lead-updated` - Lead information updated
- `lead-assigned` - Lead assigned to user
- `project-created` - New project created
- `project-updated` - Project status changed
- `appointment-created` - New appointment
- `appointment-rescheduled` - Appointment time changed
- `message` - Direct message

## User Preferences

### Managing Preferences
```python
from app.models.notification import NotificationPreferences

# Get user preferences
prefs = get_user_preferences(user_id)

# Update preferences
prefs = {
    'email_enabled': True,
    'sms_enabled': True,
    'push_enabled': True,
    'quiet_hours_enabled': True,
    'quiet_hours_start': 22,  # 10 PM
    'quiet_hours_end': 8,      # 8 AM
    'notification_types': {
        'leads': True,
        'appointments': True,
        'projects': True,
        'reviews': False
    }
}
update_user_preferences(user_id, prefs)
```

### Respecting Quiet Hours
The service automatically respects user quiet hours:
```python
# Notification will be queued if in quiet hours
notification_service.send_notification(
    type='lead_new',
    data={...},
    recipient_id='user-uuid',
    respect_quiet_hours=True  # Default
)
```

## Delivery Tracking

### Email Tracking
```python
# Get email delivery status
from app.services.email_service import email_service

activity = email_service.get_email_activity(message_id)
# Returns: {
#     'status': 'delivered',
#     'opens': 2,
#     'clicks': 1,
#     'bounced': False
# }
```

### SMS Tracking
```python
# Get SMS delivery status
from app.services.sms_service import sms_service

status = sms_service.get_sms_status(message_sid)
# Returns: {
#     'status': 'delivered',
#     'error_code': None,
#     'delivered_at': '2025-01-15T10:30:00Z'
# }
```

## Error Handling

### Retry Logic
```python
# Automatic retry with exponential backoff
notification_service = NotificationService(
    max_retries=3,
    retry_delay=60  # seconds
)
```

### Error Responses
```python
success, error = notification_service.send_notification(...)

if not success:
    print(f"Notification failed: {error}")
    # Error types:
    # - "Invalid recipient"
    # - "Template not found"
    # - "Service unavailable"
    # - "Rate limit exceeded"
    # - "Invalid phone number"
    # - "Unsubscribed recipient"
```

## Bulk Operations

### Sending Bulk Emails
```python
from app.services.email_service import email_service

recipients = [
    {
        'email': 'customer1@example.com',
        'substitutions': {'name': 'John', 'project': 'Roof Repair'}
    },
    {
        'email': 'customer2@example.com',
        'substitutions': {'name': 'Jane', 'project': 'Full Replacement'}
    }
]

result = email_service.send_bulk_emails(
    recipients=recipients,
    subject='Project Update',
    html_content='<p>Hi {name}, your project "{project}" is scheduled.</p>'
)
```

### Sending Bulk SMS
```python
from app.services.sms_service import sms_service

recipients = [
    {'phone': '+12485551234', 'name': 'John'},
    {'phone': '+12485555678', 'name': 'Jane'}
]

results = sms_service.send_bulk_sms(
    recipients=recipients,
    template='appointment_reminder',
    template_data={'time': '10:00 AM', 'date': 'tomorrow'}
)
```

## Performance Optimization

### Caching
```python
# Template caching
from functools import lru_cache

@lru_cache(maxsize=128)
def get_rendered_template(template_key, **kwargs):
    return render_template(template_key, **kwargs)
```

### Batching
```python
# Batch notifications for efficiency
notifications = []
for user in users:
    notifications.append({
        'type': 'announcement',
        'recipient_id': user.id,
        'data': announcement_data
    })

notification_service.send_batch(notifications)
```

### Rate Limiting
```python
# Respect service rate limits
from app.utils.rate_limiter import RateLimiter

limiter = RateLimiter(
    max_requests=100,
    per_seconds=60
)

@limiter.limit
def send_notification():
    # Send notification
    pass
```

## Monitoring & Logging

### Logging Configuration
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Service logs
# INFO: Successful notifications
# WARNING: Retry attempts, service degradation
# ERROR: Failed notifications, service errors
```

### Metrics to Monitor
- Delivery rate by channel
- Average delivery time
- Bounce rate (email)
- Unsubscribe rate
- Click-through rate (email)
- Response rate (SMS)
- Real-time connection count
- Error rate by type

## Testing

### Unit Tests
```python
import pytest
from unittest.mock import Mock, patch

def test_send_email_notification():
    with patch('app.services.email_service.email_service.send_email') as mock_send:
        mock_send.return_value = (True, 'msg-id', {})

        success, error = notification_service.send_notification(
            type='test',
            data={'test': 'data'},
            recipient_id='test-user',
            channels=['email']
        )

        assert success
        assert error is None
        mock_send.assert_called_once()
```

### Integration Tests
```python
def test_full_notification_flow():
    # Test with real services (test environment)
    success, error = notification_service.send_notification(
        type='lead_new',
        data={
            'lead_name': 'Test Lead',
            'source': 'test',
            'score': 85
        },
        recipient_id='test-user-id',
        channels=['email', 'sms', 'push']
    )

    assert success
    # Verify in each service
```

## Troubleshooting

### Common Issues

#### Email Not Delivered
1. Check SendGrid API key
2. Verify sender domain authentication
3. Check recipient email validity
4. Review spam score
5. Check SendGrid logs

#### SMS Not Delivered
1. Check Twilio credentials
2. Verify phone number format (+1XXXXXXXXXX)
3. Check recipient opt-out status
4. Review Twilio error codes
5. Check carrier filtering

#### Real-time Events Not Received
1. Check Pusher credentials
2. Verify channel subscription
3. Check authentication for private channels
4. Review Pusher debug console
5. Check client connection status

### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger('app.services.notification').setLevel(logging.DEBUG)

# Test mode (doesn't send actual notifications)
notification_service = NotificationService(test_mode=True)
```

## Best Practices

1. **Use Templates**: Always use predefined templates for consistency
2. **Respect Preferences**: Check user preferences before sending
3. **Handle Failures**: Implement proper error handling and retries
4. **Track Delivery**: Monitor delivery rates and handle bounces
5. **Optimize Timing**: Send notifications at optimal times
6. **Batch When Possible**: Group notifications for efficiency
7. **Test Thoroughly**: Test all channels and error scenarios
8. **Monitor Usage**: Track API usage and costs
9. **Secure Data**: Never log sensitive information
10. **Document Changes**: Keep templates and types documented

## API Reference

### NotificationService

```python
class NotificationService:
    def send_notification(
        self,
        type: str,
        data: Dict[str, Any],
        recipient_id: Optional[str] = None,
        channels: Optional[List[str]] = None,
        priority: str = 'normal',
        respect_quiet_hours: bool = True
    ) -> Tuple[bool, Optional[str]]

    def schedule_notification(
        self,
        type: str,
        data: Dict[str, Any],
        recipient_id: str,
        send_at: datetime,
        channels: Optional[List[str]] = None,
        priority: str = 'normal'
    ) -> Tuple[bool, Optional[str]]

    def cancel_scheduled_notification(
        self,
        notification_id: str
    ) -> bool

    def get_notification_history(
        self,
        recipient_id: Optional[str] = None,
        type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]
```

---

*Last Updated: 2025-01-15*
*Service Version: 1.0.0*