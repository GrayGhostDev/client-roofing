# 🚀 iSwitch Roofs Real Data - Quick Reference Card

**Keep this handy for daily operations**

---

## 📍 Access URLs

```
Backend API:  http://localhost:8001
Frontend:     http://localhost:8501
Database:     postgresql://localhost:5432/iswitch_roofs
Redis:        redis://localhost:6379/0
```

---

## 🎯 Quick Start Commands

### Start Services
```bash
# Backend
cd backend && python3 run.py

# Frontend
cd frontend-streamlit && streamlit run Home.py
```

### Check Status
```bash
# Setup checker
bash backend/scripts/setup_real_data.sh

# API tester
python3 backend/scripts/test_real_apis.py

# Health check
curl http://localhost:8001/api/live-data/health
```

### Generate Leads
```bash
# Via API (50 leads)
curl -X POST http://localhost:8001/api/live-data/generate \
  -H "Content-Type: application/json" \
  -d '{"count": 50}'

# Via script
python3 backend/scripts/generate_sample_data.py

# Via dashboard
# Go to: http://localhost:8501/16_🎯_Live_Data_Generator
```

---

## 🔧 API Keys Configuration

### Edit File
```bash
nano backend/.env
```

### Required Keys
```bash
# Priority 1 (FREE, start here)
NOAA_API_TOKEN=your-token-here

# Priority 2 (FREE, recommended)
ZILLOW_API_KEY=your-key-here
TWITTER_BEARER_TOKEN=your-token-here
GOOGLE_MAPS_API_KEY=your-key-here
```

### Registration URLs
```
NOAA:          https://www.ncdc.noaa.gov/cdo-web/token
Zillow:        https://www.zillow.com/howto/api/APIOverview.htm
Twitter:       https://developer.twitter.com/
Google Maps:   https://console.cloud.google.com/
```

---

## 📊 Expected Results by Configuration

### Level 1: NOAA Only (30 min setup)
- **Leads/month**: 200-300
- **Revenue**: $750K-$1.5M/month
- **Cost**: FREE

### Level 2: All FREE APIs (2 hour setup)
- **Leads/month**: 800-1,200
- **Revenue**: $2.4M-$4.8M/month
- **Cost**: FREE

### Level 3: Premium Sources (1 week setup)
- **Leads/month**: 1,000-1,500
- **Revenue**: $6M-$11.3M/month
- **Cost**: $100-600/month

---

## 🔍 Verify Real Data is Working

### Check 1: Lead Sources
```bash
curl http://localhost:8001/api/live-data/stats | jq '.source_distribution'
```

**Real Data Shows**: "Weather.gov Alert", "NOAA Storm DB", "Zillow API"
**Sample Data Shows**: "Sample Generator"

### Check 2: Recent Leads
```bash
psql -d iswitch_roofs -c \
  "SELECT name, city, lead_score, temperature, source
   FROM leads
   ORDER BY created_at DESC
   LIMIT 10;"
```

**Real Data**: Recent timestamps, varied scores, real sources
**Sample Data**: Evenly distributed, scores in multiples of 5

### Check 3: Temperature Distribution
Open: http://localhost:8501/16_🎯_Live_Data_Generator → Statistics tab

**Real Data**: ~15% HOT, ~35% WARM, ~35% COOL, ~15% COLD
**Sample Data**: ~25% each (too uniform)

---

## 🚨 Common Issues & Quick Fixes

### Issue: SSL Certificate Errors
```bash
# Fix (macOS)
cd /Applications/Python\ 3.*/
sudo ./Install\ Certificates.command
```

### Issue: "No API Key" Errors
```bash
# Check .env file
grep "API" backend/.env

# Restart backend after changes
cd backend && python3 run.py
```

### Issue: Port Already in Use
```bash
# Find process on port 8001
lsof -i :8001

# Kill process (replace PID)
kill -9 PID
```

### Issue: Database Connection Failed
```bash
# Check PostgreSQL is running
psql -d iswitch_roofs -c "SELECT 1;"

# Check connection string
grep "DATABASE_URL" backend/.env
```

---

## 📈 Lead Scoring Quick Reference

### Score Components (100 points total)
- **Roof Age** (0-25): 20+ years = 25 points
- **Storm Damage** (0-25): Recent storm = 25 points
- **Financial** (0-20): $500K+ home = 20 points
- **Urgency** (0-15): Active leak = 15 points
- **Intent** (0-15): Searching for quotes = 15 points

### Temperature Classification
- **HOT** (80-100): Call within 24 hours
- **WARM** (60-79): Follow up within 3 days
- **COOL** (40-59): Regular nurture sequence
- **COLD** (0-39): Long-term cultivation

---

## 🎯 Daily Operations Checklist

### Morning (5 minutes)
- [ ] Check backend is running
- [ ] Check dashboard loads
- [ ] Review overnight lead generation
- [ ] Check API quota usage

### Throughout Day (as needed)
- [ ] Generate new leads (100-200)
- [ ] Export leads to CRM
- [ ] Monitor conversion rates
- [ ] Respond to urgent (HOT) leads

