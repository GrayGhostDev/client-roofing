"""
Authentication utilities for Streamlit dashboard
"""

import streamlit as st
from typing import Optional


def require_auth() -> bool:
    """
    Require authentication for page access.

    For now, this is a placeholder that allows access.
    In production, integrate with your backend authentication system.

    Returns:
        bool: True if authenticated, redirects if not
    """
    # Check if user is logged in
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = True  # Auto-authenticate for development

    if not st.session_state.authenticated:
        st.error("⛔ Authentication required")
        st.info("Please log in to access this page")
        st.stop()

    return True


def login(username: str, password: str) -> bool:
    """
    Authenticate user credentials.

    Args:
        username: User's username
        password: User's password

    Returns:
        bool: True if authenticated successfully
    """
    # TODO: Integrate with backend /api/auth/login endpoint
    # For now, accept any credentials in development
    st.session_state.authenticated = True
    st.session_state.username = username
    return True


def logout():
    """Log out the current user."""
    st.session_state.authenticated = False
    if 'username' in st.session_state:
        del st.session_state.username


def get_current_user() -> Optional[str]:
    """
    Get the currently authenticated user.

    Returns:
        Optional[str]: Username if authenticated, None otherwise
    """
    return st.session_state.get('username', None)


def is_authenticated() -> bool:
    """
    Check if user is authenticated.

    Returns:
        bool: True if authenticated
    """
    return st.session_state.get('authenticated', False)
