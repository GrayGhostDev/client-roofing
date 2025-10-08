"""
Utility decorators for API routes
"""

from functools import wraps
from flask import request, jsonify
import logging

logger = logging.getLogger(__name__)


def require_api_key(f):
    """
    Decorator to require API key authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        # Add your API key validation logic here
        return f(*args, **kwargs)
    return decorated_function


def rate_limit(calls=100, period=60):
    """
    Basic rate limiting decorator
    
    Args:
        calls: Number of calls allowed
        period: Time period in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Add rate limiting logic here
            # For now, just pass through
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def log_request(f):
    """
    Decorator to log API requests
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"API Request: {request.method} {request.path}")
        return f(*args, **kwargs)
    return decorated_function


def validate_json(f):
    """
    Decorator to validate JSON payload exists
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        return f(*args, **kwargs)
    return decorated_function


def require_auth(f):
    """
    Decorator to require authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Add JWT validation logic here
        # For now, just pass through
        return f(*args, **kwargs)
    return decorated_function


def require_roles(*roles):
    """
    Decorator to require specific user roles
    
    Args:
        roles: Variable number of role names required
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Add role validation logic here
            # For now, just pass through
            return f(*args, **kwargs)
        return decorated_function
    return decorator