### Evening (5 minutes)
- [ ] Review daily statistics
- [ ] Check data quality metrics
- [ ] Plan next day's targets
- [ ] Backup database (optional)

---

## 📊 Key Metrics Dashboard

### Access
http://localhost:8501/16_🎯_Live_Data_Generator → Statistics Tab

### Watch These Numbers
- **Total Leads**: Should grow 50-300/day
- **Avg Lead Score**: Target 65-75
- **HOT Leads %**: Target 15-25%
- **Source Distribution**: Should show multiple sources
- **Conversion Rate**: Target 15-25%

---

## 🛠️ Database Quick Commands

### Check Lead Count
```sql
SELECT COUNT(*) FROM leads;
```

### View Recent HOT Leads
```sql
SELECT id, name, phone, city, lead_score, temperature
FROM leads
WHERE lead_score >= 80
ORDER BY created_at DESC
LIMIT 20;
```

### Source Distribution
```sql
SELECT source, COUNT(*) as count
FROM leads
GROUP BY source
ORDER BY count DESC;
```

### Today's Leads
```sql
SELECT COUNT(*) as today_count
FROM leads
WHERE created_at >= CURRENT_DATE;
```

### Average Lead Score by City
```sql
SELECT city,
       COUNT(*) as leads,
       ROUND(AVG(lead_score), 1) as avg_score
FROM leads
GROUP BY city
ORDER BY avg_score DESC;
```

---

## 📞 Support Resources

### Documentation Files
- **Quick Start**: `REAL_DATA_QUICK_START.md`
- **Complete Guide**: `REAL_DATA_TRANSITION_GUIDE.md`
- **Setup Guide**: `REAL_DATA_SETUP_GUIDE.md`
- **This Card**: `QUICK_REFERENCE_CARD.md`

### Scripts
- **Setup Check**: `bash backend/scripts/setup_real_data.sh`
- **API Test**: `python3 backend/scripts/test_real_apis.py`
- **Generate**: `python3 backend/scripts/generate_sample_data.py`

### API Documentation
- **Weather.gov**: weather.gov/documentation/services-web-api
- **NOAA**: ncdc.noaa.gov/cdo-web/webservices/v2
- **Zillow**: zillow.com/howto/api/APIOverview.htm

---

## 💡 Pro Tips

### Maximize Lead Quality
1. Focus on HOT (80-100) leads first
2. Call within 24 hours of generation
3. Reference the specific storm event in pitch
4. Offer free roof inspection
5. Mention insurance claim assistance

### Optimize Data Collection
1. Run generation during business hours
2. Generate smaller batches (50-100) frequently
3. Monitor API quota usage
4. Set up automated daily refresh
5. A/B test different lead sources

### Improve Conversion Rates
1. Track which sources convert best
2. Tune lead scoring weights
3. Adjust temperature thresholds
4. Create source-specific scripts
5. Train sales team on lead context

---

## 🎯 Performance Targets

### Daily Goals
- **Leads Generated**: 50-200
- **HOT Leads**: 10-50
- **Contacts Made**: 30-100
- **Appointments Set**: 5-20
- **Quotes Sent**: 3-10

### Monthly Goals
- **Total Leads**: 1,000-5,000
- **Conversion Rate**: 15-25%
- **Closed Deals**: 150-1,250
- **Revenue**: $3.75M-$37.5M
- **Cost per Lead**: <$10

### Quality Metrics
- **Avg Lead Score**: 65-75
- **Valid Phone %**: >90%
- **Valid Address %**: >95%
- **Duplicate Rate**: <5%
- **Customer Satisfaction**: NPS 75+

---

## 🚀 Scaling Checklist

### Week 1-2: Validation
- [ ] Verify all APIs working
- [ ] Confirm lead quality
- [ ] Track initial conversions
- [ ] Gather sales team feedback
- [ ] Tune scoring algorithm

### Week 3-4: Automation
- [ ] Deploy APScheduler
- [ ] Setup alert notifications
- [ ] Implement Redis caching
- [ ] Create monitoring dashboard
- [ ] Schedule daily reports

### Month 2: Optimization
- [ ] ML-based scoring
- [ ] Predictive models
- [ ] A/B testing
- [ ] CRM integration
- [ ] Geographic expansion

---

## ✅ Success Indicators

**You're doing it right when you see:**
- ✅ Multiple data sources contributing
- ✅ Natural score distribution (bell curve)
- ✅ 15-25% conversion rate
- ✅ Sales team praising lead quality
- ✅ Consistent daily lead flow
- ✅ API costs under control
- ✅ Database growing steadily
- ✅ ROI exceeding projections

---

## 🎉 Quick Wins

### Get Your First Real Lead (10 minutes)
1. Register for NOAA token
2. Add to `.env` file
3. Generate 10 leads
4. Call the HOT ones!

### Double Your Lead Volume (30 minutes)
1. Add Zillow API key
2. Add Google Maps key
3. Generate 50 leads
4. Compare quality

### Triple Your Conversion (1 hour)
1. Export HOT leads only
2. Call within 24 hours
3. Mention storm damage
4. Track results

---

*Print this card and keep it at your desk!*
*Last Updated: 2025-10-12*
