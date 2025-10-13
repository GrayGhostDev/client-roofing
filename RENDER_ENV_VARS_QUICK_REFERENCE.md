# Render Environment Variables - Quick Copy/Paste Reference

## 🚀 Essential Variables (Copy these to Render)

### Database (Get from Supabase Dashboard)
```
DATABASE_URL = [Your Supabase PostgreSQL URL]
SUPABASE_URL = [Your Supabase Project URL]
SUPABASE_KEY = [Your Supabase Anon Key]
SUPABASE_SERVICE_ROLE_KEY = [Your Supabase Service Role Key]
```

**Where to find these:**
1. Go to: https://supabase.com/dashboard/
2. Select your project
3. Settings → API → Copy the values

### Security (Generate New Values)
```bash
# Run these commands in terminal to generate:
openssl rand -hex 32  # Use for SECRET_KEY
openssl rand -hex 32  # Use for JWT_SECRET_KEY (different value)
```

```
SECRET_KEY = [Output from first command]
JWT_SECRET_KEY = [Output from second command]
```

### Environment Settings (Copy as-is)
```
FLASK_ENV = production
ENVIRONMENT = production
DEBUG = false
FLASK_DEBUG = 0
JWT_ALGORITHM = HS256
JWT_ACCESS_TOKEN_EXPIRES = 3600
SKIP_AUTH = true
ENABLE_LEAD_SCORING = true
```

### CORS (Copy as-is)
```
BACKEND_CORS_ORIGINS = https://iswitchroofs.streamlit.app,http://localhost:8501
CORS_SUPPORTS_CREDENTIALS = true
```

---

## 📋 Streamlit Cloud Secrets (After Render Deployment)

Once your Render service is live, update Streamlit secrets:

1. Get your Render URL (will be something like: `https://iswitch-roofs-api.onrender.com`)
2. Go to: https://share.streamlit.io/
3. Your app → Settings → Secrets
4. Paste this (replace YOUR-RENDER-URL):

```toml
[default]
api_base_url = "YOUR-RENDER-URL"
ml_api_base_url = "YOUR-RENDER-URL"

pusher_app_id = "1890740"
pusher_key = "fe32b6bb02f0c1a41bb4"
pusher_secret = "e2b7e61a1b6c1aca04b0"
pusher_cluster = "us2"
```

---

## ✅ Checklist

Before deploying to Render, make sure you have:

- [ ] Supabase project created and running
- [ ] Supabase DATABASE_URL copied
- [ ] Supabase SUPABASE_URL copied
- [ ] Supabase SUPABASE_KEY copied
- [ ] Supabase SERVICE_ROLE_KEY copied
- [ ] Generated new SECRET_KEY
- [ ] Generated new JWT_SECRET_KEY
- [ ] Render.com account created
- [ ] GitHub repository accessible to Render

After deployment:
- [ ] Render service shows "Live" status
- [ ] Health endpoint returns 200: `https://YOUR-URL/health`
- [ ] Streamlit secrets updated with Render URL
- [ ] Streamlit app loads without errors

---

## 🔗 Quick Links

- **Render Dashboard**: https://dashboard.render.com/
- **Streamlit Dashboard**: https://share.streamlit.io/
- **Supabase Dashboard**: https://supabase.com/dashboard/
- **Your GitHub Repo**: https://github.com/GrayGhostDev/client-roofing

---

*Save this file for easy reference during deployment!*
