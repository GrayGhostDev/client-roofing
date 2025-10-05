# Leads API Documentation

## Overview
The Leads API provides comprehensive functionality for managing leads in the iSwitch Roofs CRM system. This includes creating, reading, updating, and deleting leads, as well as specialized operations like lead scoring, assignment, and bulk imports.

## Base URL
```
/api/leads
```

## Authentication
All endpoints require JWT authentication via Bearer token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## Endpoints

### 1. List Leads
Get all leads with filtering, pagination, and sorting.

**Endpoint:** `GET /api/leads/`

**Query Parameters:**
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| page | int | Page number (default: 1) | `page=2` |
| per_page | int | Items per page (max: 100, default: 50) | `per_page=25` |
| sort | string | Sort field:direction | `sort=lead_score:desc` |
| status | string | Comma-separated status values | `status=new,contacted` |
| temperature | string | Comma-separated temperature values | `temperature=hot,warm` |
| source | string | Comma-separated source values | `source=google_ads,website_form` |
| assigned_to | UUID | Filter by assigned team member | `assigned_to=550e8400-e29b...` |
| created_after | ISO date | Filter by creation date | `created_after=2025-01-01` |
| min_score | int | Minimum lead score | `min_score=60` |
| max_score | int | Maximum lead score | `max_score=100` |
| zip_code | string | Filter by ZIP code | `zip_code=48301` |
| converted | boolean | Filter by conversion status | `converted=false` |

**Response (200):**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com",
      "phone": "2485551234",
      "source": "website_form",
      "status": "new",
      "temperature": "hot",
      "lead_score": 85,
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-01T12:00:00Z"
    }
  ],
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

### 2. Get Lead by ID
Get detailed information about a specific lead, including score breakdown.

**Endpoint:** `GET /api/leads/{lead_id}`

**Response (200):**
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "2485551234",
    "source": "website_form",
    "status": "new",
    "temperature": "hot",
    "lead_score": 85,
    "property_value": 550000,
    "zip_code": "48009",
    "created_by": "admin_user_id",
    "created_by_email": "admin@iswitchroofs.com"
  },
  "score_breakdown": {
    "total_score": 85,
    "temperature": "hot",
    "demographics": {
      "property_value": 30,
      "location": 10,
      "income": 15
    },
    "behavioral": {
      "engagement": 15,
      "response_time": 10,
      "interactions": 5
    },
    "bant": {
      "budget": 8,
      "authority": 7,
      "need": 5,
      "timeline": 5
    }
  }
}
```

### 3. Create Lead
Create a new lead with automatic lead scoring.

**Endpoint:** `POST /api/leads/`

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "2485551234",
  "source": "website_form",
  "street_address": "123 Main St",
  "city": "Birmingham",
  "state": "MI",
  "zip_code": "48009",
  "property_value": 550000,
  "urgency": "immediate",
  "project_description": "Need complete roof replacement",
  "budget_range_min": 15000,
  "budget_range_max": 25000,
  "insurance_claim": true
}
```

**Response (201):**
```json
{
  "data": {
    "id": "new_lead_id",
    "lead_score": 85,
    "temperature": "hot",
    "...": "other lead fields"
  },
  "score_breakdown": {
    "total_score": 85,
    "temperature": "hot",
    "...": "scoring details"
  }
}
```

### 4. Update Lead
Update a lead and recalculate its score.

**Endpoint:** `PUT /api/leads/{lead_id}`

**Request Body:**
```json
{
  "status": "contacted",
  "property_value": 600000,
  "urgency": "immediate"
}
```

**Response (200):**
```json
{
  "data": {
    "id": "lead_id",
    "...": "updated lead data"
  },
  "score_breakdown": {
    "...": "new score breakdown"
  }
}
```

