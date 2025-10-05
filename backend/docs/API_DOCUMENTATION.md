# iSwitch Roofs CRM API Documentation

## Overview
Complete REST API documentation for the iSwitch Roofs CRM system built with Flask, Supabase, and Pusher.

**Base URL:** `http://localhost:5000/api`
**Production URL:** `https://api.iswitchroofs.com/api`
**Authentication:** JWT Bearer Token
**Content-Type:** `application/json`

## Table of Contents
1. [Authentication](#authentication)
2. [Customer API](#customer-api)
3. [Projects API](#projects-api)
4. [Interactions API](#interactions-api)
5. [Leads API](#leads-api)
6. [Notification Services](#notification-services)
7. [Real-time Events](#real-time-events)
8. [Error Handling](#error-handling)

---

## Authentication

All API endpoints require authentication using JWT Bearer tokens.

### Headers Required
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### Obtaining a Token
```http
POST /api/auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1Q...",
  "refresh_token": "eyJ0eXAiOiJKV1Q...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "admin"
  }
}
```

---

## Customer API

Complete customer management with lifecycle tracking, segmentation, and insights.

### List Customers
```http
GET /api/customers/
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 50, max: 100)
- `status` (string): Filter by status (comma-separated)
- `segment` (string): Filter by segment (comma-separated)
- `assigned_to` (string): Filter by assigned user ID
- `min_lifetime_value` (float): Minimum LTV filter
- `zip_code` (string): Filter by zip code
- `city` (string): Filter by city
- `is_referral_partner` (boolean): Filter referral partners
- `tags` (string): Filter by tags (comma-separated)
- `sort` (string): Sort field:direction (e.g., "created_at:desc")

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "first_name": "Jane",
      "last_name": "Smith",
      "email": "jane@example.com",
      "phone": "248-555-0100",
      "street_address": "456 Oak Ave",
      "city": "Birmingham",
      "state": "MI",
      "zip_code": "48009",
      "customer_type": "residential",
      "status": "active",
      "segment": "premium",
      "lifetime_value": 75000.00,
      "total_projects": 3,
      "last_interaction": "2025-01-15T10:30:00Z",
      "customer_since": "2023-06-15T00:00:00Z",
      "created_at": "2023-06-15T00:00:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 245,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

### Get Customer Details
```http
GET /api/customers/{customer_id}
```

**Query Parameters:**
- `include_history` (boolean): Include interaction history
- `include_projects` (boolean): Include project list

**Response:**
```json
{
  "id": "uuid",
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane@example.com",
  "phone": "248-555-0100",
  "street_address": "456 Oak Ave",
  "city": "Birmingham",
  "state": "MI",
  "zip_code": "48009",
  "customer_type": "residential",
  "status": "active",
  "segment": "premium",
  "lifetime_value": 75000.00,
  "total_projects": 3,
  "average_project_value": 25000.00,
  "referral_source": "existing_customer",
  "nps_score": 9,
  "last_interaction": "2025-01-15T10:30:00Z",
  "customer_since": "2023-06-15T00:00:00Z",
  "insights": {
    "total_value": 75000,
    "projects_count": 3,
    "average_project_value": 25000,
    "last_project_date": "2024-11-01",
    "referrals_generated": 5,
    "review_rating": 4.8,
    "is_repeat_customer": true,
    "days_since_last_project": 75
  },
  "projects": [...],
  "history": [...]
}
```

### Create Customer
```http
POST /api/customers/
```

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "248-555-0101",
  "street_address": "789 Maple St",
  "city": "Troy",
  "state": "MI",
  "zip_code": "48084",
  "property_value": 550000,
  "customer_type": "residential",
  "referral_source": "google_ads",
  "lead_id": "optional-lead-uuid",
  "notes": "High-value property, interested in premium materials"
}
```

**Response:** 201 Created
```json
{
  "id": "new-uuid",
  "first_name": "John",
  "last_name": "Doe",
  ...
}
```

### Update Customer
```http
PUT /api/customers/{customer_id}
```

**Request Body:** (Partial updates supported)
```json
{
  "email": "newemail@example.com",
  "phone": "248-555-0102",
  "segment": "vip",
  "tags": ["premium", "referral_partner"]
}
```

**Response:** 200 OK

### Delete Customer (Soft Delete)
```http
DELETE /api/customers/{customer_id}
```

**Response:** 200 OK
```json
{
  "message": "Customer deleted successfully"
}
```

### Get Customer Projects
```http
GET /api/customers/{customer_id}/projects
```

**Response:**
```json
{
  "data": [
    {
      "id": "project-uuid",
      "name": "Complete Roof Replacement",
      "status": "completed",
      "project_type": "replacement",
      "estimated_value": 25000,
      "actual_value": 24500,
      "start_date": "2024-10-01",
      "end_date": "2024-10-05",
      "profit_margin": 42.5
    }
  ]
}
```

### Get Customer Interactions
```http
GET /api/customers/{customer_id}/interactions
```

**Query Parameters:**
- `limit` (int): Number of interactions to return (default: 50)

**Response:**
```json
{
  "data": [
    {
      "id": "interaction-uuid",
      "interaction_type": "phone_call",
      "direction": "outbound",
      "status": "completed",
      "interaction_time": "2025-01-15T10:30:00Z",
      "duration_minutes": 15,
      "summary": "Discussed upcoming maintenance needs",
      "created_by": "user-uuid"
    }
  ]
}
```

### Calculate Lifetime Value
```http
GET /api/customers/{customer_id}/ltv
```

**Response:**
```json
{
  "lifetime_value": 75000.00,
  "total_projects": 3,
  "average_project_value": 25000.00,
  "project_frequency_days": 365,
  "estimated_future_value": 25000.00
}
```

---

## Projects API

Complete project management with scheduling, profitability tracking, and resource allocation.

### List Projects
```http
GET /api/projects/
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 50, max: 100)
- `status` (string): Filter by status (comma-separated)
- `type` (string): Filter by project type
- `customer_id` (string): Filter by customer
- `assigned_to` (string): Filter by assigned user
- `priority` (string): Filter by priority (high, medium, low)
- `start_date_from` (date): Start date range filter
- `start_date_to` (date): End date range filter
- `min_value` (float): Minimum project value
- `max_value` (float): Maximum project value
- `is_delayed` (boolean): Filter delayed projects
- `sort` (string): Sort field:direction

**Response:**
```json
{
  "data": [
    {
      "id": "project-uuid",
      "customer_id": "customer-uuid",
      "name": "Complete Roof Replacement",
      "description": "Full tear-off and replacement with architectural shingles",
      "status": "in_progress",
      "project_type": "replacement",
      "priority": "high",
      "estimated_value": 28000,
      "actual_value": null,
      "materials_cost": 12000,
      "labor_cost": 8000,
      "profit_margin": 28.5,
      "start_date": "2025-01-20",
      "end_date": "2025-01-24",
      "assigned_to": "user-uuid",
      "created_at": "2025-01-10T09:00:00Z",
      "updated_at": "2025-01-15T14:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 89,
    "total_pages": 2,
    "has_next": true,
    "has_prev": false
  },
  "stats": {
    "total_projects": 89,
    "active_projects": 12,
    "completed_projects": 65,
    "total_value": 1750000,
    "average_value": 19662.92
  }
}
```

### Get Project Details
```http
GET /api/projects/{project_id}
```

**Query Parameters:**
- `include` (string): Comma-separated list of related data to include
  - Options: `timeline`, `profitability`, `resources`, `documents`, `history`

**Response:**
```json
{
  "id": "project-uuid",
  "customer_id": "customer-uuid",
  "name": "Complete Roof Replacement",
  "description": "Full tear-off and replacement with architectural shingles",
  "status": "in_progress",
  "project_type": "replacement",
  "priority": "high",
  "estimated_value": 28000,
  "materials_cost": 12000,
  "labor_cost": 8000,
  "subcontractor_cost": 2000,
  "permit_cost": 500,
  "other_costs": 500,
  "profit_margin": 28.5,
  "square_feet": 2500,
  "start_date": "2025-01-20",
  "end_date": "2025-01-24",
  "assigned_to": "user-uuid",
  "assigned_crew": "crew-uuid",
  "customer": {
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane@example.com",
    "phone": "248-555-0100"
  },
  "timeline": {
    "project_id": "project-uuid",
    "start_date": "2025-01-20",
    "end_date": "2025-01-24",
    "duration_days": 5,
    "progress_percentage": 40,
    "is_delayed": false,
    "days_remaining": 3,
    "milestones": [
      {
        "name": "Material Ordering",
        "target_days": 2,
        "completed": true
      },
      {
        "name": "Tear-off",
        "target_days": 3,
        "completed": false
      }
    ]
  },
  "profitability": {
    "revenue": 28000,
    "costs": {
      "materials": 12000,
      "labor": 8000,
      "subcontractor": 2000,
      "permits": 500,
      "other": 500,
      "total": 23000
    },
    "gross_profit": 5000,
    "gross_margin_percentage": 17.86,
    "roi_percentage": 21.74,
    "profitability_status": "fair"
  }
}
```

### Create Project
```http
POST /api/projects/
```

**Request Body:**
```json
{
  "customer_id": "customer-uuid",
  "name": "Roof Repair - Storm Damage",
  "description": "Emergency repair of storm damage to north section",
  "project_type": "repair",
  "priority": "high",
  "estimated_value": 5000,
  "materials_cost": 1500,
  "labor_cost": 2000,
  "square_feet": 500,
  "assigned_to": "user-uuid"
}
```

**Response:** 201 Created

### Update Project
```http
PUT /api/projects/{project_id}
```

**Request Body:** (Partial updates supported)
```json
{
  "status": "completed",
  "actual_value": 27500,
  "end_date": "2025-01-23"
}
```

**Response:** 200 OK

### Get Project Timeline
```http
GET /api/projects/{project_id}/timeline
```

**Response:**
```json
{
  "project_id": "project-uuid",
  "start_date": "2025-01-20",
  "end_date": "2025-01-24",
  "duration_days": 5,
  "progress_percentage": 40,
  "is_delayed": false,
  "days_remaining": 3,
  "milestones": [...]
}
```

### Calculate Project Profitability
```http
GET /api/projects/{project_id}/profitability
```

**Response:**
```json
{
  "project_id": "project-uuid",
  "revenue": 28000,
  "costs": {
    "materials": 12000,
    "labor": 8000,
    "subcontractor": 2000,
    "permits": 500,
    "other": 500,
    "total": 23000
  },
  "gross_profit": 5000,
  "gross_margin_percentage": 17.86,
  "roi_percentage": 21.74,
  "cost_breakdown": {
    "materials_percentage": 52.17,
    "labor_percentage": 34.78,
    "other_percentage": 13.04
  },
  "profitability_status": "fair"
}
```

### Schedule Project
```http
POST /api/projects/{project_id}/schedule
```

**Request Body:**
```json
{
  "start_date": "2025-01-25T08:00:00Z",
  "crew_id": "crew-uuid"
}
```

**Response:**
```json
{
  "project_id": "project-uuid",
  "start_date": "2025-01-25T08:00:00Z",
  "end_date": "2025-01-29T17:00:00Z",
  "duration_days": 5,
  "crew_id": "crew-uuid",
  "status": "scheduled"
}
```

### Manage Project Documents
```http
GET /api/projects/{project_id}/documents
POST /api/projects/{project_id}/documents
```

**POST Request Body:**
```json
{
  "name": "Contract.pdf",
  "type": "contract",
  "url": "https://storage.supabase.co/...",
  "description": "Signed contract with customer"
}
```

### Get Projects Overview Statistics
```http
GET /api/projects/stats/overview
```

**Query Parameters:**
- `period` (string): Time period - week, month, quarter, year
- `assigned_to` (string): Filter by assigned user

**Response:**
```json
{
  "period": "month",
  "total_projects": 45,
  "completed_projects": 32,
  "active_projects": 8,
  "scheduled_projects": 5,
  "completion_rate": 71.11,
  "total_estimated_value": 890000,
  "total_actual_value": 785000,
  "total_profit": 156000,
  "average_completion_time_days": 4.2,
  "projects_by_type": {
    "replacement": 25,
    "repair": 15,
    "inspection": 5
  },
  "projects_by_priority": {
    "high": 10,
    "medium": 25,
    "low": 10
  },
  "delayed_projects": 2
}
```

---

## Interactions API

Communication tracking and management for leads and customers.

### Create Interaction
```http
POST /api/interactions/
```

**Request Body:**
```json
{
  "customer_id": "customer-uuid",
  "interaction_type": "phone_call",
  "direction": "outbound",
  "status": "completed",
  "interaction_time": "2025-01-15T10:30:00Z",
  "start_time": "2025-01-15T10:30:00Z",
  "end_time": "2025-01-15T10:45:00Z",
  "summary": "Discussed project timeline and materials",
  "notes": "Customer prefers GAF shingles",
  "follow_up_required": true,
  "follow_up_date": "2025-01-17T09:00:00Z",
  "follow_up_notes": "Send material samples",
  "assigned_to": "user-uuid"
}
```

**Response:** 201 Created

### Get Interaction History
```http
GET /api/interactions/
```

**Query Parameters:**
- `customer_id` (string): Filter by customer
- `lead_id` (string): Filter by lead
- `interaction_type` (string): Filter by type
- `assigned_to` (string): Filter by assigned user
- `follow_up_required` (boolean): Filter pending follow-ups
- `limit` (int): Maximum results (default: 50)

---

## Notification Services

The system includes comprehensive notification services for email, SMS, and real-time updates.

### Email Service (SendGrid)
- Template-based emails
- Bulk email campaigns
- Scheduled emails
- Email tracking and analytics
- Unsubscribe management

### SMS Service (Twilio)
- SMS notifications
- Two-way SMS support
- SMS templates
- Opt-out management
- Delivery tracking

### Real-time Service (Pusher)
- Instant notifications
- Channel-based broadcasting
- Presence channels for team collaboration
- Event-driven updates

### Notification Templates Available
- Lead notifications (new, hot, assigned)
- Customer notifications (welcome, updates)
- Appointment reminders
- Project status updates
- Review requests
- Team alerts
- System notifications

---

## Real-time Events

The system broadcasts real-time events via Pusher channels.

### Channels

#### Public Channels
- `leads` - Lead updates
- `projects` - Project updates
- `appointments` - Appointment changes

#### Private Channels
- `private-user-{user_id}` - User-specific notifications
- `private-team-{team_id}` - Team notifications

#### Presence Channels
- `presence-team-{team_id}` - Team collaboration with online status

### Event Types
- `lead-created`
- `lead-updated`
- `lead-assigned`
- `project-created`
- `project-updated`
- `project-scheduled`
- `appointment-created`
- `appointment-rescheduled`
- `notification`

### Subscribing to Events
```javascript
// JavaScript client example
const pusher = new Pusher('your-key', {
  cluster: 'us2',
  authEndpoint: '/api/realtime/auth'
});

const channel = pusher.subscribe('leads');
channel.bind('lead-created', function(data) {
  console.log('New lead:', data);
});
```

---

## Error Handling

All API endpoints return consistent error responses.

### Error Response Format
```json
{
  "error": "Error message",
  "details": ["Additional error details"],
  "code": "ERROR_CODE"
}
```

### HTTP Status Codes
- `200 OK` - Request successful
- `201 Created` - Resource created
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate)
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service temporarily unavailable

### Common Error Codes
- `AUTH_REQUIRED` - Authentication required
- `INVALID_TOKEN` - Invalid or expired token
- `PERMISSION_DENIED` - Insufficient permissions
- `VALIDATION_ERROR` - Request validation failed
- `RESOURCE_NOT_FOUND` - Requested resource not found
- `DUPLICATE_RESOURCE` - Resource already exists
- `RATE_LIMIT_EXCEEDED` - Too many requests

---

## Rate Limiting

API endpoints are rate-limited to ensure fair usage.

### Limits
- **Default:** 1000 requests per hour per API key
- **Burst:** 100 requests per minute
- **Webhook endpoints:** 10,000 requests per hour

### Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

---

## Pagination

All list endpoints support pagination.

### Request Parameters
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 50, max: 100)

### Response Format
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 245,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## Webhooks

The system can send webhooks for important events.

### Available Webhook Events
- `lead.created`
- `lead.converted`
- `customer.created`
- `project.completed`
- `appointment.scheduled`
- `review.received`

### Webhook Payload
```json
{
  "event": "lead.created",
  "timestamp": "2025-01-15T10:30:00Z",
  "data": {
    // Event-specific data
  }
}
```

### Webhook Security
All webhooks include an HMAC signature in the `X-Webhook-Signature` header for verification.

---

## Testing

### Test Environment
Base URL: `http://localhost:5000/api`

### Test Credentials
```json
{
  "email": "test@iswitchroofs.com",
  "password": "test123",
  "api_key": "test_token"
}
```

### Postman Collection
A complete Postman collection is available at `/docs/postman_collection.json`

---

## Support

For API support, contact:
- Email: api-support@iswitchroofs.com
- Documentation: https://docs.iswitchroofs.com
- Status Page: https://status.iswitchroofs.com

---

*Last Updated: 2025-01-15*
*API Version: 1.0.0*