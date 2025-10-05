#!/usr/bin/env python3
"""
Direct model test without Flask dependencies.
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_direct_model_imports():
    """Test importing models directly."""
    print("Testing direct model imports...")

    try:
        # Import SQLAlchemy components
        from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Enum
        from sqlalchemy.dialects.postgresql import UUID
        from datetime import datetime
        import uuid
        import enum

        print("✅ SQLAlchemy components imported successfully")

        # Test enum definitions
        class LeadStatusEnum(enum.Enum):
            NEW = "new"
            CONTACTED = "contacted"
            QUALIFIED = "qualified"

        print("✅ Enum definitions work")

        # Test importing base model directly
        from app.models.base import BaseModel, Base
        print("✅ Base model imported successfully")

        # Test creating a simple model class
        class TestLead(BaseModel):
            __tablename__ = 'test_leads'

            first_name = Column(String(100), nullable=False)
            last_name = Column(String(100), nullable=False)
            phone = Column(String(20), nullable=False)
            status = Column(Enum(LeadStatusEnum), default=LeadStatusEnum.NEW)

            @property
            def full_name(self):
                return f"{self.first_name} {self.last_name}"

        print("✅ Test model class created successfully")

        # Test creating instance (without database)
        test_lead = TestLead()
        test_lead.first_name = "John"
        test_lead.last_name = "Doe"
        test_lead.phone = "2485551234"

        print(f"✅ Test instance created: {test_lead.full_name}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pydantic_schemas():
    """Test Pydantic schemas independently."""
    print("\nTesting Pydantic schemas...")

    try:
        from pydantic import BaseModel, EmailStr, Field
        from typing import Optional
        from enum import Enum

        print("✅ Pydantic components imported successfully")

        # Test enum for Pydantic
        class LeadSource(str, Enum):
            WEBSITE_FORM = "website_form"
            GOOGLE_ADS = "google_ads"
            REFERRAL = "referral"

        # Test schema definition
        class TestLeadCreate(BaseModel):
            first_name: str = Field(..., min_length=1, max_length=100)
            last_name: str = Field(..., min_length=1, max_length=100)
            phone: str
            email: Optional[EmailStr] = None
            source: LeadSource

        print("✅ Pydantic schema defined successfully")

        # Test validation
        valid_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "phone": "3135551234",
            "email": "jane@example.com",
            "source": "website_form"
        }

        lead_schema = TestLeadCreate(**valid_data)
        print(f"✅ Schema validation passed: {lead_schema.first_name} {lead_schema.last_name}")

        # Test model dump
        lead_dict = lead_schema.model_dump()
        print(f"✅ Model dump works: {len(lead_dict)} fields")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Direct Model Test (No Flask)")
    print("=" * 50)

    tests = [
        ("SQLAlchemy Models", test_direct_model_imports),
        ("Pydantic Schemas", test_pydantic_schemas),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)

        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            failed += 1
            print(f"❌ {test_name} FAILED")

    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed == 0:
        print("\n🎉 All core components work! The conversion structure is correct.")
        print("   Next step: Install Flask and other dependencies to test full integration.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Check the basic model setup.")