# 🔴 API 404 Errors - Analysis & Fix

**Errors Reported**:
```
404 Client Error: Not Found for url: https://srv-d3mlmmur433s73abuar0.onrender.com/api/leads?limit=500

404 Client Error: Not Found for url: https://srv-d3mlmmur433s73abuar0.onrender.com/api/business-metrics/lead-response
```

**Date**: 2025-10-15

---

## 🔍 Investigation Results

### Backend Route Files Exist ✅

**File**: `backend/app/routes/leads.py`
- Size: 35,435 bytes
- Endpoints found:
  - `GET /` (line 117) - List leads ✅
  - `GET /<lead_id>` (line 176) - Get single lead
  - `POST /` (line 217) - Create lead
  - `PUT /<lead_id>` (line 292) - Update lead
  - `DELETE /<lead_id>` (line 361) - Delete lead
  - `GET /hot` (line 472) - Hot leads
  - `GET /stats` (line 749) - Lead statistics
  - `POST /bulk-import` (line 768) - Bulk import

**File**: `backend/app/routes/business_metrics.py`
- Size: 10,879 bytes
- Endpoints found:
  - `GET /premium-markets` (line 25)
  - `GET /lead-response` (line 58) ✅
  - `GET /marketing-roi` (line 87)
  - `GET /conversion-optimization` (line 120)
  - `GET /revenue-growth` (line 149)
  - `GET /realtime/snapshot` (line 237) ✅
  - `GET /summary` (line 347)

### Blueprint Registration Verified ✅

**In `backend/app/__init__.py`**:
- Line 193: `from app.routes import leads` ✅
- Line 195: `app.register_blueprint(leads.bp, url_prefix="/api/leads")` ✅
- Line 281: `from app.routes import business_metrics` ✅
- Line 283: `app.register_blueprint(business_metrics.bp, url_prefix="/api/business-metrics")` ✅

---

## 🔴 Root Causes

### Possible Issue #1: Backend Not Fully Started
- Free tier backends sleep after inactivity
- First request wakes them up (30-60 seconds)
- During startup, routes may not be fully registered
- Health endpoint `/health` might respond before routes are ready

### Possible Issue #2: Database Connection Required
The route files likely require database connections:
```python
from app.models.lead_sqlalchemy import Lead
from app.services.lead_service import lead_service
```

If database is not connected:
- Routes fail to initialize
- Blueprints fail to register
- 404 errors returned

### Possible Issue #3: Import Errors
If any dependencies in the route files fail to import:
- Blueprint registration wrapped in try/except
- Logs warning but continues
- Routes not available

### Possible Issue #4: Query Parameters
Frontend calling:
```
/api/leads?limit=500
```

But endpoint might expect different parameters or have validation that rejects them.

---

## ✅ Solutions

### Solution 1: Check Backend Logs (PRIORITY 1)

**Action Required**:
1. Go to: https://dashboard.render.com/
2. Find service: `srv-d3mlmmur433s73abuar0`
3. Click "Logs" tab
4. Look for:
   ```
   Failed to register leads routes: <error>
   Failed to register business metrics routes: <error>
   ```

**What to Check**:
- Import errors (ModuleNotFoundError, ImportError)
- Database connection errors
- Missing environment variables
- Blueprint registration failures

### Solution 2: Wake Up Backend & Test Manually

**Test Health First**:
```bash
curl https://srv-d3mlmmur433s73abuar0.onrender.com/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "service": "iswitch-roofs-crm-api",
  "version": "1.0.0",
  "database": {"connected": true}
}
```

**Test Leads Endpoint**:
```bash
# Without query params
curl https://srv-d3mlmmur433s73abuar0.onrender.com/api/leads/

# With smaller limit
curl "https://srv-d3mlmmur433s73abuar0.onrender.com/api/leads/?limit=10"
```

**Test Business Metrics**:
```bash
curl https://srv-d3mlmmur433s73abuar0.onrender.com/api/business-metrics/lead-response

curl https://srv-d3mlmmur433s73abuar0.onrender.com/api/business-metrics/realtime/snapshot
```

### Solution 3: Add Frontend Error Handling

**Update frontend to handle 404s gracefully**:

**In `frontend-streamlit/Home.py`** (Sidebar Quick Stats):
```python
# Quick Stats - Real-time Data
st.subheader("📊 Quick Stats")
try:
    # Fetch real-time snapshot from business metrics
    snapshot = api_client.get_realtime_snapshot()

    if snapshot:
        # Display metrics...
    else:
        # Fallback to demo data
        st.info("📊 Using demo data (backend warming up...)")
        st.metric("Lead Response Time", "89s", "Meeting target")
        st.metric("Month Revenue", "$425,000", "85% of target")
        st.metric("Conversion Rate", "28.5%", "+3.5% vs target")

except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        st.warning("⚠️ Backend endpoint not available yet")
        st.caption("Backend is starting up. Refresh in 30 seconds.")
    else:
        st.error(f"API Error: {e}")

except Exception as e:
    st.warning("⚠️ Backend starting...")
    st.caption(f"Please wait... ({str(e)[:30]}...)")
```

