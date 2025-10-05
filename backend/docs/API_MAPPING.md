# iSwitch Roofs CRM - API Endpoint Mapping Documentation

## Overview
Complete mapping of all frontend components to their required backend API endpoints.

**Status**: ⚠️ API endpoints exist but are non-functional due to missing database tables

## API Base URL
- Development: `http://localhost:8001`
- Production: `TBD`

## Authentication
All endpoints require authentication except `/api/auth/login` and `/api/health`
- Token-based authentication using JWT
- Token should be sent in Authorization header: `Bearer <token>`

## Component-to-API Mapping

### 1. Dashboard Components

#### **dashboard** (Main Dashboard)
- `GET /api/analytics/dashboard` - Get dashboard metrics
- `GET /api/analytics/kpis` - Get KPI data
- `GET /api/activities/recent` - Get recent activities
- `GET /api/notifications/unread` - Get unread notifications

#### **metric_cards**
- `GET /api/analytics/metrics` - Get metric card data
- `GET /api/analytics/trends` - Get trend data for metrics

#### **recent_activity**
- `GET /api/activities/recent?limit=10` - Get recent activities
- `POST /api/activities/mark-read` - Mark activities as read

### 2. Lead Management

#### **leads_page**
- `GET /api/leads` - List all leads with pagination
- `GET /api/leads/stats` - Get lead statistics
- `GET /api/leads/filters` - Get available filters

#### **lead_table**
- `GET /api/leads?page=1&size=50` - Paginated lead list
- `PUT /api/leads/{id}` - Update lead
- `DELETE /api/leads/{id}` - Delete lead
- `POST /api/leads/bulk-action` - Bulk operations

#### **new_lead_wizard**
- `POST /api/leads` - Create new lead
- `GET /api/leads/duplicate-check` - Check for duplicates
- `POST /api/leads/score` - Calculate lead score
- `GET /api/team/members` - Get assignable team members

#### **lead_kanban**
- `GET /api/leads/pipeline` - Get pipeline stages
- `PUT /api/leads/{id}/stage` - Update lead stage
- `GET /api/leads/by-stage` - Get leads grouped by stage

#### **lead_scoring_display**
- `GET /api/leads/{id}/score-breakdown` - Get score details
- `PUT /api/leads/{id}/score` - Update lead score
- `GET /api/leads/scoring-rules` - Get scoring configuration

### 3. Customer Management

#### **customers_page**
- `GET /api/customers` - List all customers
- `GET /api/customers/stats` - Get customer statistics
- `GET /api/customers/segments` - Get customer segments

#### **customer_table**
- `GET /api/customers?page=1&size=50` - Paginated customer list
- `PUT /api/customers/{id}` - Update customer
- `DELETE /api/customers/{id}` - Delete customer
- `GET /api/customers/{id}/history` - Get customer history

#### **customer_detail_modal**
- `GET /api/customers/{id}` - Get customer details
- `GET /api/customers/{id}/projects` - Get customer projects
- `GET /api/customers/{id}/interactions` - Get interaction history
- `GET /api/customers/{id}/reviews` - Get customer reviews

#### **customer_analytics**
- `GET /api/customers/{id}/analytics` - Get customer analytics
- `GET /api/customers/{id}/lifetime-value` - Get LTV data
- `GET /api/customers/{id}/referrals` - Get referral data

### 4. Projects

#### **projects_module**
- `GET /api/projects` - List all projects
- `GET /api/projects/stats` - Get project statistics
- `GET /api/projects/timeline` - Get timeline data

#### **project_kanban**
- `GET /api/projects/by-status` - Get projects by status
- `PUT /api/projects/{id}/status` - Update project status
- `POST /api/projects/{id}/tasks` - Add project tasks

#### **project_timeline**
- `GET /api/projects/gantt` - Get Gantt chart data
- `PUT /api/projects/{id}/schedule` - Update project schedule
- `GET /api/projects/milestones` - Get project milestones

#### **project_detail_modal**
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `GET /api/projects/{id}/team` - Get project team
- `POST /api/projects/{id}/notes` - Add project notes

### 5. Appointments

#### **appointments_dashboard**
- `GET /api/appointments/dashboard` - Get appointment dashboard data
- `GET /api/appointments/today` - Get today's appointments
- `GET /api/appointments/week` - Get this week's appointments
- `GET /api/team/availability` - Get team availability

#### **appointment_calendar**
- `GET /api/appointments/calendar` - Get calendar view data
- `GET /api/appointments/month` - Get monthly appointments
- `POST /api/appointments/recurring` - Create recurring appointments

#### **appointment_scheduler**
- `POST /api/appointments` - Create appointment
- `GET /api/appointments/slots` - Get available time slots
- `GET /api/appointments/conflicts` - Check for conflicts
- `POST /api/appointments/reschedule` - Reschedule appointment

