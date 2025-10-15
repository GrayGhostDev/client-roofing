# 🔄 Force Streamlit Cloud Update

**Issue**: Changes pushed to GitHub but not showing in Streamlit Cloud deployment

**Status**: ⚠️ Manual action required

**Date**: 2025-10-15

---

## 🔴 Why Changes Aren't Showing

Streamlit Cloud typically auto-deploys when you push to GitHub, but sometimes it:
1. **Doesn't detect the push** - Webhook missed or delayed
2. **Is using cached version** - Old code still in memory
3. **Needs manual restart** - Auto-deploy didn't trigger
4. **Has errors preventing restart** - Check logs for issues

---

## ✅ Solution: Force Restart Streamlit Cloud App

### Method 1: Reboot from Dashboard (Fastest - 30 seconds)

**Step 1: Open Streamlit Cloud Dashboard**
1. Go to: **https://share.streamlit.io/**
2. Log in with your account
3. Find your app: **"iswitchroofs"** or **"client-roofing"**

**Step 2: Reboot the App**
1. Click on your app name
2. Click the **⋮** (three dots) menu button (top right)
3. Select **"Reboot app"**
4. Wait 30-60 seconds for restart

**Step 3: Clear Browser Cache**
1. Hard refresh: **Ctrl+Shift+R** (Windows) or **Cmd+Shift+R** (Mac)
2. Or open in **incognito/private window**

---

### Method 2: Trigger Deployment via Settings (1-2 minutes)

**Step 1: Open App Settings**
1. Go to https://share.streamlit.io/
2. Click on your app
3. Click **⚙️ Settings** (top right)
4. Select **"Advanced settings"**

**Step 2: Make a Trivial Change**
1. Scroll to any setting
2. Toggle something ON then OFF (like "Wide mode")
3. Click **"Save"**
4. This forces a redeploy

---

### Method 3: Force GitHub to Re-trigger (2-3 minutes)

**Make an empty commit to trigger webhook:**

```bash
# From your project directory
git commit --allow-empty -m "chore: Force Streamlit Cloud deployment"
git push origin main
```

**Then wait**:
- Streamlit Cloud detects push: ~30 seconds
- Builds and deploys: ~1-2 minutes
- App available: ~2-3 minutes total

---

### Method 4: Check and Fix Issues (If Nothing Works)

**Step 1: Check Streamlit Cloud Logs**
1. Go to https://share.streamlit.io/
2. Click your app
3. Click **"Manage app"** → **"Logs"**
4. Look for errors

**Common Issues in Logs**:

**Issue**: `ModuleNotFoundError: No module named 'xyz'`
**Fix**: Missing dependency in `requirements.txt`

**Issue**: `KeyError: 'api_base_url'` or `ValueError: Missing Supabase credentials`
**Fix**: Secrets not added to dashboard (see URGENT_STREAMLIT_CLOUD_FIX.md)

**Issue**: `SyntaxError` or `IndentationError`
**Fix**: Code syntax error - check recent changes

**Step 2: Verify Secrets Are Added**
1. Settings → Secrets
2. Check if TOML content is present
3. Look for `api_base_url`, `SUPABASE_URL`, `SUPABASE_KEY`
4. If missing, paste content from `URGENT_STREAMLIT_CLOUD_FIX.md`

**Step 3: Check App Settings**
1. Settings → General
2. **Main file path**: Should be `Home.py`
3. **Python version**: Should be 3.9+ (preferably 3.11)
4. **Branch**: Should be `main`

---

## 🔍 How to Verify Changes Are Live

### Check 1: Git Commit Hash
1. Open your app in browser
2. Scroll to bottom of sidebar
3. Look for version info: "iSwitch Roofs CRM v3.0.0"
4. Check browser console (F12):
   - Some apps log git commit hash
   - Check HTML source for comments

### Check 2: New Features Visible
Look for these specific changes from recent commits:

**From commit `f71b856`** (Sidebar real-time data):
1. ✅ Sidebar has **"📊 Quick Stats"** section
2. ✅ Shows **color-coded Lead Response Time** card
3. ✅ Shows **Month Revenue** with progress %
4. ✅ Shows **Conversion Rate** with delta
5. ✅ **Real-time Updates** section has pulsing green dot
6. ✅ Shows **"Last updated: XX:XX:XX PM"** timestamp

**From commit `7dd89b2`** (API URL fix):
1. ✅ No more "Connection refused to localhost:8001" errors
2. ✅ App connects to Render backend
3. ✅ Data loads from production API

