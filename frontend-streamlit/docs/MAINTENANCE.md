# iSwitch Roofs CRM - Maintenance & Operations Guide

**Version**: 2.0.0 | **Last Updated**: 2025-10-10

---

## Daily Operations

### Health Checks (Every Morning)

```bash
# 1. Check service status
docker ps | grep iswitch-crm

# 2. Verify health endpoints
curl http://localhost:8501/_stcore/health  # Frontend
curl http://localhost:8000/health           # Backend

# 3. Review overnight logs
docker logs --since 24h iswitch-crm-frontend | grep -i error
docker logs --since 24h iswitch-crm-backend | grep -i error

# 4. Check resource usage
docker stats --no-stream iswitch-crm-frontend iswitch-crm-backend
```

**Expected Results**:
- All containers: `STATUS = Up`
- Health endpoints: `200 OK`
- Error count: `<10 per day`
- CPU usage: `<50%`
- Memory: `<2GB per container`

---

## Weekly Maintenance

### Log Rotation (Every Monday)

```bash
# Rotate logs older than 7 days
cd /app/logs
find . -name "*.log" -mtime +7 -exec gzip {} \;
find . -name "*.log.gz" -mtime +30 -delete
```

### Backup Verification (Every Sunday)

```bash
# 1. List recent backups
ls -lh /backups/ | tail -10

# 2. Test latest backup restore
LATEST_BACKUP=$(ls -t /backups/ | head -1)
./deploy-production.sh restore-backup $LATEST_BACKUP --dry-run

# 3. Verify backup completeness
du -sh /backups/$LATEST_BACKUP
# Expected: >10MB (includes config + Docker image)
```

### Performance Review

```bash
# Run performance tests
cd backend
python scripts/test_performance_metrics.py

# Expected:
# - All 18 tests passing
# - Average response time: <5ms
# - No queries >100ms
```

---

## Monthly Tasks

### Dependency Updates (First Monday)

```bash
# 1. Check for security updates
cd frontend-streamlit
pip list --outdated

# 2. Review updates
pip install --upgrade --dry-run -r requirements.txt

# 3. Update in staging first
cd ../backend
docker-compose -f docker-compose.dev.yml pull
docker-compose -f docker-compose.dev.yml up -d frontend

# 4. Test thoroughly in staging
# 5. Deploy to production if tests pass
```

### Database Maintenance (15th of month)

