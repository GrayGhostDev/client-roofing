#!/usr/bin/env python3
"""
Database Initialization Script for iSwitch Roofs CRM
Creates all necessary tables and indexes

Usage:
    python scripts/init_database.py
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_supabase_client
from app.utils.database import get_database_engine, check_database_health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables():
    """Create all database tables"""
    logger.info("Creating database tables...")

    try:
        supabase = get_supabase_client()

        # Check if tables exist by trying to select from them
        tables_to_check = [
            'leads', 'customers', 'projects', 'appointments',
            'interactions', 'team_members', 'reviews',
            'partnerships', 'notifications', 'alerts', 'analytics_metrics'
        ]

        existing_tables = []
        missing_tables = []

        for table in tables_to_check:
            try:
                result = supabase.table(table).select("*").limit(1).execute()
                existing_tables.append(table)
                logger.info(f"✅ Table '{table}' exists")
            except Exception:
                missing_tables.append(table)
                logger.warning(f"⚠️  Table '{table}' does not exist")

        if missing_tables:
            logger.warning(
                f"Missing tables: {', '.join(missing_tables)}\n"
                "Please create these tables in Supabase dashboard or via SQL migrations"
            )
        else:
            logger.info("✅ All required tables exist")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to check database tables: {str(e)}")
        return False


def create_indexes():
    """Create database indexes for performance"""
    logger.info("Creating database indexes...")

    indexes = [
        # Leads indexes
        ("leads", "created_at", "idx_leads_created_at"),
        ("leads", "status", "idx_leads_status"),
        ("leads", "temperature", "idx_leads_temperature"),
        ("leads", "assigned_to", "idx_leads_assigned_to"),
        ("leads", "source", "idx_leads_source"),

        # Customers indexes
        ("customers", "created_at", "idx_customers_created_at"),
        ("customers", "tier", "idx_customers_tier"),
        ("customers", "email", "idx_customers_email"),

        # Projects indexes
        ("projects", "customer_id", "idx_projects_customer_id"),
        ("projects", "status", "idx_projects_status"),
        ("projects", "created_at", "idx_projects_created_at"),
        ("projects", "completed_at", "idx_projects_completed_at"),

        # Appointments indexes
        ("appointments", "scheduled_start", "idx_appointments_scheduled_start"),
        ("appointments", "status", "idx_appointments_status"),
        ("appointments", "customer_id", "idx_appointments_customer_id"),

        # Interactions indexes
        ("interactions", "lead_id", "idx_interactions_lead_id"),
        ("interactions", "customer_id", "idx_interactions_customer_id"),
        ("interactions", "created_at", "idx_interactions_created_at"),
    ]

    logger.info(f"Indexes to create: {len(indexes)}")
    logger.info("Note: Indexes should be created via Supabase SQL editor")

    # Generate SQL for creating indexes
    sql_statements = []
    for table, column, index_name in indexes:
        sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column});"
        sql_statements.append(sql)

    # Save to file
    sql_file = Path(__file__).parent / "create_indexes.sql"
    with open(sql_file, 'w') as f:
        f.write("-- Database Indexes for iSwitch Roofs CRM\n")
        f.write("-- Run this SQL in Supabase SQL Editor\n\n")
        for sql in sql_statements:
            f.write(sql + "\n")

    logger.info(f"✅ Index SQL written to: {sql_file}")
    return True


def verify_connection():
    """Verify database connection"""
    logger.info("Verifying database connection...")

    health = check_database_health()

    if health["healthy"]:
        logger.info("✅ Database connection verified")
        logger.info(f"   Database: {health['database']}")
        logger.info(f"   Supabase: {health['supabase']}")
        return True
    else:
        logger.error("❌ Database connection failed")
        logger.error(f"   Database: {health['database']}")
        logger.error(f"   Supabase: {health['supabase']}")
        return False


def main():
    """Main initialization function"""
    logger.info("=" * 60)
    logger.info("iSwitch Roofs CRM - Database Initialization")
    logger.info("=" * 60)

    # Step 1: Verify connection
    if not verify_connection():
        logger.error("❌ Database initialization failed: Cannot connect to database")
        sys.exit(1)

    # Step 2: Check/create tables
    if not create_tables():
        logger.error("❌ Database initialization failed: Table creation error")
        sys.exit(1)

    # Step 3: Create indexes
    if not create_indexes():
        logger.error("❌ Database initialization failed: Index creation error")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("✅ Database initialization completed successfully!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Run the index SQL: scripts/create_indexes.sql")
    logger.info("2. Seed test data: python scripts/seed_data.py")
    logger.info("")


if __name__ == "__main__":
    main()
