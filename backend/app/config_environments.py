"""
Environment-Specific Configuration Classes
Supports development, staging, and production environments
"""

import os
from typing import Optional


class BaseConfig:
    """Base configuration shared across all environments"""

    # Application
    APP_NAME = "iSwitch Roofs CRM"
    VERSION = "1.0.0"

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY")
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = False

    # Database
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600"))
    JWT_ALGORITHM = "HS256"

    # API
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8001"))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

    # Pusher (Real-time)
    PUSHER_APP_ID = os.getenv("PUSHER_APP_ID")
    PUSHER_KEY = os.getenv("PUSHER_KEY")
    PUSHER_SECRET = os.getenv("PUSHER_SECRET")
    PUSHER_CLUSTER = os.getenv("PUSHER_CLUSTER", "us2")

    # SendGrid (Email)
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    FROM_EMAIL = os.getenv("FROM_EMAIL")

    # Twilio (SMS)
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

    # CallRail (Call Tracking)
    CALLRAIL_API_KEY = os.getenv("CALLRAIL_API_KEY")
    CALLRAIL_ACCOUNT_ID = os.getenv("CALLRAIL_ACCOUNT_ID")
    CALLRAIL_COMPANY_ID = os.getenv("CALLRAIL_COMPANY_ID")
    CALLRAIL_TRACKING_ID = os.getenv("CALLRAIL_TRACKING_ID")

    # Sentry (Error Tracking)
    SENTRY_DSN = os.getenv("SENTRY_DSN")
    SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "development")
    SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))

    # Redis (Caching)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # File Upload
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "/tmp/uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx"}

    # Business Configuration
    COMPANY_NAME = os.getenv("COMPANY_NAME", "iSwitch Roofs")
    COMPANY_PHONE = os.getenv("COMPANY_PHONE", "+1234567890")
    COMPANY_EMAIL = os.getenv("COMPANY_EMAIL", "info@iswitchroofs.com")
    COMPANY_ADDRESS = os.getenv("COMPANY_ADDRESS", "123 Main St, Detroit, MI 48201")

    # Feature Flags
    ENABLE_AUTOMATED_FOLLOW_UP = os.getenv("ENABLE_AUTOMATED_FOLLOW_UP", "true").lower() == "true"
    ENABLE_SMS_NOTIFICATIONS = os.getenv("ENABLE_SMS_NOTIFICATIONS", "true").lower() == "true"
    ENABLE_EMAIL_CAMPAIGNS = os.getenv("ENABLE_EMAIL_CAMPAIGNS", "true").lower() == "true"
    ENABLE_LEAD_SCORING = os.getenv("ENABLE_LEAD_SCORING", "true").lower() == "true"

    # Lead Scoring Thresholds
    HOT_LEAD_THRESHOLD = int(os.getenv("HOT_LEAD_THRESHOLD", "80"))
    WARM_LEAD_THRESHOLD = int(os.getenv("WARM_LEAD_THRESHOLD", "60"))
    COOL_LEAD_THRESHOLD = int(os.getenv("COOL_LEAD_THRESHOLD", "40"))


class DevelopmentConfig(BaseConfig):
    """Development environment configuration"""

    DEBUG = True
    TESTING = False

    # Logging
    LOG_LEVEL = "DEBUG"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # CORS - Allow all origins in development
    CORS_ORIGINS = ["*"]

    # Sentry
    SENTRY_ENVIRONMENT = "development"
    SENTRY_TRACES_SAMPLE_RATE = 1.0  # 100% in development

    # Database
    SQLALCHEMY_ECHO = True  # Log SQL queries

    # Cache
    CACHE_TYPE = "simple"  # In-memory cache for development

    # Session
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


class StagingConfig(BaseConfig):
    """Staging environment configuration"""

    DEBUG = False
    TESTING = False

    # Logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Sentry
    SENTRY_ENVIRONMENT = "staging"
    SENTRY_TRACES_SAMPLE_RATE = 0.5  # 50% in staging

    # Database
    SQLALCHEMY_ECHO = False

    # Cache
    CACHE_TYPE = "redis"
    CACHE_REDIS_URL = os.getenv("REDIS_URL")
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes

    # Session
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = os.getenv("REDIS_URL")


class ProductionConfig(BaseConfig):
    """Production environment configuration"""

    DEBUG = False
    TESTING = False

    # Logging
    LOG_LEVEL = "WARNING"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d"

    # Sentry
    SENTRY_ENVIRONMENT = "production"
    SENTRY_TRACES_SAMPLE_RATE = 0.1  # 10% in production

    # Database
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_RECYCLE = 3600
    SQLALCHEMY_MAX_OVERFLOW = 20

    # Cache
    CACHE_TYPE = "redis"
    CACHE_REDIS_URL = os.getenv("REDIS_URL")
    CACHE_DEFAULT_TIMEOUT = 600  # 10 minutes

    # Session
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Strict"  # Strict in production
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = os.getenv("REDIS_URL")
    RATELIMIT_DEFAULT = "100 per hour"

    # Security Headers
    SECURITY_HEADERS = {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    }


class TestingConfig(BaseConfig):
    """Testing environment configuration"""

    DEBUG = True
    TESTING = True

    # Use in-memory database for testing
    DATABASE_URL = "sqlite:///:memory:"

    # Disable external services in tests
    PUSHER_APP_ID = "test-app-id"
    SENDGRID_API_KEY = "test-sendgrid-key"
    TWILIO_ACCOUNT_SID = "test-twilio-sid"

    # Fast hashing for tests
    BCRYPT_LOG_ROUNDS = 4

    # Disable CSRF for API tests
    WTF_CSRF_ENABLED = False

    # Logging
    LOG_LEVEL = "ERROR"  # Only errors in tests


# Configuration dictionary
config_by_name = {
    "development": DevelopmentConfig,
    "staging": StagingConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config(environment: Optional[str] = None):
    """
    Get configuration class for the specified environment

    Args:
        environment: Environment name (development, staging, production, testing)
                    If None, reads from FLASK_ENV environment variable

    Returns:
        Configuration class for the environment
    """
    if environment is None:
        environment = os.getenv("FLASK_ENV", "development")

    config_class = config_by_name.get(environment, DevelopmentConfig)

    return config_class
