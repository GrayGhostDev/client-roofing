#!/bin/bash
# =============================================================================
# iSwitch Roofs CRM - Zero-Downtime Deployment Script
# =============================================================================
# This script automates deployment with health checks, rollback capability,
# and zero-downtime blue-green deployment strategy.
#
# Usage:
#   ./scripts/deploy.sh --mode docker --env production
#   ./scripts/deploy.sh --mode systemd --skip-migrations
#   ./scripts/deploy.sh --dry-run
#
# =============================================================================

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
BACKUP_DIR="$PROJECT_ROOT/backups"
DEPLOYMENT_LOG="$LOG_DIR/deployment-$(date +%Y-%m-%d-%H-%M-%S).log"

# Default values
DEPLOYMENT_MODE="${DEPLOYMENT_MODE:-docker}"
ENVIRONMENT="${ENVIRONMENT:-production}"
SKIP_MIGRATIONS=false
DRY_RUN=false
NOTIFY_CHANNEL=""
FORCE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# Helper Functions
# =============================================================================
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$DEPLOYMENT_LOG"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $*" | tee -a "$DEPLOYMENT_LOG" >&2
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $*" | tee -a "$DEPLOYMENT_LOG"
}

log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $*" | tee -a "$DEPLOYMENT_LOG"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "Required command '$1' not found. Please install it first."
        exit 1
    fi
}

check_disk_space() {
    local required_gb=2
    local available_gb=$(df -BG "$PROJECT_ROOT" | tail -1 | awk '{print $4}' | sed 's/G//')

    if [ "$available_gb" -lt "$required_gb" ]; then
        log_error "Insufficient disk space. Required: ${required_gb}GB, Available: ${available_gb}GB"
        exit 1
    fi
    log "Disk space check passed: ${available_gb}GB available"
}

verify_env_file() {
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        log_error ".env file not found at $PROJECT_ROOT/.env"
        log_error "Copy .env.production to .env and configure it first"
        exit 1
    fi

    # Check required environment variables
    local required_vars=("SECRET_KEY" "DATABASE_URL" "REDIS_URL")
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$PROJECT_ROOT/.env"; then
            log_error "Required environment variable '$var' not found in .env"
            exit 1
        fi
    done
    log ".env file verified"
}

health_check() {
    local url="$1"
    local max_attempts=30
    local attempt=0

    log_info "Performing health check on $url"

    while [ $attempt -lt $max_attempts ]; do
        if curl -sf "$url/health" > /dev/null 2>&1; then
            log "Health check passed on attempt $((attempt + 1))"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    log_error "Health check failed after $max_attempts attempts"
    return 1
}

run_database_migrations() {
    if [ "$SKIP_MIGRATIONS" = true ]; then
        log_info "Skipping database migrations (--skip-migrations flag set)"
        return 0
    fi

    log "Running database migrations..."

    # Backup database before migrations
    if [ -f "$SCRIPT_DIR/backup.sh" ]; then
        log_info "Creating database backup before migrations..."
        "$SCRIPT_DIR/backup.sh" --destination local --type database || {
            log_warning "Backup failed, but continuing with migrations"
        }
    fi

    # Run migrations based on mode
    if [ "$DEPLOYMENT_MODE" = "docker" ]; then
        docker-compose exec -T backend flask db upgrade || {
            log_error "Database migrations failed"
            return 1
        }
    else
        cd "$PROJECT_ROOT" && python3 -m flask db upgrade || {
            log_error "Database migrations failed"
            return 1
        }
    fi

    log "Database migrations completed successfully"
}

