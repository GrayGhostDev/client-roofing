#!/bin/bash

################################################################################
# iSwitch Roofs CRM - Production Deployment Script
# Version: 2.0.0
# Date: 2025-10-10
#
# This script automates the deployment of the Streamlit frontend to production
# Includes: validation, build, deploy, health checks, rollback capability
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
ENVIRONMENT="${1:-production}"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-}"
IMAGE_NAME="${IMAGE_NAME:-iswitch-streamlit}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# Deployment settings
HEALTH_CHECK_RETRIES=10
HEALTH_CHECK_WAIT=6
BACKUP_ENABLED="${BACKUP_ENABLED:-true}"

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
    log "Validating deployment environment..."

    # Check if .env file exists
    if [ ! -f "$SCRIPT_DIR/.env" ]; then
        error ".env file not found. Copy .env.example to .env and configure it."
    fi

    # Load environment variables
    source "$SCRIPT_DIR/.env"

    # Validate required environment variables
    local required_vars=(
        "BACKEND_API_URL"
        "SUPABASE_URL"
        "SUPABASE_KEY"
    )

    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            error "Required environment variable $var is not set in .env"
        fi
    done

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
    local max_retries=5
    local retry=0

    while [ $retry -lt $max_retries ]; do
        if curl -sf "${backend_url}/health" > /dev/null 2>&1; then
            log "✅ Backend is healthy at $backend_url"
            return 0
        fi

        retry=$((retry + 1))
        if [ $retry -lt $max_retries ]; then
            warn "Backend not responding (attempt $retry/$max_retries). Retrying in 5 seconds..."
            sleep 5
        fi
    done

    error "Backend is not available at $backend_url. Please start the backend first."
}

validate_dependencies() {
    log "Validating Python dependencies..."

    # Check if requirements.txt exists
    if [ ! -f "$SCRIPT_DIR/requirements.txt" ]; then
        error "requirements.txt not found"
    fi

    # Validate Python version requirement
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        if grep -q "python.*3.11" "$SCRIPT_DIR/requirements.txt" || \
           grep -q "python.*3.13" "$SCRIPT_DIR/requirements.txt"; then
            log "✅ Python version requirements validated"
        fi
    fi
}

# ==============================================================================
# Backup Functions
# ==============================================================================

backup_current_deployment() {
    if [ "$BACKUP_ENABLED" = "true" ]; then
        log "Creating backup of current deployment..."

        local backup_dir="$SCRIPT_DIR/backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$backup_dir"

        # Backup configuration files
        if [ -f "$SCRIPT_DIR/.env" ]; then
            cp "$SCRIPT_DIR/.env" "$backup_dir/"
        fi

        if [ -f "$SCRIPT_DIR/.streamlit/config.toml" ]; then
            cp "$SCRIPT_DIR/.streamlit/config.toml" "$backup_dir/"
        fi

        # Export current container state
        if docker ps -a | grep -q "iswitch-crm-frontend"; then
            docker commit iswitch-crm-frontend "iswitch-streamlit:backup-$(date +%Y%m%d_%H%M%S)" || true
        fi

        log "✅ Backup created at $backup_dir"
        echo "$backup_dir" > "$SCRIPT_DIR/.last_backup"
    fi
}

# ==============================================================================
# Build Functions
# ==============================================================================

build_image() {
    log "Building Docker image: $IMAGE_NAME:$IMAGE_TAG..."

    docker build \
        --target production \
        --tag "$IMAGE_NAME:$IMAGE_TAG" \
        --tag "$IMAGE_NAME:$(date +%Y%m%d_%H%M%S)" \
        --build-arg BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        --build-arg VERSION="2.0.0" \
        "$SCRIPT_DIR"

    log "✅ Docker image built successfully"
}

push_image() {
    if [ -n "$DOCKER_REGISTRY" ]; then
        log "Pushing image to registry: $DOCKER_REGISTRY..."

        docker tag "$IMAGE_NAME:$IMAGE_TAG" "$DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
        docker push "$DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG"

        log "✅ Image pushed to registry"
    else
        info "Skipping image push (DOCKER_REGISTRY not set)"
    fi
}

# ==============================================================================
# Deployment Functions
# ==============================================================================

stop_current_deployment() {
    log "Stopping current deployment..."

    # Stop using docker-compose if available
    if [ -f "$BACKEND_DIR/docker-compose.yml" ]; then
        cd "$BACKEND_DIR"
        docker-compose stop frontend || true
    else
        # Stop container directly
        docker stop iswitch-crm-frontend || true
    fi

    log "✅ Current deployment stopped"
}

