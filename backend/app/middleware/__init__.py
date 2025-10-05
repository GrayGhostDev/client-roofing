"""
iSwitch Roofs CRM - Middleware Package
Version: 1.0.0

Middleware for request/response processing.
"""

from .audit_middleware import (
    AuditMiddleware,
    audit_middleware,
    get_current_user,
    add_audit_fields,
    setup_audit_middleware
)

__all__ = [
    'AuditMiddleware',
    'audit_middleware',
    'get_current_user',
    'add_audit_fields',
    'setup_audit_middleware'
]