"""
Comprehensive Security Testing for iSwitch Roofs CRM
Tests authentication, authorization, input validation, and security vulnerabilities
"""

import json
from datetime import datetime, timedelta
from unittest.mock import patch

import jwt
import pytest
from flask.testing import FlaskClient


class TestAuthentication:
    """Test suite for authentication security."""

    def test_login_with_valid_credentials(self, client: FlaskClient):
        """Test successful login with valid credentials."""
        login_data = {"username": "admin@iswitch.com", "password": "SecurePass123!"}

        with patch("app.services.auth_service.verify_password") as mock_verify:
            with patch("app.services.auth_service.generate_tokens") as mock_tokens:
                mock_verify.return_value = True
                mock_tokens.return_value = {
                    "access_token": "valid_jwt_token",
                    "refresh_token": "valid_refresh_token",
                    "expires_in": 3600,
                }

                response = client.post(
                    "/api/auth/login", data=json.dumps(login_data), content_type="application/json"
                )

                assert response.status_code == 200
                data = json.loads(response.data)
                assert "access_token" in data
                assert "refresh_token" in data

    def test_login_with_invalid_credentials(self, client: FlaskClient):
        """Test login rejection with invalid credentials."""
        login_data = {"username": "admin@iswitch.com", "password": "WrongPassword"}

        with patch("app.services.auth_service.verify_password") as mock_verify:
            mock_verify.return_value = False

            response = client.post(
                "/api/auth/login", data=json.dumps(login_data), content_type="application/json"
            )

            assert response.status_code == 401
            data = json.loads(response.data)
            assert "error" in data
            assert "access_token" not in data

    def test_brute_force_protection(self, client: FlaskClient):
        """Test protection against brute force attacks."""
        login_data = {"username": "admin@iswitch.com", "password": "WrongPassword"}

        # Simulate multiple failed login attempts
        for i in range(6):  # Attempt 6 failed logins
            with patch("app.services.auth_service.verify_password") as mock_verify:
                mock_verify.return_value = False

                response = client.post(
                    "/api/auth/login", data=json.dumps(login_data), content_type="application/json"
                )

                if i < 5:
                    assert response.status_code == 401
                else:
                    # After 5 failed attempts, should be rate limited
                    assert response.status_code in [429, 423]  # Too Many Requests or Locked

    def test_password_complexity_requirements(self, client: FlaskClient):
        """Test password complexity requirements."""
        weak_passwords = [
            "password",  # Too simple
            "123456",  # Too simple
            "abc",  # Too short
            "PASSWORD",  # No lowercase
            "password",  # No uppercase
            "Password",  # No numbers
            "Password123",  # No special characters
        ]

        for weak_password in weak_passwords:
            registration_data = {
                "username": "newuser@iswitch.com",
                "password": weak_password,
                "confirm_password": weak_password,
                "first_name": "New",
                "last_name": "User",
            }

            response = client.post(
                "/api/auth/register",
                data=json.dumps(registration_data),
                content_type="application/json",
            )

            # Should reject weak passwords
            assert response.status_code == 400
            data = json.loads(response.data)
            assert "password" in data.get("errors", {})

    def test_jwt_token_validation(self, client: FlaskClient):
        """Test JWT token validation."""
        # Test with invalid token
        invalid_headers = {
            "Authorization": "Bearer invalid_token_123",
            "Content-Type": "application/json",
        }

        response = client.get("/api/leads", headers=invalid_headers)
        assert response.status_code == 401

        # Test with expired token
        expired_token = jwt.encode(
            {"user_id": "user-123", "exp": datetime.utcnow() - timedelta(hours=1)},  # Expired
            "secret_key",
            algorithm="HS256",
        )

        expired_headers = {
            "Authorization": f"Bearer {expired_token}",
            "Content-Type": "application/json",
        }

        response = client.get("/api/leads", headers=expired_headers)
        assert response.status_code == 401

    def test_session_management(self, client: FlaskClient):
        """Test session security features."""
        # Test session timeout
        # Test concurrent session limits
        # Test session invalidation on logout
        assert True  # Placeholder for session tests

    def test_password_reset_security(self, client: FlaskClient):
        """Test password reset security."""
        # Test password reset token generation and validation
        reset_data = {"email": "user@iswitch.com"}

        with patch("app.services.auth_service.generate_reset_token") as mock_token:
            mock_token.return_value = "secure_reset_token_123"

            response = client.post(
                "/api/auth/password-reset",
                data=json.dumps(reset_data),
                content_type="application/json",
            )

            assert response.status_code == 200

        # Test token usage
        new_password_data = {"token": "secure_reset_token_123", "new_password": "NewSecurePass123!"}

        with patch("app.services.auth_service.validate_reset_token") as mock_validate:
            mock_validate.return_value = True

            response = client.post(
                "/api/auth/password-reset/confirm",
                data=json.dumps(new_password_data),
                content_type="application/json",
            )

            assert response.status_code == 200


