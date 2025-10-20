# 🚀 iSwitch Roofs CRM - Deployment Checklist

**Date Created:** 2025-10-20
**Purpose:** Guide for deploying/restarting Render backend and Streamlit Cloud frontend

---

## 📋 Pre-Deployment Checklist

### ✅ Local Configuration Verified
- [x] Frontend `.streamlit/secrets.toml` configured with production Render URL
- [x] Frontend `.env` configured with production Render URL
- [x] Backend `.env` updated with Pusher credentials
- [x] Backend `.env` updated with CORS origins including Streamlit Cloud
- [x] All sensitive credentials secured (not committed to git)

### ✅ Files Updated
- [x] `Home.py` - Login page navigation fixed (no emoji in filename)
- [x] `pages/0_Login.py` - Renamed from `0_🔐_Login.py`
- [x] `.streamlit/secrets.toml` - Production backend URL
- [x] `backend/.env` - Pusher credentials and CORS origins

---

## 🔧 Step 1: Configure Render.com Backend

### 1.1 Login to Render Dashboard
1. Go to: https://dashboard.render.com/
2. Login with your credentials
3. Find service: `iswitch-roofs-api` or `iswitch-roof-api`

### 1.2 Add/Update Environment Variables

**Navigate to:** Your service → **Environment** tab

**Add these environment variables:**

```bash
# ============================================================================
# Supabase Configuration
# ============================================================================
SUPABASE_URL=https://tdwpzktihdeuzapxoovk.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRkd3B6a3RpaGRldXphcHhvb3ZrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk2MDQyODgsImV4cCI6MjA3NTE4MDI4OH0.RHDETB-JCeRq4Asmh2bt2yG2wKTcryHgSzw03-kK9NY

# ============================================================================
# Pusher Real-Time Configuration
# ============================================================================
PUSHER_APP_ID=1890740
PUSHER_KEY=fe32b6bb02f0c1a41bb4
PUSHER_SECRET=e2b7e61a1b6c1aca04b0
PUSHER_CLUSTER=us2
PUSHER_SSL=true

# ============================================================================
# CORS Configuration (CRITICAL for Streamlit Cloud)
# ============================================================================
CORS_ORIGINS=https://iswitchroofs.streamlit.app,http://localhost:8501
CORS_SUPPORTS_CREDENTIALS=true

# ============================================================================
# Flask Configuration
# ============================================================================
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=ce94da40b91b21a71a6973b1f859cec135d977d42b80ea71be8a103d16932296

# ============================================================================
# JWT Authentication
# ============================================================================
JWT_SECRET_KEY=5b69908dac1913a02e002020697129410cd73cea7f93b16b233f9474a6df3c7a
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRES=3600

# ============================================================================
# Feature Flags
# ============================================================================
SKIP_AUTH=true
ENABLE_LEAD_SCORING=true
ENABLE_AUTOMATED_FOLLOW_UP=true

# ============================================================================
# Database Configuration (IMPORTANT - Check with your setup)
# ============================================================================
# Option 1: If using Supabase PostgreSQL
DATABASE_URL=postgresql://postgres:[password]@db.tdwpzktihdeuzapxoovk.supabase.co:5432/postgres

# Option 2: If using separate PostgreSQL (update with your credentials)
# DATABASE_URL=postgresql://username:password@host:5432/database_name

# ============================================================================
# Optional: Redis Configuration (if using)
# ============================================================================
# REDIS_URL=redis://[host]:[port]/0

# ============================================================================
# Business Configuration
# ============================================================================
COMPANY_NAME=iSwitch Roofs
HOT_LEAD_THRESHOLD=80
WARM_LEAD_THRESHOLD=60
COOL_LEAD_THRESHOLD=40
```

### 1.3 Save and Deploy
1. Click **"Save Changes"**
2. Render will automatically trigger a redeploy
3. **OR** click **"Manual Deploy"** → "Deploy latest commit"

### 1.4 Monitor Deployment
1. Go to **"Logs"** tab
2. Watch for:
   - ✅ Build successful
   - ✅ Server starting
   - ✅ `Listening on port [PORT]`
   - ❌ Any error messages about missing environment variables
   - ❌ Database connection errors

**Expected Success Messages:**
```
==> Build successful
==> Starting service
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:10000
```

---

## 🎨 Step 2: Configure Streamlit Cloud Frontend

### 2.1 Login to Streamlit Cloud
1. Go to: https://share.streamlit.io/
2. Login with your credentials
3. Find your app: `iswitchroofs`

### 2.2 Update Secrets Configuration

**Navigate to:** Your app → **Settings** (⚙️) → **Secrets**

**Paste this entire configuration:**

```toml
# =============================================================================
# Streamlit Cloud Secrets Configuration
# iSwitch Roofs CRM - Production
# =============================================================================

# -----------------------------------------------------------------------------
# Supabase Authentication (REQUIRED)
# -----------------------------------------------------------------------------
SUPABASE_URL = "https://tdwpzktihdeuzapxoovk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRkd3B6a3RpaGRldXphcHhvb3ZrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk2MDQyODgsImV4cCI6MjA3NTE4MDI4OH0.RHDETB-JCeRq4Asmh2bt2yG2wKTcryHgSzw03-kK9NY"

supabase_url = "https://tdwpzktihdeuzapxoovk.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRkd3B6a3RpaGRldXphcHhvb3ZrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk2MDQyODgsImV4cCI6MjA3NTE4MDI4OH0.RHDETB-JCeRq4Asmh2bt2yG2wKTcryHgSzw03-kK9NY"

# -----------------------------------------------------------------------------
# Backend API Configuration (PRODUCTION RENDER URL)
# -----------------------------------------------------------------------------
api_base_url = "https://iswitch-roof-api.onrender.com"
ml_api_base_url = "https://iswitch-roof-api.onrender.com"
BACKEND_API_URL = "https://iswitch-roof-api.onrender.com"

# -----------------------------------------------------------------------------
# Pusher Configuration (Realtime Features)
# -----------------------------------------------------------------------------
pusher_app_id = "1890740"
pusher_key = "fe32b6bb02f0c1a41bb4"
pusher_secret = "e2b7e61a1b6c1aca04b0"
pusher_cluster = "us2"

PUSHER_APP_ID = "1890740"
PUSHER_KEY = "fe32b6bb02f0c1a41bb4"
PUSHER_SECRET = "e2b7e61a1b6c1aca04b0"
PUSHER_CLUSTER = "us2"

# -----------------------------------------------------------------------------
# Application Configuration
# -----------------------------------------------------------------------------
BYPASS_AUTH = "false"
ENVIRONMENT = "production"
```

