"""
Tests for Authentication Service

Comprehensive test coverage for the authentication service including
registration, login, JWT tokens, password reset, and permissions.

Author: iSwitch Roofs Development Team
Date: 2025-01-04
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import bcrypt
import jwt
import pytest
from app.services.auth_service import (
    AuthService,
    TokenType,
    UserRole,
    auth_service,
    has_permission,
    login,
    register_user,
    validate_token,
)


@pytest.fixture
def auth_srv():
    """Create auth service instance for testing"""
    return AuthService()


@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    with patch("app.services.auth_service.get_supabase_client") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_notification():
    """Mock notification service"""
    with patch("app.services.auth_service.notification_service") as mock:
        mock.send_notification.return_value = (True, None)
        yield mock


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    with patch("app.services.auth_service.cache_set") as mock_set:
        with patch("app.services.auth_service.cache_get") as mock_get:
            with patch("app.services.auth_service.cache_delete") as mock_del:
                mock_get.return_value = None
                mock_set.return_value = True
                mock_del.return_value = True
                yield {"set": mock_set, "get": mock_get, "delete": mock_del}


@pytest.fixture
def sample_user():
    """Sample user data"""
    return {
        "id": "user-123",
        "email": "john@example.com",
        "name": "John Doe",
        "role": UserRole.SALES_REP,
        "password_hash": bcrypt.hashpw(b"TestPass123!", bcrypt.gensalt()).decode("utf-8"),
        "is_active": True,
        "is_verified": True,
        "failed_login_attempts": 0,
        "locked_until": None,
        "settings": {
            "notifications": {"email": True, "sms": True, "push": True},
            "two_factor_enabled": False,
        },
    }


class TestUserRegistration:
    """Test user registration functionality"""

    def test_register_user_success(self, auth_srv, mock_supabase, mock_notification):
        """Test successful user registration"""
        # Setup
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
            []
        )
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "new-user-id", "email": "newuser@example.com", "name": "New User"}
        ]

        # Act
        success, user_data, error = auth_srv.register_user(
            email="newuser@example.com", password="SecurePass123!", name="New User"
        )

        # Assert
        assert success is True
        assert user_data is not None
        assert error is None
        assert user_data["email"] == "newuser@example.com"
        mock_notification.send_notification.assert_called_once()

    def test_register_user_invalid_email(self, auth_srv, mock_supabase):
        """Test registration with invalid email"""
        success, user_data, error = auth_srv.register_user(
            email="invalid-email", password="SecurePass123!", name="Test User"
        )

        assert success is False
        assert user_data is None
        assert "email" in error.lower()

    def test_register_user_weak_password(self, auth_srv, mock_supabase):
        """Test registration with weak password"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
            []
        )

        success, user_data, error = auth_srv.register_user(
            email="test@example.com", password="weak", name="Test User"
        )

        assert success is False
        assert user_data is None
        assert "password" in error.lower()

    def test_register_user_already_exists(self, auth_srv, mock_supabase):
        """Test registration with existing email"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": "existing-user"}
        ]

        success, user_data, error = auth_srv.register_user(
            email="existing@example.com", password="SecurePass123!", name="Test User"
        )

        assert success is False
        assert user_data is None
        assert "already exists" in error


class TestUserLogin:
    """Test user login functionality"""

    def test_login_success(self, auth_srv, mock_supabase, mock_redis, sample_user):
        """Test successful login"""
        # Setup
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            sample_user
        ]
        mock_redis["get"].return_value = None  # No rate limiting

        # Act
        success, token_data, error = auth_srv.login(
            email="john@example.com", password="TestPass123!"
        )

        # Assert
        assert success is True
        assert token_data is not None
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert error is None

    def test_login_invalid_credentials(self, auth_srv, mock_supabase, mock_redis):
        """Test login with invalid credentials"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
            []
        )
        mock_redis["get"].return_value = None

        success, token_data, error = auth_srv.login(email="wrong@example.com", password="WrongPass")

        assert success is False
        assert token_data is None
        assert "Invalid email or password" in error

    def test_login_unverified_email(self, auth_srv, mock_supabase, mock_redis, sample_user):
        """Test login with unverified email"""
        sample_user["is_verified"] = False
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            sample_user
        ]
        mock_redis["get"].return_value = None

        success, token_data, error = auth_srv.login(
            email="john@example.com", password="TestPass123!"
        )

        assert success is False
        assert token_data is None
        assert "not verified" in error

    def test_login_rate_limited(self, auth_srv, mock_supabase, mock_redis):
        """Test login rate limiting"""
        mock_redis["get"].return_value = "5"  # Max attempts reached

        success, token_data, error = auth_srv.login(
            email="john@example.com", password="TestPass123!"
        )

        assert success is False
        assert token_data is None
        assert "too many" in error.lower()

    def test_login_account_locked(self, auth_srv, mock_supabase, mock_redis, sample_user):
        """Test login with locked account"""
        sample_user["locked_until"] = (datetime.utcnow() + timedelta(minutes=15)).isoformat()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            sample_user
        ]
        mock_redis["get"].return_value = None

        success, token_data, error = auth_srv.login(
            email="john@example.com", password="TestPass123!"
        )

        assert success is False
        assert token_data is None
        assert "locked" in error.lower()


