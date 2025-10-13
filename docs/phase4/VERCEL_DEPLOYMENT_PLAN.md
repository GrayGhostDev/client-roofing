# Vercel & Modern Serverless Deployment Plan

**iSwitch Roofs CRM - Phase 4 ML System**

**Deployment Stack**: Vercel + Railway + Upstash + n8n Cloud
**Version**: 1.0.0
**Last Updated**: October 11, 2025

---

## 🎯 Architecture Overview

### **Modern Serverless Stack**

```
┌─────────────────────────────────────────────────────────────┐
│                    USER TRAFFIC                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              VERCEL EDGE NETWORK                             │
│  - Global CDN (300+ locations)                               │
│  - Edge Functions (Serverless compute)                       │
│  - Automatic SSL/TLS                                         │
│  - DDoS protection                                           │
└──────────────┬──────────────────────┬───────────────────────┘
               │                      │
               ↓                      ↓
┌──────────────────────┐   ┌──────────────────────┐
│  STREAMLIT DASHBOARD │   │    ML API PROXY      │
│  (Vercel Deployment) │   │  (Edge Functions)    │
│  - Static hosting    │   │  - /api/v1/ml/*      │
│  - Analytics         │   │  - Request routing   │
└──────────────────────┘   └──────────┬───────────┘
                                      │
                                      ↓
                           ┌──────────────────────┐
                           │   RAILWAY.APP        │
                           │   (ML API Backend)   │
                           │   - FastAPI app      │
                           │   - Docker container │
                           │   - Auto-scaling     │
                           │   - Health checks    │
                           └──────────┬───────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ↓                 ↓                 ↓
         ┌──────────────────┐ ┌──────────────┐ ┌──────────────┐
         │  UPSTASH REDIS   │ │  SUPABASE    │ │  OPENAI API  │
         │  (Cache)         │ │  (Database)  │ │  (GPT-5)     │
         │  - Global edge   │ │  - PostgreSQL│ │  - Enhanced  │
         │  - Low latency   │ │  - Real-time │ │    predictions│
         └──────────────────┘ └──────────────┘ └──────────────┘
                    │
                    ↓
         ┌──────────────────────┐
         │    N8N CLOUD         │
         │   (Workflows)        │
         │   - 5 automations    │
         │   - Managed hosting  │
         │   - Built-in scaling │
         └──────────────────────┘
                    │
                    ↓
         ┌──────────────────────┐
         │   GRAFANA CLOUD      │
         │   (Monitoring)       │
         │   - Metrics          │
         │   - Logs             │
         │   - Alerts           │
         └──────────────────────┘
```

---

## 🚀 Service Selection & Rationale

### **1. Vercel (Frontend & Edge Functions)**

**Why Vercel**:
- ✅ Zero-config deployments from Git
- ✅ 300+ global edge locations (faster than AWS CloudFront)
- ✅ Automatic SSL, custom domains, preview deployments
- ✅ Edge Functions for API routing (100ms global latency)
- ✅ Built-in analytics and monitoring
- ✅ Generous free tier: 100GB bandwidth, 6,000 build minutes/month

**What We'll Deploy**:
- Streamlit Dashboard (frontend)
- API proxy (Edge Functions) to route ML requests to Railway
- Static assets (models metadata, documentation)

**Pricing**:
- **Free Tier**: Hobby plan (sufficient for testing)
- **Pro Plan**: $20/month (recommended for production)
  - Unlimited bandwidth
  - Commercial usage
  - Custom domains
  - Team collaboration

---

### **2. Railway.app (ML API Backend)**

**Why Railway** (vs AWS EC2):
- ✅ Docker-native deployment (no EC2 instance management)
- ✅ Automatic scaling based on traffic
- ✅ Built-in CI/CD from GitHub
- ✅ $5 credit/month free, then pay-as-you-go
- ✅ Zero DevOps overhead
- ✅ Health checks and auto-restart
- ✅ Simple environment variable management

