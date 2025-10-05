"""
iSwitch Roofs CRM - Audit Fields Unit Tests
Version: 1.0.0

Tests for audit field functionality (created_by, updated_by).
"""

from datetime import datetime

import pytest
from app.models.base import AuditMixin, BaseDBModel
from app.models.lead import Lead


class TestAuditFields:
    """Test suite for audit field functionality."""

    @pytest.mark.unit
    def test_audit_mixin_has_required_fields(self):
        """Test that AuditMixin has all required audit fields."""
        # Check that the mixin has the expected fields
        mixin = AuditMixin()

        # These fields should exist (will be None before saving)
        assert hasattr(mixin, "created_by")
        assert hasattr(mixin, "updated_by")
        assert hasattr(mixin, "created_by_email")
        assert hasattr(mixin, "updated_by_email")

    @pytest.mark.unit
    def test_base_model_includes_audit_fields(self):
        """Test that BaseDBModel includes audit fields."""
        model = BaseDBModel()

        # Check inherited fields from BaseDBModel
        assert hasattr(model, "id")
        assert hasattr(model, "created_at")
        assert hasattr(model, "updated_at")

        # Check audit fields
        assert hasattr(model, "created_by")
        assert hasattr(model, "updated_by")

    @pytest.mark.unit
    def test_audit_fields_are_optional(self):
        """Test that audit fields are optional and can be None."""
        model = BaseDBModel()

        # Audit fields should be None by default
        assert model.created_by is None
        assert model.updated_by is None
        assert model.created_by_email is None
        assert model.updated_by_email is None

    @pytest.mark.unit
    def test_audit_fields_can_be_set(self):
        """Test that audit fields can be set with user IDs."""
        model = BaseDBModel()
        user_id = "550e8400-e29b-41d4-a716-446655440000"

        # Set audit fields
        model.created_by = user_id
        model.updated_by = user_id
        model.created_by_email = "admin@iswitchroofs.com"
        model.updated_by_email = "admin@iswitchroofs.com"

        # Verify fields are set
        assert model.created_by == user_id
        assert model.updated_by == user_id
        assert model.created_by_email == "admin@iswitchroofs.com"
        assert model.updated_by_email == "admin@iswitchroofs.com"

    @pytest.mark.unit
    def test_lead_model_has_audit_fields(self):
        """Test that Lead model inherits audit fields."""
        lead_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "2485551234",
            "source": "website_form",
        }

        lead = Lead(**lead_data)

        # Check that lead has audit fields
        assert hasattr(lead, "created_by")
        assert hasattr(lead, "updated_by")
        assert lead.created_by is None  # Should be None initially
        assert lead.updated_by is None

    @pytest.mark.unit
    def test_model_dict_includes_audit_fields(self):
        """Test that model_dump includes audit fields when present."""
        model = BaseDBModel()
        user_id = "550e8400-e29b-41d4-a716-446655440000"

        model.created_by = user_id
        model.updated_by = user_id
        model.created_by_email = "admin@iswitchroofs.com"
        model.updated_by_email = "admin@iswitchroofs.com"

        # Get model as dictionary
        model_dict = model.model_dump(exclude_none=False)

        # Check audit fields are in dict
        assert "created_by" in model_dict
        assert "updated_by" in model_dict
        assert "created_by_email" in model_dict
        assert "updated_by_email" in model_dict
        assert model_dict["created_by"] == user_id
        assert model_dict["updated_by"] == user_id

    @pytest.mark.unit
    def test_model_dict_excludes_none_audit_fields(self):
        """Test that model_dump with exclude_none omits None audit fields."""
        model = BaseDBModel()

        # Get model as dictionary excluding None values
        model_dict = model.model_dump(exclude_none=True)

        # Audit fields should not be in dict when None
        assert "created_by" not in model_dict
        assert "updated_by" not in model_dict
        assert "created_by_email" not in model_dict
        assert "updated_by_email" not in model_dict

    @pytest.mark.unit
    def test_audit_fields_validation(self):
        """Test that audit field values are validated."""
        model = BaseDBModel()

        # Valid UUID string should work
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        model.created_by = valid_uuid
        assert model.created_by == valid_uuid

        # Invalid UUID should still be stored (as string)
        # This allows flexibility for different ID formats
        model.created_by = "user_123"
        assert model.created_by == "user_123"

        # Email validation for email fields
        model.created_by_email = "valid@email.com"
        assert model.created_by_email == "valid@email.com"

    @pytest.mark.unit
    def test_set_audit_fields_method(self):
        """Test the set_audit_fields helper method."""
        model = BaseDBModel()
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        user_email = "admin@iswitchroofs.com"

        # Test setting created fields
        model.set_audit_fields(user_id=user_id, user_email=user_email, is_update=False)
        assert model.created_by == user_id
        assert model.created_by_email == user_email
        assert model.updated_by == user_id
        assert model.updated_by_email == user_email

        # Test updating only updated fields
        new_user_id = "660e8400-e29b-41d4-a716-446655440001"
        new_email = "manager@iswitchroofs.com"
        model.set_audit_fields(user_id=new_user_id, user_email=new_email, is_update=True)

        # Created fields should remain unchanged
        assert model.created_by == user_id
        assert model.created_by_email == user_email
        # Updated fields should change
        assert model.updated_by == new_user_id
        assert model.updated_by_email == new_email

    @pytest.mark.unit
    def test_audit_fields_json_serialization(self):
        """Test that audit fields serialize properly to JSON."""
        model = BaseDBModel()
        user_id = "550e8400-e29b-41d4-a716-446655440000"

        model.created_by = user_id
        model.updated_by = user_id
        model.created_at = datetime.utcnow()
        model.updated_at = datetime.utcnow()

        # Convert to JSON-serializable dict
        json_dict = model.model_dump_json()

        # Should be a valid JSON string
        assert isinstance(json_dict, str)

        # Parse and check
        import json

        parsed = json.loads(json_dict)
        assert parsed.get("created_by") == user_id
        assert parsed.get("updated_by") == user_id