deploy_new_version() {
    log "Deploying new version..."

    # Deploy using docker-compose
    if [ -f "$BACKEND_DIR/docker-compose.yml" ]; then
        cd "$BACKEND_DIR"
        docker-compose up -d frontend

        log "✅ New version deployed via docker-compose"
    else
        # Deploy container directly
        docker run -d \
            --name iswitch-crm-frontend \
            --restart unless-stopped \
            -p 8501:8501 \
            --env-file "$SCRIPT_DIR/.env" \
            --network iswitch-network \
            "$IMAGE_NAME:$IMAGE_TAG"

        log "✅ New version deployed"
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

    error "Health check failed after $HEALTH_CHECK_RETRIES attempts"
}

run_smoke_tests() {
    log "Running smoke tests..."

    local frontend_url="http://localhost:8501"
    local backend_url="${BACKEND_API_URL:-http://localhost:8000}"

    # Test 1: Frontend is accessible
    if ! curl -sf "$frontend_url" > /dev/null 2>&1; then
        error "Smoke test failed: Frontend is not accessible"
    fi

    # Test 2: Health endpoint responds
    if ! curl -sf "$frontend_url/_stcore/health" > /dev/null 2>&1; then
        error "Smoke test failed: Health endpoint not responding"
    fi

    # Test 3: Backend connectivity
    if ! curl -sf "$backend_url/health" > /dev/null 2>&1; then
        warn "Backend connectivity test failed (non-critical)"
    fi

    log "✅ All smoke tests passed"
}

# ==============================================================================
# Rollback Functions
# ==============================================================================

rollback() {
    error "Deployment failed! Initiating rollback..."

    # Get last backup location
    if [ -f "$SCRIPT_DIR/.last_backup" ]; then
        local last_backup=$(cat "$SCRIPT_DIR/.last_backup")
        warn "Restoring from backup: $last_backup"

        # Restore configuration
        if [ -f "$last_backup/.env" ]; then
            cp "$last_backup/.env" "$SCRIPT_DIR/"
        fi
    fi

    # Restart with previous version
    if [ -f "$BACKEND_DIR/docker-compose.yml" ]; then
        cd "$BACKEND_DIR"
        docker-compose restart frontend
    else
        docker restart iswitch-crm-frontend || true
    fi

    error "Rollback completed. Please investigate the issue."
}

# ==============================================================================
# Cleanup Functions
# ==============================================================================

cleanup_old_images() {
    log "Cleaning up old Docker images..."

    # Remove dangling images
    docker image prune -f

    # Remove old tagged images (keep last 3)
    docker images "$IMAGE_NAME" --format "{{.Tag}}" | \
        grep -E '^[0-9]{8}_[0-9]{6}$' | \
        sort -r | \
        tail -n +4 | \
        xargs -I {} docker rmi "$IMAGE_NAME:{}" 2>/dev/null || true

    log "✅ Cleanup completed"
}

# ==============================================================================
# Main Deployment Flow
# ==============================================================================

main() {
    log "==================================================================="
    log "iSwitch Roofs CRM - Production Deployment"
    log "Environment: $ENVIRONMENT"
    log "Image: $IMAGE_NAME:$IMAGE_TAG"
    log "==================================================================="

    # Validation phase
    validate_environment
    validate_dependencies
    validate_backend

    # Backup phase
    backup_current_deployment

    # Build phase
    build_image
    push_image

    # Deployment phase
    stop_current_deployment
    deploy_new_version

    # Verification phase
    if ! wait_for_healthy; then
        rollback
    fi

    if ! run_smoke_tests; then
        rollback
    fi

    # Cleanup phase
    cleanup_old_images

    log "==================================================================="
    log "✅ Deployment completed successfully!"
    log "==================================================================="
    log ""
    log "Application URL: http://localhost:8501"
    log "Backend API: ${BACKEND_API_URL:-http://localhost:8000}"
    log ""
    log "Useful commands:"
    log "  - View logs: docker logs -f iswitch-crm-frontend"
    log "  - Check status: docker ps | grep iswitch-crm-frontend"
    log "  - Health check: curl http://localhost:8501/_stcore/health"
    log "  - Backend health: curl ${BACKEND_API_URL:-http://localhost:8000}/health"
    log ""
    log "Next steps:"
    log "  1. Verify application is working correctly"
    log "  2. Monitor logs for any errors"
    log "  3. Test key workflows (leads, analytics, etc.)"
    log "  4. Configure SSL/TLS if not already done"
    log "  5. Setup monitoring and alerts"
    log ""
}

# Trap errors and call rollback
trap 'rollback' ERR

# Run main deployment
main "$@"
