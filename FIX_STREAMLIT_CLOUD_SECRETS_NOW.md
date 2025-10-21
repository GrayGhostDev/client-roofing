# 🚨 FIX STREAMLIT CLOUD SECRETS NOW

**Date**: 2025-10-21
**Issue**: Backend URL is wrong in Streamlit Cloud
**Impact**: Frontend cannot connect to backend (500 errors)
**Time to Fix**: 2 minutes

---

## ✅ Problem Confirmed

**Service ID**: `srv-d3mlmmur433s73abuar0`

**Wrong URL** (currently in Streamlit Cloud):
```
https://iswitch-roof-api.onrender.com
```

**Correct URL** (must update to):
```
https://srv-d3mlmmur433s73abuar0.onrender.com
```

---

## 📋 Step-by-Step Fix Instructions

### Step 1: Open Streamlit Cloud Dashboard

1. Go to: https://share.streamlit.io/
2. Sign in if needed
3. Find your app: **iswitch-roofs** (or **iSwitch Roofs**)
4. Click on the app name to open it

### Step 2: Open Secrets Editor

1. Click the **⋮** (three dots) menu on the right
2. Click **Settings**
3. Click **Secrets** tab on the left

You'll see a text editor with your current secrets.

### Step 3: Find and Replace URLs

**Find these 3 lines** (around line 25-32):

```toml
api_base_url = "https://iswitch-roof-api.onrender.com"
ml_api_base_url = "https://iswitch-roof-api.onrender.com"
BACKEND_API_URL = "https://iswitch-roof-api.onrender.com"
```

**Replace them with**:

```toml
api_base_url = "https://srv-d3mlmmur433s73abuar0.onrender.com"
ml_api_base_url = "https://srv-d3mlmmur433s73abuar0.onrender.com"
BACKEND_API_URL = "https://srv-d3mlmmur433s73abuar0.onrender.com"
```

### Step 4: Save Changes

1. Click **Save** button (bottom right)
2. Streamlit will show: "Your secrets have been saved"
3. App will automatically restart (takes ~10 seconds)

### Step 5: Verify the Fix

1. Wait 30 seconds for app to fully restart
2. Go to your app: https://iswitch-roofs.streamlit.app/Dashboard
3. **Hard refresh** the page:
   - **Windows/Linux**: `Ctrl + Shift + R`
   - **Mac**: `Cmd + Shift + R`
4. Check if error is gone

---

## 🎯 Expected Results

### Before Fix:
```
❌ API Error: 500 Server Error: Internal Server Error for url:
https://iswitch-roof-api.onrender.com/api/leads?limit=500
```

### After Fix:

**If backend is working**:
```
✅ Real data loads
✅ Leads display correctly
✅ Metrics show actual values
```

**If backend has 404 errors** (routes not registered):
```
⚠️ Backend API `/api/leads` endpoint not found (404 Error)
🔍 Troubleshooting guide displays
📊 Demo data shows as fallback
```

**If backend is sleeping**:
```
⏳ Backend starting...
Wait 60 seconds and refresh
```

---

## 🔍 Troubleshooting

### If Error Still Shows After Update:

**1. Clear browser cache completely**:
- Close all Streamlit tabs
- Clear browser cache
- Reopen app in new tab

**2. Force app restart**:
- Streamlit Cloud dashboard
- Click **⋮** menu → **Reboot app**
- Wait 30 seconds

**3. Check secrets were saved**:
- Go back to Settings → Secrets
- Verify URLs show `srv-d3mlmmur433s73abuar0`
- If not, they didn't save - try again

### If Backend Still Returns Errors:

**Backend may be sleeping (Render free tier)**:
1. First request after sleep takes 30-60 seconds
2. You'll see "Backend starting..." message
3. Wait 60 seconds
4. Hard refresh page
5. Should connect on second try

**Backend may have 404 errors**:
- Routes not registered (previous issue)
- Check Render logs for "Failed to register" errors
- See [API_404_ERRORS_ANALYSIS.md](API_404_ERRORS_ANALYSIS.md)

**Backend may have 500 errors**:
- Internal server error
- Check Render logs for Python tracebacks
- May need to fix backend code or environment variables

---

## 📊 Complete Secrets Configuration

After your fix, the backend section should look like this:

```toml
# -----------------------------------------------------------------------------
# Backend API Configuration
# Switch between local development and production
# -----------------------------------------------------------------------------
# Production Backend (Render.com) - ACTIVE
# Service ID: srv-d3mlmmur433s73abuar0
api_base_url = "https://srv-d3mlmmur433s73abuar0.onrender.com"
ml_api_base_url = "https://srv-d3mlmmur433s73abuar0.onrender.com"

# Backend API URL (uppercase alternative)
BACKEND_API_URL = "https://srv-d3mlmmur433s73abuar0.onrender.com"
```

**Keep all other secrets unchanged**:
- SUPABASE_URL
- SUPABASE_KEY
- pusher_* settings
- Everything else stays the same

---

## ⏱️ Timeline

**Immediate** (2 minutes):
1. Update Streamlit Cloud secrets ← **DO THIS NOW**
2. Save and wait for restart
3. Test the connection

**If 404 errors appear** (5 minutes):
1. Backend routes not registered
2. Check Render logs
3. May need backend restart

**If 500 errors appear** (10 minutes):
1. Backend internal errors
2. Check Render logs for traceback
3. May need to fix environment variables

---

## 🎯 Quick Reference

**Streamlit Cloud Dashboard**: https://share.streamlit.io/

**Your App**: https://iswitch-roofs.streamlit.app/Dashboard

**Wrong URL**: `https://iswitch-roof-api.onrender.com` ❌

**Correct URL**: `https://srv-d3mlmmur433s73abuar0.onrender.com` ✅

**Render Service**: `srv-d3mlmmur433s73abuar0`

---

## ✅ Verification Checklist

After updating secrets:

- [ ] Secrets saved in Streamlit Cloud
- [ ] App restarted (automatic)
- [ ] Hard refreshed browser (Cmd/Ctrl + Shift + R)
- [ ] Error message changed or disappeared
- [ ] Can see loading indicator or data

**Next step depends on what you see**:
- ✅ **Data loads**: Backend connected! Issue resolved!
- ⚠️ **404 errors**: Backend routes issue (see previous docs)
- ❌ **500 errors**: Backend internal error (check logs)
- ⏳ **Timeout**: Backend sleeping (wait 60 seconds)

---

**🚨 ACTION REQUIRED**: Update Streamlit Cloud secrets RIGHT NOW with the correct backend URL!

**Expected Time**: 2 minutes

**Expected Result**: Connection errors should change from "500 at iswitch-roof-api" to either working data or different error type.
