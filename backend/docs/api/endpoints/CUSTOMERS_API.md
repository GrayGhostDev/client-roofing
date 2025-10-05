# Customer API Documentation

## Overview
The Customer API provides comprehensive functionality for managing customers in the iSwitch Roofs CRM system. Customers represent converted leads who have completed at least one project. The API includes CRUD operations, lifetime value tracking, segmentation, interaction management, and insights generation.

## Base URL
```
/api/customers
```

## Authentication
All endpoints require JWT authentication via Bearer token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## Data Model

### Customer Status
- `active` - Currently active customer
- `inactive` - No recent activity
- `vip` - High-value customer (LTV > $100K)
- `churned` - No activity in 18+ months

### Customer Segments
- `premium` - High lifetime value (>$50K)
- `standard` - Regular customers
- `repeat` - Multiple projects
- `referral_source` - Active referrers

## Endpoints

### 1. List Customers
Get all customers with filtering, pagination, and sorting.

**Endpoint:** `GET /api/customers/`

**Query Parameters:**
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| page | int | Page number (default: 1) | `page=2` |
| per_page | int | Items per page (max: 100, default: 50) | `per_page=25` |
| sort | string | Sort field:direction | `sort=lifetime_value:desc` |
| status | string | Comma-separated status values | `status=active,vip` |
| segment | string | Comma-separated segment values | `segment=premium,repeat` |
| assigned_to | UUID | Filter by assigned account manager | `assigned_to=550e8400...` |
| min_lifetime_value | int | Minimum lifetime value | `min_lifetime_value=50000` |
| zip_code | string | Filter by ZIP code | `zip_code=48009` |
| city | string | Filter by city | `city=Birmingham` |
| is_referral_partner | boolean | Filter referral partners | `is_referral_partner=true` |
| tags | string | Filter by tags (comma-separated) | `tags=premium,vip` |

**Response (200):**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "first_name": "Jane",
      "last_name": "Smith",
      "email": "jane.smith@example.com",
      "phone": "2485556789",
      "status": "active",
      "segment": "premium",
      "lifetime_value": 85000,
      "project_count": 3,
      "avg_project_value": 28333,
      "customer_since": "2024-06-15T00:00:00Z",
      "nps_score": 9,
      "created_at": "2024-06-15T12:00:00Z",
      "updated_at": "2025-01-01T12:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 250,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

### 2. Get Customer by ID
Get detailed information about a specific customer with optional history and insights.

**Endpoint:** `GET /api/customers/{customer_id}`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| include_history | boolean | Include interaction history |
| include_projects | boolean | Include project list |

