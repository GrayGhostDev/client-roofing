"""
Database Connection Utilities for iSwitch Roofs CRM
Version: 2.0.0
Date: 2025-10-09

Enhanced database connectivity with:
- Connection pooling
- Retry logic with exponential backoff
- Health monitoring
- Graceful degradation
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Optional

from sqlalchemy import create_engine, event, pool, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from supabase import Client, create_client

from app.config import get_config

logger = logging.getLogger(__name__)

# Global connection pool
_db_engine = None
_session_factory = None
_supabase_client = None


class DatabaseConnectionError(Exception):
    """Custom exception for database connection failures"""
    pass


def get_database_url_with_fallback():
    """
    Get database URL with intelligent fallback

    Priority:
    1. Primary DATABASE_URL (Supabase or remote PostgreSQL)
    2. Local PostgreSQL (LOCAL_DATABASE_URL fallback)
    3. SQLite in-memory (emergency demo mode)

    Returns:
        str: Database connection URL
    """
    import os

    config = get_config()

    # Try primary DATABASE_URL first (Supabase or configured remote)
    if config.DATABASE_URL:
        try:
            logger.info("Testing primary DATABASE_URL connection...")
            test_engine = create_engine(
                config.DATABASE_URL,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 5}
            )
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.info("✅ Primary database connection successful")
            test_engine.dispose()
            return config.DATABASE_URL

        except Exception as e:
            logger.warning(f"⚠️ Primary database connection failed: {str(e)[:100]}")

    # Fallback to local PostgreSQL
    local_url = os.getenv("LOCAL_DATABASE_URL")
    if local_url:
        try:
            logger.info("Attempting local PostgreSQL fallback...")
            test_engine = create_engine(
                local_url,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 3}
            )
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.info("✅ Local PostgreSQL connection successful (fallback mode)")
            test_engine.dispose()
            return local_url

        except Exception as e:
            logger.warning(f"⚠️ Local PostgreSQL connection failed: {str(e)[:100]}")

    # Emergency: SQLite in-memory (demo mode only)
    logger.error("❌ No database available - using SQLite in-memory (DEMO MODE ONLY)")
    logger.error("⚠️ Data will NOT persist! Configure DATABASE_URL for production use.")
    return "sqlite:///:memory:"


def get_database_engine(max_retries: int = 3, retry_delay: float = 1.0):
    """
    Get or create database engine with connection pooling

    Args:
        max_retries: Maximum number of connection attempts
        retry_delay: Initial delay between retries (exponential backoff)

    Returns:
        SQLAlchemy engine instance

    Raises:
        DatabaseConnectionError: If connection fails after all retries
    """
    global _db_engine

    if _db_engine is not None:
        return _db_engine

    # Get database URL with intelligent fallback
    database_url = get_database_url_with_fallback()

    # Determine if using SQLite (special handling needed)
    is_sqlite = database_url.startswith("sqlite:///")

    attempt = 0
    last_error = None

    while attempt < max_retries:
        try:
            logger.info(f"Attempting database connection (attempt {attempt + 1}/{max_retries})")

            # SQLite-specific configuration (in-memory database)
            if is_sqlite:
                _db_engine = create_engine(
                    database_url,
                    connect_args={"check_same_thread": False},  # Allow multi-threading
                    poolclass=pool.StaticPool,  # Use single connection for SQLite
                    echo=False  # Don't log SQL for in-memory DB
                )
                logger.warning("⚠️ Using SQLite in-memory database (demo mode)")
            else:
                # PostgreSQL-specific configuration
                config = get_config()
                _db_engine = create_engine(
                    database_url,
                    poolclass=pool.QueuePool,
                    pool_size=10,  # Maximum 10 concurrent connections
                    max_overflow=20,  # Allow 20 additional connections in overflow
                    pool_timeout=30,  # Wait up to 30 seconds for a connection
                    pool_recycle=3600,  # Recycle connections after 1 hour
                    pool_pre_ping=True,  # Verify connections before using
                    echo=config.DEBUG,  # Log SQL queries in debug mode
                    connect_args={
                        "connect_timeout": 10,  # 10 second connection timeout
                        "options": "-c statement_timeout=30000"  # 30s query timeout
                    }
                )

            # Test connection
            with _db_engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()

            logger.info("✅ Database connection established successfully")

            # Add connection event listeners
            _add_connection_listeners(_db_engine)

            return _db_engine

        except OperationalError as e:
            last_error = e
            attempt += 1

            if attempt < max_retries:
                delay = retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                logger.warning(
                    f"Database connection failed: {str(e)}. "
                    f"Retrying in {delay:.1f} seconds..."
                )
                time.sleep(delay)
            else:
                logger.error(f"❌ Database connection failed after {max_retries} attempts")
                raise DatabaseConnectionError(
                    f"Failed to connect to database after {max_retries} attempts: {str(last_error)}"
                )

        except Exception as e:
            logger.error(f"❌ Unexpected database error: {str(e)}")
            raise DatabaseConnectionError(f"Database connection error: {str(e)}")

    raise DatabaseConnectionError("Failed to establish database connection")


def _add_connection_listeners(engine):
    """Add event listeners for connection lifecycle"""

    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Log new connections"""
        logger.debug("New database connection established")

    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        """Log connection checkout from pool"""
        logger.debug("Connection checked out from pool")

    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_conn, connection_record):
        """Log connection return to pool"""
        logger.debug("Connection returned to pool")


