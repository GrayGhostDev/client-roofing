# Backend Fix Action Plan

**Date**: 2025-10-21
**Status**: Ready to Deploy
**Time Required**: 15 minutes

---

## ✅ Root Cause Analysis

### Problem Identified:
Backend routes returning 404 on Render despite working locally (203 routes registered).

### Root Causes Found:
1. **NumPy 2.x incompatibility** - Breaking imports (line 79: `numpy==2.2.1`)
2. **DATABASE_URL not set in Render** - Routes fail during initialization
3. **Proxy/SSL issues** - Local Proxyman configuration interfering with testing

### Evidence:
- ✅ Backend works locally: 203 routes registered successfully
- ✅ `/health` endpoint exists at root level
- ✅ `/api/leads` and `/api/business-metrics` routes exist locally
- ❌ All endpoints return "Not Found" on Render
- ⚠️ NumPy 2.x causing import errors: "np.float_ was removed"

---

## 🔧 Fixes Applied

### 1. NumPy Version Downgrade ✅
**File**: `backend/requirements.txt` line 79

**Changed From**:
```
numpy==2.2.1
```

**Changed To**:
```
numpy==1.26.4
```

**Impact**: Fixes import errors in `enhanced_analytics` and `advanced_analytics` routes.

---

## 📋 Deployment Steps (YOU MUST DO)

### Step 1: Commit and Push Fixes (2 minutes)

```bash
cd /Users/grayghostdataconsultants/Development/projects/clients/client-roofing/backend
git add requirements.txt
git commit -m "fix: Downgrade NumPy to 1.26.4 for compatibility

- Fixed NumPy 2.x incompatibility causing import errors
- Enhanced analytics routes were failing with 'np.float_ removed' error
- Downgraded from 2.2.1 to 1.26.4 (last stable 1.x version)

Impact:
- Fixes route registration failures on Render
- All 203 routes should now register successfully
- Resolves 404 errors for /api/leads and /api/business-metrics

🤖 Generated with Claude Code"

git push origin main
```

### Step 2: Verify Render Environment Variables (3 minutes)

**CRITICAL**: Check these environment variables in Render dashboard:

1. Go to: https://dashboard.render.com/
2. Find service: `srv-d3mlmmur433s73abuar0`
3. Click **Environment** tab
4. Verify these variables exist and have values:

**Required Variables**:
- ✅ `DATABASE_URL` - PostgreSQL connection string
  - Format: `postgresql://user:pass@host:port/dbname`
  - If missing: Routes will fail to register!

- ✅ `SUPABASE_URL` - Your Supabase project URL
  - Format: `https://xxxxx.supabase.co`

- ✅ `SUPABASE_KEY` - Supabase anon key
  - Format: `eyJhbGciOi...`

- ✅ `SECRET_KEY` - Flask secret (auto-generated)
- ✅ `JWT_SECRET_KEY` - JWT signing key (auto-generated)

**If DATABASE_URL is missing**:
1. Click "Add Environment Variable"
2. Key: `DATABASE_URL`
3. Value: Your PostgreSQL connection string from Supabase
4. Click "Save"

### Step 3: Trigger Manual Deployment (5 minutes)

**IMPORTANT**: Use "Clear build cache & deploy" to force fresh install of NumPy 1.26.4

1. Render Dashboard → Your service (`srv-d3mlmmur433s73abuar0`)
2. Click **"Manual Deploy"** dropdown (top right)
3. Select **"Clear build cache & deploy"** ⚠️ IMPORTANT!
4. Click **"Deploy"**
5. Wait 3-5 minutes for deployment to complete

**Why clear cache?**
- Forces fresh pip install with NumPy 1.26.4
- Removes cached NumPy 2.2.1 version
- Ensures clean build

### Step 4: Monitor Deployment Logs (2 minutes)

While deploying, watch the logs:

1. Click **"Logs"** tab
2. Look for these SUCCESS messages:
   ```
   ✅ Auth routes registered successfully
   ✅ Leads routes registered successfully
   ✅ Business metrics routes registered successfully
   ✅ Stats routes registered successfully
   ```

3. Look for these ERROR messages (should NOT appear):
   ```
   ❌ Failed to register leads routes
   ❌ Failed to register business metrics routes
   ❌ np.float_ was removed
   ```

4. Deployment complete when you see:
   ```
   ==> Your service is live 🎉
   ```

### Step 5: Test Backend Health (2 minutes)

**Test with correct URL** (bypassing Proxyman):

```bash
# Test health endpoint
curl --noproxy "*" -k "https://srv-d3mlmmur433s73abuar0.onrender.com/health"

# Expected: {"status": "healthy", ...} or similar
# NOT Expected: "Not Found"

# Test leads endpoint
curl --noproxy "*" -k "https://srv-d3mlmmur433s73abuar0.onrender.com/api/leads?limit=1"

# Expected: {"leads": [...]} or data response
# NOT Expected: "Not Found"
```

