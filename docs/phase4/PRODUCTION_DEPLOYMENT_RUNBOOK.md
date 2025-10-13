# Production Deployment Runbook - ML System

**iSwitch Roofs CRM - Phase 4 ML System**

**Version**: 1.0.0
**Last Updated**: October 11, 2025
**Deployment Target**: Week 9 - Day 1

---

## 🎯 Deployment Overview

**Objective**: Deploy Week 8 ML system to production with zero downtime and complete rollback capability.

**Components to Deploy**:
1. ML API (FastAPI) - 6 endpoints
2. Streamlit Dashboard - Advanced analytics
3. n8n Workflows - 5 automation workflows
4. Redis Cache - Performance layer
5. Database Migrations - Schema updates

**Deployment Strategy**: Blue-Green deployment with automated rollback

**Target Infrastructure**:
- **Cloud Provider**: AWS (primary) or GCP (alternative)
- **Region**: US-East-1 (primary), US-West-2 (DR)
- **Deployment Time**: ~2 hours
- **Rollback Time**: <5 minutes

---

## ✅ Pre-Deployment Checklist

### 1. Infrastructure Verification

**AWS Resources** (verify all exist):
- [ ] VPC with public/private subnets configured
- [ ] Security groups with proper ingress/egress rules
- [ ] Application Load Balancer (ALB) provisioned
- [ ] Target groups (blue & green) created
- [ ] Auto Scaling Groups (ASG) configured
- [ ] S3 bucket for model artifacts
- [ ] ElastiCache Redis cluster (2 nodes, Multi-AZ)
- [ ] RDS PostgreSQL or Supabase production tier
- [ ] CloudWatch alarms configured
- [ ] IAM roles and policies set up
- [ ] SSL/TLS certificates issued (ACM)
- [ ] Route 53 DNS records configured

**Verification Commands**:
```bash
# Check VPC
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=iswitch-ml-vpc"

# Check Load Balancer
aws elbv2 describe-load-balancers --names iswitch-ml-lb

# Check ElastiCache
aws elasticache describe-cache-clusters --cache-cluster-id iswitch-ml-redis

# Check security groups
aws ec2 describe-security-groups --group-names iswitch-ml-api-sg
```

---

### 2. Code & Configuration Preparation

**Code Repository**:
- [ ] All code merged to `main` branch
- [ ] Git tag created: `v1.0.0-production`
- [ ] Changelog updated with all changes
- [ ] No uncommitted changes in repository

**Environment Variables**:
- [ ] Production `.env` file created (DO NOT commit)
- [ ] All secrets stored in AWS Secrets Manager or Parameter Store
- [ ] Environment-specific configs validated

**Production `.env` Template**:
```bash
# ML API Configuration
ML_API_PORT=8000
ML_API_HOST=0.0.0.0
ENVIRONMENT=production
LOG_LEVEL=INFO

# Database (Supabase)
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_KEY=<production-anon-key>
SUPABASE_SERVICE_KEY=<production-service-key>
DATABASE_URL=postgresql://postgres:<password>@db.yourproject.supabase.co:5432/postgres

# Redis Cache
REDIS_HOST=iswitch-ml-redis.abc123.use1.cache.amazonaws.com
REDIS_PORT=6379
REDIS_PASSWORD=<redis-password>
REDIS_SSL=true

# OpenAI
OPENAI_API_KEY=<production-key>
OPENAI_ORG_ID=<org-id>

# Model Storage
MODEL_STORAGE_PATH=/opt/ml/models
MODEL_BACKUP_S3=s3://iswitch-ml-models/backups/

# Monitoring
SENTRY_DSN=<sentry-dsn>
PROMETHEUS_PORT=9090

# n8n
N8N_ENCRYPTION_KEY=<encryption-key>
N8N_WEBHOOK_URL=https://n8n.iswitch-roofs.com
```

