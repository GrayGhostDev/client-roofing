# Deployment Quick Start Guide

**iSwitch Roofs CRM - Production Deployment**
**Version**: 2.0.0 | **Date**: 2025-10-10

---

## ⚡ 5-Minute Production Deployment

### Prerequisites Checklist

- [ ] Docker 20.10+ installed
- [ ] Docker Compose 2.0+ installed
- [ ] `.env` files configured (backend and frontend)
- [ ] Supabase project created and credentials obtained
- [ ] Domain name configured (if using SSL)

---

## 🚀 Option 1: Full Stack Deployment (Recommended)

### Step 1: Configure Environment

```bash
# Navigate to backend
cd backend

# Create .env from example
cp .env.example .env

# Edit .env with your credentials
nano .env
# Required variables:
# - DATABASE_URL (PostgreSQL connection string)
# - SUPABASE_URL, SUPABASE_KEY
# - SECRET_KEY, JWT_SECRET_KEY
# - PUSHER_APP_ID, PUSHER_KEY, PUSHER_SECRET (optional)
```

```bash
# Navigate to frontend
cd ../frontend-streamlit

# Create .env from example
cp .env.example .env

# Edit .env
nano .env
# Required variables:
# - BACKEND_API_URL=http://backend:8000 (or your domain)
# - SUPABASE_URL, SUPABASE_KEY
# - PUSHER_APP_KEY (optional)
```

### Step 2: Deploy All Services

```bash
# From backend directory
cd backend

# Start all services with Docker Compose
docker-compose up -d

# Services starting:
# ✓ Redis (cache)
# ✓ Backend (FastAPI)
# ✓ Frontend (Streamlit)
# ✓ Nginx (optional - if configured)
# ✓ Celery Worker (optional)
# ✓ Celery Beat (optional)
```

### Step 3: Verify Deployment

```bash
# Check all services are running
docker-compose ps

# Expected output:
# NAME                    STATUS
# iswitch-crm-backend     Up (healthy)
# iswitch-crm-frontend    Up (healthy)
# iswitch-crm-redis       Up (healthy)

# Test health endpoints
curl http://localhost:8000/health
# Expected: {"status":"ok","timestamp":"..."}

curl http://localhost:8501/_stcore/health
# Expected: OK

# View logs
docker-compose logs -f frontend
```

### Step 4: Initialize Data

```bash
# Seed database with test data (optional)
docker exec iswitch-crm-backend python scripts/seed_large_leads_dataset.py --count 100

# Or connect to backend container
docker exec -it iswitch-crm-backend bash
python scripts/seed_large_leads_dataset.py --count 100
```

### Step 5: Access Application

**Frontend Dashboard**: http://localhost:8501
**Backend API**: http://localhost:8000
**API Documentation**: http://localhost:8000/docs

---

## 🎯 Option 2: Automated Deployment Scripts

### For Production

```bash
cd frontend-streamlit

# Run automated production deployment
./deploy-production.sh

# Script performs:
# ✓ Environment validation
# ✓ Backend connectivity check
# ✓ Automated backup
# ✓ Docker image build
# ✓ Service deployment
# ✓ Health checks (10 retries)
# ✓ Smoke tests
# ✓ Automatic rollback on failure

# Monitor deployment
docker logs -f iswitch-crm-frontend
```

### For Staging/Testing

```bash
cd frontend-streamlit

# Deploy to staging with debug mode
./deploy-staging.sh

# Features:
# ✓ Debug logging enabled
# ✓ Hot-reload (file changes auto-update)
# ✓ Test data loaded (50 leads)
# ✓ Development tools included
```

---

## 🔍 Verification Steps

### 1. Service Health Checks

```bash
# Check Docker containers
docker ps | grep iswitch-crm

# Check health endpoints
curl http://localhost:8501/_stcore/health  # Frontend
curl http://localhost:8000/health           # Backend

# Check logs for errors
docker logs iswitch-crm-frontend | grep -i error
docker logs iswitch-crm-backend | grep -i error
```

### 2. Database Connectivity

```bash
# Test database connection
docker exec iswitch-crm-backend python -c "
from app.database import get_db
db = next(get_db())
print('Database connected successfully')
"
```

### 3. Performance Tests

```bash
# Run performance benchmark
docker exec iswitch-crm-backend python scripts/test_performance_metrics.py

# Expected:
# - All 18 tests passing
# - Average response time: <5ms
# - No queries >100ms
```

### 4. Data Integrity

```bash
# Run integrity validation
docker exec iswitch-crm-backend python scripts/validate_leads_integrity.py

# Expected:
# - >80% pass rate
# - ENUM values: 100% (3/3)
# - No critical errors
```

### 5. Frontend Accessibility

```bash
# Test frontend loads
curl -I http://localhost:8501

# Expected: HTTP 200 OK

# Open in browser
# Navigate to: http://localhost:8501
# Expected: Dashboard loads with metrics
```

---

## 🛠️ Common Setup Issues

### Issue 1: Docker Compose Fails

```bash
# Check Docker is running
docker --version
docker ps

# Check compose file syntax
cd backend
docker-compose config

# Start with verbose output
docker-compose up
```

### Issue 2: Backend Not Starting

```bash
# Check backend logs
docker logs iswitch-crm-backend

# Common causes:
# - DATABASE_URL incorrect
# - Missing environment variables
# - Port 8000 already in use

# Fix:
# 1. Verify .env file
# 2. Check: docker-compose ps
# 3. Restart: docker-compose restart backend
```

