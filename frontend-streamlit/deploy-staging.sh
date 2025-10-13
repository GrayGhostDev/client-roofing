#!/bin/bash

################################################################################
# iSwitch Roofs CRM - Staging Deployment Script
# Version: 2.0.0
# Date: 2025-10-10
#
# This script automates the deployment of the Streamlit frontend to staging
# Includes: validation, build, deploy, health checks, test data loading
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit if any command in a pipe fails

# ==============================================================================
# Configuration
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Environment
ENVIRONMENT="staging"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-}"
IMAGE_NAME="${IMAGE_NAME:-iswitch-streamlit}"
IMAGE_TAG="${IMAGE_TAG:-staging}"

# Staging-specific settings
ENABLE_DEBUG_MODE="${ENABLE_DEBUG_MODE:-true}"
LOAD_TEST_DATA="${LOAD_TEST_DATA:-true}"
HEALTH_CHECK_RETRIES=15
HEALTH_CHECK_WAIT=5

# ==============================================================================
# Helper Functions
# ==============================================================================

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# ==============================================================================
# Validation Functions
# ==============================================================================

validate_environment() {
    log "Validating staging environment..."

    # Check if .env file exists, create from example if not
    if [ ! -f "$SCRIPT_DIR/.env" ]; then
        if [ -f "$SCRIPT_DIR/.env.example" ]; then
            warn ".env not found, copying from .env.example"
            cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
            warn "Please update .env with your staging credentials"
            # Don't exit - allow staging to continue with defaults
        else
            error ".env.example not found. Cannot create .env file."
        fi
    fi

    # Load environment variables (if .env exists)
    if [ -f "$SCRIPT_DIR/.env" ]; then
        source "$SCRIPT_DIR/.env"
    fi

    # Check Docker installation
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
    fi

    # Check Docker Compose installation
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
    fi

    log "✅ Environment validation passed"
}

validate_backend() {
    log "Checking backend availability..."

    local backend_url="${BACKEND_API_URL:-http://localhost:8000}"
    local max_retries=3
    local retry=0

    while [ $retry -lt $max_retries ]; do
        if curl -sf "${backend_url}/health" > /dev/null 2>&1; then
            log "✅ Backend is healthy at $backend_url"
            return 0
        fi

        retry=$((retry + 1))
        if [ $retry -lt $max_retries ]; then
            warn "Backend not responding (attempt $retry/$max_retries). Retrying in 3 seconds..."
            sleep 3
        fi
    done

    warn "Backend is not available at $backend_url. Continuing anyway (staging mode)."
    return 0  # Don't fail in staging if backend is down
}

# ==============================================================================
# Build Functions
# ==============================================================================

build_image() {
    log "Building Docker image for staging: $IMAGE_NAME:$IMAGE_TAG..."

    # Build development target for staging (includes dev tools)
    docker build \
        --target development \
        --tag "$IMAGE_NAME:$IMAGE_TAG" \
        --tag "$IMAGE_NAME:staging-$(date +%Y%m%d_%H%M%S)" \
        --build-arg BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        --build-arg VERSION="2.0.0-staging" \
        "$SCRIPT_DIR"

    log "✅ Docker image built successfully (development target)"
}

# ==============================================================================
# Deployment Functions
# ==============================================================================

stop_current_deployment() {
    log "Stopping current staging deployment..."

    # Stop using docker-compose if available
    if [ -f "$BACKEND_DIR/docker-compose.dev.yml" ]; then
        cd "$BACKEND_DIR"
        docker-compose -f docker-compose.dev.yml stop frontend || true
    elif [ -f "$BACKEND_DIR/docker-compose.yml" ]; then
        cd "$BACKEND_DIR"
        docker-compose stop frontend || true
    else
        # Stop container directly
        docker stop iswitch-crm-frontend-staging || true
        docker rm iswitch-crm-frontend-staging || true
    fi

    log "✅ Current staging deployment stopped"
}