**What We'll Deploy**:
- FastAPI ML API (all 6 endpoints)
- ML models loaded from cloud storage
- Background workers for retraining

**Pricing**:
- **Free Tier**: $5 credit/month (starter projects)
- **Pro Plan**: Pay-as-you-go
  - ~$10-30/month for ML API (estimated)
  - 2GB RAM, 2 vCPUs per service
  - Auto-scaling up to 8GB RAM

**Alternative**: Render.com (similar pricing, same benefits)

---

### **3. Upstash Redis (Caching Layer)**

**Why Upstash** (vs AWS ElastiCache):
- ✅ Serverless Redis with global edge replication
- ✅ Pay-per-request pricing (no idle costs)
- ✅ 10,000 requests/day free tier
- ✅ REST API (works in serverless environments)
- ✅ 99.99% uptime SLA
- ✅ Automatic backups

**What We'll Cache**:
- ML predictions (1-hour TTL)
- Feature engineering results
- Model metadata

**Pricing**:
- **Free Tier**: 10,000 requests/day
- **Pro Plan**: $0.20 per 100,000 requests
  - Estimated: $10-20/month for production

**Alternative**: Redis Cloud (Aiven)

---

### **4. n8n Cloud (Workflow Automation)**

**Why n8n Cloud** (vs self-hosted):
- ✅ Fully managed, no server maintenance
- ✅ Built-in scaling and high availability
- ✅ 200+ pre-built integrations
- ✅ Workflow version control
- ✅ Team collaboration features

**What We'll Run**:
- All 5 automation workflows (retraining, scoring, drift, batch, VIP)

**Pricing**:
- **Free Tier**: 5,000 workflow executions/month
- **Starter Plan**: $20/month
  - 25,000 executions/month
  - Custom workflows
  - Webhooks
- **Pro Plan**: $50/month (recommended)
  - 100,000 executions/month
  - Priority support

**Alternative**: Zapier (more expensive), Make.com (similar pricing)

---

### **5. Supabase (Database)**

**Why Supabase** (already using):
- ✅ PostgreSQL with real-time subscriptions
- ✅ Built-in authentication and storage
- ✅ Generous free tier
- ✅ Auto-scaling
- ✅ Global CDN for static assets

**Pricing**:
- **Free Tier**: 500MB database, 2GB bandwidth
- **Pro Plan**: $25/month (recommended)
  - 8GB database
  - 50GB bandwidth
  - Daily backups

---

### **6. Grafana Cloud (Monitoring)**

**Why Grafana Cloud**:
- ✅ Free tier includes 10,000 series metrics
- ✅ 50GB logs, 50GB traces
- ✅ Pre-built dashboards
- ✅ Alerts via Slack/email/PagerDuty

**Pricing**:
- **Free Tier**: Sufficient for MVP
- **Pro Plan**: Pay-as-you-go (~$50/month)

**Alternative**: Datadog (more expensive), Better Stack (cheaper)

---

## 📊 Cost Comparison: Vercel Stack vs AWS

| Service | AWS Cost/Month | Vercel Stack Cost/Month | Savings |
|---------|----------------|-------------------------|---------|
| **Compute** | $100 (2x t3.xlarge) | $20 (Railway Pro) | -$80 |
| **CDN/Edge** | $50 (CloudFront) | $0 (included in Vercel) | -$50 |
| **Redis** | $60 (ElastiCache) | $15 (Upstash) | -$45 |
| **Load Balancer** | $20 (ALB) | $0 (Vercel routing) | -$20 |
| **Monitoring** | $30 (CloudWatch) | $0 (Grafana Free) | -$30 |
| **n8n Hosting** | $50 (EC2 + EBS) | $50 (n8n Cloud Pro) | $0 |
| **Database** | $25 (Supabase) | $25 (Supabase) | $0 |
| **Total** | **$335/month** | **$110/month** | **-$225/month (-67%)** |

**Annual Savings**: **$2,700/year** with Vercel stack!

---

