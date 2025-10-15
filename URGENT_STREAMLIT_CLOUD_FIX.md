# 🚨 URGENT: Streamlit Cloud Error - Missing Secrets

## ❌ Current Error

**Error Message**: `ValueError: This app has encountered an error`

**Root Cause**: Streamlit Cloud cannot find Supabase credentials

**Location**: `frontend-streamlit/utils/supabase_auth.py` line 49

**Traceback**:
```python
File "/mount/src/client-roofing/frontend-streamlit/utils/supabase_auth.py", line 49, in __init__
    raise ValueError(error_msg)
```

---

## 🔥 IMMEDIATE FIX REQUIRED (5 Minutes)

### The Problem

Your Streamlit Cloud app is deployed but **missing the secrets configuration**. The code is looking for `SUPABASE_URL` and `SUPABASE_KEY` but can't find them.

### The Solution

You MUST manually add secrets to Streamlit Cloud dashboard. Follow these exact steps:

---

## 📋 STEP-BY-STEP FIX

### Step 1: Open Streamlit Cloud Dashboard
1. Go to: **https://share.streamlit.io/**
2. Log in with your Streamlit account
3. Find your app: **iswitchroofs** (or client-roofing)

### Step 2: Access Secrets Editor
1. Click on your app name to open it
2. Click the **⚙️ Settings** button (top right corner)
3. From the dropdown menu, select **Secrets**
4. You should see a text editor (currently empty or with old values)

### Step 3: Copy Secrets Below
**Copy the ENTIRE block below** (from `# =============` to the last line):

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
# Backend API Configuration
# -----------------------------------------------------------------------------
api_base_url = "https://srv-d3mlmmur433s73abuar0.onrender.com"
ml_api_base_url = "https://srv-d3mlmmur433s73abuar0.onrender.com"
BACKEND_API_URL = "https://srv-d3mlmmur433s73abuar0.onrender.com"

# -----------------------------------------------------------------------------
# Pusher Configuration
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

### Step 4: Paste and Save
1. **Delete** any existing content in the secrets editor
2. **Paste** the entire block above
3. Click the **Save** button
4. Streamlit will automatically restart your app (takes 1-2 minutes)

### Step 5: Verify Fix
1. Wait for the app to restart (watch for "Running" status)
2. Refresh your app URL: https://iswitchroofs.streamlit.app
3. You should see the login page (not an error)
4. If still error, check logs: Click "Manage app" → "Logs"

---

## 🔍 What the Error Means

The error occurs in this code:

```python
# frontend-streamlit/utils/supabase_auth.py, line 49
def __init__(self):
    # Try to get credentials
    self.supabase_url = os.getenv("SUPABASE_URL")
    self.supabase_key = os.getenv("SUPABASE_KEY")

    # If not in env, try Streamlit secrets
    if not self.supabase_url or not self.supabase_key:
        try:
            self.supabase_url = st.secrets.get("SUPABASE_URL")
            self.supabase_key = st.secrets.get("SUPABASE_KEY")
        except Exception:
            pass

    # If still missing, raise error ← YOU ARE HERE
    if not self.supabase_url or not self.supabase_key:
        raise ValueError(error_msg)  # ← Line 49
```

The code checked:
1. ❌ Environment variables (`os.getenv`) - Not available in Streamlit Cloud
2. ❌ Streamlit secrets (`st.secrets`) - **Empty because you haven't added them yet**
3. 🔴 Result: Raised ValueError because both checks failed

---

## ✅ After You Add Secrets

Once you save the secrets in Streamlit Cloud:
1. App will restart automatically
2. Code will find `st.secrets["SUPABASE_URL"]` ✅
3. Code will find `st.secrets["SUPABASE_KEY"]` ✅
4. Authentication will initialize successfully
5. Login page will load correctly

---

## 🎯 Quick Checklist

- [ ] Opened https://share.streamlit.io/
- [ ] Found app: iswitchroofs
- [ ] Clicked Settings → Secrets
- [ ] Copied secrets from this file
- [ ] Pasted into Streamlit Cloud editor
- [ ] Clicked Save
- [ ] Waited for app restart (1-2 min)
- [ ] Refreshed app URL
- [ ] Verified login page loads

---

## 🆘 If Still Getting Errors

### Error: "Failed to parse secrets"
**Problem**: TOML syntax error in secrets
**Solution**:
- Make sure you copied the ENTIRE block
- Check for missing quotes or brackets
- Try copying again from this file

### Error: Still "Missing Supabase credentials"
**Problem**: Secrets not saved correctly
**Solution**:
1. Go back to Settings → Secrets
2. Verify the content is there
3. Look for `SUPABASE_URL = "https://tdwpzktihdeuzapxoovk..."`
4. If missing, paste again and save

### Error: Different error message
**Problem**: New issue after secrets added
**Solution**:
1. Click "Manage app" → "Logs" in Streamlit Cloud
2. Copy the new error message
3. Check if backend URL is wrong
4. Verify backend is running: curl https://srv-d3mlmmur433s73abuar0.onrender.com/health

---

## 📝 Important Notes

### Why This Happened
- Local development uses `.env` files
- Streamlit Cloud doesn't have access to local `.env`
- Cloud apps MUST use Streamlit secrets dashboard
- We created the secrets file but didn't upload it yet

### Security
- ✅ Secrets are encrypted in Streamlit Cloud
- ✅ Only you can see them in the dashboard
- ✅ Not exposed in logs or public URLs
- ✅ `.streamlit/secrets.toml` is in `.gitignore`

### What Are These Secrets?
- **SUPABASE_URL**: Your authentication server address
- **SUPABASE_KEY**: Public API key (safe to use in frontend)
- **Backend URLs**: Your Render.com API endpoints
- **Pusher**: Realtime notification service

---

## 🚀 After Fix Works

Once login page loads:
1. Test signup with a **real email** (Gmail, company email)
2. Check email for verification link
3. Click verification link
4. Return to app and login
5. Should see dashboard

❌ **Don't use**: @example.com, @test.com (Supabase blocks these)

---

## 📞 Quick Reference

**Streamlit Cloud Dashboard**: https://share.streamlit.io/
**App URL**: https://iswitchroofs.streamlit.app
**Backend Health**: https://srv-d3mlmmur433s73abuar0.onrender.com/health

**Local Secrets File**: `frontend-streamlit/.streamlit/secrets.toml`
**Example File**: `frontend-streamlit/.streamlit/secrets.toml.example`

---

**⏰ TIME TO FIX: 5 minutes**

**🎯 PRIORITY: URGENT** (app is broken until fixed)

**💡 TIP**: Keep this file open while configuring - you can copy directly from the secrets block above.
