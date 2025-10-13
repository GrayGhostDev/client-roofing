#!/bin/bash
# =============================================================================
# iSwitch Roofs CRM - Database & Redis Backup Script
# =============================================================================
# Automated backup with compression, encryption, and retention policies
#
# Usage:
#   ./scripts/backup.sh --destination local
#   ./scripts/backup.sh --destination s3 --bucket my-backups
#   ./scripts/backup.sh --encrypt --gpg-key admin@example.com
#   ./scripts/backup.sh --restore /path/to/backup.sql.gz
#
# =============================================================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Default values
DESTINATION="local"
S3_BUCKET=""
ENCRYPT=false
GPG_KEY=""
BACKUP_TYPE="full"  # full, database, redis
RESTORE_FILE=""
RETENTION_DAYS=7
RETENTION_WEEKS=4
RETENTION_MONTHS=12

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# =============================================================================
# Helper Functions
# =============================================================================
log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"; }
log_error() { echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $*" >&2; }
log_warning() { echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $*"; }

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

backup_database() {
    log "Starting PostgreSQL database backup..."

    local backup_file="$BACKUP_DIR/database_backup_$TIMESTAMP.sql"
    local compressed_file="${backup_file}.gz"

    # Extract connection details from DATABASE_URL
    if [ -z "${DATABASE_URL:-}" ]; then
        log_error "DATABASE_URL not set in .env"
        return 1
    fi

    # Parse DATABASE_URL (postgresql://user:pass@host:port/dbname)
    local db_user=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    local db_pass=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
    local db_host=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
    local db_port=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    local db_name=$(echo "$DATABASE_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')

    # Create backup
    log "Dumping database: $db_name"
    PGPASSWORD="$db_pass" pg_dump -h "$db_host" -p "$db_port" -U "$db_user" \
        -F plain -f "$backup_file" "$db_name" || {
        log_error "Database dump failed"
        return 1
    }

    # Get table count for verification
    local table_count=$(grep -c "CREATE TABLE" "$backup_file" || echo "0")
    log "Backed up $table_count tables"

    # Compress
    log "Compressing backup..."
    gzip "$backup_file"

    # Get final size
    local size=$(du -h "$compressed_file" | cut -f1)
    log "Compressed backup size: $size"

    # Encrypt if requested
    if [ "$ENCRYPT" = true ]; then
        log "Encrypting backup with GPG..."
        gpg --encrypt --recipient "$GPG_KEY" "$compressed_file"
        rm "$compressed_file"
        compressed_file="${compressed_file}.gpg"
        log "Encrypted backup: $compressed_file"
    fi

    # Store metadata
    cat > "${compressed_file}.meta" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "database": "$db_name",
  "host": "$db_host",
  "tables": $table_count,
  "size": "$size",
  "encrypted": $ENCRYPT,
  "file": "$(basename $compressed_file)"
}
EOF

    echo "$compressed_file"
}

backup_redis() {
    log "Starting Redis backup..."

    if [ -z "${REDIS_URL:-}" ]; then
        log_warning "REDIS_URL not set, skipping Redis backup"
        return 0
    fi

    local redis_host=$(echo "$REDIS_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p' || echo "localhost")
    local redis_port=$(echo "$REDIS_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p' || echo "6379")

    # Trigger Redis BGSAVE
    redis-cli -h "$redis_host" -p "$redis_port" BGSAVE

    # Wait for save to complete
    sleep 2
    while redis-cli -h "$redis_host" -p "$redis_port" LASTSAVE | grep -q "$(date +%s)"; do
        sleep 1
    done

    # Copy RDB file
    local rdb_source="/var/lib/redis/dump.rdb"
    local rdb_backup="$BACKUP_DIR/redis_backup_$TIMESTAMP.rdb"

    if [ -f "$rdb_source" ]; then
        cp "$rdb_source" "$rdb_backup"
        gzip "$rdb_backup"
        log "Redis backup completed: ${rdb_backup}.gz"
        echo "${rdb_backup}.gz"
    else
        log_warning "Redis RDB file not found at $rdb_source"
        return 0
    fi
}

upload_to_s3() {
    local file="$1"

    if [ -z "$S3_BUCKET" ]; then
        log_error "S3 bucket not specified"
        return 1
    fi

    log "Uploading to S3: s3://$S3_BUCKET/backups/$(basename $file)"

    aws s3 cp "$file" "s3://$S3_BUCKET/backups/" --storage-class STANDARD_IA || {
        log_error "S3 upload failed"
        return 1
    }

    # Upload metadata
    if [ -f "${file}.meta" ]; then
        aws s3 cp "${file}.meta" "s3://$S3_BUCKET/backups/"
    fi

    log "S3 upload completed"
}

upload_to_gcs() {
    local file="$1"
    local bucket="$S3_BUCKET"  # Reuse S3_BUCKET variable for GCS

    log "Uploading to Google Cloud Storage: gs://$bucket/backups/$(basename $file)"

    gsutil cp "$file" "gs://$bucket/backups/" || {
        log_error "GCS upload failed"
        return 1
    }

    log "GCS upload completed"
}

restore_database() {
    local backup_file="$1"

    log "Starting database restore from: $backup_file"

    # Decompress if needed
    if [[ "$backup_file" == *.gz ]]; then
        log "Decompressing backup..."
        gunzip -k "$backup_file"
        backup_file="${backup_file%.gz}"
    fi

    # Decrypt if needed
    if [[ "$backup_file" == *.gpg ]]; then
        log "Decrypting backup..."
        gpg --decrypt "$backup_file" > "${backup_file%.gpg}"
        backup_file="${backup_file%.gpg}"
    fi

    # Parse DATABASE_URL
    local db_user=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    local db_pass=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
    local db_host=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
    local db_port=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    local db_name=$(echo "$DATABASE_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')

    # Confirm restore
    read -p "⚠️  This will OVERWRITE the current database. Continue? (yes/no) " -r
    if [ "$REPLY" != "yes" ]; then
        log "Restore cancelled"
        return 0
    fi

    # Restore
    log "Restoring database..."
    PGPASSWORD="$db_pass" psql -h "$db_host" -p "$db_port" -U "$db_user" \
        -d "$db_name" -f "$backup_file" || {
        log_error "Database restore failed"
        return 1
    }

    log "✅ Database restored successfully"
}

apply_retention_policy() {
    log "Applying retention policy..."

    # Daily backups: keep for 7 days
    find "$BACKUP_DIR" -name "*backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

    # Weekly backups: keep for 4 weeks (assume Sunday backups)
    # TODO: Implement weekly logic

    # Monthly backups: keep for 12 months (assume 1st of month backups)
    # TODO: Implement monthly logic

    log "Retention policy applied"
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    --destination DEST      Backup destination: local, s3, gcs (default: local)
    --bucket BUCKET        S3/GCS bucket name (required for s3/gcs)
    --type TYPE            Backup type: full, database, redis (default: full)
    --encrypt              Encrypt backup with GPG
    --gpg-key EMAIL        GPG key for encryption
    --restore FILE         Restore from backup file
    -h, --help             Show this help message

Examples:
    $0 --destination local
    $0 --destination s3 --bucket my-backups
    $0 --encrypt --gpg-key admin@example.com
    $0 --restore /backups/database_backup_20250109_120000.sql.gz

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
            --destination)
                DESTINATION="$2"
                shift 2
                ;;
            --bucket)
                S3_BUCKET="$2"
                shift 2
                ;;
            --type)
                BACKUP_TYPE="$2"
                shift 2
                ;;
            --encrypt)
                ENCRYPT=true
                shift
                ;;
            --gpg-key)
                GPG_KEY="$2"
                shift 2
                ;;
            --restore)
                RESTORE_FILE="$2"
                shift 2
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

    # Create backup directory
    mkdir -p "$BACKUP_DIR"

    # Restore mode
    if [ -n "$RESTORE_FILE" ]; then
        restore_database "$RESTORE_FILE"
        exit 0
    fi

    # Backup mode
    echo "=========================================="
    echo "iSwitch Roofs CRM - Backup Script"
    echo "=========================================="
    echo "Destination: $DESTINATION"
    echo "Type: $BACKUP_TYPE"
    echo "=========================================="
    echo ""

    local backup_files=()

    # Perform backups
    case "$BACKUP_TYPE" in
        full)
            backup_files+=("$(backup_database)")
            backup_files+=("$(backup_redis)")
            ;;
        database)
            backup_files+=("$(backup_database)")
            ;;
        redis)
            backup_files+=("$(backup_redis)")
            ;;
        *)
            log_error "Unknown backup type: $BACKUP_TYPE"
            exit 1
            ;;
    esac

    # Upload to destination
    if [ "$DESTINATION" != "local" ]; then
        for file in "${backup_files[@]}"; do
            if [ -f "$file" ]; then
                case "$DESTINATION" in
                    s3)
                        upload_to_s3 "$file"
                        ;;
                    gcs)
                        upload_to_gcs "$file"
                        ;;
                esac
            fi
        done
    fi

    # Apply retention policy
    apply_retention_policy

    log "✅ Backup completed successfully"
    log "Backup files:"
    for file in "${backup_files[@]}"; do
        if [ -f "$file" ]; then
            log "  - $file"
        fi
    done
}

main "$@"
