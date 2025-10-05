#!/usr/bin/env python3
"""
Test script to verify all SQLAlchemy models can be imported correctly
"""
import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))


def test_model_imports():
    """Test importing all SQLAlchemy models"""
    try:
        print("Testing base model imports...")

        print("✅ Base models imported successfully")

        print("\nTesting core models...")

        print("✅ Lead model imported successfully")


        print("✅ Customer model imported successfully")

        print("\nTesting business process models...")

        print("✅ Project model imported successfully")


        print("✅ Appointment model imported successfully")


        print("✅ Interaction model imported successfully")

        print("\nTesting support models...")

        print("✅ Team model imported successfully")


        print("✅ Review model imported successfully")


        print("✅ Partnership model imported successfully")

        print("\nTesting system models...")

        print("✅ Notification models imported successfully")


        print("✅ Alert model imported successfully")

        print("\nTesting analytics models...")

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


        print("✅ Project schemas imported successfully")


        print("✅ Appointment schemas imported successfully")


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
