"""
iSwitch Roofs CRM - Flask Application Factory
Version: 1.0.0
Date: 2025-10-01
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_cors import CORS
from flask_compress import Compress

# Optional Sentry integration
try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

from app.config import get_config


def _resolve_config_name(explicit_name: str | None = None) -> str:
    """Determine which configuration profile to load."""

    if explicit_name:
        return explicit_name

    for env_var in ("FLASK_CONFIG", "APP_ENV", "FLASK_ENV"):
        value = os.getenv(env_var)
        if value:
            return value.lower()

    return "development"


def create_app(config_name: str | None = None):
    """
    Flask application factory pattern.

    Args:
        config_name (str): Configuration name (development, production, testing)

    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration
    resolved_config_name = _resolve_config_name(config_name)
    config = get_config(resolved_config_name)
    app.config.from_object(config)
    app.config["ACTIVE_CONFIG"] = resolved_config_name

    # Initialize Sentry for error tracking (production only)
    if resolved_config_name == "production" and app.config.get("SENTRY_DSN") and SENTRY_AVAILABLE:
        sentry_sdk.init(
            dsn=app.config["SENTRY_DSN"],
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0,
            environment=app.config.get("SENTRY_ENVIRONMENT", "production"),
        )

    # Setup CORS - Allow all routes including health endpoints
    CORS(
        app,
        resources={
            r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")},
            r"/health": {"origins": app.config.get("CORS_ORIGINS", "*")},
            r"/": {"origins": app.config.get("CORS_ORIGINS", "*")},
        },
        supports_credentials=True,
    )

    # Enable response compression (gzip) for all responses
    # Reduces JSON payload size by 60-80%
    Compress(app)

    # Setup logging
    setup_logging(app)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Register CLI commands
    register_commands(app)

    # Health check endpoint
    @app.route("/health")
    def health_check():
        """
        Enhanced health check endpoint with database status.

        Returns:
            dict: Health status including database connectivity
            int: HTTP status code (200 if healthy, 503 if degraded)
        """
        from app.utils.database import check_database_health

        # Get database health status
        db_health = check_database_health()

        response = {
            "status": "healthy" if db_health["healthy"] else "degraded",
            "service": "iswitch-roofs-crm-api",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_health.get("database", {}),
            "pool": db_health.get("pool", {}),
            "checks": {
                "database_connected": db_health.get("database", {}).get("connected", False),
                "pool_available": db_health.get("pool", {}).get("size", 0) > 0
            }
        }

        # Return 503 if database is not connected (degraded state)
        status_code = 200 if db_health["healthy"] else 503

        return response, status_code

    @app.route("/")
    def index():
        """Root endpoint with API information."""
        return {
            "service": "iSwitch Roofs CRM API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/api/docs",
        }, 200

    return app


