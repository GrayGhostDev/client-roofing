#!/bin/bash
# =============================================================================
# iSwitch Roofs CRM - Comprehensive Health Check Script
# =============================================================================
# Monitors all system components: API, Database, Redis, External Services
#
# Usage:
#   ./scripts/health_check.sh
#   ./scripts/health_check.sh --format json
#   ./scripts/health_check.sh --component database
#   ./scripts/health_check.sh --verbose
#
# =============================================================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
API_URL="${API_URL:-http://localhost:8000}"
TIMEOUT=10

# Options
FORMAT="console"  # console, json, prometheus
COMPONENT="all"   # all, backend, database, redis, external, system
VERBOSE=false
EXIT_ON_FAILURE=false

# Health status
OVERALL_HEALTH="healthy"
CHECKS_PASSED=0
CHECKS_FAILED=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Results storage
declare -A HEALTH_RESULTS

# =============================================================================
# Helper Functions
# =============================================================================
log() {
    if [ "$FORMAT" = "console" ]; then
        echo -e "${GREEN}✓${NC} $*"
    fi
}

log_error() {
    if [ "$FORMAT" = "console" ]; then
        echo -e "${RED}✗${NC} $*" >&2
    fi
    OVERALL_HEALTH="unhealthy"
}

log_warning() {
    if [ "$FORMAT" = "console" ]; then
        echo -e "${YELLOW}⚠${NC} $*"
    fi
}

log_info() {
    if [ "$VERBOSE" = true ] && [ "$FORMAT" = "console" ]; then
        echo -e "${BLUE}ℹ${NC} $*"
    fi
}

record_check() {
    local component="$1"
    local status="$2"
    local message="$3"
    local details="${4:-}"

    HEALTH_RESULTS["${component}_status"]="$status"
    HEALTH_RESULTS["${component}_message"]="$message"
    HEALTH_RESULTS["${component}_details"]="$details"

    if [ "$status" = "pass" ]; then
        ((CHECKS_PASSED++))
    else
        ((CHECKS_FAILED++))
    fi
}

# =============================================================================
# Backend API Health Checks
# =============================================================================
check_backend_health() {
    log_info "Checking backend API health..."

    local start_time=$(date +%s%N)
    local response=$(curl -sf -m $TIMEOUT "$API_URL/health" 2>/dev/null || echo "")
    local end_time=$(date +%s%N)
    local response_time=$(( (end_time - start_time) / 1000000 ))

    if [ -n "$response" ]; then
        log "Backend API is healthy (${response_time}ms)"
        record_check "backend" "pass" "API responding" "response_time: ${response_time}ms"

        # Check response time threshold
        if [ $response_time -gt 200 ]; then
            log_warning "Backend response time is high: ${response_time}ms (target: <200ms)"
        fi
    else
        log_error "Backend API is not responding"
        record_check "backend" "fail" "API not responding" ""
        return 1
    fi
}

check_backend_endpoints() {
    log_info "Testing sample API endpoints..."

    local endpoints=("/api/auth/health" "/api/leads" "/api/customers")
    local failed=0

    for endpoint in "${endpoints[@]}"; do
        if curl -sf -m $TIMEOUT "$API_URL$endpoint" > /dev/null 2>&1; then
            log_info "  ✓ $endpoint"
        else
            log_warning "  ✗ $endpoint (may require authentication)"
            ((failed++))
        fi
    done

    if [ $failed -eq 0 ]; then
        record_check "backend_endpoints" "pass" "All endpoints accessible" ""
    else
        record_check "backend_endpoints" "warn" "$failed endpoints failed" ""
    fi
}

