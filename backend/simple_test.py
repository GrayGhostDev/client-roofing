#!/usr/bin/env python3
"""
Simple test script to validate Lead model imports.
"""

import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))


def test_basic_imports():
    """Test basic model imports without Flask app context."""
    print("Testing basic imports...")

    try:
        # Test SQLAlchemy model import
        from app.models.lead_sqlalchemy import (
            Lead,
            LeadSourceEnum,
            LeadStatusEnum,
        )

        print("✅ SQLAlchemy Lead model imported successfully")

        # Test Pydantic schema imports
        from app.schemas.lead import LeadCreate

        print("✅ Pydantic schemas imported successfully")

        # Test model creation
        lead = Lead(
            first_name="John",
            last_name="Doe",
            phone="2485551234",
            email="john@example.com",
            source=LeadSourceEnum.WEBSITE_FORM,
            status=LeadStatusEnum.NEW,
        )

        print(f"✅ Lead model created: {lead.full_name}")
        print(f"   Status: {lead.status}")
        print(f"   Source: {lead.source}")

        # Test schema validation
        lead_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "phone": "3135551234",
            "email": "jane@example.com",
            "source": "website_form",
        }

        lead_schema = LeadCreate(**lead_data)
        print(f"✅ Schema validation passed: {lead_schema.first_name} {lead_schema.last_name}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Simple Lead Model Test")
    print("=" * 40)

    if test_basic_imports():
        print("\n🎉 SUCCESS! Lead model conversion is working!")
    else:
        print("\n❌ FAILED! There are issues with the conversion.")
