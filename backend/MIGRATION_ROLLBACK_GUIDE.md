# Database Migration Rollback Guide

## Pre-Migration Checklist

Before running ANY migration:
1. ✅ Create full database backup
2. ✅ Test migration in development environment
3. ✅ Document all changes being made
4. ✅ Have rollback SQL ready
5. ✅ Schedule during low-traffic period

## Rollback Procedures

### 1. Automated Rollback (Alembic)

```bash
# View migration history
alembic history

# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

### 2. Manual Rollback (SQL)

If automated rollback fails:

```sql
-- 1. Begin transaction
BEGIN;

-- 2. Rollback schema changes
DROP INDEX IF EXISTS idx_leads_status_temperature;
ALTER TABLE leads DROP COLUMN IF EXISTS new_column;

-- 3. Restore data from backup if needed
-- (Use pg_restore or copy from backup)

-- 4. Verify changes
SELECT * FROM leads LIMIT 5;

-- 5. Commit if everything looks good
COMMIT;
-- Or rollback if issues found
-- ROLLBACK;
```

### 3. Emergency Restore from Backup

```bash
# Stop application
systemctl stop iswitch-crm

# Restore from backup
supabase db reset --project-ref tdwpzktihdeuzapxoovk
pg_restore --dbname=postgresql://... backup.sql

# Restart application
systemctl start iswitch-crm
```

## Migration Best Practices

1. **Small, Incremental Changes**
   - One logical change per migration
   - Easier to rollback individual changes

2. **Test Rollback Procedure**
   - Test downgrade in development
   - Ensure data integrity after rollback

3. **Data Migrations**
   - Separate data migrations from schema migrations
   - Always have a rollback for data changes

4. **Zero-Downtime Migrations**
   - Add new columns as nullable first
   - Deploy code that works with both schemas
   - Remove old columns in separate migration

5. **Monitor After Migration**
   - Check error logs
   - Verify application functionality
   - Monitor query performance