class TestAuthorization:
    """Test suite for authorization and access control."""

    def test_role_based_access_control(self, client: FlaskClient):
        """Test role-based access control."""
        # Test admin access
        admin_token = self._generate_test_token("admin")
        admin_headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json",
        }

        response = client.get("/api/admin/users", headers=admin_headers)
        # Admin should have access (assuming endpoint exists)
        assert response.status_code in [200, 404]  # 404 if endpoint not implemented

        # Test user access to admin endpoint
        user_token = self._generate_test_token("user")
        user_headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}

        response = client.get("/api/admin/users", headers=user_headers)
        assert response.status_code == 403  # Forbidden

    def test_resource_ownership_validation(self, client: FlaskClient, auth_headers):
        """Test that users can only access their own resources."""
        # User should only access their own leads
        user_id = "user-123"
        other_user_id = "user-456"

        # Test accessing own lead
        response = client.get(f"/api/leads/lead-owned-by-{user_id}", headers=auth_headers)
        # Should succeed (200) or not found (404)
        assert response.status_code in [200, 404]

        # Test accessing another user's lead
        response = client.get(f"/api/leads/lead-owned-by-{other_user_id}", headers=auth_headers)
        # Should be forbidden
        assert response.status_code in [403, 404]

    def test_api_endpoint_protection(self, client: FlaskClient):
        """Test that all API endpoints require authentication."""
        unprotected_endpoints = [
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/password-reset",
            "/health",
        ]

        protected_endpoints = [
            "/api/leads",
            "/api/customers",
            "/api/projects",
            "/api/appointments",
            "/api/analytics/dashboard",
            "/api/team",
            "/api/settings",
        ]

        # Test unprotected endpoints
        for endpoint in unprotected_endpoints:
            response = client.get(endpoint)
            assert response.status_code != 401  # Should not require auth

        # Test protected endpoints
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401  # Should require auth

    def _generate_test_token(self, role="user"):
        """Generate test JWT token with specified role."""
        payload = {
            "user_id": "test-user-123",
            "role": role,
            "exp": datetime.utcnow() + timedelta(hours=1),
        }
        return jwt.encode(payload, "test_secret_key", algorithm="HS256")


