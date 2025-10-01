# Implementation Strategy: iSwitch Roofs CRM Complete Application

## Executive Summary
Comprehensive implementation plan to complete the full-stack roofing CRM application built on Flask/Supabase/Pusher backend with Reflex and Streamlit frontends. The strategy is organized into 7 phases covering backend completion, frontend development, integrations, testing, deployment, and business-specific features.

**Current Status:** Backend foundation complete (Flask + Supabase + Pusher + 10 route blueprints)
**Timeline:** 15 weeks to full production
**MVP Target:** 7 weeks

---

## PHASE 1: Backend API Development (Weeks 1-3)
**Goal:** Complete REST API with full CRUD operations and business logic

### 1.1 Data Models & ORM (Week 1)
- [ ] **backend/app/models/__init__.py** - Model registry and base classes
- [ ] **backend/app/models/lead.py** - Lead model with scoring logic
- [ ] **backend/app/models/customer.py** - Customer model with relationship tracking
- [ ] **backend/app/models/project.py** - Project model with status workflows
- [ ] **backend/app/models/interaction.py** - Interaction tracking model
- [ ] **backend/app/models/appointment.py** - Appointment scheduling model
- [ ] **backend/app/models/team.py** - Team member and assignment models
- [ ] **backend/app/models/review.py** - Review management model
- [ ] **backend/app/models/partnership.py** - Partnership tracking model

**Technical Details:**
- Use dataclasses or Pydantic models for validation
- Implement model serialization/deserialization
- Add relationships between models
- Include soft delete functionality
- Add audit fields (created_at, updated_at, created_by, updated_by)

### 1.2 Lead Scoring Engine (Week 1)
- [ ] **backend/app/services/lead_scoring.py** - Implement 0-100 point algorithm
  - [ ] Demographics scoring (property value 0-30 pts, income level 0-15 pts, location 0-10 pts)
  - [ ] Behavioral scoring (website engagement 0-15 pts, response time 0-10 pts, interactions 0-10 pts)
  - [ ] BANT qualification (Budget 0-8 pts, Authority 0-7 pts, Need 0-5 pts, Timeline 0-5 pts)
  - [ ] Temperature classification (Hot 80+, Warm 60-79, Cool 40-59, Cold <40)

**Scoring Breakdown:**
```
TOTAL SCORE = Demographics (55 pts) + Behavioral (35 pts) + BANT (10 pts)

Demographics (55 points):
  - Property Value: $500K+ (30), $300-500K (20), $200-300K (10), <$200K (5)
  - Income Level: $200K+ (15), $150-200K (10), $100-150K (5), <$100K (2)
  - Location: Premium zip codes (10), Target markets (7), Other (3)

Behavioral (35 points):
  - Website Engagement: Multiple visits (15), Single visit (10), Form fill (5)
  - Response Time: <5 min (10), <1 hr (7), <24 hr (4), >24 hr (1)
  - Interactions: 5+ (10), 3-4 (7), 1-2 (4), None (0)

BANT (10 points):
  - Budget: Confirmed (8), Estimated (5), Unknown (2)
  - Authority: Decision maker (7), Influencer (4), Unknown (1)
  - Need: Immediate (5), Within 3 months (3), Exploring (1)
  - Timeline: <30 days (5), 30-90 days (3), >90 days (1)
```

### 1.3 REST API Endpoints (Week 2)

#### Leads API (backend/app/routes/leads.py)
- [ ] POST /api/leads/ - Create lead with auto-scoring
- [ ] GET /api/leads/ - List leads with filtering/pagination
- [ ] GET /api/leads/{id} - Get lead details
- [ ] PUT /api/leads/{id} - Update lead (recalculate score)
- [ ] DELETE /api/leads/{id} - Soft delete lead
- [ ] POST /api/leads/{id}/assign - Assign to team member
- [ ] POST /api/leads/{id}/convert - Convert to customer
- [ ] GET /api/leads/stats - Lead statistics (by status, source, temperature)
- [ ] POST /api/leads/{id}/score - Manually recalculate score
- [ ] GET /api/leads/hot - Get all hot leads
- [ ] POST /api/leads/bulk-import - Bulk import from CSV/Excel

**Query Parameters:**
```
GET /api/leads?
  status=new,contacted&
  source=google_ads&
  temperature=hot,warm&
  assigned_to=user_id&
  created_after=2025-01-01&
  page=1&
  per_page=50&
  sort=lead_score:desc
```

#### Customers API (backend/app/routes/customers.py)
- [ ] POST /api/customers/ - Create customer
- [ ] GET /api/customers/ - List customers with filtering/pagination
- [ ] GET /api/customers/{id} - Get customer details with project history
- [ ] PUT /api/customers/{id} - Update customer
- [ ] DELETE /api/customers/{id} - Soft delete customer
- [ ] GET /api/customers/{id}/projects - Get customer's projects
- [ ] GET /api/customers/{id}/interactions - Get customer's interaction timeline
- [ ] GET /api/customers/{id}/ltv - Calculate lifetime value
- [ ] POST /api/customers/{id}/request-review - Send review request

#### Projects API (backend/app/routes/projects.py)
- [ ] POST /api/projects/ - Create project
- [ ] GET /api/projects/ - List projects with filtering/pagination
- [ ] GET /api/projects/{id} - Get project details
- [ ] PUT /api/projects/{id} - Update project
- [ ] DELETE /api/projects/{id} - Soft delete project
- [ ] POST /api/projects/{id}/status - Update project status (with workflow validation)
- [ ] POST /api/projects/{id}/documents - Upload documents (Supabase Storage)
- [ ] GET /api/projects/{id}/documents - List project documents
- [ ] DELETE /api/projects/{id}/documents/{doc_id} - Delete document
- [ ] GET /api/projects/pipeline - Get project pipeline view
- [ ] GET /api/projects/gantt - Get Gantt chart data

