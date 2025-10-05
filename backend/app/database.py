"""
Database Session Management for iSwitch Roofs CRM
Version: 1.0.0

SQLAlchemy session management with PostgreSQL connection.
"""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_config

# Get configuration
config = get_config()

# Create SQLAlchemy engine
engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=config.DEBUG,  # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import the shared Base
from app.models.base import Base


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.

    Yields:
        Session: SQLAlchemy database session
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

    Yields:
        Session: SQLAlchemy database session
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
    """Initialize database tables."""
    # Import all models here to ensure they are registered

    # Create all tables
    Base.metadata.create_all(bind=engine)


def drop_all_tables():
    """Drop all database tables. Use with caution!"""
    Base.metadata.drop_all(bind=engine)