**Response (200):**
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@example.com",
    "phone": "2485556789",
    "street_address": "456 Oak Ave",
    "city": "Troy",
    "state": "MI",
    "zip_code": "48084",
    "property_value": 650000,
    "status": "vip",
    "segment": "premium",
    "lifetime_value": 125000,
    "project_count": 4,
    "avg_project_value": 31250,
    "customer_since": "2024-06-15T00:00:00Z",
    "last_interaction": "2025-01-01T10:00:00Z",
    "interaction_count": 45,
    "referral_count": 3,
    "referral_value": 75000,
    "is_referral_partner": true,
    "nps_score": 10,
    "satisfaction_rating": 4.8,
    "created_at": "2024-06-15T12:00:00Z"
  },
  "insights": {
    "health_score": 95,
    "nps_category": "promoter",
    "is_at_risk": false,
    "opportunities": [
      "Candidate for referral program",
      "High engagement - potential upsell opportunity"
    ],
    "recommendations": [
      "Schedule quarterly check-in",
      "Good time for roof inspection outreach"
    ]
  },
  "interaction_history": [
    {
      "id": "interaction_id",
      "type": "phone_call",
      "date": "2025-01-01T10:00:00Z",
      "notes": "Quarterly check-in call",
      "outcome": "positive"
    }
  ],
  "projects": [
    {
      "id": "project_id",
      "project_type": "roof_replacement",
      "total_amount": 45000,
      "status": "completed",
      "completed_at": "2024-08-15T00:00:00Z"
    }
  ]
}
```

### 3. Create Customer
Create a new customer, typically from lead conversion.

**Endpoint:** `POST /api/customers/`

**Request Body:**
```json
{
  "first_name": "Alice",
  "last_name": "Johnson",
  "email": "alice@example.com",
  "phone": "2485557890",
  "street_address": "789 Pine St",
  "city": "Birmingham",
  "state": "MI",
  "zip_code": "48009",
  "property_value": 750000,
  "property_type": "single_family",
  "roof_age": 15,
  "roof_type": "asphalt_shingle",
  "converted_from_lead_id": "lead_uuid",
  "original_source": "google_ads",
  "assigned_to": "team_member_uuid",
  "notes": "Premium customer, referred by Bob Smith",
  "tags": "premium,referral"
}
```

**Response (201):**
```json
{
  "data": {
    "id": "new_customer_id",
    "first_name": "Alice",
    "last_name": "Johnson",
    "email": "alice@example.com",
    "status": "active",
    "segment": "standard",
    "customer_since": "2025-01-01T12:00:00Z",
    "created_at": "2025-01-01T12:00:00Z"
  }
}
```

### 4. Update Customer
Update customer information and automatically recalculate segment.

**Endpoint:** `PUT /api/customers/{customer_id}`

**Request Body:**
```json
{
  "phone": "2485551111",
  "status": "vip",
  "nps_score": 10,
  "is_referral_partner": true,
  "preferred_contact_method": "phone",
  "best_call_time": "mornings",
  "email_opt_in": true,
  "sms_opt_in": true
}
```

**Response (200):**
```json
{
  "data": {
    "id": "customer_id",
    "...: "updated customer data",
    "segment": "premium"
  }
}
```

### 5. Delete Customer
Soft delete a customer (marks as deleted, doesn't remove from database).

**Endpoint:** `DELETE /api/customers/{customer_id}`

**Response (200):**
```json
{
  "message": "Customer customer_id deleted successfully"
}
```

### 6. Get Customer Projects
Get all projects for a specific customer.

**Endpoint:** `GET /api/customers/{customer_id}/projects`

**Response (200):**
```json
{
  "data": [
    {
      "id": "project_id",
      "project_type": "roof_replacement",
      "total_amount": 45000,
      "status": "completed",
      "start_date": "2024-07-01T00:00:00Z",
      "completion_date": "2024-07-15T00:00:00Z"
    },
    {
      "id": "project_id_2",
      "project_type": "repair",
      "total_amount": 5000,
      "status": "in_progress",
      "start_date": "2025-01-01T00:00:00Z"
    }
  ],
  "count": 2,
  "total_value": 50000
}
```

### 7. Get Customer Interactions
Get interaction history for a customer.

**Endpoint:** `GET /api/customers/{customer_id}/interactions`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| limit | int | Number of interactions to return (default: 50) |
| type | string | Filter by interaction type |

**Response (200):**
```json
{
  "data": [
    {
      "id": "interaction_id",
      "type": "phone_call",
      "date": "2025-01-01T10:00:00Z",
      "notes": "Quarterly check-in",
      "outcome": "positive",
      "created_by": "team_member_id",
      "created_by_email": "team@iswitchroofs.com"
    }
  ],
  "count": 15
}
```

### 8. Create Customer Interaction
Log a new interaction with a customer.

**Endpoint:** `POST /api/customers/{customer_id}/interactions`

**Request Body:**
```json
{
  "type": "email",
  "notes": "Sent maintenance reminder and special offer",
  "outcome": "positive"
}
```

**Response (201):**
```json
{
  "data": {
    "id": "new_interaction_id",
    "customer_id": "customer_id",
    "type": "email",
    "notes": "Sent maintenance reminder and special offer",
    "outcome": "positive",
    "created_at": "2025-01-01T12:00:00Z"
  }
}
```

### 9. Calculate Lifetime Value
Recalculate customer's lifetime value based on all projects.

**Endpoint:** `POST /api/customers/{customer_id}/calculate-ltv`

**Response (200):**
```json
{
  "customer_id": "customer_id",
  "lifetime_value": 125000,
  "projects_count": 4,
  "average_project_value": 31250
}
```

### 10. Get Customer Statistics
Get aggregate statistics for all customers.

**Endpoint:** `GET /api/customers/stats`

**Response (200):**
```json
{
  "total_customers": 250,
  "total_revenue": 12500000,
  "avg_lifetime_value": 50000,
  "by_status": {
    "active": 180,
    "inactive": 45,
    "vip": 20,
    "churned": 5
  },
  "by_segment": {
    "premium": 50,
    "standard": 150,
    "repeat": 35,
    "referral_source": 15
  },
  "by_location": {
    "Birmingham": 45,
    "Troy": 38,
    "Bloomfield Hills": 25
  },
  "by_source": {
    "google_ads": 80,
    "website_form": 60,
    "referral": 50,
    "social_media": 35
  },
  "nps_breakdown": {
    "promoters": 150,
    "passives": 75,
    "detractors": 25,
    "nps_score": 50
  }
}
```

### 11. Bulk Update Customers
Update multiple customers at once.

**Endpoint:** `POST /api/customers/bulk-update`

**Request Body:**
```json
{
  "customer_ids": [
    "customer_id_1",
    "customer_id_2",
    "customer_id_3"
  ],
  "updates": {
    "campaign": "spring_2025",
    "segment": "premium",
    "tags": "spring_campaign,premium"
  }
}
```

**Response (207):**
```json
{
  "message": "Updated 3 customers",
  "updated": 3,
  "requested": 3
}
```

### 12. Export Customers
Export customers to CSV format.

**Endpoint:** `GET /api/customers/export`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| format | string | Export format (csv) |
| fields | string | Comma-separated fields to include |
| status | string | Filter by status |
| segment | string | Filter by segment |

**Response (200):**
```
Content-Type: text/csv
Content-Disposition: attachment; filename=customers_20250101_120000.csv