## 🛠️ Step-by-Step Implementation Plan

### **Phase 1: Environment Setup (Day 1 - Morning)**

#### **Step 1.1: Create Vercel Account & Project**

1. **Sign up for Vercel**:
   ```bash
   # Visit https://vercel.com/signup
   # Connect with GitHub account
   ```

2. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   vercel login
   ```

3. **Create New Project**:
   ```bash
   cd /path/to/client-roofing
   vercel init

   # Answer prompts:
   # Project name: iswitch-roofs-ml
   # Framework: Other
   # Build command: (leave empty for now)
   # Output directory: frontend-streamlit
   ```

4. **Configure Project Settings**:
   - Go to Vercel Dashboard → Project Settings
   - **Environment Variables**:
     ```
     ML_API_BASE_URL=https://iswitch-ml-api.up.railway.app
     SUPABASE_URL=https://yourproject.supabase.co
     SUPABASE_ANON_KEY=your-anon-key
     OPENAI_API_KEY=sk-...
     ```

---

#### **Step 1.2: Set Up Railway.app for ML API**

1. **Sign up for Railway**:
   ```bash
   # Visit https://railway.app/
   # Sign in with GitHub
   ```

2. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   railway login
   ```

3. **Create New Project**:
   ```bash
   railway init
   # Project name: iswitch-ml-api
   ```

4. **Link GitHub Repository**:
   ```bash
   railway link
   # Select: client-roofing repository
   ```

