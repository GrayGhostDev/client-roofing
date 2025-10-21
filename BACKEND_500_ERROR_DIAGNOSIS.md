# 🚨 Backend 500 Error Diagnosis

**Date:** 2025-10-20
**Issue:** Backend returning 500 Internal Server Error and timeouts
**Previous Status:** 503 Degraded (SQLite fallback mode)
**Current Status:** 500 errors suggest backend may be crashing

---

## 📊 Error Patterns from Streamlit Cloud Logs

```
Health check failed: HTTPSConnectionPool(host='iswitch-roof-api.onrender.com', port=443): Read timed out. (read timeout=5)

API request failed: 500 Server Error: Internal Server Error for url: https://iswitch-roof-api.onrender.com/api/customers/?limit=100

API request failed: HTTPSConnectionPool(host='iswitch-roof-api.onrender.com', port=443): Read timed out. (read timeout=30)
```

---

## 🔍 Analysis

### Change in Error Pattern

**Before (Working but Degraded):**
- Status: `503 Service Unavailable`
- Response: JSON with database error details
- Backend: Running in SQLite fallback mode

**Now (Broken):**
- Status: `500 Internal Server Error`
- Response: Timeouts (30 seconds)
- Backend: Likely crashing on database operations

### Most Likely Causes

1. **Backend Crash on Startup** - Database connection failing catastrophically
2. **SQLite Table Errors** - API endpoints trying to query non-existent tables
3. **Database Migration Issues** - Schema mismatch
4. **Memory/Resource Limits** - Render free tier limits exceeded

---

## 🚨 Critical Issue: SQLite Can't Handle Production Schema

The backend code expects PostgreSQL tables that don't exist in SQLite:

### Expected Tables (from backend code):
- `leads` - Lead management
- `customers` - Customer data
- `projects` - Project tracking
- `users` - User authentication
- `activities` - Activity logs
- `appointments` - Scheduling
- `contracts` - Contract management
- `invoices` - Billing
- `payments` - Payment tracking
- Many more...

### SQLite In-Memory:
- ❌ No tables created
- ❌ No schema initialized
- ❌ Empty database

**When Streamlit tries to fetch `/api/customers/?limit=100`:**
```python
# Backend tries to query SQLite
session.query(Customer).limit(100).all()

# SQLite responds
# sqlite3.OperationalError: no such table: customers

# Flask returns
# 500 Internal Server Error
```

---

## 🎯 Why DATABASE_URL is ABSOLUTELY CRITICAL

### With DATABASE_URL (PostgreSQL):
1. ✅ Backend connects to Supabase
2. ✅ Tables already exist in Supabase
3. ✅ Schema is properly initialized
4. ✅ API endpoints work
5. ✅ Real data available

### Without DATABASE_URL (SQLite):
1. ❌ Backend falls back to SQLite
2. ❌ No tables exist
3. ❌ API queries crash
4. ❌ 500 errors everywhere
5. ❌ Complete failure

---

## 📋 Immediate Actions Required

### Action 1: Add DATABASE_URL to Render (CRITICAL)

**This is not optional. The backend CANNOT function without it.**

1. Go to: https://dashboard.render.com/
2. Select: `iswitch-roofs-api`
3. Environment tab
4. Add:
   ```
   DATABASE_URL=postgresql://postgres:1vJvs55RSiJ3JhWO@db.tdwpzktihdeuzapxoovk.supabase.co:5432/postgres
   ```
5. Save and wait for redeploy

### Action 2: Check Render Logs

**Look for these error messages in Render logs:**

```
❌ No database available - using SQLite in-memory
sqlite3.OperationalError: no such table: leads
sqlite3.OperationalError: no such table: customers
[ERROR] Exception on /api/customers/ [GET]
```

### Action 3: Verify Supabase Database Has Tables

**Check Supabase Dashboard:**
1. Go to: https://supabase.com/dashboard/project/tdwpzktihdeuzapxoovk
2. Click: Table Editor
3. Verify these tables exist:
   - leads
   - customers
   - projects
   - users

**If tables are missing:**
- Need to run database migrations
- Use backend migration scripts
- Or create tables manually in Supabase

---

## 🔍 Diagnostic Commands

### Test Backend Health:
```bash
curl https://iswitch-roof-api.onrender.com/health
```

**Expected (Bad - Current State):**
```json
{
  "status": "degraded",
  "database": {"connected": false}
}
```
**Or:** `500 Internal Server Error` (crash)

**Expected (Good - After Fix):**
```json
{
  "status": "healthy",
  "database": {
    "connected": true,
    "latency_ms": 150
  }
}
```

### Test API Endpoint:
```bash
curl https://iswitch-roof-api.onrender.com/api/leads/?limit=1
```

**Current Response:**
- `500 Internal Server Error`
- Or timeout after 30 seconds

**After Fix:**
- `200 OK`
- JSON array with lead data

---

## 📊 Database Connection Flow

```
1. Backend Starts
   ↓
2. Tries to load DATABASE_URL
   ↓
   ├─ ✅ Found → Connects to Supabase PostgreSQL
   │                ↓
   │              Tables exist
   │                ↓
   │              API endpoints work
   │                ↓
   │              Status: 200 OK
   │
   └─ ❌ Missing → Falls back to SQLite in-memory
                     ↓
                   No tables
                     ↓
                   API queries crash
                     ↓
                   Status: 500 Error
```

---

## ⏱️ Timeline of Backend Behavior

### Phase 1: Initial Deployment (No DATABASE_URL)
- Backend starts successfully
- Falls back to SQLite
- `/health` returns `503 degraded`
- `/api/*` endpoints crash with `500` errors

### Phase 2: After Adding DATABASE_URL
- Render triggers automatic redeploy (2-3 minutes)
- Backend starts with PostgreSQL connection
- `/health` returns `200 healthy`
- `/api/*` endpoints return data

### Phase 3: Production Ready
- All endpoints functional
- Real data from Supabase
- Streamlit can fetch data
- System fully operational

---

## 🚨 Critical Reminder

**The backend architecture REQUIRES PostgreSQL:**

1. **Health Check** (`app/__init__.py:97-127`) - Calls `check_database_health()`
2. **Database Utils** (`app/utils/database.py:38-96`) - Expects DATABASE_URL
3. **All API Routes** - Query database tables
4. **SQLAlchemy Models** - Designed for PostgreSQL features
5. **Connection Pooling** - QueuePool for PostgreSQL, not StaticPool for SQLite

**SQLite is only an emergency fallback for local development, NOT production.**

---

## ✅ Solution Summary

**Problem:** Backend using SQLite in-memory (no tables) → API crashes → 500 errors

**Solution:** Add DATABASE_URL to Render → Backend uses PostgreSQL → Tables exist → API works

**Status:** Waiting for DATABASE_URL to be added to Render environment variables

**ETA:** 5-10 minutes after DATABASE_URL is added (automatic redeploy)

---

**Priority:** 🔴 CRITICAL - System completely non-functional
**Action Required:** Add DATABASE_URL to Render dashboard IMMEDIATELY
**Documentation:** All steps detailed in `RENDER_DEPLOYMENT_FIX_NOW.md`