#### Interactions API (backend/app/routes/interactions.py)
- [ ] POST /api/interactions/ - Log interaction (call, email, meeting, note)
- [ ] GET /api/interactions/ - List interactions with filtering
- [ ] GET /api/interactions/{id} - Get interaction details
- [ ] PUT /api/interactions/{id} - Update interaction
- [ ] DELETE /api/interactions/{id} - Delete interaction
- [ ] GET /api/interactions/timeline/{entity_type}/{entity_id} - Get timeline for lead/customer
- [ ] POST /api/interactions/{id}/transcription - Add call transcription

#### Appointments API (backend/app/routes/appointments.py)
- [ ] POST /api/appointments/ - Create appointment
- [ ] GET /api/appointments/ - List appointments with filtering
- [ ] GET /api/appointments/{id} - Get appointment details
- [ ] PUT /api/appointments/{id} - Update appointment
- [ ] DELETE /api/appointments/{id} - Cancel appointment
- [ ] GET /api/appointments/calendar - Get calendar view
- [ ] GET /api/appointments/availability/{team_member_id} - Get availability
- [ ] POST /api/appointments/{id}/reschedule - Reschedule appointment
- [ ] POST /api/appointments/{id}/send-reminder - Manual reminder send
- [ ] GET /api/appointments/upcoming - Get upcoming appointments

#### Analytics API (backend/app/routes/analytics.py)
- [ ] GET /api/analytics/dashboard - Dashboard KPIs
- [ ] GET /api/analytics/funnel - Conversion funnel data
- [ ] GET /api/analytics/revenue - Revenue analytics
- [ ] GET /api/analytics/team-performance - Team metrics
- [ ] GET /api/analytics/lead-sources - Lead source ROI
- [ ] GET /api/analytics/geographic - Geographic distribution
- [ ] GET /api/analytics/forecasting - Revenue forecasting
- [ ] POST /api/analytics/custom-report - Generate custom report

#### Team API (backend/app/routes/team.py)
- [ ] POST /api/team/ - Create team member
- [ ] GET /api/team/ - List team members
- [ ] GET /api/team/{id} - Get team member details
- [ ] PUT /api/team/{id} - Update team member
- [ ] DELETE /api/team/{id} - Deactivate team member
- [ ] GET /api/team/{id}/performance - Get performance metrics
- [ ] GET /api/team/{id}/assignments - Get current assignments
- [ ] PUT /api/team/{id}/availability - Update availability

#### Reviews API (backend/app/routes/reviews.py)
- [ ] POST /api/reviews/ - Create review (from BirdEye webhook)
- [ ] GET /api/reviews/ - List reviews with filtering
- [ ] GET /api/reviews/{id} - Get review details
- [ ] PUT /api/reviews/{id}/respond - Respond to review
- [ ] GET /api/reviews/stats - Review statistics
- [ ] POST /api/reviews/request/{customer_id} - Send review request

#### Partnerships API (backend/app/routes/partnerships.py)
- [ ] POST /api/partnerships/ - Create partnership
- [ ] GET /api/partnerships/ - List partnerships
- [ ] GET /api/partnerships/{id} - Get partnership details
- [ ] PUT /api/partnerships/{id} - Update partnership
- [ ] DELETE /api/partnerships/{id} - Deactivate partnership
- [ ] GET /api/partnerships/{id}/referrals - Get referral history
- [ ] POST /api/partnerships/{id}/referral - Log referral
- [ ] GET /api/partnerships/{id}/commission - Calculate commission

### 1.4 Business Logic Services (Week 2-3)

#### Notification Service
- [ ] **backend/app/services/notification_service.py**
  - [ ] send_email(recipient, template, data)
  - [ ] send_sms(phone_number, message)
  - [ ] send_push_notification(user_id, title, message)
  - [ ] schedule_notification(type, recipient, datetime, template)
  - [ ] send_lead_alert(lead_data, assigned_to)
  - [ ] send_appointment_reminder(appointment_data, remind_hours_before)

#### Automation Service
- [ ] **backend/app/services/automation_service.py**
  - [ ] execute_workflow(workflow_id, trigger_data)
  - [ ] setup_16_touch_campaign(lead_id)
  - [ ] trigger_review_request(customer_id, days_after_completion)
  - [ ] auto_assign_lead(lead_id, round_robin_or_scoring)
  - [ ] escalate_unresponded_leads(hours_threshold)
  - [ ] send_abandoned_quote_follow_up(project_id, days_since)

#### Analytics Service
- [ ] **backend/app/services/analytics_service.py**
  - [ ] calculate_conversion_rate(date_range, filters)
  - [ ] calculate_revenue_metrics(date_range)
  - [ ] calculate_lead_source_roi(date_range, source)
  - [ ] calculate_team_performance(team_member_id, date_range)
  - [ ] generate_funnel_data(date_range)
  - [ ] forecast_revenue(months_ahead, model='linear')

#### Integration Service
- [ ] **backend/app/services/integration_service.py**
  - [ ] sync_acculynx_leads()
  - [ ] import_callrail_calls()
  - [ ] sync_birdeye_reviews()
  - [ ] import_google_lsa_leads()
  - [ ] send_google_calendar_invite(appointment_data)
  - [ ] trigger_sendgrid_campaign(customer_segment, template_id)

#### Report Service
- [ ] **backend/app/services/report_service.py**
  - [ ] generate_weekly_report(team_member_id)
  - [ ] generate_monthly_executive_report()
  - [ ] export_leads_csv(filters)
  - [ ] generate_invoice_pdf(project_id)
  - [ ] create_proposal_pdf(project_id, template)

### 1.5 Authentication & Authorization (Week 3)
- [ ] **backend/app/services/auth_service.py**
  - [ ] register_user(email, password, role)
  - [ ] login(email, password) → JWT token
  - [ ] refresh_token(refresh_token) → new JWT
  - [ ] logout(token)
  - [ ] request_password_reset(email)
  - [ ] reset_password(token, new_password)
  - [ ] verify_email(token)

- [ ] **backend/app/middleware/auth.py**
  - [ ] @require_auth decorator
  - [ ] @require_role(['admin', 'manager']) decorator
  - [ ] extract_user_from_token(request)

