"""
Authentication Utilities
Version: 1.0.0

Authentication and authorization utilities for the API.
"""

from functools import wraps
from flask import request, jsonify, g
from typing import Optional, Dict, List
import logging

from app.services.auth_service import auth_service

logger = logging.getLogger(__name__)


def require_auth(f):
    """
    Decorator to require authentication for an endpoint.

    Checks for Bearer token in Authorization header and validates it.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({'error': 'Authentication required'}), 401

        # Extract token from "Bearer <token>"
        try:
            parts = auth_header.split()
            if parts[0].lower() != 'bearer' or len(parts) != 2:
                return jsonify({'error': 'Invalid authorization header format'}), 401

            token = parts[1]
        except Exception:
            return jsonify({'error': 'Invalid authorization header'}), 401

        # Validate token using auth service
        try:
            payload = auth_service.validate_token(token)

            if not payload:
                return jsonify({'error': 'Invalid or expired token'}), 401

            # Store user info in g for use in route
            g.user = payload
            g.user_id = payload['user_id']
            g.user_email = payload['email']
            g.user_role = payload['role']

            return f(*args, **kwargs)

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return jsonify({'error': 'Authentication failed'}), 401

    return decorated_function


def require_role(role):
    """
    Decorator to require a specific role for an endpoint.

    Args:
        role: Required role (admin, manager, user)
    """
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user_role = g.get('user_role', 'user')

            # Role hierarchy: admin > manager > user
            role_levels = {'user': 1, 'manager': 2, 'admin': 3}

            if role_levels.get(user_role, 0) < role_levels.get(role, 0):
                return jsonify({'error': 'Insufficient permissions'}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def generate_token(user_id: str, email: str, role: str = 'user',
                  expires_in: int = 3600) -> str:
    """
    Generate JWT token for a user.

    Args:
        user_id: User ID
        email: User email
        role: User role
        expires_in: Token expiry in seconds

    Returns:
        JWT token string
    """
    try:
        secret = os.environ.get('JWT_SECRET_KEY', 'test_secret')

        payload = {
            'user_id': user_id,
            'email': email,
            'role': role,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow()
        }

        token = jwt.encode(payload, secret, algorithm='HS256')

        return token

    except Exception as e:
        logger.error(f"Failed to generate token: {str(e)}")
        return None


def verify_token(token: str) -> Optional[Dict]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload or None if invalid
    """
    try:
        secret = os.environ.get('JWT_SECRET_KEY', 'test_secret')
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None

    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        return None

    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return None


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    try:
        import bcrypt
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except ImportError:
        # Fallback to simple hash for testing if bcrypt not available
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        password: Plain text password
        hashed: Hashed password

    Returns:
        True if password matches
    """
    try:
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except ImportError:
        # Fallback for testing
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest() == hashed