### Check 3: Browser Console
Press **F12** → Console tab

**Good signs** (changes are live):
```
✅ No localhost:8001 errors
✅ API calls to https://srv-d3mlmmur433s73abuar0.onrender.com
✅ Successfully fetching /api/business-metrics/realtime/snapshot
✅ No 404 errors
```

**Bad signs** (old code still running):
```
❌ Connection refused to localhost:8001
❌ 404 error on /stats/summary
❌ No pulsing animation visible
❌ Static "Stats loading..." message
```

### Check 4: Page Source
1. Right-click on page → **"View page source"**
2. Search for `@keyframes pulse`
3. If found → New code is live ✅
4. If not found → Old code still running ❌

---

## 🎯 Complete Update Checklist

Follow this step-by-step:

### Phase 1: Force Restart (5 minutes)
- [ ] Open https://share.streamlit.io/
- [ ] Find your app (iswitchroofs)
- [ ] Click three dots → Reboot app
- [ ] Wait 60 seconds for restart
- [ ] Hard refresh browser (Ctrl+Shift+R)

### Phase 2: Verify Secrets (If Still Not Working)
- [ ] Click Settings → Secrets
- [ ] Verify TOML content is present
- [ ] Look for `api_base_url = "https://srv-d3mlmmur433s73abuar0..."`
- [ ] Look for `SUPABASE_URL = "https://tdwpzktihdeuzapxoovk..."`
- [ ] If missing, paste from `URGENT_STREAMLIT_CLOUD_FIX.md`
- [ ] Click Save
- [ ] Wait for app restart (1-2 min)

### Phase 3: Check Logs (If Still Broken)
- [ ] Click Manage app → Logs
- [ ] Look for error messages
- [ ] Check for import errors
- [ ] Check for syntax errors
- [ ] Note any error messages

### Phase 4: Force Deploy (Last Resort)
- [ ] Run: `git commit --allow-empty -m "chore: Force deploy"`
- [ ] Run: `git push origin main`
- [ ] Wait 2-3 minutes
- [ ] Hard refresh browser

### Phase 5: Verify Changes
- [ ] See color-coded Lead Response Time in sidebar
- [ ] See pulsing green dot animation
- [ ] See "Last updated" timestamp
- [ ] No localhost connection errors
- [ ] Data loads from backend

---

## 📊 Recent Commits to Verify

### Commit `c12f0e2` (Just Now)
- Documentation only, won't change app behavior

### Commit `f71b856` ⭐ (IMPORTANT - Sidebar Fix)
**Should see**:
- Color-coded Lead Response Time card
- Month Revenue metric
- Conversion Rate metric
- Pulsing green/red dot
- Auto-refresh functionality
- Last updated timestamp

### Commit `7dd89b2` ⭐ (IMPORTANT - API URL Fix)
**Should see**:
- No localhost errors
- Data loading from Render backend
- Backend URL: `https://srv-d3mlmmur433s73abuar0.onrender.com`

### Commit `3e717e4` (Earlier)
- Documentation only, won't change app behavior

---

## 🆘 Common Issues & Solutions

### Issue: "App is not responding"
**Symptoms**: White screen, loading forever
**Solutions**:
1. Backend might be sleeping (free tier)
2. Wait 60 seconds for backend to wake up
3. Check: https://srv-d3mlmmur433s73abuar0.onrender.com/health
4. Should return: `{"status":"healthy"}`

### Issue: "ValueError: Missing Supabase credentials"
**Symptoms**: Error page with Supabase message
**Solution**: Secrets not added yet
1. Follow: `URGENT_STREAMLIT_CLOUD_FIX.md`
2. Add secrets to dashboard
3. Save and wait for restart

### Issue: Old code still showing after reboot
**Symptoms**: No pulsing dots, wrong metrics
**Solutions**:
1. **Clear browser cache completely**:
   - Chrome: Settings → Privacy → Clear browsing data
   - Select "Cached images and files"
   - Clear data
2. **Try different browser** (Firefox, Safari, Edge)
3. **Try incognito/private window**
4. **Force full redeploy**: Make empty commit and push

### Issue: Logs show import errors
**Symptoms**: `ModuleNotFoundError: No module named 'X'`
**Solution**: Check `requirements.txt`
1. Verify all dependencies are listed
2. Check for version conflicts
3. May need to update requirements.txt

