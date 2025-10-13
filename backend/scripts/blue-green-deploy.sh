#!/bin/bash

################################################################################
# Blue-Green Deployment Script for iSwitch Roofs ML System
#
# This script performs a zero-downtime deployment using blue-green strategy:
# 1. Deploys new version to green environment
# 2. Runs health checks on green
# 3. Switches load balancer to green
# 4. Monitors for issues
# 5. Decommissions blue OR rolls back if issues detected
#
# Usage: ./blue-green-deploy.sh <version>
# Example: ./blue-green-deploy.sh v1.0.1
#
# Environment Variables Required:
# - AWS_REGION: AWS region (default: us-east-1)
# - ECR_REGISTRY: ECR registry URL
# - LB_ARN: Load balancer ARN
# - GREEN_TG_ARN: Green target group ARN
# - BLUE_TG_ARN: Blue target group ARN
# - SLACK_WEBHOOK: Slack webhook URL for notifications
################################################################################

set -e  # Exit on any error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VERSION=${1:-latest}
AWS_REGION=${AWS_REGION:-us-east-1}
ECR_REGISTRY=${ECR_REGISTRY:-123456789.dkr.ecr.us-east-1.amazonaws.com}
IMAGE_NAME="iswitch-ml-api"
HEALTH_CHECK_RETRIES=30
HEALTH_CHECK_INTERVAL=2
MONITORING_DURATION=300  # 5 minutes
ERROR_THRESHOLD=1.0      # 1% error rate
LATENCY_THRESHOLD=500    # 500ms P95

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Slack notification function
notify_slack() {
    local message=$1
    local color=${2:-good}  # good, warning, danger

    if [ -n "${SLACK_WEBHOOK:-}" ]; then
        curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"ML API Deployment\",
                    \"text\": \"$message\",
                    \"footer\": \"Version: $VERSION\",
                    \"ts\": $(date +%s)
                }]
            }" 2>/dev/null || true
    fi
}

# Cleanup function
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "Deployment failed with exit code $exit_code"
        notify_slack "🚨 Deployment FAILED - Version: $VERSION" "danger"
    fi
    exit $exit_code
}

trap cleanup EXIT

################################################################################
# Step 1: Pre-flight Checks
################################################################################

log_info "Starting blue-green deployment for version: $VERSION"
notify_slack "🚀 Starting deployment - Version: $VERSION" "warning"

# Check required tools
log_info "Checking required tools..."
for tool in aws docker jq curl; do
    if ! command -v $tool &> /dev/null; then
        log_error "$tool is not installed"
        exit 1
    fi
done
log_success "All required tools are available"

# Verify AWS credentials
log_info "Verifying AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    log_error "AWS credentials are not configured"
    exit 1
fi
log_success "AWS credentials verified"

# Check if image exists in ECR
log_info "Checking if image exists in ECR..."
if ! aws ecr describe-images \
    --registry-id ${ECR_REGISTRY%%.*} \
    --repository-name $IMAGE_NAME \
    --image-ids imageTag=$VERSION \
    --region $AWS_REGION &> /dev/null; then
    log_error "Image $IMAGE_NAME:$VERSION not found in ECR"
    exit 1
fi
log_success "Image $IMAGE_NAME:$VERSION found in ECR"

################################################################################
# Step 2: Get Current Environment Status
################################################################################

log_info "Getting current environment status..."

# Get listener ARN
LISTENER_ARN=$(aws elbv2 describe-listeners \
    --load-balancer-arn $LB_ARN \
    --region $AWS_REGION \
    --query 'Listeners[0].ListenerArn' \
    --output text)

if [ -z "$LISTENER_ARN" ]; then
    log_error "Could not find listener for load balancer"
    exit 1
fi

# Get current target group
CURRENT_TG_ARN=$(aws elbv2 describe-listeners \
    --listener-arns $LISTENER_ARN \
    --region $AWS_REGION \
    --query 'Listeners[0].DefaultActions[0].TargetGroupArn' \
    --output text)

# Determine which environment is currently active
if [ "$CURRENT_TG_ARN" == "$BLUE_TG_ARN" ]; then
    ACTIVE_COLOR="blue"
    INACTIVE_COLOR="green"
    ACTIVE_TG_ARN=$BLUE_TG_ARN
    INACTIVE_TG_ARN=$GREEN_TG_ARN
else
    ACTIVE_COLOR="green"
    INACTIVE_COLOR="blue"
    ACTIVE_TG_ARN=$GREEN_TG_ARN
    INACTIVE_TG_ARN=$BLUE_TG_ARN
fi

log_info "Current active environment: $ACTIVE_COLOR"
log_info "Will deploy to: $INACTIVE_COLOR"

