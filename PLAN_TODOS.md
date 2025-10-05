# PLAN_TODOS: iSwitch Roofs CRM — Consolidated Implementation Plan (2025)

Last Updated: 2025-10-05
Branch: plan/todos-2025-10-05
Owners: Backend/Infra/Frontend (see PR sequencing)

This document consolidates outstanding TODOs across the repository into a single, prioritized plan aligned with the current 2025 implementation (Flask + Supabase + Pusher + Reflex + Streamlit). It preserves existing global patterns and avoids any duplicate files.

References
- Canonical backlog: TODO.md (repo root)
- Frontend backlog: frontend-reflex/TODO.md
- CI: .github/workflows/ci.yml
- Backend app: backend/app

Guiding constraints (must follow)
- Preserve globals: Do not remove or refactor away existing global constructs, especially frontend_reflex/state.py global app_state.
- No duplicate files: New artifacts must be created exactly at the specified paths below.
- 2025 stack only: Flask 3.1.x, Python 3.11+, Reflex 0.8.13, Supabase, Pusher. No FastAPI references.
- Documentation-first: For any implementation, update related docs and OpenAPI in the same PR.
- Performance budgets: Keep UI rendering within a 16ms budget; use pagination/virtualization and background work.
- Security & secrets: Use env vars only; document all in render_env_vars.txt; never commit secrets.

Decisions & standards
- Backend port source of truth: 8000 (unify compose/nginx later)
- Real-time: Continue with Pusher only. No Reflex WebSocket state dependencies.
- Testing: Maintain >= 80% coverage (pyproject.toml). Mock external APIs.
- Feature flags: Wrap risky features (workflows, 2FA enforcement, integrations) in config flags.

Current state snapshot (from code + TODOs)
- Backend: Comprehensive routes and services exist; Partnerships API marked “in progress”; Realtime route still uses header-derived identity; 2FA TODO in auth_service.py.
- Frontend (Reflex): Core CRM + Kanban + analytics modules implemented; global app_state in use; enhancements pending (bulk ops, pagination, skeletons, dynamic badges, mobile).
- Streamlit: Project skeleton only (requirements.txt) — pages/components/utils not created yet.
- Integrations: Integration modules not present yet (acculynx, callrail, birdeye, google_lsa, sendgrid, twilio, google_calendar, stripe).
- Monitoring/Logging: No dedicated monitoring modules folder yet.
- DevOps: backend Dockerfile exists; compose includes backend/redis/nginx; missing Reflex/Streamlit Dockerfiles; nginx Dockerfile missing; render.yaml not present.
- Docs: Many reports exist; technical and user docs enumerated in root TODO.md still need completion; OpenAPI spec missing.

Backlog by phase (deliverables, exact paths, acceptance criteria)

Phase 2A — Backend services scaffolding and contracts (Flask)
Create only the files; implement minimal contracts with TODOs and docstrings. Add xfail tests to scaffold.
- Files to add
  - backend/app/services/automation_service.py
  - backend/app/services/integration_service.py
  - backend/app/services/report_service.py
  - backend/app/services/invoice_service.py
- Contracts (align with TODO.md; may refine during PR)
  - automation_service: schedule_follow_up, run_campaign, cancel_scheduled_tasks
  - integration_service: enqueue_sync, handle_webhook, get_oauth_credentials
  - report_service: generate_leads_report, generate_revenue_report, export_csv
  - invoice_service: create_invoice, send_invoice, get_invoice_status, refund_invoice
- Acceptance
  - Files created with typed signatures and TODO markers
  - Unit test scaffolds added (xfail)

Phase 2B — Workflows (campaigns/automation)
- Files to add
  - backend/app/workflows/16_touch_campaign.py
  - backend/app/workflows/review_automation.py
  - backend/app/workflows/referral_automation.py
- Notes
  - Orchestrate via automation_service; idempotency keys; Redis queue for scheduling; audit to Supabase.
- Acceptance
  - Expose run_for_lead(lead_id, context) and enqueue_for_segment(segment_filter)
  - Dry-run mode (no side-effects)