### Issue: "Connection timed out"
**Symptoms**: Slow loading, timeout errors
**Solutions**:
1. Backend is sleeping (free tier)
2. First request wakes it up (30-60s)
3. Subsequent requests are fast
4. Consider upgrading to paid tier for always-on

---

## 🔧 Advanced: Debugging with Browser DevTools

### Step 1: Open DevTools
- Press **F12** or Right-click → Inspect
- Go to **Console** tab

### Step 2: Check Network Requests
1. Click **Network** tab
2. Refresh page (Ctrl+R)
3. Look for API calls
4. Filter by "business-metrics"

**Good signs**:
```
✅ GET https://srv-d3mlmmur433s73abuar0.onrender.com/api/business-metrics/realtime/snapshot
   Status: 200 OK
   Response: {"lead_response": {...}, "revenue": {...}}
```

**Bad signs**:
```
❌ GET http://localhost:8001/api/stats/summary
   Status: Failed (net::ERR_CONNECTION_REFUSED)

❌ GET https://srv-d3mlmmur433s73abuar0.onrender.com/api/stats/summary
   Status: 404 Not Found
```

### Step 3: Check Console Errors
Look for JavaScript errors:
```javascript
❌ TypeError: Cannot read property 'get' of undefined
❌ ReferenceError: api_base_url is not defined
❌ SyntaxError: Unexpected token
```

### Step 4: Verify CSS Loaded
1. Go to **Elements** tab
2. Search for: `@keyframes pulse`
3. If found in `<style>` tag → New code loaded ✅
4. If not found → Old code cached ❌

---

## 📝 Quick Commands Reference

```bash
# Check current commit
git log --oneline -1

# Force empty commit to trigger deploy
git commit --allow-empty -m "chore: Force Streamlit Cloud deployment"
git push origin main

# Check if changes are pushed
git log --oneline -5

# Verify branch
git branch -v
```

---

## ⏰ Expected Timeline

### Scenario 1: Simple Reboot
- Click "Reboot app": **Instant**
- App restarts: **30-60 seconds**
- Browser refresh: **Instant**
- **Total**: 1-2 minutes ✅

### Scenario 2: Add Secrets + Restart
- Add secrets: **1 minute**
- Click Save: **Instant**
- App restarts: **1-2 minutes**
- Browser refresh: **Instant**
- **Total**: 3-4 minutes ✅

### Scenario 3: Force Deploy via Git
- Make empty commit: **10 seconds**
- Git push: **5-10 seconds**
- Streamlit detects: **30-60 seconds**
- Build and deploy: **1-2 minutes**
- Browser refresh: **Instant**
- **Total**: 3-4 minutes ✅

### Scenario 4: Backend Sleeping
- First request: **30-60 seconds** (wake up)
- Backend responds: **Instant**
- Data loads: **1-2 seconds**
- **Total**: 30-60 seconds ⏰

---

## 🎯 Final Checklist

**Before Contacting Support**:
- [ ] Tried "Reboot app" button
- [ ] Hard refreshed browser (Ctrl+Shift+R)
- [ ] Checked Streamlit Cloud logs for errors
- [ ] Verified secrets are added to dashboard
- [ ] Checked backend is running (health endpoint)
- [ ] Tried incognito/private window
- [ ] Forced empty commit and pushed
- [ ] Waited at least 5 minutes after push

**What to Have Ready for Support**:
- App URL: https://iswitchroofs.streamlit.app
- GitHub repo: https://github.com/GrayGhostDev/client-roofing
- Latest commit hash: `c12f0e2`
- Error messages from logs
- Screenshots of issues

---

## 📞 Support Resources

**Streamlit Cloud**:
- Dashboard: https://share.streamlit.io/
- Docs: https://docs.streamlit.io/deploy
- Community: https://discuss.streamlit.io/

**Your Documentation**:
- Urgent Fix Guide: `URGENT_STREAMLIT_CLOUD_FIX.md`
- API Fix Details: `LOCALHOST_CONNECTION_ERROR_FIXED.md`
- Sidebar Fix Details: `SIDEBAR_REALTIME_DATA_FIXED.md`
- This Guide: `FORCE_STREAMLIT_CLOUD_UPDATE.md`

---

**🚀 TL;DR**: Go to https://share.streamlit.io/ → Find your app → Click three dots → Reboot app → Wait 60 seconds → Hard refresh browser (Ctrl+Shift+R)

**⏰ Time to Fix**: 2 minutes

**💡 Key**: If reboot doesn't work, check secrets are added and backend is running!
