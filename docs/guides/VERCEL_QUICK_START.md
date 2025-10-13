# 🚀 Vercel Stack - Quick Start Guide

**Deploy the iSwitch Roofs ML System in 30 Minutes**

**Stack**: Vercel + Railway + Upstash + n8n Cloud + Supabase
**Cost**: $130/month (vs $335/month on AWS - save $2,460/year!)
**Difficulty**: Beginner-friendly ⭐⭐☆☆☆

---

## 📋 Prerequisites (5 minutes)

### **Accounts Needed** (all have generous free tiers):

1. ✅ **GitHub Account** (you already have this)
2. ✅ **Vercel** - https://vercel.com/signup (free)
3. ✅ **Railway** - https://railway.app/ (free $5 credit/month)
4. ✅ **Upstash** - https://upstash.com/ (10K requests/day free)
5. ✅ **n8n Cloud** - https://n8n.io/cloud (5K executions/month free)
6. ✅ **Streamlit Cloud** - https://streamlit.io/cloud (free)
7. ✅ **Supabase** - https://supabase.com/ (already have)
8. ✅ **Grafana Cloud** - https://grafana.com/ (free tier)

### **Tools to Install**:

```bash
# Vercel CLI
npm install -g vercel

# Railway CLI
npm install -g @railway/cli

# Login to services
vercel login
railway login
```

---

## 🎯 30-Minute Deployment Checklist

Follow these steps in order. Each step takes ~5 minutes.

### ☑️ **Step 1: Set Up Upstash Redis** (3 minutes)

1. Go to https://upstash.com/ → Sign up with GitHub
2. Click "Create Database"
   - Name: `iswitch-ml-cache`
   - Type: **Global** (for low latency worldwide)
   - Region: **US-EAST-1**
   - Enable TLS: ✅
3. Click "Create"
4. Copy connection details:
   ```
   UPSTASH_REDIS_REST_URL=https://your-db.upstash.io
   UPSTASH_REDIS_REST_TOKEN=your-token
   ```
5. Save these for later ✅

---

### ☑️ **Step 2: Deploy ML API to Railway** (10 minutes)

1. **Sign up for Railway**:
   - Go to https://railway.app/
   - Click "Login with GitHub"
   - Authorize Railway

2. **Create New Project**:
   ```bash
   cd /path/to/client-roofing
   railway init
   ```
   - Project name: `iswitch-ml-api`
   - Press Enter

3. **Link GitHub Repository**:
   ```bash
   railway link
   ```
   - Select: `client-roofing` repository

4. **Set Environment Variables**:
   ```bash
   # Supabase (you already have these)
   railway variables set SUPABASE_URL="https://yourproject.supabase.co"
   railway variables set SUPABASE_KEY="your-service-key-here"

   # OpenAI (get from https://platform.openai.com/api-keys)
   railway variables set OPENAI_API_KEY="sk-..."

   # Upstash Redis (from Step 1)
   railway variables set UPSTASH_REDIS_REST_URL="https://your-db.upstash.io"
   railway variables set UPSTASH_REDIS_REST_TOKEN="your-token"

   # Production flag
   railway variables set ENVIRONMENT="production"
   ```

5. **Upload Models to Supabase Storage**:
   ```bash
   # First, create storage bucket in Supabase dashboard
   # Go to: Supabase → Storage → Create new bucket
   # Name: ml-models
   # Public: No (private)

   # Then upload models using Python:
   python3 << 'EOF'
   from supabase import create_client
   import os

   supabase = create_client(
       "https://yourproject.supabase.co",
       "your-service-key-here"
   )

   # Upload NBA model
   with open('backend/models/nba_model_v1.0.joblib', 'rb') as f:
       supabase.storage.from_('ml-models').upload(
           'production/nba_model_v1.0.joblib', f
       )

   # Upload metadata
   with open('backend/models/nba_model_v1.0_metadata.json', 'rb') as f:
       supabase.storage.from_('ml-models').upload(
           'production/nba_model_v1.0_metadata.json', f
       )

   print("✅ Models uploaded to Supabase Storage")
   EOF
   ```

6. **Deploy to Railway**:
   ```bash
   cd backend
   railway up
   ```

   Railway will:
   - Build Docker image from `Dockerfile.ml`
   - Download models from Supabase
   - Start FastAPI server
   - Assign public URL

7. **Get Your Railway URL**:
   ```bash
   railway open
   ```
   - Your URL will be something like: `https://iswitch-ml-api.up.railway.app`
   - **Save this URL** - you'll need it for other services

8. **Test the Deployment**:
   ```bash
   # Replace with your actual Railway URL
   RAILWAY_URL="https://iswitch-ml-api.up.railway.app"

   # Test health
   curl $RAILWAY_URL/api/v1/ml/health

   # Should return: {"status":"healthy","model_loaded":true}
   ```

✅ **ML API is now deployed on Railway!**

---

### ☑️ **Step 3: Deploy Dashboard to Streamlit Cloud** (5 minutes)

