"""
Authentication API Routes for iSwitch Roofs CRM

Provides REST endpoints for user authentication including registration,
login, logout, token refresh, password reset, and email verification.

Security Features:
- JWT-based authentication
- Refresh token rotation
- Rate limiting on auth endpoints
- Device tracking
- Audit logging

Author: iSwitch Roofs Development Team
Date: 2025-01-04
"""

from flask import Blueprint, request, jsonify, g
from typing import Optional
import logging
from datetime import datetime

from app.services.auth_service import auth_service, UserRole
from app.utils.auth import require_auth
from app.utils.validators import validate_email_format, validate_phone_format

logger = logging.getLogger(__name__)
bp = Blueprint('auth', __name__)


@bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user account

    Request Body:
        {
            "email": "user@example.com",
            "password": "SecurePassword123!",
            "name": "John Doe",
            "phone": "+1234567890",  // optional
            "role": "sales_rep",     // optional, default: sales_rep
            "team_id": "uuid"         // optional
        }

    Returns:
        201: User created successfully
        400: Validation error
        409: User already exists
        500: Server error

    Example:
        POST /api/auth/register
        {
            "email": "john@iswitchroofs.com",
            "password": "MySecure@Pass123",
            "name": "John Smith",
            "phone": "+12485551234",
            "role": "sales_rep"
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Validate required fields
        required_fields = ['email', 'password', 'name']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400

        # Validate email format
        if not validate_email_format(data['email']):
            return jsonify({"error": "Invalid email format"}), 400

        # Validate phone format if provided
        phone = data.get('phone')
        if phone and not validate_phone_format(phone):
            return jsonify({"error": "Invalid phone format"}), 400

        # Validate role if provided
        role = data.get('role', UserRole.SALES_REP)
        valid_roles = [UserRole.ADMIN, UserRole.MANAGER, UserRole.SALES_REP, UserRole.FIELD_TECH]
        if role not in valid_roles:
            return jsonify({"error": f"Invalid role. Must be one of: {', '.join(valid_roles)}"}), 400

        # Register user
        success, user_data, error = auth_service.register_user(
            email=data['email'],
            password=data['password'],
            name=data['name'],
            phone=phone,
            role=role,
            team_id=data.get('team_id')
        )

        if not success:
            if "already exists" in str(error):
                return jsonify({"error": error}), 409
            return jsonify({"error": error}), 400

        return jsonify({
            "success": True,
            "message": "User registered successfully. Please check your email to verify your account.",
            "user": user_data
        }), 201

    except Exception as e:
        logger.error(f"Error in registration: {str(e)}")
        return jsonify({"error": "Failed to register user"}), 500


@bp.route('/login', methods=['POST'])
def login():
    """
    Login user and get JWT tokens

    Request Body:
        {
            "email": "user@example.com",
            "password": "password",
            "device_info": {  // optional
                "device_type": "web",
                "browser": "Chrome",
                "os": "Windows",
                "ip_address": "192.168.1.1"
            }
        }

    Returns:
        200: Login successful with tokens
        400: Invalid credentials
        403: Account locked or unverified
        429: Too many attempts (rate limited)
        500: Server error

    Example:
        POST /api/auth/login
        {
            "email": "john@iswitchroofs.com",
            "password": "MySecure@Pass123"
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Validate required fields
        if 'email' not in data or 'password' not in data:
            return jsonify({"error": "Email and password are required"}), 400

        # Get device info
        device_info = data.get('device_info', {})
        if not device_info:
            # Extract from request headers
            device_info = {
                'user_agent': request.headers.get('User-Agent'),
                'ip_address': request.remote_addr,
                'device_type': 'web'
            }

        # Attempt login
        success, token_data, error = auth_service.login(
            email=data['email'],
            password=data['password'],
            device_info=device_info
        )

        if not success:
            if "too many" in str(error).lower():
                return jsonify({"error": error}), 429
            elif "locked" in str(error).lower() or "inactive" in str(error).lower():
                return jsonify({"error": error}), 403
            elif "not verified" in str(error).lower():
                return jsonify({"error": error}), 403
            else:
                return jsonify({"error": error}), 400

        return jsonify({
            "success": True,
            "message": "Login successful",
            **token_data
        }), 200

    except Exception as e:
        logger.error(f"Error in login: {str(e)}")
        return jsonify({"error": "Failed to login"}), 500


@bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """
    Logout user and invalidate tokens

    Headers:
        Authorization: Bearer <access_token>

    Request Body (optional):
        {
            "session_id": "session-uuid"
        }

    Returns:
        200: Logout successful
        401: Unauthorized
        500: Server error

    Example:
        POST /api/auth/logout
    """
    try:
        # Get user from request context (set by require_auth)
        user = g.get('user')
        if not user:
            return jsonify({"error": "User not found in context"}), 401

        # Get session ID if provided
        data = request.get_json() or {}
        session_id = data.get('session_id')

        # Logout user
        success = auth_service.logout(user['user_id'], session_id)

        if not success:
            return jsonify({"error": "Failed to logout"}), 500

        return jsonify({
            "success": True,
            "message": "Logout successful"
        }), 200

    except Exception as e:
        logger.error(f"Error in logout: {str(e)}")
        return jsonify({"error": "Failed to logout"}), 500


@bp.route('/refresh', methods=['POST'])
def refresh_token():
    """
    Refresh access token using refresh token

    Request Body:
        {
            "refresh_token": "refresh_token_string"
        }

    Returns:
        200: New tokens generated
        400: Invalid refresh token
        500: Server error

    Example:
        POST /api/auth/refresh
        {
            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
        }
    """
    try:
        data = request.get_json()

        if not data or 'refresh_token' not in data:
            return jsonify({"error": "Refresh token is required"}), 400

        # Refresh token
        success, token_data, error = auth_service.refresh_token(data['refresh_token'])

        if not success:
            return jsonify({"error": error}), 400

        return jsonify({
            "success": True,
            "message": "Token refreshed successfully",
            **token_data
        }), 200

    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        return jsonify({"error": "Failed to refresh token"}), 500


@bp.route('/password/reset/request', methods=['POST'])
def request_password_reset():
    """
    Request password reset email

    Request Body:
        {
            "email": "user@example.com"
        }

    Returns:
        200: Reset email sent (always returns 200 for security)
        500: Server error

    Example:
        POST /api/auth/password/reset/request
        {
            "email": "john@iswitchroofs.com"
        }
    """
    try:
        data = request.get_json()

        if not data or 'email' not in data:
            return jsonify({"error": "Email is required"}), 400

        # Request password reset
        success, error = auth_service.request_password_reset(data['email'])

        # Always return success for security (don't reveal if email exists)
        return jsonify({
            "success": True,
            "message": "If an account exists with this email, a password reset link has been sent."
        }), 200

    except Exception as e:
        logger.error(f"Error requesting password reset: {str(e)}")
        return jsonify({"error": "Failed to process request"}), 500


@bp.route('/password/reset', methods=['POST'])
def reset_password():
    """
    Reset password with token

    Request Body:
        {
            "token": "reset_token_string",
            "new_password": "NewSecurePassword123!"
        }

    Returns:
        200: Password reset successful
        400: Invalid token or password
        500: Server error

    Example:
        POST /api/auth/password/reset
        {
            "token": "abc123...",
            "new_password": "MyNewSecure@Pass456"
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Validate required fields
        if 'token' not in data or 'new_password' not in data:
            return jsonify({"error": "Token and new password are required"}), 400

        # Reset password
        success, error = auth_service.reset_password(
            reset_token=data['token'],
            new_password=data['new_password']
        )

        if not success:
            return jsonify({"error": error}), 400

        return jsonify({
            "success": True,
            "message": "Password reset successful. Please login with your new password."
        }), 200

    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        return jsonify({"error": "Failed to reset password"}), 500


@bp.route('/password/change', methods=['POST'])
@require_auth
def change_password():
    """
    Change password (requires authentication)

    Headers:
        Authorization: Bearer <access_token>

    Request Body:
        {
            "current_password": "CurrentPassword",
            "new_password": "NewSecurePassword123!"
        }

    Returns:
        200: Password changed successfully
        400: Invalid password
        401: Unauthorized
        500: Server error

    Example:
        POST /api/auth/password/change
        {
            "current_password": "MyOldPass123",
            "new_password": "MyNewSecure@Pass456"
        }
    """
    try:
        # Get user from request context
        user = g.get('user')
        if not user:
            return jsonify({"error": "User not found in context"}), 401

        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Validate required fields
        if 'current_password' not in data or 'new_password' not in data:
            return jsonify({"error": "Current and new passwords are required"}), 400

        # Change password
        success, error = auth_service.change_password(
            user_id=user['user_id'],
            current_password=data['current_password'],
            new_password=data['new_password']
        )

        if not success:
            return jsonify({"error": error}), 400

        return jsonify({
            "success": True,
            "message": "Password changed successfully"
        }), 200

    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        return jsonify({"error": "Failed to change password"}), 500


@bp.route('/verify-email', methods=['POST'])
def verify_email():
    """
    Verify email with token

    Request Body:
        {
            "token": "verification_token_string"
        }

    Returns:
        200: Email verified successfully
        400: Invalid token
        500: Server error

    Example:
        POST /api/auth/verify-email
        {
            "token": "verification_token_here"
        }
    """
    try:
        data = request.get_json()

        if not data or 'token' not in data:
            return jsonify({"error": "Verification token is required"}), 400

        # Verify email
        success, error = auth_service.verify_email(data['token'])

        if not success:
            return jsonify({"error": error}), 400

        return jsonify({
            "success": True,
            "message": "Email verified successfully. You can now login."
        }), 200

    except Exception as e:
        logger.error(f"Error verifying email: {str(e)}")
        return jsonify({"error": "Failed to verify email"}), 500


@bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    """
    Get current user information

    Headers:
        Authorization: Bearer <access_token>

    Returns:
        200: User information
        401: Unauthorized
        500: Server error

    Example:
        GET /api/auth/me
    """
    try:
        # Get user from request context
        user = g.get('user')
        if not user:
            return jsonify({"error": "User not found in context"}), 401

        # Get full user data from database
        from app.config import get_supabase_client
        supabase = get_supabase_client()

        result = supabase.table('users').select(
            'id', 'email', 'name', 'role', 'phone', 'team_id',
            'is_active', 'is_verified', 'created_at', 'last_login',
            'settings'
        ).eq('id', user['user_id']).execute()

        if not result.data:
            return jsonify({"error": "User not found"}), 404

        user_data = result.data[0]

        # Get permissions for role
        permissions = auth_service.get_user_permissions(user_data['role'])

        return jsonify({
            "success": True,
            "user": user_data,
            "permissions": permissions
        }), 200

    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        return jsonify({"error": "Failed to get user information"}), 500


@bp.route('/validate', methods=['POST'])
def validate_token():
    """
    Validate JWT token

    Request Body:
        {
            "token": "jwt_token_string"
        }

    Returns:
        200: Token is valid
        400: Invalid token
        500: Server error

    Example:
        POST /api/auth/validate
        {
            "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
        }
    """
    try:
        data = request.get_json()

        if not data or 'token' not in data:
            return jsonify({"error": "Token is required"}), 400

        # Validate token
        payload = auth_service.validate_token(data['token'])

        if not payload:
            return jsonify({
                "success": False,
                "valid": False,
                "error": "Invalid or expired token"
            }), 400

        return jsonify({
            "success": True,
            "valid": True,
            "payload": {
                "user_id": payload.get('user_id'),
                "email": payload.get('email'),
                "role": payload.get('role'),
                "expires_at": payload.get('exp')
            }
        }), 200

    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        return jsonify({"error": "Failed to validate token"}), 500


@bp.route('/permissions/<permission>', methods=['GET'])
@require_auth
def check_permission(permission: str):
    """
    Check if current user has specific permission

    Headers:
        Authorization: Bearer <access_token>

    Path Parameters:
        permission: Permission string (e.g., "leads:create")

    Returns:
        200: Permission check result
        401: Unauthorized
        500: Server error

    Example:
        GET /api/auth/permissions/leads:create
    """
    try:
        # Get user from request context
        user = g.get('user')
        if not user:
            return jsonify({"error": "User not found in context"}), 401

        # Check permission
        has_permission = auth_service.has_permission(user['role'], permission)

        return jsonify({
            "success": True,
            "permission": permission,
            "has_permission": has_permission,
            "user_role": user['role']
        }), 200

    except Exception as e:
        logger.error(f"Error checking permission: {str(e)}")
        return jsonify({"error": "Failed to check permission"}), 500


# Health check endpoint
@bp.route('/health', methods=['GET'])
def health_check():
    """
    Check auth service health

    Returns:
        200: Service is healthy
    """
    return jsonify({
        "success": True,
        "service": "auth",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }), 200


# Error handlers
@bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Auth endpoint not found"}), 404


@bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error in auth API: {error}")
    return jsonify({"error": "Internal server error"}), 500