Phase 2C — Partnerships API parity
- Verify and complete endpoints marked “IN PROGRESS” in backend/app/routes/partnerships.py.
- Acceptance
  - CRUD and metrics endpoints working with validation and RBAC
  - Integration tests added

Phase 2D — Realtime identity & Auth 2FA
- Realtime identity
  - backend/app/routes/realtime.py: replace header-derived identity with JWT/session (e.g., get_jwt_identity() or session)
- 2FA
  - backend/app/services/auth_service.py: implement TOTP (pyotp), backup codes, rate limiting; add tests
- Acceptance
  - Realtime routes read identity from verified context only
  - 2FA flow: enroll → verify → login → backup codes; unit tests pass

Phase 2E — services/__init__.py exports
- Update backend/app/services/__init__.py to export lead scoring and shared services as needed without import cycles.
- Acceptance
  - from app.services import lead_scoring works where used

Phase 2F — Monitoring & logging modules
- Files to add
  - backend/app/monitoring/sentry_config.py
  - backend/app/monitoring/logger_config.py
  - backend/app/monitoring/performance.py
- Acceptance
  - Sentry init callable from app factory
  - Structured logging with PII masking utility and tests
  - Request timing middleware hooks

Phase 3 — Reflex frontend enhancements (Reflex 0.8.13)
- Scope
  - Bulk operations: multi-select, bulk status update, export, assignment
  - Performance: skeleton loaders, query caching, server-side pagination for large lists
  - Advanced filters/search: combinable filters, saved presets, tagging
  - Notifications/alerts: follow-ups and activity alerts (Pusher-driven)
  - Mobile responsiveness; fix sitemap warnings; dynamic badges from state
  - Future stubs behind flags: a11y review, dark mode toggle, keyboard shortcuts, i18n
- Constraints
  - Preserve global app_state usage in frontend_reflex/state.py
- Acceptance
  - Smooth rendering under load with pagination and skeletons
  - Saved filters persisted
  - No regression to global state pattern

Phase 3.1 — Dockerize Reflex frontend
- Files to add
  - frontend-reflex/Dockerfile
- Compose profile update (later in Phase 5)
- Acceptance
  - Image builds; healthcheck in compose

Phase 4 — Streamlit analytics app scaffolding
- Files to add
  - frontend-streamlit/app.py
  - frontend-streamlit/pages/{overview.py,leads_analytics.py,revenue.py,team_performance.py,geographic.py,marketing_roi.py}
  - frontend-streamlit/components/{charts.py,filters.py}
  - frontend-streamlit/utils/export.py
  - frontend-streamlit/Dockerfile
- Acceptance
  - docker compose --profile streamlit up serves basic pages with sample queries

Phase 4.2 — Third-party integrations (clients + webhooks)
- Files to add
  - backend/app/integrations/{acculynx.py,callrail.py,birdeye.py,google_lsa.py,sendgrid.py,twilio.py,google_calendar.py,stripe.py}
- Notes
  - Load credentials via app.config; retries/backoff with jitter; webhook signature verification where supported
- Acceptance
  - Thin clients implemented; unit tests with HTTP mocks
  - render_env_vars.txt lists all required env vars

Phase 5 — DevOps (compose, nginx, Render)
- Files/changes
  - docker-compose.yml: add profiles for reflex (3001) and streamlit (8501); unify backend to 8000; healthchecks
  - nginx/Dockerfile (new)
  - Adjust nginx/nginx.conf upstreams to backend:8000, route /api to backend, optional /app to Reflex, /analytics to Streamlit
  - render.yaml (new) with backend/reflex/streamlit/redis services
- Acceptance
  - compose up works locally with default profile (backend+redis+nginx)
  - Render deployable spec present

Phase 5.4 — SLOs & operational readiness
- Wire Sentry init, structured logging, and define health/readiness endpoints
- Document UptimeRobot monitors and alert thresholds
- Acceptance
  - Test exception visible in Sentry
  - TROUBLESHOOTING.md updated with logging queries