1. **Go to Streamlit Cloud**:
   - Visit: https://share.streamlit.io/
   - Click "Sign up" → Use GitHub

2. **Deploy New App**:
   - Click "New app"
   - Repository: `client-roofing`
   - Branch: `main`
   - Main file path: `frontend-streamlit/Home.py`
   - Click "Deploy"

3. **Add Secrets** (in Streamlit Cloud dashboard):
   - Click "⚙️ Settings" → "Secrets"
   - Paste this (update with your values):
   ```toml
   [default]
   ml_api_base_url = "https://iswitch-ml-api.up.railway.app"
   supabase_url = "https://yourproject.supabase.co"
   supabase_key = "your-anon-key-here"
   pusher_app_id = "1890740"
   pusher_key = "fe32b6bb02f0c1a41bb4"
   pusher_secret = "e2b7e61a1b6c1aca04b0"
   pusher_cluster = "us2"
   ```

4. **Save & Reboot**:
   - Click "Save"
   - App will redeploy automatically

5. **Your Dashboard URL**:
   ```
   https://iswitch-roofs-ml.streamlit.app
   ```

✅ **Dashboard is now live on Streamlit Cloud!**

---

### ☑️ **Step 4: Set Up n8n Cloud Workflows** (7 minutes)

1. **Sign up for n8n Cloud**:
   - Go to: https://n8n.io/cloud
   - Click "Start free trial"
   - Choose "Pro Plan" ($50/month - 100K executions)

2. **Create Instance**:
   - Instance name: `iswitch-ml-workflows`
   - Region: **US-EAST**
   - Click "Create instance"

3. **Import Workflows**:
   - Click "Workflows" → "Import from File"
   - Upload these 5 files (one by one):
     ```
     backend/workflows/n8n/01_automated_daily_retraining.json
     backend/workflows/n8n/02_realtime_lead_scoring.json
     backend/workflows/n8n/03_model_drift_detection.json
     backend/workflows/n8n/04_batch_prediction_pipeline.json
     backend/workflows/n8n/05_gpt_enhancement_queue.json
     ```

4. **Configure Credentials** (for all workflows):

   **a) PostgreSQL (Supabase)**:
   - Name: `Supabase Production DB`
   - Host: `db.yourproject.supabase.co`
   - Database: `postgres`
   - User: `postgres`
   - Password: `your-password`
   - Port: `5432`
   - SSL: ✅ **require**

   **b) OpenAI**:
   - Name: `OpenAI GPT-5`
   - API Key: `sk-...`

   **c) Slack OAuth**:
   - Follow n8n's OAuth flow
   - Authorize your Slack workspace

   **d) HTTP Request** (for ML API):
   - Base URL: `https://iswitch-ml-api.up.railway.app`

5. **Update ML API URLs in All Workflows**:
   - In each workflow, find nodes calling `http://localhost:8000`
   - Replace with: `https://iswitch-ml-api.up.railway.app`

6. **Activate Workflows**:
   - Toggle "Active" on each workflow
   - Test with "Execute Workflow" button

✅ **All 5 workflows are now running on n8n Cloud!**

---

### ☑️ **Step 5: Set Up Monitoring (Grafana Cloud)** (5 minutes)

1. **Sign up for Grafana Cloud**:
   - Go to: https://grafana.com/auth/sign-up
   - Choose "Free Forever" plan
   - Sign up with GitHub

2. **Add Data Sources**:

   **a) Railway Metrics**:
   - Go to: Connections → Data Sources → Add Prometheus
   - Get URL from Railway dashboard → Your Project → Observability
   - Save & Test

   **b) Upstash Redis**:
   - Add Prometheus data source
   - Get URL from Upstash dashboard → Your DB → Monitoring

3. **Import Dashboards**:
   - Go to: Dashboards → Import
   - Import by ID:
     - FastAPI: `14405`
     - Redis: `11835`
     - PostgreSQL: `9628`

4. **Create Custom Dashboard**:
   - Name: "iSwitch ML System"
   - Add panels:
     - API Request Rate
     - Model Accuracy
     - Prediction Latency
     - Error Rate

5. **Set Up Alerts**:
   ```yaml
   # Alert when error rate > 1%
   - name: high-error-rate
     condition: error_rate > 1%
     notify: slack

   # Alert when model accuracy < 75%
   - name: low-accuracy
     condition: model_accuracy < 75%
     notify: slack, email
   ```

✅ **Monitoring is now set up in Grafana Cloud!**

---

## 🎉 You're Done! Test Everything

### **1. Test ML API**:
```bash
# Health check
curl https://iswitch-ml-api.up.railway.app/api/v1/ml/health

# Get metrics
curl https://iswitch-ml-api.up.railway.app/api/v1/ml/metrics

# Make a prediction
curl -X POST https://iswitch-ml-api.up.railway.app/api/v1/ml/predict/nba \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": "test-001",
    "source": "website",
    "created_at": "2025-10-11T10:00:00",
    "property_zip": "48304",
    "estimated_value": 850000,
    "interaction_count": 3,
    "email_open_rate": 0.5,
    "response_rate": 0.3,
    "lead_score": 75
  }'
```

