"""
iSwitch Roofs CRM - Configuration Management
Version: 1.0.0
Date: 2025-10-01
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)


class Config:
    """Base configuration class."""

    # Flask configuration
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError(
            "Missing SECRET_KEY environment variable. Set it in the project's .env file."
        )
    DEBUG = False
    TESTING = False

    # Supabase configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

    # Database configuration
    DATABASE_URL = os.getenv("DATABASE_URL")

    # JWT configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600)))

    # API configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))

    # CORS configuration
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8501").split(
        ","
    )

    # Sentry configuration
    SENTRY_DSN = os.getenv("SENTRY_DSN")
    SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "development")

    # Email configuration (SendGrid)
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@iswitchroofs.com")

    # SMS configuration (Twilio)
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

    # Google Analytics
    GA_TRACKING_ID = os.getenv("GA_TRACKING_ID")
    GA4_MEASUREMENT_ID = os.getenv("GA4_MEASUREMENT_ID")

    # Cloudflare configuration
    CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
    CLOUDFLARE_ZONE_ID = os.getenv("CLOUDFLARE_ZONE_ID")

    # UptimeRobot configuration
    UPTIMEROBOT_API_KEY = os.getenv("UPTIMEROBOT_API_KEY")

    # Pusher configuration (Real-time)
    PUSHER_APP_ID = os.getenv("PUSHER_APP_ID")
    PUSHER_KEY = os.getenv("PUSHER_KEY")
    PUSHER_SECRET = os.getenv("PUSHER_SECRET")
    PUSHER_CLUSTER = os.getenv("PUSHER_CLUSTER", "us2")

    # AccuLynx CRM Integration
    ACCULYNX_API_KEY = os.getenv("ACCULYNX_API_KEY")
    ACCULYNX_API_URL = os.getenv("ACCULYNX_API_URL", "https://api.acculynx.com/v1")

    # CallRail configuration
    CALLRAIL_API_KEY = os.getenv("CALLRAIL_API_KEY")
    CALLRAIL_ACCOUNT_ID = os.getenv("CALLRAIL_ACCOUNT_ID")

    # BirdEye configuration
    BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")
    BIRDEYE_BUSINESS_ID = os.getenv("BIRDEYE_BUSINESS_ID")

    # Google Local Services Ads
    GOOGLE_LSA_API_KEY = os.getenv("GOOGLE_LSA_API_KEY")

    # Redis configuration (if using caching)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Feature flags
    ENABLE_AUTOMATED_FOLLOW_UP = os.getenv("ENABLE_AUTOMATED_FOLLOW_UP", "true").lower() == "true"
    ENABLE_SMS_NOTIFICATIONS = os.getenv("ENABLE_SMS_NOTIFICATIONS", "true").lower() == "true"
    ENABLE_EMAIL_CAMPAIGNS = os.getenv("ENABLE_EMAIL_CAMPAIGNS", "true").lower() == "true"
    ENABLE_LEAD_SCORING = os.getenv("ENABLE_LEAD_SCORING", "true").lower() == "true"

    # Business configuration
    COMPANY_NAME = os.getenv("COMPANY_NAME", "iSwitch Roofs")
    COMPANY_PHONE = os.getenv("COMPANY_PHONE")
    COMPANY_EMAIL = os.getenv("COMPANY_EMAIL", "info@iswitchroofs.com")
    COMPANY_ADDRESS = os.getenv("COMPANY_ADDRESS")

    # Lead scoring thresholds
    HOT_LEAD_THRESHOLD = int(os.getenv("HOT_LEAD_THRESHOLD", 80))
    WARM_LEAD_THRESHOLD = int(os.getenv("WARM_LEAD_THRESHOLD", 60))
    COOL_LEAD_THRESHOLD = int(os.getenv("COOL_LEAD_THRESHOLD", 40))

    # Response time targets (in seconds)
    TARGET_RESPONSE_TIME = int(os.getenv("TARGET_RESPONSE_TIME", 120))
    EMERGENCY_RESPONSE_TIME = int(os.getenv("EMERGENCY_RESPONSE_TIME", 300))

    # Business hours
    BUSINESS_HOURS_START = os.getenv("BUSINESS_HOURS_START", "08:00")
    BUSINESS_HOURS_END = os.getenv("BUSINESS_HOURS_END", "18:00")
    BUSINESS_TIMEZONE = os.getenv("BUSINESS_TIMEZONE", "America/Detroit")

    # File upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
    UPLOAD_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx"}


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False

    # In production, enforce HTTPS
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Production-specific settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)


class TestingConfig(Config):
    """Testing configuration."""

    DEBUG = True
    TESTING = True

    # Use in-memory database for testing
    DATABASE_URL = "postgresql://test:test@localhost:5432/test_db"

    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False

    # Use faster password hashing for tests
    BCRYPT_LOG_ROUNDS = 4


# Configuration dictionary
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config(config_name="development"):
    """
    Get configuration object by name.

    Args:
        config_name (str): Configuration name (development, production, testing)

    Returns:
        Config: Configuration object
    """
    return config_by_name.get(config_name, DevelopmentConfig)


def get_supabase_client():
    """
    Get Supabase client instance.

    Returns:
        Supabase: Configured Supabase client
    """
    from supabase import create_client

    config = get_config()
    url = config.SUPABASE_URL
    key = config.SUPABASE_KEY

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be configured")

    return create_client(url, key)


def get_pusher_client():
    """
    Get Pusher client instance.

    Returns:
        Pusher: Configured Pusher client
    """
    import pusher

    config = get_config()

    if not all([config.PUSHER_APP_ID, config.PUSHER_KEY, config.PUSHER_SECRET]):
        raise ValueError("PUSHER_APP_ID, PUSHER_KEY, and PUSHER_SECRET must be configured")

    return pusher.Pusher(
        app_id=config.PUSHER_APP_ID,
        key=config.PUSHER_KEY,
        secret=config.PUSHER_SECRET,
        cluster=config.PUSHER_CLUSTER,
        ssl=True,
    )


def get_sendgrid_client():
    """
    Get SendGrid client instance.

    Returns:
        SendGridAPIClient: Configured SendGrid client
    """
    from sendgrid import SendGridAPIClient

    config = get_config()

    if not config.SENDGRID_API_KEY:
        raise ValueError("SENDGRID_API_KEY must be configured")

    return SendGridAPIClient(config.SENDGRID_API_KEY)


def get_twilio_client():
    """
    Get Twilio client instance.

    Returns:
        Client: Configured Twilio client
    """
    from twilio.rest import Client

    config = get_config()

    if not all([config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN]):
        raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be configured")

    return Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)


def get_redis_client():
    """
    Get Redis client instance.

    Returns:
        Redis: Configured Redis client
    """
    from urllib.parse import urlparse

    import redis

    config = get_config()

    if not config.REDIS_URL:
        raise ValueError("REDIS_URL must be configured")

    # Parse Redis URL
    url = urlparse(config.REDIS_URL)

    return redis.Redis(
        host=url.hostname or "localhost",
        port=url.port or 6379,
        db=int(url.path.lstrip("/")) if url.path else 0,
        password=url.password,
        decode_responses=True,
    )