**Docker Images**:
- [ ] ML API Docker image built and tagged
- [ ] Image pushed to ECR (Elastic Container Registry)
- [ ] Image scanned for vulnerabilities
- [ ] Image size optimized (<500MB)

**Build Commands**:
```bash
# Build ML API image
docker build -t iswitch-ml-api:v1.0.0 -f backend/Dockerfile.ml .

# Tag for ECR
docker tag iswitch-ml-api:v1.0.0 123456789.dkr.ecr.us-east-1.amazonaws.com/iswitch-ml-api:v1.0.0
docker tag iswitch-ml-api:v1.0.0 123456789.dkr.ecr.us-east-1.amazonaws.com/iswitch-ml-api:latest

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

# Push to ECR
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/iswitch-ml-api:v1.0.0
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/iswitch-ml-api:latest
```

---

### 3. Database Preparation

**Schema Migrations**:
- [ ] All migration scripts reviewed
- [ ] Migrations tested on staging database
- [ ] Rollback scripts prepared
- [ ] Backup taken before migration

**Migration Scripts Location**: `backend/migrations/`

**Backup Database**:
```bash
# Supabase backup (via CLI)
supabase db dump -f backup_pre_ml_deployment_$(date +%Y%m%d).sql

# Or manual backup
pg_dump -h db.yourproject.supabase.co -U postgres -d postgres > backup_$(date +%Y%m%d).sql
```

**Run Migrations**:
```bash
# Apply migrations
psql $DATABASE_URL -f backend/migrations/001_ml_predictions_table.sql
psql $DATABASE_URL -f backend/migrations/002_ml_training_logs.sql
psql $DATABASE_URL -f backend/migrations/003_performance_indexes.sql

# Verify migrations
psql $DATABASE_URL -c "\dt+" | grep ml_
```

**Required Tables**:
1. `ml_predictions` - Prediction history
2. `ml_training_logs` - Training job tracking
3. `ml_drift_logs` - Model drift monitoring
4. `ab_experiments` - A/B testing data
5. `ab_experiment_results` - Experiment outcomes

---

### 4. Model Artifacts

**Model Files**:
- [ ] Production models uploaded to S3
- [ ] Model metadata JSON files included
- [ ] Model versioning scheme implemented
- [ ] Checksums verified for integrity

**Upload Models to S3**:
```bash
# Upload current production model
aws s3 cp models/nba_model_v1.0.joblib s3://iswitch-ml-models/production/nba_model_v1.0.joblib
aws s3 cp models/nba_model_v1.0_metadata.json s3://iswitch-ml-models/production/nba_model_v1.0_metadata.json

# Set proper permissions
aws s3api put-object-acl --bucket iswitch-ml-models --key production/nba_model_v1.0.joblib --acl private

# Verify upload
aws s3 ls s3://iswitch-ml-models/production/
```

**Model Versioning Structure**:
```
s3://iswitch-ml-models/
├── production/
│   ├── nba_model_v1.0.joblib
│   ├── nba_model_v1.0_metadata.json
│   └── current -> nba_model_v1.0.joblib (symlink)
├── staging/
│   └── nba_model_v1.1_beta.joblib
└── backups/
    ├── 2025-10-11/
    │   └── nba_model_v1.0.joblib
    └── 2025-10-10/
        └── nba_model_v0.9.joblib
```

---

### 5. Secrets Management

**AWS Secrets Manager**:
- [ ] All secrets created in Secrets Manager
- [ ] IAM policies grant EC2 instances read access
- [ ] Secrets rotation configured (90 days)

**Create Secrets**:
```bash
# Supabase credentials
aws secretsmanager create-secret \
  --name iswitch/ml/supabase \
  --secret-string '{"url":"https://...","key":"...","service_key":"..."}'

# OpenAI API key
aws secretsmanager create-secret \
  --name iswitch/ml/openai \
  --secret-string '{"api_key":"sk-...","org_id":"org-..."}'

# Redis password
aws secretsmanager create-secret \
  --name iswitch/ml/redis \
  --secret-string '{"password":"..."}'

# n8n encryption key
aws secretsmanager create-secret \
  --name iswitch/ml/n8n \
  --secret-string '{"encryption_key":"..."}'
```