class TestTokenManagement:
    """Test JWT token management"""

    def test_generate_access_token(self, auth_srv):
        """Test access token generation"""
        token = auth_srv._generate_token(
            user_id="test-user",
            email="test@example.com",
            role=UserRole.SALES_REP,
            token_type=TokenType.ACCESS,
        )

        assert token is not None
        assert isinstance(token, str)

        # Decode and verify
        payload = jwt.decode(token, auth_srv.jwt_secret, algorithms=[auth_srv.jwt_algorithm])

        assert payload["user_id"] == "test-user"
        assert payload["email"] == "test@example.com"
        assert payload["role"] == UserRole.SALES_REP
        assert payload["token_type"] == TokenType.ACCESS

    def test_validate_token_success(self, auth_srv):
        """Test successful token validation"""
        token = auth_srv._generate_token(
            user_id="test-user",
            email="test@example.com",
            role=UserRole.ADMIN,
            token_type=TokenType.ACCESS,
        )

        payload = auth_srv.validate_token(token)

        assert payload is not None
        assert payload["user_id"] == "test-user"
        assert payload["role"] == UserRole.ADMIN

    def test_validate_expired_token(self, auth_srv):
        """Test validation of expired token"""
        # Create expired token
        auth_srv.access_token_expires = -1  # Expire immediately
        token = auth_srv._generate_token(
            user_id="test-user",
            email="test@example.com",
            role=UserRole.SALES_REP,
            token_type=TokenType.ACCESS,
        )

        payload = auth_srv.validate_token(token)

        assert payload is None

    def test_validate_invalid_token(self, auth_srv):
        """Test validation of invalid token"""
        payload = auth_srv.validate_token("invalid.token.here")
        assert payload is None

    def test_refresh_token_success(self, auth_srv, mock_supabase, mock_redis, sample_user):
        """Test successful token refresh"""
        # Generate refresh token
        refresh_token = auth_srv._generate_token(
            user_id=sample_user["id"],
            email=sample_user["email"],
            role=sample_user["role"],
            token_type=TokenType.REFRESH,
        )

        # Mock Redis to return the same token
        mock_redis["get"].return_value = refresh_token
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            sample_user
        ]

        success, token_data, error = auth_srv.refresh_token(refresh_token)

        assert success is True
        assert token_data is not None
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert error is None


class TestPasswordManagement:
    """Test password-related functionality"""

    def test_password_validation(self, auth_srv):
        """Test password validation rules"""
        # Too short
        valid, error = auth_srv._validate_password("Short1!")
        assert valid is False
        assert "at least" in error

        # No uppercase
        valid, error = auth_srv._validate_password("lowercase123!")
        assert valid is False
        assert "uppercase" in error

        # No lowercase
        valid, error = auth_srv._validate_password("UPPERCASE123!")
        assert valid is False
        assert "lowercase" in error

        # No number
        valid, error = auth_srv._validate_password("NoNumbers!")
        assert valid is False
        assert "number" in error

        # No special character
        valid, error = auth_srv._validate_password("NoSpecial123")
        assert valid is False
        assert "special" in error

        # Valid password
        valid, error = auth_srv._validate_password("ValidPass123!")
        assert valid is True
        assert error is None

    def test_password_hashing(self, auth_srv):
        """Test password hashing and verification"""
        password = "TestPassword123!"
        hashed = auth_srv._hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert auth_srv._verify_password(password, hashed) is True
        assert auth_srv._verify_password("WrongPassword", hashed) is False

    def test_request_password_reset(self, auth_srv, mock_supabase, mock_redis, mock_notification):
        """Test password reset request"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": "user-123", "name": "John Doe"}
        ]

        success, error = auth_srv.request_password_reset("john@example.com")

        assert success is True
        assert error is None
        mock_redis["set"].assert_called()
        mock_notification.send_notification.assert_called_once()

    def test_reset_password_success(self, auth_srv, mock_supabase, mock_redis, mock_notification):
        """Test successful password reset"""
        reset_token = "valid-reset-token"
        mock_redis["get"].return_value = {"user_id": "user-123", "email": "john@example.com"}

        success, error = auth_srv.reset_password(reset_token, "NewPassword123!")

        assert success is True
        assert error is None
        mock_supabase.table.return_value.update.assert_called()
        mock_redis["delete"].assert_called()

    def test_change_password_success(self, auth_srv, mock_supabase, sample_user):
        """Test successful password change"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            sample_user
        ]

        success, error = auth_srv.change_password(
            user_id=sample_user["id"],
            current_password="TestPass123!",
            new_password="NewSecurePass456!",
        )

        assert success is True
        assert error is None
        mock_supabase.table.return_value.update.assert_called()