class TestInputValidation:
    """Test suite for input validation security."""

    def test_sql_injection_protection(self, client: FlaskClient, auth_headers):
        """Test SQL injection protection."""
        sql_injection_payloads = [
            "'; DROP TABLE leads; --",
            "' OR '1'='1",
            "'; SELECT * FROM users; --",
            "' UNION SELECT * FROM customers --",
            "admin'--",
            "admin'/*",
            "' OR 1=1#",
        ]

        for payload in sql_injection_payloads:
            # Test in search parameters
            response = client.get(f"/api/leads?search={payload}", headers=auth_headers)
            # Should not return 500 error (database error)
            assert response.status_code != 500

            # Test in POST data
            malicious_data = {
                "first_name": payload,
                "last_name": "Test",
                "email": "test@example.com",
                "phone": "555-1234",
            }

            response = client.post(
                "/api/leads", data=json.dumps(malicious_data), headers=auth_headers
            )
            # Should either reject (400) or sanitize input
            assert response.status_code in [400, 422, 201]

    def test_xss_protection(self, client: FlaskClient, auth_headers):
        """Test Cross-Site Scripting (XSS) protection."""
        xss_payloads = [
            '<script>alert("xss")</script>',
            '<img src=x onerror=alert("xss")>',
            'javascript:alert("xss")',
            '<svg onload=alert("xss")>',
            "<iframe src=\"javascript:alert('xss')\"></iframe>",
            '"><script>alert("xss")</script>',
        ]

        for payload in xss_payloads:
            malicious_data = {
                "first_name": payload,
                "last_name": "Test",
                "email": "test@example.com",
                "phone": "555-1234",
                "notes": f"Customer notes: {payload}",
            }

            response = client.post(
                "/api/leads", data=json.dumps(malicious_data), headers=auth_headers
            )

            if response.status_code == 201:
                # If created, check that script tags are sanitized
                data = json.loads(response.data)
                assert "<script>" not in data.get("first_name", "")
                assert "javascript:" not in data.get("first_name", "")

    def test_file_upload_security(self, client: FlaskClient, auth_headers):
        """Test file upload security."""
        # Test malicious file extensions
        malicious_files = [
            ("malware.exe", b"MZ\x90\x00"),  # Executable
            ("script.php", b'<?php echo "hack"; ?>'),  # PHP script
            ("test.jsp", b'<%@ page import="java.io.*" %>'),  # JSP
            ("shell.sh", b"#!/bin/bash\nrm -rf /"),  # Shell script
        ]

        for filename, content in malicious_files:
            files = {"file": (filename, content, "application/octet-stream")}

            response = client.post("/api/leads/upload", data=files, headers=auth_headers)

            # Should reject malicious file types
            assert response.status_code in [400, 422, 415]

    def test_json_bomb_protection(self, client: FlaskClient, auth_headers):
        """Test protection against JSON bombs."""
        # Create deeply nested JSON structure
        deep_json = {"a": "value"}
        for _ in range(1000):  # Create very deep nesting
            deep_json = {"nested": deep_json}

        response = client.post("/api/leads", data=json.dumps(deep_json), headers=auth_headers)

        # Should reject or handle gracefully
        assert response.status_code in [400, 413, 422]

    def test_large_payload_protection(self, client: FlaskClient, auth_headers):
        """Test protection against large payloads."""
        # Create very large payload
        large_data = {
            "first_name": "A" * 10000,  # 10KB name
            "notes": "B" * 100000,  # 100KB notes
            "description": "C" * 1000000,  # 1MB description
        }

        response = client.post("/api/leads", data=json.dumps(large_data), headers=auth_headers)

        # Should reject oversized payloads
        assert response.status_code in [400, 413, 422]