5. **Create Railway Configuration** (`railway.json`):
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "DOCKERFILE",
       "dockerfilePath": "backend/Dockerfile.ml"
     },
     "deploy": {
       "startCommand": "uvicorn main_ml:app --host 0.0.0.0 --port $PORT",
       "healthcheckPath": "/api/v1/ml/health",
       "healthcheckTimeout": 100,
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

6. **Set Environment Variables in Railway**:
   ```bash
   railway variables set ENVIRONMENT=production
   railway variables set SUPABASE_URL=https://yourproject.supabase.co
   railway variables set SUPABASE_KEY=your-service-key
   railway variables set OPENAI_API_KEY=sk-...
   railway variables set REDIS_URL=redis://default:password@url.upstash.io:6379
   ```

---

#### **Step 1.3: Configure Upstash Redis**

1. **Sign up for Upstash**:
   ```bash
   # Visit https://upstash.com/
   # Sign up with GitHub
   ```

2. **Create Redis Database**:
   - Click "Create Database"
   - Name: `iswitch-ml-cache`
   - Type: **Global** (multi-region replication)
   - Region: **US-EAST-1** (primary)
   - Enable: **TLS**

3. **Get Connection Details**:
   ```bash
   # From Upstash Dashboard → Database → Details
   UPSTASH_REDIS_REST_URL=https://your-db.upstash.io
   UPSTASH_REDIS_REST_TOKEN=your-token

   # Or use Redis protocol
   REDIS_URL=redis://default:password@url.upstash.io:6379
   ```

4. **Test Connection**:
   ```bash
   curl -X POST $UPSTASH_REDIS_REST_URL/set/test-key/hello \
     -H "Authorization: Bearer $UPSTASH_REDIS_REST_TOKEN"

   curl $UPSTASH_REDIS_REST_URL/get/test-key \
     -H "Authorization: Bearer $UPSTASH_REDIS_REST_TOKEN"
   ```

---

#### **Step 1.4: Set Up n8n Cloud**

1. **Sign up for n8n Cloud**:
   ```bash
   # Visit https://n8n.io/cloud
   # Create account
   ```

2. **Create New Instance**:
   - Instance name: `iswitch-ml-workflows`
   - Region: **US-EAST**
   - Plan: **Pro** ($50/month for 100K executions)

3. **Import Workflows**:
   - Go to n8n Cloud Dashboard → Workflows
   - Click "Import from File"
   - Upload all 5 workflow JSON files:
     - `01_automated_daily_retraining.json`
     - `02_realtime_lead_scoring.json`
     - `03_model_drift_detection.json`
     - `04_batch_prediction_pipeline.json`
     - `05_gpt_enhancement_queue.json`

4. **Configure Credentials**:
   - **PostgreSQL** (Supabase):
     - Host: `db.yourproject.supabase.co`
     - Database: `postgres`
     - User: `postgres`
     - Password: `your-password`
     - SSL: `require`

   - **OpenAI**:
     - API Key: `sk-...`

   - **Slack OAuth**:
     - Follow n8n OAuth flow
     - Authorize workspace

   - **HTTP Request** (ML API):
     - Base URL: `https://iswitch-ml-api.up.railway.app`

5. **Update Workflow URLs**:
   - In each workflow, replace:
     ```
     http://localhost:8000 → https://iswitch-ml-api.up.railway.app
     ```

6. **Activate Workflows**:
   - Toggle "Active" for each workflow
   - Test with "Execute Workflow" button

---

### **Phase 2: Application Deployment (Day 1 - Afternoon)**

#### **Step 2.1: Prepare ML API for Railway**

1. **Create Production Dockerfile** (`backend/Dockerfile.ml`):
   ```dockerfile
   FROM python:3.11-slim

   # Set working directory
   WORKDIR /app

   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       curl \
       && rm -rf /var/lib/apt/lists/*

   # Copy requirements
   COPY requirements.txt .

   # Install Python dependencies
   RUN pip install --no-cache-dir -r requirements.txt

   # Copy application code
   COPY app/ ./app/
   COPY main_ml.py .

   # Create models directory
   RUN mkdir -p /app/models

   # Download models from Supabase Storage at startup
   COPY scripts/download_models.py .

   # Expose port (Railway will set PORT env var)
   ENV PORT=8000
   EXPOSE $PORT

   # Health check
   HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
     CMD curl -f http://localhost:$PORT/api/v1/ml/health || exit 1

   # Start application
   CMD python download_models.py && \
       uvicorn main_ml:app --host 0.0.0.0 --port $PORT --workers 2
   ```

2. **Create Model Download Script** (`backend/scripts/download_models.py`):
   ```python
   import os
   import boto3
   from supabase import create_client

   # Download models from Supabase Storage
   supabase = create_client(
       os.getenv('SUPABASE_URL'),
       os.getenv('SUPABASE_KEY')
   )

   # Download NBA model
   model_data = supabase.storage.from_('ml-models').download('production/nba_model_v1.0.joblib')
   with open('/app/models/nba_model_v1.0.joblib', 'wb') as f:
       f.write(model_data)

   # Download metadata
   metadata = supabase.storage.from_('ml-models').download('production/nba_model_v1.0_metadata.json')
   with open('/app/models/nba_model_v1.0_metadata.json', 'wb') as f:
       f.write(metadata)

   print("✅ Models downloaded successfully")
   ```

3. **Update ML API for Serverless** (`backend/main_ml.py`):
   ```python
   import os
   from fastapi import FastAPI
   from fastapi.middleware.cors import CORSMiddleware
   from app.routes.ml_predictions import router as ml_router

   # Get port from environment (Railway sets this)
   PORT = int(os.getenv('PORT', 8000))

   app = FastAPI(
       title="iSwitch Roofs ML API",
       description="Machine Learning prediction endpoints for CRM",
       version="1.0.0",
       docs_url="/api/docs",  # Swagger UI
       redoc_url="/api/redoc"  # ReDoc
   )

   # CORS for Vercel frontend
   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "https://*.vercel.app",
           "https://dashboard.iswitch-roofs.com",
           "http://localhost:8501"
       ],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )

   # Health check (Railway uses this)
   @app.get("/health")
   async def health_check():
       return {"status": "healthy"}

   # Include ML routes
   app.include_router(ml_router)

   if __name__ == "__main__":
       import uvicorn
       uvicorn.run(app, host="0.0.0.0", port=PORT)
   ```

4. **Deploy to Railway**:
   ```bash
   cd backend
   railway up

   # Railway will:
   # 1. Build Docker image
   # 2. Deploy to cloud
   # 3. Assign public URL: https://iswitch-ml-api.up.railway.app
   # 4. Set up health checks
   # 5. Enable auto-restart on failure
   ```

5. **Verify Deployment**:
   ```bash
   # Check health
   curl https://iswitch-ml-api.up.railway.app/api/v1/ml/health

   # Check metrics
   curl https://iswitch-ml-api.up.railway.app/api/v1/ml/metrics

   # Test prediction
   curl -X POST https://iswitch-ml-api.up.railway.app/api/v1/ml/predict/nba \
     -H "Content-Type: application/json" \
     -d '{
       "lead_id": "test-001",
       "source": "website",
       "created_at": "2025-10-11T10:00:00",
       "property_zip": "48304",
       "estimated_value": 850000
     }'
   ```

---

#### **Step 2.2: Deploy Streamlit Dashboard to Vercel**

**Option A: Direct Streamlit Hosting** (Recommended)

1. **Use Streamlit Cloud** (Free):
   ```bash
   # Visit https://streamlit.io/cloud
   # Sign in with GitHub
   # Deploy from repository: client-roofing
   # Branch: main
   # Main file: frontend-streamlit/Home.py
   ```

2. **Configure Streamlit Secrets** (in Streamlit Cloud dashboard):
   ```toml
   [default]
   ml_api_base_url = "https://iswitch-ml-api.up.railway.app"
   supabase_url = "https://yourproject.supabase.co"
   supabase_key = "your-anon-key"
   ```

3. **Access Dashboard**:
   ```
   https://iswitch-roofs-ml.streamlit.app
   ```

**Option B: Convert to Next.js for Vercel** (Advanced)

1. **Create Next.js Wrapper** (`frontend-nextjs/pages/dashboard.tsx`):
   ```typescript
   import { useEffect, useRef } from 'react';

   export default function Dashboard() {
     const iframeRef = useRef(null);

     return (
       <div style={{ width: '100vw', height: '100vh' }}>
         <iframe
           ref={iframeRef}
           src={process.env.NEXT_PUBLIC_STREAMLIT_URL}
           style={{ width: '100%', height: '100%', border: 'none' }}
         />
       </div>
     );
   }
   ```

2. **Deploy Next.js to Vercel**:
   ```bash
   cd frontend-nextjs
   vercel --prod
   ```

---

#### **Step 2.3: Create Vercel Edge Functions (API Proxy)**

**Purpose**: Route ML API requests through Vercel Edge for better performance

1. **Create Edge Function** (`api/ml-proxy.ts`):
   ```typescript
   import type { VercelRequest, VercelResponse } from '@vercel/node';

   export const config = {
     runtime: 'edge',
   };

   export default async function handler(req: VercelRequest) {
     const url = new URL(req.url!);
     const path = url.pathname.replace('/api/ml-proxy', '');

     // Forward request to Railway ML API
     const mlApiUrl = `${process.env.ML_API_BASE_URL}${path}${url.search}`;

     const response = await fetch(mlApiUrl, {
       method: req.method,
       headers: {
         'Content-Type': 'application/json',
         'User-Agent': 'Vercel-Edge-Function',
       },
       body: req.method !== 'GET' ? await req.text() : undefined,
     });

     const data = await response.json();

     return new Response(JSON.stringify(data), {
       status: response.status,
       headers: {
         'Content-Type': 'application/json',
         'Cache-Control': 's-maxage=60, stale-while-revalidate',
       },
     });
   }
   ```

2. **Configure Vercel Routes** (`vercel.json`):
   ```json
   {
     "rewrites": [
       {
         "source": "/api/v1/ml/:path*",
         "destination": "https://iswitch-ml-api.up.railway.app/api/v1/ml/:path*"
       }
     ],
     "headers": [
       {
         "source": "/api/(.*)",
         "headers": [
           {
             "key": "Cache-Control",
             "value": "s-maxage=60, stale-while-revalidate"
           }
         ]
       }
     ]
   }
   ```

3. **Deploy Edge Functions**:
   ```bash
   vercel --prod
   ```

---

### **Phase 3: Monitoring Setup (Day 2)**

#### **Step 3.1: Configure Grafana Cloud**

1. **Sign up for Grafana Cloud**:
   ```bash
   # Visit https://grafana.com/auth/sign-up
   # Free tier: 10K series, 50GB logs
   ```

2. **Create Data Sources**:

   **a) Railway Metrics**:
   - Go to Connections → Data Sources → Add Prometheus
   - URL: Get from Railway dashboard → Metrics
   - Save & Test

   **b) Vercel Analytics**:
   - Install Vercel integration
   - Connect Vercel account
   - Select project: iswitch-roofs-ml

   **c) Upstash Redis**:
   - Add Prometheus data source
   - URL: Get from Upstash dashboard → Monitoring