################################################################################
# Step 3: Deploy to Inactive Environment (Green/Blue)
################################################################################

log_info "Deploying to $INACTIVE_COLOR environment..."

# Get instances in inactive target group
INACTIVE_INSTANCES=$(aws elbv2 describe-target-health \
    --target-group-arn $INACTIVE_TG_ARN \
    --region $AWS_REGION \
    --query 'TargetHealthDescriptions[*].Target.Id' \
    --output text)

if [ -z "$INACTIVE_INSTANCES" ]; then
    log_error "No instances found in $INACTIVE_COLOR target group"
    exit 1
fi

log_info "Found instances in $INACTIVE_COLOR: $INACTIVE_INSTANCES"

# Deploy to each instance
for instance_id in $INACTIVE_INSTANCES; do
    log_info "Deploying to instance: $instance_id"

    # Get instance IP
    INSTANCE_IP=$(aws ec2 describe-instances \
        --instance-ids $instance_id \
        --region $AWS_REGION \
        --query 'Reservations[0].Instances[0].PrivateIpAddress' \
        --output text)

    # SSH and deploy (using SSM instead of direct SSH for security)
    aws ssm send-command \
        --instance-ids $instance_id \
        --region $AWS_REGION \
        --document-name "AWS-RunShellScript" \
        --parameters 'commands=[
            "# Pull new image",
            "aws ecr get-login-password --region '$AWS_REGION' | docker login --username AWS --password-stdin '$ECR_REGISTRY'",
            "docker pull '$ECR_REGISTRY'/'$IMAGE_NAME':'$VERSION'",
            "",
            "# Stop old container",
            "docker stop ml-api || true",
            "docker rm ml-api || true",
            "",
            "# Start new container",
            "docker run -d \\",
            "  --name ml-api \\",
            "  --restart unless-stopped \\",
            "  -p 8000:8000 \\",
            "  -v /opt/ml/models:/opt/ml/models \\",
            "  --env-file /opt/ml/.env \\",
            "  '$ECR_REGISTRY'/'$IMAGE_NAME':'$VERSION'",
            "",
            "# Wait for startup",
            "sleep 10",
            "",
            "# Verify health",
            "for i in {1..30}; do",
            "  if curl -f http://localhost:8000/api/v1/ml/health; then",
            "    echo \"Health check passed\"",
            "    exit 0",
            "  fi",
            "  sleep 2",
            "done",
            "",
            "echo \"Health check failed\"",
            "exit 1"
        ]' \
        --output text > /tmp/deploy_command_$instance_id.txt

    COMMAND_ID=$(cat /tmp/deploy_command_$instance_id.txt | head -1)

    # Wait for command to complete
    log_info "Waiting for deployment command to complete on $instance_id..."
    sleep 5

    COMMAND_STATUS=$(aws ssm get-command-invocation \
        --command-id $COMMAND_ID \
        --instance-id $instance_id \
        --region $AWS_REGION \
        --query 'Status' \
        --output text)

    if [ "$COMMAND_STATUS" != "Success" ]; then
        log_error "Deployment failed on instance $instance_id"
        exit 1
    fi

    log_success "Deployed successfully to instance $instance_id"
done

log_success "Deployment completed on all $INACTIVE_COLOR instances"

################################################################################
# Step 4: Health Checks on Inactive Environment
################################################################################

log_info "Running health checks on $INACTIVE_COLOR environment..."

for retry in $(seq 1 $HEALTH_CHECK_RETRIES); do
    # Check target health
    HEALTH_STATUS=$(aws elbv2 describe-target-health \
        --target-group-arn $INACTIVE_TG_ARN \
        --region $AWS_REGION \
        --query 'TargetHealthDescriptions[*].TargetHealth.State' \
        --output text)

    # Check if all targets are healthy
    UNHEALTHY_COUNT=$(echo "$HEALTH_STATUS" | grep -v "healthy" | wc -l)

    if [ $UNHEALTHY_COUNT -eq 0 ]; then
        log_success "All targets in $INACTIVE_COLOR are healthy"
        break
    fi

    log_info "Waiting for targets to become healthy... ($retry/$HEALTH_CHECK_RETRIES)"
    sleep $HEALTH_CHECK_INTERVAL
done

# Final health check
FINAL_HEALTH=$(aws elbv2 describe-target-health \
    --target-group-arn $INACTIVE_TG_ARN \
    --region $AWS_REGION \
    --query 'TargetHealthDescriptions[*].TargetHealth.State' \
    --output text)

if echo "$FINAL_HEALTH" | grep -q "unhealthy"; then
    log_error "Some targets are still unhealthy in $INACTIVE_COLOR environment"
    exit 1