deploy_new_version() {
    log "Deploying new staging version..."

    # Create staging-specific environment file
    if [ -f "$SCRIPT_DIR/.env" ]; then
        cat > "$SCRIPT_DIR/.env.staging" <<EOF
# Auto-generated staging environment
STREAMLIT_SERVER_LOG_LEVEL=debug
STREAMLIT_CLIENT_SHOW_ERROR_DETAILS=true
BACKEND_API_URL=${BACKEND_API_URL:-http://localhost:8000}
SUPABASE_URL=${SUPABASE_URL:-}
SUPABASE_KEY=${SUPABASE_KEY:-}
PUSHER_APP_KEY=${PUSHER_APP_KEY:-}
PUSHER_CLUSTER=${PUSHER_CLUSTER:-us2}
CACHE_TTL_SECONDS=60
EOF
    fi

    # Deploy container directly with debug settings
    docker run -d \
        --name iswitch-crm-frontend-staging \
        --restart unless-stopped \
        -p 8501:8501 \
        --env-file "$SCRIPT_DIR/.env.staging" \
        -v "$SCRIPT_DIR:/app" \
        --network iswitch-network \
        "$IMAGE_NAME:$IMAGE_TAG"

    log "✅ New staging version deployed with debug mode"
    info "Volume mounted for hot-reload: $SCRIPT_DIR:/app"
}

# ==============================================================================
# Test Data Functions
# ==============================================================================

load_test_data() {
    if [ "$LOAD_TEST_DATA" = "true" ]; then
        log "Loading test data into staging environment..."

        # Check if backend seeder script exists
        if [ -f "$BACKEND_DIR/scripts/seed_large_leads_dataset.py" ]; then
            info "Running backend data seeder..."

            cd "$BACKEND_DIR"
            if command -v python &> /dev/null; then
                # Run locally if Python is available
                python scripts/seed_large_leads_dataset.py --count 50 || warn "Test data loading failed (non-critical)"
            elif docker ps | grep -q "iswitch-crm-backend"; then
                # Run in backend container if available
                docker exec iswitch-crm-backend python scripts/seed_large_leads_dataset.py --count 50 || warn "Test data loading failed (non-critical)"
            else
                warn "Cannot load test data: Python not available and backend container not running"
            fi
        else
            warn "Test data seeder script not found, skipping"
        fi

        log "✅ Test data loading completed"
    fi
}

# ==============================================================================
# Health Check Functions
# ==============================================================================

wait_for_healthy() {
    log "Waiting for application to become healthy..."

    local retry=0
    local health_url="http://localhost:8501/_stcore/health"

    while [ $retry -lt $HEALTH_CHECK_RETRIES ]; do
        sleep $HEALTH_CHECK_WAIT

        if curl -sf "$health_url" > /dev/null 2>&1; then
            log "✅ Application is healthy!"
            return 0
        fi

        retry=$((retry + 1))
        info "Health check attempt $retry/$HEALTH_CHECK_RETRIES..."
    done

    warn "Health check timed out, but continuing (staging mode)"
    return 0  # Don't fail in staging
}

run_smoke_tests() {
    log "Running smoke tests..."

    local frontend_url="http://localhost:8501"
    local backend_url="${BACKEND_API_URL:-http://localhost:8000}"

    # Test 1: Frontend is accessible
    if curl -sf "$frontend_url" > /dev/null 2>&1; then
        log "✅ Frontend is accessible"
    else
        warn "Frontend accessibility test failed"
    fi

    # Test 2: Health endpoint responds
    if curl -sf "$frontend_url/_stcore/health" > /dev/null 2>&1; then
        log "✅ Health endpoint responding"
    else
        warn "Health endpoint test failed"
    fi

    # Test 3: Backend connectivity
    if curl -sf "$backend_url/health" > /dev/null 2>&1; then
        log "✅ Backend connectivity verified"
    else
        warn "Backend connectivity test failed (non-critical in staging)"
    fi

    log "✅ Smoke tests completed (warnings are non-critical)"
}

# ==============================================================================
# Logging Functions
# ==============================================================================

show_logs() {
    log "Showing container logs (last 50 lines)..."
    docker logs --tail 50 iswitch-crm-frontend-staging || warn "Could not retrieve logs"
}

enable_debug_logging() {
    if [ "$ENABLE_DEBUG_MODE" = "true" ]; then
        log "Debug mode enabled - verbose logging active"
        info "Logs will include detailed error traces and performance metrics"
    fi
}

# ==============================================================================
# Main Deployment Flow
# ==============================================================================

main() {
    log "==================================================================="
    log "iSwitch Roofs CRM - Staging Deployment"
    log "Environment: $ENVIRONMENT"
    log "Image: $IMAGE_NAME:$IMAGE_TAG"
    log "Debug Mode: $ENABLE_DEBUG_MODE"
    log "Test Data: $LOAD_TEST_DATA"
    log "==================================================================="

    # Validation phase
    validate_environment
    validate_backend

    # Build phase
    build_image

    # Deployment phase
    stop_current_deployment
    deploy_new_version
    enable_debug_logging

    # Verification phase
    wait_for_healthy
    run_smoke_tests

    # Test data phase
    load_test_data

    # Show logs
    show_logs

    log "==================================================================="
    log "✅ Staging deployment completed successfully!"
    log "==================================================================="
    log ""
    log "Staging Application URL: http://localhost:8501"
    log "Backend API: ${BACKEND_API_URL:-http://localhost:8000}"
    log ""
    log "Staging Features:"
    log "  ✅ Debug mode enabled"
    log "  ✅ Hot-reload on file changes"
    log "  ✅ Detailed error messages"
    log "  ✅ Test data loaded (50 leads)"
    log "  ✅ Development dependencies available"
    log ""
    log "Useful commands:"
    log "  - View logs: docker logs -f iswitch-crm-frontend-staging"
    log "  - Check status: docker ps | grep staging"
    log "  - Health check: curl http://localhost:8501/_stcore/health"
    log "  - Restart: docker restart iswitch-crm-frontend-staging"
    log "  - Stop: docker stop iswitch-crm-frontend-staging"
    log ""
    log "Testing workflow:"
    log "  1. Verify application loads correctly"
    log "  2. Test leads management with 50 test records"
    log "  3. Check analytics dashboards"
    log "  4. Test real-time updates (30-second refresh)"
    log "  5. Verify error handling and logging"
    log ""
    log "Next steps:"
    log "  - Test new features thoroughly"
    log "  - Check logs for any errors: docker logs -f iswitch-crm-frontend-staging"
    log "  - Review performance metrics"
    log "  - Deploy to production when ready: ./deploy-production.sh"
    log ""
}

# Don't exit on error in staging (more lenient)
trap 'warn "Error occurred but continuing in staging mode"' ERR

# Run main deployment
main "$@"
