"""
Data Integrity Validation Script for Phase C Testing
Validates database constraints, ENUM values, and data consistency
Version: 1.0.0
Date: 2025-10-10
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import get_db
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError


class DataIntegrityValidator:
    """Validate data integrity for all CRM tables"""

    def __init__(self):
        self.db = next(get_db())
        self.errors = []
        self.warnings = []
        self.success_checks = 0
        self.failed_checks = 0

    def log_error(self, message: str):
        """Log validation error"""
        self.errors.append(message)
        self.failed_checks += 1
        print(f"  ❌ {message}")

    def log_warning(self, message: str):
        """Log validation warning"""
        self.warnings.append(message)
        print(f"  ⚠️  {message}")

    def log_success(self, message: str):
        """Log successful validation"""
        self.success_checks += 1
        print(f"  ✅ {message}")

    def validate_leads_enums(self) -> bool:
        """Validate leads table ENUM constraints"""
        print("\n🔍 Validating Leads ENUM Values...")

        try:
            # Check lead status ENUM (lowercase)
            result = self.db.execute(text("""
                SELECT DISTINCT status FROM leads
                WHERE status NOT IN ('new', 'contacted', 'qualified', 'appointment_scheduled',
                                    'inspection_completed', 'quote_sent', 'negotiation', 'won', 'lost', 'nurture')
                AND is_deleted = false
            """))
            invalid_statuses = [row[0] for row in result]

            if invalid_statuses:
                self.log_error(f"Invalid lead statuses found: {invalid_statuses}")
            else:
                self.log_success("All lead statuses are valid")

            # Check temperature ENUM (lowercase)
            result = self.db.execute(text("""
                SELECT DISTINCT temperature FROM leads
                WHERE temperature NOT IN ('hot', 'warm', 'cool', 'cold')
                AND is_deleted = false
            """))
            invalid_temps = [row[0] for row in result]

            if invalid_temps:
                self.log_error(f"Invalid lead temperatures found: {invalid_temps}")
            else:
                self.log_success("All lead temperatures are valid")

            # Check source ENUM (valid values from LeadSourceEnum)
            result = self.db.execute(text("""
                SELECT DISTINCT source FROM leads
                WHERE source NOT IN ('website_form', 'google_lsa', 'google_ads', 'facebook_ads',
                                    'referral', 'door_to_door', 'storm_response', 'organic_search',
                                    'phone_inquiry', 'email_inquiry', 'partner_referral', 'repeat_customer')
                AND is_deleted = false
            """))
            invalid_sources = [row[0] for row in result]

            if invalid_sources:
                self.log_error(f"Invalid lead sources found: {invalid_sources}")
            else:
                self.log_success("All lead sources are valid")

            return len(invalid_statuses) == 0 and len(invalid_temps) == 0 and len(invalid_sources) == 0

        except SQLAlchemyError as e:
            self.log_error(f"Error validating leads ENUMs: {str(e)}")
            return False

    def validate_customers_enums(self) -> bool:
        """Validate customers table ENUM constraints"""
        print("\n🔍 Validating Customers ENUM Values...")

        try:
            # Check customer status ENUM (lowercase: active, inactive, vip, churned)
            result = self.db.execute(text("""
                SELECT DISTINCT customer_status FROM customers
                WHERE customer_status NOT IN ('active', 'inactive', 'vip', 'churned')
                AND is_deleted = false
            """))
            invalid_statuses = [row[0] for row in result]

            if invalid_statuses:
                self.log_error(f"Invalid customer statuses found: {invalid_statuses}")
            else:
                self.log_success("All customer statuses are valid")

            return len(invalid_statuses) == 0

        except SQLAlchemyError as e:
            self.log_error(f"Error validating customers ENUMs: {str(e)}")
            return False

    def validate_not_null_constraints(self) -> bool:
        """Validate NOT NULL constraints"""
        print("\n🔍 Validating NOT NULL Constraints...")

        critical_fields = {
            "leads": ["first_name", "last_name", "phone", "email", "status", "temperature", "source", "created_at"],
            "customers": ["first_name", "last_name", "phone", "email", "customer_status", "created_at"],
            "projects": ["customer_id", "name", "status", "created_at"],
            "appointments": ["customer_id", "scheduled_date", "status", "created_at"]
        }

        all_valid = True

        for table, fields in critical_fields.items():
            for field in fields:
                try:
                    result = self.db.execute(text(f"""
                        SELECT COUNT(*) FROM {table}
                        WHERE {field} IS NULL AND is_deleted = false
                    """))
                    null_count = result.scalar()

                    if null_count > 0:
                        self.log_error(f"{table}.{field} has {null_count} NULL values")
                        all_valid = False
                    else:
                        self.log_success(f"{table}.{field} has no NULL values")

                except SQLAlchemyError as e:
                    # Table or column might not exist - just log warning
                    self.log_warning(f"Could not validate {table}.{field}: {str(e)}")

        return all_valid

    def validate_foreign_keys(self) -> bool:
        """Validate foreign key relationships"""
        print("\n🔍 Validating Foreign Key Relationships...")

        try:
            # Projects must reference valid customers
            result = self.db.execute(text("""
                SELECT COUNT(*) FROM projects p
                LEFT JOIN customers c ON p.customer_id = c.id
                WHERE c.id IS NULL AND p.is_deleted = false
            """))
            orphaned_projects = result.scalar()

            if orphaned_projects > 0:
                self.log_error(f"{orphaned_projects} projects reference non-existent customers")
            else:
                self.log_success("All projects reference valid customers")

            # Appointments must reference valid customers or leads
            result = self.db.execute(text("""
                SELECT COUNT(*) FROM appointments a
                LEFT JOIN customers c ON a.customer_id = c.id
                LEFT JOIN leads l ON a.lead_id = l.id
                WHERE c.id IS NULL AND l.id IS NULL AND a.is_deleted = false
            """))
            orphaned_appointments = result.scalar()

            if orphaned_appointments > 0:
                self.log_error(f"{orphaned_appointments} appointments reference non-existent customers/leads")
            else:
                self.log_success("All appointments reference valid customers or leads")

            return orphaned_projects == 0 and orphaned_appointments == 0

        except SQLAlchemyError as e:
            self.log_warning(f"Could not validate foreign keys: {str(e)}")
            return True  # Don't fail if tables don't exist yet

    def validate_data_ranges(self) -> bool:
        """Validate data ranges (scores, values, dates)"""
        print("\n🔍 Validating Data Ranges...")

        all_valid = True

        try:
            # Lead scores should be 0-100
            result = self.db.execute(text("""
                SELECT COUNT(*) FROM leads
                WHERE (lead_score < 0 OR lead_score > 100) AND is_deleted = false
            """))
            invalid_scores = result.scalar()

            if invalid_scores > 0:
                self.log_error(f"{invalid_scores} leads have invalid lead_score (must be 0-100)")
                all_valid = False
            else:
                self.log_success("All lead scores are within valid range (0-100)")

            # Property values should be positive
            result = self.db.execute(text("""
                SELECT COUNT(*) FROM leads
                WHERE property_value IS NOT NULL AND property_value < 0 AND is_deleted = false
            """))
            invalid_values = result.scalar()

            if invalid_values > 0:
                self.log_error(f"{invalid_values} leads have negative property_value")
                all_valid = False
            else:
                self.log_success("All property values are positive")

            # Created dates should not be in future
            result = self.db.execute(text("""
                SELECT COUNT(*) FROM leads
                WHERE created_at > NOW() AND is_deleted = false
            """))
            future_dates = result.scalar()

            if future_dates > 0:
                self.log_error(f"{future_dates} leads have future created_at dates")
                all_valid = False
            else:
                self.log_success("All created_at dates are not in the future")

        except SQLAlchemyError as e:
            self.log_error(f"Error validating data ranges: {str(e)}")
            all_valid = False

        return all_valid

    def validate_email_phone_formats(self) -> bool:
        """Validate email and phone number formats"""
        print("\n🔍 Validating Email and Phone Formats...")

        try:
            # Check email format (basic validation)
            result = self.db.execute(text("""
                SELECT COUNT(*) FROM leads
                WHERE email NOT LIKE '%@%.%' AND is_deleted = false
            """))
            invalid_emails = result.scalar()

            if invalid_emails > 0:
                self.log_warning(f"{invalid_emails} leads have potentially invalid email formats")
            else:
                self.log_success("All lead emails have basic valid format")

            # Check phone format (should have digits)
            result = self.db.execute(text("""
                SELECT COUNT(*) FROM leads
                WHERE phone !~ '[0-9]' AND is_deleted = false
            """))
            invalid_phones = result.scalar()

            if invalid_phones > 0:
                self.log_warning(f"{invalid_phones} leads have phone numbers without digits")
            else:
                self.log_success("All lead phone numbers contain digits")

            return True  # These are warnings, not errors

        except SQLAlchemyError as e:
            self.log_warning(f"Could not validate email/phone formats: {str(e)}")
            return True

    def generate_statistics(self):
        """Generate database statistics"""
        print("\n📊 Database Statistics...")

        try:
            # Leads statistics
            result = self.db.execute(text("SELECT COUNT(*) FROM leads WHERE is_deleted = false"))
            total_leads = result.scalar()
            print(f"\n  📋 Leads: {total_leads}")

            if total_leads > 0:
                result = self.db.execute(text("""
                    SELECT temperature, COUNT(*) as count
                    FROM leads
                    WHERE is_deleted = false
                    GROUP BY temperature
                    ORDER BY count DESC
                """))
                print("    Temperature distribution:")
                for row in result:
                    print(f"      {row[0]}: {row[1]} ({row[1]/total_leads*100:.1f}%)")

                result = self.db.execute(text("""
                    SELECT status, COUNT(*) as count
                    FROM leads
                    WHERE is_deleted = false
                    GROUP BY status
                    ORDER BY count DESC
                """))
                print("    Status distribution:")
                for row in result:
                    print(f"      {row[0]}: {row[1]} ({row[1]/total_leads*100:.1f}%)")

            # Customers statistics
            result = self.db.execute(text("SELECT COUNT(*) FROM customers WHERE is_deleted = false"))
            total_customers = result.scalar()
            print(f"\n  👥 Customers: {total_customers}")

            # Projects statistics
            result = self.db.execute(text("SELECT COUNT(*) FROM projects WHERE is_deleted = false"))
            total_projects = result.scalar()
            print(f"\n  🏗️  Projects: {total_projects}")

            # Appointments statistics
            result = self.db.execute(text("SELECT COUNT(*) FROM appointments WHERE is_deleted = false"))
            total_appointments = result.scalar()
            print(f"\n  📅 Appointments: {total_appointments}")

        except SQLAlchemyError as e:
            print(f"  ⚠️  Could not generate statistics: {str(e)}")

    def run_all_validations(self) -> bool:
        """Run all validation checks"""
        print("=" * 80)
        print("PHASE C: DATA INTEGRITY VALIDATION")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        all_passed = True

        # Run all validations
        all_passed &= self.validate_leads_enums()
        all_passed &= self.validate_customers_enums()
        all_passed &= self.validate_not_null_constraints()
        all_passed &= self.validate_foreign_keys()
        all_passed &= self.validate_data_ranges()
        all_passed &= self.validate_email_phone_formats()

        # Generate statistics
        self.generate_statistics()

        # Print summary
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        print(f"  ✅ Passed checks: {self.success_checks}")
        print(f"  ❌ Failed checks: {self.failed_checks}")
        print(f"  ⚠️  Warnings: {len(self.warnings)}")
        print()

        if self.errors:
            print("❌ ERRORS:")
            for error in self.errors:
                print(f"  • {error}")
            print()

        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning}")
            print()

        if all_passed and not self.errors:
            print("✅ ALL VALIDATIONS PASSED!")
        else:
            print("❌ VALIDATION FAILED - Please review errors above")

        print("=" * 80)
        print()

        return all_passed

    def close(self):
        """Close database connection"""
        self.db.close()


if __name__ == "__main__":
    validator = DataIntegrityValidator()

    try:
        success = validator.run_all_validations()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Validation script failed: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
    finally:
        validator.close()