fi

################################################################################
# Step 5: Smoke Tests on Inactive Environment
################################################################################

log_info "Running smoke tests on $INACTIVE_COLOR environment..."

# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --load-balancer-arns $LB_ARN \
    --region $AWS_REGION \
    --query 'LoadBalancers[0].DNSName' \
    --output text)

# Temporarily route test traffic to inactive environment
# (In practice, you'd use a test endpoint or direct instance IP)
TEST_INSTANCE=$(echo $INACTIVE_INSTANCES | awk '{print $1}')
TEST_IP=$(aws ec2 describe-instances \
    --instance-ids $TEST_INSTANCE \
    --region $AWS_REGION \
    --query 'Reservations[0].Instances[0].PrivateIpAddress' \
    --output text)

# Test health endpoint
log_info "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://$TEST_IP:8000/api/v1/ml/health)
if ! echo "$HEALTH_RESPONSE" | jq -e '.status == "healthy"' > /dev/null; then
    log_error "Health check failed: $HEALTH_RESPONSE"
    exit 1
fi
log_success "Health check passed"

# Test metrics endpoint
log_info "Testing metrics endpoint..."
METRICS_RESPONSE=$(curl -s http://$TEST_IP:8000/api/v1/ml/metrics)
ACCURACY=$(echo "$METRICS_RESPONSE" | jq -r '.accuracy // .test_accuracy')
if [ "$ACCURACY" == "null" ] || [ -z "$ACCURACY" ]; then
    log_error "Metrics endpoint failed"
    exit 1
fi
log_success "Metrics endpoint passed (Accuracy: $ACCURACY)"

# Test prediction endpoint
log_info "Testing prediction endpoint..."
PREDICTION_RESPONSE=$(curl -s -X POST http://$TEST_IP:8000/api/v1/ml/predict/nba \
    -H "Content-Type: application/json" \
    -d '{
        "lead_id": "smoke-test-'$(date +%s)'",
        "source": "website",
        "created_at": "'$(date -u +%Y-%m-%dT%H:%M:%S)'",
        "property_zip": "48304",
        "estimated_value": 850000
    }')

ACTION=$(echo "$PREDICTION_RESPONSE" | jq -r '.action')
if [ "$ACTION" == "null" ] || [ -z "$ACTION" ]; then
    log_error "Prediction endpoint failed: $PREDICTION_RESPONSE"
    exit 1
fi
log_success "Prediction endpoint passed (Action: $ACTION)"

log_success "All smoke tests passed on $INACTIVE_COLOR environment"

################################################################################
# Step 6: Switch Traffic to Inactive Environment
################################################################################

log_info "Switching traffic from $ACTIVE_COLOR to $INACTIVE_COLOR..."
notify_slack "🔄 Switching traffic to $INACTIVE_COLOR environment" "warning"

aws elbv2 modify-listener \
    --listener-arn $LISTENER_ARN \
    --default-actions Type=forward,TargetGroupArn=$INACTIVE_TG_ARN \
    --region $AWS_REGION > /dev/null

log_success "Traffic switched to $INACTIVE_COLOR environment at $(date)"
notify_slack "✅ Traffic switched to $INACTIVE_COLOR environment" "good"

################################################################################
# Step 7: Monitor New Environment
################################################################################

log_info "Monitoring $INACTIVE_COLOR environment for $MONITORING_DURATION seconds..."

START_TIME=$(date +%s)
END_TIME=$((START_TIME + MONITORING_DURATION))
ISSUE_DETECTED=false

while [ $(date +%s) -lt $END_TIME ]; do
    ELAPSED=$(($(date +%s) - START_TIME))
    REMAINING=$((MONITORING_DURATION - ELAPSED))

    # Check error rate
    ERROR_COUNT=$(aws cloudwatch get-metric-statistics \
        --namespace AWS/ApplicationELB \
        --metric-name HTTPCode_Target_5XX_Count \
        --dimensions Name=TargetGroup,Value=${INACTIVE_TG_ARN##*/} \
        --start-time $(date -u -d "1 minute ago" +%Y-%m-%dT%H:%M:%S) \
        --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
        --period 60 \
        --statistics Sum \
        --region $AWS_REGION \
        --query 'Datapoints[0].Sum' \
        --output text 2>/dev/null || echo "0")

    REQUEST_COUNT=$(aws cloudwatch get-metric-statistics \
        --namespace AWS/ApplicationELB \
        --metric-name RequestCount \
        --dimensions Name=TargetGroup,Value=${INACTIVE_TG_ARN##*/} \
        --start-time $(date -u -d "1 minute ago" +%Y-%m-%dT%H:%M:%S) \
        --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
        --period 60 \
        --statistics Sum \
        --region $AWS_REGION \
        --query 'Datapoints[0].Sum' \
        --output text 2>/dev/null || echo "0")

    if [ "$REQUEST_COUNT" != "None" ] && [ "$REQUEST_COUNT" != "0" ]; then
        ERROR_RATE=$(echo "scale=2; ($ERROR_COUNT / $REQUEST_COUNT) * 100" | bc)

        if (( $(echo "$ERROR_RATE > $ERROR_THRESHOLD" | bc -l) )); then
            log_error "Error rate too high: $ERROR_RATE% (threshold: $ERROR_THRESHOLD%)"
            ISSUE_DETECTED=true
            break
        fi
    fi

    # Check latency
    LATENCY=$(aws cloudwatch get-metric-statistics \
        --namespace AWS/ApplicationELB \
        --metric-name TargetResponseTime \
        --dimensions Name=TargetGroup,Value=${INACTIVE_TG_ARN##*/} \
        --start-time $(date -u -d "1 minute ago" +%Y-%m-%dT%H:%M:%S) \
        --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
        --period 60 \
        --statistics Average \
        --region $AWS_REGION \
        --query 'Datapoints[0].Average' \
        --output text 2>/dev/null || echo "0")

    LATENCY_MS=$(echo "$LATENCY * 1000" | bc | cut -d. -f1)

    if [ "$LATENCY_MS" != "None" ] && [ $LATENCY_MS -gt $LATENCY_THRESHOLD ]; then
        log_error "Latency too high: ${LATENCY_MS}ms (threshold: ${LATENCY_THRESHOLD}ms)"
        ISSUE_DETECTED=true
        break
    fi

    log_info "Monitoring... (${REMAINING}s remaining) - Error Rate: ${ERROR_RATE:-0}%, Latency: ${LATENCY_MS:-0}ms"
    sleep 10
done

################################################################################
# Step 8: Rollback or Decommission
################################################################################

if [ "$ISSUE_DETECTED" = true ]; then
    log_error "Issues detected during monitoring - initiating rollback"
    notify_slack "🚨 Issues detected - Rolling back to $ACTIVE_COLOR" "danger"

    # Switch back to active environment
    aws elbv2 modify-listener \
        --listener-arn $LISTENER_ARN \
        --default-actions Type=forward,TargetGroupArn=$ACTIVE_TG_ARN \
        --region $AWS_REGION > /dev/null

    log_success "Rolled back to $ACTIVE_COLOR environment"
    notify_slack "✅ Rollback completed - Traffic restored to $ACTIVE_COLOR" "warning"
    exit 1
else
    log_success "No issues detected during monitoring period"

    # Decommission old environment
    log_info "Decommissioning $ACTIVE_COLOR environment..."

    # Deregister targets from old target group
    OLD_TARGETS=$(aws elbv2 describe-target-health \
        --target-group-arn $ACTIVE_TG_ARN \
        --region $AWS_REGION \
        --query 'TargetHealthDescriptions[*].Target.Id' \
        --output text)

    if [ -n "$OLD_TARGETS" ]; then
        for instance_id in $OLD_TARGETS; do
            aws elbv2 deregister-targets \
                --target-group-arn $ACTIVE_TG_ARN \
                --targets Id=$instance_id \
                --region $AWS_REGION
            log_info "Deregistered $instance_id from $ACTIVE_COLOR target group"
        done
    fi

    log_success "$ACTIVE_COLOR environment decommissioned"

    # Final success notification
    log_success "Deployment completed successfully!"
    notify_slack "🎉 Deployment SUCCESS - Version $VERSION is now live in $INACTIVE_COLOR environment" "good"
fi

################################################################################
# Step 9: Cleanup and Summary
################################################################################

log_info "==================================="
log_info "Deployment Summary"
log_info "==================================="
log_info "Version deployed: $VERSION"
log_info "New active environment: $INACTIVE_COLOR"
log_info "Deployment duration: $(($(date +%s) - START_TIME)) seconds"
log_info "==================================="

# Save deployment metadata
DEPLOYMENT_LOG="/var/log/ml-deployments/deployment-$VERSION-$(date +%Y%m%d-%H%M%S).log"
mkdir -p /var/log/ml-deployments
cat > $DEPLOYMENT_LOG <<EOF
{
  "version": "$VERSION",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "previous_environment": "$ACTIVE_COLOR",
  "new_environment": "$INACTIVE_COLOR",
  "duration_seconds": $(($(date +%s) - START_TIME)),
  "final_accuracy": "$ACCURACY",
  "status": "success"
}
EOF

log_info "Deployment log saved to: $DEPLOYMENT_LOG"

exit 0