class TestPermissions:
    """Test role-based permissions"""

    def test_admin_permissions(self, auth_srv):
        """Test admin has all permissions"""
        permissions = auth_srv.get_user_permissions(UserRole.ADMIN)

        assert "users:*" in permissions
        assert "leads:*" in permissions
        assert "projects:*" in permissions
        assert len(permissions) > 5

    def test_sales_rep_permissions(self, auth_srv):
        """Test sales rep has limited permissions"""
        permissions = auth_srv.get_user_permissions(UserRole.SALES_REP)

        assert "leads:create" in permissions
        assert "leads:update" in permissions
        assert "users:*" not in permissions
        assert "settings:*" not in permissions

    def test_has_permission_check(self, auth_srv):
        """Test permission checking"""
        # Admin can do anything
        assert auth_srv.has_permission(UserRole.ADMIN, "leads:delete") is True
        assert auth_srv.has_permission(UserRole.ADMIN, "users:create") is True

        # Sales rep has limited permissions
        assert auth_srv.has_permission(UserRole.SALES_REP, "leads:create") is True
        assert auth_srv.has_permission(UserRole.SALES_REP, "users:delete") is False

        # Field tech is very limited
        assert auth_srv.has_permission(UserRole.FIELD_TECH, "projects:read") is True
        assert auth_srv.has_permission(UserRole.FIELD_TECH, "leads:create") is False

    def test_wildcard_permissions(self, auth_srv):
        """Test wildcard permission matching"""
        # Admin has leads:* which should match any leads permission
        assert auth_srv.has_permission(UserRole.ADMIN, "leads:create") is True
        assert auth_srv.has_permission(UserRole.ADMIN, "leads:delete") is True
        assert auth_srv.has_permission(UserRole.ADMIN, "leads:anything") is True


class TestEmailVerification:
    """Test email verification functionality"""

    def test_verify_email_success(self, auth_srv, mock_supabase, mock_notification):
        """Test successful email verification"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": "user-123", "email": "john@example.com"}
        ]

        success, error = auth_srv.verify_email("valid-verification-token")

        assert success is True
        assert error is None
        mock_supabase.table.return_value.update.assert_called()
        mock_notification.send_notification.assert_called()

    def test_verify_email_invalid_token(self, auth_srv, mock_supabase):
        """Test email verification with invalid token"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
            []
        )

        success, error = auth_srv.verify_email("invalid-token")

        assert success is False
        assert error is not None
        assert "Invalid" in error


class TestLogout:
    """Test logout functionality"""

    def test_logout_success(self, auth_srv, mock_redis):
        """Test successful logout"""
        success = auth_srv.logout("user-123", "session-456")

        assert success is True
        mock_redis["delete"].assert_called()


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_register_user_function(self, mock_supabase, mock_notification):
        """Test the convenience register_user function"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
            []
        )
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "new-user", "email": "test@example.com"}
        ]

        success, user_data, error = register_user(
            email="test@example.com", password="SecurePass123!", name="Test User"
        )

        assert success is True
        assert user_data is not None

    def test_login_function(self, mock_supabase, mock_redis):
        """Test the convenience login function"""
        sample_user = {
            "id": "user-123",
            "email": "test@example.com",
            "password_hash": bcrypt.hashpw(b"TestPass123!", bcrypt.gensalt()).decode("utf-8"),
            "is_active": True,
            "is_verified": True,
            "settings": {},
        }
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            sample_user
        ]
        mock_redis["get"].return_value = None

        success, token_data, error = login("test@example.com", "TestPass123!")

        assert success is True
        assert token_data is not None

    def test_validate_token_function(self):
        """Test the convenience validate_token function"""
        # Generate a test token
        test_token = jwt.encode(
            {
                "user_id": "test-user",
                "email": "test@example.com",
                "role": "admin",
                "token_type": "access",
                "exp": datetime.utcnow() + timedelta(hours=1),
            },
            auth_service.jwt_secret,
            algorithm=auth_service.jwt_algorithm,
        )

        payload = validate_token(test_token)

        assert payload is not None
        assert payload["user_id"] == "test-user"

    def test_has_permission_function(self):
        """Test the convenience has_permission function"""
        assert has_permission(UserRole.ADMIN, "leads:delete") is True
        assert has_permission(UserRole.SALES_REP, "users:delete") is False


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
