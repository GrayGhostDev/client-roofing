# iSwitch Roofs CRM - Vercel Backend Deployment Guide

## ⚠️ Important: Vercel Limitations for Flask

Before deploying to Vercel, understand these constraints:

### **Vercel Serverless Limitations:**

1. **❌ 10-second timeout** (free tier) or 60s (paid)
2. **❌ Stateless** - No persistent connections (WebSockets, long-polling)
3. **❌ Cold starts** - 1-3 second delay on first request
4. **❌ 50MB package size limit**
5. **✅ Good for**: API endpoints, stateless requests
6. **❌ Not ideal for**: Real-time features, background jobs, long processes

### **Recommendation:**

For your CRM with real-time features (Pusher, live updates), **Render.com or Railway** are better choices because they provide:
- Always-on containers (no cold starts)
- No timeout limits
- WebSocket support
- Background job support

**However**, if you want to proceed with Vercel for basic API functionality, here's how:

---

## 🚀 Vercel Deployment Steps

### **Prerequisites**

1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Login to Vercel:
   ```bash
   vercel login
   ```

### **Option 1: Deploy via CLI (Fastest)**

```bash
# 1. Navigate to project root
cd /Users/grayghostdataconsultants/Development/projects/clients/client-roofing

# 2. Deploy to Vercel
vercel --prod

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name: iswitch-roofs-backend
# - Directory with code: ./
# - Override settings? No

# 3. Your API will be deployed to: https://iswitch-roofs-backend.vercel.app
```

### **Option 2: Deploy via Vercel Dashboard**

1. Go to https://vercel.com/dashboard
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository: `GrayGhostDev/client-roofing`
4. Configure:
   - **Framework Preset**: Other
   - **Root Directory**: Leave as `./`
   - **Build Command**: Leave empty
   - **Output Directory**: Leave empty
5. Add Environment Variables (see below)
6. Click **"Deploy"**

---

## 🔐 Environment Variables (Vercel Dashboard)

Add these in Vercel Dashboard → Your Project → Settings → Environment Variables:

### **Required:**

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/database
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Security (generate with: openssl rand -hex 32)
SECRET_KEY=your-secret-key-32-chars
JWT_SECRET_KEY=your-jwt-secret-32-chars

# Environment
FLASK_ENV=production
ENVIRONMENT=production
DEBUG=false

# CORS
BACKEND_CORS_ORIGINS=https://iswitchroofs.streamlit.app
```

### **Optional (if using):**

```bash
# Pusher (real-time updates - may not work well in serverless)
PUSHER_APP_ID=1890740
PUSHER_KEY=fe32b6bb02f0c1a41bb4
PUSHER_SECRET=e2b7e61a1b6c1aca04b0
PUSHER_CLUSTER=us2

# Redis (caching - requires external Redis service)
REDIS_HOST=your-redis-host.com
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
```

---

## 📋 After Deployment

### **1. Get Your API URL**

After deployment, you'll get: `https://iswitch-roofs-backend.vercel.app`

### **2. Test the API**

```bash
# Test health endpoint
curl https://iswitch-roofs-backend.vercel.app/health

# Expected response (may take 1-3s first time due to cold start):
# {
#   "status": "healthy",
#   "timestamp": "2025-10-13T...",
#   "environment": "production"
# }
```

### **3. Test API endpoints**

```bash
# Test leads endpoint
curl https://iswitch-roofs-backend.vercel.app/api/leads?limit=5

# Test customers endpoint
curl https://iswitch-roofs-backend.vercel.app/api/customers?limit=5
```

### **4. Configure Streamlit Cloud**

1. Go to https://share.streamlit.io/
2. Click your app → **Settings** → **Secrets**
3. Add:

```toml
[default]
api_base_url = "https://iswitch-roofs-backend.vercel.app"
ml_api_base_url = "https://iswitch-roofs-backend.vercel.app"

# Copy other secrets from your local .streamlit/secrets.toml
pusher_app_id = "1890740"
pusher_key = "fe32b6bb02f0c1a41bb4"
pusher_secret = "e2b7e61a1b6c1aca04b0"
pusher_cluster = "us2"
```

4. Save and your app will restart

---

## ⚡ Performance Considerations

### **Cold Starts**

- First request after inactivity: **1-3 seconds**
- Subsequent requests: **<100ms**
- Keep warm by pinging `/health` every 5 minutes (optional)

### **Timeout Issues**

If you get timeout errors:
- Optimize database queries
- Add database indexes
- Use caching for expensive operations
- Consider upgrading to Vercel Pro (60s timeout)

---

## 🔧 Troubleshooting

### **Deployment Fails**

```bash
# Check logs
vercel logs https://iswitch-roofs-backend.vercel.app --follow

# Redeploy
vercel --prod --force
```

### **Import Errors**

Vercel has a 50MB size limit. If you get package size errors:
- Use `requirements-vercel.txt` (minimal dependencies)
- Remove unused packages
- Consider Railway/Render for full feature set

### **Environment Variables Not Working**

- Verify variables are set in Vercel Dashboard
- Redeploy after adding variables
- Check variable names match exactly (case-sensitive)

### **CORS Errors**

Update vercel.backend.json CORS headers:
```json
{
  "key": "Access-Control-Allow-Origin",
  "value": "https://iswitchroofs.streamlit.app"
}
```

---

## 🎯 Vercel vs Alternative Platforms

| Feature | Vercel | Render | Railway |
|---------|--------|--------|---------|
| **Timeout** | 10s (free) / 60s (pro) | No limit | No limit |
| **Cold Starts** | Yes (1-3s) | No | No |
| **WebSockets** | ❌ No | ✅ Yes | ✅ Yes |
| **Background Jobs** | ❌ No | ✅ Yes | ✅ Yes |
| **Price (Free Tier)** | $0 | $0 (750hrs) | $5 credit |
| **Best For** | Stateless APIs | Full Flask apps | Full Flask apps |

### **My Recommendation:**

Given your CRM has:
- Real-time features (Pusher)
- Complex database operations
- Potential long-running requests
- Background processing needs

**I strongly recommend Railway.app or Render.com instead of Vercel.**

They're just as easy to deploy but won't have the serverless limitations.

---

## 🚀 Quick Switch to Render (Recommended)

If Vercel gives issues, switch to Render in 5 minutes:

```bash
# Already configured! Just go to render.com
# 1. New Web Service
# 2. Connect GitHub repo
# 3. Root: backend/
# 4. Use existing render.yaml configuration
# 5. Add environment variables
# 6. Deploy!

# URL will be: https://iswitch-roofs-api.onrender.com
```

---

## 📞 Next Steps

Choose your path:

### **Path A: Continue with Vercel**
- Deploy using steps above
- Test thoroughly
- Monitor for timeout issues
- May need to disable some real-time features

### **Path B: Switch to Render (Recommended)**
- Better for your use case
- No serverless limitations
- See `BACKEND_DEPLOYMENT_GUIDE.md`
- Deploy in 5 minutes

**Which would you like to proceed with?**

---

*Last Updated: 2025-10-13*
*Configuration for: Vercel Serverless Functions*
