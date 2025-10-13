# System Architecture - iSwitch Roofs CRM

Complete technical architecture documentation for the iSwitch Roofs CRM system.

## Table of Contents
- [System Overview](#system-overview)
- [Architecture Layers](#architecture-layers)
- [Data Flow](#data-flow)
- [Database Schema](#database-schema)
- [Caching Strategy](#caching-strategy)
- [Real-Time Communication](#real-time-communication)
- [Security Architecture](#security-architecture)

---

## System Overview

### Technology Stack

**Backend:**
- **Framework:** Flask 3.0.0 with Flask-RESTX
- **Database:** PostgreSQL 15+ (via Supabase)
- **Cache:** Redis 7+
- **Real-Time:** Pusher Channels
- **ORM:** SQLAlchemy 2.0+
- **Authentication:** JWT (PyJWT)
- **Task Queue:** Celery (optional)

**Frontend:**
- **Framework:** Streamlit 1.28+
- **UI Components:** Custom components + Streamlit native
- **Charts:** Plotly, Matplotlib, Seaborn
- **Data Visualization:** Pandas, NumPy

**Infrastructure:**
- **Deployment:** Docker, Kubernetes, systemd
- **Web Server:** Gunicorn (production), Flask dev (development)
- **Reverse Proxy:** Nginx
- **Monitoring:** Custom health checks, Prometheus-ready

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │   Browser   │  │ Mobile App   │  │  External Systems   │   │
│  │  (Admin UI) │  │   (Future)   │  │  (Integrations)     │   │
│  └──────┬──────┘  └───────┬──────┘  └──────────┬──────────┘   │
└─────────┼─────────────────┼────────────────────┼───────────────┘
          │                 │                    │
          │                 │                    │
┌─────────┼─────────────────┼────────────────────┼───────────────┐
│         │                 │                    │                │
│    ┌────▼─────────────────▼────────────────────▼───────┐       │
│    │              Nginx Reverse Proxy                  │       │
│    │        (SSL, Rate Limiting, Load Balancing)       │       │
│    └────┬─────────────────┬────────────────────┬───────┘       │
│         │                 │                    │                │
│         │                 │                    │                │
│    ┌────▼────────┐   ┌────▼────────┐   ┌──────▼──────┐        │
│    │  Streamlit  │   │    Flask    │   │  WebSocket  │        │
│    │  Dashboard  │   │  REST API   │   │   Server    │        │
│    │   :8501     │   │   :8000     │   │  (Pusher)   │        │
│    └─────────────┘   └──────┬──────┘   └─────────────┘        │
│                              │                                  │
│                        Application Layer                        │
└──────────────────────────────┼──────────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
     ┌────▼────┐          ┌────▼────┐         ┌────▼────┐
     │  Redis  │          │  Flask  │         │ Pusher  │
     │  Cache  │          │ Routes  │         │Channels │
     │  :6379  │          │         │         │  Cloud  │
     └─────────┘          └────┬────┘         └─────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
     ┌────▼─────┐         ┌────▼────┐         ┌────▼────┐
     │ Business │         │  Data   │         │  Auth   │
     │  Logic   │         │ Access  │         │ Service │
     │ Services │         │  Layer  │         │   JWT   │
     └──────────┘         └────┬────┘         └─────────┘
                               │
                          ┌────▼────┐
                          │ SQLAlch │
                          │   ORM   │
                          └────┬────┘
                               │
┌──────────────────────────────┼──────────────────────────────────┐
│                         Data Layer                               │
│                         ┌────▼────┐                              │
│                         │Supabase │                              │
│                         │Postgres │                              │
│                         │  :5432  │                              │
│                         └─────────┘                              │
└──────────────────────────────────────────────────────────────────┘
```

---

## Architecture Layers

### 1. Presentation Layer (Frontend)

**Streamlit Dashboard** (`frontend-streamlit/`):
```
Home.py                    # Entry point, navigation
pages/
  ├── 1_📊_Dashboard.py   # Analytics & metrics
  ├── 2_👥_Customers.py   # Customer management
  ├── 3_🎯_Leads.py       # Lead tracking
  ├── 4_📋_Projects.py    # Project management
  ├── 5_📅_Appointments.py # Scheduling
  ├── 6_💬_Interactions.py # Communication log
  └── 7_⚙️_Settings.py    # System configuration
utils/
  ├── api_client.py       # Backend API integration
  ├── auth.py             # Authentication helpers
  └── components.py       # Reusable UI components
```

**Key Features:**
- Session-based authentication
- Real-time data updates (via Pusher)
- Responsive design with Streamlit components
- Interactive data visualizations

### 2. Application Layer (Backend API)

**Flask REST API** (`backend/app/`):
```
app/
├── __init__.py            # Application factory
├── config.py              # Configuration management
├── models/                # SQLAlchemy models & Pydantic schemas
│   ├── customer_sqlalchemy.py
│   ├── customer_schemas.py
│   ├── lead.py
│   ├── lead_schemas.py
│   ├── project_sqlalchemy.py
│   ├── project_schemas.py
│   ├── appointment_sqlalchemy.py
│   ├── appointment_schemas.py
│   ├── interaction_sqlalchemy.py
│   ├── interaction_schemas.py
│   ├── notification_sqlalchemy.py
│   ├── team_sqlalchemy.py
│   ├── alert_sqlalchemy.py
│   ├── analytics_sqlalchemy.py
│   ├── partnership_sqlalchemy.py
│   └── review_sqlalchemy.py
├── routes/                # API endpoints (Flask-RESTX)
│   ├── auth.py           # Authentication & authorization
│   ├── customers.py      # Customer CRUD
│   ├── leads.py          # Lead management
│   ├── projects.py       # Project operations
│   ├── appointments.py   # Scheduling
│   ├── interactions.py   # Communication tracking
│   ├── teams.py          # Team management
│   ├── notifications.py  # Alert system
│   ├── analytics.py      # Reporting & metrics
│   ├── partnerships.py   # Partnership management
│   └── reviews.py        # Review management
├── services/              # Business logic layer
│   ├── customer_service.py
│   ├── lead_scoring.py
│   ├── project_service.py
│   ├── interaction_service.py
│   ├── notification.py
│   ├── partnerships_service.py
│   └── reviews_service.py
├── middleware/            # Request/response processing
│   └── audit_middleware.py  # Audit logging
└── utils/                 # Shared utilities
    ├── auth.py           # JWT utilities
    ├── validators.py     # Input validation
    └── decorators.py     # Custom decorators
```

**Design Patterns:**
- **Factory Pattern:** Application creation (`create_app()`)
- **Repository Pattern:** Data access abstraction
- **Service Layer:** Business logic separation
- **Dependency Injection:** Configuration and services
- **Decorator Pattern:** Authentication, caching, validation

### 3. Data Access Layer

**SQLAlchemy ORM:**
```python
# Example: Customer Model
class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(200), nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), index=True)
    address = db.Column(db.Text)

    # Relationships
    projects = db.relationship('Project', back_populates='customer', lazy='dynamic')
    interactions = db.relationship('Interaction', back_populates='customer', lazy='dynamic')
    appointments = db.relationship('Appointment', back_populates='customer', lazy='dynamic')

    # Indexes for performance
    __table_args__ = (
        db.Index('idx_customer_name_email', 'name', 'email'),
        db.Index('idx_customer_created', 'created_at'),
    )
```

**Pydantic Schemas for Validation:**
```python
# Input validation
class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    phone: Optional[str] = Field(None, regex=r'^\+?1?\d{9,15}$')
    address: Optional[str] = None

# Response serialization
class CustomerResponse(BaseModel):
    id: UUID
    name: str
    email: str
    phone: Optional[str]
    created_at: datetime
    project_count: int
```

### 4. Caching Layer

**Redis Cache Strategy:**
```python
# Cache decorator (app/utils/decorators.py)
def cache_result(timeout=300):
    """Cache function result in Redis with automatic invalidation"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = f"cache:{f.__name__}:{hash_args(args, kwargs)}"

            # Try cache first
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Execute function
            result = f(*args, **kwargs)

            # Store in cache
            redis_client.setex(cache_key, timeout, json.dumps(result))
            return result
        return decorated_function
    return decorator
```

**Cache Invalidation:**
- **TTL-based:** Automatic expiration (5-60 minutes)
- **Event-based:** Manual invalidation on data changes
- **Pattern-based:** Bulk deletion by key pattern

---

## Data Flow

### 1. User Request Flow

**Example: Create New Lead**
```
1. User submits lead form (Streamlit UI)
   └─> POST /api/leads

2. Flask receives request
   └─> Authentication middleware (JWT validation)
   └─> Request validation (Pydantic schema)
   └─> Route handler (routes/leads.py)

3. Business logic (services/lead_scoring.py)
   └─> Calculate lead score
   └─> Assign to team member
   └─> Create notification

4. Data persistence
   └─> SQLAlchemy creates Lead record
   └─> Supabase PostgreSQL insert
   └─> Commit transaction

5. Cache update
   └─> Invalidate leads list cache
   └─> Update analytics cache

6. Real-time notification
   └─> Pusher broadcast to team members

7. Response
   └─> Return created lead (JSON)
   └─> Frontend updates UI
```

### 2. Background Job Flow (Future)

**Example: Lead Follow-Up Reminder**
```
1. Celery Beat scheduler triggers task

2. Task execution (tasks/reminders.py)
   └─> Query overdue follow-ups
   └─> For each lead:
       └─> Create notification
       └─> Send email (optional)
       └─> Update lead status

3. Real-time updates
   └─> Pusher notification to assigned team member

4. Audit log
   └─> Record task execution in audit table
```

---

## Database Schema

### Core Tables

**customers**
```sql
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    customer_type VARCHAR(50) DEFAULT 'residential',
    segment VARCHAR(50),
    lifetime_value DECIMAL(12, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),

    -- Indexes
    CONSTRAINT idx_customer_email UNIQUE (email),
    INDEX idx_customer_name (name),
    INDEX idx_customer_segment (segment),
    INDEX idx_customer_created (created_at)
);
```

**leads**
```sql
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    source VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'new',
    score INTEGER DEFAULT 0,
    assigned_to UUID REFERENCES users(id),
    project_type VARCHAR(100),
    estimated_value DECIMAL(12, 2),
    priority VARCHAR(20) DEFAULT 'medium',
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes for lead scoring & filtering
    INDEX idx_lead_status (status),
    INDEX idx_lead_score (score DESC),
    INDEX idx_lead_assigned (assigned_to),
    INDEX idx_lead_created (created_at DESC)
);
```

**projects**
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    project_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'planning',
    budget DECIMAL(12, 2),
    actual_cost DECIMAL(12, 2) DEFAULT 0,
    start_date DATE,
    end_date DATE,
    completion_percentage INTEGER DEFAULT 0,
    assigned_team UUID[] DEFAULT ARRAY[]::UUID[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    INDEX idx_project_customer (customer_id),
    INDEX idx_project_status (status),
    INDEX idx_project_dates (start_date, end_date)
);
```

### Relationship Tables

**interactions**
```sql
CREATE TABLE interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    interaction_type VARCHAR(50) NOT NULL,
    channel VARCHAR(50),
    direction VARCHAR(20),
    subject VARCHAR(200),
    notes TEXT,
    outcome VARCHAR(100),
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),

    -- Indexes for filtering & reporting
    INDEX idx_interaction_customer (customer_id),
    INDEX idx_interaction_type (interaction_type),
    INDEX idx_interaction_created (created_at DESC)
);
```

### Analytics Tables

**analytics_snapshots**
```sql
CREATE TABLE analytics_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_date DATE NOT NULL,
    metric_type VARCHAR(100) NOT NULL,
    metric_value JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_snapshot UNIQUE (snapshot_date, metric_type),
    INDEX idx_snapshot_date (snapshot_date DESC)
);
```

---

## Caching Strategy

### Cache Layers

**L1 Cache (Application):**
- In-memory caching for hot data
- Function-level memoization
- Request-scoped caching

**L2 Cache (Redis):**
- Shared cache across application instances
- Session storage
- Real-time data caching
- Analytics aggregations

### Cache Keys Convention

```
Format: {prefix}:{entity}:{identifier}:{version}

Examples:
- customer:123e4567:v1
- leads:list:assigned:456:page:1
- analytics:dashboard:daily:2025-09-26
- session:user:789abc:token
```

### Cache Invalidation Strategy

**Write-Through:**
```python
def update_customer(customer_id, data):
    # Update database
    customer = Customer.query.get(customer_id)
    customer.update(data)
    db.session.commit()

    # Invalidate cache
    redis_client.delete(f"customer:{customer_id}")
    redis_client.delete(f"customers:list:*")  # Pattern-based

    return customer
```

---

## Real-Time Communication

### Pusher Integration

**Event Types:**
- `lead-created` - New lead notification
- `project-updated` - Project status changes
- `appointment-reminder` - Upcoming appointments
- `notification` - General alerts

**Channel Structure:**
```
user-{user_id}          # Private user channel
team-{team_id}          # Team broadcasts
project-{project_id}    # Project updates
dashboard               # Public dashboard updates
```

---

## Security Architecture

### Authentication Flow

1. User login → Credentials validation
2. Generate JWT token (24h expiration)
3. Return token + refresh token
4. Client stores in secure cookie/localStorage
5. All requests include Authorization header
6. Backend validates JWT on each request
7. Refresh token extends session

### Authorization Levels

- **Admin:** Full system access
- **Manager:** Team management, reports
- **Sales:** Leads, customers, projects
- **Field Tech:** Assigned projects only

### Data Protection

- **Encryption at rest:** PostgreSQL encryption (Supabase)
- **Encryption in transit:** TLS 1.3 (HTTPS)
- **Password hashing:** bcrypt (10 rounds)
- **Secrets management:** Environment variables