**Application Retrieval** (in code):
```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage
supabase_creds = get_secret('iswitch/ml/supabase')
SUPABASE_URL = supabase_creds['url']
SUPABASE_KEY = supabase_creds['key']
```

---

### 6. Testing & Validation

**Staging Environment Tests**:
- [ ] All 6 ML API endpoints tested
- [ ] Streamlit dashboard loads correctly
- [ ] n8n workflows execute successfully
- [ ] End-to-end integration test passed
- [ ] Load testing completed (100 req/sec sustained)
- [ ] Security scan passed (no critical vulnerabilities)

**Load Testing** (using Apache Bench or k6):
```bash
# Test ML API prediction endpoint
ab -n 1000 -c 10 -p test_payload.json -T application/json \
  https://staging-ml-api.iswitch-roofs.com/api/v1/ml/predict/nba

# Expected results:
# - Requests per second: >100
# - Mean response time: <100ms
# - 95th percentile: <200ms
# - Error rate: <0.1%
```

**Integration Test**:
```bash
# Run full integration test suite
pytest backend/tests/integration/ --env=staging -v

# Expected: All tests pass (20/20)
```

---

## 🚀 Deployment Procedure

### Step 1: Prepare Green Environment (30 minutes)

**1.1 Launch Green EC2 Instances**:
```bash
# Launch 2 instances for ML API (green environment)
aws ec2 run-instances \
  --image-id ami-0abcdef1234567890 \
  --count 2 \
  --instance-type t3.xlarge \
  --key-name iswitch-ml-key \
  --security-group-ids sg-0123456789abcdef0 \
  --subnet-id subnet-0123456789abcdef0 \
  --iam-instance-profile Name=iswitch-ml-role \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=iswitch-ml-api-green},{Key=Environment,Value=production},{Key=Color,Value=green}]' \
  --user-data file://scripts/user-data-ml-api.sh

# Wait for instances to be running
aws ec2 wait instance-running --instance-ids i-0123456789abcdef0 i-0123456789abcdef1
```

**1.2 User Data Script** (`scripts/user-data-ml-api.sh`):
```bash
#!/bin/bash
set -e

# Update system
yum update -y

# Install Docker
amazon-linux-extras install docker -y
service docker start
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

# Pull ML API image
docker pull 123456789.dkr.ecr.us-east-1.amazonaws.com/iswitch-ml-api:v1.0.0

# Download model artifacts from S3
mkdir -p /opt/ml/models
aws s3 cp s3://iswitch-ml-models/production/nba_model_v1.0.joblib /opt/ml/models/
aws s3 cp s3://iswitch-ml-models/production/nba_model_v1.0_metadata.json /opt/ml/models/

# Retrieve secrets and create .env file
aws secretsmanager get-secret-value --secret-id iswitch/ml/supabase --query SecretString --output text > /tmp/supabase.json
aws secretsmanager get-secret-value --secret-id iswitch/ml/openai --query SecretString --output text > /tmp/openai.json
aws secretsmanager get-secret-value --secret-id iswitch/ml/redis --query SecretString --output text > /tmp/redis.json

cat > /opt/ml/.env <<EOF
ML_API_PORT=8000
ENVIRONMENT=production
SUPABASE_URL=$(jq -r .url /tmp/supabase.json)
SUPABASE_KEY=$(jq -r .key /tmp/supabase.json)
REDIS_HOST=$(jq -r .host /tmp/redis.json)
REDIS_PASSWORD=$(jq -r .password /tmp/redis.json)
OPENAI_API_KEY=$(jq -r .api_key /tmp/openai.json)
MODEL_STORAGE_PATH=/opt/ml/models
EOF

# Start ML API container
docker run -d \
  --name ml-api \
  --restart unless-stopped \
  -p 8000:8000 \
  -v /opt/ml/models:/opt/ml/models \
  --env-file /opt/ml/.env \
  123456789.dkr.ecr.us-east-1.amazonaws.com/iswitch-ml-api:v1.0.0

# Wait for health check
for i in {1..30}; do
  if curl -f http://localhost:8000/api/v1/ml/health; then
    echo "ML API healthy"
    break
  fi
  sleep 2
done

# Clean up sensitive files
rm /tmp/*.json
```