3. **Import Dashboards**:
   ```bash
   # Download pre-built dashboards
   # 1. FastAPI Dashboard (ID: 14405)
   # 2. Redis Dashboard (ID: 11835)
   # 3. PostgreSQL Dashboard (ID: 9628)
   ```

4. **Create Custom Dashboard** (ML System):
   - **Panel 1**: API Request Rate (requests/sec)
   - **Panel 2**: API Latency (P50, P95, P99)
   - **Panel 3**: Error Rate (5xx responses)
   - **Panel 4**: Model Accuracy (from /api/v1/ml/metrics)
   - **Panel 5**: Prediction Confidence Distribution
   - **Panel 6**: Cache Hit Rate (Upstash)
   - **Panel 7**: Database Connections (Supabase)
   - **Panel 8**: n8n Workflow Executions

5. **Set Up Alerts**:
   ```yaml
   # Alert: High Error Rate
   - name: ml-api-high-error-rate
     condition: error_rate > 1%
     duration: 5m
     notify: slack, email
     message: "ML API error rate is {{ $value }}%"

   # Alert: High Latency
   - name: ml-api-high-latency
     condition: p95_latency > 500ms
     duration: 5m
     notify: slack
     message: "ML API P95 latency is {{ $value }}ms"

   # Alert: Model Accuracy Drop
   - name: model-accuracy-drop
     condition: accuracy < 75%
     duration: 10m
     notify: slack, email, pagerduty
     message: "Model accuracy dropped to {{ $value }}%"
   ```