first_name,last_name,email,phone,lifetime_value,status,segment
Jane,Smith,jane@example.com,2485556789,125000,vip,premium
John,Doe,john@example.com,2485551234,45000,active,standard
```

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid customer ID format"
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
  "error": "Customer not found"
}
```

### 409 Conflict
```json
{
  "error": "Customer with this email already exists"
}
```

### 500 Internal Server Error
```json
{
  "error": "Failed to create customer",
  "details": "Database connection error"
}
```

## Customer Health Score Calculation

The health score (0-100) is calculated based on:

- **Lifetime Value (30 points max)**
  - $100K+: 30 points
  - $50K+: 25 points
  - $25K+: 20 points
  - $10K+: 15 points
  - Any value: 10 points

- **Project Frequency (20 points max)**
  - 5+ projects: 20 points
  - 3+ projects: 15 points
  - 2 projects: 10 points
  - 1 project: 5 points

- **NPS Score (20 points max)**
  - 9-10: 20 points
  - 7-8: 15 points
  - 5-6: 10 points

- **Referral Activity (15 points max)**
  - 5+ referrals: 15 points
  - 3+ referrals: 12 points
  - 1+ referrals: 8 points

- **Recent Interaction (15 points max)**
  - Within 30 days: 15 points
  - Within 90 days: 10 points
  - Within 180 days: 5 points

## Customer Insights

The insights object provides:

- `health_score` - Overall customer health (0-100)
- `nps_category` - promoter/passive/detractor
- `is_at_risk` - Boolean indicating churn risk
- `opportunities` - List of upsell/engagement opportunities
- `recommendations` - Suggested actions for the team

## Rate Limiting
- 1000 requests per hour per user
- 100 bulk operations per day
- 10 export operations per hour

## Webhooks
The following events trigger webhooks:
- `customer.created` - New customer created
- `customer.updated` - Customer information updated
- `customer.deleted` - Customer deleted
- `customer.converted` - Lead converted to customer
- `interaction.created` - New interaction logged

## Best Practices

1. **Segmentation**: Use segments to target marketing campaigns
2. **Health Monitoring**: Regularly check customer health scores
3. **Interaction Tracking**: Log all customer interactions for insights
4. **LTV Calculation**: Recalculate LTV after project completions
5. **Risk Management**: Monitor inactive and churned customers
6. **Export Data**: Regularly export customer data for backup

## Examples

### cURL Examples

**Get VIP customers:**
```bash
curl -X GET "https://api.iswitchroofs.com/api/customers/?status=vip&sort=lifetime_value:desc" \
  -H "Authorization: Bearer your_token"
```

**Create customer from lead:**
```bash
curl -X POST "https://api.iswitchroofs.com/api/customers/" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "New",
    "last_name": "Customer",
    "email": "new@example.com",
    "phone": "2485559999",
    "converted_from_lead_id": "lead_uuid",
    "original_source": "referral"
  }'
```

**Log interaction:**
```bash
curl -X POST "https://api.iswitchroofs.com/api/customers/customer_id/interactions" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "phone_call",
    "notes": "Discussed upcoming maintenance",
    "outcome": "positive"
  }'
```

## Related Documentation
- [Lead API](./LEADS_API.md) - Lead management
- [Project API](./PROJECTS_API.md) - Project management
- [Interactions API](./INTERACTIONS_API.md) - Interaction tracking
- [Analytics API](./ANALYTICS_API.md) - Customer analytics

---

Last Updated: 2025-01-01
API Version: 1.0.0