### 2.3 Save and Reboot
1. Click **"Save"**
2. Close the secrets dialog
3. Click **"Reboot app"** button
4. Wait 1-2 minutes for app to restart

---

## ✅ Step 3: Verification Tests

### 3.1 Test Backend API (Render)

**Test 1: Health Check**
```bash
curl https://iswitch-roof-api.onrender.com/health
```
**Expected:** `{"status": "healthy"}` or similar

**Test 2: API Endpoints**
```bash
curl https://iswitch-roof-api.onrender.com/api/leads/?limit=5
```
**Expected:** JSON response with leads data (not 500 error)

**Test 3: CORS Headers**
```bash
curl -I -X OPTIONS https://iswitch-roof-api.onrender.com/api/leads/ \
  -H "Origin: https://iswitchroofs.streamlit.app"
```
**Expected:** Headers including `Access-Control-Allow-Origin`

### 3.2 Test Frontend (Streamlit Cloud)

**Test 1: App Loads**
1. Open: https://iswitchroofs.streamlit.app (or your Streamlit URL)
2. **Expected:** App loads without errors
3. **Expected:** No 500 Server Error messages

**Test 2: Login Page**
1. Navigate to Login page from sidebar
2. **Expected:** Page loads correctly (no emoji filename error)
3. **Expected:** Login form displays

**Test 3: Data Fetching**
1. Navigate to "Leads Management" or "Dashboard"
2. **Expected:** Data loads from backend
3. **Expected:** No "API Error: 500" messages
4. **Expected:** Real data displays (not demo data)

**Test 4: Live Data Generator**
1. Navigate to "Live Data Generator" page
2. Try generating 25 test leads
3. **Expected:** Leads are created successfully
4. **Expected:** Success message displayed

---

## 🐛 Troubleshooting Guide

### Backend Issues

**Problem:** 500 Internal Server Error
- **Check:** Render logs for error messages
- **Check:** All environment variables are set in Render dashboard
- **Check:** DATABASE_URL is correct and accessible
- **Solution:** Review logs, add missing env vars, redeploy

**Problem:** CORS errors in Streamlit
- **Check:** `CORS_ORIGINS` includes `https://iswitchroofs.streamlit.app`
- **Check:** `CORS_SUPPORTS_CREDENTIALS=true` is set
- **Solution:** Add Streamlit URL to CORS_ORIGINS, redeploy

**Problem:** Database connection errors
- **Check:** DATABASE_URL format is correct
- **Check:** Database exists and tables are created
- **Solution:** Run database migrations, verify connection string

### Frontend Issues

**Problem:** "Could not find page" error
- **Check:** All page files exist in `pages/` directory
- **Check:** No emoji characters in filenames
- **Solution:** Verify file `pages/0_Login.py` exists (not `0_🔐_Login.py`)

**Problem:** "API Error: 500"
- **Check:** Backend is running and healthy
- **Check:** `api_base_url` in secrets points to correct Render URL
- **Solution:** Verify backend URL, check backend logs

**Problem:** No data loading
- **Check:** Backend API is responding
- **Check:** Database has data
- **Solution:** Generate test data using Live Data Generator

---

## 📊 Success Criteria

### ✅ Backend (Render)
- [ ] Deployment completed successfully
- [ ] Health check endpoint returns 200 OK
- [ ] API endpoints return data (not 500 errors)
- [ ] Logs show no critical errors
- [ ] CORS headers properly configured

### ✅ Frontend (Streamlit Cloud)
- [ ] App loads without errors
- [ ] Login page accessible
- [ ] Dashboard displays data
- [ ] No 500 Server Error messages
- [ ] Real data loads from backend

### ✅ Integration
- [ ] Frontend can fetch data from backend
- [ ] Lead generation works
- [ ] Navigation works across all pages
- [ ] Real-time updates work (if using Pusher)

---

## 🔄 Rollback Plan

If deployment fails:

### Render Backend
1. Go to **"Deploys"** tab
2. Find last successful deployment
3. Click **"Redeploy"** on that version

### Streamlit Cloud
1. Revert secrets to previous working configuration
2. Click **"Reboot app"**

---

## 📞 Support Resources

- **Render Docs:** https://render.com/docs
- **Streamlit Cloud Docs:** https://docs.streamlit.io/streamlit-community-cloud
- **Supabase Docs:** https://supabase.com/docs
- **Backend Logs:** https://dashboard.render.com/ → Your service → Logs
- **Streamlit Logs:** https://share.streamlit.io/ → Your app → Manage app → Logs

---

## 📝 Notes

- Backend `.env` file is not committed to git (correct security practice)
- Secrets must be configured directly in Render and Streamlit dashboards
- Changes to environment variables require redeploy/reboot
- Monitor logs during and after deployment for any issues

**Last Updated:** 2025-10-20
**Version:** 1.0
