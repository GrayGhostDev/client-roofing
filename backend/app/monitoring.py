"""
Monitoring and Observability Module
Provides comprehensive monitoring, health checks, and observability features
"""

import logging
import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict

import psutil
from flask import Flask, jsonify, request

try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

logger = logging.getLogger(__name__)


class HealthCheckStatus:
    """Health check status enumeration"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class PerformanceMonitor:
    """
    Performance monitoring and metrics collection
    """

    def __init__(self):
        self.metrics = {
            "request_count": 0,
            "error_count": 0,
            "total_response_time": 0.0,
            "start_time": datetime.utcnow().isoformat(),
        }
        self.request_times = []
        self.endpoint_metrics = {}

    def record_request(self, endpoint: str, response_time: float, status_code: int):
        """Record a request metric"""
        self.metrics["request_count"] += 1
        self.metrics["total_response_time"] += response_time
        self.request_times.append(response_time)

        # Keep only last 1000 request times
        if len(self.request_times) > 1000:
            self.request_times.pop(0)

        # Track per-endpoint metrics
        if endpoint not in self.endpoint_metrics:
            self.endpoint_metrics[endpoint] = {
                "count": 0,
                "total_time": 0.0,
                "errors": 0,
            }

        self.endpoint_metrics[endpoint]["count"] += 1
        self.endpoint_metrics[endpoint]["total_time"] += response_time

        if status_code >= 400:
            self.metrics["error_count"] += 1
            self.endpoint_metrics[endpoint]["errors"] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        avg_response_time = 0.0
        if self.metrics["request_count"] > 0:
            avg_response_time = (
                self.metrics["total_response_time"] / self.metrics["request_count"]
            )

        # Calculate percentiles
        p50 = p95 = p99 = 0.0
        if self.request_times:
            sorted_times = sorted(self.request_times)
            count = len(sorted_times)
            p50 = sorted_times[int(count * 0.50)]
            p95 = sorted_times[int(count * 0.95)]
            p99 = sorted_times[int(count * 0.99)]

        return {
            "requests": {
                "total": self.metrics["request_count"],
                "errors": self.metrics["error_count"],
                "error_rate": (
                    self.metrics["error_count"] / self.metrics["request_count"]
                    if self.metrics["request_count"] > 0
                    else 0.0
                ),
            },
            "response_times": {
                "average": round(avg_response_time, 3),
                "p50": round(p50, 3),
                "p95": round(p95, 3),
                "p99": round(p99, 3),
            },
            "uptime_seconds": (
                datetime.utcnow()
                - datetime.fromisoformat(self.metrics["start_time"])
            ).total_seconds(),
        }

    def get_endpoint_metrics(self) -> Dict[str, Any]:
        """Get per-endpoint metrics"""
        result = {}
        for endpoint, metrics in self.endpoint_metrics.items():
            avg_time = 0.0
            if metrics["count"] > 0:
                avg_time = metrics["total_time"] / metrics["count"]

            result[endpoint] = {
                "requests": metrics["count"],
                "errors": metrics["errors"],
                "avg_response_time": round(avg_time, 3),
            }
        return result


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def init_sentry(app: Flask) -> None:
    """
    Initialize Sentry error tracking

    Args:
        app: Flask application instance
    """
    if not SENTRY_AVAILABLE:
        logger.warning("Sentry SDK not available. Error tracking disabled.")
        return

    sentry_dsn = app.config.get("SENTRY_DSN")
    if not sentry_dsn:
        logger.warning("SENTRY_DSN not configured. Error tracking disabled.")
        return

    environment = app.config.get("SENTRY_ENVIRONMENT", "development")

    # Configure Sentry logging integration
    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR  # Send errors as events
    )

    # Determine sample rate based on environment
    traces_sample_rate = 0.1 if environment == "production" else 1.0

    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[
            FlaskIntegration(),
            sentry_logging,
        ],
        traces_sample_rate=traces_sample_rate,
        environment=environment,
        release=app.config.get("APP_VERSION", "1.0.0"),
        send_default_pii=False,  # Don't send PII by default
        before_send=before_send_sentry,
    )

    logger.info(f"Sentry initialized for environment: {environment}")


def before_send_sentry(event, hint):
    """
    Filter and modify events before sending to Sentry

    Args:
        event: Sentry event
        hint: Additional context

    Returns:
        Modified event or None to drop the event
    """
    # Don't send health check failures
    if "request" in event and event["request"].get("url", "").endswith("/health"):
        return None

    # Add custom tags
    event.setdefault("tags", {})
    event["tags"]["service"] = "iswitch-roofs-crm"

    return event


def performance_tracking(f: Callable) -> Callable:
    """
    Decorator to track endpoint performance

    Args:
        f: Function to wrap

    Returns:
        Wrapped function with performance tracking
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()

        try:
            response = f(*args, **kwargs)
            status_code = getattr(response, "status_code", 200)
            return response
        except Exception as e:
            status_code = 500
            raise
        finally:
            response_time = time.time() - start_time
            endpoint = request.endpoint or "unknown"
            performance_monitor.record_request(endpoint, response_time, status_code)

            # Log slow requests
            if response_time > 1.0:
                logger.warning(
                    f"Slow request detected: {endpoint} took {response_time:.2f}s"
                )

    return decorated_function


