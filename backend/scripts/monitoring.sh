#!/bin/bash
# =============================================================================
# iSwitch Roofs CRM - Continuous Monitoring Script
# =============================================================================
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
INTERVAL="${INTERVAL:-60}"
ALERT_EMAIL="${ALERT_EMAIL:-}"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
EXPORT_FORMAT="csv"
EXPORT_FILE=""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $*"; }
log_error() { echo -e "${RED}[$(date +'%H:%M:%S')] ERROR:${NC} $*"; }
log_warning() { echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARN:${NC} $*"; }

send_alert() {
    local message="$1"
    local severity="${2:-warning}"

    log_error "ALERT: $message"

    # Email
    if [ -n "$ALERT_EMAIL" ] && command -v mail &> /dev/null; then
        echo "$message" | mail -s "[iSwitch CRM] $severity Alert" "$ALERT_EMAIL"
    fi

    # Slack
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{\"text\": \":warning: $message\"}" > /dev/null 2>&1
    fi
}

collect_metrics() {
    local timestamp=$(date +%Y-%m-%d\ %H:%M:%S)

    # Response time
    local start=$(date +%s%N)
    local status=$(curl -sf -o /dev/null -w "%{http_code}" "$API_URL/health" 2>/dev/null || echo "000")
    local end=$(date +%s%N)
    local response_time=$(( (end - start) / 1000000 ))

    # Error rate
    local error_rate=0
    if [ "$status" != "200" ]; then
        error_rate=100
        send_alert "API health check failed (HTTP $status)" "critical"
    fi

    # Check response time threshold
    if [ "$response_time" -gt 500 ]; then
        log_warning "High response time: ${response_time}ms"
        send_alert "Response time exceeded 500ms: ${response_time}ms"
    fi

    # Cache stats
    local cache_hit_rate=0
    if [ "$status" = "200" ]; then
        cache_hit_rate=$(curl -sf "$API_URL/api/cache/stats" 2>/dev/null | \
            python3 -c "import sys, json; print(json.load(sys.stdin).get('hit_rate_percent', 0))" 2>/dev/null || echo "0")

        if [ "$(echo "$cache_hit_rate < 50" | bc -l 2>/dev/null || echo "0")" -eq 1 ]; then
            log_warning "Low cache hit rate: ${cache_hit_rate}%"
        fi
    fi

    # System resources
    local cpu_usage=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//' || echo "0")
    local mem_usage=$(vm_stat | perl -ne '/Pages active:\s+(\d+)/ and printf("%.0f", $1 * 4096 / 1048576)' 2>/dev/null || echo "0")
    local disk_free=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//' || echo "0")

    # Alerts
    if [ "$(echo "$cpu_usage > 80" | bc -l 2>/dev/null || echo "0")" -eq 1 ]; then
        send_alert "High CPU usage: ${cpu_usage}%"
    fi

    if [ "$disk_free" -lt 2 ]; then
        send_alert "Low disk space: ${disk_free}GB" "critical"
    fi

    # Export metrics
    if [ -n "$EXPORT_FILE" ]; then
        echo "$timestamp,$response_time,$error_rate,$cache_hit_rate,$cpu_usage,$mem_usage,$disk_free" >> "$EXPORT_FILE"
    fi

    # Console output
    log "Response: ${response_time}ms | Cache: ${cache_hit_rate}% | CPU: ${cpu_usage}% | Mem: ${mem_usage}MB | Disk: ${disk_free}GB"
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    --interval SEC       Check interval in seconds (default: 60)
    --export FILE        Export metrics to CSV file
    --alert-email EMAIL  Send alerts to email
    --slack-webhook URL  Send alerts to Slack
    -h, --help           Show help

Examples:
    $0 --interval 30
    $0 --export /var/log/metrics.csv
    $0 --alert-email admin@example.com

Cron example:
    */5 * * * * /opt/iswitch-crm/backend/scripts/monitoring.sh --interval 60 --export /var/log/metrics.csv

EOF
    exit 0
}

main() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --interval) INTERVAL="$2"; shift 2 ;;
            --export) EXPORT_FILE="$2"; shift 2 ;;
            --alert-email) ALERT_EMAIL="$2"; shift 2 ;;
            --slack-webhook) SLACK_WEBHOOK="$2"; shift 2 ;;
            -h|--help) show_usage ;;
            *) echo "Unknown option: $1"; show_usage ;;
        esac
    done

    # Create CSV header
    if [ -n "$EXPORT_FILE" ] && [ ! -f "$EXPORT_FILE" ]; then
        echo "timestamp,response_time_ms,error_rate,cache_hit_rate,cpu_usage,memory_mb,disk_free_gb" > "$EXPORT_FILE"
    fi

    log "Starting monitoring (interval: ${INTERVAL}s)"

    while true; do
        collect_metrics
        sleep "$INTERVAL"
    done
}

main "$@"