### **2. Test Dashboard**:
- Visit: `https://iswitch-roofs-ml.streamlit.app`
- Click "ML Dashboard" in sidebar
- Verify metrics are displaying

### **3. Test n8n Workflows**:
- Go to n8n Cloud → Workflows
- Click "Execute Workflow" on any workflow
- Check execution logs

### **4. Test Monitoring**:
- Go to Grafana Cloud
- Check dashboards are showing data
- Verify alerts are configured

---

## 📊 Your Live URLs

| Service | URL |
|---------|-----|
| **ML API** | https://iswitch-ml-api.up.railway.app |
| **API Docs** | https://iswitch-ml-api.up.railway.app/api/docs |
| **Dashboard** | https://iswitch-roofs-ml.streamlit.app |
| **n8n Workflows** | https://app.n8n.cloud/workflow/... |
| **Grafana** | https://yourorg.grafana.net |
| **Railway Dashboard** | https://railway.app/project/... |

---

## 💰 Monthly Cost Breakdown

| Service | Plan | Cost |
|---------|------|------|
| Railway | Pay-as-you-go | $20 |
| Upstash Redis | Free tier | $0 → $15 (if exceeds free) |
| n8n Cloud | Pro | $50 |
| Streamlit Cloud | Free | $0 |
| Supabase | Pro | $25 |
| Grafana Cloud | Free | $0 |
| **Total** | | **$95-110/month** |

**vs AWS Stack**: $335/month
**Savings**: $225-240/month = **$2,700-2,880/year**

---

## 🔧 Common Issues & Fixes

### **Issue 1: Railway deployment fails**
**Solution**:
```bash
# Check logs
railway logs

# Common fix: restart deployment
railway up --detach
```

### **Issue 2: Models not loading**
**Solution**:
```bash
# Verify models exist in Supabase Storage
# Go to: Supabase → Storage → ml-models → production/
# Should see: nba_model_v1.0.joblib and nba_model_v1.0_metadata.json

# If missing, re-upload:
python3 backend/scripts/upload_models_to_supabase.py
```

### **Issue 3: Dashboard not connecting to API**
**Solution**:
- Check Streamlit secrets have correct `ml_api_base_url`
- Verify Railway app is running: `railway status`
- Test API directly: `curl https://your-url.up.railway.app/api/v1/ml/health`

### **Issue 4: n8n workflows failing**
**Solution**:
- Check credentials are configured correctly
- Verify ML API URL is updated in all workflow nodes
- Test credentials: click "Test" button in n8n credential modal

---

## 🚀 Next Steps

### **Immediate (Today)**:
- [ ] Set up custom domain (optional)
- [ ] Configure email alerts in Grafana
- [ ] Add team members to Railway/Vercel

### **This Week**:
- [ ] Build advanced analytics dashboard (Day 3)
- [ ] Implement A/B testing framework (Day 4)
- [ ] Create revenue forecasting model (Day 5)

### **This Month**:
- [ ] Optimize model performance
- [ ] Add more ML features
- [ ] Scale to production traffic

---

## 📚 Documentation Links

- **Railway Docs**: https://docs.railway.app/
- **Vercel Docs**: https://vercel.com/docs
- **Streamlit Docs**: https://docs.streamlit.io/
- **n8n Docs**: https://docs.n8n.io/
- **Upstash Docs**: https://docs.upstash.com/
- **Grafana Docs**: https://grafana.com/docs/

---

## 🆘 Get Help

**Stuck? Need help?**

1. **Check logs**:
   - Railway: `railway logs`
   - Streamlit: View in dashboard → Manage app → Logs
   - n8n: Workflow → Executions

2. **Community Support**:
   - Railway Discord: https://discord.gg/railway
   - Streamlit Forum: https://discuss.streamlit.io/
   - n8n Forum: https://community.n8n.io/

3. **Documentation**:
   - Full deployment plan: `docs/phase4/VERCEL_DEPLOYMENT_PLAN.md`
   - AWS alternative: `docs/phase4/PRODUCTION_DEPLOYMENT_RUNBOOK.md`

---

## ✅ Deployment Complete!

**Congratulations!** 🎉

You've successfully deployed a production-ready ML system with:
- ✅ FastAPI ML API on Railway
- ✅ Interactive Streamlit dashboard
- ✅ 5 automated workflows on n8n Cloud
- ✅ Redis caching with Upstash
- ✅ Comprehensive monitoring with Grafana

**Total deployment time**: 30 minutes
**Total monthly cost**: $95-110 (vs $335 on AWS)
**Annual savings**: $2,700+

Your ML system is now serving predictions at:
🚀 **https://iswitch-ml-api.up.railway.app**

---

**Last Updated**: October 11, 2025
**Version**: 1.0.0 (Vercel Stack)
**Next Review**: Day 3 (Advanced Analytics)