### Issue 3: Frontend Can't Connect to Backend

```bash
# Check network
docker network inspect iswitch-network

# Verify backend URL in frontend .env
cat frontend-streamlit/.env | grep BACKEND_API_URL

# Should be:
# - Docker: BACKEND_API_URL=http://backend:8000
# - Local: BACKEND_API_URL=http://localhost:8000

# Restart frontend
docker-compose restart frontend
```

### Issue 4: Database Connection Fails

```bash
# Test Supabase connection
python -c "
from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv()
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
print('Supabase connected')
"

# Verify credentials in .env
# - SUPABASE_URL format: https://xxxxx.supabase.co
# - SUPABASE_KEY should be 'anon' key (not service_role)
```

---

## 📊 Production Checklist (Condensed)

Before deploying to production, verify:

### Critical (Must Complete)

- [ ] `.env` files configured with production credentials
- [ ] SECRET_KEY and JWT_SECRET_KEY are strong, unique values
- [ ] CORS_ORIGINS includes your production domain
- [ ] SSL certificates installed (if using HTTPS)
- [ ] Database migrations applied
- [ ] Backup strategy configured
- [ ] Health endpoints responding

### Important (Recommended)

- [ ] Performance tests passing (>90%)
- [ ] Data integrity validation passing (>80%)
- [ ] Monitoring and alerts configured
- [ ] Log rotation setup
- [ ] Firewall configured (ports 80, 443, 8000, 8501)
- [ ] Domain DNS configured

### Optional (Nice to Have)

- [ ] Celery workers for background jobs
- [ ] Nginx for SSL termination and reverse proxy
- [ ] Redis configured for caching
- [ ] Pusher for real-time updates

**Full Checklist**: See `frontend-streamlit/PRODUCTION_CHECKLIST.md` (75 items)

---

## 🔄 Updating After Deployment

### Code Changes

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
cd backend
docker-compose build
docker-compose up -d

# Or use deployment script
cd ../frontend-streamlit
./deploy-production.sh
```

### Configuration Changes

```bash
# Update .env files
nano backend/.env
nano frontend-streamlit/.env

# Restart affected services
docker-compose restart backend frontend
```

### Database Migrations

```bash
# Run migrations
docker exec iswitch-crm-backend alembic upgrade head

# Verify
docker exec iswitch-crm-backend alembic current
```

---

## 📈 Monitoring & Maintenance

### Daily

```bash
# Check service health
docker-compose ps

# Review logs
docker-compose logs --tail 100 frontend backend | grep -i error

# Check resource usage
docker stats --no-stream
```

### Weekly

```bash
# Rotate logs
find /app/logs -name "*.log" -mtime +7 -exec gzip {} \;

# Verify backups
ls -lh /backups/ | tail -10

# Run performance tests
docker exec iswitch-crm-backend python scripts/test_performance_metrics.py
```

### Monthly

```bash
# Update dependencies
cd backend
pip list --outdated

# Security audit
grep -i "failed\|unauthorized" /app/logs/*.log

# Check disk space
df -h
```

---

## 🆘 Emergency Procedures

### Application Down

```bash
# Quick restart
docker-compose restart

# If that fails, full restart
docker-compose down
docker-compose up -d

# Check health
curl http://localhost:8000/health
curl http://localhost:8501/_stcore/health
```

### Rollback to Previous Version

```bash
# Using deployment script (automatic backup/rollback)
cd frontend-streamlit
./deploy-production.sh
# Rollback happens automatically on failure

# Manual rollback
docker tag iswitch-streamlit:backup-YYYYMMDD iswitch-streamlit:latest
docker-compose restart frontend
```

### Database Issues

```bash
# Check database connection
docker exec iswitch-crm-backend psql $DATABASE_URL -c "SELECT version();"

# Run integrity validation
docker exec iswitch-crm-backend python scripts/validate_leads_integrity.py

# If needed, restore from backup
# (Backup procedure in MAINTENANCE.md)
```

---

## 📚 Additional Resources

- **Full Setup Guide**: `frontend-streamlit/README.md`
- **Production Checklist**: `frontend-streamlit/PRODUCTION_CHECKLIST.md` (75 items)
- **User Guide**: `frontend-streamlit/docs/USER_GUIDE.md`
- **Maintenance Guide**: `frontend-streamlit/docs/MAINTENANCE.md`
- **Backend Deployment**: `backend/docs/DEPLOYMENT.md`
- **Troubleshooting**: `backend/docs/TROUBLESHOOTING.md`

---

## 🎯 Success Criteria

Your deployment is successful when:

- ✅ All Docker containers are running (`docker-compose ps`)
- ✅ Health endpoints return 200 OK
- ✅ Frontend dashboard loads in browser
- ✅ Backend API documentation accessible at `/docs`
- ✅ Performance tests passing (18/18)
- ✅ No critical errors in logs
- ✅ Real-time updates working (30-second refresh)

---

## 📞 Support

- **Documentation**: See `README.md` at repository root
- **Issues**: Check phase documentation (PHASE_B through PHASE_E)
- **Emergency**: Contact technical lead

---

**Quick Start Guide Version**: 2.0.0
**Last Updated**: 2025-10-10
**Estimated Deployment Time**: 5-15 minutes
