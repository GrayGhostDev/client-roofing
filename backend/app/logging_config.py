"""
Structured Logging Configuration
Provides centralized logging setup with structured output
"""

import json
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict

from flask import Flask, has_request_context, request


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in JSON format for better parsing
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request context if available
        if has_request_context():
            log_data["request"] = {
                "method": request.method,
                "path": request.path,
                "remote_addr": request.remote_addr,
                "user_agent": request.user_agent.string if request.user_agent else None,
            }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        return json.dumps(log_data)


class ColoredConsoleFormatter(logging.Formatter):
    """
    Formatter that adds colors to console output for better readability
    """

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with colors

        Args:
            record: Log record to format

        Returns:
            Colored log string
        """
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Build log message
        log_message = f"{timestamp} [{record.levelname}] {record.name}: {record.getMessage()}"

        # Add request context if available
        if has_request_context():
            log_message += f" | {request.method} {request.path}"

        # Add exception info if present
        if record.exc_info:
            log_message += f"\n{self.formatException(record.exc_info)}"

        return log_message


def setup_logging(app: Flask) -> None:
    """
    Configure application logging with structured output

    Args:
        app: Flask application instance
    """
    # Determine log level
    log_level_str = app.config.get("LOG_LEVEL", "INFO")
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)

    # Get environment
    environment = app.config.get("SENTRY_ENVIRONMENT", "development")

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler with colors for development
    if environment == "development":
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(ColoredConsoleFormatter())
        root_logger.addHandler(console_handler)
    else:
        # JSON structured logging for production
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(console_handler)

    # File handler with rotation
    log_dir = Path(app.config.get("LOG_DIR", "logs"))
    log_dir.mkdir(exist_ok=True, parents=True)

    # Application logs
    app_log_file = log_dir / "application.log"
    file_handler = RotatingFileHandler(
        app_log_file, maxBytes=10 * 1024 * 1024, backupCount=10  # 10 MB
    )
    file_handler.setLevel(log_level)

    if environment == "development":
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
    else:
        file_handler.setFormatter(StructuredFormatter())

    root_logger.addHandler(file_handler)

    # Error logs (separate file for errors only)
    error_log_file = log_dir / "errors.log"
    error_handler = RotatingFileHandler(
        error_log_file, maxBytes=10 * 1024 * 1024, backupCount=10  # 10 MB
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(error_handler)

    # Set levels for noisy third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    app.logger.info(
        f"Logging configured: level={log_level_str}, environment={environment}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """
    Context manager for adding extra context to logs
    """

    def __init__(self, logger: logging.Logger, **context):
        """
        Initialize log context

        Args:
            logger: Logger instance
            **context: Additional context to add to logs
        """
        self.logger = logger
        self.context = context
        self.old_factory = None

    def __enter__(self):
        """Enter context"""
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.extra = self.context
            return record

        logging.setLogRecordFactory(record_factory)
        self.old_factory = old_factory
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context"""
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)


# Example usage functions
def log_api_call(endpoint: str, method: str, status_code: int, duration_ms: float):
    """
    Log an API call with structured data

    Args:
        endpoint: API endpoint
        method: HTTP method
        status_code: Response status code
        duration_ms: Request duration in milliseconds
    """
    logger = get_logger("api")
    logger.info(
        f"{method} {endpoint} - {status_code}",
        extra={
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration_ms": duration_ms,
        },
    )


def log_database_query(query: str, duration_ms: float, row_count: int):
    """
    Log a database query with performance metrics

    Args:
        query: SQL query (sanitized)
        duration_ms: Query duration in milliseconds
        row_count: Number of rows returned/affected
    """
    logger = get_logger("database")
    logger.debug(
        f"Query executed in {duration_ms:.2f}ms, {row_count} rows",
        extra={
            "query": query[:200],  # Truncate long queries
            "duration_ms": duration_ms,
            "row_count": row_count,
        },
    )


def log_external_service_call(
    service: str, operation: str, success: bool, duration_ms: float, error: str = None
):
    """
    Log an external service call

    Args:
        service: Service name (e.g., 'twilio', 'sendgrid')
        operation: Operation performed
        success: Whether the call succeeded
        duration_ms: Call duration in milliseconds
        error: Error message if failed
    """
    logger = get_logger("external_services")

    extra = {
        "service": service,
        "operation": operation,
        "success": success,
        "duration_ms": duration_ms,
    }

    if error:
        extra["error"] = error

    if success:
        logger.info(f"{service}.{operation} succeeded in {duration_ms:.2f}ms", extra=extra)
    else:
        logger.error(f"{service}.{operation} failed: {error}", extra=extra)


def log_business_event(event_type: str, entity_id: str, details: Dict[str, Any]):
    """
    Log a business event (e.g., lead created, appointment scheduled)

    Args:
        event_type: Type of event
        entity_id: ID of the entity involved
        details: Additional event details
    """
    logger = get_logger("business_events")
    logger.info(
        f"Business event: {event_type}",
        extra={
            "event_type": event_type,
            "entity_id": entity_id,
            "details": details,
        },
    )
