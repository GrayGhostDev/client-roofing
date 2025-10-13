# API Reference - iSwitch Roofs CRM

Complete REST API documentation for all endpoints.

## Table of Contents
- [Base URL & Authentication](#base-url--authentication)
- [Authentication Endpoints](#authentication-endpoints)
- [Customer Endpoints](#customer-endpoints)
- [Lead Endpoints](#lead-endpoints)
- [Project Endpoints](#project-endpoints)
- [Appointment Endpoints](#appointment-endpoints)
- [Interaction Endpoints](#interaction-endpoints)
- [Team Endpoints](#team-endpoints)
- [Notification Endpoints](#notification-endpoints)
- [Analytics Endpoints](#analytics-endpoints)
- [Partnership Endpoints](#partnership-endpoints)
- [Review Endpoints](#review-endpoints)
- [Error Responses](#error-responses)

---

## Base URL & Authentication

**Base URL:** `http://localhost:8000` (development) or `https://api.iswitchroofs.com` (production)

**Authentication:** JWT Bearer Token

```bash
# Include in all authenticated requests
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**API Documentation (Interactive):** `http://localhost:8000/docs` (Swagger UI)

---

## Authentication Endpoints

### POST /api/auth/login
**Description:** Authenticate user and receive JWT token

**Request:**
```json
{
  "email": "admin@iswitchroofs.com",
  "password": "SecurePassword123"
}
```

**Response (200):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "admin@iswitchroofs.com",
    "name": "John Doe",
    "role": "admin"
  },
  "expires_in": 86400
}
```

### POST /api/auth/refresh
**Description:** Refresh expired JWT token

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 86400
}
```

### GET /api/auth/me
**Description:** Get current authenticated user details

**Response (200):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "admin@iswitchroofs.com",
  "name": "John Doe",
  "role": "admin",
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

## Customer Endpoints

### GET /api/customers
**Description:** List all customers with pagination and filtering

**Query Parameters:**
- `page` (int, default=1): Page number
- `per_page` (int, default=20, max=100): Items per page
- `search` (string): Search by name, email, or phone
- `segment` (string): Filter by customer segment
- `sort_by` (string): Sort field (name, created_at, lifetime_value)
- `sort_order` (string): asc or desc

**Example Request:**
```bash
GET /api/customers?page=1&per_page=20&search=John&segment=premium&sort_by=lifetime_value&sort_order=desc
```

**Response (200):**
```json
{
  "customers": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "John Smith",
      "email": "john.smith@example.com",
      "phone": "+1234567890",
      "address": "123 Main St, City, State 12345",
      "customer_type": "residential",
      "segment": "premium",
      "lifetime_value": 50000.00,
      "project_count": 3,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8
  }
}
```

### POST /api/customers
**Description:** Create new customer

**Request:**
```json
{
  "name": "John Smith",
  "email": "john.smith@example.com",
  "phone": "+1234567890",
  "address": "123 Main St, City, State 12345",
  "customer_type": "residential",
  "segment": "premium",
  "notes": "High-value customer, prefers premium materials"
}
```

**Response (201):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "John Smith",
  "email": "john.smith@example.com",
  "phone": "+1234567890",
  "address": "123 Main St, City, State 12345",
  "customer_type": "residential",
  "segment": "premium",
  "lifetime_value": 0.00,
  "created_at": "2025-09-26T12:00:00Z",
  "updated_at": "2025-09-26T12:00:00Z"
}
```

### GET /api/customers/{customer_id}
**Description:** Get customer by ID with related data

**Response (200):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "John Smith",
  "email": "john.smith@example.com",
  "phone": "+1234567890",
  "address": "123 Main St, City, State 12345",
  "customer_type": "residential",
  "segment": "premium",
  "lifetime_value": 50000.00,
  "projects": [
    {
      "id": "proj-123",
      "name": "Roof Replacement",
      "status": "completed",
      "budget": 25000.00
    }
  ],
  "recent_interactions": [
    {
      "id": "int-456",
      "type": "phone_call",
      "subject": "Follow-up on warranty",
      "created_at": "2025-09-25T14:00:00Z"
    }
  ],
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-09-26T12:00:00Z"
}
```

### PUT /api/customers/{customer_id}
**Description:** Update customer information

**Request:**
```json
{
  "phone": "+1987654321",
  "segment": "ultra_premium",
  "notes": "Upgraded to ultra-premium tier"
}
```

**Response (200):** Updated customer object

### DELETE /api/customers/{customer_id}
**Description:** Delete customer (soft delete)

**Response (204):** No content

---

## Lead Endpoints

### GET /api/leads
**Description:** List leads with filtering and scoring

**Query Parameters:**
- `status` (string): Filter by status (new, contacted, qualified, converted, lost)
- `source` (string): Filter by lead source
- `assigned_to` (uuid): Filter by assigned user
- `min_score` (int): Minimum lead score
- `priority` (string): high, medium, low

**Response (200):**
```json
{
  "leads": [
    {
      "id": "lead-123",
      "customer_id": "cust-456",
      "customer_name": "Jane Doe",
      "source": "google_ads",
      "status": "qualified",
      "score": 85,
      "assigned_to": "user-789",
      "assigned_to_name": "Sales Rep",
      "project_type": "roof_replacement",
      "estimated_value": 30000.00,
      "priority": "high",
      "created_at": "2025-09-20T10:00:00Z",
      "last_contact": "2025-09-24T15:30:00Z"
    }
  ],
  "pagination": {...}
}
```

### POST /api/leads
**Description:** Create new lead with automatic scoring

**Request:**
```json
{
  "customer_id": "cust-456",
  "source": "website_form",
  "project_type": "roof_replacement",
  "estimated_value": 30000.00,
  "urgency": "within_month",
  "property_type": "residential",
  "notes": "Customer mentioned roof damage from recent storm"
}
```

**Response (201):**
```json
{
  "id": "lead-123",
  "customer_id": "cust-456",
  "source": "website_form",
  "status": "new",
  "score": 75,
  "assigned_to": "user-789",
  "project_type": "roof_replacement",
  "estimated_value": 30000.00,
  "priority": "high",
  "score_breakdown": {
    "project_value": 30,
    "urgency": 25,
    "source_quality": 20
  },
  "created_at": "2025-09-26T12:00:00Z"
}
```

### PUT /api/leads/{lead_id}/status
**Description:** Update lead status and trigger workflows

**Request:**
```json
{
  "status": "converted",
  "notes": "Customer signed contract"
}
```

**Response (200):** Updated lead object

### POST /api/leads/{lead_id}/assign
**Description:** Assign lead to team member

**Request:**
```json
{
  "assigned_to": "user-789",
  "notes": "Assigned based on territory"
}
```

**Response (200):** Updated lead object

---

## Project Endpoints

### GET /api/projects
**Description:** List all projects with filtering

**Query Parameters:**
- `status` (string): planning, in_progress, completed, on_hold
- `customer_id` (uuid): Filter by customer
- `assigned_team` (uuid): Filter by team member

**Response (200):**
```json
{
  "projects": [
    {
      "id": "proj-123",
      "customer_id": "cust-456",
      "customer_name": "John Smith",
      "name": "Roof Replacement - Main House",
      "project_type": "roof_replacement",
      "status": "in_progress",
      "budget": 25000.00,
      "actual_cost": 15000.00,
      "completion_percentage": 60,
      "start_date": "2025-09-01",
      "end_date": "2025-09-30",
      "assigned_team": ["user-789", "user-012"],
      "created_at": "2025-08-15T10:00:00Z"
    }
  ],
  "pagination": {...}
}
```

### POST /api/projects
**Description:** Create new project

**Request:**
```json
{
  "customer_id": "cust-456",
  "name": "Roof Replacement - Main House",
  "project_type": "roof_replacement",
  "budget": 25000.00,
  "start_date": "2025-09-01",
  "end_date": "2025-09-30",
  "assigned_team": ["user-789", "user-012"],
  "materials": ["premium_shingles", "underlayment"],
  "notes": "Customer wants GAF Timberline HDZ"
}
```

**Response (201):** Created project object

### PUT /api/projects/{project_id}/progress
**Description:** Update project completion percentage

**Request:**
```json
{
  "completion_percentage": 75,
  "actual_cost": 18000.00,
  "notes": "Completed shingle installation"
}
```

**Response (200):** Updated project object

---

## Appointment Endpoints

### GET /api/appointments
**Description:** List appointments with calendar integration

**Query Parameters:**
- `start_date` (date): Filter appointments from date
- `end_date` (date): Filter appointments until date
- `assigned_to` (uuid): Filter by assigned user
- `status` (string): scheduled, completed, cancelled, no_show

**Response (200):**
```json
{
  "appointments": [
    {
      "id": "appt-123",
      "customer_id": "cust-456",
      "customer_name": "John Smith",
      "project_id": "proj-789",
      "appointment_type": "inspection",
      "start_time": "2025-09-27T10:00:00Z",
      "end_time": "2025-09-27T11:00:00Z",
      "assigned_to": "user-012",
      "status": "scheduled",
      "location": "123 Main St, City, State",
      "notes": "Initial roof inspection",
      "created_at": "2025-09-26T12:00:00Z"
    }
  ],
  "pagination": {...}
}
```

### POST /api/appointments
**Description:** Schedule new appointment

**Request:**
```json
{
  "customer_id": "cust-456",
  "project_id": "proj-789",
  "appointment_type": "inspection",
  "start_time": "2025-09-27T10:00:00Z",
  "end_time": "2025-09-27T11:00:00Z",
  "assigned_to": "user-012",
  "location": "123 Main St, City, State",
  "notes": "Initial roof inspection",
  "send_reminder": true
}
```

**Response (201):** Created appointment object

---

## Analytics Endpoints

### GET /api/analytics/dashboard
**Description:** Get comprehensive dashboard metrics

**Query Parameters:**
- `start_date` (date): Start of date range
- `end_date` (date): End of date range
- `granularity` (string): day, week, month

**Response (200):**
```json
{
  "period": {
    "start_date": "2025-09-01",
    "end_date": "2025-09-26"
  },
  "revenue": {
    "total": 450000.00,
    "growth_percentage": 15.5,
    "by_project_type": {
      "roof_replacement": 300000.00,
      "repair": 100000.00,
      "inspection": 50000.00
    }
  },
  "leads": {
    "total": 145,
    "conversion_rate": 32.5,
    "by_source": {
      "google_ads": 45,
      "referral": 35,
      "website": 30,
      "social": 20,
      "other": 15
    }
  },
  "projects": {
    "total": 47,
    "completed": 30,
    "in_progress": 12,
    "on_hold": 5,
    "average_value": 25000.00
  },
  "customers": {
    "total": 320,
    "new_this_period": 28,
    "retention_rate": 87.5
  }
}
```

### GET /api/analytics/lead-funnel
**Description:** Lead conversion funnel metrics

**Response (200):**
```json
{
  "funnel_stages": [
    {
      "stage": "new",
      "count": 150,
      "conversion_rate": 100
    },
    {
      "stage": "contacted",
      "count": 120,
      "conversion_rate": 80
    },
    {
      "stage": "qualified",
      "count": 75,
      "conversion_rate": 50
    },
    {
      "stage": "converted",
      "count": 45,
      "conversion_rate": 30
    }
  ],
  "average_time_to_convert": 7.5
}
```

---

## Error Responses

**Standard Error Format:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "email": "Invalid email format",
      "phone": "Phone number required"
    }
  }
}
```

**HTTP Status Codes:**
- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `204 No Content` - Successful deletion
- `400 Bad Request` - Invalid input data
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (duplicate)
- `422 Unprocessable Entity` - Validation failed
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service temporarily unavailable
