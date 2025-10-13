"""
Database Session Management for iSwitch Roofs CRM
Version: 2.0.0
Date: 2025-10-10

Enhanced database connectivity using centralized utilities.
Provides backwards compatibility for existing route imports.
"""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session, sessionmaker

# Import enhanced database utilities
from app.utils.database import (
    get_database_engine,
    get_db_session as get_enhanced_db_session,
    DatabaseSession,
    check_database_health,
    retry_on_db_error,
    close_database_connections
)

# Import the shared Base
from app.models.base import Base

# Create SQLAlchemy engine with enhanced connection pooling and retry logic
# This uses the centralized get_database_engine() which includes:
# - Connection pooling (10 base + 20 overflow)
# - Exponential backoff retry logic (3 attempts)
# - Pool pre-ping for connection health
# - Automatic connection recycling
# - Event listeners for connection lifecycle
engine = get_database_engine(max_retries=3, retry_delay=1.0)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    Backwards compatible with existing route imports.

    Yields:
        Session: SQLAlchemy database session

    Usage in routes:
        from app.database import get_db

        @bp.route("/")
        def my_route():
            db = next(get_db())
            try:
                # Use db
                pass
            finally:
                db.close()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """
    Context manager for database session.
    Backwards compatible with existing code.

    Yields:
        Session: SQLAlchemy database session

    Usage:
        from app.database import get_db_session

        with get_db_session() as db:
            # Use db
            db.commit()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    Creates all tables defined in SQLAlchemy models.

    Usage:
        from app.database import init_db
        init_db()
    """
    # Import all models here to ensure they are registered with Base
    # This is required for create_all() to work properly
    from app.models import (
        lead_sqlalchemy,
        customer_sqlalchemy,
        project_sqlalchemy,
        interaction_sqlalchemy,
        appointment_sqlalchemy,
        notification_sqlalchemy,
        partnership_sqlalchemy,
        review_sqlalchemy,
        team_sqlalchemy,
        alert_sqlalchemy,
        analytics_sqlalchemy,
        conversation_sqlalchemy  # Week 10: Conversation AI models
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


def drop_all_tables():
    """
    Drop all database tables. Use with caution!
    Only use in development for database resets.

    Usage:
        from app.database import drop_all_tables
        drop_all_tables()
    """
    import os
    if os.getenv("FLASK_ENV") == "production":
        raise RuntimeError("Cannot drop tables in production environment!")

    Base.metadata.drop_all(bind=engine)
    print("⚠️ All database tables dropped")


def get_health():
    """
    Get database health status.
    Uses the enhanced health check from utils.

    Returns:
        dict: Health status with connection info

    Usage:
        from app.database import get_health
        status = get_health()
    """
    return check_database_health()


# Expose enhanced utilities for direct import
__all__ = [
    'get_db',
    'get_db_session',
    'init_db',
    'drop_all_tables',
    'get_health',
    'engine',
    'SessionLocal',
    'Base',
    # Enhanced utilities
    'get_database_engine',
    'get_enhanced_db_session',
    'DatabaseSession',
    'check_database_health',
    'retry_on_db_error',
    'close_database_connections'
]
