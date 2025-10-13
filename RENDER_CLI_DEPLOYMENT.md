# 🚀 Render CLI Deployment Guide

Complete guide for deploying iSwitch Roofs Backend using Render CLI

---

## ⚡ Quick Deploy (3 Commands)

```bash
# 1. Authenticate with Render
render login

# 2. Create .env.production with your credentials (see template)
cp .env.production.template .env.production
# Edit .env.production with your Supabase credentials

# 3. Deploy!
./deploy-to-render.sh
```

---

## 📋 Detailed Step-by-Step

### **Step 1: Install Render CLI** (if not already installed)

```bash
# macOS (via Homebrew)
brew install render

# Or download from: https://render.com/docs/cli
```

Verify installation:
```bash
render --version
```

---

### **Step 2: Authenticate with Render**

```bash
render login
```

This will:
1. Open your browser
2. Prompt you to log in to Render (or create account)
3. Grant CLI access
4. Save credentials locally

Verify authentication:
```bash
render whoami
```

You should see your email address.

---

### **Step 3: Prepare Environment Variables**

#### Get Your Supabase Credentials:

1. Go to: https://supabase.com/dashboard/
2. Select your project (or create one)
3. Navigate to **Settings** → **Database**
   - Copy **Connection string** (with connection pooling)
   - Format: `postgresql://postgres.[PROJECT-REF]:[PASSWORD]@...`

4. Navigate to **Settings** → **API**
   - Copy **Project URL**: `https://xxxxx.supabase.co`
   - Copy **anon/public key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
   - Copy **service_role key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

#### Create .env.production:

```bash
# Copy template
cp .env.production.template .env.production

# Edit with your actual values
nano .env.production
# or
code .env.production
```

**Example .env.production:**
```bash
DATABASE_URL=postgresql://postgres.abcdefgh:MyP@ssw0rd@aws-0-us-west-1.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://abcdefghijklmnop.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0...
```

**Important:**
- ⚠️ Never commit `.env.production` to git
- ✅ Already in `.gitignore`
- 🔒 Keep `SUPABASE_SERVICE_ROLE_KEY` secret

---

### **Step 4: Deploy Using Automated Script**

```bash
./deploy-to-render.sh
```

The script will:
1. ✅ Check Render CLI is installed
2. ✅ Verify authentication
3. ✅ Validate environment variables
4. ✅ Deploy backend using `render.yaml`
5. ✅ Set environment variables from `.env.production`
6. ✅ Show deployment status and URL

**Expected output:**
```
🚀 iSwitch Roofs CRM - Render Deployment Script
================================================

📋 Step 1: Checking Render CLI installation...
✅ Render CLI is installed

📋 Step 2: Checking Render authentication...
✅ Authenticated as: your-email@example.com

📋 Step 3: Checking environment variables...
✅ Environment variables validated

📋 Step 4: Preparing deployment...
✅ render.yaml found

📋 Step 5: Deploying to Render...
🚀 Starting deployment...
✅ Service created successfully!

🔗 Service URL: https://iswitch-roofs-api.onrender.com

================================================
🎉 Deployment Complete!
================================================
```

---

### **Step 5: Monitor Deployment**

Watch deployment logs:
```bash
render services logs iswitch-roofs-api --tail
```

Check service status:
```bash
render services list
```

Get service info:
```bash
render services get iswitch-roofs-api
```

---

### **Step 6: Test Your API**

Once deployment completes (3-5 minutes):

```bash
# Test health endpoint
curl https://iswitch-roofs-api.onrender.com/health

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2025-10-13T...",
#   "environment": "production",
#   "database": "connected"
# }
```

Test other endpoints:
```bash
# Test leads API
curl https://iswitch-roofs-api.onrender.com/api/leads?limit=5

# Test customers API
curl https://iswitch-roofs-api.onrender.com/api/customers?limit=5
```

---

### **Step 7: Update Streamlit Cloud**

Now connect your Streamlit frontend:

1. Go to: https://share.streamlit.io/
2. Find your app: **"iswitchroofs"**
3. Click **Settings** → **Secrets**
4. Update secrets:

```toml
[default]
api_base_url = "https://iswitch-roofs-api.onrender.com"
ml_api_base_url = "https://iswitch-roofs-api.onrender.com"

# Add other secrets if you have them
pusher_app_id = "1890740"
pusher_key = "fe32b6bb02f0c1a41bb4"
pusher_secret = "e2b7e61a1b6c1aca04b0"
pusher_cluster = "us2"
```

5. Click **Save**
6. Wait 30 seconds for restart
7. Open: https://iswitchroofs.streamlit.app/

✅ **Your CRM should now be fully connected!**

---

## 🔧 Render CLI Commands Reference

### Service Management

```bash
# List all services
render services list

# Get service details
render services get iswitch-roofs-api

# View logs (live tail)
render services logs iswitch-roofs-api --tail

# View logs (last 100 lines)
render services logs iswitch-roofs-api --num 100

# Restart service
render services restart iswitch-roofs-api

# Delete service
render services delete iswitch-roofs-api
```

### Environment Variables

```bash
# List environment variables
render config iswitch-roofs-api

# Set a single variable
render config:set --service iswitch-roofs-api KEY=value

# Set multiple variables from file
render config:set --service iswitch-roofs-api --env-file .env.production

# Unset a variable
render config:unset --service iswitch-roofs-api KEY
```

### Deployments

```bash
# Create new service from render.yaml
render services create --yaml backend/render.yaml

# Update existing service
render services update iswitch-roofs-api --yaml backend/render.yaml

# Trigger manual deploy
render services deploy iswitch-roofs-api

# List deployments
render deploys list --service iswitch-roofs-api
```

---

## 🔍 Troubleshooting

### Authentication Issues

```bash
# Re-authenticate
render login

# Check current user
render whoami

# Logout and re-login
render logout
render login
```

### Deployment Fails

```bash
# Check logs for errors
render services logs iswitch-roofs-api --num 200

# Common issues:
# 1. Missing environment variables
# 2. Invalid DATABASE_URL
# 3. Python version mismatch
# 4. Missing dependencies in requirements.txt
```

### Environment Variables Not Set

```bash
# Verify variables are set
render config iswitch-roofs-api

# Re-set from file
render config:set --service iswitch-roofs-api --env-file .env.production

# Or set individual variables
render config:set --service iswitch-roofs-api DATABASE_URL="postgresql://..."
```

### Service Won't Start

```bash
# Check service status
render services get iswitch-roofs-api

# View recent logs
render services logs iswitch-roofs-api --tail

# Try restart
render services restart iswitch-roofs-api

# If all else fails, redeploy
render services deploy iswitch-roofs-api
```

---

## 📊 Monitoring & Maintenance

### Check Service Health

```bash
# Via CLI
render services get iswitch-roofs-api

# Via curl
curl https://iswitch-roofs-api.onrender.com/health
```

### View Metrics

```bash
# In Render Dashboard
# https://dashboard.render.com/web/iswitch-roofs-api

# Shows:
# - CPU usage
# - Memory usage
# - Request rate
# - Response times
# - Error rate
```

### Auto-Deploy on Git Push

With `autoDeploy: true` in render.yaml:
- Every push to `main` branch triggers automatic deployment
- Monitor with: `render services logs iswitch-roofs-api --tail`

---

## ✅ Success Checklist

After deployment, verify:

- [ ] Render CLI authenticated
- [ ] `.env.production` created with valid Supabase credentials
- [ ] `./deploy-to-render.sh` completed successfully
- [ ] Service shows as "Live" in Render dashboard
- [ ] Health endpoint returns `{"status": "healthy"}`
- [ ] API endpoints return data
- [ ] Streamlit secrets updated with API URL
- [ ] Streamlit app loads without "Connection refused" errors
- [ ] Dashboard shows real data from backend

---

## 🚀 You're Done!

**Your full stack is now deployed:**
- ✅ Backend API on Render: `https://iswitch-roofs-api.onrender.com`
- ✅ Frontend on Streamlit: `https://iswitchroofs.streamlit.app`
- ✅ Database on Supabase
- ✅ Auto-deploys on git push

---

*For issues or questions, check the Render docs: https://render.com/docs*
