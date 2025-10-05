#!/usr/bin/env python3
"""
Test script to verify all SQLAlchemy models can be imported correctly
"""
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_model_imports():
    """Test importing all SQLAlchemy models"""
    try:
        print("Testing base model imports...")
        from app.models.base import Base, BaseModel
        print("✅ Base models imported successfully")

        print("\nTesting core models...")
        from app.models.lead_sqlalchemy import Lead, LeadStatus, LeadTemperature
        print("✅ Lead model imported successfully")

        from app.models.customer_sqlalchemy import Customer, CustomerStatus, CustomerSegment
        print("✅ Customer model imported successfully")

        print("\nTesting business process models...")
        from app.models.project_sqlalchemy import Project, ProjectStatus, ProjectType, ProjectPriority
        print("✅ Project model imported successfully")

        from app.models.appointment_sqlalchemy import Appointment, AppointmentType, AppointmentStatus
        print("✅ Appointment model imported successfully")

        from app.models.interaction_sqlalchemy import Interaction, InteractionType, InteractionDirection
        print("✅ Interaction model imported successfully")

        print("\nTesting support models...")
        from app.models.team_sqlalchemy import TeamMember, TeamRole, TeamMemberStatus
        print("✅ Team model imported successfully")

        from app.models.review_sqlalchemy import Review, ReviewPlatform, ReviewStatus
        print("✅ Review model imported successfully")

        from app.models.partnership_sqlalchemy import Partnership, PartnerType, PartnershipStatus
        print("✅ Partnership model imported successfully")

        print("\nTesting system models...")
        from app.models.notification_sqlalchemy import Notification, NotificationTemplate, NotificationStatus
        print("✅ Notification models imported successfully")

        from app.models.alert_sqlalchemy import Alert, AlertType, AlertPriority
        print("✅ Alert model imported successfully")

        print("\nTesting analytics models...")
        from app.models.analytics_sqlalchemy import (
            KPIDefinition, MetricValue, ConversionFunnel,
            RevenueAnalytics, CustomerAnalytics, TeamPerformance,
            MarketingAnalytics, BusinessAlert
        )
        print("✅ Analytics models imported successfully")

        print("\nTesting full package import...")
        from app.models import *
        print("✅ All models imported successfully via package")

        print("\n🎉 All model imports completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Error importing models: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_model_schemas():
    """Test importing Pydantic schemas"""
    try:
        print("\nTesting Pydantic schemas...")

        from app.models.project_sqlalchemy import ProjectCreateSchema, ProjectUpdateSchema
        print("✅ Project schemas imported successfully")

        from app.models.appointment_sqlalchemy import AppointmentCreateSchema, AppointmentUpdateSchema
        print("✅ Appointment schemas imported successfully")

        from app.models.interaction_sqlalchemy import InteractionCreateSchema, InteractionUpdateSchema
        print("✅ Interaction schemas imported successfully")

        print("✅ All Pydantic schemas imported successfully!")
        return True

    except Exception as e:
        print(f"❌ Error importing schemas: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing SQLAlchemy Model Imports")
    print("=" * 60)

    models_ok = test_model_imports()
    schemas_ok = test_model_schemas()

    print("\n" + "=" * 60)
    if models_ok and schemas_ok:
        print("🎉 ALL TESTS PASSED! Models are ready for use.")
        sys.exit(0)
    else:
        print("❌ TESTS FAILED! Please fix import errors.")
        sys.exit(1)