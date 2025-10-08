# Database Connection Fix Guide

**Issue:** Cannot connect to Supabase PostgreSQL database  
**Error:** `connection to server failed: No route to host`  
**Current Status:** IPv6 connection failing on port 5432

---

## 🔧 Quick Fix: Switch to Connection Pooler

Supabase provides a connection pooler on port **6543** which often works better than direct connections on port 5432.

### Step 1: Update .env File

**Current:** Port 5432 (Direct PostgreSQL)  
**Change to:** Port 6543 (Connection Pooler with PgBouncer)

```bash
# Backup current .env
cp .env .env.backup

# Update DATABASE_URL to use port 6543 and add pgbouncer parameter
# Change from:
# DATABASE_URL=postgresql://postgres:PASSWORD@db.tdwpzktihdeuzapxoovk.supabase.co:5432/postgres
# 
# To:
# DATABASE_URL=postgresql://postgres:PASSWORD@db.tdwpzktihdeuzapxoovk.supabase.co:6543/postgres?pgbouncer=true
```

**Manual Edit Command:**
```bash
# Open .env and change port 5432 to 6543, and add ?pgbouncer=true
nano .env
```

Or use this sed command (CAREFUL - verify first):
```bash
cd /Users/grayghostdataconsultants/Development/projects/clients/client-roofing
sed -i.bak 's/:5432\/postgres/:6543\/postgres?pgbouncer=true/' .env
```

### Step 2: Restart Backend

```bash
# Kill existing backend
pkill -9 -f "backend/run.py"

# Wait a moment
sleep 3

# Start backend fresh
cd /Users/grayghostdataconsultants/Development/projects/clients/client-roofing
.venv/bin/python backend/run.py > /tmp/backend.log 2>&1 &

# Wait for startup
sleep 10

# Test connection
curl --noproxy "*" -s http://127.0.0.1:8000/api/leads/stats | head -c 200
```

---

## 🌐 Alternative Fix: Check Supabase Project

### Option A: Verify Project Status

1. **Visit Supabase Dashboard:**
   ```
   https://app.supabase.com/project/tdwpzktihdeuzapxoovk
   ```

2. **Check:**
   - ✅ Project is not paused
   - ✅ Database is running
   - ✅ No billing issues
   - ✅ IPv4 pooler is enabled

### Option B: Get IPv4 Address

Supabase might have an IPv4 address for the connection pooler:

1. Go to **Settings → Database** in Supabase dashboard
2. Look for "Connection Pooling" section
3. Copy the **IPv4 pooler URL** if available
4. Update your `.env` with the IPv4 address

### Option C: Disable IPv6 in PostgreSQL Connection

Add this to your DATABASE_URL:
```
?target_session_attrs=read-write&connect_timeout=10
```

---

## 🔍 Troubleshooting Steps

### Test 1: Check Supabase Accessibility
```bash
# Try to reach Supabase API
curl -I https://tdwpzktihdeuzapxoovk.supabase.co 2>&1 | head -5

# Check if port 6543 is accessible
nc -z db.tdwpzktihdeuzapxoovk.supabase.co 6543 && echo "Port 6543 OK" || echo "Port 6543 blocked"
```

### Test 2: Check Network/Firewall
```bash
# Test if firewall is blocking PostgreSQL ports
sudo pfctl -s rules | grep 5432
sudo pfctl -s rules | grep 6543

# Check if VPN is interfering
# Temporarily disable VPN and test again
```

### Test 3: Verify Environment Variables
```bash
cd /Users/grayghostdataconsultants/Development/projects/clients/client-roofing
grep DATABASE_URL .env | sed 's/:[^:]*@/:****@/'  # Shows URL without password
```

### Test 4: Test from Python Directly
```bash
cd /Users/grayghostdataconsultants/Development/projects/clients/client-roofing
.venv/bin/python -c "
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
db_url = os.getenv('DATABASE_URL')
print(f'Testing connection...')

try:
    # Try connection
    conn = psycopg2.connect(db_url, connect_timeout=5)
    print('✅ Connection successful!')
    conn.close()
except Exception as e:
    print(f'❌ Connection failed: {e}')
"
```

---

## 🚫 Known Issues

### Issue 1: IPv6 Only Resolution
**Problem:** Hostname only resolves to IPv6, but IPv6 routing is broken  
**Solution:** Use connection pooler (port 6543) or get IPv4 address from Supabase

### Issue 2: Firewall Blocking
**Problem:** macOS firewall or corporate firewall blocking PostgreSQL ports  
**Solution:** 
- Check macOS firewall settings
- Add exception for ports 5432 and 6543
- Or use Supabase's REST API as fallback

### Issue 3: Supabase Project Paused
**Problem:** Free tier projects pause after inactivity  
**Solution:** Visit dashboard and resume project

---

## ✅ Quick Commands Reference

```bash
# 1. Backup .env
cp .env .env.backup

# 2. Change port to 6543 (manual edit recommended)
nano .env
# Change: :5432/postgres
# To: :6543/postgres?pgbouncer=true

# 3. Restart backend
pkill -9 -f "backend/run.py"
sleep 3
cd /Users/grayghostdataconsultants/Development/projects/clients/client-roofing
.venv/bin/python backend/run.py > /tmp/backend.log 2>&1 &

# 4. Wait and test
sleep 10
curl --noproxy "*" -s http://127.0.0.1:8000/api/leads/stats | head -c 200

# 5. Check logs if issues
tail -50 /tmp/backend.log | grep -i "error\|connection"
```

---

## 📊 Expected Results

### Success:
```json
{
  "success": true,
  "data": {
    "total_leads": 150,
    "new_leads": 25,
    ...
  }
}
```

### Still Failing:
```json
{
  "error": "Failed to fetch stats",
  "details": "connection to server failed..."
}
```

If still failing after port change:
1. Verify Supabase project is active
2. Check Supabase dashboard for connection string
3. Try REST API fallback (see below)

---

## 🔄 Fallback: Use Supabase REST API

If PostgreSQL connection continues to fail, you can use Supabase's REST API:

```python
# Instead of direct SQL, use Supabase client
from supabase import create_client

client = create_client(SUPABASE_URL, SUPABASE_KEY)
leads = client.table('leads').select('*').execute()
```

This bypasses PostgreSQL direct connection and uses HTTPS instead.

---

## 📞 Next Steps After Fix

Once database connection works:

1. ✅ Test all API endpoints
2. ✅ Configure Streamlit authentication
3. ✅ Verify dashboard data loads
4. ✅ Test real-time updates

**Priority:** Fix database connection first - everything else depends on it.
