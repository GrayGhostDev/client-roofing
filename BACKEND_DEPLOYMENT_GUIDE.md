# iSwitch Roofs CRM - Backend API Deployment Guide

## 🎯 Quick Deploy Options

You have **3 easy deployment options** for the Flask backend API:

### **Option 1: Render.com (Recommended - Free Tier)**

✅ **Pros**: Free tier, automatic SSL, easy setup, great for Flask apps
📋 **Steps**:

1. Go to https://render.com and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository: `GrayGhostDev/client-roofing`
4. Configure:
   - **Name**: `iswitch-roofs-api`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 2 -k gevent --bind 0.0.0.0:$PORT --timeout 120 --access-logfile - --error-logfile - 'app:create_app()'`
5. Add Environment Variables (see below)
6. Click **"Create Web Service"**
7. Wait 3-5 minutes for deployment
8. Your API will be available at: `https://iswitch-roofs-api.onrender.com`

### **Option 2: Railway.app**

✅ **Pros**: Easy deployment, good free tier, auto-deploys from GitHub
📋 **Steps**:

1. Go to https://railway.app and sign up/login
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your repository and click **"Deploy"**
4. Railway will detect the `railway.backend.json` configuration
5. Add Environment Variables (see below)
6. Your API will be available at: `https://your-project.up.railway.app`

### **Option 3: Fly.io**

✅ **Pros**: Global edge network, generous free tier
📋 **Steps**:

1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Login: `fly auth login`
3. Navigate to backend: `cd backend`
4. Deploy: `fly launch`
5. Follow prompts to create and deploy
6. Your API will be available at: `https://your-app.fly.dev`

---

## 🔐 Required Environment Variables

Add these to your deployment platform:

### **Essential (Required)**

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/database
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Security (auto-generate with: openssl rand -hex 32)
SECRET_KEY=<auto-generate-32-char-hex>
JWT_SECRET_KEY=<auto-generate-32-char-hex>

# CORS - Allow Streamlit frontend
BACKEND_CORS_ORIGINS=["https://iswitchroofs.streamlit.app","http://localhost:8501"]

# Environment
ENVIRONMENT=production
DEBUG=false
FLASK_ENV=production
```

### **Optional (Real-time features)**

```bash
# Pusher (for real-time updates)
PUSHER_APP_ID=1890740
PUSHER_KEY=fe32b6bb02f0c1a41bb4
PUSHER_SECRET=e2b7e61a1b6c1aca04b0
PUSHER_CLUSTER=us2

# Redis (for caching) - if you have Redis add-on
REDIS_HOST=your-redis-host
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
```

---

## ⚡ Quick Start (Choose One Platform)

### **Render.com (Easiest)**

```bash
# 1. Push code to GitHub (already done)
git push origin main

# 2. Go to Render.com dashboard
# 3. Click "New Web Service"
# 4. Select your repo: client-roofing
# 5. Configure as shown above
# 6. Add environment variables
# 7. Deploy!

# Your API URL will be: https://iswitch-roofs-api.onrender.com
```

### **Railway.app**

```bash
# 1. Push code to GitHub (already done)
git push origin main

# 2. Go to Railway dashboard
# 3. New Project → Deploy from GitHub
# 4. Select client-roofing repo
# 5. Railway auto-detects configuration
# 6. Add environment variables
# 7. Deploy!

# Your API URL will be: https://[project-name].up.railway.app
```

---

## 🔗 After Deployment

### **1. Get Your API URL**

After deployment completes, you'll receive a URL like:
- Render: `https://iswitch-roofs-api.onrender.com`
- Railway: `https://iswitch-roofs-api.up.railway.app`
- Fly.io: `https://iswitch-roofs-api.fly.dev`

### **2. Test the API**

```bash
# Test health endpoint
curl https://YOUR-API-URL/health

# Should return:
# {"status": "healthy", "database": "connected", ...}
```

### **3. Configure Streamlit Cloud**

1. Go to https://share.streamlit.io/
2. Click on your app "iswitchroofs"
3. Click "Settings" → "Secrets"
4. Add this secret:

```toml
[default]
api_base_url = "https://YOUR-API-URL"
ml_api_base_url = "https://YOUR-API-URL"
```

5. Save and your app will restart
6. Connection should work! 🎉

---

## 🚀 Deployment Status Checklist

- [ ] Choose deployment platform (Render/Railway/Fly.io)
- [ ] Create web service from GitHub repo
- [ ] Configure build and start commands
- [ ] Add required environment variables
- [ ] Wait for deployment to complete (3-5 minutes)
- [ ] Test `/health` endpoint
- [ ] Add API URL to Streamlit Cloud secrets
- [ ] Test Streamlit app connection

---

## 📊 Cost Comparison

| Platform | Free Tier | Startup Time | Auto-Sleep |
|----------|-----------|--------------|------------|
| **Render** | 750 hrs/month | ~30-60s | After 15min inactive |
| **Railway** | $5 credit/month | ~10-20s | No |
| **Fly.io** | 3 shared VMs | ~5-10s | No |

**Recommendation**: Start with **Render.com** for simplicity. Upgrade to Railway or Fly.io if you need better performance.

---

## 🔧 Troubleshooting

### **Build Fails**

- Check that `requirements.txt` has all dependencies
- Ensure Python version is 3.11
- Check build logs for specific errors

### **App Crashes on Start**

- Verify all required environment variables are set
- Check that `DATABASE_URL` and `SUPABASE_URL` are valid
- Review application logs

### **Health Check Fails**

- Ensure `/health` endpoint is accessible
- Check that app binds to `0.0.0.0:$PORT`
- Verify database connection works

### **Streamlit Can't Connect**

- Ensure CORS is configured correctly
- Verify API URL in Streamlit secrets matches deployment URL
- Check that API is publicly accessible (not localhost)

---

## 📞 Next Steps

After successful deployment:

1. ✅ Backend API deployed and running
2. ✅ Health check passing
3. ✅ Streamlit configured with production API URL
4. ✅ Test full stack: Streamlit → API → Database → Streamlit

**Your CRM is now live in production!** 🚀

---

*Last Updated: 2025-10-13*
*Backend Version: 1.0.0*
