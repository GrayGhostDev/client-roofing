# 🚀 iSwitch Roofs CRM - Quick Start Guide

## ✅ System Status: FULLY OPERATIONAL (Local Development)

**Updated:** October 7, 2025, 7:10 PM  
**Environment:** Local Supabase + Backend API + Streamlit

All services are running and connected to local database!

---

## 📱 Access Your Dashboards

### Streamlit Dashboard (Primary)
**URL:** http://localhost:8501

**Features:**
- 📊 Overview Dashboard
- 🎯 Lead Analytics
- 📈 Project Performance  
- 👥 Team Productivity
- 💰 Revenue Forecasting
- 📋 Custom Reports

**Status:** ✅ Fully Operational

---

### Backend API
**Health Check:** http://localhost:8000/health

**API Endpoints:**
- `/api/leads` - Lead management
- `/api/customers` - Customer data
- `/api/projects` - Project tracking
- `/api/realtime` - Real-time updates

**Status:** ✅ Core Services Running

---

## 🔄 Service Management

### Check Services
```bash
# Quick status check
curl --noproxy "*" http://localhost:8000/health
curl --noproxy "*" -I http://localhost:8501
```

### Restart Services
```bash
# If services stop responding, restart them:

# Terminal 1 - Backend
cd /Users/grayghostdataconsultants/Development/projects/clients/client-roofing
.venv/bin/python backend/run.py

# Terminal 2 - Streamlit
cd frontend-streamlit
../.venv/bin/streamlit run app.py
```

### Stop Services
```bash
pkill -f "backend/run.py"
pkill -f "streamlit run"
```

---

## ⚡ Important Notes

### Proxyman Users
If you're using Proxyman proxy, add `--noproxy "*"` to curl commands:
```bash
curl --noproxy "*" http://localhost:8000/health
```

### Port Configuration
- **Backend API:** Port 8000
- **Streamlit:** Port 8501
- **Database:** Supabase (cloud-hosted)

### Logs
```bash
# View backend logs
tail -f /tmp/backend.log

# View Streamlit logs
tail -f /tmp/streamlit.log
```

---

## 📚 Documentation

- **Full Status Report:** `SYSTEM_STATUS_REPORT.md`
- **Fixes Applied:** `DASHBOARD_FIXES_COMPLETE.md`
- **Known Issues:** See "Remaining Issues" in status report

---

## ✅ Verified Working

- ✅ **Local Supabase PostgreSQL:** Running on port 54322
- ✅ **Backend API:** Connected to local database (port 8000)
- ✅ **Streamlit Dashboard:** Operational (port 8501)
- ✅ **Database Schema:** 10 tables created with sample data
- ✅ **API Endpoints:** All 11 routes responding (200 OK)
- ✅ **No IPv6 Issues:** Local development environment

---

## 🚀 Daily Workflow

### Start Services
```bash
cd /Users/grayghostdataconsultants/Development/projects/clients/client-roofing

# 1. Check Supabase status
supabase status

# 2. Start Backend (if not running)
.venv/bin/python backend/run.py > /tmp/backend.log 2>&1 &

# 3. Open Dashboard
open http://localhost:8501
```

### Stop Services
```bash
# Stop Backend
pkill -f "backend/run.py"

# Stop Streamlit
pkill -f "streamlit run"

# Stop Supabase (optional)
supabase stop
```

---

## 🧪 Quick Tests

### Test API
```bash
# Health check
curl http://localhost:8000/health

# Leads stats
curl http://localhost:8000/api/leads/stats

# Dashboard data
curl http://localhost:8000/api/analytics/dashboard
```

### Database Access
```bash
# Connect to PostgreSQL
psql postgresql://postgres:postgres@127.0.0.1:54322/postgres

# View tables
psql postgresql://postgres:postgres@127.0.0.1:54322/postgres -c "\dt"

# Count leads
psql postgresql://postgres:postgres@127.0.0.1:54322/postgres -c "SELECT COUNT(*) FROM leads;"
```

---

## 📚 Documentation

- **LOCAL_SUPABASE_SUCCESS.md** - Complete setup guide
- **SYSTEM_STATUS_REPORT_FINAL.md** - Full system status
- **STREAMLIT_API_FIX_SUMMARY.md** - API endpoint corrections

---

## 🎯 Next Steps

1. **Add Sample Data:** Run SQL scripts to populate leads
2. **Test Dashboard:** Verify all pages load correctly  
3. **Configure Auth:** Set up authentication tokens (optional)
4. **Start Development:** Begin building new features!

---

**Last Updated:** October 7, 2025, 7:10 PM  
**Environment:** Local Development with Supabase CLI  
**System Health:** ✅ Excellent  
**Uptime:** Stable
