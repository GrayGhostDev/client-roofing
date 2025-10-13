# Troubleshooting Guide - iSwitch Roofs CRM

Common issues and solutions for the iSwitch Roofs CRM system.

## Table of Contents
- [Application Won't Start](#application-wont-start)
- [Database Issues](#database-issues)
- [Redis/Cache Issues](#rediscache-issues)
- [API Response Issues](#api-response-issues)
- [Authentication Problems](#authentication-problems)
- [Performance Issues](#performance-issues)
- [Deployment Issues](#deployment-issues)

---

## Application Won't Start

### Issue: "ModuleNotFoundError: No module named 'flask'"

**Symptom:**
```
ModuleNotFoundError: No module named 'flask'
```

**Cause:** Python dependencies not installed

**Solution:**
```bash
# Activate virtual environment
cd /opt/iswitch-crm/backend
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep -i flask
```

### Issue: "Address already in use" (Port 8000)

**Symptom:**
```
OSError: [Errno 98] Address already in use
```

**Cause:** Another process is using port 8000

**Solution:**
```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>

# Or use a different port
export API_PORT=8001
python run.py
```

### Issue: Application exits immediately

**Symptom:** Application starts then immediately exits

**Cause:** Environment variables not loaded or invalid configuration

**Solution:**
```bash
# Check .env file exists
ls -la /opt/iswitch-crm/backend/.env

# Validate environment variables
python << EOF
from dotenv import load_dotenv
import os
load_dotenv()
print("DATABASE_URL:", os.getenv("DATABASE_URL")[:30])
print("REDIS_URL:", os.getenv("REDIS_URL"))
print("JWT_SECRET:", "PRESENT" if os.getenv("JWT_SECRET") else "MISSING")
EOF

# Check logs for specific error
journalctl -u iswitch-crm -n 50 --no-pager
```

---

## Database Issues

### Issue: "could not connect to server: Connection refused"

**Symptom:**
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Cause:** PostgreSQL not running or wrong connection details

**Solution:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL if stopped
sudo systemctl start postgresql

# Test connection manually
psql "$DATABASE_URL"

# Verify firewall allows connection
sudo ufw status | grep 5432

# For Supabase, check URL format
echo $DATABASE_URL
# Should be: postgresql://user:pass@host:port/dbname?sslmode=require
```

### Issue: "Too many connections"

**Symptom:**
```
psycopg2.OperationalError: FATAL: too many connections for role "user"
```

**Cause:** Connection pool exhausted

**Solution:**
```sql
-- Check current connections
SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active';

-- Kill idle connections
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
AND state_change < NOW() - INTERVAL '10 minutes';

-- Increase max connections (requires restart)
ALTER SYSTEM SET max_connections = 100;
```

**Application fix:**
```python
# In app/config.py, reduce pool size
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 10,         # Reduced from 20
    "max_overflow": 20,      # Reduced from 30
    "pool_recycle": 300,
    "pool_pre_ping": True
}
```

### Issue: Slow query performance

**Symptom:** API responses > 500ms, database CPU high

**Diagnosis:**
```sql
-- Find slow queries
SELECT pid, now() - query_start AS duration, query, state
FROM pg_stat_activity
WHERE state != 'idle' AND now() - query_start > INTERVAL '1 second'
ORDER BY duration DESC;

-- Check missing indexes
SELECT
    schemaname,
    tablename,
    attname
FROM pg_stats
WHERE schemaname = 'public'
AND n_distinct > 100;
```

**Solution:**
```sql
-- Add missing indexes (examples)
CREATE INDEX CONCURRENTLY idx_leads_status_score
ON leads (status, score DESC);

CREATE INDEX CONCURRENTLY idx_customers_email
ON customers (email);

CREATE INDEX CONCURRENTLY idx_projects_customer_status
ON projects (customer_id, status);

-- Update statistics
ANALYZE;
```

---

## Redis/Cache Issues

### Issue: "Connection to Redis failed"

**Symptom:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Cause:** Redis not running or wrong connection URL

**Solution:**
```bash
# Check Redis status
sudo systemctl status redis

# Start Redis
sudo systemctl start redis

# Test connection
redis-cli ping
# Expected: PONG

# Check Redis logs
sudo journalctl -u redis -n 50

# Verify REDIS_URL
echo $REDIS_URL
# Should be: redis://localhost:6379/0
```

### Issue: High cache miss rate (< 50%)

**Symptom:** Cache hit rate below 50%, slow API responses

**Diagnosis:**
```bash
# Check cache stats
./scripts/health_check.sh --component redis --verbose

# Check Redis memory
redis-cli INFO memory

# Check key expiration
redis-cli INFO stats | grep expired
```

**Solution:**
```bash
# Increase cache TTL in decorators
# Edit app/utils/decorators.py
@cache_result(timeout=600)  # Increased from 300

# Increase Redis memory
redis-cli CONFIG SET maxmemory 4gb

# Warm up cache
python scripts/warm_cache.py
```

### Issue: Redis out of memory

**Symptom:**
```
OOM command not allowed when used memory > 'maxmemory'
```

**Solution:**
```bash
# Check memory usage
redis-cli INFO memory

# Increase max memory
redis-cli CONFIG SET maxmemory 4gb

# Enable eviction policy
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Clear old keys
redis-cli --scan --pattern "cache:analytics:*" | xargs redis-cli DEL

# Make permanent
sudo nano /etc/redis/redis.conf
# Add: maxmemory 4gb
# Add: maxmemory-policy allkeys-lru
```

---

## API Response Issues

### Issue: 500 Internal Server Error

**Symptom:** API returns 500 error with no details

**Diagnosis:**
```bash
# Check application logs
tail -f /var/log/iswitch-crm/error.log

# Or with Docker
docker logs --tail 100 iswitch-crm-backend

# Check specific endpoint
curl -v http://localhost:8000/api/customers
```

**Common causes:**
1. **Database connection failure** - Check DATABASE_URL
2. **Missing environment variable** - Verify all required env vars
3. **Unhandled exception** - Check error logs for traceback

**Solution:**
```bash
# Enable debug mode temporarily
export DEBUG=true
python run.py

# This will show detailed error traces
```

### Issue: 401 Unauthorized on valid token

**Symptom:** Valid JWT token rejected with 401

**Diagnosis:**
```bash
# Decode JWT token (without verification)
python << EOF
import jwt
token = "your_token_here"
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded)
EOF

# Check token expiration
# "exp" field should be > current timestamp
```

**Solution:**
```bash
# Token expired - get new token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@iswitchroofs.com","password":"password"}'

# If JWT_SECRET changed, all tokens invalidated
# Users need to login again
```

### Issue: CORS errors in browser

**Symptom:**
```
Access to fetch at 'http://localhost:8000/api/customers' from origin
'http://localhost:8501' has been blocked by CORS policy
```

**Solution:**
```python
# In app/__init__.py, verify CORS configuration
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:8501", "https://app.iswitchroofs.com"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

---

## Authentication Problems

### Issue: "Invalid credentials" on correct password

**Symptom:** Login fails with correct username/password

**Diagnosis:**
```sql
-- Check user exists
SELECT id, email, role FROM users WHERE email = 'admin@iswitchroofs.com';

-- Check password hash
SELECT password_hash FROM users WHERE email = 'admin@iswitchroofs.com';
```

**Solution:**
```bash
# Reset password
python << EOF
from app import create_app, db
from app.models.user import User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    user = User.query.filter_by(email='admin@iswitchroofs.com').first()
    user.password_hash = generate_password_hash('NewPassword123')
    db.session.commit()
    print("Password reset successfully")
EOF
```

### Issue: JWT token validation fails

**Symptom:**
```
jwt.exceptions.InvalidSignatureError: Signature verification failed
```

**Cause:** JWT_SECRET mismatch or changed

**Solution:**
```bash
# Verify JWT_SECRET is consistent
grep JWT_SECRET /opt/iswitch-crm/backend/.env

# If changed, all existing tokens are invalid
# Users must login again to get new tokens
```

---

## Performance Issues

### Issue: High CPU usage (> 80%)

**Diagnosis:**
```bash
# Check CPU usage
top -bn1 | grep iswitch-crm

# Check slow queries
psql "$DATABASE_URL" << EOF
SELECT pid, query, state, wait_event_type
FROM pg_stat_activity
WHERE state != 'idle'
AND query NOT LIKE '%pg_stat_activity%';
EOF
```

**Solution:**
```bash
# Optimize database queries (add indexes)
# Increase Gunicorn workers
# Edit /etc/systemd/system/iswitch-crm.service
ExecStart=/opt/iswitch-crm/venv/bin/gunicorn \
    --workers 8 \  # Increased from 4
    --threads 2 \
    ...

# Restart service
sudo systemctl daemon-reload
sudo systemctl restart iswitch-crm
```

### Issue: High memory usage (> 90%)

**Diagnosis:**
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Check Redis memory
redis-cli INFO memory
```

**Solution:**
```bash
# Reduce SQLAlchemy pool size
# In app/config.py:
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 10,  # Reduced
    "max_overflow": 10  # Reduced
}

# Reduce Gunicorn workers
# Edit systemd service: --workers 4

# Limit Redis memory
redis-cli CONFIG SET maxmemory 2gb
```

---

## Deployment Issues

### Issue: Docker build fails

**Symptom:**
```
ERROR: failed to solve: process "/bin/sh -c pip install -r requirements.txt"
did not complete successfully
```

**Solution:**
```bash
# Build with no cache
docker build --no-cache -t iswitch-crm-backend:latest .

# Check dependencies conflict
pip check

# Update pip
pip install --upgrade pip
```

### Issue: Health check fails after deployment

**Symptom:** Deployment completes but health check fails

**Diagnosis:**
```bash
# Check health manually
curl http://localhost:8000/health

# Check container logs
docker logs iswitch-crm-backend

# Check service status
systemctl status iswitch-crm
```

**Solution:**
```bash
# Rollback to previous version
./scripts/rollback.sh

# Check configuration
diff .env.production .env.example

# Verify database migrations
python scripts/migrate_database.py
```

For additional help, contact: support@iswitchroofs.com