**1.3 Verify Green Environment**:
```bash
# Get green instance IPs
GREEN_IPS=$(aws ec2 describe-instances \
  --filters "Name=tag:Color,Values=green" "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].PrivateIpAddress' \
  --output text)

# Test each instance
for ip in $GREEN_IPS; do
  echo "Testing $ip..."
  curl -f http://$ip:8000/api/v1/ml/health
  curl -f http://$ip:8000/api/v1/ml/metrics
done
```

---

### Step 2: Register Green Instances with Target Group (10 minutes)

**2.1 Register Targets**:
```bash
# Get green target group ARN
GREEN_TG_ARN=$(aws elbv2 describe-target-groups \
  --names iswitch-ml-green-tg \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

# Register green instances
aws elbv2 register-targets \
  --target-group-arn $GREEN_TG_ARN \
  --targets Id=i-0123456789abcdef0 Id=i-0123456789abcdef1
```

**2.2 Wait for Health Checks**:
```bash
# Monitor target health
aws elbv2 describe-target-health \
  --target-group-arn $GREEN_TG_ARN

# Expected output: All targets "healthy"
# Wait up to 5 minutes for health checks to pass
```

---

### Step 3: Smoke Testing on Green (15 minutes)

**3.1 Test All Endpoints**:
```bash
# Get ALB DNS (with green targets)
ALB_DNS="iswitch-ml-lb-123456789.us-east-1.elb.amazonaws.com"

# Test health endpoint
curl https://$ALB_DNS/api/v1/ml/health

# Test metrics endpoint
curl https://$ALB_DNS/api/v1/ml/metrics

# Test NBA prediction
curl -X POST https://$ALB_DNS/api/v1/ml/predict/nba \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": "smoke-test-001",
    "source": "website",
    "created_at": "2025-10-11T10:00:00",
    "property_zip": "48304",
    "estimated_value": 850000
  }'

# Test batch prediction
curl -X POST https://$ALB_DNS/api/v1/ml/predict/nba/batch \
  -H "Content-Type: application/json" \
  -d '{"leads": [...]}'

# Test model reload
curl -X POST https://$ALB_DNS/api/v1/ml/reload
```

**3.2 Verify Responses**:
- ✅ Health check returns `{"status": "healthy", "model_loaded": true}`
- ✅ Metrics return valid data with 87% accuracy
- ✅ Predictions return valid NBA actions with confidence scores
- ✅ Batch predictions process 100 leads in <10 seconds
- ✅ Model reload succeeds without errors

---

### Step 4: Switch Traffic to Green (5 minutes)

**4.1 Modify Load Balancer Listener**:
```bash
# Get listener ARN
LISTENER_ARN=$(aws elbv2 describe-listeners \
  --load-balancer-arn $LB_ARN \
  --query 'Listeners[0].ListenerArn' \
  --output text)

# Switch to green target group
aws elbv2 modify-listener \
  --listener-arn $LISTENER_ARN \
  --default-actions Type=forward,TargetGroupArn=$GREEN_TG_ARN

echo "Traffic switched to GREEN environment at $(date)"
```

**4.2 Monitor Traffic Switch**:
```bash
# Watch CloudWatch metrics for 5 minutes
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --dimensions Name=TargetGroup,Value=$GREEN_TG_ARN \
  --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average
```

