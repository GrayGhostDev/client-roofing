#!/usr/bin/env python3
"""
iSwitch Roofs CRM Database Migration Script

This script creates all required database tables by executing the SQL migration script
against the Supabase PostgreSQL database.

Usage:
    python backend/scripts/migrate_database.py

Requirements:
    - DATABASE_URL configured in .env file
    - create_tables.sql file exists in backend/
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
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('migration.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Handle database migration operations"""

    def __init__(self, database_url: str):
        """Initialize the migrator with database connection details"""
        self.database_url = database_url
        self.connection: Optional[psycopg2.extensions.connection] = None

    def connect(self) -> bool:
        """Establish connection to the database"""
        try:
            logger.info("Connecting to database...")
            self.connection = psycopg2.connect(self.database_url)
            self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            # Test connection
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                logger.info(f"Connected to PostgreSQL: {version}")

            return True

        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
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

def load_environment() -> bool:
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent.parent.parent / '.env'

    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment from: {env_path}")
        return True
    else:
        logger.warning(f"No .env file found at: {env_path}")
        return False

def get_database_url() -> Optional[str]:
    """Get database URL from environment variables"""
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        logger.error("DATABASE_URL not found in environment variables")
        logger.info("Please ensure DATABASE_URL is set in your .env file")
        return None

    # Mask password in log
    masked_url = database_url
    if '@' in masked_url:
        parts = masked_url.split('@')
        if ':' in parts[0]:
            user_pass = parts[0].split(':')
            if len(user_pass) >= 3:  # protocol:user:pass
                masked_url = f"{user_pass[0]}:{user_pass[1]}:****@{parts[1]}"

    logger.info(f"Database URL configured: {masked_url}")
    return database_url

def find_sql_file() -> Optional[Path]:
    """Find the SQL migration file"""
    # Look for create_tables.sql in backend directory
    sql_file = Path(__file__).parent.parent / 'create_tables.sql'

    if sql_file.exists():
        logger.info(f"Found SQL file: {sql_file}")
        return sql_file
    else:
        logger.error(f"SQL file not found: {sql_file}")
        return None

def main() -> int:
    """Main migration function"""
    logger.info("=" * 60)
    logger.info("iSwitch Roofs CRM Database Migration Started")
    logger.info("=" * 60)

    try:
        # Load environment
        if not load_environment():
            logger.warning("Continuing without .env file...")

        # Get database URL
        database_url = get_database_url()
        if not database_url:
            return 1

        # Find SQL file
        sql_file = find_sql_file()
        if not sql_file:
            return 1

        # Initialize migrator
        migrator = DatabaseMigrator(database_url)

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
                logger.info("✓ MIGRATION COMPLETED SUCCESSFULLY")
                logger.info("=" * 60)

                # Show table details
                for table in created_tables:
                    info = migrator.get_table_info(table)
                    if info:
                        logger.info(f"Table '{table}': {len(info['columns'])} columns, {info['row_count']} rows")

                logger.info("\nDatabase is ready for use!")
                return 0
            else:
                logger.error("=" * 60)
                logger.error("✗ MIGRATION FAILED")
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