# 🚀 Render.com Deployment - Step-by-Step Guide

## ✅ Prerequisites Checklist

- [x] Backend code pushed to GitHub
- [x] `render.yaml` configuration file ready
- [x] Database credentials available (Supabase)
- [ ] Render.com account (we'll create this now)

---

## 📋 Step 1: Create Render Account (2 minutes)

1. **Open browser** and go to: https://render.com/
2. Click **"Get Started"** button (top right)
3. **Sign up with GitHub** (easiest option - click GitHub button)
4. Authorize Render to access your GitHub account
5. You'll be redirected to Render Dashboard

✅ **Done!** You now have a Render account.

---

## 📋 Step 2: Create Web Service (3 minutes)

1. In Render Dashboard, click **"New +"** button (top right)
2. Select **"Web Service"** from dropdown
3. You'll see "Create a new Web Service" page

### Connect GitHub Repository:

4. Find **"GrayGhostDev/client-roofing"** in the list
   - If you don't see it, click **"Configure account"** to give Render access
5. Click **"Connect"** button next to your repository

### Configure Service:

6. **Name**: `iswitch-roofs-api`
7. **Region**: `Oregon (US West)` (or closest to you)
8. **Branch**: `main`
9. **Root Directory**: `backend` ⚠️ **IMPORTANT**
10. **Runtime**: `Python 3`
11. **Build Command**:
    ```bash
    pip install --upgrade pip && pip install -r requirements.txt
    ```
12. **Start Command**:
    ```bash
    gunicorn -w 2 -k gevent --bind 0.0.0.0:$PORT --timeout 120 --access-logfile - --error-logfile - 'app:create_app()'
    ```

### Select Plan:

13. **Instance Type**: Select **"Free"** (at the bottom)
    - ✅ Free tier: 750 hours/month
    - ✅ Automatic SSL
    - ✅ Custom domains

14. Click **"Create Web Service"** button at bottom

⏳ Render will now start building your service (takes 3-5 minutes)

---

## 📋 Step 3: Add Environment Variables (5 minutes)

While the build is running, let's add environment variables:

1. In your service page, click **"Environment"** tab (left sidebar)
2. Click **"Add Environment Variable"** button
3. Add each variable below:

### 🔐 Required Environment Variables:

Copy these **one by one** (click "+ Add Environment Variable" for each):

#### Database Configuration:
```
Key: DATABASE_URL
Value: [Your Supabase PostgreSQL URL]
Note: Get from Supabase Dashboard → Settings → Database → Connection String (Direct)
```

```
Key: SUPABASE_URL
Value: [Your Supabase Project URL]
Note: Get from Supabase Dashboard → Settings → API → Project URL
Example: https://xxxxxxxxxxxxx.supabase.co
```

```
Key: SUPABASE_KEY
Value: [Your Supabase Anon Key]
Note: Get from Supabase Dashboard → Settings → API → Project API keys → anon/public
Example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

```
Key: SUPABASE_SERVICE_ROLE_KEY
Value: [Your Supabase Service Role Key]
Note: Get from Supabase Dashboard → Settings → API → Project API keys → service_role
⚠️ KEEP THIS SECRET - It has admin privileges
```

#### Security Configuration:
```
Key: SECRET_KEY
Value: [Generate new - see command below]
```

```
Key: JWT_SECRET_KEY
Value: [Generate new - see command below]
```

**Generate secrets in terminal:**
```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate JWT_SECRET_KEY (use different value)
openssl rand -hex 32
```

#### Environment Settings:
```
Key: FLASK_ENV
Value: production
```

```
Key: ENVIRONMENT
Value: production
```

```
Key: DEBUG
Value: false
```

```
Key: FLASK_DEBUG
Value: 0
```

#### CORS Configuration:
```
Key: BACKEND_CORS_ORIGINS
Value: https://iswitchroofs.streamlit.app,http://localhost:8501
```

```
Key: CORS_SUPPORTS_CREDENTIALS
Value: true
```

#### JWT Settings:
```
Key: JWT_ALGORITHM
Value: HS256
```

```
Key: JWT_ACCESS_TOKEN_EXPIRES
Value: 3600
```

#### Feature Flags:
```
Key: SKIP_AUTH
Value: true
```

```
Key: ENABLE_LEAD_SCORING
Value: true
```

### 🎯 Optional (Add if you have these services):

#### Pusher (Real-time updates):
```
Key: PUSHER_APP_ID
Value: [Your Pusher App ID]

Key: PUSHER_KEY
Value: [Your Pusher Key]

Key: PUSHER_SECRET
Value: [Your Pusher Secret]

Key: PUSHER_CLUSTER
Value: us2

Key: PUSHER_SSL
Value: true
```

#### Redis (Caching - if you add Redis add-on):
```
Key: REDIS_URL
Value: [Your Redis URL]
Note: Format: redis://username:password@host:port/0
```

4. After adding all variables, click **"Save Changes"**
5. Render will automatically redeploy with new environment variables

---

## 📋 Step 4: Monitor Deployment (3-5 minutes)

1. Click **"Logs"** tab to watch deployment progress
2. You'll see:
   - ⏳ Installing dependencies...
   - ⏳ Building application...
   - ⏳ Starting web service...
   - ✅ **"Your service is live"** 🎉

3. Once you see: `Live` indicator (green dot at top)
   - Your API URL will be shown: `https://iswitch-roofs-api.onrender.com`

---

## 📋 Step 5: Test Your API (1 minute)

### Test in Browser:

1. Copy your API URL: `https://iswitch-roofs-api.onrender.com`
2. Open in browser: `https://iswitch-roofs-api.onrender.com/health`
3. You should see:
   ```json
   {
     "status": "healthy",
     "timestamp": "2025-10-13T...",
     "environment": "production",
     "database": "connected"
   }
   ```

### Test in Terminal:

```bash
# Test health endpoint
curl https://iswitch-roofs-api.onrender.com/health

# Test leads API
curl https://iswitch-roofs-api.onrender.com/api/leads?limit=5

# Test customers API
curl https://iswitch-roofs-api.onrender.com/api/customers?limit=5
```

✅ **If you see JSON responses, your API is working!**

---

## 📋 Step 6: Configure Streamlit Cloud (2 minutes)

Now connect your Streamlit frontend to the production backend:

1. Go to: https://share.streamlit.io/
2. Find your app: **"iswitchroofs"**
3. Click **"Settings"** (gear icon or three dots menu)
4. Click **"Secrets"** in the left sidebar
5. **Replace the entire secrets content** with:

```toml
[default]
# Production API URLs
api_base_url = "https://iswitch-roofs-api.onrender.com"
ml_api_base_url = "https://iswitch-roofs-api.onrender.com"

# Pusher Configuration (if you have it)
pusher_app_id = "1890740"
pusher_key = "fe32b6bb02f0c1a41bb4"
pusher_secret = "e2b7e61a1b6c1aca04b0"
pusher_cluster = "us2"
```

6. Click **"Save"**
7. Streamlit will automatically restart your app (takes 30 seconds)

---

## 📋 Step 7: Test Full Stack Connection (1 minute)

1. Open your Streamlit app: https://iswitchroofs.streamlit.app/
2. You should see:
   - ✅ No more "Connection refused" errors
   - ✅ Dashboard loads with data
   - ✅ Leads, Customers, Projects pages work
   - ✅ Real-time features active

### Verify Connection:

- Check the Dashboard - should load without errors
- Navigate to Leads Management - should show leads
- Check connection status indicator (if visible) - should be green

---

## 🎉 Success! Your CRM is Live!

### **Production URLs:**

- 🔗 **Backend API**: `https://iswitch-roofs-api.onrender.com`
- 🔗 **Frontend App**: `https://iswitchroofs.streamlit.app`
- 🔗 **API Health**: `https://iswitch-roofs-api.onrender.com/health`
- 🔗 **API Docs**: `https://iswitch-roofs-api.onrender.com/api/docs` (if enabled)

### **Next Steps:**

- ✅ Backend deployed and running
- ✅ Frontend connected to backend
- ✅ Full CRM functionality active
- ✅ Ready for production use!

---

## 🔧 Troubleshooting

### ❌ Build Fails

**Check Logs:**
1. Go to your service in Render
2. Click "Logs" tab
3. Look for error messages (usually red text)

**Common Issues:**
- Missing dependencies in `requirements.txt`
- Python version mismatch
- Incorrect build command

**Solution:**
```bash
# Fix locally and push
git add .
git commit -m "fix: resolve build issues"
git push origin main
# Render auto-deploys on push
```

### ❌ Service Starts but Health Check Fails

**Check:**
1. Environment variables are set correctly
2. Database URL is valid (test connection)
3. All required variables are present

**View Logs:**
- Render Dashboard → Your Service → Logs
- Look for database connection errors

### ❌ Streamlit Still Shows Connection Error

**Verify:**
1. API URL in Streamlit secrets matches Render URL exactly
2. No typos in `api_base_url`
3. Render service is actually running (check dashboard)
4. Try accessing API URL directly in browser

**Force Refresh:**
1. Streamlit Cloud → Your App → Manage App → Reboot

### ❌ CORS Errors

**Add to Render Environment Variables:**
```
BACKEND_CORS_ORIGINS=https://iswitchroofs.streamlit.app,http://localhost:8501
```

Then click "Save Changes" to redeploy.

---

## 📊 Render Free Tier Limits

- ✅ 750 hours/month (enough for 24/7 if only 1 app)
- ✅ Sleeps after 15 minutes of inactivity
- ⏳ Wake-up time: ~30 seconds (first request after sleep)
- ✅ Automatic SSL certificates
- ✅ Automatic deploys on git push

### Keep Your Service Awake (Optional):

Use a service like UptimeRobot or cron-job.org to ping your health endpoint every 10 minutes:

```
GET https://iswitch-roofs-api.onrender.com/health
```

This prevents sleeping and keeps response times fast.

---

## 🚀 Deployment Complete!

**Summary:**
- ✅ Backend API live on Render
- ✅ Frontend connected to production API
- ✅ All CRM features operational
- ✅ Automatic deployments on git push

**You're all set!** 🎉

---

*Last Updated: 2025-10-13*
*Platform: Render.com*
*Backend: Flask + PostgreSQL*
*Frontend: Streamlit Cloud*