def check_database_health(app: Flask) -> Dict[str, Any]:
    """
    Check database connectivity and health

    Args:
        app: Flask application instance

    Returns:
        Health check result
    """
    try:
        from app.database import get_supabase_client

        client = get_supabase_client()
        # Simple query to check connectivity
        _ = client.table("leads").select("id").limit(1).execute()

        return {
            "status": HealthCheckStatus.HEALTHY,
            "message": "Database connection successful",
            "latency_ms": 0,  # Could add timing here
        }
    except Exception as exc:
        logger.error(f"Database health check failed: {str(exc)}")
        return {
            "status": HealthCheckStatus.UNHEALTHY,
            "message": f"Database connection failed: {str(exc)}",
            "error": str(exc),
        }


def check_external_services(app: Flask) -> Dict[str, Any]:
    """
    Check external service dependencies

    Args:
        app: Flask application instance

    Returns:
        Health check results for external services
    """
    services = {}

    # Check SendGrid
    if app.config.get("SENDGRID_API_KEY"):
        services["sendgrid"] = {"status": HealthCheckStatus.HEALTHY, "available": True}
    else:
        services["sendgrid"] = {
            "status": HealthCheckStatus.DEGRADED,
            "available": False,
            "message": "API key not configured",
        }

    # Check Twilio
    if app.config.get("TWILIO_ACCOUNT_SID") and app.config.get("TWILIO_AUTH_TOKEN"):
        services["twilio"] = {"status": HealthCheckStatus.HEALTHY, "available": True}
    else:
        services["twilio"] = {
            "status": HealthCheckStatus.DEGRADED,
            "available": False,
            "message": "Credentials not configured",
        }

    # Check Pusher
    if app.config.get("PUSHER_APP_ID") and app.config.get("PUSHER_KEY"):
        services["pusher"] = {"status": HealthCheckStatus.HEALTHY, "available": True}
    else:
        services["pusher"] = {
            "status": HealthCheckStatus.DEGRADED,
            "available": False,
            "message": "Credentials not configured",
        }

    # Check CallRail
    if app.config.get("CALLRAIL_API_KEY"):
        services["callrail"] = {"status": HealthCheckStatus.HEALTHY, "available": True}
    else:
        services["callrail"] = {
            "status": HealthCheckStatus.DEGRADED,
            "available": False,
            "message": "API key not configured",
        }

    return services


