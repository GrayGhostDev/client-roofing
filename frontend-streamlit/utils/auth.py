"""
Authentication utilities for Streamlit dashboard
Wrapper around Supabase authentication for backward compatibility
"""

import streamlit as st
from typing import Optional, Dict, Any
from .supabase_auth import get_auth_client, require_auth as supabase_require_auth


def require_auth() -> bool:
    """
    Require authentication for page access.
    Redirects to login page if not authenticated.

    Returns:
        bool: True if authenticated, redirects if not
    """
    supabase_require_auth()
    return True


def login(email: str, password: str) -> bool:
    """
    Authenticate user credentials using Supabase.

    Args:
        email: User's email address
        password: User's password

    Returns:
        bool: True if authenticated successfully
    """
    auth = get_auth_client()
    result = auth.sign_in(email, password)

    # Handle case where result might be a string (error) instead of dict
    if isinstance(result, dict):
        return result.get('success', False)
    else:
        # If result is not a dict, authentication failed
        return False


def logout():
    """Log out the current user."""
    auth = get_auth_client()
    auth.sign_out()


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get the currently authenticated user.

    Returns:
        Optional[Dict]: User object if authenticated, None otherwise
    """
    try:
        auth = get_auth_client()
        user = auth.get_current_user()

        # Ensure we return None if not a valid user object
        if user and isinstance(user, dict):
            return user
        return None
    except Exception:
        return None


def is_authenticated() -> bool:
    """
    Check if user is authenticated.

    Returns:
        bool: True if authenticated
    """
    auth = get_auth_client()
    return auth.is_authenticated()


def get_user_email() -> Optional[str]:
    """
    Get the email of the currently authenticated user.

    Returns:
        Optional[str]: User email if authenticated, None otherwise
    """
    return st.session_state.get('user_email', None)


def get_user_metadata() -> Dict[str, Any]:
    """
    Get metadata for the currently authenticated user.

    Returns:
        Dict: User metadata (empty dict if not available)
    """
    try:
        auth = get_auth_client()
        metadata = auth.get_user_metadata()

        # Ensure we always return a dict
        if isinstance(metadata, dict):
            return metadata
        else:
            return {}
    except Exception:
        return {}