**If you get "Not Found"**:
- Check Render logs for route registration errors
- Verify DATABASE_URL is set
- Check for import errors in logs

### Step 6: Update Streamlit Cloud Secrets (2 minutes)

1. Go to: https://share.streamlit.io/
2. Find app: **iswitch-roofs**
3. Click ⋮ → **Settings** → **Secrets**
4. Change these 3 lines:

**FROM**:
```toml
api_base_url = "https://iswitch-roof-api.onrender.com"
ml_api_base_url = "https://iswitch-roof-api.onrender.com"
BACKEND_API_URL = "https://iswitch-roof-api.onrender.com"
```

**TO**:
```toml
api_base_url = "https://srv-d3mlmmur433s73abuar0.onrender.com"
ml_api_base_url = "https://srv-d3mlmmur433s73abuar0.onrender.com"
BACKEND_API_URL = "https://srv-d3mlmmur433s73abuar0.onrender.com"
```

5. Click **Save**
6. Wait 30 seconds for app to restart

### Step 7: Test Full Integration (1 minute)

1. Go to: https://iswitch-roofs.streamlit.app/Dashboard
2. **Hard refresh**: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
3. Check sidebar for real data (not demo data)
4. Navigate to "Leads Management" page
5. Verify leads data loads

---

## 🎯 Success Criteria

### ✅ Backend is working if you see:
- `/health` endpoint returns 200 OK
- `/api/leads` returns lead data (not "Not Found")
- Render logs show "routes registered successfully"
- No "np.float_" errors in logs

### ✅ Frontend is working if you see:
- Sidebar shows real metrics (not "📊 Displaying demo data")
- Leads Management page loads real data
- No 404 or 500 errors in browser console

### ❌ Still broken if you see:
- "Not Found" on all endpoints
- "Failed to register" errors in Render logs
- Demo data in Streamlit sidebar
- 404/500 errors in browser console

---

## 🔍 Troubleshooting

### If Backend Still Returns 404:

**Check DATABASE_URL**:
```bash
# In Render logs, look for:
"❌ No database available - using SQLite in-memory"
```
- This means DATABASE_URL is not set!
- Add it in Render Environment tab

**Check for Import Errors**:
```bash
# In Render logs, look for:
"Failed to register X routes: <error message>"
```
- Share the error message
- May need additional dependency fixes

### If Frontend Still Shows Errors:

**Clear All Caches**:
1. Streamlit Cloud → Reboot app
2. Browser → Hard refresh (Cmd/Ctrl + Shift + R)
3. Close all Streamlit tabs
4. Reopen app in new tab

**Verify Secrets**:
1. Streamlit Cloud → Settings → Secrets
2. Confirm URLs show `srv-d3mlmmur433s73abuar0`
3. If not, save again

---

## 📊 Timeline

| Step | Action | Time | Status |
|------|--------|------|--------|
| 1 | Commit NumPy fix | 2 min | ✅ Ready |
| 2 | Verify DATABASE_URL | 3 min | ⏳ User action |
| 3 | Deploy with cache clear | 5 min | ⏳ User action |
| 4 | Monitor logs | 2 min | ⏳ User action |
| 5 | Test backend | 2 min | ⏳ User action |
| 6 | Update Streamlit secrets | 2 min | ⏳ User action |
| 7 | Test integration | 1 min | ⏳ User action |
| **Total** | **Complete fix** | **17 min** | |

---

## 🚀 Quick Commands Reference

```bash
# Commit fix
git add backend/requirements.txt
git commit -m "fix: Downgrade NumPy to 1.26.4 for compatibility"
git push origin main

# Test backend (bypassing Proxyman)
curl --noproxy "*" -k "https://srv-d3mlmmur433s73abuar0.onrender.com/health"
curl --noproxy "*" -k "https://srv-d3mlmmur433s73abuar0.onrender.com/api/leads?limit=1"
```

**Render Dashboard**: https://dashboard.render.com/
**Streamlit Cloud**: https://share.streamlit.io/
**Your App**: https://iswitch-roofs.streamlit.app/Dashboard

**Service ID**: `srv-d3mlmmur433s73abuar0`
**Correct Backend URL**: `https://srv-d3mlmmur433s73abuar0.onrender.com`

---

## ✅ Next Steps

1. **YOU**: Commit and push the NumPy fix (Step 1)
2. **YOU**: Check DATABASE_URL in Render (Step 2)
3. **YOU**: Deploy with cache clear (Step 3)
4. **YOU**: Watch logs for success messages (Step 4)
5. **YOU**: Test endpoints with curl (Step 5)
6. **YOU**: Update Streamlit secrets (Step 6)
7. **YOU**: Test full app (Step 7)

**Expected Result**: Backend connects, data loads, everything works!

---

**Status**: Action plan ready. Waiting for you to execute Steps 1-7.