```bash
# 1. Vacuum PostgreSQL (via backend)
docker exec iswitch-crm-backend python scripts/vacuum_database.py

# 2. Update statistics
docker exec iswitch-crm-backend python scripts/analyze_database.py

# 3. Check table sizes
docker exec iswitch-crm-backend psql $DATABASE_URL -c "
  SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
  FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

### Security Audit (Last Friday)

```bash
# 1. Review access logs
grep -i "failed\|unauthorized\|403\|401" /app/logs/*.log

# 2. Check SSL certificate expiry
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates

# 3. Rotate API keys (if needed)
# Update .env with new keys
# Restart services: docker-compose restart

# 4. Review user permissions
# Audit database access logs
```

---

## Monitoring & Alerts

### Key Metrics to Monitor

1. **Uptime**
   - Target: 99.9%
   - Alert: Service down >5 minutes

2. **Response Time**
   - Target: <2s page load
   - Alert: >5s average over 5 minutes

3. **Error Rate**
   - Target: <1% of requests
   - Alert: >5% error rate

4. **Resource Usage**
   - Target: <70% CPU, <80% memory
   - Alert: >90% for >10 minutes

5. **Disk Space**
   - Target: <70% full
   - Alert: >85% full

### Alert Response Procedures

#### Service Down

```bash
# 1. Check container status
docker ps -a | grep iswitch-crm

# 2. View recent logs
docker logs --tail 100 iswitch-crm-frontend

# 3. Restart if needed
docker restart iswitch-crm-frontend

# 4. If restart fails, rollback
cd backend
docker-compose down
docker-compose up -d
```

#### High Error Rate

```bash
# 1. Identify error types
docker logs iswitch-crm-frontend | grep -i error | sort | uniq -c | sort -rn

# 2. Check backend connectivity
curl http://backend:8000/health

# 3. Review recent changes
git log --since="2 hours ago" --oneline

# 4. Rollback if necessary
./deploy-production.sh rollback
```

#### Performance Degradation

```bash
# 1. Check resource usage
docker stats --no-stream

# 2. Identify slow queries
cd backend
python scripts/test_performance_metrics.py

# 3. Check database connections
docker exec iswitch-crm-backend psql $DATABASE_URL -c "
  SELECT count(*) FROM pg_stat_activity WHERE state != 'idle';
"

# 4. Restart services if needed
docker-compose restart frontend backend
```

---

## Backup & Recovery

### Daily Automated Backup

**Cron Job** (`/etc/cron.d/iswitch-backup`):
```cron
0 2 * * * root /opt/iswitch-roofs/frontend-streamlit/scripts/backup.sh
```

**Backup Script** (`scripts/backup.sh`):
```bash
#!/bin/bash
BACKUP_DIR="/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup configuration
cp .env "$BACKUP_DIR/"
cp .streamlit/config.toml "$BACKUP_DIR/"

# Backup Docker image
docker commit iswitch-crm-frontend "iswitch-streamlit:backup-$(date +%Y%m%d)"

# Compress and upload (if S3 configured)
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
# aws s3 cp "$BACKUP_DIR.tar.gz" s3://your-bucket/backups/
```

### Recovery Procedures

#### Restore from Backup

```bash
# 1. List available backups
ls -lh /backups/

# 2. Extract backup
tar -xzf /backups/20251010_020000.tar.gz -C /tmp/

# 3. Restore configuration
cp /tmp/20251010_020000/.env /opt/iswitch-roofs/frontend-streamlit/
cp /tmp/20251010_020000/.streamlit/config.toml /opt/iswitch-roofs/frontend-streamlit/.streamlit/

# 4. Restore Docker image
docker load < /tmp/20251010_020000/image.tar

# 5. Restart services
cd /opt/iswitch-roofs/backend
docker-compose restart frontend
```

#### Emergency Rollback

```bash
# Automatic rollback (deployment script)
./deploy-production.sh
# Rollback happens automatically on failure

# Manual rollback
docker tag iswitch-streamlit:backup-20251010 iswitch-streamlit:latest
docker-compose restart frontend
```

---

## Common Issues & Solutions

### Issue 1: Dashboard Not Loading

**Symptoms**:
- Blank page or loading spinner
- Browser console shows connection errors

**Diagnosis**:
```bash
# Check service status
docker ps | grep frontend

# Check logs
docker logs iswitch-crm-frontend | tail -50

# Check backend connectivity
curl http://backend:8000/health
```

**Solutions**:
1. Restart frontend: `docker restart iswitch-crm-frontend`
2. Check `.env` configuration
3. Verify backend is running
4. Clear browser cache

---

### Issue 2: Slow Performance

**Symptoms**:
- Dashboard takes >5s to load
- Charts render slowly

**Diagnosis**:
```bash
# Run performance tests
cd backend
python scripts/test_performance_metrics.py

# Check resource usage
docker stats iswitch-crm-frontend

# Check database
docker exec iswitch-crm-backend psql $DATABASE_URL -c "
  SELECT pid, query, state, wait_event_type
  FROM pg_stat_activity WHERE state != 'idle';
"
```

**Solutions**:
1. Increase cache TTL: `.env` → `CACHE_TTL_SECONDS=600`
2. Optimize database: `python scripts/vacuum_database.py`
3. Restart services: `docker-compose restart`
4. Scale resources if needed

---

### Issue 3: Real-time Updates Not Working

**Symptoms**:
- Dashboard shows stale data
- "Last Updated" timestamp not changing

**Diagnosis**:
```bash
# Check auto-refresh setting
grep -i refresh .streamlit/config.toml

# Check Pusher connectivity (if used)
docker logs iswitch-crm-frontend | grep -i pusher

# Check backend connectivity
curl http://backend:8000/realtime/snapshot
```

**Solutions**:
1. Click "Refresh Now" button manually
2. Check backend health
3. Verify Pusher credentials (if used)
4. Restart frontend container

---

### Issue 4: Data Integrity Errors

**Symptoms**:
- ENUM value errors in logs
- NULL constraint violations
- Foreign key errors

**Diagnosis**:
```bash
cd backend
python scripts/validate_leads_integrity.py
```

**Solutions**:
1. Fix legacy data:
   ```sql
   UPDATE leads SET temperature = 'warm' WHERE temperature IS NULL;
   UPDATE leads SET created_at = NOW() WHERE created_at > NOW();
   ```
2. Rerun validation
3. Document any persistent issues

---

## Deployment Updates

### Zero-Downtime Deployment

```bash
# 1. Deploy to staging
cd frontend-streamlit
./deploy-staging.sh

# 2. Test in staging
# - Verify all features work
# - Run performance tests
# - Check logs for errors

# 3. Deploy to production
./deploy-production.sh
# Automatic health checks and rollback on failure

# 4. Monitor for 1 hour post-deployment
docker logs -f iswitch-crm-frontend | grep -i error
```

### Emergency Hotfix

```bash
# 1. Fix code locally
# 2. Build new image
docker build -t iswitch-streamlit:hotfix .

# 3. Stop current container
docker stop iswitch-crm-frontend

# 4. Deploy hotfix
docker run -d --name iswitch-crm-frontend \
  --restart unless-stopped \
  -p 8501:8501 \
  --env-file .env \
  iswitch-streamlit:hotfix

# 5. Verify fix
curl http://localhost:8501/_stcore/health
```

---

## Configuration Management

### Environment Variables

**Critical Variables** (`.env`):
```bash
BACKEND_API_URL=http://backend:8000  # Production URL
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx                      # Anon key only
PUSHER_APP_KEY=xxx                    # Optional
CACHE_TTL_SECONDS=300
```

**Security Best Practices**:
- Never commit `.env` to git
- Rotate keys every 90 days
- Use separate keys for staging/production
- Limit Supabase key permissions

### Streamlit Configuration

**File**: `.streamlit/config.toml`

```toml
[server]
port = 8501
enableCORS = false
enableXsrfProtection = true

[theme]
primaryColor = "#667eea"
```

**Changes Require**: Container restart

---

## Performance Optimization

### Caching Strategy

1. **Streamlit Cache** (`@st.cache_data`):
   - TTL: 300 seconds (5 minutes)
   - Used for: API responses, charts

2. **Backend Cache** (Redis):
   - TTL: 60 seconds
   - Used for: Database queries

3. **Browser Cache**:
   - Static assets: 1 hour
   - API responses: No cache

### Database Optimization

```bash
# Create indexes (if not exists)
cd backend
python scripts/create_indexes.py

# Analyze query plans
docker exec iswitch-crm-backend psql $DATABASE_URL -c "
  EXPLAIN ANALYZE SELECT * FROM leads WHERE temperature = 'hot';
"
```

---

## Disaster Recovery

### RTO/RPO Targets

- **RTO** (Recovery Time Objective): <30 minutes
- **RPO** (Recovery Point Objective): <24 hours

### Recovery Steps

1. **Assess Damage**
   - Identify failed components
   - Determine data loss scope

2. **Restore Infrastructure**
   ```bash
   # Restore Docker containers
   docker-compose up -d

   # Restore from backup
   tar -xzf /backups/latest.tar.gz
   cp -r /backups/latest/.env /opt/iswitch-roofs/frontend-streamlit/
   ```

3. **Verify Integrity**
   ```bash
   # Run health checks
   curl http://localhost:8501/_stcore/health

   # Validate data
   cd backend
   python scripts/validate_leads_integrity.py
   ```

4. **Resume Operations**
   - Notify users
   - Monitor closely for 24 hours
   - Document incident

---

## Contact & Escalation

### Support Tiers

**Tier 1** (Self-Service):
- Check logs
- Review troubleshooting guide
- Restart services

**Tier 2** (Technical Lead):
- Complex issues
- Performance problems
- Configuration changes

**Tier 3** (Engineering Team):
- Code bugs
- Architecture changes
- Major incidents

### On-Call Schedule

- **Weekdays**: Technical lead (9am-5pm)
- **Nights/Weekends**: On-call rotation
- **Emergency**: Page engineering team

---

**Maintenance Guide Version**: 2.0.0
**Last Updated**: 2025-10-10
**Next Review**: Quarterly or after major incident