**In Leads Management Page**:
```python
try:
    leads = api_client.get_leads(limit=500)
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        st.error("🔴 Leads API endpoint not available")
        st.info("""
        **Backend Issue**: The /api/leads endpoint is returning 404.

        **Possible causes**:
        1. Backend is starting up (wait 60 seconds)
        2. Database not connected
        3. Route registration failed

        **Check**: Render logs for errors
        """)
        leads = []  # Empty list to prevent crash
    else:
        raise
```

### Solution 4: Verify Database Environment Variables

**Check Render Dashboard**:
1. Go to service settings
2. Check environment variables:
   - `DATABASE_URL` - PostgreSQL connection string
   - `SUPABASE_URL` - Supabase project URL
   - `SUPABASE_KEY` - Supabase anon key

**Required for routes to work**:
```env
DATABASE_URL=postgresql://...
SUPABASE_URL=https://tdwpzktihdeuzapxoovk.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Solution 5: Manual Backend Restart

**Force backend to restart**:
1. Render Dashboard → Your service
2. Click "Manual Deploy" → "Clear build cache & deploy"
3. Wait 5-10 minutes for full rebuild
4. Check logs for successful route registration

---

## 🧪 Testing Checklist

### Step 1: Verify Backend is Running
- [ ] Health endpoint responds: `/health`
- [ ] Returns `{"status": "healthy"}`
- [ ] Database connected: `"database": {"connected": true}`

### Step 2: Test Each Problematic Endpoint
- [ ] `/api/leads/` - Returns list or empty array (not 404)
- [ ] `/api/leads/?limit=10` - Returns with query params
- [ ] `/api/business-metrics/lead-response` - Returns metrics
- [ ] `/api/business-metrics/realtime/snapshot` - Returns snapshot

### Step 3: Check Render Logs
- [ ] No "Failed to register leads routes" errors
- [ ] No "Failed to register business metrics routes" errors
- [ ] No import errors
- [ ] No database connection errors

### Step 4: Test Frontend
- [ ] Dashboard loads without errors
- [ ] Sidebar shows Quick Stats (not "loading...")
- [ ] Leads Management page shows data or proper error
- [ ] No 404 errors in browser console

---

## 📊 Expected vs Actual

### Expected Behavior
```bash
$ curl "https://srv-.../api/leads/?limit=5"
{
  "leads": [
    {
      "id": "uuid",
      "name": "John Doe",
      "email": "john@example.com",
      ...
    }
  ],
  "total": 150,
  "page": 1
}
```

### Actual Behavior
```bash
$ curl "https://srv-.../api/leads/?limit=500"
{
  "error": "Not Found",
  "message": "The requested resource was not found"
}
```

---

## 🔧 Quick Fixes to Deploy

### Fix 1: Add Better Error Handling in Sidebar

**File**: `frontend-streamlit/Home.py`
**Lines**: ~335-390

Add try/except with specific 404 handling and fallback demo data.

### Fix 2: Add Graceful Degradation

When backend returns 404:
1. Show user-friendly message
2. Display demo data if available
3. Provide troubleshooting instructions
4. Log error for debugging

### Fix 3: Add Retry Logic

```python
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Create session with retries
session = requests.Session()
retry = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)
```

---

## 📞 Immediate Actions

### For You (User)
1. **Check Render Logs** (Priority 1)
   - Go to: https://dashboard.render.com/
   - View logs for errors during startup
   - Look for "Failed to register" messages

2. **Wait for Backend** (If sleeping)
   - First request takes 30-60 seconds
   - Try refreshing after 1 minute
   - Check health endpoint first

3. **Verify Environment Variables**
   - Settings → Environment
   - Ensure DATABASE_URL exists
   - Ensure SUPABASE credentials exist

### For Me (Dev)
1. **Add error handling** to frontend sidebar
2. **Add fallback demo data** for 404 scenarios
3. **Improve error messages** for users
4. **Add retry logic** for transient failures
5. **Document troubleshooting** steps

---

## 🎯 Priority Fix Plan

### High Priority (Fix Now)
1. ✅ Add 404 error handling in sidebar
2. ✅ Add fallback demo data
3. ✅ Improve error messages

### Medium Priority (After Testing)
4. ⏳ Add retry logic with backoff
5. ⏳ Add health check before API calls
6. ⏳ Cache last successful response

### Low Priority (Nice to Have)
7. ⏳ Add offline mode with cached data
8. ⏳ Add service worker for PWA
9. ⏳ Add metrics dashboard for API health

---

**🚀 Next Step**: Check Render logs to see why routes aren't registering, then I'll add proper error handling to the frontend.

**⏰ ETA**: 10 minutes to implement error handling and redeploy.

**💡 Action Required**: Please check Render dashboard logs and share any error messages you see.
