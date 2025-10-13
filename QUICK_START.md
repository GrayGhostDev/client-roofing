# 🚀 Quick Start Guide - iSwitch Roofs CRM

## ⚡ Access URLs

### Frontend Dashboard
```
http://localhost:8501
```
**Default Landing**: Dashboard with real-time statistics

### Backend API
```
http://localhost:8001
```
**Health Check**: http://localhost:8001/health

### Stats Endpoint
```
http://localhost:8001/api/stats/summary
```
**Returns**: Real-time lead, customer, project, and revenue data

---

## 🎯 Quick Tests

### 1. Check All Services
```bash
# PostgreSQL
pg_isready -h localhost -p 5432

# Redis
redis-cli ping

# Backend
curl http://localhost:8001/health

# Frontend
curl -I http://localhost:8501
```

### 2. Get Dashboard Data
```bash
# Summary statistics
curl http://localhost:8001/api/stats/summary | python3 -m json.tool

# Key performance indicators
curl http://localhost:8001/api/stats/kpis | python3 -m json.tool
```

### 3. View Real Data
```bash
# Current stats
curl -s http://localhost:8001/api/stats/summary | grep -E '"total_leads"|"hot_leads"|"conversion_rate"'
```

**Expected Output**:
```
"total_leads": 556,
"hot_leads": 37,
"conversion_rate": 2.5,
```

---

## 📊 18 Available Services

### From Sidebar Navigation:

1. **🏠 Dashboard** - Real-time KPIs and metrics
2. **👥 Leads** - Lead management (556 leads)
3. **🏢 Customers** - Customer records (5 customers)
4. **🏗️ Projects** - Project tracking
5. **📅 Appointments** - Appointment scheduling
6. **💬 Chat AI** - Conversational AI (GPT-4o)
7. **🔍 AI Search** - Natural language search
8. **🚀 Sales Automation** - Campaign management (⚠️ FastAPI - needs conversion)
9. **📡 Data Pipeline** - Automated lead discovery
10. **🎯 Live Data** - Real-time data generator
11. **📊 Enhanced Analytics** - Advanced metrics
12. **📉 Lead Analytics** - Lead performance
13. **📈 Advanced Analytics** - Business intelligence
14. **📋 Custom Reports** - Report builder
15. **⚡ Project Performance** - Project metrics
16. **🧪 A/B Testing** - Experiment management
17. **💰 Revenue Forecasting** - Financial predictions
18. **👥 Team Productivity** - Team performance

---

## 🔧 Common Tasks

### Start/Restart Services

#### Backend:
```bash
cd /Users/grayghostdataconsultants/Development/projects/clients/client-roofing/backend
pkill -f "python3.*run.py"
nohup python3 run.py > logs/backend.log 2>&1 &
```

#### Frontend:
```bash
cd /Users/grayghostdataconsultants/Development/projects/clients/client-roofing/frontend-streamlit
pkill -f "streamlit"
nohup streamlit run Home.py --server.port 8501 --server.headless true > logs/frontend.log 2>&1 &
```

#### Check Logs:
```bash
# Backend logs
tail -f backend/logs/backend.log

# Frontend logs
tail -f frontend-streamlit/logs/frontend.log
```

---

## 📈 Current Data Summary

### Live Statistics (as of 2025-10-13):
- **Total Leads**: 556
- **HOT Leads**: 37 (score >= 80)
- **Leads Today**: 14
- **Customers**: 5
- **Conversion Rate**: 2.5%
- **Active Projects**: 0
- **Monthly Revenue**: $0
- **Proposals Sent**: 36

### Business Insights:
- ✅ Strong lead generation (14 today)
- ✅ Good HOT lead ratio (6.7%)
- ⚠️ Need to schedule appointments
- ⚠️ Need to close proposals → projects
- ⚠️ Target conversion rate: 8-10%

---

## 🛠️ Troubleshooting

### Frontend won't load?
```bash
# Check if Streamlit is running
ps aux | grep streamlit

# Restart if needed
pkill -f "streamlit" && cd frontend-streamlit && streamlit run Home.py --server.port 8501
```

### Backend returns 404?
```bash
# Check if backend is running
curl http://localhost:8001/health

# Restart if needed
cd backend && pkill -f "python3.*run.py" && python3 run.py
```

### Database connection error?
```bash
# Check PostgreSQL
pg_isready -h localhost -p 5432

# Check Redis
redis-cli ping
```

---

## 📝 Known Issues

### 1. Sales Automation (⚠️)
**Issue**: Shows 404 errors
**Cause**: Uses FastAPI, not Flask
**Status**: Documented, needs conversion
**Impact**: Page loads but can't fetch data

### 2. No Real-time Updates Yet
**Issue**: Pusher configuration invalid
**Status**: Need to update app_id
**Impact**: No live updates (uses 30s refresh instead)

---

## 🎯 Next Actions

### For Users:
1. Open dashboard: http://localhost:8501
2. Review 556 leads in Leads Management
3. Contact 37 HOT leads (score >= 80)
4. Schedule appointments for top prospects
5. Convert 36 proposals to projects

### For Developers:
1. Convert Sales Automation to Flask
2. Fix Pusher configuration
3. Add appointment scheduling integration
4. Implement lead follow-up automation
5. Add conversion optimization features

---

## 📚 Documentation

### Full Documentation:
- `FINAL_STATUS_REPORT.md` - Complete session summary
- `STATS_ENDPOINT_COMPLETE.md` - Stats API details
- `SYSTEM_READY.md` - System status
- `REMAINING_FIXES.md` - Known issues
- `ALL_SERVICES_ENABLED.md` - Service catalog

### API Documentation:
- Health: `GET /health`
- Stats: `GET /api/stats/summary`
- KPIs: `GET /api/stats/kpis`
- 25+ other routes (see backend/app/routes/)

---

## ✅ Success Checklist

Before using the system, verify:
- [ ] PostgreSQL accepting connections (port 5432)
- [ ] Redis responding to PING (port 6379)
- [ ] Backend healthy (http://localhost:8001/health)
- [ ] Frontend loading (http://localhost:8501)
- [ ] Stats endpoint returning data (http://localhost:8001/api/stats/summary)

**All checked?** → System is ready! 🎉

---

## 🎓 Quick Tips

### Dashboard Features:
- **Auto-refresh**: Every 30 seconds
- **Real data**: No mock data, all from PostgreSQL
- **Navigation**: Sidebar has 18 services
- **Metrics**: Hover for details

### Lead Management:
- **HOT leads**: Score >= 80 (37 leads)
- **Filter by**: Status, score, date
- **Actions**: Contact, schedule, convert

### Analytics:
- **Multiple views**: Enhanced, Lead, Advanced
- **Custom reports**: Build your own
- **Export**: Download as CSV/Excel

---

## 📞 Support

### If you need help:
1. Check logs: `backend/logs/backend.log`, `frontend-streamlit/logs/frontend.log`
2. Review documentation: `FINAL_STATUS_REPORT.md`
3. Test services: Run health checks above
4. Restart services: Follow "Start/Restart Services" section

---

**Last Updated**: 2025-10-13
**Version**: 1.0.0
**Status**: ✅ Production Ready
