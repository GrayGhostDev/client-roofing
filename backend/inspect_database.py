#!/usr/bin/env python3
"""
Database Schema Inspector
Lists actual tables and structures in Supabase
"""

import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from app import create_app
from app.utils.supabase_client import SupabaseService


def inspect_database_schema():
    """Inspect the actual database schema"""
    print("🔍 Inspecting Supabase Database Schema...")
    print("=" * 60)

    app = create_app("development")

    with app.app_context():
        try:
            service = SupabaseService(use_admin=True)
            client = service.client

            # Try to execute a raw SQL query to get table information
            try:
                # Get all tables in public schema
                result = client.rpc(
                    "sql",
                    {
                        "query": """
                    SELECT table_name, table_type
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """
                    },
                ).execute()

                if result.data:
                    print("📋 Tables in public schema:")
                    for row in result.data:
                        print(f"  - {row['table_name']} ({row['table_type']})")
                else:
                    print("❌ No tables found or RPC not available")

            except Exception as e:
                print(f"❌ SQL query failed: {e}")

            # Try to list any available tables through PostgREST
            print("\n🔍 Attempting to discover tables via API...")

            # Common table names to test
            test_tables = [
                "leads",
                "customers",
                "projects",
                "appointments",
                "team_members",
                "interactions",
                "reviews",
                "partnerships",
                "analytics",
                "alerts",
                "users",
                "profiles",
            ]

            found_tables = []
            for table in test_tables:
                try:
                    response = client.table(table).select("*").limit(1).execute()
                    if response.data is not None:
                        found_tables.append(table)
                        print(f"✅ {table} - accessible")
                    else:
                        print(f"❌ {table} - not found")
                except Exception as e:
                    if "PGRST205" not in str(e):
                        print(f"⚠️ {table} - error: {str(e)}")
                    else:
                        print(f"❌ {table} - not found")

            if found_tables:
                print(
                    f"\n✅ Found {len(found_tables)} accessible tables: {', '.join(found_tables)}"
                )
            else:
                print("\n❌ No accessible tables found")

            # Check for any system tables
            print("\n🔍 Checking system information...")
            try:
                # Try to get schema information
                result = client.from_("information_schema.schemata").select("schema_name").execute()
                if result.data:
                    schemas = [row["schema_name"] for row in result.data]
                    print(f"📊 Available schemas: {', '.join(schemas)}")
            except Exception as e:
                print(f"⚠️ Could not access schema information: {e}")

        except Exception as e:
            print(f"❌ Database inspection failed: {e}")


if __name__ == "__main__":
    inspect_database_schema()