- [ ] **Roles & Permissions**
  - Admin: Full access
  - Manager: View all, manage team
  - Sales: View/edit own leads, create customers
  - Field Tech: View assigned projects, update status

### 1.6 Testing (Week 3)
- [ ] **tests/unit/test_models.py** - Model validation tests
- [ ] **tests/unit/test_lead_scoring.py** - Scoring algorithm tests
- [ ] **tests/unit/test_validators.py** - Validation utility tests
- [ ] **tests/integration/test_leads_api.py** - Leads endpoint tests
- [ ] **tests/integration/test_customers_api.py** - Customers endpoint tests
- [ ] **tests/integration/test_projects_api.py** - Projects endpoint tests
- [ ] **tests/integration/test_auth.py** - Authentication flow tests
- [ ] **tests/integration/test_pusher.py** - Real-time notification tests
- [ ] **pytest.ini** update with coverage targets (>80%)

---

## PHASE 2: Reflex Frontend Development (Weeks 4-6)
**Goal:** Build primary CRM interface with Shadcn-UI components

### 2.1 Project Setup (Week 4, Day 1-2)
- [ ] Initialize Reflex project: `reflex init` in frontend-reflex/
- [ ] Configure Shadcn-UI theme (rxconfig.py)
- [ ] Setup routing structure
- [ ] Create base layout component (sidebar, header, footer)
- [ ] Setup API client (httpx with JWT auth)
- [ ] Configure state management (Reflex State classes)
- [ ] Setup Pusher client for real-time updates

**File Structure:**
```
frontend-reflex/
├── rxconfig.py
├── requirements.txt
├── .env
├── frontend_reflex/
│   ├── __init__.py
│   ├── frontend_reflex.py (main app)
│   ├── components/
│   │   ├── layout.py
│   │   ├── sidebar.py
│   │   ├── header.py
│   │   ├── kpi_card.py
│   │   ├── lead_card.py
│   │   ├── table.py
│   │   ├── modal.py
│   │   └── charts.py
│   ├── pages/
│   │   ├── dashboard.py
│   │   ├── leads.py
│   │   ├── customers.py
│   │   ├── projects.py
│   │   ├── appointments.py
│   │   ├── analytics.py
│   │   └── settings.py
│   ├── state/
│   │   ├── auth_state.py
│   │   ├── leads_state.py
│   │   ├── dashboard_state.py
│   │   └── realtime_state.py
│   └── utils/
│       ├── api_client.py
│       ├── formatters.py
│       └── pusher_client.py
```

### 2.2 Dashboard (Week 4, Day 3-5)
- [ ] **frontend-reflex/pages/dashboard.py**
  - [ ] KPI cards component
    - Total leads today
    - Leads this month
    - Conversion rate (30 days)
    - Revenue MTD
    - Avg response time
    - Hot leads requiring action
  - [ ] Lead temperature distribution (pie chart)
  - [ ] Recent activity feed (last 20 interactions)
  - [ ] Upcoming appointments (next 7 days)
  - [ ] Lead source breakdown (bar chart)
  - [ ] Quick actions panel (new lead, log interaction, schedule appointment)
  - [ ] Real-time lead alerts (Pusher integration)

### 2.3 Lead Management (Week 5, Day 1-3)
- [ ] **frontend-reflex/pages/leads.py**
  - [ ] View toggle: Kanban board / List view / Map view
  - [ ] Kanban board by status
    - Drag and drop to change status
    - Lead cards with score badge, temperature color, source icon
    - Quick actions menu (call, email, assign, convert)
  - [ ] List view with advanced filters
    - Filter by: status, temperature, source, assigned_to, date_range
    - Sort by: score, created_at, last_interaction
    - Bulk actions: assign, export, delete
  - [ ] Lead detail modal
    - Contact information
    - Lead score breakdown visualization
    - Property details (if available)
    - Interaction timeline
    - Related documents
    - Edit form
  - [ ] Create lead form with validation
  - [ ] Real-time updates when leads are created/updated

### 2.4 Customer Management (Week 5, Day 4-5)
- [ ] **frontend-reflex/pages/customers.py**
  - [ ] Customer list with search and filters
  - [ ] Customer profile page
    - Contact and property information
    - Lifetime value display
    - Project history (all projects with status)
    - Interaction timeline
    - Document library
    - Review history
  - [ ] Create customer form
  - [ ] Customer segmentation view (by value, recency, frequency)
  - [ ] Export customer data

### 2.5 Projects & Appointments (Week 6, Day 1-2)

#### Projects
- [ ] **frontend-reflex/pages/projects.py**
  - [ ] Project pipeline view (grouped by status)
  - [ ] Gantt chart for scheduling
  - [ ] Project detail page
    - Project info and financials
    - Status workflow with progress bar
    - Photo upload (before/after gallery)
    - Document management
    - Team assignment
    - Material/labor tracking
  - [ ] Create project form
  - [ ] Invoice generation
  - [ ] Project completion checklist

#### Appointments
- [ ] **frontend-reflex/pages/appointments.py**
  - [ ] Calendar view (month/week/day)
  - [ ] Appointment list view
  - [ ] Create appointment form
    - Customer/lead selection
    - Team member assignment
    - Date/time picker with availability check
    - Appointment type selection
    - Location (auto-populate from lead/customer)
    - Notes
  - [ ] Appointment detail modal
  - [ ] Reschedule/cancel functionality
  - [ ] Send manual reminder button

### 2.6 Analytics & Reports (Week 6, Day 3-4)
- [ ] **frontend-reflex/pages/analytics.py**
  - [ ] Conversion funnel visualization
  - [ ] Revenue analytics
    - Revenue by month (bar chart)
    - Revenue by project type
    - Average project value trend
  - [ ] Team performance dashboard
    - Leaderboard by conversions
    - Response time metrics
    - Individual performance cards
  - [ ] Lead source ROI comparison
  - [ ] Geographic heat map
  - [ ] Date range selector
  - [ ] Export reports to PDF

