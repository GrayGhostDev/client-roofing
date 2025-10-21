# 🚨 CRITICAL: Backend URL Mismatch Found

**Date**: 2025-10-21
**Status**: URGENT FIX REQUIRED
**Impact**: Frontend cannot connect to backend - showing 500 errors

---

## 🔴 Problem Identified

**Screenshot Evidence**: Frontend is trying to connect to:
```
https://iswitch-roof-api.onrender.com/api/leads?limit=500
```

**Result**:
```
API Error: 500 Server Error: Internal Server Error
```

---

## 🎯 Root Cause

**Streamlit Cloud secrets are using the wrong backend URL.**

**Current Configuration** (WRONG):
```toml
# In Streamlit Cloud secrets
api_base_url = "https://iswitch-roof-api.onrender.com"
ml_api_base_url = "https://iswitch-roof-api.onrender.com"
BACKEND_API_URL = "https://iswitch-roof-api.onrender.com"
```

**Question**: Which URL is correct?

### Option 1: Render Service URL (From Previous Errors)
```
https://srv-d3mlmmur433s73abuar0.onrender.com
```
- This was in your previous 404 error messages
- This is the default Render service URL
- Format: `srv-{service-id}.onrender.com`

### Option 2: Custom Domain (From secrets.toml)
```
https://iswitch-roof-api.onrender.com
```
- This is in your local secrets.toml file
- Could be a custom domain you set up in Render
- Friendlier URL format

---

## 🔍 How to Determine Correct URL

### Step 1: Check Render Dashboard

1. Go to https://dashboard.render.com/
2. Find your backend service (likely named "iswitch-roof-api" or similar)
3. Look at the top of the service page for the URL
4. You'll see either:
   - **Default URL**: `https://srv-XXXXX.onrender.com`
   - **Custom Domain**: `https://iswitch-roof-api.onrender.com` (if you added it)

### Step 2: Test URLs Manually

**Test Default Render URL**:
```bash
curl https://srv-d3mlmmur433s73abuar0.onrender.com/health
```

**Test Custom Domain**:
```bash
curl https://iswitch-roof-api.onrender.com/health
```

**One of these should return**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-21T...",
  ...
}
```

---

## 🛠️ Fix Instructions

### If Correct URL is `srv-d3mlmmur433s73abuar0.onrender.com`:

**Update Streamlit Cloud Secrets**:

1. Go to https://share.streamlit.io/
2. Find your app: `iswitch-roofs`
3. Click **Settings** → **Secrets**
4. Find these lines and change them:

```toml
# CHANGE FROM:
api_base_url = "https://iswitch-roof-api.onrender.com"
ml_api_base_url = "https://iswitch-roof-api.onrender.com"
BACKEND_API_URL = "https://iswitch-roof-api.onrender.com"

# CHANGE TO:
api_base_url = "https://srv-d3mlmmur433s73abuar0.onrender.com"
ml_api_base_url = "https://srv-d3mlmmur433s73abuar0.onrender.com"
BACKEND_API_URL = "https://srv-d3mlmmur433s73abuar0.onrender.com"
```

5. Click **Save**
6. App will auto-restart
7. Test the connection

### If Correct URL is `iswitch-roof-api.onrender.com`:

**Then the URL is already correct** but the backend service at that URL is returning 500 errors.

This means the backend has a different problem:
- Internal server error
- Database connection failure
- Environment variables missing
- Code error in the backend

---

## 🔍 Additional Debugging

### Check Both URLs

**Test with curl to see which responds**:

```bash
# Test default Render URL
curl -v https://srv-d3mlmmur433s73abuar0.onrender.com/health

# Test custom domain
curl -v https://iswitch-roof-api.onrender.com/health

# Test leads endpoint (default URL)
curl -v https://srv-d3mlmmur433s73abuar0.onrender.com/api/leads?limit=1

