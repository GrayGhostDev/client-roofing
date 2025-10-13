#!/bin/bash
# =============================================================================
# iSwitch Roofs CRM - Frontend (Streamlit) Deployment Script
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
MODE="${MODE:-docker}"
ACTION="${ACTION:-deploy}"
PORT=8501

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}✓${NC} $*"; }
log_error() { echo -e "${RED}✗${NC} $*" >&2; exit 1; }

deploy_docker() {
    log "Deploying frontend with Docker..."

    if [ ! -f "$SCRIPT_DIR/Dockerfile" ]; then
        # Create Dockerfile if it doesn't exist
        cat > "$SCRIPT_DIR/Dockerfile" << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
EOF
    fi

    # Build image
    docker build -t iswitch-crm-frontend:latest "$SCRIPT_DIR"

    # Stop existing container
    docker stop iswitch-crm-frontend 2>/dev/null || true
    docker rm iswitch-crm-frontend 2>/dev/null || true

    # Run new container
    docker run -d \
        --name iswitch-crm-frontend \
        --restart unless-stopped \
        -p $PORT:8501 \
        -e BACKEND_URL="$BACKEND_URL" \
        iswitch-crm-frontend:latest

    log "Frontend deployed on port $PORT"
}

deploy_systemd() {
    log "Deploying frontend with systemd..."

    # Create systemd service file
    sudo tee /etc/systemd/system/iswitch-crm-frontend.service > /dev/null << EOF
[Unit]
Description=iSwitch Roofs CRM Frontend (Streamlit)
After=network.target

[Service]
Type=simple
User=iswitch
WorkingDirectory=$SCRIPT_DIR
Environment="BACKEND_URL=$BACKEND_URL"
ExecStart=/opt/iswitch-crm/venv/bin/streamlit run Home.py --server.port=$PORT --server.address=0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable iswitch-crm-frontend
    sudo systemctl restart iswitch-crm-frontend

    log "Frontend service started"
}

check_health() {
    log "Checking frontend health..."
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -sf "http://localhost:$PORT/_stcore/health" > /dev/null 2>&1; then
            log "Frontend is healthy"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    log_error "Frontend health check failed"
}

restart_service() {
    log "Restarting frontend..."

    if [ "$MODE" = "docker" ]; then
        docker restart iswitch-crm-frontend
    else
        sudo systemctl restart iswitch-crm-frontend
    fi

    check_health
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    --mode MODE             Deployment mode: docker, systemd (default: docker)
    --backend-url URL       Backend API URL (default: http://localhost:8000)
    --action ACTION         Action: deploy, restart (default: deploy)
    --port PORT            Port number (default: 8501)
    -h, --help             Show help

Examples:
    $0 --mode docker
    $0 --mode systemd --backend-url https://api.iswitchroofs.com
    $0 --action restart

EOF
    exit 0
}

main() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --mode) MODE="$2"; shift 2 ;;
            --backend-url) BACKEND_URL="$2"; shift 2 ;;
            --action) ACTION="$2"; shift 2 ;;
            --port) PORT="$2"; shift 2 ;;
            -h|--help) show_usage ;;
            *) log_error "Unknown option: $1" ;;
        esac
    done

    echo "=========================================="
    echo "iSwitch Roofs CRM - Frontend Deployment"
    echo "=========================================="
    echo "Mode: $MODE"
    echo "Backend URL: $BACKEND_URL"
    echo "Port: $PORT"
    echo "=========================================="

    case "$ACTION" in
        deploy)
            if [ "$MODE" = "docker" ]; then
                deploy_docker
            else
                deploy_systemd
            fi
            check_health
            ;;
        restart)
            restart_service
            ;;
        *)
            log_error "Unknown action: $ACTION"
            ;;
    esac

    log "✅ Frontend deployment completed successfully!"
    log "Access dashboard at: http://localhost:$PORT"
}

main "$@"