deploy_docker() {
    log "Starting Docker deployment..."

    # Check if docker and docker-compose are available
    check_command "docker"
    check_command "docker-compose"

    # Get current version (if running)
    local current_version=""
    if docker ps -q -f name=iswitch-crm-backend &> /dev/null; then
        current_version=$(docker ps -f name=iswitch-crm-backend --format "{{.Image}}")
        log_info "Current version: $current_version"
    else
        log_info "No previous version running"
    fi

    # Pull/build new version
    log "Building new Docker images..."
    if [ "$DRY_RUN" = false ]; then
        docker-compose build --no-cache || {
            log_error "Docker build failed"
            exit 1
        }
    else
        log_info "[DRY RUN] Would build Docker images"
    fi

    # Run database migrations
    run_database_migrations

    # Start new version alongside old (blue-green deployment)
    log "Starting new version..."
    if [ "$DRY_RUN" = false ]; then
        docker-compose up -d --scale backend=2 || {
            log_error "Failed to start new version"
            exit 1
        }

        # Wait for new version to be healthy
        sleep 10
        if ! health_check "http://localhost:8000"; then
            log_error "New version health check failed, rolling back..."
            docker-compose down
            exit 1
        fi

        # Stop old version
        if [ -n "$current_version" ]; then
            log "Stopping old version..."
            docker-compose stop backend
            sleep 5
        fi

        # Scale back to 1 instance
        docker-compose up -d --scale backend=1

        log "Docker deployment completed successfully"
    else
        log_info "[DRY RUN] Would perform blue-green deployment"
    fi
}