---

### Step 5: Monitor Green Environment (30 minutes)

**5.1 Real-Time Monitoring**:
```bash
# Monitor error rate
watch -n 10 'aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name HTTPCode_Target_5XX_Count \
  --dimensions Name=TargetGroup,Value=$GREEN_TG_ARN \
  --start-time $(date -u -d "1 minute ago" +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Sum'

# Expected: 0 errors in first 30 minutes
```

**5.2 Application Logs**:
```bash
# Stream logs from CloudWatch Logs
aws logs tail /aws/ec2/ml-api --follow --filter-pattern "ERROR"

# Expected: No ERROR logs
```

**5.3 Success Criteria** (all must pass):
- ✅ Error rate <0.1% for 30 minutes
- ✅ Average response time <100ms
- ✅ P95 response time <200ms
- ✅ No application errors in logs
- ✅ All health checks passing
- ✅ Prediction accuracy maintained (87%)

---

### Step 6: Decommission Blue Environment (10 minutes)

**6.1 Only if Step 5 succeeds**:
```bash
# Deregister blue targets
BLUE_TG_ARN=$(aws elbv2 describe-target-groups \
  --names iswitch-ml-blue-tg \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

aws elbv2 deregister-targets \
  --target-group-arn $BLUE_TG_ARN \
  --targets Id=i-blue1 Id=i-blue2

# Wait for connection draining (300 seconds)
sleep 300

# Terminate blue instances
aws ec2 terminate-instances --instance-ids i-blue1 i-blue2

echo "Blue environment decommissioned at $(date)"
```

**6.2 Update DNS** (if using Route 53):
```bash
# Update A record to point to green ALB
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789ABC \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "ml-api.iswitch-roofs.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z35SXDOTRQ7X7K",
          "DNSName": "'$ALB_DNS'",
          "EvaluateTargetHealth": true
        }
      }
    }]
  }'
```

---

## 🔄 Rollback Procedure

**Trigger Conditions** (rollback if any occur):
- Error rate >1% for 5 consecutive minutes
- P95 latency >500ms for 5 consecutive minutes
- Prediction accuracy drops >10%
- Critical application errors in logs
- Database connection failures

**Automated Rollback** (`scripts/rollback.sh`):
```bash
#!/bin/bash
set -e

echo "INITIATING ROLLBACK at $(date)"

# Get blue target group ARN
BLUE_TG_ARN=$(aws elbv2 describe-target-groups \
  --names iswitch-ml-blue-tg \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

# Get listener ARN
LISTENER_ARN=$(aws elbv2 describe-listeners \
  --load-balancer-arn $LB_ARN \
  --query 'Listeners[0].ListenerArn' \
  --output text)

# Switch traffic back to blue
aws elbv2 modify-listener \
  --listener-arn $LISTENER_ARN \
  --default-actions Type=forward,TargetGroupArn=$BLUE_TG_ARN

echo "Traffic switched back to BLUE at $(date)"

# Verify blue health
for i in {1..30}; do
  HEALTH=$(aws elbv2 describe-target-health \
    --target-group-arn $BLUE_TG_ARN \
    --query 'TargetHealthDescriptions[0].TargetHealth.State' \
    --output text)

  if [ "$HEALTH" == "healthy" ]; then
    echo "Rollback successful - Blue environment healthy"
    exit 0
  fi
  sleep 2
done

echo "ROLLBACK FAILED - Manual intervention required"
exit 1
```

**Manual Rollback Steps**:
1. SSH to blue instances: `ssh -i iswitch-ml-key.pem ec2-user@<blue-ip>`
2. Check application status: `docker ps`, `docker logs ml-api`
3. Restart if needed: `docker restart ml-api`
4. Modify listener to point to blue target group (see script above)
5. Notify team via Slack: "Production rollback completed"