---

#### **Step 3.2: Set Up Better Stack (Logs)**

**Alternative to Grafana Logs** (More affordable):

1. **Sign up for Better Stack**:
   ```bash
   # Visit https://betterstack.com/logs
   # Free: 1GB/month, 7-day retention
   ```

2. **Install Logtail Source**:
   ```bash
   # Create source: iswitch-ml-api
   # Get source token: <your-token>
   ```

3. **Configure Railway Logging**:
   ```bash
   # In Railway dashboard → Settings → Logging
   # Add webhook: https://in.logs.betterstack.com/<your-token>
   ```

4. **Configure n8n Logging**:
   - n8n Cloud has built-in logging
   - Export to Better Stack via webhook

5. **Create Log Queries**:
   ```
   # All errors
   level:error

   # ML prediction errors
   level:error AND message:"prediction failed"

   # Slow requests
   duration:>1000

   # 5xx errors
   status:>=500
   ```

---

### **Phase 4: CI/CD Pipeline (Day 2 - Afternoon)**

#### **Step 4.1: GitHub Actions for Railway**

Create `.github/workflows/deploy-ml-api.yml`:

```yaml
name: Deploy ML API to Railway

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'
      - '.github/workflows/deploy-ml-api.yml'
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          cd backend
          pytest tests/ --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
          fail_ci_if_error: false

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3

      - name: Install Railway CLI
        run: npm install -g @railway/cli

      - name: Deploy to Railway
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: |
          cd backend
          railway up --detach

      - name: Wait for deployment
        run: sleep 60

      - name: Run smoke tests
        env:
          ML_API_URL: ${{ secrets.ML_API_URL }}
        run: |
          # Health check
          curl -f $ML_API_URL/api/v1/ml/health

          # Metrics check
          curl -f $ML_API_URL/api/v1/ml/metrics

          # Test prediction
          curl -X POST $ML_API_URL/api/v1/ml/predict/nba \
            -H "Content-Type: application/json" \
            -d '{"lead_id":"ci-test","source":"website","created_at":"2025-10-11T10:00:00","property_zip":"48304","estimated_value":850000}'

      - name: Notify Slack
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK }}
          payload: |
            {
              "text": "ML API Deployment ${{ job.status }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "Deployment to Railway: *${{ job.status }}*\nCommit: `${{ github.sha }}`"
                  }
                }
              ]
            }
```

