# iSwitch Roofs CRM - Backend Documentation

## Table of Contents

### 📚 API Documentation
- [API Overview](./api/README.md)
- [Authentication](./api/AUTHENTICATION.md)
- [Audit Fields](./api/AUDIT_FIELDS.md)
- [Workflows](./api/WORKFLOWS.md)

#### API Endpoints
- [Leads API](./api/endpoints/LEADS_API.md) ✅
- [Customers API](./api/endpoints/CUSTOMERS_API.md)
- [Projects API](./api/endpoints/PROJECTS_API.md)
- [Interactions API](./api/endpoints/INTERACTIONS_API.md)
- [Appointments API](./api/endpoints/APPOINTMENTS_API.md)
- [Analytics API](./api/endpoints/ANALYTICS_API.md)
- [Team API](./api/endpoints/TEAM_API.md)
- [Reviews API](./api/endpoints/REVIEWS_API.md)
- [Partnerships API](./api/endpoints/PARTNERSHIPS_API.md)

### 🔧 Services
- [Notification Service](./services/NOTIFICATION_SERVICE.md)
- [Lead Scoring Service](./services/LEAD_SCORING_SERVICE.md)
- [Automation Service](./services/AUTOMATION_SERVICE.md)
- [Analytics Service](./services/ANALYTICS_SERVICE.md)
- [Integration Service](./services/INTEGRATION_SERVICE.md)
- [Report Service](./services/REPORT_SERVICE.md)

### 🔌 Integrations
- [AccuLynx](./integrations/ACCULYNX.md)
- [CallRail](./integrations/CALLRAIL.md)
- [BirdEye](./integrations/BIRDEYE.md)
- [Google LSA](./integrations/GOOGLE_LSA.md)
- [SendGrid](./integrations/SENDGRID.md)
- [Twilio](./integrations/TWILIO.md)
- [Pusher](./integrations/PUSHER.md)
- [Stripe](./integrations/STRIPE.md)

### 🔒 Security
- [Security Guide](./security/SECURITY_GUIDE.md)
- [JWT Setup](./security/JWT_SETUP.md)
- [RBAC (Role-Based Access Control)](./security/RBAC.md)
- [Permissions Matrix](./security/PERMISSIONS_MATRIX.md)
- [OWASP Compliance](./security/OWASP_COMPLIANCE.md)

### 📊 Workflows & Business Logic
- [16-Touch Campaign](./workflows/16_TOUCH_CAMPAIGN.md)
- [Lead Lifecycle](./workflows/LEAD_LIFECYCLE.md)
- [Project Workflow](./workflows/PROJECT_WORKFLOW.md)
- [Review Automation](./workflows/REVIEW_AUTOMATION.md)
- [Referral Workflow](./workflows/REFERRAL_WORKFLOW.md)

### 🧪 Testing
- [Test Guide](./testing/TEST_GUIDE.md)
- [Unit Tests](./testing/UNIT_TESTS.md)
- [Integration Tests](./testing/INTEGRATION_TESTS.md)
- [E2E Tests](./testing/E2E_GUIDE.md)
- [Performance Tests](./testing/PERFORMANCE_TESTS.md)
- [Coverage Report](./testing/COVERAGE_REPORT.md)

### ⚡ Performance
- [Optimization Guide](./performance/OPTIMIZATION_GUIDE.md)
- [Benchmarks](./performance/BENCHMARKS.md)
- [Caching Strategy](./performance/CACHING.md)
- [Load Test Results](./performance/LOAD_TEST_RESULTS.md)

### 📈 KPIs & Metrics
- [Metrics Definitions](./kpis/METRICS_DEFINITIONS.md)
- [Dashboard Guide](./kpis/DASHBOARD_GUIDE.md)
- [Reporting Guide](./kpis/REPORTING_GUIDE.md)

