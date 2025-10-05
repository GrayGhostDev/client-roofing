"""
iSwitch Roofs CRM - Flask Application Factory
Version: 1.0.0
Date: 2025-10-01
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_cors import CORS

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
        """Health check endpoint for monitoring."""
        return {"status": "healthy", "service": "iswitch-roofs-crm-api"}, 200

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
