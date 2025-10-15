# 🚀 Quick Start - Deploy in 10 Minutes

## Current Status

- ✅ Frontend LIVE: https://iswitchroofs.streamlit.app
- ⚠️ Backend needs env vars: https://srv-d3mlmmur433s73abuar0.onrender.com

## Choose Your Path

### Path A: Automated with MCP (Recommended) ⚡

**Time:** 10 minutes | **Difficulty:** Easy | **Repeatability:** High

1. **Create API Key** (2 min)
   ```
   1. Go to: https://dashboard.render.com/settings#api-keys
   2. Click "Create API Key"
   3. Name: "Claude Code MCP"
   4. Copy the key
   ```

2. **Configure MCP** (1 min)
   ```bash
   claude mcp add render https://mcp.render.com/mcp \
     --header "Authorization: Bearer YOUR_API_KEY_HERE"
   ```

3. **Tell Claude Code:** "Set up environment variables for Render service srv-d3mlmmur433s73abuar0"

4. **Wait** (5 min) - Claude Code will:
   - Set all environment variables
   - Trigger deployment
   - Monitor status
   - Verify health

5. **Update Streamlit** (2 min)
   - Claude Code will guide you through this

✅ **Done!** Full stack operational

---

### Path B: Manual Dashboard Method 📝

**Time:** 10 minutes | **Difficulty:** Easy | **Repeatability:** Medium

1. **Open Render Dashboard** (1 min)
   ```
   https://dashboard.render.com/web/srv-d3mlmmur433s73abuar0
   ```
   Click "Environment" tab

2. **Add These 4 Variables** (2 min)

   Get values from your `.env` file and add:

   ```bash
   DATABASE_URL = [copy from .env]
   SUPABASE_URL = [copy from .env]
   SUPABASE_KEY = [copy from .env]
   SUPABASE_SERVICE_ROLE_KEY = [copy SUPABASE_SERVICE_KEY value from .env]
   ```

   ⚠️ **Important:** Last variable is `SUPABASE_SERVICE_ROLE_KEY` (not `_SERVICE_KEY`)

3. **Save** (auto-deploys in 3-5 min)

4. **Verify Backend** (after 5 min)
   ```bash
   curl -k "https://srv-d3mlmmur433s73abuar0.onrender.com/health"
   # Should return: {"status": "healthy"}
   ```

5. **Update Streamlit Secrets** (2 min)
   ```
   1. Go to: https://share.streamlit.io/
   2. Find app: "iswitchroofs"
   3. Settings → Secrets
   4. Update:
      api_base_url = "https://srv-d3mlmmur433s73abuar0.onrender.com"
      ml_api_base_url = "https://srv-d3mlmmur433s73abuar0.onrender.com"
   5. Save (auto-redeploys in 30 sec)
   ```

6. **Test Your App** (1 min)
   ```
   Visit: https://iswitchroofs.streamlit.app
   - Should load without errors
   - Test creating a lead
   - Test customer management
   ```

✅ **Done!** Full stack operational

---

## Verification Commands

```bash
# Check backend health
curl -k "https://srv-d3mlmmur433s73abuar0.onrender.com/health"

# Test leads API
curl -k "https://srv-d3mlmmur433s73abuar0.onrender.com/api/leads?limit=1"

# Run full verification
./verify-deployment.sh
```

## Expected Results

### Healthy Backend Response
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-10-13T..."
}
```

### Working Streamlit App
- No "Connection refused" errors
- Dashboard loads with data
- Lead creation works
- Customer management functional

---

## Troubleshooting

### Backend Returns 404
**Wait:** Deployment takes 3-5 minutes after setting env vars

**Check:**
- Render Dashboard → Logs for errors
- All 4 env vars are set correctly
- Variable names are exact

**Fix:** Manually trigger deploy:
```bash
curl -X POST "https://api.render.com/deploy/srv-d3mlmmur433s73abuar0?key=mT_YPrdnfTk"
```

### Streamlit Connection Error
**Check:**
- Backend health endpoint works first
- Streamlit secrets have correct URL
- Clear browser cache

**Fix:**
- Update Streamlit secrets with correct backend URL
- Wait 30 seconds for automatic redeploy

---

## Quick Links

| Resource | URL |
|----------|-----|
| **Render Dashboard** | https://dashboard.render.com/web/srv-d3mlmmur433s73abuar0 |
| **Streamlit Cloud** | https://share.streamlit.io/ |
| **Frontend App** | https://iswitchroofs.streamlit.app |
| **Create API Key** | https://dashboard.render.com/settings#api-keys |

---

## Full Documentation

For detailed information, see:

- **[DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)** - Complete overview
- **[RENDER_MCP_SETUP.md](RENDER_MCP_SETUP.md)** - MCP setup details
- **[RENDER_DEPLOYMENT_GUIDE.md](RENDER_DEPLOYMENT_GUIDE.md)** - Step-by-step guide
- **[DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md)** - Current status

---

**Bottom Line:** Pick a path above and follow the steps. You'll be fully operational in ~10 minutes!

*Last Updated: 2025-10-13*
