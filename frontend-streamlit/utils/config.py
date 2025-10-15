"""
Configuration utilities for iSwitch Roofs CRM Frontend
Handles API configuration, timeouts, and environment settings
"""

import os
import streamlit as st
from typing import Optional
from urllib.parse import urlparse, urlunparse


class APIConfig:
    """API configuration constants"""
    HEALTH_CHECK_TIMEOUT = 5
    READ_TIMEOUT = 30
    WRITE_TIMEOUT = 60
    UPLOAD_TIMEOUT = 300

    # Retry configuration
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 1
    RETRY_STATUS_CODES = [429, 500, 502, 503, 504]


def get_api_base_url() -> str:
    """
    Get API base URL from environment or secrets with validation

    Priority order:
    1. BACKEND_API_URL environment variable
    2. ML_API_BASE_URL environment variable
    3. api_base_url from st.secrets
    4. ml_api_base_url from st.secrets
    5. Fail with error (no default in production)

    Returns:
        str: Validated API base URL

    Raises:
        ValueError: If no API URL is configured
    """
    # Try environment variables first
    api_url = os.getenv('BACKEND_API_URL') or os.getenv('ML_API_BASE_URL')

    # Try Streamlit secrets if env vars not set
    if not api_url:
        try:
            api_url = st.secrets.get('api_base_url') or st.secrets.get('ml_api_base_url')
        except Exception:
            pass

    # In development, allow localhost fallback
    if not api_url:
        env = os.getenv('STREAMLIT_ENV', 'development')
        if env == 'development':
            st.warning("⚠️ Using localhost API - not configured for production")
            return 'http://localhost:8001'
        else:
            # Production must have API URL configured
            st.error("""
                ❌ **API URL Not Configured**

                Please set one of the following:
                - Environment variable: `BACKEND_API_URL`
                - Streamlit secret: `api_base_url`

                Contact your system administrator.
            """)
            st.stop()

    # Clean and validate URL
    api_url = api_url.rstrip('/')

    # Validate URL format
    try:
        parsed = urlparse(api_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid API URL format: {api_url}")
    except Exception as e:
        st.error(f"❌ Invalid API URL: {str(e)}")
        st.stop()

    return api_url


def get_health_check_url(base_url: str) -> str:
    """
    Construct health check URL from base API URL

    Properly handles various base URL formats:
    - http://localhost:8001/api -> http://localhost:8001/health
    - http://api.example.com/api/v1 -> http://api.example.com/health
    - http://api.example.com -> http://api.example.com/health

    Args:
        base_url: Base API URL

    Returns:
        str: Health check endpoint URL
    """
    try:
        parsed = urlparse(base_url)

        # Construct health check URL at root
        health_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            '/health',
            '', '', ''
        ))

        return health_url
    except Exception as e:
        # Fallback to simple replacement if parsing fails
        return base_url.replace('/api', '').rstrip('/') + '/health'


def get_environment() -> str:
    """
    Get current environment (development, staging, production)

    Returns:
        str: Environment name
    """
    return os.getenv('STREAMLIT_ENV', 'development')


def is_production() -> bool:
    """Check if running in production environment"""
    return get_environment() == 'production'


def get_pusher_config() -> dict:
    """
    Get Pusher configuration from secrets

    Returns:
        dict: Pusher configuration or None if not configured
    """
    try:
        return {
            'app_id': st.secrets.get('pusher_app_id'),
            'key': st.secrets.get('pusher_key'),
            'secret': st.secrets.get('pusher_secret'),
            'cluster': st.secrets.get('pusher_cluster', 'us2'),
            'ssl': st.secrets.get('pusher_ssl', True)
        }
    except Exception:
        return None
