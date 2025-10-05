# API Overview

## Introduction
The iSwitch Roofs CRM API is a RESTful web service that provides comprehensive functionality for managing leads, customers, projects, and business operations for a roofing company. Built with Flask and backed by PostgreSQL (via Supabase), it offers real-time updates, automated workflows, and integrations with industry-leading services.

## Base URL
```
Development: http://localhost:5000/api
Staging: https://staging-api.iswitchroofs.com/api
Production: https://api.iswitchroofs.com/api
```

## Authentication
All API endpoints (except health checks) require authentication using JWT tokens.

### Getting a Token
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

### Using the Token
Include the token in the Authorization header:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

See [Authentication Guide](./AUTHENTICATION.md) for details.

## API Endpoints

### Core Resources

| Resource | Base Path | Description |
|----------|-----------|-------------|
| [Leads](./endpoints/LEADS_API.md) | `/api/leads` | Lead management and scoring |
| [Customers](./endpoints/CUSTOMERS_API.md) | `/api/customers` | Customer profiles and history |
| [Projects](./endpoints/PROJECTS_API.md) | `/api/projects` | Roofing projects and workflows |
| [Interactions](./endpoints/INTERACTIONS_API.md) | `/api/interactions` | Communication tracking |
| [Appointments](./endpoints/APPOINTMENTS_API.md) | `/api/appointments` | Scheduling and calendar |
| [Analytics](./endpoints/ANALYTICS_API.md) | `/api/analytics` | Reports and metrics |
| [Team](./endpoints/TEAM_API.md) | `/api/team` | Team member management |
| [Reviews](./endpoints/REVIEWS_API.md) | `/api/reviews` | Customer reviews |
| [Partnerships](./endpoints/PARTNERSHIPS_API.md) | `/api/partnerships` | Partner relationships |

### Health & Status

#### Health Check
```http
GET /health

Response:
{
  "status": "healthy",
  "service": "iswitch-roofs-crm-api"
}
```

#### API Info
```http
GET /

Response:
{
  "service": "iSwitch Roofs CRM API",
  "version": "1.0.0",
  "status": "running",
  "docs": "/api/docs"
}
```

## Request Format

### Headers
```http
Content-Type: application/json
Authorization: Bearer <token>
Accept: application/json
X-Request-ID: <optional-request-id>
```

### Request Body
All POST, PUT, and PATCH requests should send JSON:
```json
{
  "field1": "value1",
  "field2": "value2"
}
```

### Query Parameters
List endpoints support standard query parameters:
- `page` - Page number (1-indexed)
- `per_page` - Items per page (max: 100)
- `sort` - Sort field and direction (e.g., `created_at:desc`)
- `fields` - Comma-separated fields to include
- Various filters specific to each endpoint

## Response Format

### Success Response
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "...": "..."
  }
}
```

### List Response with Pagination
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 150,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

### Error Response
```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {
    "field": "Additional error details"
  }
}
```

## Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 204 | No Content | Request successful, no content |
| 207 | Multi-Status | Partial success (bulk operations) |
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict |
| 422 | Unprocessable Entity | Validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

## Pagination

All list endpoints support pagination:

```http
GET /api/leads?page=2&per_page=25

Response Headers:
X-Total-Count: 150
X-Page: 2
X-Per-Page: 25
X-Total-Pages: 6
```

## Filtering

Use query parameters to filter results:

```http
GET /api/leads?status=new,contacted&temperature=hot&source=google_ads
```

### Common Filter Operators
- `eq` - Equals (default)
- `neq` - Not equals
- `gt` - Greater than
- `gte` - Greater than or equal
- `lt` - Less than
- `lte` - Less than or equal
- `in` - In list
- `contains` - Contains (text fields)

## Sorting

Sort results by any field:

```http
GET /api/leads?sort=lead_score:desc
GET /api/customers?sort=created_at:asc
```

Multiple sort fields:
```http
GET /api/leads?sort=temperature:desc,created_at:desc
```

## Field Selection

Specify which fields to include:

```http
GET /api/leads?fields=id,first_name,last_name,email,lead_score
```

## Rate Limiting

API rate limits per user:
- 1,000 requests per hour
- 10,000 requests per day
- 100 concurrent requests
- 10 MB max request size

Headers in response:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Webhooks

Register webhooks to receive real-time event notifications:

```http
POST /api/webhooks
{
  "url": "https://your-app.com/webhook",
  "events": ["lead.created", "lead.converted"],
  "secret": "webhook_secret"
}
```

### Available Events
- `lead.*` - Lead events
- `customer.*` - Customer events
- `project.*` - Project events
- `appointment.*` - Appointment events
- `review.*` - Review events

## Real-time Updates

Real-time updates via Pusher WebSocket:

```javascript
const pusher = new Pusher('app_key', {
  cluster: 'us2',
  auth: {
    headers: {
      Authorization: 'Bearer ' + token
    }
  }
});