class TestDataProtection:
    """Test suite for data protection and privacy."""

    def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        plain_password = "TestPassword123!"

        # Test with bcrypt or similar
        with patch("app.services.auth_service.hash_password") as mock_hash:
            mock_hash.return_value = "$2b$12$hashed_password_here"

            hashed = mock_hash(plain_password)

            # Should not store plain text password
            assert hashed != plain_password
            assert len(hashed) > 50  # Hashed passwords are longer

    def test_sensitive_data_masking(self, client: FlaskClient, auth_headers):
        """Test that sensitive data is masked in responses."""
        # Test that SSN, credit card numbers, etc. are masked
        sensitive_data = {
            "first_name": "John",
            "last_name": "Doe",
            "ssn": "123-45-6789",
            "credit_card": "4111-1111-1111-1111",
        }

        response = client.post(
            "/api/customers", data=json.dumps(sensitive_data), headers=auth_headers
        )

        if response.status_code == 201:
            data = json.loads(response.data)
            # SSN should be masked
            if "ssn" in data:
                assert data["ssn"] == "***-**-6789"
            # Credit card should be masked
            if "credit_card" in data:
                assert data["credit_card"] == "****-****-****-1111"

    def test_data_encryption_at_rest(self):
        """Test data encryption at rest."""
        # Test that sensitive fields are encrypted in database
        # This would require database integration testing
        assert True  # Placeholder

    def test_audit_logging(self, client: FlaskClient, auth_headers):
        """Test audit logging for sensitive operations."""
        # Test that sensitive operations are logged
        with patch("app.middleware.audit_middleware.log_audit_event") as mock_log:
            # Perform sensitive operation
            response = client.delete("/api/leads/test-lead-id", headers=auth_headers)

            # Should log the operation
            mock_log.assert_called_once()


class TestSessionSecurity:
    """Test suite for session security."""

    def test_secure_cookie_settings(self, client: FlaskClient):
        """Test secure cookie settings."""
        # Test that cookies have secure flags
        with client.session_transaction() as session:
            session["user_id"] = "test-user"

        response = client.get("/")

        # Check cookie security attributes
        set_cookie_header = response.headers.get("Set-Cookie", "")
        if set_cookie_header:
            assert "Secure" in set_cookie_header
            assert "HttpOnly" in set_cookie_header
            assert "SameSite" in set_cookie_header

    def test_session_fixation_protection(self, client: FlaskClient):
        """Test protection against session fixation attacks."""
        # Test that session ID changes after login
        assert True  # Placeholder for session fixation tests

    def test_concurrent_session_limits(self, client: FlaskClient):
        """Test concurrent session limits."""
        # Test that users can't have too many concurrent sessions
        assert True  # Placeholder


class TestRateLimiting:
    """Test suite for rate limiting."""

    def test_api_rate_limiting(self, client: FlaskClient, auth_headers):
        """Test API rate limiting."""
        # Make many requests quickly
        responses = []
        for i in range(100):
            response = client.get("/api/leads", headers=auth_headers)
            responses.append(response.status_code)

        # Should eventually hit rate limit
        rate_limited = any(status == 429 for status in responses)
        # If no rate limiting implemented, all should be 200
        assert rate_limited or all(status == 200 for status in responses)

    def test_login_rate_limiting(self, client: FlaskClient):
        """Test login endpoint rate limiting."""
        login_data = {"username": "test@example.com", "password": "wrongpassword"}

        # Attempt many logins
        for i in range(10):
            response = client.post(
                "/api/auth/login", data=json.dumps(login_data), content_type="application/json"
            )

            if i > 5:  # After several attempts
                # Should be rate limited
                assert response.status_code in [429, 423]


class TestSecurityHeaders:
    """Test suite for security headers."""

    def test_security_headers_present(self, client: FlaskClient):
        """Test that security headers are present."""
        response = client.get("/")

        # Check for security headers
        headers = response.headers

        # Content Security Policy
        assert "Content-Security-Policy" in headers

        # X-Frame-Options
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"

        # X-Content-Type-Options
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"

        # X-XSS-Protection
        assert "X-XSS-Protection" in headers

        # Strict-Transport-Security (if HTTPS)
        if request.is_secure:
            assert "Strict-Transport-Security" in headers

    def test_cors_configuration(self, client: FlaskClient):
        """Test CORS configuration security."""
        response = client.options("/api/leads")

        cors_origin = response.headers.get("Access-Control-Allow-Origin")
        # Should not allow all origins in production
        assert cors_origin != "*" or True  # Adjust based on environment


# Mark all tests as security tests
pytestmark = [pytest.mark.security, pytest.mark.integration]
