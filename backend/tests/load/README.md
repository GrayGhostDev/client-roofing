# Load Testing with Locust - Setup & Execution Guide

## Overview
This directory contains Locust load testing scripts for the iSwitch Roofs CRM backend. The tests simulate realistic user behavior patterns with 100 concurrent users across 5 user types.

## Prerequisites

- Python 3.11+
- Backend running on `http://localhost:8000`
- Redis running on `localhost:6379`
- Database with seeded test data

## Installation

```bash
# Install Locust
pip install locust==2.15.1

# Or install from requirements.txt
cd backend
pip install -r requirements.txt
```

## Quick Start

### 1. Seed Test Data

```bash
# From backend directory
python scripts/seed_data.py --leads 100 --customers 50 --projects 75 --clear-first
```

### 2. Start Backend

```bash
# Terminal 1
cd backend
python run.py
```

### 3. Run Load Test

```bash
# Terminal 2
cd backend/tests/load
locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --html report.html
```

### 4. Monitor Test

- **Locust Web UI**: http://localhost:8089
- **Cache Stats**: http://localhost:8000/api/cache/stats
- **Backend Logs**: Watch Terminal 1 for errors

## Test Configuration

### User Types & Distribution

| User Type | Weight | Behavior |
|-----------|--------|----------|
| DashboardUser | 40% | Views dashboard and metrics (mostly read) |
| LeadManagementUser | 30% | CRUD operations on leads (mixed read/write) |
| ProjectViewUser | 20% | Views and filters projects (read-heavy) |
| AnalyticsUser | 10% | Heavy analytics queries (expensive reads) |
| MixedWorkloadUser | 15% | Combined workflows (realistic patterns) |

**Total**: 115% (intentional overlap - users can switch behaviors)

### Performance Targets

| Metric | Target | Priority |
|--------|--------|----------|
| 95th percentile response time | <500ms | Critical |
| Error rate | <1% | Critical |
| Throughput | >500 req/s | High |
| Cache hit rate | >80% | High |
| Concurrent connections | 100+ | Medium |

## Command-Line Options

### Basic Usage

```bash
# Run with default settings (100 users, 5 min)
locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m

# Run headless (no web UI)
locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --headless --html report.html

# Run with specific user class only
locust -f locustfile.py --host=http://localhost:8000 --users 50 DashboardUser --spawn-rate 10 --run-time 2m
```

### Advanced Options

```bash
# Gradual ramp-up (recommended for production)
locust -f locustfile.py --host=http://localhost:8000 \
  --users 100 --spawn-rate 5 --run-time 10m \
  --html report.html --logfile locust.log --loglevel INFO

# Stress test (find breaking point)
locust -f locustfile.py --host=http://localhost:8000 \
  --users 200 --spawn-rate 20 --run-time 5m --headless

# Custom CSV output
locust -f locustfile.py --host=http://localhost:8000 \
  --users 100 --spawn-rate 10 --run-time 5m \
  --csv=results --html=report.html
```

## Interpreting Results

### Locust Web UI (http://localhost:8089)

**Key Metrics**:

1. **RPS (Requests Per Second)**: Current throughput
   - Target: >500 req/s
   - Watch for drops during test

2. **Failure Rate**: Percentage of failed requests
   - Target: <1%
   - Investigate any failures immediately

3. **Response Time Distribution**:
   - Median: Should be <200ms
   - 95th percentile: Should be <500ms
   - 99th percentile: Should be <1000ms

4. **Charts**:
   - Total Requests per Second
   - Response Times (median, 95th percentile)
   - Number of Users

### HTML Report

After test completion, open `report.html` in browser:

- **Statistics Table**: Per-endpoint performance
- **Charts**: Visual representation of metrics
- **Failures**: List of all failed requests

**Key Sections**:
1. Requests: Total request count and distribution
2. Failures: Types and frequencies of errors
3. Response Time Distribution: Histogram
4. Current RPS: Throughput over time

### Terminal Output

At test completion, you'll see:

```
========================================================
LOAD TEST RESULTS
========================================================
Total Requests: 24,567
Total Failures: 12
Error Rate: 0.05% ✅ PASS (Target: <1%)

Response Times:
  Average: 187.34ms
  95th Percentile: 423.12ms ✅ PASS (Target: <500ms)

Throughput:
  Requests/second: 612.45 ✅ PASS (Target: >500 req/s)

========================================================
CACHE PERFORMANCE STATISTICS
========================================================
Cache Hits: 19,245
Cache Misses: 5,322
Hit Rate: 78.32%
Target: >80%
Status: ❌ FAIL
========================================================

RECOMMENDATION:
❌ System does not meet performance targets
   Review bottlenecks before production deployment
========================================================
```

## Troubleshooting

### High Error Rate (>1%)