---

## 📊 Post-Deployment Validation

### 1. Functional Testing (30 minutes)

**Test Checklist**:
- [ ] Health endpoint responding correctly
- [ ] All 6 ML endpoints operational
- [ ] Predictions returning accurate results
- [ ] Model accuracy maintained (87%)
- [ ] Batch processing working (1,000 leads in <3 min)
- [ ] Enhanced predictions with GPT-5 working
- [ ] Cache hit rate >30%
- [ ] Database writes succeeding
- [ ] n8n workflows triggered successfully

**Test Script** (`scripts/post-deployment-test.sh`):
```bash
#!/bin/bash

API_URL="https://ml-api.iswitch-roofs.com"
PASSED=0
FAILED=0

# Test 1: Health Check
echo "Test 1: Health Check"
RESPONSE=$(curl -s $API_URL/api/v1/ml/health)
if echo $RESPONSE | jq -e '.status == "healthy"' > /dev/null; then
  echo "✅ PASSED"
  ((PASSED++))
else
  echo "❌ FAILED"
  ((FAILED++))
fi

# Test 2: Metrics
echo "Test 2: Metrics"
RESPONSE=$(curl -s $API_URL/api/v1/ml/metrics)
ACCURACY=$(echo $RESPONSE | jq -r '.accuracy')
if (( $(echo "$ACCURACY >= 0.80" | bc -l) )); then
  echo "✅ PASSED (Accuracy: $ACCURACY)"
  ((PASSED++))
else
  echo "❌ FAILED (Accuracy: $ACCURACY)"
  ((FAILED++))
fi

# Test 3: NBA Prediction
echo "Test 3: NBA Prediction"
RESPONSE=$(curl -s -X POST $API_URL/api/v1/ml/predict/nba \
  -H "Content-Type: application/json" \
  -d '{"lead_id":"test-001","source":"website","created_at":"2025-10-11T10:00:00","property_zip":"48304","estimated_value":850000}')
ACTION=$(echo $RESPONSE | jq -r '.action')
if [ ! -z "$ACTION" ] && [ "$ACTION" != "null" ]; then
  echo "✅ PASSED (Action: $ACTION)"
  ((PASSED++))
else
  echo "❌ FAILED"
  ((FAILED++))
fi

# ... more tests ...

echo ""
echo "========================================="
echo "Test Results: $PASSED passed, $FAILED failed"
echo "========================================="

if [ $FAILED -gt 0 ]; then
  exit 1
else
  exit 0
fi
```

---

### 2. Performance Validation (1 hour)

**Load Test** (using k6):
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '5m', target: 50 },   // Ramp up to 50 users
    { duration: '10m', target: 100 },  // Ramp up to 100 users
    { duration: '5m', target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'],  // 95% under 200ms
    http_req_failed: ['rate<0.01'],     // Error rate <1%
  },
};

export default function () {
  const payload = JSON.stringify({
    lead_id: `test-${__VU}-${__ITER}`,
    source: 'website',
    created_at: new Date().toISOString(),
    property_zip: '48304',
    estimated_value: 850000,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  let res = http.post(
    'https://ml-api.iswitch-roofs.com/api/v1/ml/predict/nba',
    payload,
    params
  );

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
    'has action': (r) => JSON.parse(r.body).action !== undefined,
  });

  sleep(1);
}
```

**Run Load Test**:
```bash
k6 run load-test.js