def get_session_factory():
    """
    Get or create SQLAlchemy session factory

    Returns:
        sessionmaker instance
    """
    global _session_factory

    if _session_factory is None:
        engine = get_database_engine()
        _session_factory = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )

    return _session_factory


def get_db_session() -> Session:
    """
    Get a new database session

    Returns:
        SQLAlchemy Session instance

    Usage:
        with get_db_session() as session:
            # Use session
            pass
    """
    SessionFactory = get_session_factory()
    return SessionFactory()


def get_supabase_client_with_retry(max_retries: int = 3) -> Client:
    """
    Get or create Supabase client with retry logic

    Args:
        max_retries: Maximum number of connection attempts

    Returns:
        Supabase Client instance

    Raises:
        DatabaseConnectionError: If connection fails
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    config = get_config()

    if not config.SUPABASE_URL or not config.SUPABASE_KEY:
        raise DatabaseConnectionError("SUPABASE_URL and SUPABASE_KEY must be configured")

    attempt = 0
    last_error = None

    while attempt < max_retries:
        try:
            logger.info(f"Connecting to Supabase (attempt {attempt + 1}/{max_retries})")

            _supabase_client = create_client(
                config.SUPABASE_URL,
                config.SUPABASE_KEY
            )

            # Test connection with a simple query
            result = _supabase_client.table("leads").select("id").limit(1).execute()

            logger.info("✅ Supabase connection established successfully")
            return _supabase_client

        except Exception as e:
            last_error = e
            attempt += 1

            if attempt < max_retries:
                delay = 1.0 * (2 ** (attempt - 1))
                logger.warning(
                    f"Supabase connection failed: {str(e)}. "
                    f"Retrying in {delay:.1f} seconds..."
                )
                time.sleep(delay)
            else:
                logger.error(f"❌ Supabase connection failed after {max_retries} attempts")
                raise DatabaseConnectionError(
                    f"Failed to connect to Supabase: {str(last_error)}"
                )

    raise DatabaseConnectionError("Failed to establish Supabase connection")


def retry_on_db_error(max_retries: int = 3, retry_delay: float = 0.5):
    """
    Decorator to retry database operations on failure

    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries (exponential backoff)

    Usage:
        @retry_on_db_error(max_retries=3)
        def my_database_function():
            # Database operations
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            last_error = None

            while attempt < max_retries:
                try:
                    return func(*args, **kwargs)

                except (OperationalError, SQLAlchemyError) as e:
                    last_error = e
                    attempt += 1

                    if attempt < max_retries:
                        delay = retry_delay * (2 ** (attempt - 1))
                        logger.warning(
                            f"Database operation failed: {func.__name__}. "
                            f"Retrying in {delay:.1f} seconds... (attempt {attempt}/{max_retries})"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"❌ Database operation {func.__name__} failed after {max_retries} attempts"
                        )
                        raise

            raise last_error

        return wrapper
    return decorator


def check_database_health() -> dict:
    """
    Check database health and return status

    Returns:
        Dictionary with health status:
        {
            "healthy": bool,
            "database": {"connected": bool, "latency_ms": float},
            "supabase": {"connected": bool, "latency_ms": float},
            "pool": {"size": int, "checked_out": int, "overflow": int}
        }
    """
    health = {
        "healthy": False,
        "database": {"connected": False, "latency_ms": None},
        "supabase": {"connected": False, "latency_ms": None},
        "pool": {"size": 0, "checked_out": 0, "overflow": 0}
    }

    # Check SQLAlchemy connection
    try:
        start_time = time.time()
        engine = get_database_engine()

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        latency = (time.time() - start_time) * 1000  # Convert to milliseconds
        health["database"] = {"connected": True, "latency_ms": round(latency, 2)}

        # Get pool stats
        pool_status = engine.pool.status()
        health["pool"] = {
            "size": engine.pool.size(),
            "checked_out": engine.pool.checkedout(),
            "overflow": engine.pool.overflow()
        }

    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health["database"] = {"connected": False, "error": str(e)}

    # Check Supabase connection
    try:
        start_time = time.time()
        client = get_supabase_client_with_retry(max_retries=1)

        # Simple query to test connection
        client.table("leads").select("id").limit(1).execute()

        latency = (time.time() - start_time) * 1000
        health["supabase"] = {"connected": True, "latency_ms": round(latency, 2)}

    except Exception as e:
        logger.error(f"Supabase health check failed: {str(e)}")
        health["supabase"] = {"connected": False, "error": str(e)}

    # Overall health is true if at least one connection works
    health["healthy"] = (
        health["database"]["connected"] or
        health["supabase"]["connected"]
    )

    return health


def close_database_connections():
    """
    Close all database connections gracefully

    Call this during application shutdown
    """
    global _db_engine, _session_factory, _supabase_client

    if _db_engine:
        logger.info("Closing database connections...")
        _db_engine.dispose()
        _db_engine = None

    _session_factory = None
    _supabase_client = None

    logger.info("✅ Database connections closed")


# Context manager for database sessions
class DatabaseSession:
    """
    Context manager for database sessions with automatic rollback

    Usage:
        with DatabaseSession() as session:
            # Use session
            session.add(obj)
            session.commit()
    """

    def __init__(self):
        self.session = None

    def __enter__(self) -> Session:
        self.session = get_db_session()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f"Database session error: {exc_val}")
            self.session.rollback()

        self.session.close()
        return False  # Don't suppress exceptions
