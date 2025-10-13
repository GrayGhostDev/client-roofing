"""
Leads Data Integrity Validation Script for Phase D
Focuses on validating leads table (live data) with 114 records
Version: 1.0.0
Date: 2025-10-10
"""

import os
import sys
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import get_db
from sqlalchemy import text


class LeadsIntegrityValidator:
    """Validate data integrity for leads table"""

    def __init__(self):
        self.db = next(get_db())
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }

    def log_pass(self, message: str):
        """Log successful validation"""
        self.results['passed'].append(message)
        print(f"  ✅ {message}")

    def log_fail(self, message: str):
        """Log failed validation"""
        self.results['failed'].append(message)
        print(f"  ❌ {message}")

    def log_warning(self, message: str):
        """Log warning"""
        self.results['warnings'].append(message)
        print(f"  ⚠️  {message}")

    def validate_enums(self):
        """Validate ENUM values"""
        print("\n🔍 Validating ENUM Values...")

        # Valid status enum
        result = self.db.execute(text("""
            SELECT COUNT(*) FROM leads
            WHERE status NOT IN ('new', 'contacted', 'qualified', 'appointment_scheduled',
                                'inspection_completed', 'quote_sent', 'negotiation', 'won', 'lost', 'nurture')
            AND is_deleted = false
        """))
        invalid_count = result.scalar()
        if invalid_count == 0:
            self.log_pass("All lead statuses are valid")
        else:
            self.log_fail(f"{invalid_count} leads have invalid status values")

        # Valid temperature enum
        result = self.db.execute(text("""
            SELECT COUNT(*) FROM leads
            WHERE temperature NOT IN ('hot', 'warm', 'cool', 'cold')
            AND is_deleted = false
        """))
        invalid_count = result.scalar()
        if invalid_count == 0:
            self.log_pass("All lead temperatures are valid")
        else:
            self.log_fail(f"{invalid_count} leads have invalid temperature values")

        # Valid source enum
        result = self.db.execute(text("""
            SELECT COUNT(*) FROM leads
            WHERE source NOT IN ('website_form', 'google_lsa', 'google_ads', 'facebook_ads',
                                'referral', 'door_to_door', 'storm_response', 'organic_search',
                                'phone_inquiry', 'email_inquiry', 'partner_referral', 'repeat_customer')
            AND is_deleted = false
        """))
        invalid_count = result.scalar()
        if invalid_count == 0:
            self.log_pass("All lead sources are valid")
        else:
            self.log_fail(f"{invalid_count} leads have invalid source values")

    def validate_required_fields(self):
        """Validate required (NOT NULL) fields"""
        print("\n🔍 Validating Required Fields...")

        required_fields = ['first_name', 'last_name', 'phone', 'email', 'status', 'temperature', 'source', 'created_at']

        for field in required_fields:
            result = self.db.execute(text(f"""
                SELECT COUNT(*) FROM leads
                WHERE {field} IS NULL AND is_deleted = false
            """))
            null_count = result.scalar()

            if null_count == 0:
                self.log_pass(f"Field '{field}' has no NULL values")
            else:
                self.log_fail(f"Field '{field}' has {null_count} NULL values")

    def validate_data_ranges(self):
        """Validate data ranges"""
        print("\n🔍 Validating Data Ranges...")

        # Lead scores should be 0-100
        result = self.db.execute(text("""
            SELECT COUNT(*) FROM leads
            WHERE lead_score < 0 OR lead_score > 100
            AND is_deleted = false
        """))
        invalid_count = result.scalar()
        if invalid_count == 0:
            self.log_pass("All lead scores are within valid range (0-100)")
        else:
            self.log_fail(f"{invalid_count} leads have invalid lead_score values")

        # Property values should be positive
        result = self.db.execute(text("""
            SELECT COUNT(*) FROM leads
            WHERE property_value IS NOT NULL AND property_value < 0
            AND is_deleted = false
        """))
        invalid_count = result.scalar()
        if invalid_count == 0:
            self.log_pass("All property values are positive or NULL")
        else:
            self.log_fail(f"{invalid_count} leads have negative property_value")

        # Created dates should not be in future
        result = self.db.execute(text("""
            SELECT COUNT(*) FROM leads
            WHERE created_at > NOW()
            AND is_deleted = false
        """))
        invalid_count = result.scalar()
        if invalid_count == 0:
            self.log_pass("No future created_at dates")
        else:
            self.log_fail(f"{invalid_count} leads have future created_at dates")

    def validate_formats(self):
        """Validate email and phone formats"""
        print("\n🔍 Validating Email and Phone Formats...")

        # Email format
        result = self.db.execute(text("""
            SELECT COUNT(*) FROM leads
            WHERE email NOT LIKE '%@%.%'
            AND is_deleted = false
        """))
        invalid_count = result.scalar()
        if invalid_count == 0:
            self.log_pass("All emails have basic valid format")
        else:
            self.log_warning(f"{invalid_count} leads have potentially invalid email format")

        # Phone format
        result = self.db.execute(text("""
            SELECT COUNT(*) FROM leads
            WHERE phone !~ '[0-9]'
            AND is_deleted = false
        """))
        invalid_count = result.scalar()
        if invalid_count == 0:
            self.log_pass("All phone numbers contain digits")
        else:
            self.log_warning(f"{invalid_count} leads have phone numbers without digits")

    def generate_statistics(self):
        """Generate database statistics"""
        print("\n📊 Database Statistics...")

        # Total leads
        result = self.db.execute(text("SELECT COUNT(*) FROM leads WHERE is_deleted = false"))
        total = result.scalar()
        print(f"\n  Total Leads: {total}")

        # Temperature distribution
        result = self.db.execute(text("""
            SELECT temperature, COUNT(*) as count
            FROM leads
            WHERE is_deleted = false
            GROUP BY temperature
            ORDER BY count DESC
        """))
        print(f"\n  Temperature Distribution:")
        for row in result:
            print(f"    {row[0]}: {row[1]} ({row[1]/total*100:.1f}%)")

        # Status distribution
        result = self.db.execute(text("""
            SELECT status, COUNT(*) as count
            FROM leads
            WHERE is_deleted = false
            GROUP BY status
            ORDER BY count DESC
        """))
        print(f"\n  Status Distribution:")
        for row in result:
            print(f"    {row[0]}: {row[1]} ({row[1]/total*100:.1f}%)")

        # Source distribution
        result = self.db.execute(text("""
            SELECT source, COUNT(*) as count
            FROM leads
            WHERE is_deleted = false
            GROUP BY source
            ORDER BY count DESC
        """))
        print(f"\n  Source Distribution:")
        for row in result:
            print(f"    {row[0]}: {row[1]} ({row[1]/total*100:.1f}%)")

        # Average metrics
        result = self.db.execute(text("""
            SELECT AVG(lead_score) as avg_score, AVG(property_value) as avg_value
            FROM leads
            WHERE is_deleted = false
        """))
        row = result.fetchone()
        print(f"\n  Average lead_score: {row[0]:.1f}/100")
        print(f"  Average property_value: ${row[1]:,.0f}")

    def run_all_validations(self):
        """Run all validation checks"""
        print("="*80)
        print("PHASE D: LEADS DATA INTEGRITY VALIDATION")
        print("="*80)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            self.validate_enums()
            self.validate_required_fields()
            self.validate_data_ranges()
            self.validate_formats()
            self.generate_statistics()

            # Summary
            print("\n" + "="*80)
            print("VALIDATION SUMMARY")
            print("="*80)
            print(f"  ✅ Passed: {len(self.results['passed'])}")
            print(f"  ❌ Failed: {len(self.results['failed'])}")
            print(f"  ⚠️  Warnings: {len(self.results['warnings'])}")

            if self.results['failed']:
                print("\n❌ FAILED CHECKS:")
                for msg in self.results['failed']:
                    print(f"  • {msg}")

            if self.results['warnings']:
                print("\n⚠️  WARNINGS:")
                for msg in self.results['warnings']:
                    print(f"  • {msg}")

            if not self.results['failed']:
                print("\n✅ ALL VALIDATIONS PASSED!")
                return True
            else:
                print("\n❌ VALIDATION FAILED - See errors above")
                return False

        except Exception as e:
            print(f"\n❌ Validation failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def close(self):
        """Close database connection"""
        self.db.close()


if __name__ == "__main__":
    validator = LeadsIntegrityValidator()

    try:
        success = validator.run_all_validations()
        print("\n" + "="*80)
        print("✅ VALIDATION COMPLETE" if success else "❌ VALIDATION FAILED")
        print("="*80)
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Validation script failed: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
    finally:
        validator.close()
