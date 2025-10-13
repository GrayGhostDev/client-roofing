# iSwitch Roofs CRM - Quick Start Guide

**System Status:** ✅ RUNNING
**Last Updated:** 2025-10-12

---

## 🚀 1-Minute Quick Start

### System is Already Running!

**Dashboard:** http://localhost:8501
**API:** http://localhost:8001

### Generate Leads Now (30 seconds)

1. Open: http://localhost:8501
2. Click: "🎯 Live Data Generator" (in sidebar)
3. Click: "🚀 Generate Leads" button
4. Done! View leads in "Leads Management"

---

## 📊 Current System Stats

- **Total Leads:** 125
- **HOT Leads:** 34 (ready for immediate contact)
- **Pipeline Value:** $1.75M - $2.6M
- **Average Score:** 66.54/100

---

## 🌐 Quick Access Links

### Dashboard Pages
- **Home:** http://localhost:8501
- **Leads:** http://localhost:8501/1_Leads_Management
- **Live Data:** http://localhost:8501/16_🎯_Live_Data_Generator
- **Analytics:** http://localhost:8501/10_📊_Advanced_Analytics

### API Endpoints
- **Stats:** http://localhost:8001/api/live-data/stats
- **Health:** http://localhost:8001/api/live-data/health

---

## ⚡ Quick Commands

### Generate 50 Leads (Command Line)
```bash
curl -X POST http://localhost:8001/api/live-data/generate \
  -H "Content-Type: application/json" \
  -d '{"count": 50}'
```

### Get Statistics
```bash
curl http://localhost:8001/api/live-data/stats | python3 -m json.tool
```

### Restart System
```bash
# Backend
lsof -ti:8001 | xargs kill -9
cd backend && python3 run.py &

# Frontend
lsof -ti:8501 | xargs kill -9
cd frontend-streamlit && streamlit run Home.py &
```

---

## 📚 Full Documentation

- **Setup Guide:** [REAL_DATA_SETUP_GUIDE.md](REAL_DATA_SETUP_GUIDE.md)
- **Technical Docs:** [REAL_DATA_IMPLEMENTATION_COMPLETE.md](REAL_DATA_IMPLEMENTATION_COMPLETE.md)
- **Full Report:** [SYSTEM_RUNNING_FINAL_REPORT.md](SYSTEM_RUNNING_FINAL_REPORT.md)

---

## 🎯 Priority Actions

### For Sales Team
1. Open Leads Management
2. Filter: Temperature = HOT
3. Export top 34 leads
4. Begin immediate follow-up (2-minute rule)

### For Management
1. Review Advanced Analytics dashboard
2. Check revenue forecast
3. Monitor conversion funnel
4. Review pipeline value

### For Tech Team
1. Add API keys for more data sources
2. Set up automated daily pipeline
3. Monitor system logs
4. Enable additional cities

---

## 💡 Tips

- **Best Time to Generate Leads:** After storms or market updates
- **Follow-up Priority:** HOT > WARM > COOL > COLD
- **Response Time Target:** <2 minutes for HOT leads
- **Pipeline Review:** Daily for HOT, weekly for WARM

---

**Questions?** Check [SYSTEM_RUNNING_FINAL_REPORT.md](SYSTEM_RUNNING_FINAL_REPORT.md) for complete details.

✅ **System Ready - Start Generating Revenue!**
