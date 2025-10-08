"""
Database Optimization & Performance Analyzer
Analyzes query performance, recommends indexes, and optimizes database operations
"""

import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from supabase import create_client, Client


class DatabaseOptimizer:
    """Database optimization and performance analysis tool"""

    def __init__(self):
        """Initialize database connection"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY', os.getenv('SUPABASE_KEY'))

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

        self.client: Client = create_client(self.supabase_url, self.supabase_key)

    def analyze_table_sizes(self) -> Dict[str, dict]:
        """
        Analyze table sizes and row counts

        Returns:
            Dictionary of table statistics
        """
        print("\n" + "="*80)
        print("TABLE SIZE ANALYSIS")
        print("="*80)

        tables = [
            'leads', 'customers', 'projects', 'interactions',
            'appointments', 'team_members', 'reviews', 'partnerships',
            'notifications', 'analytics_cache'
        ]

        stats = {}

        for table in tables:
            try:
                # Get row count
                response = self.client.table(table).select('id', count='exact').limit(1).execute()
                row_count = response.count if hasattr(response, 'count') else 0

                stats[table] = {
                    'row_count': row_count,
                    'status': '✅' if row_count > 0 else '⚠️'
                }

                print(f"\n{stats[table]['status']} {table}")
                print(f"   Rows: {row_count:,}")

            except Exception as e:
                stats[table] = {
                    'row_count': 0,
                    'status': '❌',
                    'error': str(e)
                }
                print(f"\n❌ {table}")
                print(f"   Error: {str(e)}")

        return stats

    def analyze_query_performance(self) -> List[Dict]:
        """
        Analyze common query performance

        Returns:
            List of query performance metrics
        """
        print("\n" + "="*80)
        print("QUERY PERFORMANCE ANALYSIS")
        print("="*80)

        queries = [
            {
                'name': 'Get Hot Leads',
                'table': 'leads',
                'filters': {'temperature': 'hot', 'status': 'new'},
                'expected_ms': 100
            },
            {
                'name': 'Get Recent Leads',
                'table': 'leads',
                'order': 'created_at.desc',
                'limit': 50,
                'expected_ms': 150
            },
            {
                'name': 'Get Active Projects',
                'table': 'projects',
                'filters': {'status': 'in_progress'},
                'expected_ms': 100
            },
            {
                'name': 'Get Upcoming Appointments',
                'table': 'appointments',
                'order': 'scheduled_time.asc',
                'limit': 20,
                'expected_ms': 100
            },
            {
                'name': 'Get Customer Interactions',
                'table': 'interactions',
                'order': 'created_at.desc',
                'limit': 100,
                'expected_ms': 200
            }
        ]

        results = []

        for query_info in queries:
            try:
                # Build query
                query = self.client.table(query_info['table']).select('*')

                # Add filters
                if 'filters' in query_info:
                    for key, value in query_info['filters'].items():
                        query = query.eq(key, value)

                # Add ordering
                if 'order' in query_info:
                    query = query.order(query_info['order'])

                # Add limit
                if 'limit' in query_info:
                    query = query.limit(query_info['limit'])

                # Measure execution time
                start_time = time.time()
                response = query.execute()
                execution_time_ms = (time.time() - start_time) * 1000

                # Determine status
                expected = query_info['expected_ms']
                if execution_time_ms < expected:
                    status = '✅ GOOD'
                elif execution_time_ms < expected * 2:
                    status = '⚠️ SLOW'
                else:
                    status = '❌ VERY SLOW'

                result = {
                    'name': query_info['name'],
                    'execution_time_ms': execution_time_ms,
                    'expected_ms': expected,
                    'status': status,
                    'row_count': len(response.data) if response.data else 0
                }

                results.append(result)

                print(f"\n{status} {query_info['name']}")
                print(f"   Execution Time: {execution_time_ms:.2f}ms (expected: {expected}ms)")
                print(f"   Rows Returned: {result['row_count']}")

            except Exception as e:
                result = {
                    'name': query_info['name'],
                    'execution_time_ms': 0,
                    'expected_ms': query_info['expected_ms'],
                    'status': '❌ ERROR',
                    'error': str(e)
                }
                results.append(result)
                print(f"\n❌ ERROR: {query_info['name']}")
                print(f"   {str(e)}")

        return results

    def recommend_indexes(self) -> List[Dict]:
        """
        Recommend database indexes based on common queries

        Returns:
            List of index recommendations
        """
        print("\n" + "="*80)
        print("INDEX RECOMMENDATIONS")
        print("="*80)

        recommendations = [
            {
                'table': 'leads',
                'columns': ['status', 'temperature'],
                'reason': 'Filtering hot/warm leads by status is very common',
                'type': 'composite',
                'priority': 'HIGH'
            },
            {
                'table': 'leads',
                'columns': ['created_at'],
                'reason': 'Sorting leads by creation date for dashboards',
                'type': 'single',
                'priority': 'HIGH'
            },
            {
                'table': 'leads',
                'columns': ['assigned_to', 'status'],
                'reason': 'Team members frequently filter their assigned leads',
                'type': 'composite',
                'priority': 'HIGH'
            },
            {
                'table': 'leads',
                'columns': ['source'],
                'reason': 'Lead source reporting and analytics',
                'type': 'single',
                'priority': 'MEDIUM'
            },
            {
                'table': 'customers',
                'columns': ['phone'],
                'reason': 'Phone number lookup for call tracking',
                'type': 'single',
                'priority': 'HIGH'
            },
            {
                'table': 'customers',
                'columns': ['email'],
                'reason': 'Email lookup for communications',
                'type': 'single',
                'priority': 'MEDIUM'
            },
            {
                'table': 'projects',
                'columns': ['status', 'start_date'],
                'reason': 'Active project tracking and scheduling',
                'type': 'composite',
                'priority': 'HIGH'
            },
            {
                'table': 'projects',
                'columns': ['customer_id'],
                'reason': 'Foreign key relationship queries',
                'type': 'single',
                'priority': 'HIGH'
            },
            {
                'table': 'interactions',
                'columns': ['lead_id', 'created_at'],
                'reason': 'Lead interaction timeline queries',
                'type': 'composite',
                'priority': 'HIGH'
            },
            {
                'table': 'interactions',
                'columns': ['customer_id', 'created_at'],
                'reason': 'Customer interaction history',
                'type': 'composite',
                'priority': 'HIGH'
            },
            {
                'table': 'appointments',
                'columns': ['scheduled_time', 'status'],
                'reason': 'Upcoming appointments dashboard',
                'type': 'composite',
                'priority': 'HIGH'
            },
            {
                'table': 'appointments',
                'columns': ['assigned_to'],
                'reason': 'Team member schedule queries',
                'type': 'single',
                'priority': 'MEDIUM'
            },
            {
                'table': 'reviews',
                'columns': ['rating', 'created_at'],
                'reason': 'Review analytics and trending',
                'type': 'composite',
                'priority': 'MEDIUM'
            },
            {
                'table': 'team_members',
                'columns': ['role', 'is_active'],
                'reason': 'Active team member queries by role',
                'type': 'composite',
                'priority': 'MEDIUM'
            },
            {
                'table': 'notifications',
                'columns': ['user_id', 'read', 'created_at'],
                'reason': 'Unread notification queries',
                'type': 'composite',
                'priority': 'HIGH'
            }
        ]

        for rec in recommendations:
            priority_icon = {
                'HIGH': '🔴',
                'MEDIUM': '🟡',
                'LOW': '🟢'
            }.get(rec['priority'], '⚪')

            columns_str = ', '.join(rec['columns'])

            print(f"\n{priority_icon} {rec['priority']} PRIORITY")
            print(f"   Table: {rec['table']}")
            print(f"   Columns: {columns_str}")
            print(f"   Type: {rec['type']}")
            print(f"   Reason: {rec['reason']}")

        return recommendations

    def generate_index_sql(self, recommendations: List[Dict]) -> str:
        """
        Generate SQL statements for creating indexes

        Args:
            recommendations: List of index recommendations

        Returns:
            SQL script as string
        """
        sql_statements = []
        sql_statements.append("-- Database Index Creation Script")
        sql_statements.append(f"-- Generated: {datetime.now().isoformat()}")
        sql_statements.append("-- Run this script in your Supabase SQL editor\n")

        for rec in recommendations:
            table = rec['table']
            columns = rec['columns']

            # Generate index name
            columns_str = '_'.join(columns)
            index_name = f"idx_{table}_{columns_str}"

            # Generate SQL
            columns_list = ', '.join(columns)
            sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({columns_list});"

            sql_statements.append(f"-- {rec['reason']}")
            sql_statements.append(sql)
            sql_statements.append("")

        return '\n'.join(sql_statements)

    def analyze_slow_queries(self) -> List[Dict]:
        """
        Identify potentially slow query patterns

        Returns:
            List of slow query patterns
        """
        print("\n" + "="*80)
        print("SLOW QUERY PATTERNS")
        print("="*80)

        patterns = [
            {
                'pattern': 'Full table scan on leads without filters',
                'risk': 'HIGH',
                'solution': 'Always include WHERE clauses for status, temperature, or date range'
            },
            {
                'pattern': 'Sorting large result sets without LIMIT',
                'risk': 'HIGH',
                'solution': 'Add LIMIT clause to pagination queries'
            },
            {
                'pattern': 'Multiple JOINs without proper indexes',
                'risk': 'MEDIUM',
                'solution': 'Ensure foreign keys have indexes'
            },
            {
                'pattern': 'LIKE queries with leading wildcard (%term)',
                'risk': 'MEDIUM',
                'solution': 'Use full-text search or trigram indexes'
            },
            {
                'pattern': 'N+1 query problem (loading related records)',
                'risk': 'HIGH',
                'solution': 'Use eager loading with joins or select/prefetch'
            }
        ]

        for pattern_info in patterns:
            risk_icon = {
                'HIGH': '🔴',
                'MEDIUM': '🟡',
                'LOW': '🟢'
            }.get(pattern_info['risk'], '⚪')

            print(f"\n{risk_icon} {pattern_info['risk']} RISK")
            print(f"   Pattern: {pattern_info['pattern']}")
            print(f"   Solution: {pattern_info['solution']}")

        return patterns

    def generate_backup_script(self) -> str:
        """
        Generate backup script for database

        Returns:
            Backup script as string
        """
        script = """#!/bin/bash
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
"""
        return script

    def generate_migration_rollback_guide(self) -> str:
        """
        Generate migration rollback procedures

        Returns:
            Rollback guide as string
        """
        guide = """# Database Migration Rollback Guide

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
"""
        return guide

    def run_full_analysis(self):
        """Run complete database optimization analysis"""
        print("\n" + "="*80)
        print("DATABASE OPTIMIZATION & PERFORMANCE ANALYSIS")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

        # 1. Table size analysis
        table_stats = self.analyze_table_sizes()

        # 2. Query performance analysis
        query_results = self.analyze_query_performance()

        # 3. Index recommendations
        recommendations = self.recommend_indexes()

        # 4. Slow query patterns
        slow_patterns = self.analyze_slow_queries()

        # 5. Generate SQL script
        print("\n" + "="*80)
        print("GENERATING SQL SCRIPT")
        print("="*80)

        sql_script = self.generate_index_sql(recommendations)
        sql_file = 'backend/database_indexes.sql'

        with open(sql_file, 'w') as f:
            f.write(sql_script)

        print(f"\n✅ SQL script saved: {sql_file}")

        # 6. Generate backup script
        backup_script = self.generate_backup_script()
        backup_file = 'backend/backup_database.sh'

        with open(backup_file, 'w') as f:
            f.write(backup_script)

        print(f"✅ Backup script saved: {backup_file}")

        # 7. Generate rollback guide
        rollback_guide = self.generate_migration_rollback_guide()
        rollback_file = 'backend/MIGRATION_ROLLBACK_GUIDE.md'

        with open(rollback_file, 'w') as f:
            f.write(rollback_guide)

        print(f"✅ Rollback guide saved: {rollback_file}")

        # Summary
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)

        total_tables = len(table_stats)
        active_tables = sum(1 for s in table_stats.values() if s['status'] == '✅')

        print(f"\n📊 Database Statistics:")
        print(f"   Total Tables: {total_tables}")
        print(f"   Active Tables: {active_tables}")

        print(f"\n⚡ Query Performance:")
        good_queries = sum(1 for q in query_results if '✅' in q['status'])
        print(f"   Good Performance: {good_queries}/{len(query_results)}")

        print(f"\n📈 Index Recommendations:")
        high_priority = sum(1 for r in recommendations if r['priority'] == 'HIGH')
        print(f"   High Priority: {high_priority}")
        print(f"   Total Recommendations: {len(recommendations)}")

        print(f"\n📁 Generated Files:")
        print(f"   {sql_file}")
        print(f"   {backup_file}")
        print(f"   {rollback_file}")

        print("\n" + "="*80)


def main():
    """Main function"""
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Run analysis
    optimizer = DatabaseOptimizer()
    optimizer.run_full_analysis()


if __name__ == '__main__':
    main()