# =============================================================================
# Database Health Checks
# =============================================================================
check_database_health() {
    log_info "Checking PostgreSQL database health..."

    # Load DATABASE_URL
    if [ -f "$PROJECT_ROOT/.env" ]; then
        export $(grep -v '^#' "$PROJECT_ROOT/.env" | grep DATABASE_URL | xargs)
    fi

    if [ -z "${DATABASE_URL:-}" ]; then
        log_error "DATABASE_URL not configured"
        record_check "database" "fail" "DATABASE_URL not set" ""
        return 1
    fi

    # Parse connection details
    local db_host=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
    local db_port=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    local db_name=$(echo "$DATABASE_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')
    local db_user=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    local db_pass=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')

    # Test connection
    local result=$(PGPASSWORD="$db_pass" psql -h "$db_host" -p "$db_port" -U "$db_user" \
        -d "$db_name" -t -c "SELECT 1" 2>/dev/null || echo "")

    if [ "$result" = " 1" ]; then
        log "Database connection successful"

        # Get connection count
        local connections=$(PGPASSWORD="$db_pass" psql -h "$db_host" -p "$db_port" -U "$db_user" \
            -d "$db_name" -t -c "SELECT count(*) FROM pg_stat_activity" 2>/dev/null || echo "0")
        connections=$(echo "$connections" | xargs)

        log_info "Active connections: $connections"

        if [ "$connections" -gt 50 ]; then
            log_warning "High connection count: $connections (max: 60)"
        fi

        record_check "database" "pass" "Database healthy" "connections: $connections"
    else
        log_error "Database connection failed"
        record_check "database" "fail" "Cannot connect to database" ""
        return 1
    fi
}

check_database_tables() {
    log_info "Verifying database tables..."

    if [ -z "${DATABASE_URL:-}" ]; then
        return 1
    fi

    local db_host=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
    local db_port=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    local db_name=$(echo "$DATABASE_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')
    local db_user=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    local db_pass=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')

    # Count tables
    local table_count=$(PGPASSWORD="$db_pass" psql -h "$db_host" -p "$db_port" -U "$db_user" \
        -d "$db_name" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'" 2>/dev/null || echo "0")
    table_count=$(echo "$table_count" | xargs)

    log_info "Tables found: $table_count"

    if [ "$table_count" -gt 0 ]; then
        record_check "database_tables" "pass" "Tables exist" "count: $table_count"
    else
        log_warning "No tables found in database"
        record_check "database_tables" "warn" "No tables found" ""
    fi
}

# =============================================================================
# Redis Health Checks
# =============================================================================
check_redis_health() {
    log_info "Checking Redis health..."

    if [ -f "$PROJECT_ROOT/.env" ]; then
        export $(grep -v '^#' "$PROJECT_ROOT/.env" | grep REDIS_URL | xargs)
    fi

    local redis_host=$(echo "${REDIS_URL:-redis://localhost:6379}" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p' || echo "localhost")
    local redis_port=$(echo "${REDIS_URL:-redis://localhost:6379}" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p' || echo "6379")

    # Test connection
    if redis-cli -h "$redis_host" -p "$redis_port" PING > /dev/null 2>&1; then
        log "Redis connection successful"

        # Get memory info
        local memory=$(redis-cli -h "$redis_host" -p "$redis_port" INFO memory | grep "used_memory_human" | cut -d':' -f2 | tr -d '\r')
        local max_memory=$(redis-cli -h "$redis_host" -p "$redis_port" CONFIG GET maxmemory | tail -1)

        log_info "Redis memory usage: $memory"

        # Get cache stats
        local keys=$(redis-cli -h "$redis_host" -p "$redis_port" DBSIZE | cut -d':' -f2 | xargs)
        log_info "Cache keys: $keys"

        record_check "redis" "pass" "Redis healthy" "keys: $keys, memory: $memory"
    else
        log_error "Redis connection failed"
        record_check "redis" "fail" "Cannot connect to Redis" ""
        return 1
    fi
}

check_cache_performance() {
    log_info "Checking cache performance..."

    local cache_stats=$(curl -sf -m $TIMEOUT "$API_URL/api/cache/stats" 2>/dev/null || echo "")

    if [ -n "$cache_stats" ]; then
        local hit_rate=$(echo "$cache_stats" | python3 -c "import sys, json; print(json.load(sys.stdin).get('hit_rate_percent', 0))" 2>/dev/null || echo "0")

        log_info "Cache hit rate: ${hit_rate}%"

        if [ "$(echo "$hit_rate > 80" | bc -l)" -eq 1 ]; then
            log "Cache hit rate is excellent: ${hit_rate}%"
            record_check "cache_performance" "pass" "Hit rate: ${hit_rate}%" ""
        elif [ "$(echo "$hit_rate > 50" | bc -l)" -eq 1 ]; then
            log_warning "Cache hit rate is moderate: ${hit_rate}% (target: >80%)"
            record_check "cache_performance" "warn" "Hit rate below target" "hit_rate: ${hit_rate}%"
        else
            log_warning "Cache hit rate is low: ${hit_rate}%"
            record_check "cache_performance" "warn" "Low hit rate" "hit_rate: ${hit_rate}%"
        fi
    else
        log_warning "Unable to fetch cache stats"
        record_check "cache_performance" "warn" "Stats unavailable" ""
    fi
}

# =============================================================================
# System Resource Checks
# =============================================================================
check_system_resources() {
    log_info "Checking system resources..."

    # CPU usage
    local cpu_usage=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//' || echo "0")
    log_info "CPU usage: ${cpu_usage}%"

    if [ "$(echo "$cpu_usage > 80" | bc -l 2>/dev/null || echo "0")" -eq 1 ]; then
        log_warning "High CPU usage: ${cpu_usage}%"
    fi

    # Memory usage
    local memory_usage=$(vm_stat | perl -ne '/page size of (\d+)/ and $size=$1; /Pages\s+active:\s+(\d+)/ and printf("%.1f", $1 * $size / 1048576);' 2>/dev/null || echo "0")
    log_info "Memory usage: ${memory_usage}MB"

    # Disk space
    local disk_free=$(df -BG "$PROJECT_ROOT" | tail -1 | awk '{print $4}' | sed 's/G//' || echo "0")
    log_info "Disk space free: ${disk_free}GB"

    if [ "$disk_free" -lt 2 ]; then
        log_warning "Low disk space: ${disk_free}GB (recommend: >2GB)"
        record_check "system_resources" "warn" "Low disk space" "free: ${disk_free}GB"
    else
        record_check "system_resources" "pass" "Resources adequate" "disk: ${disk_free}GB"
    fi
}

# =============================================================================
# Output Formatters
# =============================================================================
output_console() {
    echo ""
    echo "=========================================="
    echo "Health Check Summary"
    echo "=========================================="
    echo "Status: $OVERALL_HEALTH"
    echo "Checks Passed: $CHECKS_PASSED"
    echo "Checks Failed: $CHECKS_FAILED"
    echo "=========================================="
}

output_json() {
    cat << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "$OVERALL_HEALTH",
  "checks_passed": $CHECKS_PASSED,
  "checks_failed": $CHECKS_FAILED,
  "components": {
$(
    for key in "${!HEALTH_RESULTS[@]}"; do
        echo "    \"$key\": \"${HEALTH_RESULTS[$key]}\","
    done | sed '$ s/,$//'
)
  }
}
EOF
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    --format FORMAT      Output format: console, json, prometheus (default: console)
    --component COMP     Check specific component: all, backend, database, redis, system
    --verbose           Show detailed information
    --exit-on-failure   Exit with code 1 if any check fails
    -h, --help          Show this help message

Examples:
    $0
    $0 --format json
    $0 --component database --verbose
    $0 --exit-on-failure

EOF
    exit 0
}

# =============================================================================
# Main Logic
# =============================================================================
main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --format)
                FORMAT="$2"
                shift 2
                ;;
            --component)
                COMPONENT="$2"
                shift 2
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --exit-on-failure)
                EXIT_ON_FAILURE=true
                shift
                ;;
            -h|--help)
                show_usage
                ;;
            *)
                echo "Unknown option: $1"
                show_usage
                ;;
        esac
    done

    if [ "$FORMAT" = "console" ]; then
        echo "=========================================="
        echo "iSwitch Roofs CRM - Health Check"
        echo "=========================================="
        echo ""
    fi

    # Run checks based on component
    case "$COMPONENT" in
        all)
            check_backend_health || true
            check_backend_endpoints || true
            check_database_health || true
            check_database_tables || true
            check_redis_health || true
            check_cache_performance || true
            check_system_resources || true
            ;;
        backend)
            check_backend_health || true
            check_backend_endpoints || true
            ;;
        database)
            check_database_health || true
            check_database_tables || true
            ;;
        redis)
            check_redis_health || true
            check_cache_performance || true
            ;;
        system)
            check_system_resources || true
            ;;
        *)
            echo "Unknown component: $COMPONENT"
            exit 1
            ;;
    esac

    # Output results
    case "$FORMAT" in
        console)
            output_console
            ;;
        json)
            output_json
            ;;
        prometheus)
            # TODO: Implement Prometheus format
            log_warning "Prometheus format not yet implemented"
            ;;
    esac

    # Exit with appropriate code
    if [ "$EXIT_ON_FAILURE" = true ] && [ "$OVERALL_HEALTH" = "unhealthy" ]; then
        exit 1
    fi

    exit 0
}

main "$@"
