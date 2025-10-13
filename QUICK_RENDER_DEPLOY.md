# 🚀 Quick Render Deployment - 3 Simple Steps

You already have a Render service created!
**Service ID**: `srv-d3mlmmur433s73abuar0`

Let's configure and deploy it properly.

---

## Step 1: Re-authenticate Render CLI (30 seconds)

```bash
render login
```

This will open your browser to re-authenticate. After that, verify:

```bash
render whoami
```

---

## Step 2: Create Environment File (2 minutes)

```bash
# Copy the template
cp .env.production.template .env.production

# Edit with your Supabase credentials
nano .env.production
```

**Get your Supabase credentials:**
1. Go to: https://supabase.com/dashboard/
2. Select your project
3. Settings → Database → Copy "Connection string" (with pooling)
4. Settings → API → Copy URL, anon key, and service_role key

**Your .env.production should look like:**
```bash
DATABASE_URL=postgresql://postgres.abcdefgh:MyP@ssw0rd@aws-0-us-west-1.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://abcdefghijklmnop.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Step 3: Deploy! (One Command)

```bash
./deploy-to-render.sh
```

Or if you prefer manual control:

```bash
# Update service configuration
cd backend
render services update srv-d3mlmmur433s73abuar0 --yaml render.yaml --confirm

# Set environment variables
cd ..
render config:set --service srv-d3mlmmur433s73abuar0 --env-file .env.production --confirm

# View deployment logs
render services logs srv-d3mlmmur433s73abuar0 --tail
```

---

## ✅ After Deployment (1 minute)

### 1. Get your service URL:

```bash
render services get srv-d3mlmmur433s73abuar0 -o json | grep serviceUrl
```

Or check dashboard: https://dashboard.render.com/web/srv-d3mlmmur433s73abuar0

### 2. Test the API:

```bash
# Replace with your actual URL
curl https://YOUR-SERVICE-NAME.onrender.com/health
```

### 3. Update Streamlit Secrets:

Go to: https://share.streamlit.io/
Your app → Settings → Secrets

```toml
[default]
api_base_url = "https://YOUR-SERVICE-NAME.onrender.com"
ml_api_base_url = "https://YOUR-SERVICE-NAME.onrender.com"

pusher_app_id = "1890740"
pusher_key = "fe32b6bb02f0c1a41bb4"
pusher_secret = "e2b7e61a1b6c1aca04b0"
pusher_cluster = "us2"
```

---

## 🎉 Done!

Your backend should now be:
- ✅ Deployed on Render
- ✅ Connected to Supabase
- ✅ Auto-deploying on git push
- ✅ Ready for your Streamlit frontend

Test your full stack:
- Backend: https://YOUR-SERVICE-NAME.onrender.com/health
- Frontend: https://iswitchroofs.streamlit.app/

---

## 🔧 Troubleshooting

### If deployment fails:

```bash
# Check logs
render services logs srv-d3mlmmur433s73abuar0 --num 100

# Check environment variables are set
render config srv-d3mlmmur433s73abuar0

# Force redeploy
render services deploy srv-d3mlmmur433s73abuar0 --confirm
```

### If authentication issues:

```bash
render logout
render login
# Try again
```

---

**Need help?** Check `RENDER_CLI_DEPLOYMENT.md` for detailed troubleshooting.
