#!/bin/bash
# =============================================================================
# iSwitch Roofs CRM - Rollback Script
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEPLOY_DIR="/opt/iswitch-crm"
VERSION=""
SKIP_DB=false
FORCE=false

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $*"; }
log_error() { echo -e "${RED}ERROR:${NC} $*" >&2; }
log_warning() { echo -e "${YELLOW}WARNING:${NC} $*"; }

list_versions() {
    log "Available versions:"
    if [ -d "$DEPLOY_DIR/releases" ]; then
        ls -lt "$DEPLOY_DIR/releases" | tail -n +2 | head -5 | awk '{print "  " $9}'
    elif docker images | grep -q "iswitch-crm"; then
        docker images iswitch-crm --format "{{.Tag}}" | head -5 | sed 's/^/  /'
    else
        log_warning "No previous versions found"
    fi
}

rollback_docker() {
    log "Rolling back Docker deployment to version: $VERSION"

    if [ -z "$VERSION" ]; then
        log_error "Version required for Docker rollback"
        exit 1
    fi

    # Check if image exists
    if ! docker images | grep -q "$VERSION"; then
        log_error "Docker image not found: $VERSION"
        exit 1
    fi

    # Update docker-compose to use specific version
    sed -i.bak "s/image: iswitch-crm:.*/image: iswitch-crm:$VERSION/" docker-compose.yml

    # Restart services
    docker-compose down
    docker-compose up -d

    log "✅ Rolled back to version: $VERSION"
}

rollback_systemd() {
    log "Rolling back systemd deployment..."

    if [ ! -d "$DEPLOY_DIR/releases" ]; then
        log_error "No releases directory found"
        exit 1
    fi

    local current=$(readlink "$DEPLOY_DIR/current" || echo "")
    local previous=$(ls -t "$DEPLOY_DIR/releases" | head -2 | tail -1)

    if [ -z "$previous" ]; then
        log_error "No previous version found"
        exit 1
    fi

    log "Current: $(basename $current)"
    log "Rollback to: $previous"

    if [ "$FORCE" = false ]; then
        read -p "Continue? (y/N) " -n 1 -r
        echo
        [[ ! $REPLY =~ ^[Yy]$ ]] && exit 0
    fi

    sudo ln -sfn "$DEPLOY_DIR/releases/$previous" "$DEPLOY_DIR/current"
    sudo systemctl reload iswitch-crm

    log "✅ Rolled back to: $previous"
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    --version VERSION    Version to rollback to
    --skip-db           Skip database rollback
    --force             Skip confirmation
    -h, --help          Show help

Examples:
    $0                                    # Interactive
    $0 --version 20250109_120000         # Specific version
    $0 --skip-db                         # No DB changes

EOF
    exit 0
}

main() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --version) VERSION="$2"; shift 2 ;;
            --skip-db) SKIP_DB=true; shift ;;
            --force) FORCE=true; shift ;;
            -h|--help) show_usage ;;
            *) log_error "Unknown option: $1"; show_usage ;;
        esac
    done

    echo "=========================================="
    echo "iSwitch Roofs CRM - Rollback"
    echo "=========================================="

    list_versions

    if [ -d "$DEPLOY_DIR" ]; then
        rollback_systemd
    elif command -v docker-compose &> /dev/null; then
        rollback_docker
    else
        log_error "No deployment method detected"
        exit 1
    fi
}

main "$@"