const channel = pusher.subscribe('leads');
channel.bind('lead-created', function(data) {
  console.log('New lead:', data);
});
```

## Batch Operations

Some endpoints support batch operations:

```http
POST /api/leads/batch
{
  "operations": [
    {"method": "create", "data": {...}},
    {"method": "update", "id": "...", "data": {...}},
    {"method": "delete", "id": "..."}
  ]
}
```

## Audit Fields

All resources include audit fields:
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp
- `created_by` - User ID who created
- `created_by_email` - Email of creator
- `updated_by` - User ID who updated
- `updated_by_email` - Email of updater

See [Audit Fields](./AUDIT_FIELDS.md) for details.

## Error Handling

### Error Response Format
```json
{
  "error": "Human-readable error message",
  "code": "MACHINE_READABLE_CODE",
  "details": {
    "field_name": "Field-specific error"
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Common Error Codes
- `VALIDATION_ERROR` - Request validation failed
- `AUTHENTICATION_REQUIRED` - Missing or invalid token
- `PERMISSION_DENIED` - Insufficient permissions
- `RESOURCE_NOT_FOUND` - Resource doesn't exist
- `DUPLICATE_RESOURCE` - Resource already exists
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `INTERNAL_ERROR` - Server error

## SDK & Client Libraries

### Official SDKs
- JavaScript/TypeScript: `npm install @iswitchroofs/crm-sdk`
- Python: `pip install iswitchroofs-crm`
- PHP: `composer require iswitchroofs/crm-sdk`

### Example Usage (JavaScript)
```javascript
import { ISwitchRoofsCRM } from '@iswitchroofs/crm-sdk';

const client = new ISwitchRoofsCRM({
  apiKey: 'your_api_key',
  environment: 'production'
});

// Create a lead
const lead = await client.leads.create({
  firstName: 'John',
  lastName: 'Doe',
  email: 'john@example.com',
  phone: '2485551234',
  source: 'website_form'
});

// Get hot leads
const hotLeads = await client.leads.list({
  temperature: 'hot',
  sort: 'lead_score:desc'
});
```

## Testing

### Test Environment
```
Base URL: https://sandbox-api.iswitchroofs.com/api
Test Credentials: Available in developer portal
```

### Postman Collection
Import our Postman collection for easy API testing:
[Download Postman Collection](./postman_collection.json)

### cURL Examples
See individual endpoint documentation for cURL examples.

## Versioning

The API uses URL versioning. The current version is v1.

Future versions:
```
/api/v2/leads
/api/v3/leads
```

## Deprecation Policy

- Deprecated features marked with `X-Deprecated` header
- 6-month deprecation notice
- Migration guides provided
- Backward compatibility maintained during deprecation

## Support

### Documentation
- [Full API Reference](./endpoints/)
- [Authentication Guide](./AUTHENTICATION.md)
- [Webhooks Guide](./WEBHOOKS.md)
- [Error Codes](./ERROR_CODES.md)

### Developer Resources
- [GitHub Repository](https://github.com/iswitchroofs/crm-api)
- [API Status Page](https://status.iswitchroofs.com)
- [Developer Portal](https://developers.iswitchroofs.com)

### Contact
- **Email:** api-support@iswitchroofs.com
- **Slack:** #api-support
- **Response Time:** < 24 hours

## Changelog

### v1.0.0 (2025-01-01)
- Initial release
- Core CRUD operations for all resources
- Lead scoring algorithm
- Real-time notifications
- Bulk import functionality
- Third-party integrations

---

Last Updated: 2025-01-01
API Version: 1.0.0