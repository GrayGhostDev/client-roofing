#!/usr/bin/env python3
"""
iSwitch Roofs CRM Database Migration Script (Local Development)

This script creates all required database tables by executing the SQL migration script
against a local PostgreSQL database (for development).

Usage:
    python backend/scripts/migrate_database_local.py

Requirements:
    - Local PostgreSQL database running
    - create_tables_local.sql file exists in backend/
    - psycopg2 package installed

Author: Database Architect Agent
Date: 2025-10-05
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple, List
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('migration_local.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

class LocalDatabaseMigrator:
    """Handle local database migration operations"""

    def __init__(self, database_url: str):
        """Initialize the migrator with database connection details"""
        self.database_url = database_url
        self.connection: Optional[psycopg2.extensions.connection] = None

    def connect(self) -> bool:
        """Establish connection to the database"""
        try:
            logger.info("Connecting to local PostgreSQL database...")

            # Parse the existing DATABASE_URL to get local connection info
            # For development, we'll connect to the local database detected from the error
            local_db_url = "postgresql://eduplatform@localhost/educational_platform_dev"

            self.connection = psycopg2.connect(local_db_url)
            self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            # Test connection
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                logger.info(f"Connected to PostgreSQL: {version}")

            return True

        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            logger.info("Make sure your local PostgreSQL is running and accessible")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during connection: {e}")
            return False

    def disconnect(self) -> None:
        """Close database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info("Database connection closed")

    def execute_sql_file(self, sql_file_path: Path) -> bool:
        """Execute SQL commands from file"""
        try:
            if not sql_file_path.exists():
                logger.error(f"SQL file not found: {sql_file_path}")
                return False

            with open(sql_file_path, 'r', encoding='utf-8') as file:
                sql_content = file.read()

            logger.info(f"Executing SQL from: {sql_file_path}")
            logger.info(f"SQL content size: {len(sql_content)} characters")

            with self.connection.cursor() as cursor:
                cursor.execute(sql_content)

            logger.info("SQL execution completed successfully")
            return True

        except psycopg2.Error as e:
            logger.error(f"SQL execution failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during SQL execution: {e}")
            return False

    def verify_tables_created(self) -> Tuple[bool, List[str]]:
        """Verify that all expected tables were created"""
        expected_tables = [
            'leads', 'customers', 'team_members', 'appointments',
            'projects', 'interactions', 'reviews', 'partnerships',
            'notifications', 'alerts'
        ]

        try:
            with self.connection.cursor() as cursor:
                # Query to get all table names
                cursor.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """)

                existing_tables = [row[0] for row in cursor.fetchall()]
                logger.info(f"Found {len(existing_tables)} tables in database")

                missing_tables = []
                created_tables = []

                for table in expected_tables:
                    if table in existing_tables:
                        created_tables.append(table)
                        logger.info(f"✓ Table '{table}' exists")
                    else:
                        missing_tables.append(table)
                        logger.warning(f"✗ Table '{table}' missing")

                # Check for unexpected tables
                unexpected_tables = [t for t in existing_tables if t not in expected_tables]
                if unexpected_tables:
                    logger.info(f"Additional tables found: {', '.join(unexpected_tables)}")

                success = len(missing_tables) == 0
                if success:
                    logger.info(f"✓ All {len(expected_tables)} expected tables verified")
                else:
                    logger.error(f"✗ {len(missing_tables)} tables missing: {', '.join(missing_tables)}")

                return success, created_tables

        except psycopg2.Error as e:
            logger.error(f"Table verification failed: {e}")
            return False, []
        except Exception as e:
            logger.error(f"Unexpected error during table verification: {e}")
            return False, []

    def get_table_info(self, table_name: str) -> Optional[dict]:
        """Get detailed information about a specific table"""
        try:
            with self.connection.cursor() as cursor:
                # Get column information
                cursor.execute("""
                    SELECT
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = %s
                    ORDER BY ordinal_position;
                """, (table_name,))

                columns = cursor.fetchall()

                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                row_count = cursor.fetchone()[0]

                return {
                    'columns': columns,
                    'row_count': row_count
                }

        except psycopg2.Error as e:
            logger.error(f"Failed to get table info for '{table_name}': {e}")
            return None

def find_local_sql_file() -> Optional[Path]:
    """Find the local SQL migration file"""
    # Look for create_tables_local.sql in backend directory
    sql_file = Path(__file__).parent.parent / 'create_tables_local.sql'

    if sql_file.exists():
        logger.info(f"Found local SQL file: {sql_file}")
        return sql_file
    else:
        logger.error(f"Local SQL file not found: {sql_file}")
        return None

def main() -> int:
    """Main migration function"""
    logger.info("=" * 60)
    logger.info("iSwitch Roofs CRM Local Database Migration Started")
    logger.info("=" * 60)

    try:
        # Find SQL file
        sql_file = find_local_sql_file()
        if not sql_file:
            return 1

        # Initialize migrator (dummy URL, we'll use local connection)
        migrator = LocalDatabaseMigrator("dummy")

        try:
            # Connect to database
            if not migrator.connect():
                return 1

            # Execute migration
            logger.info("Starting database migration...")
            if not migrator.execute_sql_file(sql_file):
                return 1

            # Verify tables
            logger.info("Verifying table creation...")
            success, created_tables = migrator.verify_tables_created()

            if success:
                logger.info("=" * 60)
                logger.info("✓ LOCAL MIGRATION COMPLETED SUCCESSFULLY")
                logger.info("=" * 60)

                # Show table details
                for table in created_tables:
                    info = migrator.get_table_info(table)
                    if info:
                        logger.info(f"Table '{table}': {len(info['columns'])} columns, {info['row_count']} rows")

                logger.info("\nLocal database is ready for development!")
                logger.info("Note: For production, use the Supabase migration script with proper credentials.")
                return 0
            else:
                logger.error("=" * 60)
                logger.error("✗ LOCAL MIGRATION FAILED")
                logger.error("=" * 60)
                return 1

        finally:
            migrator.disconnect()

    except KeyboardInterrupt:
        logger.info("\nMigration interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)