### 2.7 Settings & Team (Week 6, Day 5)

#### Settings
- [ ] **frontend-reflex/pages/settings.py**
  - [ ] User profile edit
  - [ ] Business information
  - [ ] Working hours configuration
  - [ ] Lead scoring thresholds
  - [ ] Notification preferences
  - [ ] Integration settings (API keys)

#### Team
- [ ] **frontend-reflex/pages/team.py**
  - [ ] Team member list
  - [ ] Create/edit team member
  - [ ] Role assignment
  - [ ] Availability calendar
  - [ ] Performance metrics per member

---

## PHASE 3: Streamlit Analytics Dashboard (Week 7)
**Goal:** Executive-level analytics and reporting interface

### 3.1 Dashboard Setup
- [ ] **frontend-streamlit/app.py** - Main dashboard entry
- [ ] Configure multi-page navigation
- [ ] Setup API client with authentication
- [ ] Add real-time data refresh (st.cache with TTL)
- [ ] Implement responsive layout
- [ ] Add export functionality (CSV, PDF)

### 3.2 Pages

#### Overview Dashboard
- [ ] **frontend-streamlit/pages/1_overview.py**
  - Executive summary with key metrics
  - Revenue trend chart
  - Lead funnel visualization
  - Monthly performance comparison
  - Top 5 team members
  - Alert section (unresponded leads, overdue appointments)

#### Lead Analytics
- [ ] **frontend-streamlit/pages/2_leads_analytics.py**
  - Lead volume trends
  - Conversion funnel with drop-off analysis
  - Lead source comparison
  - Temperature distribution over time
  - Lead score distribution histogram
  - Time-to-conversion analysis

#### Revenue Analytics
- [ ] **frontend-streamlit/pages/3_revenue.py**
  - Revenue forecasting (linear regression)
  - Revenue by geographic area
  - Revenue by project type
  - Average project value trends
  - Win/loss analysis
  - Pipeline value tracking

#### Team Performance
- [ ] **frontend-streamlit/pages/4_team_performance.py**
  - Individual performance cards
  - Response time comparison
  - Conversion rate by team member
  - Activity heatmap (interactions per day)
  - Lead assignment distribution
  - Sales velocity metrics

#### Geographic Analysis
- [ ] **frontend-streamlit/pages/5_geographic.py**
  - Interactive map with Folium
  - Leads by zip code heat map
  - Revenue by city
  - Market penetration analysis
  - Target market opportunity overlay
  - Service area visualization

#### Marketing ROI
- [ ] **frontend-streamlit/pages/6_marketing_roi.py**
  - Cost per lead by channel
  - Conversion rate by source
  - ROI calculation per campaign
  - Attribution modeling
  - Monthly ad spend vs revenue
  - Channel performance trends

### 3.3 Visualizations & Components
- [ ] **frontend-streamlit/components/charts.py**
  - create_funnel_chart()
  - create_revenue_trend()
  - create_geographic_heatmap()
  - create_team_performance_bars()
  - create_forecast_chart()

- [ ] **frontend-streamlit/components/filters.py**
  - date_range_filter()
  - team_member_filter()
  - lead_source_filter()
  - geographic_filter()

- [ ] **frontend-streamlit/utils/export.py**
  - export_to_pdf(report_data, template)
  - export_to_csv(dataframe)
  - schedule_report_email(frequency, recipients)

---

## PHASE 4: Third-Party Integrations (Weeks 8-9)

### 4.1 Core Integrations (Week 8)

#### AccuLynx CRM
- [ ] **backend/app/integrations/acculynx.py**
  - [ ] OAuth2 authentication
  - [ ] Bi-directional lead sync
  - [ ] Project status sync
  - [ ] Customer data sync
  - [ ] Webhook handlers for real-time updates
  - [ ] Error handling and retry logic

#### CallRail
- [ ] **backend/app/integrations/callrail.py**
  - [ ] API authentication
  - [ ] Import call logs
  - [ ] Link calls to leads/customers
  - [ ] Call recording retrieval
  - [ ] Call transcription (via Assembly AI)
  - [ ] Webhook for new calls

#### BirdEye
- [ ] **backend/app/integrations/birdeye.py**
  - [ ] API authentication
  - [ ] Automated review requests
  - [ ] Review import and storage
  - [ ] Sentiment analysis
  - [ ] Review response automation
  - [ ] Webhook for new reviews

#### Google Local Services Ads
- [ ] **backend/app/integrations/google_lsa.py**
  - [ ] API authentication
  - [ ] Lead import
  - [ ] Lead update status sync
  - [ ] Cost per lead tracking

#### SendGrid
- [ ] **backend/app/integrations/sendgrid.py**
  - [ ] Template management
  - [ ] Email campaign triggers
  - [ ] Drip campaign automation
  - [ ] Email analytics import
  - [ ] Unsubscribe handling

#### Twilio
- [ ] **backend/app/integrations/twilio.py**
  - [ ] SMS sending
  - [ ] SMS template library
  - [ ] Scheduled SMS
  - [ ] Two-way SMS handling
  - [ ] SMS opt-out management

### 4.2 Calendar & Communication (Week 8)

#### Google Calendar
- [ ] **backend/app/integrations/google_calendar.py**
  - [ ] OAuth2 authentication
  - [ ] Create calendar events
  - [ ] Update/delete events
  - [ ] Check availability
  - [ ] Send invites to customers

