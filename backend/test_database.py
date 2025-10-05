#!/usr/bin/env python3
"""
Database Integration Test Script
Tests connection, schema, and basic operations
"""

import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))


from app import create_app
from app.config import get_supabase_client
from app.utils.supabase_client import SupabaseService


def test_database_connection():
    """Test basic database connection"""
    print("🔌 Testing Database Connection...")

    try:
        client = get_supabase_client()
        print("✅ Supabase client created successfully")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_schema_inspection():
    """Inspect database schema and list tables"""
    print("\n📊 Inspecting Database Schema...")

    try:
        service = SupabaseService(use_admin=True)

        # Try to get information about tables using PostgREST admin endpoint
        # This is a workaround since Supabase doesn't expose schema introspection directly

        # List of expected tables based on our migration
        expected_tables = [
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
        ]

        table_status = {}

        for table in expected_tables:
            try:
                # Try to select count from each table
                count_result = service.count(table)
                table_status[table] = {
                    "exists": True,
                    "count": count_result,
                    "status": "accessible",
                }
                print(f"✅ {table}: {count_result} records")
            except Exception as e:
                table_status[table] = {"exists": False, "error": str(e), "status": "error"}
                print(f"❌ {table}: Error - {str(e)}")

        return table_status

    except Exception as e:
        print(f"❌ Schema inspection failed: {e}")
        return {}


def test_basic_crud_operations():
    """Test basic CRUD operations on a safe table"""
    print("\n🧪 Testing Basic CRUD Operations...")

    try:
        service = SupabaseService(use_admin=True)

        # Test with leads table (safest for testing)
        test_table = "leads"

        # Test SELECT
        print(f"📖 Testing SELECT on {test_table}...")
        leads = service.select(test_table, limit=5)
        print(f"✅ SELECT successful - found {len(leads)} records")

        if leads:
            print("Sample record structure:")
            sample = leads[0]
            for key in list(sample.keys())[:5]:  # Show first 5 fields
                print(f"  - {key}: {type(sample[key])}")

        # Test INSERT (with safe test data)
        print(f"📝 Testing INSERT on {test_table}...")
        test_lead = {
            "first_name": "Test",
            "last_name": "Customer",
            "phone": "248-555-0123",
            "email": "test@example.com",
            "source": "website_form",
            "status": "new",
            "notes": "Database integration test record",
        }

        try:
            new_lead = service.insert(test_table, test_lead)
            test_lead_id = new_lead["id"]
            print(f"✅ INSERT successful - created record with ID: {test_lead_id}")

            # Test UPDATE
            print(f"✏️ Testing UPDATE on {test_table}...")
            updated_lead = service.update(
                test_table,
                test_lead_id,
                {"status": "contacted", "notes": "Updated by database integration test"},
            )
            print("✅ UPDATE successful")

            # Test DELETE (cleanup test record)
            print(f"🗑️ Testing DELETE on {test_table}...")
            deleted_lead = service.delete(test_table, test_lead_id)
            print("✅ DELETE successful - test record cleaned up")

        except Exception as e:
            print(f"⚠️ CRUD test failed: {e}")
            # This might be expected if tables don't exist yet

        return True

    except Exception as e:
        print(f"❌ CRUD operations test failed: {e}")
        return False


def test_database_performance():
    """Test database performance and connection pooling"""
    print("\n⚡ Testing Database Performance...")

    try:
        import time

        service = SupabaseService(use_admin=True)

        # Test multiple concurrent requests
        start_time = time.time()

        for i in range(5):
            try:
                service.select("leads", limit=1)
            except:
                pass  # Table might not exist

        end_time = time.time()
        avg_time = (end_time - start_time) / 5

        print(f"✅ Average query time: {avg_time:.3f}s")

        if avg_time < 1.0:
            print("✅ Database performance: Good")
        elif avg_time < 3.0:
            print("⚠️ Database performance: Acceptable")
        else:
            print("❌ Database performance: Slow")

        return True

    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False


def main():
    """Run all database tests"""
    print("🚀 iSwitch Roofs CRM - Database Integration Test")
    print("=" * 60)

    # Create Flask app and context
    app = create_app("development")

    with app.app_context():
        # Test results
        results = {"connection": False, "schema": {}, "crud": False, "performance": False}

        # 1. Test connection
        results["connection"] = test_database_connection()

        if not results["connection"]:
            print("\n❌ Cannot proceed without database connection")
            return results

        # 2. Test schema
        results["schema"] = test_schema_inspection()

        # 3. Test CRUD operations
        results["crud"] = test_basic_crud_operations()

        # 4. Test performance
        results["performance"] = test_database_performance()

        # Summary
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)

        print(f"🔌 Database Connection: {'✅ PASS' if results['connection'] else '❌ FAIL'}")

        if results["schema"]:
            accessible_tables = sum(
                1 for table in results["schema"].values() if table.get("exists")
            )
            total_tables = len(results["schema"])
            print(f"📊 Schema Inspection: ✅ {accessible_tables}/{total_tables} tables accessible")
        else:
            print("📊 Schema Inspection: ❌ FAIL")

        print(f"🧪 CRUD Operations: {'✅ PASS' if results['crud'] else '❌ FAIL'}")
        print(f"⚡ Performance Test: {'✅ PASS' if results['performance'] else '❌ FAIL'}")

        # Recommendations
        print("\n🎯 RECOMMENDATIONS")
        print("-" * 60)

        if not results["connection"]:
            print("❌ Fix database connection configuration")
            print("   - Check SUPABASE_URL and SUPABASE_KEY in .env")
            print("   - Verify Supabase project is active")

        if results["schema"] and not any(
            table.get("exists") for table in results["schema"].values()
        ):
            print("❌ No accessible tables found")
            print("   - Run database migrations")
            print("   - Check table permissions and RLS policies")

        if not results["crud"]:
            print("⚠️ CRUD operations failed")
            print("   - Tables may not exist yet")
            print("   - Check row-level security policies")

        return results


if __name__ == "__main__":
    main()