#### **Step 4.2: Vercel Automatic Deployments**

Vercel automatically deploys on Git push (already configured):

1. **Every Push to Main**:
   - Triggers production deployment
   - Runs build
   - Deploys to global edge
   - Updates https://dashboard.iswitch-roofs.com

2. **Every Pull Request**:
   - Creates preview deployment
   - URL: https://iswitch-roofs-ml-<pr-number>.vercel.app
   - Allows testing before merge

3. **Configure Deployment Settings** (vercel.json):
   ```json
   {
     "buildCommand": "echo 'Streamlit hosted separately'",
     "framework": null,
     "installCommand": "echo 'No install needed'",
     "devCommand": "streamlit run frontend-streamlit/Home.py",
     "env": {
       "ML_API_BASE_URL": "https://iswitch-ml-api.up.railway.app"
     }
   }
   ```

---

### **Phase 5: Model Storage (Day 3)**

#### **Step 5.1: Supabase Storage for Models**

1. **Create Storage Bucket**:
   ```sql
   -- In Supabase SQL Editor
   INSERT INTO storage.buckets (id, name, public)
   VALUES ('ml-models', 'ml-models', false);
   ```

2. **Set Access Policies**:
   ```sql
   -- Allow authenticated service to read/write
   CREATE POLICY "Service can manage models"
   ON storage.objects FOR ALL
   USING (bucket_id = 'ml-models');
   ```

3. **Upload Models**:
   ```python
   from supabase import create_client

   supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

   # Upload NBA model
   with open('models/nba_model_v1.0.joblib', 'rb') as f:
       supabase.storage.from_('ml-models').upload(
           'production/nba_model_v1.0.joblib',
           f,
           file_options={"content-type": "application/octet-stream"}
       )

   # Upload metadata
   with open('models/nba_model_v1.0_metadata.json', 'rb') as f:
       supabase.storage.from_('ml-models').upload(
           'production/nba_model_v1.0_metadata.json',
           f,
           file_options={"content-type": "application/json"}
       )
   ```

4. **Download in Railway** (startup script):
   ```python
   # In backend/scripts/download_models.py
   import os
   from supabase import create_client

   supabase = create_client(
       os.getenv('SUPABASE_URL'),
       os.getenv('SUPABASE_SERVICE_KEY')
   )

   # Download model
   model_data = supabase.storage.from_('ml-models').download('production/nba_model_v1.0.joblib')
   with open('/app/models/nba_model_v1.0.joblib', 'wb') as f:
       f.write(model_data)

   print("✅ Model loaded from Supabase Storage")
   ```

---

## 📋 Deployment Checklist

### **Pre-Deployment**

- [ ] Vercel account created and CLI installed
- [ ] Railway account created and project linked to GitHub
- [ ] Upstash Redis database created
- [ ] n8n Cloud instance provisioned
- [ ] Grafana Cloud account created
- [ ] All environment variables documented
- [ ] Supabase storage bucket created
- [ ] Models uploaded to Supabase Storage