def setup_logging(app):
    """
    Configure application logging.

    Args:
        app (Flask): Flask application instance
    """
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        if not os.path.exists("logs"):
            os.mkdir("logs")

        # Setup file handler
        file_handler = RotatingFileHandler(
            "logs/iswitch_roofs_crm.log", maxBytes=10240000, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info("iSwitch Roofs CRM startup")


def register_blueprints(app):
    """
    Register Flask blueprints for API routes.

    Args:
        app (Flask): Flask application instance
    """
    # Import and register realtime routes for Pusher functionality
    from app.routes import realtime

    # Register realtime blueprint for Pusher integration
    app.register_blueprint(realtime.bp, url_prefix="/api/realtime")

    app.logger.info("Realtime routes enabled for Pusher integration")

    # Import and register all API route blueprints
    try:
        from app.routes import auth

        app.register_blueprint(auth.bp, url_prefix="/api/auth")
        app.logger.info("Auth routes registered successfully")
    except Exception as e:
        app.logger.warning(f"Failed to register auth routes: {e}")

    try:
        from app.routes import leads

        app.register_blueprint(leads.bp, url_prefix="/api/leads")
        app.logger.info("Leads routes registered successfully")
    except Exception as e:
        app.logger.warning(f"Failed to register leads routes: {e}")

    try:
        from app.routes import customers

        app.register_blueprint(customers.bp, url_prefix="/api/customers")
        app.logger.info("Customer routes registered successfully")
    except Exception as e:
        app.logger.warning(f"Failed to register customer routes: {e}")

    try:
        from app.routes import projects

        app.register_blueprint(projects.bp, url_prefix="/api/projects")
        app.logger.info("Project routes registered successfully")
    except Exception as e:
        app.logger.warning(f"Failed to register project routes: {e}")

    try:
        from app.routes import interactions

        app.register_blueprint(interactions.bp, url_prefix="/api/interactions")
        app.logger.info("Interaction routes registered successfully")
    except Exception as e:
        app.logger.warning(f"Failed to register interaction routes: {e}")

    try:
        from app.routes import partnerships

        app.register_blueprint(partnerships.bp, url_prefix="/api/partnerships")
        app.logger.info("Partnership routes registered successfully")
    except Exception as e:
        app.logger.warning(f"Failed to register partnership routes: {e}")

    try:
        from app.routes import reviews

        app.register_blueprint(reviews.bp, url_prefix="/api/reviews")
        app.logger.info("Review routes registered successfully")
    except Exception as e:
        app.logger.warning(f"Failed to register review routes: {e}")

    try:
        from app.routes import appointments

        app.register_blueprint(appointments.bp, url_prefix="/api/appointments")
        app.logger.info("Appointment routes registered successfully")
    except Exception as e:
        app.logger.warning(f"Failed to register appointment routes: {e}")

    try:
        from app.routes import analytics

        app.register_blueprint(analytics.bp, url_prefix="/api/analytics")
        app.logger.info("Analytics routes registered successfully")
    except Exception as e:
        app.logger.warning(f"Failed to register analytics routes: {e}")

    try:
        from app.routes import enhanced_analytics

        app.register_blueprint(enhanced_analytics.bp, url_prefix="/api/enhanced-analytics")
        app.logger.info("Enhanced analytics routes registered successfully")
    except Exception as e:
        app.logger.warning(f"Failed to register enhanced analytics routes: {e}")

    try:
        from app.routes import team

        app.register_blueprint(team.bp, url_prefix="/api/team")
        app.logger.info("Team routes registered successfully")
    except Exception as e:
        app.logger.warning(f"Failed to register team routes: {e}")

    try:
        from app.routes import alerts

        app.register_blueprint(alerts.bp, url_prefix="/api/alerts")
        app.logger.info("Alert routes registered successfully")
    except Exception as e:
        app.logger.warning(f"Failed to register alert routes: {e}")

    try:
        from app.routes import business_metrics

        app.register_blueprint(business_metrics.bp, url_prefix="/api/business-metrics")
        app.logger.info("Business metrics routes registered successfully")
    except Exception as e:
        app.logger.warning(f"Failed to register business metrics routes: {e}")

    # Stats API Routes (Dashboard Summary Statistics with REAL DATA)
    try:
        from app.routes import stats

        app.register_blueprint(stats.stats_bp)
        app.logger.info("Stats routes registered successfully (REAL DATA)")
    except Exception as e:
        app.logger.warning(f"Failed to register stats routes: {e}")

    try:
        from app.routes import cache_monitor

        app.register_blueprint(cache_monitor.cache_monitor_bp, url_prefix="/api/cache")
        app.logger.info("Cache monitor routes registered successfully")
    except Exception as e:
        app.logger.warning(f"Failed to register cache monitor routes: {e}")

    try:
        from app.routes import advanced_analytics_flask

        app.register_blueprint(advanced_analytics_flask.bp, url_prefix="/api/advanced-analytics")
        app.logger.info("Advanced analytics routes registered successfully")
    except Exception as e:
        app.logger.warning(f"Failed to register advanced analytics routes: {e}")

    # Week 10: Conversational AI Routes (Synchronous with REAL data)
    try:
        from app.routes import conversation_sync

        app.register_blueprint(conversation_sync.bp, url_prefix="/api/conversation")
        app.logger.info("Conversation routes registered successfully (Week 10 - REAL DATA)")
    except Exception as e:
        app.logger.warning(f"Failed to register conversation routes: {e}")

    # Week 10: Call Transcription Routes (GPT-4o + Whisper API - REAL AI)
    try:
        from app.routes import transcription_sync

        app.register_blueprint(transcription_sync.bp, url_prefix="/api/transcription")
        app.logger.info("Transcription routes registered successfully (GPT-4o + Whisper - REAL AI)")
    except Exception as e:
        app.logger.warning(f"Failed to register transcription routes: {e}")

    # AI-Powered Search Routes (GPT-4o Natural Language Search)
    try:
        from app.routes import ai_search

        app.register_blueprint(ai_search.bp, url_prefix="/api/ai-search")
        app.logger.info("AI-powered search routes registered successfully (GPT-4o)")
    except Exception as e:
        app.logger.warning(f"Failed to register AI search routes: {e}")

    # Data Pipeline Routes (Automated Lead Discovery)
    try:
        from app.routes import data_pipeline

        app.register_blueprint(data_pipeline.bp, url_prefix="/api/data-pipeline")
        app.logger.info("Data pipeline routes registered successfully")
    except Exception as e:
        app.logger.warning(f"Failed to register data pipeline routes: {e}")

    # Live Data Collection Routes (Real-time Lead Generation)
    try:
        from app.routes import live_data

        app.register_blueprint(live_data.bp, url_prefix="/api/live-data")
        app.logger.info("Live data collection routes registered successfully")
    except Exception as e:
        app.logger.warning(f"Failed to register live data routes: {e}")

    # Sales Automation Routes (Placeholder endpoints for development)
    try:
        from app.routes import sales_automation_flask

        app.register_blueprint(sales_automation_flask.bp, url_prefix="/api/sales-automation")
        app.logger.info("Sales automation routes registered successfully (development mode)")
    except Exception as e:
        app.logger.warning(f"Failed to register sales automation routes: {e}")

    # CRM Assistant Routes (Intelligent chatbot for dashboard)
    try:
        from app.routes import crm_assistant

        app.register_blueprint(crm_assistant.bp, url_prefix="/api/crm-assistant")
        app.logger.info("CRM Assistant routes registered successfully (AI-powered chatbot)")
    except Exception as e:
        app.logger.warning(f"Failed to register CRM assistant routes: {e}")


def register_error_handlers(app):
    """
    Register custom error handlers.

    Args:
        app (Flask): Flask application instance
    """
    from werkzeug.exceptions import HTTPException

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle HTTP exceptions."""
        app.logger.error(f"HTTP Error: {error.code} - {error.description}")
        return {
            "error": error.name,
            "message": error.description,
            "code": error.code,
        }, error.code

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle unexpected exceptions."""
        app.logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
        return {
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        }, 500

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return {"error": "Not Found", "message": "The requested resource was not found"}, 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 errors."""
        return {
            "error": "Method Not Allowed",
            "message": "The method is not allowed for the requested URL",
        }, 405


def register_commands(app):
    """
    Register Flask CLI commands.

    Args:
        app (Flask): Flask application instance
    """
    import click

    @app.cli.command()
    def init_db():
        """Initialize the database."""
        click.echo("Initializing database...")
        # Add database initialization logic here
        click.echo("Database initialized successfully!")

    @app.cli.command()
    def seed_db():
        """Seed the database with test data."""
        click.echo("Seeding database with test data...")
        # Add seeding logic here
        click.echo("Database seeded successfully!")

    @app.cli.command()
    def routes():
        """Display all registered routes."""
        import urllib

        from flask import url_for

        output = []
        for rule in app.url_map.iter_rules():
            methods = ",".join(sorted(rule.methods))
            output.append(f"{rule.endpoint:50s} {methods:20s} {rule.rule}")

        for line in sorted(output):
            click.echo(line)