#### **appointment_detail_modal**
- `GET /api/appointments/{id}` - Get appointment details
- `PUT /api/appointments/{id}` - Update appointment
- `DELETE /api/appointments/{id}` - Cancel appointment
- `POST /api/appointments/{id}/confirm` - Confirm appointment

### 6. Settings

#### **settings_page**
- `GET /api/settings` - Get all settings
- `PUT /api/settings` - Update settings
- `GET /api/settings/activity` - Get settings change history

#### **user_profile**
- `GET /api/users/profile` - Get user profile
- `PUT /api/users/profile` - Update profile
- `POST /api/users/change-password` - Change password
- `POST /api/users/upload-avatar` - Upload avatar

#### **team_management**
- `GET /api/team` - List team members
- `POST /api/team` - Add team member
- `PUT /api/team/{id}` - Update team member
- `DELETE /api/team/{id}` - Remove team member
- `GET /api/team/{id}/performance` - Get member performance

#### **notification_settings**
- `GET /api/notifications/settings` - Get notification preferences
- `PUT /api/notifications/settings` - Update preferences
- `GET /api/notifications/channels` - Get available channels
- `POST /api/notifications/test` - Test notification

#### **integrations**
- `GET /api/integrations` - List integrations
- `POST /api/integrations/{type}/connect` - Connect integration
- `DELETE /api/integrations/{id}` - Disconnect integration
- `GET /api/integrations/{id}/status` - Check integration status

### 7. Analytics

#### **analytics_dashboard**
- `GET /api/analytics/overview` - Get analytics overview
- `GET /api/analytics/revenue` - Get revenue analytics
- `GET /api/analytics/conversion` - Get conversion metrics
- `GET /api/analytics/performance` - Get performance data

#### **revenue_charts**
- `GET /api/analytics/revenue/daily` - Daily revenue data
- `GET /api/analytics/revenue/monthly` - Monthly revenue data
- `GET /api/analytics/revenue/yearly` - Yearly revenue data
- `GET /api/analytics/revenue/forecast` - Revenue forecast

#### **conversion_funnel**
- `GET /api/analytics/funnel` - Get funnel data
- `GET /api/analytics/funnel/stages` - Get stage metrics
- `GET /api/analytics/funnel/dropoff` - Get dropoff analysis

#### **team_performance**
- `GET /api/analytics/team` - Team performance metrics
- `GET /api/analytics/team/{id}` - Individual performance
- `GET /api/analytics/team/leaderboard` - Team leaderboard

## Real-time Endpoints (Pusher)

### Channels
- `private-user-{userId}` - User-specific updates
- `private-team-{teamId}` - Team updates
- `presence-dashboard` - Dashboard presence
- `private-notifications` - Real-time notifications

### Events
- `lead.created` - New lead added
- `lead.updated` - Lead information updated
- `appointment.reminder` - Appointment reminder
- `notification.new` - New notification
- `activity.new` - New activity

## Error Response Format
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {}
  },
  "timestamp": "2025-10-05T10:00:00Z"
}
```

## Success Response Format
```json
{
  "data": {},
  "message": "Operation successful",
  "timestamp": "2025-10-05T10:00:00Z"
}
```

## Pagination Format
```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "size": 50,
    "total": 500,
    "totalPages": 10
  }
}
```

## Current Issues

### ❌ Critical Blockers
1. **Database tables don't exist** - Preventing all CRUD operations
2. **Models use Pydantic instead of SQLAlchemy** - Cannot interact with DB
3. **Missing dependencies** - Some routes can't register

### ⚠️ Import Errors
1. `SupabaseClient` import error in partnership routes
2. Notification model references broken
3. Authentication service imports failing

## Testing Endpoints

### With cURL
```bash
# Health check
curl http://localhost:8001/api/health

# Get leads (will fail without auth/DB)
curl http://localhost:8001/api/leads \
  -H "Authorization: Bearer <token>"

# Create lead (will fail without DB)
curl -X POST http://localhost:8001/api/leads \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"first_name":"John","last_name":"Doe","phone":"555-0123"}'
```

### With HTTPie
```bash
# Health check
http GET localhost:8001/api/health

# Get leads
http GET localhost:8001/api/leads \
  Authorization:"Bearer <token>"

# Create lead
http POST localhost:8001/api/leads \
  first_name=John last_name=Doe phone=555-0123 \
  Authorization:"Bearer <token>"
```

## Next Steps

1. **Execute database migration** to create tables
2. **Convert models to SQLAlchemy** for ORM functionality
3. **Fix import errors** in service layer
4. **Implement authentication** with JWT tokens
5. **Add request validation** with Pydantic schemas
6. **Enable CORS** for frontend access
7. **Add rate limiting** for API protection
8. **Implement caching** for performance

## Notes

- All endpoints return 404 currently due to registration failures
- Frontend components are fully functional but can't persist data
- Real-time features via Pusher are configured but not active
- Authentication middleware is not yet implemented