#### Email Templates
- [ ] **backend/app/templates/email/**
  - [ ] lead_assignment.html
  - [ ] appointment_confirmation.html
  - [ ] appointment_reminder.html
  - [ ] review_request.html
  - [ ] quote_sent.html
  - [ ] project_completion.html
  - [ ] follow_up_sequence/ (16 templates)

#### SMS Templates
- [ ] **backend/app/templates/sms/**
  - [ ] lead_response.txt
  - [ ] appointment_reminder.txt
  - [ ] quote_follow_up.txt
  - [ ] review_request.txt

### 4.3 Marketing Automation (Week 9)

#### 16-Touch Follow-Up Campaign
- [ ] **backend/app/workflows/16_touch_campaign.py**
  - Day 1: Immediate response (2 minutes)
  - Day 1: Follow-up email (4 hours later)
  - Day 2: SMS check-in
  - Day 3: Value proposition email
  - Day 5: Case study email
  - Day 7: Phone call
  - Day 10: Limited-time offer email
  - Day 14: Educational content
  - Day 17: Testimonial showcase
  - Day 21: Phone call #2
  - Day 25: Referral request
  - Day 30: Final offer email
  - Day 35: Break-up email
  - Day 40: Last chance email
  - Day 60: Re-engagement attempt
  - Day 90: Cold lead nurture

#### Review Automation
- [ ] **backend/app/workflows/review_automation.py**
  - [ ] Trigger review request 3 days after project completion
  - [ ] Send reminder if no review after 7 days
  - [ ] Second reminder after 14 days
  - [ ] Internal alert if negative review received
  - [ ] Automated thank you for positive reviews

#### Referral Workflows
- [ ] **backend/app/workflows/referral_automation.py**
  - [ ] Request referral 7 days after positive review
  - [ ] Automated referral reward tracking
  - [ ] Thank you for referral email
  - [ ] Referral status updates

### 4.4 Payment & Invoicing (Week 9)

#### Stripe Integration
- [ ] **backend/app/integrations/stripe.py**
  - [ ] Payment intent creation
  - [ ] Deposit collection
  - [ ] Subscription handling (for maintenance plans)
  - [ ] Refund processing
  - [ ] Payment link generation

#### Invoice Generation
- [ ] **backend/app/services/invoice_service.py**
  - [ ] Generate invoice PDF
  - [ ] Email invoice to customer
  - [ ] Payment tracking
  - [ ] Late payment reminders
  - [ ] Receipt generation

---

## PHASE 5: DevOps & Infrastructure (Week 10)

### 5.1 Docker Configuration

#### Multi-Service Orchestration
- [ ] **docker-compose.yml**
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports: ["5000:5000"]
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
    depends_on: [redis]

  reflex:
    build: ./frontend-reflex
    ports: ["3000:3000"]
    environment:
      - API_URL=http://backend:5000

  streamlit:
    build: ./frontend-streamlit
    ports: ["8501:8501"]
    environment:
      - API_URL=http://backend:5000

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  nginx:
    build: ./nginx
    ports: ["80:80", "443:443"]
    depends_on: [backend, reflex, streamlit]
```

#### Dockerfiles
- [ ] **backend/Dockerfile**
- [ ] **frontend-reflex/Dockerfile**
- [ ] **frontend-streamlit/Dockerfile**
- [ ] **nginx/Dockerfile**
- [ ] **nginx/nginx.conf** - Reverse proxy configuration

### 5.2 CI/CD Pipeline (TeamCity)

#### Build Configuration
- [ ] **.teamcity/settings.kts**
  - [ ] Checkout from GitHub
  - [ ] Install dependencies
  - [ ] Run linting (black, ruff, mypy)
  - [ ] Run unit tests
  - [ ] Run integration tests
  - [ ] Security scanning (bandit, safety)
  - [ ] Build Docker images
  - [ ] Push to Docker registry
  - [ ] Deploy to staging
  - [ ] Run smoke tests
  - [ ] Deploy to production (manual trigger)

#### GitHub Actions (Alternative/Supplemental)
- [ ] **.github/workflows/ci.yml** - CI pipeline
- [ ] **.github/workflows/deploy-staging.yml** - Auto-deploy to staging
- [ ] **.github/workflows/deploy-production.yml** - Manual production deploy

### 5.3 Render Deployment

#### Infrastructure as Code
- [ ] **render.yaml**
```yaml
services:
  - type: web
    name: iswitch-roofs-api
    env: python
    buildCommand: pip install -r backend/requirements.txt
    startCommand: gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.app:app
    envVars:
      - key: DATABASE_URL
        sync: false

  - type: web
    name: iswitch-roofs-reflex
    env: python
    buildCommand: pip install -r frontend-reflex/requirements.txt
    startCommand: reflex run --env production

  - type: web
    name: iswitch-roofs-streamlit
    env: python
    buildCommand: pip install -r frontend-streamlit/requirements.txt
    startCommand: streamlit run app.py --server.port $PORT

  - type: redis
    name: iswitch-roofs-redis
    plan: starter
```

#### Environment Variables
- [ ] **render_env_vars.txt** - Document all required env vars
- [ ] Setup Render secrets
- [ ] Configure custom domains
- [ ] Enable auto-deploy from main branch

### 5.4 Monitoring & Logging

#### Sentry Setup
- [ ] **backend/app/monitoring/sentry_config.py**
  - [ ] Error tracking initialization
  - [ ] Performance monitoring
  - [ ] User context tracking
  - [ ] Custom event tracking

#### Logging
- [ ] **backend/app/monitoring/logger_config.py**
  - [ ] Structured logging (JSON format)
  - [ ] Log levels by environment
  - [ ] Sensitive data filtering
  - [ ] Log rotation

#### Uptime Monitoring
- [ ] Setup UptimeRobot monitors
  - API health endpoint
  - Reflex frontend
  - Streamlit dashboard
  - Database connectivity
- [ ] Configure alert thresholds
- [ ] Setup notification channels

#### Performance Monitoring
- [ ] **backend/app/monitoring/performance.py**
  - [ ] Request timing middleware
  - [ ] Database query logging
  - [ ] API endpoint metrics
  - [ ] Real-time connection monitoring

---

## PHASE 6: Testing & Quality Assurance (Week 11)

### 6.1 Backend Testing

#### Unit Tests
- [ ] **tests/unit/test_models.py** - All model validations
- [ ] **tests/unit/test_lead_scoring.py** - Scoring algorithm accuracy
- [ ] **tests/unit/test_validators.py** - Input validation
- [ ] **tests/unit/test_services/** - All service methods

#### Integration Tests
- [ ] **tests/integration/test_auth_flow.py** - Complete auth workflow
- [ ] **tests/integration/test_lead_lifecycle.py** - Create → Convert → Project
- [ ] **tests/integration/test_appointments.py** - Scheduling workflow
- [ ] **tests/integration/test_notifications.py** - Email/SMS sending
- [ ] **tests/integration/test_pusher.py** - Real-time events
- [ ] **tests/integration/test_integrations.py** - Third-party API calls

#### Performance Tests
- [ ] **tests/performance/k6_load_test.js**
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 }, // Ramp up to 100 users
    { duration: '5m', target: 100 }, // Stay at 100 users
    { duration: '2m', target: 200 }, // Ramp up to 200 users
    { duration: '5m', target: 200 }, // Stay at 200 users
    { duration: '2m', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    http_req_failed: ['rate<0.01'],   // Less than 1% errors
  },
};

export default function() {
  // Test lead creation
  let payload = JSON.stringify({
    first_name: 'Test',
    last_name: 'User',
    email: 'test@example.com',
    phone: '2485551234',
    source: 'google_ads'
  });

  let params = {
    headers: { 'Content-Type': 'application/json' },
  };

  let res = http.post('http://localhost:5000/api/leads/', payload, params);
  check(res, {
    'status is 201': (r) => r.status === 201,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });

  sleep(1);
}
```

#### Security Tests
- [ ] **tests/security/test_sql_injection.py**
- [ ] **tests/security/test_xss.py**
- [ ] **tests/security/test_auth_bypass.py**
- [ ] **tests/security/test_rate_limiting.py**

### 6.2 Frontend Testing

#### Reflex Component Tests
- [ ] **frontend-reflex/tests/test_components.py**
- [ ] **frontend-reflex/tests/test_state.py**
- [ ] **frontend-reflex/tests/test_api_client.py**

#### E2E Tests (Playwright)
- [ ] **tests/e2e/test_auth.spec.py** - Login/logout flow
- [ ] **tests/e2e/test_lead_creation.spec.py** - Create and view lead
- [ ] **tests/e2e/test_lead_conversion.spec.py** - Convert lead to customer
- [ ] **tests/e2e/test_project_workflow.spec.py** - Complete project lifecycle
- [ ] **tests/e2e/test_appointment_scheduling.spec.py** - Book appointment
- [ ] **tests/e2e/test_realtime_updates.spec.py** - Verify Pusher updates

```python
# Example E2E test
from playwright.sync_api import Page, expect

def test_create_lead(page: Page):
    page.goto("http://localhost:3000/login")
    page.fill("#email", "admin@iswitchroofs.com")
    page.fill("#password", "password")
    page.click("button:has-text('Login')")

    expect(page).to_have_url("http://localhost:3000/dashboard")

    page.click("a:has-text('Leads')")
    page.click("button:has-text('New Lead')")

    page.fill("#first_name", "John")
    page.fill("#last_name", "Doe")
    page.fill("#email", "john@example.com")
    page.fill("#phone", "(248) 555-1234")
    page.select_option("#source", "google_ads")

    page.click("button:has-text('Create Lead')")

    expect(page.locator(".toast")).to_contain_text("Lead created successfully")
    expect(page.locator("text=John Doe")).to_be_visible()
```

#### Cross-Browser Testing
- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Edge

#### Mobile Responsiveness
- [ ] iPhone 12/13/14
- [ ] iPad
- [ ] Android phones
- [ ] Android tablets

#### Accessibility Testing
- [ ] WCAG 2.1 AA compliance
- [ ] Screen reader compatibility
- [ ] Keyboard navigation
- [ ] Color contrast ratios

### 6.3 Database Testing
- [ ] Migration tests (up and down)
- [ ] Data integrity constraints
- [ ] Performance of complex queries
- [ ] Index effectiveness

### 6.4 User Acceptance Testing
- [ ] Sales team workflow testing
- [ ] Manager reporting validation
- [ ] Field technician app usage
- [ ] Executive dashboard review
- [ ] Mobile usability testing

---

## PHASE 7: Business-Specific Features (Weeks 12-14)

### 7.1 2-Minute Response System (Week 12)

#### Real-Time Lead Alerts
- [ ] **backend/app/services/alert_service.py**
  - [ ] trigger_lead_alert(lead_id) → Pusher + SMS + Email
  - [ ] calculate_available_team_member()
  - [ ] escalate_if_no_response(lead_id, minutes=2)
  - [ ] log_response_time(lead_id, responded_by, seconds)

#### Mobile Notifications
- [ ] **Future: React Native app** (Week 20+)
  - Push notifications for new leads
  - Quick actions (call, text, schedule)
  - Offline mode

#### Response Time Dashboard
- [ ] **frontend-reflex/pages/response_times.py**
  - Average response time by team member
  - Compliance tracking (% under 2 minutes)
  - Alert for leads exceeding threshold
  - Historical trends

### 7.2 Premium Market Features (Week 12)

#### Luxury Property Identification
- [ ] **backend/app/integrations/zillow.py**
  - [ ] Enrich lead with property data (value, size, year built)
  - [ ] Identify premium properties ($500K+)
  - [ ] Auto-boost lead score for luxury homes

#### High-Value Lead Prioritization
- [ ] **backend/app/services/lead_routing.py**
  - [ ] Route leads scoring 80+ to top performers
  - [ ] Special handling workflow for ultra-premium (90+)
  - [ ] White-glove service checklist

#### 3D Modeling & Drone Integration
- [ ] **backend/app/routes/media.py**
  - [ ] Upload 3D models (via Supabase Storage)
  - [ ] Schedule drone inspection
  - [ ] Photo gallery with before/after comparison
  - [ ] Customer-facing portal for viewing

### 7.3 Community Marketing Tools (Week 13)

#### Social Media Scheduler
- [ ] **backend/app/integrations/social_media.py**
  - [ ] Schedule posts to Facebook, Nextdoor
  - [ ] Content calendar
  - [ ] Post performance tracking
  - [ ] Engagement monitoring

#### Community Engagement Tracking
- [ ] **backend/app/models/community_activity.py**
  - [ ] Log Facebook group interactions
  - [ ] Track Nextdoor posts
  - [ ] Measure engagement metrics
  - [ ] Lead attribution to community efforts

#### Ambassador Program
- [ ] **backend/app/routes/ambassadors.py**
  - [ ] Ambassador registration
  - [ ] Referral tracking
  - [ ] Reward calculation
  - [ ] Performance leaderboard

### 7.4 Sales Conversion Tools (Week 13)

#### Objection Handling Library
- [ ] **frontend-reflex/pages/sales_playbook.py**
  - [ ] Searchable objection database
  - [ ] Recommended responses by category
  - [ ] Success rate tracking per response
  - [ ] Add custom objections and responses

#### Call Recording & Transcription
- [ ] **backend/app/integrations/assembly_ai.py**
  - [ ] Transcribe CallRail recordings
  - [ ] Keyword extraction
  - [ ] Sentiment analysis
  - [ ] Flag negative calls for coaching

#### Win/Loss Analysis
- [ ] **backend/app/services/win_loss_analysis.py**
  - [ ] Automated win/loss surveys
  - [ ] Categorize loss reasons
  - [ ] Identify patterns
  - [ ] Generate coaching insights

### 7.5 Partnership Management (Week 14)

#### Insurance Agent Portal
- [ ] **frontend-reflex/pages/partner_portal.py**
  - [ ] Login for partners
  - [ ] Submit referrals
  - [ ] Track referral status
  - [ ] Commission reports

#### Referral Tracking
- [ ] **backend/app/models/referral.py**
  - [ ] Link leads to referring partner
  - [ ] Track conversion of referred leads
  - [ ] Calculate commission owed

#### Co-Marketing Tools
- [ ] **backend/app/services/co_marketing.py**
  - [ ] Generate co-branded materials
  - [ ] Split lead costs
  - [ ] Joint campaign tracking

### 7.6 Advanced Analytics (Week 14)

#### Predictive Lead Scoring (ML)
- [ ] **backend/app/ml/predictive_scoring.py**
  - [ ] Train model on historical conversion data
  - [ ] Features: lead attributes, behavioral data, timing
  - [ ] Predict probability of conversion
  - [ ] Model retraining pipeline

#### Revenue Forecasting
- [ ] **backend/app/services/forecasting.py**
  - [ ] Linear regression model
  - [ ] Seasonal adjustment (storm season)
  - [ ] Pipeline value analysis
  - [ ] Confidence intervals

#### Customer Churn Prediction
- [ ] **backend/app/ml/churn_prediction.py**
  - [ ] Identify at-risk customers
  - [ ] Proactive re-engagement campaigns
  - [ ] Factors contributing to churn

#### Optimal Pricing Model
- [ ] **backend/app/services/pricing_optimizer.py**
  - [ ] Analyze won/lost quotes by price
  - [ ] Recommend pricing by project type and market
  - [ ] Competitive analysis integration

---

## PHASE 8: Documentation & Training (Week 15)

### 8.1 Technical Documentation
- [ ] **docs/API_DOCUMENTATION.md** - Complete API reference with examples
- [ ] **docs/ARCHITECTURE.md** - System architecture diagrams
- [ ] **docs/DATABASE_SCHEMA.md** - ER diagram and table descriptions
- [ ] **docs/DEPLOYMENT.md** - Step-by-step deployment guide
- [ ] **docs/TROUBLESHOOTING.md** - Common issues and solutions
- [ ] **docs/CONTRIBUTING.md** - Developer contribution guidelines
- [ ] **backend/openapi.yaml** - OpenAPI 3.0 specification

### 8.2 User Documentation
- [ ] **docs/user-guide/ADMIN_GUIDE.md**
  - User management
  - System configuration
  - Integration setup
  - Reporting

- [ ] **docs/user-guide/SALES_HANDBOOK.md**
  - Lead management workflow
  - Using the lead scoring system
  - Appointment scheduling
  - Converting leads to customers
  - Sales playbook access

- [ ] **docs/user-guide/FIELD_TECH_GUIDE.md**
  - Project status updates
  - Photo uploads
  - Material tracking
  - Time logging

- [ ] **docs/user-guide/MANAGER_REPORTING.md**
  - Dashboard overview
  - Running reports
  - Team performance tracking
  - Revenue analytics

- [ ] **docs/user-guide/FAQ.md** - Frequently asked questions

### 8.3 Training Materials
- [ ] **Video tutorials** (Loom/YouTube)
  - System overview (5 min)
  - Creating and managing leads (10 min)
  - Scheduling appointments (5 min)
  - Converting leads to customers (8 min)
  - Using the sales playbook (7 min)
  - Running reports (10 min)

- [ ] **Interactive demos** (Reflex tutorial mode)
  - Guided walkthrough of key features
  - Sample data for practice

- [ ] **Onboarding checklist**
  - Account setup
  - First lead creation
  - First appointment scheduled
  - First project created
  - First report run

- [ ] **Best practices guide**
  - Response time best practices
  - Lead qualification tips
  - Effective follow-up strategies
  - Using automation effectively

---

## Implementation Priorities by Business Impact

### 🔥 CRITICAL - Week 1-2 (MVP Core)
**Business Impact: Enable basic lead management and response**

1. ✅ Backend foundation (Flask + Supabase) - COMPLETE
2. ✅ Database schema and migrations - COMPLETE
3. ✅ Pusher real-time integration - COMPLETE
4. [ ] Lead model and scoring algorithm
5. [ ] Basic Leads API (CRUD + list)
6. [ ] 2-minute alert system
7. [ ] Notification service (email/SMS)
8. [ ] Basic Reflex dashboard

**Goal:** Sales team can capture leads, see real-time alerts, and respond quickly

---

### ⭐ HIGH - Week 3-6 (Full CRM)
**Business Impact: Complete sales workflow and visibility**

9. [ ] Complete all REST APIs (customers, projects, appointments)
10. [ ] Authentication & authorization
11. [ ] Full Reflex frontend (all pages)
12. [ ] Kanban lead board
13. [ ] Appointment scheduling
14. [ ] Team assignment logic
15. [ ] CallRail integration (call tracking)
16. [ ] BirdEye integration (reviews)

**Goal:** End-to-end sales workflow from lead to completed project

---

### 📊 MEDIUM - Week 7-10 (Analytics & DevOps)
**Business Impact: Data-driven decisions and operational efficiency**

17. [ ] Streamlit analytics dashboard
18. [ ] Marketing automation (16-touch campaign)
19. [ ] Docker containerization
20. [ ] CI/CD pipeline
21. [ ] Production deployment on Render
22. [ ] AccuLynx integration
23. [ ] Google LSA integration

**Goal:** Executive visibility, automated follow-ups, production-ready system

---

### 💡 NICE-TO-HAVE - Week 11-15 (Advanced Features)
**Business Impact: Competitive differentiation and scaling**

24. [ ] ML-based predictive lead scoring
25. [ ] Revenue forecasting
26. [ ] Partnership portal
27. [ ] Community marketing tools
28. [ ] 3D modeling/drone integration
29. [ ] Advanced analytics (churn prediction, pricing optimization)
30. [ ] Comprehensive testing and documentation

**Goal:** Advanced features for market domination and premium positioning

---

## Success Metrics & KPIs

### Technical Metrics
- [ ] API response time p95 < 500ms
- [ ] Frontend load time < 2 seconds
- [ ] Test coverage > 80%
- [ ] Zero critical security vulnerabilities
- [ ] 99.9% uptime (after week 10)
- [ ] Real-time notification latency < 500ms

### Business Metrics (Post-Launch)
- [ ] Lead response time < 2 minutes (100% compliance)
- [ ] Conversion rate improvement: 8% → 25%
- [ ] Cost per lead: < $100
- [ ] Customer satisfaction: NPS > 75
- [ ] Sales cycle reduction: 30-45 days → 15-20 days
- [ ] Team adoption rate: > 90% daily active users

---

## Risk Mitigation

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Supabase API rate limits | Medium | High | Implement Redis caching, optimize queries |
| Pusher connection limits | Low | Medium | Use channel batching, upgrade plan if needed |
| Third-party API failures | High | Medium | Retry logic, fallback workflows, error handling |
| Data migration complexity | Medium | High | Phased migration, extensive testing, rollback plan |
| Performance degradation | Medium | High | Load testing, query optimization, caching strategy |

### Business Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Low user adoption | Medium | Critical | Comprehensive training, change management, user feedback |
| Data quality issues | High | High | Import validation, cleanup scripts, data governance |
| Integration failures | Medium | Medium | Manual fallback workflows, vendor SLAs |
| Budget overruns | Low | Medium | Phased approach, MVP first, monitor spend |

---

## Resource Requirements

### Development Team (15 weeks)
- **Backend Developer** (Flask/Python) - Full-time
- **Frontend Developer** (Reflex/Streamlit) - Full-time
- **DevOps Engineer** - Part-time (50%)
- **QA Engineer** - Part-time (50%)
- **Project Manager** - Part-time (25%)

### Infrastructure Costs (Monthly)
- Render hosting: $85 (Starter × 3)
- Supabase Pro: $25
- Pusher Startup: $49
- Sentry Team: $26
- Redis Cloud: $0 (free tier)
- Third-party APIs: $615 (CallRail, BirdEye, SendGrid, Twilio)
- **Total: ~$800/month**

### One-Time Costs
- Development: $150K (15 weeks × $10K/week team cost)
- Testing tools: $1K
- Training creation: $2K
- **Total: ~$153K**

---

## Timeline Summary

| Phase | Duration | Deliverable | Business Value |
|-------|----------|-------------|----------------|
| Phase 1 | 3 weeks | Backend API complete | API foundation for all features |
| Phase 2 | 3 weeks | Reflex frontend complete | Sales team can use full CRM |
| Phase 3 | 1 week | Streamlit analytics | Executive visibility |
| Phase 4 | 2 weeks | Integrations | Automated workflows |
| Phase 5 | 1 week | DevOps & deployment | Production-ready system |
| Phase 6 | 1 week | Testing & QA | Quality assurance |
| Phase 7 | 3 weeks | Advanced features | Competitive differentiation |
| Phase 8 | 1 week | Documentation | Training & support |

**Total: 15 weeks to full production**

**MVP Milestone: 7 weeks** (Phases 1-3)
- Complete backend API
- Full Reflex CRM interface
- Basic Streamlit analytics
- 2-minute response system
- Essential integrations (CallRail, BirdEye)

---

## Next Steps (Priority Order)

### Week 1, Day 1-2: Data Models
1. Create backend/app/models/ directory structure
2. Implement Lead model with scoring logic
3. Implement Customer, Project, Interaction models
4. Write model validation tests

### Week 1, Day 3-5: Lead Scoring
1. Implement lead_scoring.py with algorithm
2. Add scoring breakdown calculation
3. Add temperature classification
4. Write comprehensive scoring tests

### Week 2: REST APIs
1. Complete Leads API with all endpoints
2. Complete Customers API
3. Complete Projects API
4. Complete Interactions API
5. Add pagination, filtering, sorting

### Week 3: Core Services & Auth
1. Build notification_service.py
2. Build automation_service.py
3. Implement JWT authentication
4. Add role-based access control
5. Write integration tests

---

## Notes

- This TODO.md file should be updated weekly to track progress
- Each completed task should be marked with a checkbox: [x]
- Blockers should be documented in a BLOCKERS.md file
- Code review required before marking phase complete
- User acceptance testing required before production deploy

---

**Last Updated:** 2025-10-01
**Current Phase:** Phase 1 - Backend API Development
**Next Milestone:** MVP (7 weeks)
**Production Target:** 15 weeks
