# ✅ Correct App URL

**Actual Production URL**: https://iswitch-roofs.streamlit.app/Dashboard

**Note**: Previous documentation incorrectly referenced `iswitchroofs` (no hyphen)

---

## 🎯 Correct URLs

### Production App
- **Main Dashboard**: https://iswitch-roofs.streamlit.app/Dashboard
- **Login Page**: https://iswitch-roofs.streamlit.app/Login
- **Leads Management**: https://iswitch-roofs.streamlit.app/Leads_Management
- **Base URL**: https://iswitch-roofs.streamlit.app/

### Streamlit Cloud Dashboard
- **Dashboard**: https://share.streamlit.io/
- **App Name**: `iswitch-roofs` (with hyphen)

### Backend API
- **Render API**: https://srv-d3mlmmur433s73abuar0.onrender.com
- **Health Check**: https://srv-d3mlmmur433s73abuar0.onrender.com/health
- **API Base**: https://srv-d3mlmmur433s73abuar0.onrender.com/api

---

## 🔧 How to Access Your Deployed App

### Step 1: Open Main Dashboard
**URL**: https://iswitch-roofs.streamlit.app/Dashboard

**What you should see**:
- Login prompt (if not authenticated)
- Dashboard with business metrics (if authenticated)
- Sidebar with navigation menu

### Step 2: Check Authentication
1. If you see "Please log in" → Go to Login page
2. Login page: https://iswitch-roofs.streamlit.app/Login
3. Use your Supabase credentials (real email required)

### Step 3: Navigate the App
Once logged in, use sidebar to navigate:
- 🏠 Dashboard
- 👥 Leads Management
- 🏢 Customers Management
- 🏗️ Projects Management
- 📅 Appointments
- 📊 Enhanced Analytics
- And 12 more pages...

---

## ✅ Verify Latest Changes

### What to Check (After 3-4 min from last deploy)

**In Sidebar**:
1. ✅ "📊 Quick Stats" section
2. ✅ Color-coded Lead Response Time card (green/red)
3. ✅ Month Revenue metric
4. ✅ Conversion Rate metric
5. ✅ "🔄 Real-time Updates" section
6. ✅ Green success box: "🟢 Live Updates Active"
7. ✅ "Last updated:" timestamp
8. ✅ **NO CSS code displayed!**

**Should NOT see**:
- ❌ `<style>` tag text
- ❌ `@keyframes pulse` code
- ❌ "Connection refused to localhost:8001"
- ❌ "Stats loading..." stuck

---

## 🚀 Quick Access Commands

### Check Backend Health
```bash
curl https://srv-d3mlmmur433s73abuar0.onrender.com/health
# Should return: {"status":"healthy"}
```

### Test Real-time Snapshot Endpoint
```bash
curl https://srv-d3mlmmur433s73abuar0.onrender.com/api/business-metrics/realtime/snapshot
# Should return JSON with lead_response, revenue, conversion data
```

### Check App Status
```bash
# Open browser and navigate to:
https://iswitch-roofs.streamlit.app/Dashboard

# Hard refresh to clear cache:
# Windows/Linux: Ctrl + Shift + R
# Mac: Cmd + Shift + R
```

---

## 📝 Important Notes

### App Name Format
- **Correct**: `iswitch-roofs` (with hyphen)
- **Incorrect**: `iswitchroofs` (no hyphen - was in old docs)

### URL Structure
- Base: `https://iswitch-roofs.streamlit.app/`
- Pages: `https://iswitch-roofs.streamlit.app/PageName`
- Default: Shows Home or redirects to Dashboard

### Authentication Required
- Most pages require Supabase authentication
- Login page: https://iswitch-roofs.streamlit.app/Login
- Logout: Use sidebar button

### Backend Connection
- Frontend connects to: `https://srv-d3mlmmur433s73abuar0.onrender.com`
- Configured via Streamlit secrets: `api_base_url`
- No more localhost errors (fixed in commit 7dd89b2)

---

## 🆘 Troubleshooting

### Issue: 404 Not Found
**Problem**: Wrong URL or page doesn't exist
**Solution**: Use correct URL with hyphen: `iswitch-roofs`

### Issue: Login Loop
**Problem**: Authentication not working
**Solution**: Check Streamlit Cloud secrets are configured (see URGENT_STREAMLIT_CLOUD_FIX.md)

### Issue: Backend Connection Error
**Problem**: Backend sleeping (free tier)
**Solution**: Wait 30-60 seconds for backend to wake up on first request

### Issue: Old Code Still Showing
**Problem**: Browser cache
**Solution**: Hard refresh (Ctrl+Shift+R) or use incognito window

---

## 📊 Deployment Status Check

### Verify Streamlit Cloud Deployment
1. Go to: https://share.streamlit.io/
2. Find app: `iswitch-roofs` (with hyphen)
3. Check status: Should be "Running" (green)
4. Click "Manage app" → "Logs" to see deployment logs

### Verify Backend Deployment
1. Go to: https://dashboard.render.com/
2. Find service: `srv-d3mlmmur433s73abuar0`
3. Check status: Should be "Live" (green)
4. Check logs for errors

### Test End-to-End
1. Open: https://iswitch-roofs.streamlit.app/Dashboard
2. Should redirect to login if not authenticated
3. Login with real email (Gmail, company email)
4. Should see dashboard with data loading
5. Check sidebar for real-time stats

---

## 🎯 Current Deployment Status

### Recent Commits
1. **0439840** - CSS display bug fix documentation
2. **3b45d36** ⭐ - Simplified real-time status (no more CSS bug)
3. **7d43e56** - Force deployment trigger
4. **f71b856** - Real-time sidebar data fix
5. **7dd89b2** - API URL configuration fix

### Expected State (After Deploy)
- ✅ No CSS code in sidebar
- ✅ Green/blue boxes with emojis
- ✅ Real-time data from backend
- ✅ No localhost connection errors
- ✅ Auto-refresh working (30s)

### Timeline
- **Last push**: Just now (commit 0439840)
- **Auto-deploy**: 2-3 minutes
- **App restart**: 1 minute
- **Check app**: In 3-4 minutes

---

## 📞 Quick Reference

| Resource | URL |
|----------|-----|
| **Production App** | https://iswitch-roofs.streamlit.app/Dashboard |
| **Login Page** | https://iswitch-roofs.streamlit.app/Login |
| **Streamlit Cloud** | https://share.streamlit.io/ |
| **Backend API** | https://srv-d3mlmmur433s73abuar0.onrender.com |
| **Backend Health** | https://srv-d3mlmmur433s73abuar0.onrender.com/health |
| **Render Dashboard** | https://dashboard.render.com/ |
| **GitHub Repo** | https://github.com/GrayGhostDev/client-roofing |

---

## ✅ Action Items

### Immediate (Now)
1. Open: https://iswitch-roofs.streamlit.app/Dashboard
2. Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R)
3. Check sidebar for clean UI (no CSS code)

### If Issues (After 5 minutes)
1. Check Streamlit Cloud logs
2. Verify secrets are configured
3. Check backend is running (health endpoint)
4. Try incognito/private window

### Documentation Update Needed
- [ ] Previous docs referenced wrong URL (`iswitchroofs`)
- [ ] Should be: `iswitch-roofs` (with hyphen)
- [ ] Update bookmarks and saved links

---

**🚀 Correct URL**: https://iswitch-roofs.streamlit.app/Dashboard

**⏰ Check Status**: Go there now and verify the fixes are live!

**💡 Tip**: Bookmark the correct URL for easy access.
