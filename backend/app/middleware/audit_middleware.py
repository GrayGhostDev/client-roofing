"""
iSwitch Roofs CRM - Audit Middleware
Version: 1.0.0

Middleware for automatically tracking user actions in audit fields.
"""

from flask import g, request
from functools import wraps
from typing import Optional, Dict, Any
import jwt
import logging

logger = logging.getLogger(__name__)


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get the current user from the request context.

    This function extracts user information from JWT token or session.

    Returns:
        Dict: User information including id and email, or None if not authenticated
    """
    # Check if user is already set in Flask's g object
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user

    # Try to extract from JWT token in Authorization header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        try:
            token = auth_header.split(' ')[1]
            # This will be replaced with actual JWT decoding when auth is implemented
            # For now, return mock user for testing
            if token == "mock_token_for_testing":
                user = {
                    'id': 'test_user_id',
                    'email': 'test@iswitchroofs.com',
                    'name': 'Test User',
                    'role': 'admin'
                }
                g.current_user = user
                return user

            # Real JWT decoding (to be implemented)
            # payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            # user = {
            #     'id': payload.get('user_id'),
            #     'email': payload.get('email'),
            #     'name': payload.get('name'),
            #     'role': payload.get('role')
            # }
            # g.current_user = user
            # return user

        except Exception as e:
            logger.warning(f"Failed to decode JWT token: {e}")
            return None

    # Check session (if using session-based auth)
    # if 'user_id' in session:
    #     user = {
    #         'id': session['user_id'],
    #         'email': session.get('email'),
    #         'name': session.get('name'),
    #         'role': session.get('role')
    #     }
    #     g.current_user = user
    #     return user

    return None


def add_audit_fields(data: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
    """
    Add audit fields to data dictionary.

    Args:
        data: Dictionary containing request data
        is_update: Whether this is an update operation (vs create)

    Returns:
        Dict: Data with audit fields added
    """
    user = get_current_user()

    if user:
        if not is_update:
            # For create operations, set both created and updated fields
            data['created_by'] = user.get('id')
            data['created_by_email'] = user.get('email')
            data['updated_by'] = user.get('id')
            data['updated_by_email'] = user.get('email')
        else:
            # For update operations, only set updated fields
            data['updated_by'] = user.get('id')
            data['updated_by_email'] = user.get('email')

    return data


def audit_middleware(f):
    """
    Decorator to automatically add audit fields to request data.

    This decorator can be applied to route handlers to automatically
    inject audit fields into the request data.

    Usage:
        @app.route('/api/resource', methods=['POST'])
        @audit_middleware
        def create_resource():
            data = request.get_json()  # Will have audit fields
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Only process for methods that modify data
        if request.method in ['POST', 'PUT', 'PATCH']:
            # Get the current user
            user = get_current_user()

            # Store user in g for use in the request
            if user:
                g.current_user = user

                # If request has JSON data, add audit fields
                if request.is_json:
                    data = request.get_json()
                    if data:
                        is_update = request.method in ['PUT', 'PATCH']
                        # Add audit fields to the data
                        data = add_audit_fields(data, is_update=is_update)
                        # Store modified data in g for use in the route
                        g.audit_data = data

        return f(*args, **kwargs)

    return decorated_function


class AuditMiddleware:
    """
    Flask middleware class for automatic audit field tracking.

    This can be used as application-wide middleware.
    """

    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the middleware with a Flask app."""
        app.before_request(self.before_request)

    def before_request(self):
        """Process request before it reaches the route handler."""
        # Extract and store current user
        user = get_current_user()
        if user:
            g.current_user = user
            logger.debug(f"Request from user: {user.get('email')}")


def setup_audit_middleware(app):
    """
    Setup audit middleware for the Flask application.

    Args:
        app: Flask application instance
    """
    audit = AuditMiddleware()
    audit.init_app(app)
    logger.info("Audit middleware initialized")