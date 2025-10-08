#!/bin/bash
# iSwitch Roofs CRM - Database Backup Script
# Automated backup to Supabase storage

set -e

# Configuration
SUPABASE_PROJECT_ID="tdwpzktihdeuzapxoovk"
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="iswitch_crm_backup_${DATE}.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

echo "Starting database backup..."

# Export database using pg_dump
# Note: Supabase provides pg_dump access via their CLI
# Install: npm install -g supabase
# Login: supabase login

supabase db dump --project-ref $SUPABASE_PROJECT_ID > "$BACKUP_DIR/$BACKUP_FILE"

# Compress backup
echo "Compressing backup..."
gzip "$BACKUP_DIR/$BACKUP_FILE"

# Upload to cloud storage (optional)
# aws s3 cp "$BACKUP_DIR/${BACKUP_FILE}.gz" s3://your-backup-bucket/

echo "Backup completed: ${BACKUP_FILE}.gz"

# Cleanup old backups (keep last 30 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Old backups cleaned up"
