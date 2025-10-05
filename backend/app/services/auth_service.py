"""
Authentication Service for iSwitch Roofs CRM

Provides comprehensive authentication and authorization functionality including
JWT token management, refresh tokens, password reset, email verification,
and role-based access control.

Security Features:
- JWT with RS256 algorithm for production (HS256 for development)
- Refresh token rotation
- Password hashing with bcrypt
- Email verification
- 2FA support (optional)
- Rate limiting on auth endpoints
- Session management with Redis

Author: iSwitch Roofs Development Team
Date: 2025-01-04
"""

import logging
import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import bcrypt
import jwt
from email_validator import EmailNotValidError, validate_email

from app.config import get_supabase_client
from app.services.notification import notification_service
from app.utils.redis_client import cache_delete, cache_get, cache_set

logger = logging.getLogger(__name__)


class UserRole:
    """User role constants"""

    ADMIN = "admin"
    MANAGER = "manager"
    SALES_REP = "sales_rep"
    FIELD_TECH = "field_tech"
    CUSTOMER = "customer"


class TokenType:
    """Token type constants"""

    ACCESS = "access"
    REFRESH = "refresh"
    RESET = "reset"
    VERIFICATION = "verification"
    TWO_FACTOR = "two_factor"


class AuthService:
    """
    Comprehensive authentication service handling user registration,
    login, JWT token management, and password operations.
    """

    def __init__(self):
        """Initialize authentication service with configuration"""
        # JWT Configuration
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expires = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))  # 1 hour
        self.refresh_token_expires = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 604800))  # 7 days
        self.reset_token_expires = 3600  # 1 hour
        self.verification_token_expires = 86400  # 24 hours

        # Password policy
        self.min_password_length = 8
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_number = True
        self.require_special = True

        # Rate limiting
        self.max_login_attempts = 5
        self.lockout_duration = 900  # 15 minutes

        # Initialize Supabase client lazily
        self._supabase = None

    @property
    def supabase(self):
        """Get Supabase client (lazy initialization)"""
        if self._supabase is None:
            self._supabase = get_supabase_client()
        return self._supabase

    def register_user(
        self,
        email: str,
        password: str,
        name: str,
        role: str = UserRole.SALES_REP,
        phone: str | None = None,
        team_id: str | None = None,
    ) -> tuple[bool, dict[str, Any] | None, str | None]:
        """
        Register a new user with email verification

        Args:
            email: User's email address
            password: Plain text password (will be hashed)
            name: User's full name
            role: User role (default: sales_rep)
            phone: Optional phone number
            team_id: Optional team assignment

        Returns:
            Tuple of (success, user_data, error_message)
        """
        try:
            # Validate email
            try:
                valid_email = validate_email(email, check_deliverability=False)
                email = valid_email.email.lower()
            except EmailNotValidError as e:
                return False, None, str(e)

            # Check if user already exists
            existing = self.supabase.table("users").select("id").eq("email", email).execute()
            if existing.data:
                return False, None, "User with this email already exists"

            # Validate password strength
            password_valid, password_error = self._validate_password(password)
            if not password_valid:
                return False, None, password_error

            # Hash password
            password_hash = self._hash_password(password)

            # Generate verification token
            verification_token = secrets.token_urlsafe(32)

            # Create user record
            user_data = {
                "id": str(uuid4()),
                "email": email,
                "password_hash": password_hash,
                "name": name,
                "role": role,
                "phone": phone,
                "team_id": team_id,
                "is_active": False,  # Inactive until email verified
                "is_verified": False,
                "verification_token": verification_token,
                "created_at": datetime.utcnow().isoformat(),
                "last_login": None,
                "failed_login_attempts": 0,
                "locked_until": None,
                "password_changed_at": datetime.utcnow().isoformat(),
                "settings": {
                    "notifications": {"email": True, "sms": bool(phone), "push": True},
                    "two_factor_enabled": False,
                },
            }

            # Insert user into database
            result = self.supabase.table("users").insert(user_data).execute()

            if not result.data:
                return False, None, "Failed to create user"

            created_user = result.data[0]

            # Send verification email
            self._send_verification_email(email, name, verification_token)

            # Remove sensitive data from response
            created_user.pop("password_hash", None)
            created_user.pop("verification_token", None)

            logger.info(f"User registered: {email} with role {role}")

            return True, created_user, None

        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            return False, None, str(e)

    def login(
        self, email: str, password: str, device_info: dict[str, Any] | None = None
    ) -> tuple[bool, dict[str, Any] | None, str | None]:
        """
        Authenticate user and generate JWT tokens

        Args:
            email: User's email
            password: Plain text password
            device_info: Optional device/browser information

        Returns:
            Tuple of (success, token_data, error_message)
        """
        try:
            email = email.lower()

            # Check rate limiting
            if self._is_rate_limited(email):
                return False, None, "Too many login attempts. Please try again later."

            # Get user from database
            result = self.supabase.table("users").select("*").eq("email", email).execute()

            if not result.data:
                self._record_failed_login(email)
                return False, None, "Invalid email or password"

            user = result.data[0]

            # Check if account is locked
            if user.get("locked_until"):
                locked_until = datetime.fromisoformat(user["locked_until"])
                if locked_until > datetime.utcnow():
                    remaining = int((locked_until - datetime.utcnow()).total_seconds() / 60)
                    return False, None, f"Account locked. Try again in {remaining} minutes."

            # Check if email is verified
            if not user.get("is_verified"):
                return False, None, "Email not verified. Please check your email."

            # Check if account is active
            if not user.get("is_active"):
                return False, None, "Account is inactive. Please contact support."

            # Verify password
            if not self._verify_password(password, user["password_hash"]):
                self._record_failed_login(email, user["id"])
                return False, None, "Invalid email or password"

            # Check if 2FA is enabled
            if user.get("settings", {}).get("two_factor_enabled"):
                # Begin two-factor flow: return a short-lived token; client must call /api/auth/2fa/complete
                two_factor_token = self._generate_token(
                    user_id=user["id"],
                    email=user["email"],
                    role=user["role"],
                    token_type=TokenType.TWO_FACTOR,
                )
                token_data = {
                    "requires_2fa": True,
                    "two_factor_token": two_factor_token,
                    "user": {
                        "id": user["id"],
                        "email": user["email"],
                        "name": user.get("name"),
                        "role": user.get("role"),
                    },
                }
                return True, token_data, None

            # Generate tokens
            access_token = self._generate_token(
                user_id=user["id"],
                email=user["email"],
                role=user["role"],
                token_type=TokenType.ACCESS,
            )

            refresh_token = self._generate_token(
                user_id=user["id"],
                email=user["email"],
                role=user["role"],
                token_type=TokenType.REFRESH,
            )

            # Create session in Redis
            session_id = str(uuid4())
            session_data = {
                "user_id": user["id"],
                "email": user["email"],
                "role": user["role"],
                "device_info": device_info,
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat(),
            }

            cache_set(f"session:{session_id}", session_data, ttl=self.refresh_token_expires)

            # Store refresh token in Redis
            cache_set(f"refresh_token:{user['id']}", refresh_token, ttl=self.refresh_token_expires)

            # Update last login
            self.supabase.table("users").update(
                {
                    "last_login": datetime.utcnow().isoformat(),
                    "failed_login_attempts": 0,
                    "locked_until": None,
                }
            ).eq("id", user["id"]).execute()

            # Log successful login
            self._log_auth_event(user["id"], "login", device_info)

            # Prepare response
            token_data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": self.access_token_expires,
                "session_id": session_id,
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "name": user["name"],
                    "role": user["role"],
                    "team_id": user.get("team_id"),
                },
            }

            logger.info(f"User logged in: {email}")

            return True, token_data, None

        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            return False, None, "An error occurred during login"

    def refresh_token(self, refresh_token: str) -> tuple[bool, dict[str, Any] | None, str | None]:
        """
        Generate new access token using refresh token

        Args:
            refresh_token: Valid refresh token

        Returns:
            Tuple of (success, token_data, error_message)
        """
        try:
            # Decode refresh token
            payload = self._decode_token(refresh_token, TokenType.REFRESH)

            if not payload:
                return False, None, "Invalid refresh token"

            user_id = payload.get("user_id")

            # Verify refresh token in Redis
            stored_token = cache_get(f"refresh_token:{user_id}")

            if stored_token != refresh_token:
                return False, None, "Invalid refresh token"

            # Get updated user data
            result = self.supabase.table("users").select("*").eq("id", user_id).execute()

            if not result.data:
                return False, None, "User not found"

            user = result.data[0]

            # Check if account is still active
            if not user.get("is_active"):
                return False, None, "Account is inactive"

            # Generate new access token
            new_access_token = self._generate_token(
                user_id=user["id"],
                email=user["email"],
                role=user["role"],
                token_type=TokenType.ACCESS,
            )

            # Optional: Rotate refresh token for enhanced security
            new_refresh_token = self._generate_token(
                user_id=user["id"],
                email=user["email"],
                role=user["role"],
                token_type=TokenType.REFRESH,
            )

            # Update refresh token in Redis
            cache_set(f"refresh_token:{user_id}", new_refresh_token, ttl=self.refresh_token_expires)

            return (
                True,
                {
                    "access_token": new_access_token,
                    "refresh_token": new_refresh_token,
                    "token_type": "Bearer",
                    "expires_in": self.access_token_expires,
                },
                None,
            )

        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return False, None, "Failed to refresh token"

    def logout(self, user_id: str, session_id: str | None = None) -> bool:
        """
        Logout user and invalidate tokens

        Args:
            user_id: User ID
            session_id: Optional session ID to logout specific session

        Returns:
            Success boolean
        """
        try:
            # Delete refresh token
            cache_delete(f"refresh_token:{user_id}")

            # Delete session
            if session_id:
                cache_delete(f"session:{session_id}")

            # Log logout event
            self._log_auth_event(user_id, "logout")

            logger.info(f"User logged out: {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")
            return False

    def request_password_reset(self, email: str) -> tuple[bool, str | None]:
        """
        Initiate password reset process

        Args:
            email: User's email address

        Returns:
            Tuple of (success, error_message)
        """
        try:
            email = email.lower()

            # Get user
            result = self.supabase.table("users").select("id", "name").eq("email", email).execute()

            if not result.data:
                # Don't reveal if user exists
                logger.warning(f"Password reset requested for non-existent email: {email}")
                return True, None

            user = result.data[0]

            # Generate reset token
            reset_token = secrets.token_urlsafe(32)

            # Store reset token in Redis with expiration
            cache_set(
                f"reset_token:{reset_token}",
                {"user_id": user["id"], "email": email},
                ttl=self.reset_token_expires,
            )

            # Send reset email
            self._send_password_reset_email(email, user["name"], reset_token)

            # Log password reset request
            self._log_auth_event(user["id"], "password_reset_requested")

            logger.info(f"Password reset requested for: {email}")

            return True, None

        except Exception as e:
            logger.error(f"Error requesting password reset: {str(e)}")
            return False, "Failed to process password reset request"

    def reset_password(self, reset_token: str, new_password: str) -> tuple[bool, str | None]:
        """
        Reset user password with token

        Args:
            reset_token: Password reset token
            new_password: New password

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get token data from Redis
            token_data = cache_get(f"reset_token:{reset_token}")

            if not token_data:
                return False, "Invalid or expired reset token"

            user_id = token_data["user_id"]

            # Validate new password
            password_valid, password_error = self._validate_password(new_password)
            if not password_valid:
                return False, password_error

            # Hash new password
            password_hash = self._hash_password(new_password)

            # Update user password
            self.supabase.table("users").update(
                {
                    "password_hash": password_hash,
                    "password_changed_at": datetime.utcnow().isoformat(),
                }
            ).eq("id", user_id).execute()

            # Delete reset token
            cache_delete(f"reset_token:{reset_token}")

            # Invalidate all existing sessions
            cache_delete(f"refresh_token:{user_id}")

            # Send confirmation email
            self._send_password_changed_email(token_data["email"])

            # Log password reset
            self._log_auth_event(user_id, "password_reset_completed")

            logger.info(f"Password reset completed for user: {user_id}")

            return True, None

        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}")
            return False, "Failed to reset password"

    def verify_email(self, verification_token: str) -> tuple[bool, str | None]:
        """
        Verify user email with token

        Args:
            verification_token: Email verification token

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Find user with verification token
            result = (
                self.supabase.table("users")
                .select("id", "email")
                .eq("verification_token", verification_token)
                .execute()
            )

            if not result.data:
                return False, "Invalid verification token"

            user = result.data[0]

            # Update user as verified
            self.supabase.table("users").update(
                {
                    "is_verified": True,
                    "is_active": True,
                    "verification_token": None,
                    "verified_at": datetime.utcnow().isoformat(),
                }
            ).eq("id", user["id"]).execute()

            # Send welcome email
            self._send_welcome_email(user["email"])

            # Log verification
            self._log_auth_event(user["id"], "email_verified")

            logger.info(f"Email verified for user: {user['email']}")

            return True, None

        except Exception as e:
            logger.error(f"Error verifying email: {str(e)}")
            return False, "Failed to verify email"

    def change_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> tuple[bool, str | None]:
        """
        Change user password (requires current password)

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get user
            result = (
                self.supabase.table("users")
                .select("password_hash", "email")
                .eq("id", user_id)
                .execute()
            )

            if not result.data:
                return False, "User not found"

            user = result.data[0]

            # Verify current password
            if not self._verify_password(current_password, user["password_hash"]):
                return False, "Current password is incorrect"

            # Validate new password
            password_valid, password_error = self._validate_password(new_password)
            if not password_valid:
                return False, password_error

            # Check if new password is same as current
            if self._verify_password(new_password, user["password_hash"]):
                return False, "New password must be different from current password"

            # Hash new password
            password_hash = self._hash_password(new_password)

            # Update password
            self.supabase.table("users").update(
                {
                    "password_hash": password_hash,
                    "password_changed_at": datetime.utcnow().isoformat(),
                }
            ).eq("id", user_id).execute()

            # Send confirmation email
            self._send_password_changed_email(user["email"])

            # Log password change
            self._log_auth_event(user_id, "password_changed")

            logger.info(f"Password changed for user: {user_id}")

            return True, None

        except Exception as e:
            logger.error(f"Error changing password: {str(e)}")
            return False, "Failed to change password"

    def validate_token(self, token: str) -> dict[str, Any] | None:
        """
        Validate and decode JWT token

        Args:
            token: JWT token

        Returns:
            Decoded token payload or None if invalid
        """
        return self._decode_token(token, TokenType.ACCESS)

    def get_user_permissions(self, role: str) -> list[str]:
        """
        Get permissions for a role

        Args:
            role: User role

        Returns:
            List of permission strings
        """
        permissions_map = {
            UserRole.ADMIN: [
                "users:*",
                "leads:*",
                "customers:*",
                "projects:*",
                "analytics:*",
                "settings:*",
                "team:*",
                "reviews:*",
                "partnerships:*",
            ],
            UserRole.MANAGER: [
                "users:read",
                "users:update",
                "leads:*",
                "customers:*",
                "projects:*",
                "analytics:read",
                "team:*",
                "reviews:*",
            ],
            UserRole.SALES_REP: [
                "leads:read",
                "leads:create",
                "leads:update",
                "customers:read",
                "customers:create",
                "customers:update",
                "projects:read",
                "projects:create",
                "analytics:read:own",
            ],
            UserRole.FIELD_TECH: [
                "projects:read",
                "projects:update:status",
                "customers:read",
                "appointments:read:assigned",
            ],
            UserRole.CUSTOMER: ["projects:read:own", "appointments:read:own", "reviews:create"],
        }

        return permissions_map.get(role, [])

    def has_permission(self, user_role: str, required_permission: str) -> bool:
        """
        Check if role has required permission

        Args:
            user_role: User's role
            required_permission: Permission to check

        Returns:
            True if user has permission
        """
        user_permissions = self.get_user_permissions(user_role)

        # Check for wildcard permissions
        for permission in user_permissions:
            if permission.endswith(":*"):
                resource = permission.split(":")[0]
                if required_permission.startswith(f"{resource}:"):
                    return True
            elif permission == required_permission:
                return True

        return False

    # Private helper methods

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

    def _validate_password(self, password: str) -> tuple[bool, str | None]:
        """
        Validate password strength

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < self.min_password_length:
            return False, f"Password must be at least {self.min_password_length} characters"

        if self.require_uppercase and not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"

        if self.require_lowercase and not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"

        if self.require_number and not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"

        if self.require_special and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False, "Password must contain at least one special character"

        return True, None

    def _generate_token(
        self, user_id: str, email: str, role: str, token_type: str = TokenType.ACCESS
    ) -> str:
        """Generate JWT token"""
        now = datetime.now(UTC)

        if token_type == TokenType.ACCESS:
            expires_delta = timedelta(seconds=self.access_token_expires)
        elif token_type == TokenType.REFRESH:
            expires_delta = timedelta(seconds=self.refresh_token_expires)
        elif token_type == TokenType.TWO_FACTOR:
            expires_delta = timedelta(minutes=5)
        else:
            expires_delta = timedelta(hours=1)

        payload = {
            "user_id": user_id,
            "email": email,
            "role": role,
            "token_type": token_type,
            "iat": now,
            "exp": now + expires_delta,
            "jti": str(uuid4()),  # JWT ID for token revocation
        }

        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def _decode_token(
        self, token: str, expected_type: str = TokenType.ACCESS
    ) -> dict[str, Any] | None:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])

            # Validate token type
            if payload.get("token_type") != expected_type:
                logger.warning(
                    f"Invalid token type: expected {expected_type}, got {payload.get('token_type')}"
                )
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None

    def _is_rate_limited(self, email: str) -> bool:
        """Check if email is rate limited"""
        key = f"login_attempts:{email}"
        attempts = cache_get(key)

        if attempts and int(attempts) >= self.max_login_attempts:
            return True

        return False

    def _record_failed_login(self, email: str, user_id: str | None = None):
        """Record failed login attempt"""
        key = f"login_attempts:{email}"
        attempts = cache_get(key)

        if attempts:
            new_attempts = int(attempts) + 1
        else:
            new_attempts = 1

        cache_set(key, new_attempts, ttl=self.lockout_duration)

        # If user exists, update failed attempts in database
        if user_id:
            self.supabase.table("users").update({"failed_login_attempts": new_attempts}).eq(
                "id", user_id
            ).execute()

            # Lock account after max attempts
            if new_attempts >= self.max_login_attempts:
                locked_until = datetime.utcnow() + timedelta(seconds=self.lockout_duration)
                self.supabase.table("users").update({"locked_until": locked_until.isoformat()}).eq(
                    "id", user_id
                ).execute()

    def _log_auth_event(
        self, user_id: str, event_type: str, metadata: dict[str, Any] | None = None
    ):
        """Log authentication event"""
        try:
            event_data = {
                "id": str(uuid4()),
                "user_id": user_id,
                "event_type": event_type,
                "metadata": metadata,
                "ip_address": metadata.get("ip_address") if metadata else None,
                "user_agent": metadata.get("user_agent") if metadata else None,
                "created_at": datetime.utcnow().isoformat(),
            }

            self.supabase.table("auth_logs").insert(event_data).execute()

        except Exception as e:
            logger.error(f"Error logging auth event: {str(e)}")

    def _send_verification_email(self, email: str, name: str, token: str):
        """Send email verification link"""
        try:
            verification_url = (
                f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/verify-email?token={token}"
            )

            notification_service.send_notification(
                type="email_verification",
                data={"name": name, "verification_url": verification_url},
                recipient_email=email,
            )

        except Exception as e:
            logger.error(f"Error sending verification email: {str(e)}")

    def _send_password_reset_email(self, email: str, name: str, token: str):
        """Send password reset email"""
        try:
            reset_url = (
                f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={token}"
            )

        except Exception as e:
            logger.error(f"Error sending password reset email: {str(e)}")

    # ====================== 2FA (TOTP) METHODS ======================

    def generate_two_factor_secret(self, user_id: str) -> tuple[bool, dict | None, str | None]:
        """
        Generate and store a TOTP secret for a user. Returns provisioning URI for authenticator apps.
        """
        try:
            import pyotp

            # Get user
            result = self.supabase.table("users").select("id,email,settings").eq("id", user_id).execute()
            if not result.data:
                return False, None, "User not found"

            user = result.data[0]
            secret = pyotp.random_base32()
            settings = user.get("settings") or {}
            settings["two_factor_secret"] = secret
            settings["two_factor_enabled"] = False

            self.supabase.table("users").update({"settings": settings}).eq("id", user_id).execute()

            otpauth_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.get("email"), issuer_name="iSwitch Roofs CRM")
            return True, {"secret": secret, "otpauth_uri": otpauth_uri}, None
        except Exception as e:
            logger.error(f"Error generating 2FA secret: {str(e)}")
            return False, None, str(e)

    def verify_two_factor_code(self, user_id: str, code: str) -> tuple[bool, str | None]:
        """Verify a TOTP code for the user and enable 2FA if valid."""
        try:
            import pyotp

            result = self.supabase.table("users").select("id,settings").eq("id", user_id).execute()
            if not result.data:
                return False, "User not found"

            user = result.data[0]
            settings = user.get("settings") or {}
            secret = settings.get("two_factor_secret")
            if not secret:
                return False, "2FA not enrolled"

            totp = pyotp.TOTP(secret)
            if not totp.verify(code, valid_window=1):
                return False, "Invalid 2FA code"

            settings["two_factor_enabled"] = True
            self.supabase.table("users").update({"settings": settings}).eq("id", user_id).execute()
            return True, None
        except Exception as e:
            logger.error(f"Error verifying 2FA code: {str(e)}")
            return False, str(e)

    def generate_backup_codes(self, user_id: str, count: int = 10) -> list[str]:
        """Generate one-time backup codes for 2FA and store hashed versions in settings."""
        import hashlib
        import secrets as _secrets

        result = self.supabase.table("users").select("id,settings").eq("id", user_id).execute()
        if not result.data:
            return []
        user = result.data[0]
        settings = user.get("settings") or {}

        codes = []
        hashed_codes = []
        for _ in range(count):
            code = _secrets.token_hex(5)
            codes.append(code)
            hashed_codes.append(hashlib.sha256(code.encode()).hexdigest())

        settings["two_factor_backup_codes"] = hashed_codes
        self.supabase.table("users").update({"settings": settings}).eq("id", user_id).execute()
        return codes

    def verify_backup_code(self, user_id: str, code: str) -> bool:
        """Verify and consume a backup code."""
        import hashlib

        result = self.supabase.table("users").select("id,settings").eq("id", user_id).execute()
        if not result.data:
            return False
        user = result.data[0]
        settings = user.get("settings") or {}
        hashes = settings.get("two_factor_backup_codes") or []
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        if code_hash in hashes:
            # consume
            hashes.remove(code_hash)
            settings["two_factor_backup_codes"] = hashes
            self.supabase.table("users").update({"settings": settings}).eq("id", user_id).execute()
            return True
        return False

    def disable_two_factor(self, user_id: str) -> bool:
        """Disable 2FA for a user and clear secrets/backup codes."""
        result = self.supabase.table("users").select("id,settings").eq("id", user_id).execute()
        if not result.data:
            return False
        user = result.data[0]
        settings = user.get("settings") or {}
        settings.pop("two_factor_secret", None)
        settings.pop("two_factor_backup_codes", None)
        settings["two_factor_enabled"] = False
        self.supabase.table("users").update({"settings": settings}).eq("id", user_id).execute()
        return True

    def complete_two_factor_login(
        self,
        two_factor_token: str,
        code: str | None = None,
        backup_code: str | None = None,
        device_info: dict | None = None,
    ) -> tuple[bool, dict | None, str | None]:
        """
        Verify 2FA token/code and issue access/refresh tokens.
        """
        try:
            # Decode 2FA token
            payload = self._decode_token(two_factor_token, TokenType.TWO_FACTOR)
            if not payload:
                return False, None, "Invalid or expired 2FA token"

            user_id = payload.get("user_id")
            result = self.supabase.table("users").select("*").eq("id", user_id).execute()
            if not result.data:
                return False, None, "User not found"
            user = result.data[0]

            # Verify code or backup
            ok = False
            if code:
                ok, err = self.verify_two_factor_code(user_id, code)
                if not ok:
                    return False, None, err or "Invalid 2FA code"
            elif backup_code:
                if not self.verify_backup_code(user_id, backup_code):
                    return False, None, "Invalid backup code"
            else:
                return False, None, "2FA code or backup_code required"

            # Issue tokens (same as login flow)
            access_token = self._generate_token(
                user_id=user["id"], email=user["email"], role=user["role"], token_type=TokenType.ACCESS
            )
            refresh_token = self._generate_token(
                user_id=user["id"], email=user["email"], role=user["role"], token_type=TokenType.REFRESH
            )

            session_id = str(uuid4())
            session_data = {
                "user_id": user["id"],
                "email": user["email"],
                "role": user["role"],
                "device_info": device_info,
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat(),
            }
            cache_set(f"session:{session_id}", session_data, ttl=self.refresh_token_expires)
            cache_set(f"refresh_token:{user['id']}", refresh_token, ttl=self.refresh_token_expires)

            # Update last login
            self.supabase.table("users").update(
                {"last_login": datetime.utcnow().isoformat(), "failed_login_attempts": 0, "locked_until": None}
            ).eq("id", user["id"]).execute()

            token_data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": self.access_token_expires,
                "session_id": session_id,
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "name": user.get("name"),
                    "role": user.get("role"),
                    "team_id": user.get("team_id"),
                },
            }
            return True, token_data, None
        except Exception as e:
            logger.error(f"Error completing 2FA login: {str(e)}")
            return False, None, "Failed to complete 2FA login"

            notification_service.send_notification(
                type="password_reset",
                data={"name": name, "reset_url": reset_url, "expires_in": "1 hour"},
                recipient_email=email,
            )

        except Exception as e:
            logger.error(f"Error sending password reset email: {str(e)}")

    def _send_password_changed_email(self, email: str):
        """Send password changed notification"""
        try:
            notification_service.send_notification(
                type="password_changed",
                data={"changed_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")},
                recipient_email=email,
            )

        except Exception as e:
            logger.error(f"Error sending password changed email: {str(e)}")

    def _send_welcome_email(self, email: str):
        """Send welcome email after verification"""
        try:
            notification_service.send_notification(
                type="welcome",
                data={"login_url": f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/login"},
                recipient_email=email,
            )

        except Exception as e:
            logger.error(f"Error sending welcome email: {str(e)}")


# Create singleton instance
auth_service = AuthService()


# Export convenience functions
def register_user(
    email: str, password: str, name: str, **kwargs
) -> tuple[bool, dict[str, Any] | None, str | None]:
    """Register a new user"""
    return auth_service.register_user(email, password, name, **kwargs)


def login(
    email: str, password: str, device_info: dict[str, Any] | None = None
) -> tuple[bool, dict[str, Any] | None, str | None]:
    """Login user"""
    return auth_service.login(email, password, device_info)


def logout(user_id: str, session_id: str | None = None) -> bool:
    """Logout user"""
    return auth_service.logout(user_id, session_id)


def validate_token(token: str) -> dict[str, Any] | None:
    """Validate JWT token"""
    return auth_service.validate_token(token)


def refresh_token(refresh_token: str) -> tuple[bool, dict[str, Any] | None, str | None]:
    """Refresh access token"""
    return auth_service.refresh_token(refresh_token)


def has_permission(user_role: str, required_permission: str) -> bool:
    """Check if role has permission"""
    return auth_service.has_permission(user_role, required_permission)
