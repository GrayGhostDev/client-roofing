# Monitoring & Observability Implementation Guide

## Overview

This guide covers the comprehensive monitoring and observability infrastructure for the iSwitch Roofs CRM application. The implementation includes error tracking, health checks, structured logging, metrics collection, and uptime monitoring.

## Table of Contents

1. [Architecture](#architecture)
2. [Sentry Error Tracking](#sentry-error-tracking)
3. [Health Check Endpoints](#health-check-endpoints)
4. [Structured Logging](#structured-logging)
5. [Performance Monitoring](#performance-monitoring)
6. [UptimeRobot Integration](#uptimerobot-integration)
7. [Metrics Collection](#metrics-collection)
8. [Alerting](#alerting)
9. [Troubleshooting](#troubleshooting)

## Architecture

### Components

1. **Sentry SDK** - Error tracking and performance monitoring
2. **Health Endpoints** - Kubernetes-style health probes
3. **Structured Logging** - JSON-formatted logs for aggregation
4. **Performance Monitor** - Request/response metrics collection
5. **UptimeRobot** - External uptime monitoring
6. **System Metrics** - CPU, memory, disk usage tracking

### Data Flow

```
Application → Sentry (Errors/Performance)
           → Logs (Structured JSON)
           → Metrics Endpoint
           → Health Endpoints ← UptimeRobot
```

## Sentry Error Tracking

### Configuration

Sentry is automatically initialized when the application starts. Configuration is loaded from environment variables:

```bash
SENTRY_DSN=https://9a28c885ea1271c594ed0b7b08189b73@o4509912543199232.ingest.us.sentry.io/4509912547459072
SENTRY_ENVIRONMENT=development  # or production, staging
SENTRY_AUTH_TOKEN=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
```

### Features

- **Automatic Error Capture**: All uncaught exceptions are sent to Sentry
- **Performance Monitoring**: Transaction tracing for slow requests
- **Breadcrumbs**: Request/response logging for context
- **Release Tracking**: Version information attached to errors
- **Environment Tags**: Distinguish dev/staging/production errors

### Sample Rates

- **Development**: 100% of transactions
- **Production**: 10% of transactions (configurable)

### Manual Error Reporting

```python
import sentry_sdk

# Capture exception
try:
    risky_operation()
except Exception as e:
    sentry_sdk.capture_exception(e)

# Capture message
sentry_sdk.capture_message("Something went wrong", level="error")

# Add context
with sentry_sdk.push_scope() as scope:
    scope.set_tag("customer_id", "12345")
    scope.set_context("lead", {"id": lead_id, "status": status})
    sentry_sdk.capture_exception(e)
```

## Health Check Endpoints

### Available Endpoints

#### 1. Basic Health Check (`/health`)

**Purpose**: Verify service is running  
**Use Case**: Load balancer health checks  
**Response Time**: < 50ms

```bash
curl http://localhost:5000/health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "iSwitch Roofs CRM API",
  "timestamp": "2025-10-06T12:00:00.000Z",
  "version": "1.0.0"
}
```

#### 2. Readiness Check (`/health/ready`)

**Purpose**: Verify service is ready to accept traffic  
**Use Case**: Kubernetes readiness probe  
**Checks**: Database connectivity, external services

```bash
curl http://localhost:5000/health/ready
```

**Response** (Healthy):
```json
{
  "status": "healthy",
  "timestamp": "2025-10-06T12:00:00.000Z",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "Database connection successful",
      "latency_ms": 15
    },
    "external_services": {
      "sendgrid": {"status": "healthy", "available": true},
      "twilio": {"status": "healthy", "available": true},
      "pusher": {"status": "healthy", "available": true},
      "callrail": {"status": "healthy", "available": true}
    }
  }
}
```

**Response** (Degraded - 503):
```json
{
  "status": "degraded",
  "timestamp": "2025-10-06T12:00:00.000Z",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "Database connection successful"
    },
    "external_services": {
      "sendgrid": {
        "status": "degraded",
        "available": false,
        "message": "API key not configured"
      }
    }
  }
}
```

#### 3. Liveness Check (`/health/live`)

**Purpose**: Verify process is alive and responsive  
**Use Case**: Kubernetes liveness probe  
**Response Time**: < 10ms

```bash
curl http://localhost:5000/health/live
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-06T12:00:00.000Z"
}
```

### Kubernetes Configuration

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: crm-api
    image: iswitchroofs/crm-api:latest
    livenessProbe:
      httpGet:
        path: /health/live
        port: 5000
      initialDelaySeconds: 30
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /health/ready
        port: 5000
      initialDelaySeconds: 10
      periodSeconds: 5
      timeoutSeconds: 3
      failureThreshold: 3
```

## Structured Logging

### Log Formats

#### Development (Colored Console)

```
2025-10-06 12:00:00 [INFO] app.routes.leads: Lead created successfully | POST /api/leads
```

#### Production (JSON)

```json
{
  "timestamp": "2025-10-06T12:00:00.000Z",
  "level": "INFO",
  "logger": "app.routes.leads",
  "message": "Lead created successfully",
  "module": "leads",
  "function": "create_lead",
  "line": 45,
  "request": {
    "method": "POST",
    "path": "/api/leads",
    "remote_addr": "192.168.1.1",
    "user_agent": "Mozilla/5.0..."
  }
}
```

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: Confirmation that things are working
- **WARNING**: Something unexpected but handled
- **ERROR**: Error that prevented an operation
- **CRITICAL**: Serious error, application may fail

### Configuration

```python
# In .env or config
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DIR=logs    # Directory for log files
```

### Log Files

- **logs/application.log** - All logs (rotated at 10MB, 10 backups)
- **logs/errors.log** - Errors only (rotated at 10MB, 10 backups)

### Custom Logging

```python
from app.logging_config import get_logger

logger = get_logger(__name__)

# Basic logging
logger.info("Operation completed successfully")
logger.error("Failed to process request", exc_info=True)

# With extra context
logger.info(
    "Lead created",
    extra={
        "lead_id": lead.id,
        "customer_name": lead.name,
        "source": lead.source
    }
)

# Using context manager
from app.logging_config import LogContext

with LogContext(logger, customer_id="12345", operation="create_lead"):
    logger.info("Processing lead")  # Automatically includes context
```

### Specialized Loggers

```python
from app.logging_config import (
    log_api_call,
    log_database_query,
    log_external_service_call,
    log_business_event
)

# API call logging
log_api_call("/api/leads", "POST", 201, 145.5)

# Database query logging
log_database_query("SELECT * FROM leads WHERE status = 'new'", 25.3, 150)

# External service logging
log_external_service_call("twilio", "send_sms", True, 234.5)

# Business event logging
log_business_event("lead_created", lead_id, {"source": "website", "score": 85})
```

## Performance Monitoring

### Automatic Tracking

All API requests are automatically tracked with:
- Request count
- Error count and rate
- Response times (average, p50, p95, p99)
- Per-endpoint metrics

### Manual Performance Tracking

```python
from app.monitoring import performance_tracking

@app.route('/api/leads')
@performance_tracking
def get_leads():
    # Endpoint automatically tracked
    return jsonify(leads)
```

### Metrics Endpoint

```bash
curl http://localhost:5000/metrics
```

**Response**:
```json
{
  "timestamp": "2025-10-06T12:00:00.000Z",
  "application": {
    "requests": {
      "total": 1523,
      "errors": 12,
      "error_rate": 0.008
    },
    "response_times": {
      "average": 0.234,
      "p50": 0.145,
      "p95": 0.567,
      "p99": 1.234
    },
    "uptime_seconds": 86400
  },
  "endpoints": {
    "/api/leads": {
      "requests": 450,
      "errors": 3,
      "avg_response_time": 0.189
    },
    "/api/customers": {
      "requests": 320,
      "errors": 1,
      "avg_response_time": 0.215
    }
  },
  "system": {
    "cpu": {
      "usage_percent": 45.2,
      "count": 4
    },
    "memory": {
      "total_mb": 8192,
      "available_mb": 4096,
      "used_mb": 4096,
      "percent": 50.0
    },
    "disk": {
      "total_gb": 100,
      "used_gb": 45,
      "free_gb": 55,
      "percent": 45.0
    }
  }
}
```

### Slow Request Detection

Requests taking > 1 second are automatically logged as warnings:

```
2025-10-06 12:00:00 [WARNING] app.monitoring: Slow request detected: /api/leads/statistics took 1.45s
```

## UptimeRobot Integration

### Setup

```bash
# Configure in .env
UPTIMEROBOT_API_KEY=m801526410-ccbf950ab78bc4ec4d2290ca
APP_BASE_URL=https://api.iswitchroofs.com

# Run setup script
python backend/app/uptimerobot_setup.py
```

### Configured Monitors

1. **Main Health Check** (5 min intervals)
   - URL: `/health`
   - Method: HEAD
   - Expected: 200 OK

2. **Readiness Check** (5 min intervals)
   - URL: `/health/ready`
   - Method: GET
   - Expected: 200 OK

3. **API Liveness** (3 min intervals)
   - URL: `/health/live`
   - Method: HEAD
   - Expected: 200 OK

4. **Lead API** (10 min intervals)
   - URL: `/api/leads`
   - Method: HEAD
   - Expected: 200 OK

5. **Metrics Endpoint** (10 min intervals)
   - URL: `/metrics`
   - Method: GET
   - Expected: 200 OK

### Programmatic Access

```python
from app.uptimerobot_setup import UptimeRobotClient

client = UptimeRobotClient(api_key)

# Get all monitors
monitors = client.get_monitors()

# Create monitor
client.create_monitor(
    friendly_name="My API",
    url="https://api.example.com/health",
    interval=300
)

# Update monitor
client.update_monitor(monitor_id, interval=600)

# Delete monitor
client.delete_monitor(monitor_id)
```

## Metrics Collection

### Available Metrics

#### Application Metrics
- Request count
- Error count and rate
- Response time percentiles
- Uptime duration

#### Endpoint Metrics
- Per-endpoint request count
- Per-endpoint error count
- Per-endpoint average response time

#### System Metrics
- CPU usage (percent and core count)
- Memory usage (total, used, available, percent)
- Disk usage (total, used, free, percent)

### Accessing Metrics

```bash
# Get all metrics
curl http://localhost:5000/metrics

# Filter with jq
curl -s http://localhost:5000/metrics | jq '.application.requests'
curl -s http://localhost:5000/metrics | jq '.endpoints["/api/leads"]'
curl -s http://localhost:5000/metrics | jq '.system.memory'
```

### Grafana Integration (Future)

Metrics endpoint can be scraped by Prometheus and visualized in Grafana:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'iswitch-crm'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['api.iswitchroofs.com:5000']
```

## Alerting

### Sentry Alerts

Configure alerts in Sentry dashboard:

1. **Error Rate Spike**: Alert when error rate > 5%
2. **New Error Type**: Alert on first occurrence of new error
3. **Performance Degradation**: Alert when p95 > 2 seconds
4. **High Volume**: Alert when request volume increases 200%

### UptimeRobot Alerts

Configure alert contacts in UptimeRobot:

1. **Email Alerts**: Send to ops@iswitchroofs.com
2. **SMS Alerts**: Send to on-call engineer
3. **Webhook**: POST to Slack channel
4. **Alert Threshold**: 2 consecutive failures

### Custom Alerts

```python
import sentry_sdk

def check_critical_metric():
    if metric_value > threshold:
        sentry_sdk.capture_message(
            "Critical metric exceeded threshold",
            level="warning",
            extras={"metric": metric_name, "value": metric_value}
        )
```

## Troubleshooting

### Common Issues

#### 1. Sentry Not Receiving Errors

**Symptoms**: Errors not appearing in Sentry dashboard

**Solutions**:
```bash
# Check DSN is configured
echo $SENTRY_DSN

# Test Sentry connection
python -c "import sentry_sdk; sentry_sdk.init('YOUR_DSN'); sentry_sdk.capture_message('test')"

# Check logs for Sentry errors
grep -i sentry logs/application.log
```

#### 2. Health Checks Failing

**Symptoms**: `/health/ready` returns 503

**Solutions**:
```bash
# Check database connectivity
curl http://localhost:5000/health/ready | jq '.checks.database'

# Check external services
curl http://localhost:5000/health/ready | jq '.checks.external_services'

# Test database directly
psql $DATABASE_URL -c "SELECT 1"
```

#### 3. High Memory Usage

**Symptoms**: System metrics show memory > 90%

**Solutions**:
```bash
# Check metrics
curl http://localhost:5000/metrics | jq '.system.memory'

# Restart application
systemctl restart iswitch-crm

# Check for memory leaks in logs
grep -i "memory" logs/application.log
```

#### 4. Slow Requests

**Symptoms**: Response times > 1 second

**Solutions**:
```bash
# Check slow requests in logs
grep "Slow request" logs/application.log

# Check endpoint metrics
curl http://localhost:5000/metrics | jq '.endpoints'

# Enable query logging
LOG_LEVEL=DEBUG python run.py
```

### Log Analysis

```bash
# View recent errors
tail -f logs/errors.log

# Count errors by type
grep "ERROR" logs/application.log | cut -d: -f2 | sort | uniq -c | sort -rn

# Find slowest endpoints
grep "Slow request" logs/application.log | awk '{print $NF}' | sort | uniq -c | sort -rn

# Monitor in real-time
tail -f logs/application.log | grep -i error
```

## Best Practices

### 1. Error Handling

```python
try:
    risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {str(e)}", exc_info=True)
    sentry_sdk.capture_exception(e)
    return {"error": "Operation failed"}, 500
```

### 2. Performance Tracking

```python
import time

start_time = time.time()
result = expensive_operation()
duration = time.time() - start_time

logger.info(f"Operation completed in {duration:.2f}s")

if duration > 1.0:
    logger.warning(f"Slow operation: {duration:.2f}s")
```

### 3. Context Enrichment

```python
with sentry_sdk.push_scope() as scope:
    scope.set_user({"id": user.id, "email": user.email})
    scope.set_tag("customer_type", customer.tier)
    scope.set_context("business", {
        "lead_id": lead.id,
        "source": lead.source,
        "value": lead.estimated_value
    })
    
    # All errors now include this context
    process_lead(lead)
```

### 4. Structured Logging

```python
# Good
logger.info("Lead created", extra={
    "lead_id": lead.id,
    "source": lead.source,
    "score": lead.score
})

# Bad
logger.info(f"Lead {lead.id} created from {lead.source} with score {lead.score}")
```

## Next Steps

1. **Set up Grafana** for metrics visualization
2. **Configure PagerDuty** for on-call alerting
3. **Implement custom metrics** for business KPIs
4. **Add distributed tracing** with OpenTelemetry
5. **Set up log aggregation** with Datadog or ELK stack

## References

- [Sentry Documentation](https://docs.sentry.io/)
- [UptimeRobot API](https://uptimerobot.com/api/)
- [Flask Logging](https://flask.palletsprojects.com/en/latest/logging/)
- [Kubernetes Health Checks](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