# Expected results:
# ✓ http_req_duration..........: avg=89ms  min=45ms med=78ms max=198ms p(95)=156ms
# ✓ http_req_failed............: 0.02%   ✓ 4    ✗ 19996
# ✓ checks.....................: 99.98%  ✓ 59994 ✗ 6
```

---

### 3. Business Validation (2 hours)

**Real Lead Testing**:
- [ ] Process 100 real leads from CRM
- [ ] Verify predictions are accurate
- [ ] Check conversion tracking
- [ ] Validate CRM updates
- [ ] Confirm Slack notifications sent

**Sales Team Validation**:
- [ ] Demo dashboard to sales team
- [ ] Verify VIP lead alerts received
- [ ] Test strategic playbook emails
- [ ] Confirm talking points are relevant
- [ ] Validate recommended actions make sense

---

## 📈 Monitoring & Alerting

### CloudWatch Alarms

**Create Critical Alarms**:
```bash
# API Error Rate Alarm
aws cloudwatch put-metric-alarm \
  --alarm-name ml-api-error-rate-critical \
  --alarm-description "Alert when error rate >1%" \
  --metric-name HTTPCode_Target_5XX_Count \
  --namespace AWS/ApplicationELB \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:123456789:ml-alerts

# High Latency Alarm
aws cloudwatch put-metric-alarm \
  --alarm-name ml-api-latency-warning \
  --alarm-description "Alert when P95 latency >200ms" \
  --metric-name TargetResponseTime \
  --namespace AWS/ApplicationELB \
  --statistic Average \
  --period 300 \
  --threshold 0.2 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 3 \
  --alarm-actions arn:aws:sns:us-east-1:123456789:ml-alerts
```

### Slack Notifications

**Configure SNS → Slack Integration**:
```bash
# Create SNS topic
aws sns create-topic --name ml-production-alerts

# Subscribe Slack webhook
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789:ml-production-alerts \
  --protocol https \
  --notification-endpoint https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXX
```

---

## 📝 Post-Deployment Checklist

**Immediate (Within 1 Hour)**:
- [ ] All tests passing
- [ ] Monitoring dashboards showing healthy metrics
- [ ] No errors in application logs
- [ ] Sales team notified of go-live
- [ ] Documentation updated with production URLs

**Within 24 Hours**:
- [ ] Review first 24 hours of metrics
- [ ] Address any minor issues discovered
- [ ] Gather user feedback
- [ ] Update runbook with lessons learned
- [ ] Schedule retrospective meeting

**Within 1 Week**:
- [ ] Comprehensive performance review
- [ ] Cost analysis (infrastructure spend)
- [ ] Business impact assessment (conversions, revenue)
- [ ] Plan optimization opportunities
- [ ] Document best practices

---

## 🆘 Emergency Contacts

**On-Call Rotation**:
- **Week 1**: DevOps Lead - John Doe - +1-555-0100 - john@iswitch-roofs.com
- **Week 2**: ML Engineer - Jane Smith - +1-555-0101 - jane@iswitch-roofs.com
- **Week 3**: Platform Engineer - Bob Johnson - +1-555-0102 - bob@iswitch-roofs.com

**Escalation Path**:
1. On-call engineer (respond within 15 minutes)
2. Engineering Manager (if unresolved in 30 minutes)
3. CTO (if critical business impact)

**Support Channels**:
- **Slack**: #ml-production-alerts (critical alerts)
- **Slack**: #ml-support (general issues)
- **PagerDuty**: ML Production team
- **Email**: ml-ops@iswitch-roofs.com

---

## 📚 Additional Resources

**Documentation**:
- [Week 8 Final Summary](./WEEK_8_FINAL_COMPLETE.md)
- [ML API Reference](../backend/ML_API_QUICK_START.md)
- [n8n Workflow Guide](../backend/workflows/n8n/README.md)
- [Monitoring Dashboard](https://grafana.iswitch-roofs.com)

**Runbooks**:
- [Incident Response Playbook](./INCIDENT_RESPONSE.md)
- [Database Maintenance Guide](./DATABASE_MAINTENANCE.md)
- [Model Retraining Procedures](./MODEL_RETRAINING.md)
- [Scaling Guide](./SCALING_GUIDE.md)

---

**Last Updated**: October 11, 2025
**Version**: 1.0.0
**Next Review**: October 18, 2025