### 5. Delete Lead
Soft delete a lead (marks as deleted, doesn't remove from database).

**Endpoint:** `DELETE /api/leads/{lead_id}`

**Response (200):**
```json
{
  "message": "Lead lead_id deleted successfully"
}
```

### 6. Assign Lead to Team Member
Assign a lead to a specific team member or use automatic assignment.

**Endpoint:** `POST /api/leads/{lead_id}/assign`

**Request Body:**
```json
{
  "team_member_id": "550e8400-e29b-41d4-a716-446655440001",
  "force_reassign": false,
  "notes": "High priority lead, needs immediate follow-up",
  "send_notification": true
}
```

**Alternative - Auto Assignment:**
```json
{
  "auto_assign": true,
  "strategy": "round_robin",
  "send_notification": true
}
```

**Response (200):**
```json
{
  "message": "Lead assigned successfully",
  "lead_id": "lead_id",
  "assigned_to": "team_member_id",
  "assigned_at": "2025-01-01T12:00:00Z",
  "status": "contacted"
}
```

### 7. Convert Lead to Customer
Convert a lead to a customer.

**Endpoint:** `POST /api/leads/{lead_id}/convert`

**Request Body:**
```json
{
  "customer_id": "optional_existing_customer_id"
}
```

**Response (200):**
```json
{
  "message": "Lead converted to customer successfully",
  "lead_id": "lead_id",
  "customer_id": "customer_id"
}
```

### 8. Recalculate Lead Score
Manually trigger lead score recalculation.

**Endpoint:** `POST /api/leads/{lead_id}/score`

**Request Body (optional):**
```json
{
  "interaction_count": 5,
  "response_time_minutes": 2,
  "budget_confirmed": true,
  "is_decision_maker": true
}
```

**Response (200):**
```json
{
  "data": {
    "...": "lead data with new score"
  },
  "score_breakdown": {
    "...": "detailed score breakdown"
  }
}
```

### 9. Get Hot Leads
Get all hot leads (score >= 80) requiring immediate action.

**Endpoint:** `GET /api/leads/hot`

**Response (200):**
```json
{
  "data": [
    {
      "...": "hot lead data"
    }
  ],
  "count": 15
}
```

### 10. Get Lead Statistics
Get aggregate statistics and KPIs for leads.

**Endpoint:** `GET /api/leads/stats`

**Response (200):**
```json
{
  "total_leads": 500,
  "by_temperature": {
    "hot": 50,
    "warm": 150,
    "cool": 200,
    "cold": 100
  },
  "by_status": {
    "new": 100,
    "qualified": 200
  },
  "conversion": {
    "converted_count": 125,
    "conversion_rate": 25.0
  }
}
```

### 11. Bulk Import Leads
Import multiple leads from a CSV or Excel file.

**Endpoint:** `POST /api/leads/bulk-import`

**Request:** Multipart form data

**Form Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | file | Yes | CSV or Excel file containing leads |
| skip_duplicates | boolean | No | Skip leads with duplicate emails (default: true) |
| auto_score | boolean | No | Automatically calculate lead scores (default: true) |
| validate_strict | boolean | No | Use strict validation mode (default: false) |
| field_mapping | JSON | No | Custom field mapping object |
| max_rows | int | No | Maximum rows to import (default: 10000) |

**CSV Format Example:**
```csv
first_name,last_name,email,phone,source,street_address,city,state,zip_code,property_value
John,Doe,john@example.com,2485551234,website_form,123 Main St,Birmingham,MI,48009,550000
Jane,Smith,jane@example.com,2485555678,google_ads,456 Oak Ave,Troy,MI,48084,450000
```

**Field Mapping Example:**
```json
{
  "Name": "full_name",
  "Email Address": "email",
  "Phone Number": "phone",
  "Lead Source": "source"
}
```

**Response (201/207):**
```json
{
  "import_id": "import_batch_id",
  "total_imported": 100,
  "success": 95,
  "failed": 3,
  "duplicates": 2,
  "imported_leads": [
    {
      "id": "lead_id",
      "name": "John Doe",
      "score": 85
    }
  ],
  "errors": [
    {
      "row": 5,
      "error": "Invalid email format",
      "data": {...}
    }
  ]
}
```

## Error Responses

### 400 Bad Request
```json
{
  "error": "Validation error",
  "details": "Invalid email format"
}
```

### 401 Unauthorized
```json
{
  "error": "Authentication required"
}
```

### 404 Not Found
```json
{
  "error": "Lead not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Failed to create lead",
  "details": "Database connection error"
}
```

## Rate Limiting
- 1000 requests per hour per user
- 100 bulk import operations per day

## Webhooks
The following events trigger webhooks:
- `lead.created` - New lead created
- `lead.updated` - Lead information updated
- `lead.assigned` - Lead assigned to team member
- `lead.converted` - Lead converted to customer
- `bulk_import.complete` - Bulk import operation completed

## Best Practices

1. **Pagination**: Always use pagination for list endpoints
2. **Filtering**: Use filters to reduce payload size
3. **Bulk Operations**: Use bulk import for multiple leads
4. **Caching**: Cache frequently accessed lead data
5. **Error Handling**: Implement retry logic for failed requests
6. **Audit**: All operations are logged with audit fields

## Examples

### cURL Examples

**Get all hot leads:**
```bash
curl -X GET "https://api.iswitchroofs.com/api/leads/hot" \
  -H "Authorization: Bearer your_token"
```

**Create a new lead:**
```bash
curl -X POST "https://api.iswitchroofs.com/api/leads/" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "2485551234",
    "source": "website_form"
  }'
```

**Bulk import from CSV:**
```bash
curl -X POST "https://api.iswitchroofs.com/api/leads/bulk-import" \
  -H "Authorization: Bearer your_token" \
  -F "file=@leads.csv" \
  -F "auto_score=true" \
  -F "skip_duplicates=true"
```

## Related Documentation
- [Lead Scoring Algorithm](../LEAD_SCORING.md)
- [Authentication](../AUTHENTICATION.md)
- [Audit Fields](../AUDIT_FIELDS.md)
- [Webhooks](../WEBHOOKS.md)