### 🚀 Deployment
- [Deployment Guide](./deployment/DEPLOYMENT_GUIDE.md)
- [Production Checklist](./deployment/PRODUCTION_CHECKLIST.md)
- [Environment Variables](./deployment/ENVIRONMENT_VARIABLES.md)
- [Docker Setup](./deployment/DOCKER_SETUP.md)
- [Render Configuration](./deployment/RENDER_CONFIG.md)
- [Troubleshooting](./deployment/TROUBLESHOOTING.md)

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+ (via Supabase)
- Redis 6+ (optional, for caching)
- Node.js 18+ (for frontend development)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/iswitchroofs/crm-backend.git
cd crm-backend/backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```
   - Generate a secure Flask secret and update the `SECRET_KEY` entry in `.env`:
     ```bash
     python -c "import secrets; print(secrets.token_urlsafe(64))"
     ```
   - Keep `.env.example` updated with placeholders only—never commit real secrets.

5. **Run migrations:**
```bash
flask db upgrade
```

6. **Start the development server:**
```bash
flask run
```

The API will be available at `http://localhost:5000`

> The application selects its configuration profile from the first set environment variable among `FLASK_CONFIG`, `APP_ENV`, or `FLASK_ENV` (defaulting to `development`).

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_lead_scoring.py

# Run tests in watch mode
ptw
```

## Architecture Overview

```
backend/
├── app/                     # Application code
│   ├── __init__.py         # Flask app factory
│   ├── config.py           # Configuration management
│   ├── models/             # Data models (Pydantic)
│   ├── routes/             # API endpoints
│   ├── services/           # Business logic
│   ├── middleware/         # Request/response middleware
│   ├── utils/              # Utility functions
│   └── integrations/       # Third-party integrations
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   ├── e2e/               # End-to-end tests
│   └── performance/        # Performance tests
├── docs/                    # Documentation
├── migrations/             # Database migrations
└── scripts/                # Utility scripts
```

## Technology Stack

### Core
- **Framework:** Flask 3.1.0
- **Database:** PostgreSQL (via Supabase)
- **Real-time:** Pusher
- **Authentication:** JWT (PyJWT)
- **Validation:** Pydantic

### Services
- **Email:** SendGrid
- **SMS:** Twilio
- **Payments:** Stripe
- **CRM Integration:** AccuLynx
- **Call Tracking:** CallRail
- **Reviews:** BirdEye

### Testing
- **Framework:** pytest
- **Coverage:** pytest-cov
- **Mocking:** pytest-mock
- **Factory:** factory-boy
- **Load Testing:** Locust

## API Standards

### Request/Response Format
- **Content-Type:** `application/json`
- **Authentication:** Bearer token in Authorization header
- **Date Format:** ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)
- **UUID Format:** Standard UUID v4

### Status Codes
- `200` - Success
- `201` - Created
- `204` - No Content
- `207` - Multi-Status (partial success)
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `409` - Conflict
- `422` - Unprocessable Entity
- `429` - Too Many Requests
- `500` - Internal Server Error

### Pagination
All list endpoints support pagination:
```
GET /api/resource?page=1&per_page=50
```

### Filtering
Multiple filters can be combined:
```
GET /api/leads?status=new,contacted&temperature=hot&source=google_ads
```

### Sorting
Sort by any field in ascending or descending order:
```
GET /api/leads?sort=lead_score:desc
```

## Development Guidelines

### Code Style
- Follow PEP 8
- Use type hints
- Document all functions
- Write tests for new features

### Git Workflow
1. Create feature branch from `main`
2. Write tests
3. Implement feature
4. Ensure tests pass
5. Update documentation
6. Create pull request

### Commit Messages
Use conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring
- `perf:` Performance improvement
- `chore:` Maintenance

## Support

### Resources
- [API Documentation](./api/README.md)
- [Troubleshooting Guide](./deployment/TROUBLESHOOTING.md)
- [FAQ](./FAQ.md)

### Contact
- **Email:** tech@iswitchroofs.com
- **Slack:** #tech-support
- **GitHub Issues:** [Create Issue](https://github.com/iswitchroofs/crm-backend/issues)

## License
Copyright © 2025 iSwitch Roofs. All rights reserved.

---

Last Updated: 2025-01-01
Version: 1.0.0