### **Deployment**

- [ ] ML API deployed to Railway
- [ ] Health check endpoint responding
- [ ] Streamlit dashboard deployed to Streamlit Cloud
- [ ] Vercel project configured (if using Edge Functions)
- [ ] All 5 n8n workflows imported and activated
- [ ] Upstash Redis connected and tested
- [ ] Environment variables set in all services

### **Post-Deployment**

- [ ] Grafana dashboards created and displaying data
- [ ] Alerts configured in Grafana Cloud
- [ ] Better Stack logging operational
- [ ] GitHub Actions CI/CD pipeline working
- [ ] End-to-end smoke tests passed
- [ ] Custom domain configured (optional)
- [ ] SSL certificates verified
- [ ] Performance baseline established

---

## 🔒 Security Checklist

### **Environment Variables**

- [ ] Never commit `.env` files to Git
- [ ] Use Railway environment variables for secrets
- [ ] Use Vercel environment variables for frontend
- [ ] Use n8n Cloud credentials manager
- [ ] Rotate API keys every 90 days

### **API Security**

- [ ] CORS properly configured (whitelist domains)
- [ ] Rate limiting enabled (Railway has built-in)
- [ ] Input validation on all endpoints (Pydantic)
- [ ] SQL injection prevention (Supabase handles this)
- [ ] No secrets in client-side code

### **Database Security**

- [ ] Supabase RLS (Row Level Security) enabled
- [ ] Database backups automated (Supabase Pro)
- [ ] Connection pooling configured
- [ ] SSL/TLS enforced for all connections

---

## 📊 Monitoring Dashboards

### **Grafana Cloud Dashboard Layout**

**Dashboard 1: System Health**
- API uptime (Railway)
- Request rate (requests/sec)
- Error rate (%)
- P95 latency (ms)
- Active connections
- Memory usage
- CPU usage

**Dashboard 2: ML Performance**
- Model accuracy (%)
- Predictions per minute
- Confidence distribution
- Cache hit rate (Upstash)
- Feature importance changes
- Drift detection status

**Dashboard 3: Business Metrics**
- Lead conversion rate
- VIP lead conversion
- Revenue impact (daily/weekly/monthly)
- Response time distribution
- Top performing actions

**Dashboard 4: n8n Workflows**
- Workflow execution counts
- Success/failure rates
- Execution duration
- Queue depths
- Alert notification delivery

---

## 💰 Total Monthly Cost Estimate

| Service | Plan | Cost |
|---------|------|------|
| **Vercel** | Pro | $20 |
| **Railway** | Pay-as-you-go | $20 |
| **Upstash Redis** | Pay-per-request | $15 |
| **n8n Cloud** | Pro | $50 |
| **Supabase** | Pro | $25 |
| **Grafana Cloud** | Free | $0 |
| **Better Stack** | Free | $0 |
| **Streamlit Cloud** | Free | $0 |
| **Total** | | **$130/month** |

**Compared to AWS**: **$335/month**
**Savings**: **$205/month** (61% cheaper)
**Annual Savings**: **$2,460/year**

---

## 🚀 Deployment Commands Summary

```bash
# 1. Railway ML API
cd backend
railway up

# 2. Vercel (if using Edge Functions)
cd frontend-nextjs
vercel --prod

# 3. Streamlit Cloud
# Deploy via web interface: https://streamlit.io/cloud

# 4. n8n Cloud
# Import workflows via web interface

# 5. Monitor deployment
railway logs
vercel logs
# Check Grafana Cloud dashboards
```

---

## 📝 Next Steps

**Day 1**: Complete infrastructure setup
**Day 2**: Deploy all services and configure monitoring
**Day 3**: Set up CI/CD and test end-to-end
**Day 4**: Build advanced analytics features
**Day 5**: Implement A/B testing and revenue forecasting

---

**Last Updated**: October 11, 2025
**Version**: 1.0.0 (Vercel Stack)
**Author**: Phase 4 ML Implementation Team