def get_system_metrics() -> Dict[str, Any]:
    """
    Get system-level metrics (CPU, memory, disk)

    Returns:
        System metrics
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "cpu": {
                "usage_percent": cpu_percent,
                "count": psutil.cpu_count(),
            },
            "memory": {
                "total_mb": round(memory.total / (1024 * 1024), 2),
                "available_mb": round(memory.available / (1024 * 1024), 2),
                "used_mb": round(memory.used / (1024 * 1024), 2),
                "percent": memory.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
                "used_gb": round(disk.used / (1024 * 1024 * 1024), 2),
                "free_gb": round(disk.free / (1024 * 1024 * 1024), 2),
                "percent": disk.percent,
            },
        }
    except Exception as exc:
        logger.error(f"Failed to get system metrics: {str(exc)}")
        return {"error": str(exc)}


def register_health_endpoints(app: Flask) -> None:
    """
    Register health check and monitoring endpoints

    Args:
        app: Flask application instance
    """

    @app.route("/health", methods=["GET"])
    def health_check():
        """
        Basic health check endpoint
        Returns 200 if service is running
        """
        return jsonify(
            {
                "status": HealthCheckStatus.HEALTHY,
                "service": "iSwitch Roofs CRM API",
                "timestamp": datetime.utcnow().isoformat(),
                "version": app.config.get("APP_VERSION", "1.0.0"),
            }
        ), 200

    @app.route("/health/ready", methods=["GET"])
    def readiness_check():
        """
        Readiness check - verifies service is ready to accept traffic
        Checks database and critical dependencies
        """
        checks = {
            "database": check_database_health(app),
            "external_services": check_external_services(app),
        }

        # Determine overall status
        overall_status = HealthCheckStatus.HEALTHY
        if checks["database"]["status"] == HealthCheckStatus.UNHEALTHY:
            overall_status = HealthCheckStatus.UNHEALTHY
        elif any(
            svc["status"] == HealthCheckStatus.DEGRADED
            for svc in checks["external_services"].values()
        ):
            overall_status = HealthCheckStatus.DEGRADED

        status_code = 200 if overall_status == HealthCheckStatus.HEALTHY else 503

        return jsonify(
            {
                "status": overall_status,
                "timestamp": datetime.utcnow().isoformat(),
                "checks": checks,
            }
        ), status_code

    @app.route("/health/live", methods=["GET"])
    def liveness_check():
        """
        Liveness check - verifies service is running and responsive
        Should return 200 if process is alive
        """
        return jsonify(
            {
                "status": HealthCheckStatus.HEALTHY,
                "timestamp": datetime.utcnow().isoformat(),
            }
        ), 200

    @app.route("/metrics", methods=["GET"])
    def metrics_endpoint():
        """
        Metrics endpoint - returns application and system metrics
        """
        return jsonify(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "application": performance_monitor.get_metrics(),
                "endpoints": performance_monitor.get_endpoint_metrics(),
                "system": get_system_metrics(),
            }
        ), 200

    logger.info("Health check and metrics endpoints registered")


def setup_request_logging(app: Flask) -> None:
    """
    Setup request/response logging middleware

    Args:
        app: Flask application instance
    """

    @app.before_request
    def log_request():
        """Log incoming requests"""
        # Skip logging for health checks to reduce noise
        if request.path in ["/health", "/health/live", "/health/ready"]:
            return

        logger.info(
            f"Request: {request.method} {request.path}",
            extra={
                "method": request.method,
                "path": request.path,
                "remote_addr": request.remote_addr,
                "user_agent": request.user_agent.string if request.user_agent else None,
            },
        )

    @app.after_request
    def log_response(response):
        """Log outgoing responses"""
        # Skip logging for health checks
        if request.path in ["/health", "/health/live", "/health/ready"]:
            return response

        logger.info(
            f"Response: {request.method} {request.path} - {response.status_code}",
            extra={
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
            },
        )

        return response

    logger.info("Request/response logging middleware configured")


def init_monitoring(app: Flask) -> None:
    """
    Initialize all monitoring and observability features

    Args:
        app: Flask application instance
    """
    # Initialize Sentry
    if app.config.get("SENTRY_DSN"):
        init_sentry(app)

    # Register health check endpoints
    register_health_endpoints(app)

    # Setup request logging
    setup_request_logging(app)

    logger.info("Monitoring and observability initialized")
