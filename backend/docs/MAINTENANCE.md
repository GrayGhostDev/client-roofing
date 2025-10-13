# Maintenance Guide - iSwitch Roofs CRM

Operational procedures for maintaining the iSwitch Roofs CRM system.

## Table of Contents
- [Daily Maintenance](#daily-maintenance)
- [Weekly Maintenance](#weekly-maintenance)
- [Monthly Maintenance](#monthly-maintenance)
- [Database Maintenance](#database-maintenance)
- [Cache Maintenance](#cache-maintenance)
- [Log Management](#log-management)
- [Backup Procedures](#backup-procedures)

---

## Daily Maintenance

### Health Checks (Every 4 hours)
```bash
# Run comprehensive health check
./scripts/health_check.sh --component all --exit-on-failure

# Expected output:
# ✓ Backend API is healthy (125ms)
# ✓ Database connection successful
# ✓ Redis connection successful
# ✓ Cache hit rate is excellent: 85%
# ✓ Resources adequate (disk: 150GB)
```

### Monitor Application Logs
```bash
# Check for errors in last 24 hours
journalctl -u iswitch-crm --since "24 hours ago" | grep -i error

# Or with Docker
docker logs --since 24h iswitch-crm-backend | grep -i error

# Watch real-time logs
tail -f /var/log/iswitch-crm/error.log
```

### Check System Resources
```bash
# CPU and memory
htop

# Disk usage
df -h | grep -v tmpfs

# Alert if disk usage > 80%
df -h / | awk 'NR==2 {if (int($5) > 80) print "WARNING: Disk usage is " $5}'
```

### Verify Backup Status
```bash
# Check last backup
ls -lh /backups/ | head -5

# Verify backup size
du -sh /backups/database_backup_*.sql.gz
```

---

## Weekly Maintenance

### Database Maintenance

**Vacuum and Analyze (Every Sunday 2 AM):**
```bash
# Add to crontab
0 2 * * 0 /opt/iswitch-crm/backend/scripts/db_maintenance.sh

# db_maintenance.sh content:
#!/bin/bash
set -euo pipefail

source /opt/iswitch-crm/backend/.env

echo "Starting database maintenance..."

# Connect to database and run maintenance
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
-- Vacuum all tables
VACUUM ANALYZE customers;
VACUUM ANALYZE leads;
VACUUM ANALYZE projects;
VACUUM ANALYZE appointments;
VACUUM ANALYZE interactions;

-- Update statistics
ANALYZE;

-- Report table sizes
SELECT
    relname AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 10;
EOF

echo "Database maintenance completed"
```

### Clear Old Data

**Remove old audit logs (> 90 days):**
```bash
# audit_cleanup.sh
#!/bin/bash
DAYS_TO_KEEP=90

psql "$DATABASE_URL" << EOF
DELETE FROM audit_logs
WHERE created_at < NOW() - INTERVAL '$DAYS_TO_KEEP days';

SELECT COUNT(*) AS deleted_records FROM audit_logs;
EOF
```

**Archive completed projects (> 1 year):**
```bash
# Archive to separate table
psql "$DATABASE_URL" << EOF
INSERT INTO projects_archive
SELECT * FROM projects
WHERE status = 'completed'
AND end_date < NOW() - INTERVAL '1 year';

-- Verify before deleting
SELECT COUNT(*) FROM projects_archive;
EOF
```

### Cache Optimization

**Clear expired keys:**
```bash
# Redis maintenance
redis-cli INFO keyspace
redis-cli --scan --pattern "cache:*" | xargs redis-cli DEL
redis-cli MEMORY PURGE
```

**Analyze cache hit rate:**
```bash
# Check hit rate for last 7 days
./scripts/monitoring.sh --interval 3600 --export /tmp/metrics.csv &
sleep 86400  # Run for 24 hours
kill %1

# Analyze CSV
awk -F',' '{sum+=$4; count++} END {print "Avg hit rate: " sum/count "%"}' /tmp/metrics.csv
```

---

## Monthly Maintenance

### Security Updates

**Update system packages:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y

# Check for security updates
sudo unattended-upgrades --dry-run
```

**Update Python dependencies:**
```bash
cd /opt/iswitch-crm/backend

# Backup current requirements
cp requirements.txt requirements.txt.backup

# Update packages
source venv/bin/activate
pip list --outdated
pip install --upgrade pip
pip install --upgrade -r requirements.txt

# Test application
python -m pytest tests/

# If tests fail, rollback
cp requirements.txt.backup requirements.txt
pip install -r requirements.txt
```

### Database Performance Review

**Identify slow queries:**
```sql
-- Enable pg_stat_statements extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find slowest queries
SELECT
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    stddev_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 100  -- queries slower than 100ms
ORDER BY mean_exec_time DESC
LIMIT 20;
```

**Add missing indexes:**
```sql
-- Check missing indexes
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
AND n_distinct > 100
AND correlation < 0.1;

-- Example: Add index if needed
CREATE INDEX CONCURRENTLY idx_leads_created_status
ON leads (created_at DESC, status)
WHERE status IN ('new', 'contacted');
```

### Generate Performance Reports

**Monthly analytics export:**
```bash
# Export analytics data
./scripts/generate_report.sh --month "$(date +%Y-%m)" --output /reports/

# Report includes:
# - Revenue by project type
# - Lead conversion funnel
# - Customer acquisition cost
# - Team performance metrics
# - System uptime and response times
```

---

## Database Maintenance

### Full Database Backup (Weekly)

**Automated backup script** (already configured):
```bash
# Run backup manually
./scripts/backup.sh \
  --destination s3 \
  --compress \
  --encrypt \
  --retention 30

# Cron job for weekly full backup
0 3 * * 0 /opt/iswitch-crm/backend/scripts/backup.sh --destination s3 --compress --encrypt
```

### Incremental Backup (Daily)

**Point-in-Time Recovery (PITR) setup:**
```bash
# Configure PostgreSQL WAL archiving
# In postgresql.conf:
archive_mode = on
archive_command = 'cp %p /backups/wal_archive/%f'
wal_level = replica

# Restore from PITR
pg_basebackup -h localhost -U postgres -D /var/lib/postgresql/restore -Fp -Xs -P
```

### Database Replication (High Availability)

**Setup read replica:**
```sql
-- On primary server
CREATE USER replicator REPLICATION LOGIN ENCRYPTED PASSWORD 'secure_password';

-- In pg_hba.conf
host replication replicator REPLICA_IP/32 md5

-- On replica server
pg_basebackup -h PRIMARY_IP -D /var/lib/postgresql/data -U replicator -P -v -W
```

---

## Cache Maintenance

### Redis Memory Optimization

**Configure eviction policy:**
```bash
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru  # Evict least recently used keys

# Apply configuration
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

**Monitor Redis memory:**
```bash
# Check memory usage
redis-cli INFO memory

# Find large keys
redis-cli --bigkeys

# Sample keys
redis-cli --scan --pattern "cache:*" | head -20
```

### Clear Cache Selectively

```bash
# Clear specific pattern
redis-cli --scan --pattern "analytics:*" | xargs redis-cli DEL

# Clear all cache (use with caution!)
redis-cli FLUSHDB

# Restart Redis
sudo systemctl restart redis
```

---

## Log Management

### Log Rotation

**Configure logrotate** (`/etc/logrotate.d/iswitch-crm`):
```
/var/log/iswitch-crm/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 iswitch iswitch
    sharedscripts
    postrotate
        systemctl reload iswitch-crm > /dev/null 2>&1 || true
    endscript
}
```

### Analyze Logs

**Find errors:**
```bash
# Count errors by type
grep -i error /var/log/iswitch-crm/error.log | \
  cut -d':' -f1-2 | \
  sort | uniq -c | sort -rn

# Find 500 errors
grep "500" /var/log/iswitch-crm/access.log | tail -20
```

**Monitor response times:**
```bash
# Average response time
awk '{print $10}' /var/log/iswitch-crm/access.log | \
  awk '{sum+=$1; count++} END {print "Avg: " sum/count "ms"}'
```

---

## Backup Procedures

### Full Backup Checklist

1. **Database Backup**
```bash
./scripts/backup.sh --destination s3 --compress --encrypt
```

2. **Redis Backup**
```bash
redis-cli BGSAVE
aws s3 cp /var/lib/redis/dump.rdb s3://iswitch-backups/redis/
```

3. **Application Files**
```bash
tar -czf /backups/app-$(date +%Y%m%d).tar.gz /opt/iswitch-crm/backend
aws s3 cp /backups/app-*.tar.gz s3://iswitch-backups/app/
```

4. **Configuration Files**
```bash
tar -czf /backups/config-$(date +%Y%m%d).tar.gz \
  /opt/iswitch-crm/backend/.env \
  /etc/nginx/sites-available/iswitch-crm \
  /etc/systemd/system/iswitch-crm.service
```

### Disaster Recovery Test (Quarterly)

**Recovery drill:**
```bash
# 1. Restore database to test environment
./scripts/backup.sh --action restore --file s3://backups/latest.sql.gz

# 2. Verify data integrity
psql "$DATABASE_URL" << EOF
SELECT COUNT(*) FROM customers;
SELECT COUNT(*) FROM projects;
SELECT COUNT(*) FROM leads;
EOF

# 3. Test application functionality
curl http://test-api:8000/health
curl http://test-api:8000/api/customers?page=1

# 4. Document recovery time
echo "Recovery completed in X minutes"
```