# Test leads endpoint (custom domain)
curl -v https://iswitch-roof-api.onrender.com/api/leads?limit=1
```

**Expected Responses**:
- **200 OK**: Backend is working, URL is correct
- **404 Not Found**: Backend is running but routes not registered
- **500 Internal Server Error**: Backend has internal errors
- **Connection timeout**: Backend is not running or URL is wrong

### Check Render Service Configuration

1. Render Dashboard → Your service
2. Check **"Settings"** tab:
   - Look for "Custom Domains" section
   - See if `iswitch-roof-api.onrender.com` is listed
3. Check **"Environment"** tab:
   - Verify DATABASE_URL is set
   - Verify SUPABASE_URL and SUPABASE_KEY are set

---

## 📊 Error Analysis

### Current Error: 500 Internal Server Error

**What 500 means**:
- Backend is reachable (URL is correct)
- But backend code is crashing
- Check backend logs for Python traceback

**Possible causes**:
1. **Database connection failure**
   - DATABASE_URL not set or incorrect
   - PostgreSQL database not accessible
   - Connection pool exhausted

2. **Missing environment variables**
   - SUPABASE_URL, SUPABASE_KEY missing
   - SECRET_KEY, JWT_SECRET_KEY missing
   - Other required config missing

3. **Code errors in backend**
   - Import errors in route files
   - Syntax errors
   - Runtime exceptions

4. **Dependency issues**
   - Missing Python packages
   - Version conflicts
   - Build failed

---

## 🚀 Immediate Action Plan

### Step 1: Verify Backend URL (2 minutes)

Go to Render Dashboard and confirm which URL is correct:
- [ ] Default: `srv-d3mlmmur433s73abuar0.onrender.com`
- [ ] Custom: `iswitch-roof-api.onrender.com`

### Step 2: Test Backend Health (2 minutes)

```bash
curl https://[CORRECT_URL]/health
```

If you get 500 error, proceed to Step 3.

### Step 3: Check Backend Logs (5 minutes)

1. Render Dashboard → Your service → **Logs** tab
2. Look for recent errors (red text)
3. Search for:
   - "Traceback"
   - "Error"
   - "Exception"
   - "Failed"
   - "Database"

### Step 4: Fix Based on Logs

**If logs show "Database connection failed"**:
- Check DATABASE_URL environment variable in Render
- Verify PostgreSQL database is running
- Test database connection manually

**If logs show "ModuleNotFoundError"**:
- Check requirements.txt has all dependencies
- Trigger manual redeploy with cache clear

**If logs show "SUPABASE_URL not found"**:
- Add missing environment variables in Render
- Restart service

### Step 5: Update Streamlit Secrets (2 minutes)

Once you know the correct URL, update Streamlit Cloud secrets.

### Step 6: Test Connection (2 minutes)

After fixing:
1. Refresh Streamlit Cloud app
2. Check if error changes from 500 to 200
3. Verify real data loads

---

## 📝 URLs Summary

### What We Know:

**Streamlit Cloud Frontend**:
```
https://iswitch-roofs.streamlit.app/Dashboard
```

**Backend URLs (Need Verification)**:
- **Secrets.toml says**: `https://iswitch-roof-api.onrender.com`
- **Previous errors showed**: `https://srv-d3mlmmur433s73abuar0.onrender.com`

**Screenshot shows frontend trying**: `https://iswitch-roof-api.onrender.com`
**Screenshot shows error**: `500 Internal Server Error`

### What We Need:

1. **Confirm correct backend URL from Render Dashboard**
2. **Check why backend is returning 500 errors**
3. **Update Streamlit secrets with correct URL**

---

## 🎯 Quick Fix Script

Once you know the correct URL, update local secrets file:

```bash
# Update secrets.toml with correct URL
cd /Users/grayghostdataconsultants/Development/projects/clients/client-roofing/frontend-streamlit/.streamlit

# Edit secrets.toml and replace all instances of the wrong URL
# Then manually update Streamlit Cloud secrets dashboard
```

**DO NOT commit secrets.toml to git!**

---

## 🔗 Related Files

- **Local secrets**: `frontend-streamlit/.streamlit/secrets.toml`
- **API client**: `frontend-streamlit/utils/api_client.py`
- **Config**: `frontend-streamlit/utils/config.py`

---

## ⚠️ URGENT NEXT STEP

**YOU NEED TO**:

1. **Check Render Dashboard RIGHT NOW**
   - Find the correct backend URL
   - Check if `iswitch-roof-api.onrender.com` is configured
   - Or if you should use `srv-d3mlmmur433s73abuar0.onrender.com`

2. **Check Backend Logs**
   - See why it's returning 500 errors
   - Get the Python traceback
   - Share the error messages

3. **Update Streamlit Cloud Secrets**
   - Use the correct backend URL
   - Save and restart

**This is blocking all frontend functionality!**

---

**Status**: Waiting for you to check Render Dashboard and share:
1. Correct backend URL
2. Backend error logs showing why 500 error is happening
