#!/usr/bin/env python3
"""
Database Utility Script for iSwitch Roofs CRM

Provides common database operations for development and testing.

Usage:
    python backend/scripts/db_utils.py --help
    python backend/scripts/db_utils.py --check-tables
    python backend/scripts/db_utils.py --sample-data
    python backend/scripts/db_utils.py --clear-data

Author: Database Architect Agent
Date: 2025-10-05
"""

import argparse
import logging
import sys

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class DatabaseUtils:
    """Database utility operations"""

    def __init__(self):
        """Initialize connection to local database"""
        self.db_url = "postgresql://eduplatform@localhost/educational_platform_dev"
        self.connection = None

    def connect(self) -> bool:
        """Connect to database"""
        try:
            self.connection = psycopg2.connect(self.db_url)
            self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            return True
        except psycopg2.Error as e:
            logger.error(f"Connection failed: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close()

    def check_tables(self):
        """Check all CRM tables and their data"""
        logger.info("Checking iSwitch Roofs CRM Tables")
        logger.info("=" * 50)

        crm_tables = [
            "leads",
            "customers",
            "team_members",
            "appointments",
            "projects",
            "interactions",
            "reviews",
            "partnerships",
            "notifications",
            "alerts",
        ]

        try:
            with self.connection.cursor() as cursor:
                for table in crm_tables:
                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]

                    # Get recent records info
                    cursor.execute(
                        f"""
                        SELECT created_at FROM {table}
                        ORDER BY created_at DESC LIMIT 1
                    """
                    )
                    result = cursor.fetchone()
                    last_created = (
                        result[0].strftime("%Y-%m-%d %H:%M:%S") if result else "No records"
                    )

                    status = "✅" if count > 0 else "⚪"
                    logger.info(f"{status} {table:<15} | {count:>4} records | Last: {last_created}")

        except psycopg2.Error as e:
            logger.error(f"Error checking tables: {e}")

    def show_sample_data(self):
        """Display sample data from key tables"""
        logger.info("Sample Data from CRM Tables")
        logger.info("=" * 50)

        try:
            with self.connection.cursor() as cursor:
                # Show leads
                logger.info("\n📋 LEADS (Sample):")
                cursor.execute(
                    """
                    SELECT first_name, last_name, city, lead_score, status
                    FROM leads
                    ORDER BY created_at DESC
                    LIMIT 3
                """
                )
                for row in cursor.fetchall():
                    logger.info(f"  • {row[0]} {row[1]} | {row[2]} | Score: {row[3]} | {row[4]}")

                # Show customers
                logger.info("\n👥 CUSTOMERS (Sample):")
                cursor.execute(
                    """
                    SELECT first_name, last_name, city, lifetime_value, status
                    FROM customers
                    ORDER BY created_at DESC
                    LIMIT 3
                """
                )
                for row in cursor.fetchall():
                    logger.info(f"  • {row[0]} {row[1]} | {row[2]} | LTV: ${row[3]:,} | {row[4]}")

                # Show team members
                logger.info("\n👨‍💼 TEAM MEMBERS:")
                cursor.execute(
                    """
                    SELECT first_name, last_name, email, role, status
                    FROM team_members
                    ORDER BY created_at DESC
                """
                )
                for row in cursor.fetchall():
                    logger.info(f"  • {row[0]} {row[1]} | {row[2]} | {row[3]} | {row[4]}")

        except psycopg2.Error as e:
            logger.error(f"Error showing sample data: {e}")

    def clear_sample_data(self):
        """Clear sample data (keep table structure)"""
        logger.info("Clearing Sample Data from CRM Tables")
        logger.info("=" * 50)

        tables = [
            "interactions",
            "reviews",
            "appointments",
            "projects",
            "notifications",
            "alerts",
            "partnerships",
            "leads",
            "customers",
        ]

        try:
            with self.connection.cursor() as cursor:
                for table in tables:
                    cursor.execute(f"DELETE FROM {table}")
                    logger.info(f"✅ Cleared {table}")

                # Keep one team member for testing
                cursor.execute(
                    "DELETE FROM team_members WHERE email != 'john.sales@iswitchroofs.com'"
                )
                logger.info("✅ Cleared team_members (kept John Sales)")

            logger.info("\n🔄 Sample data cleared. Tables are ready for fresh data.")

        except psycopg2.Error as e:
            logger.error(f"Error clearing data: {e}")

    def add_more_sample_data(self):
        """Add additional sample data for testing"""
        logger.info("Adding Extended Sample Data")
        logger.info("=" * 50)

        try:
            with self.connection.cursor() as cursor:
                # Add more team members
                team_members = [
                    ("Sarah", "Manager", "sarah.manager@iswitchroofs.com", "sales_manager"),
                    ("Mike", "Estimator", "mike.estimator@iswitchroofs.com", "estimator"),
                    ("Lisa", "Coordinator", "lisa.coord@iswitchroofs.com", "project_coordinator"),
                ]

                for first_name, last_name, email, role in team_members:
                    cursor.execute(
                        """
                        INSERT INTO team_members (first_name, last_name, email, role)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (email) DO NOTHING
                    """,
                        (first_name, last_name, email, role),
                    )

                # Add more leads
                leads = [
                    (
                        "Amanda",
                        "Thompson",
                        "248-555-9999",
                        "amanda.t@email.com",
                        "google_ads",
                        "Birmingham",
                        "MI",
                        "48009",
                        "qualified",
                        88,
                    ),
                    (
                        "James",
                        "Miller",
                        "313-555-8888",
                        "james.miller@email.com",
                        "referral",
                        "Grosse Pointe",
                        "MI",
                        "48236",
                        "contacted",
                        92,
                    ),
                    (
                        "Patricia",
                        "Anderson",
                        "586-555-7777",
                        "patricia.a@email.com",
                        "facebook_ads",
                        "Rochester Hills",
                        "MI",
                        "48309",
                        "new",
                        67,
                    ),
                ]

                for (
                    first_name,
                    last_name,
                    phone,
                    email,
                    source,
                    city,
                    state,
                    zip_code,
                    status,
                    score,
                ) in leads:
                    cursor.execute(
                        """
                        INSERT INTO leads (first_name, last_name, phone, email, source, city, state, zip_code, status, lead_score)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                        (
                            first_name,
                            last_name,
                            phone,
                            email,
                            source,
                            city,
                            state,
                            zip_code,
                            status,
                            score,
                        ),
                    )

                logger.info("✅ Added 3 team members and 3 leads")
                logger.info("🎯 Database now has expanded sample data for testing")

        except psycopg2.Error as e:
            logger.error(f"Error adding sample data: {e}")


def main():
    """Main function with command line arguments"""
    parser = argparse.ArgumentParser(description="iSwitch Roofs CRM Database Utilities")
    parser.add_argument("--check-tables", action="store_true", help="Check all CRM tables")
    parser.add_argument("--sample-data", action="store_true", help="Show sample data")
    parser.add_argument("--clear-data", action="store_true", help="Clear sample data")
    parser.add_argument("--add-data", action="store_true", help="Add more sample data")

    args = parser.parse_args()

    # Show help if no arguments
    if not any(vars(args).values()):
        parser.print_help()
        return

    # Initialize database utilities
    db_utils = DatabaseUtils()

    try:
        if not db_utils.connect():
            sys.exit(1)

        if args.check_tables:
            db_utils.check_tables()

        if args.sample_data:
            db_utils.show_sample_data()

        if args.clear_data:
            confirm = input("Are you sure you want to clear all sample data? (yes/no): ")
            if confirm.lower() == "yes":
                db_utils.clear_sample_data()
            else:
                logger.info("Operation cancelled.")

        if args.add_data:
            db_utils.add_more_sample_data()

    finally:
        db_utils.disconnect()


if __name__ == "__main__":
    main()