Phase 6 — Testing & QA expansion (>=80% coverage)
- Add unit/integration tests for new services, workflows, routes, integrations, and realtime/2FA
- Acceptance
  - CI coverage >= 80%; flaky tests quarantined

Phase 7 — Documentation & OpenAPI
- Files to add/update
  - docs/API_DOCUMENTATION.md
  - docs/ARCHITECTURE.md
  - docs/DATABASE_SCHEMA.md
  - docs/DEPLOYMENT.md
  - docs/TROUBLESHOOTING.md
  - docs/CONTRIBUTING.md
  - backend/openapi.yaml
  - render_env_vars.txt (root, new)
- Acceptance
  - Docs consistent, Flask terminology only; OpenAPI validates

Phase 8 — CI/CD updates
- Extend CI as needed to build Reflex/Streamlit images (optional) and include new tests
- Acceptance
  - CI green; caches effective; coverage gate enforced

Environment variables (to finalize in render_env_vars.txt)
Core
- FLASK_ENV, SECRET_KEY, JWT_SECRET_KEY
- SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY
- REDIS_URL

Realtime
- PUSHER_APP_ID, PUSHER_KEY, PUSHER_SECRET, PUSHER_CLUSTER

Monitoring
- SENTRY_DSN, SENTRY_ENVIRONMENT, SENTRY_RELEASE

Email/SMS
- SENDGRID_API_KEY, SENDGRID_WEBHOOK_VERIFICATION_KEY (optional)
- TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_MESSAGING_SERVICE_SID, TWILIO_WEBHOOK_SECRET (optional)

Payments & Calendars
- STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
- GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN (or service account)

Vertical/Reviews/Calls
- ACCULYNX_API_KEY
- BIRDEYE_API_KEY
- CALLRAIL_API_KEY
- GOOGLE_ADS_DEVELOPER_TOKEN (or LSA credentials)

Milestones & PR sequencing (small, reviewable units)
1) Services scaffolding (Phase 2A) + xfail tests
2) Workflows (Phase 2B) — feature-flagged
3) Partnerships parity + Realtime identity + 2FA (Phases 2C–2D)
4) Monitoring/logging modules (Phase 2F)
5) Integrations (Phase 4.2) in batches: Comms → Billing → Marketing → LSA
6) Reflex features + Dockerfile (Phases 3 & 3.1)
7) Streamlit scaffold + Dockerfile (Phase 4)
8) DevOps: compose/nginx/render.yaml (Phase 5)
9) Docs + OpenAPI + env vars (Phase 7)
10) CI refinements and final coverage (Phase 8)

Acceptance criteria summary (end-state)
- Backend
  - Services/workflows integrated; partnerships complete; realtime uses JWT/session; 2FA functional
  - Monitoring/logging operational; /health stable
- Frontend (Reflex)
  - Bulk ops, pagination, filters, notifications, mobile responsiveness; Dockerized; globals preserved
- Analytics (Streamlit)
  - App scaffolded with six analytics pages; exports; Dockerized
- Integrations
  - Thin clients with retry/backoff and webhook verification; env vars documented
- DevOps
  - compose profiles (backend+nginx+redis default; reflex and streamlit optional), nginx aligned to ports, render.yaml ready
- Quality
  - >=80% test coverage; CI green
- Docs
  - Technical and user docs updated; OpenAPI present; render_env_vars.txt complete

Risks & mitigations
- Third-party API availability and rate limits → Retry/backoff, mocks in tests, feature flags, queue throttles
- Performance regressions in UI → Server-side pagination, skeleton loaders, virtualization
- Import cycles when exporting services → Use local imports, keep __all__ lean
- Secret handling → Strict reliance on env, never commit secrets

Rollback strategy
- All high-risk features behind flags; reverts limited to single PR scope
- Default to minimal, mocked, or dry-run behavior where possible

Change log policy
- Each PR must update this PLAN_TODOS.md (or relevant docs) and reference exact paths changed
- Keep a short “Docs Updated” checklist in PR descriptions
