#!/bin/bash
# =============================================================================
# iSwitch Roofs CRM - Initial Server Setup Script
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALL_DIR="/opt/iswitch-crm"
AUTO=false
SKIP_DATABASE=false

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}✓${NC} $*"; }
log_error() { echo -e "${RED}✗${NC} $*" >&2; exit 1; }

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Please run as root (sudo)"
    fi
}

update_system() {
    log "Updating system packages..."
    apt-get update && apt-get upgrade -y
    apt-get install -y python3.11 python3-pip python3-venv nginx redis-server \
        postgresql-client git curl ufw fail2ban
}

create_user() {
    log "Creating system user..."
    if ! id -u iswitch > /dev/null 2>&1; then
        useradd -r -s /bin/false iswitch
    fi
}

setup_directories() {
    log "Creating directories..."
    mkdir -p "$INSTALL_DIR"/{backend,releases,current}
    mkdir -p /var/log/iswitch-crm
    mkdir -p /var/run/iswitch-crm
    chown -R iswitch:iswitch "$INSTALL_DIR"
    chown -R iswitch:iswitch /var/log/iswitch-crm
}

install_application() {
    log "Installing application..."
    cp -r "$PROJECT_ROOT"/* "$INSTALL_DIR/backend/"

    # Create virtual environment
    sudo -u iswitch python3 -m venv "$INSTALL_DIR/venv"
    sudo -u iswitch "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/backend/requirements.txt"
}

setup_systemd() {
    log "Configuring systemd service..."
    cp "$PROJECT_ROOT/systemd/iswitch-crm.service" /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable iswitch-crm
}

setup_nginx() {
    log "Configuring nginx..."
    cp "$PROJECT_ROOT/nginx/nginx.conf" /etc/nginx/sites-available/iswitch-crm
    ln -sf /etc/nginx/sites-available/iswitch-crm /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx
}

setup_ssl() {
    log "Setting up SSL certificates..."
    if command -v certbot &> /dev/null; then
        certbot --nginx -d app.iswitchroofs.com --non-interactive --agree-tos -m admin@iswitchroofs.com
    else
        log "Certbot not found, skipping SSL setup"
    fi
}

setup_firewall() {
    log "Configuring firewall..."
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    --auto             Non-interactive mode
    --skip-database    Skip database initialization
    -h, --help         Show help

EOF
    exit 0
}

main() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --auto) AUTO=true; shift ;;
            --skip-database) SKIP_DATABASE=true; shift ;;
            -h|--help) show_usage ;;
            *) log_error "Unknown option: $1" ;;
        esac
    done

    check_root

    echo "=========================================="
    echo "iSwitch Roofs CRM - Server Setup"
    echo "=========================================="

    update_system
    create_user
    setup_directories
    install_application
    setup_systemd
    setup_nginx
    setup_ssl
    setup_firewall

    log "✅ Setup completed successfully!"
    log "Next steps:"
    log "1. Configure .env file at $INSTALL_DIR/backend/.env"
    log "2. Start service: systemctl start iswitch-crm"
    log "3. Check status: systemctl status iswitch-crm"
}

main "$@"