**Possible Causes**:
1. Database connection pool exhausted
2. Redis connection issues
3. Slow database queries
4. Memory issues

**Solutions**:
```bash
# Check database connection pool
curl http://localhost:8000/api/cache/stats

# Check Redis connection
redis-cli ping

# Review backend logs for errors
tail -f logs/iswitch_roofs_crm.log
```

### Slow Response Times (95th >500ms)

**Possible Causes**:
1. Missing database indexes
2. Low cache hit rate
3. Expensive analytics queries
4. Network latency

**Solutions**:
```bash
# Apply database indexes
psql -U postgres -d iswitch_crm -f migrations/003_performance_indexes.sql

# Warm cache
python scripts/warm_cache.py

# Check cache stats
curl http://localhost:8000/api/cache/stats
```

### Low Throughput (<500 req/s)

**Possible Causes**:
1. CPU bottleneck
2. Network bottleneck
3. Database contention
4. Inefficient queries

**Solutions**:
1. Optimize expensive queries
2. Increase connection pool size
3. Scale horizontally (multiple backend instances)
4. Use CDN for static assets

### Low Cache Hit Rate (<80%)

**Possible Causes**:
1. Cache not warmed
2. TTL too short
3. Cache invalidation too aggressive
4. Test data causing cache misses

**Solutions**:
```bash
# Warm cache before test
python scripts/warm_cache.py

# Increase TTL in cache.py (if appropriate)
# Check cache invalidation logic

# Verify cache is working
curl http://localhost:8000/api/cache/health
```

## Best Practices

### Pre-Test Checklist

- [ ] Backend is running and healthy
- [ ] Redis is running (`redis-cli ping`)
- [ ] Database has test data (run seed script)
- [ ] Database indexes are applied
- [ ] Cache is warmed (`python scripts/warm_cache.py`)
- [ ] Previous test results cleared

### During Test

- [ ] Monitor Locust Web UI (http://localhost:8089)
- [ ] Watch backend logs for errors
- [ ] Monitor system resources (CPU, memory, disk)
- [ ] Check cache stats periodically
- [ ] Note any anomalies or spikes

### Post-Test

- [ ] Review HTML report
- [ ] Check cache hit rate (target >80%)
- [ ] Identify slowest endpoints
- [ ] Document any failures
- [ ] Compare against baseline
- [ ] Update load test report template

## Test Scenarios

### Scenario 1: Baseline Performance (5 min)

**Objective**: Establish baseline performance metrics

```bash
locust -f locustfile.py --host=http://localhost:8000 \
  --users 100 --spawn-rate 10 --run-time 5m --html baseline_report.html
```

**Expected Results**:
- 95th percentile: <500ms
- Error rate: <1%
- Throughput: >500 req/s

### Scenario 2: Stress Test (5 min)

**Objective**: Find system breaking point

```bash
locust -f locustfile.py --host=http://localhost:8000 \
  --users 200 --spawn-rate 20 --run-time 5m --html stress_report.html
```

**Expected Results**:
- Identify maximum concurrent users
- Determine failure mode
- Measure degradation

### Scenario 3: Sustained Load (30 min)

**Objective**: Test stability under sustained load

```bash
locust -f locustfile.py --host=http://localhost:8000 \
  --users 100 --spawn-rate 5 --run-time 30m --html sustained_report.html
```

**Expected Results**:
- No memory leaks
- Consistent performance
- No connection pool exhaustion

### Scenario 4: Dashboard-Only Load

**Objective**: Test dashboard query performance

```bash
locust -f locustfile.py --host=http://localhost:8000 \
  --users 100 DashboardUser --spawn-rate 10 --run-time 5m --html dashboard_report.html
```

**Expected Results**:
- Cache hit rate: >90%
- Response times: <200ms avg

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Load Test

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  load-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
      redis:
        image: redis:7

    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Seed test data
        run: python scripts/seed_data.py --clear-first

      - name: Start backend
        run: python run.py &

      - name: Run load test
        run: |
          cd tests/load
          locust -f locustfile.py --host=http://localhost:8000 \
            --users 100 --spawn-rate 10 --run-time 5m \
            --headless --html report.html --csv results

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: tests/load/report.html

      - name: Check performance thresholds
        run: python tests/load/check_thresholds.py results_stats.csv
```

## Additional Resources

- **Locust Documentation**: https://docs.locust.io/
- **Performance Testing Guide**: https://martinfowler.com/articles/practical-test-pyramid.html
- **Backend Optimization**: See `docs/PERFORMANCE_OPTIMIZATION.md`

## Contact

For questions or issues with load testing:
- Review backend logs: `logs/iswitch_roofs_crm.log`
- Check system health: `http://localhost:8000/health`
- Cache monitoring: `http://localhost:8000/api/cache/health`