deploy_systemd() {
    log "Starting systemd deployment..."

    check_command "systemctl"

    # Check if service exists
    if ! systemctl list-unit-files | grep -q "iswitch-crm.service"; then
        log_error "iswitch-crm.service not found. Run setup.sh first."
        exit 1
    fi

    # Get current version
    local deploy_dir="/opt/iswitch-crm"
    local current_dir="$deploy_dir/current"
    local new_dir="$deploy_dir/releases/$(date +%Y%m%d%H%M%S)"

    # Create new release directory
    log "Creating new release directory: $new_dir"
    if [ "$DRY_RUN" = false ]; then
        sudo mkdir -p "$new_dir"
        sudo cp -r "$PROJECT_ROOT"/* "$new_dir/"
        sudo chown -R iswitch:iswitch "$new_dir"
    else
        log_info "[DRY RUN] Would create release at $new_dir"
    fi

    # Install dependencies
    log "Installing Python dependencies..."
    if [ "$DRY_RUN" = false ]; then
        sudo -u iswitch /opt/iswitch-crm/venv/bin/pip install -r "$new_dir/requirements.txt" || {
            log_error "Failed to install dependencies"
            exit 1
        }
    else
        log_info "[DRY RUN] Would install dependencies"
    fi

    # Run migrations
    run_database_migrations

    # Switch symlink (zero-downtime)
    log "Switching to new version..."
    if [ "$DRY_RUN" = false ]; then
        sudo ln -sfn "$new_dir" "$current_dir"
        sudo systemctl reload iswitch-crm || {
            log_error "Failed to reload service"
            # Rollback symlink
            if [ -L "$current_dir.old" ]; then
                sudo ln -sfn "$(readlink $current_dir.old)" "$current_dir"
            fi
            exit 1
        }

        # Wait and verify
        sleep 5
        if ! health_check "http://localhost:8000"; then
            log_error "New version health check failed, rolling back..."
            sudo ln -sfn "$(readlink $current_dir.old)" "$current_dir"
            sudo systemctl reload iswitch-crm
            exit 1
        fi

        log "Systemd deployment completed successfully"
    else
        log_info "[DRY RUN] Would switch symlink and reload service"
    fi
}

deploy_kubernetes() {
    log "Starting Kubernetes deployment..."

    check_command "kubectl"

    log_warning "Kubernetes deployment is basic. Consider using Helm for production."

    if [ "$DRY_RUN" = false ]; then
        # Apply Kubernetes manifests (you'll need to create these)
        if [ -d "$PROJECT_ROOT/k8s" ]; then
            kubectl apply -f "$PROJECT_ROOT/k8s/" || {
                log_error "Kubernetes deployment failed"
                exit 1
            }

            # Wait for rollout
            kubectl rollout status deployment/iswitch-crm-backend || {
                log_error "Rollout failed"
                exit 1
            }

            log "Kubernetes deployment completed successfully"
        else
            log_error "k8s/ directory not found. Create Kubernetes manifests first."
            exit 1
        fi
    else
        log_info "[DRY RUN] Would apply Kubernetes manifests"
    fi
}

send_notification() {
    local status="$1"
    local message="$2"

    if [ -z "$NOTIFY_CHANNEL" ]; then
        return 0
    fi

    case "$NOTIFY_CHANNEL" in
        slack)
            if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
                curl -X POST "$SLACK_WEBHOOK_URL" \
                    -H 'Content-Type: application/json' \
                    -d "{\"text\": \"Deployment $status: $message\"}" \
                    > /dev/null 2>&1
            fi
            ;;
        email)
            if command -v mail &> /dev/null && [ -n "${NOTIFY_EMAIL:-}" ]; then
                echo "$message" | mail -s "Deployment $status" "$NOTIFY_EMAIL"
            fi
            ;;
    esac
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    --mode MODE              Deployment mode: docker, systemd, kubernetes (default: docker)
    --env ENV               Environment: development, staging, production (default: production)
    --skip-migrations       Skip database migrations
    --dry-run              Show what would be done without actually doing it
    --notify CHANNEL       Send notifications: slack, email
    --force                Force deployment without confirmations
    -h, --help             Show this help message

Examples:
    $0 --mode docker --env production
    $0 --mode systemd --skip-migrations
    $0 --dry-run
    $0 --mode docker --notify slack

Environment Variables:
    SLACK_WEBHOOK_URL      Slack webhook for notifications
    NOTIFY_EMAIL          Email address for notifications

EOF
    exit 0
}

# =============================================================================
# Main Deployment Logic
# =============================================================================
main() {
    # Parse command-line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --mode)
                DEPLOYMENT_MODE="$2"
                shift 2
                ;;
            --env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --skip-migrations)
                SKIP_MIGRATIONS=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --notify)
                NOTIFY_CHANNEL="$2"
                shift 2
                ;;
            --force)
                FORCE=true
                shift
                ;;
            -h|--help)
                show_usage
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                ;;
        esac
    done

    # Create log directory
    mkdir -p "$LOG_DIR" "$BACKUP_DIR"

    # Print banner
    echo "=========================================="
    echo "iSwitch Roofs CRM - Deployment Script"
    echo "=========================================="
    echo "Mode: $DEPLOYMENT_MODE"
    echo "Environment: $ENVIRONMENT"
    echo "Dry Run: $DRY_RUN"
    echo "Skip Migrations: $SKIP_MIGRATIONS"
    echo "=========================================="
    echo ""

    # Confirmation (unless --force)
    if [ "$FORCE" = false ] && [ "$DRY_RUN" = false ]; then
        read -p "Proceed with deployment? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Deployment cancelled by user"
            exit 0
        fi
    fi

    # Pre-deployment checks
    log "Running pre-deployment checks..."
    check_disk_space
    verify_env_file

    # Record deployment metadata
    cat > "$LOG_DIR/deployment-metadata.json" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "mode": "$DEPLOYMENT_MODE",
  "environment": "$ENVIRONMENT",
  "user": "$(whoami)",
  "hostname": "$(hostname)",
  "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "git_branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
}
EOF

    # Deploy based on mode
    case "$DEPLOYMENT_MODE" in
        docker)
            deploy_docker
            ;;
        systemd)
            deploy_systemd
            ;;
        kubernetes|k8s)
            deploy_kubernetes
            ;;
        *)
            log_error "Unknown deployment mode: $DEPLOYMENT_MODE"
            exit 1
            ;;
    esac

    # Post-deployment validation
    log "Running post-deployment validation..."
    if health_check "http://localhost:8000"; then
        log "✅ Deployment completed successfully!"
        send_notification "SUCCESS" "Deployment completed successfully for $ENVIRONMENT"
    else
        log_error "❌ Deployment completed but health check failed"
        send_notification "FAILED" "Deployment health check failed for $ENVIRONMENT"
        exit 1
    fi

    log "Deployment log saved to: $DEPLOYMENT_LOG"
}

# Run main function
main "$@"
