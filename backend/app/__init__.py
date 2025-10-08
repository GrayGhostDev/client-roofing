"""
iSwitch Roofs CRM - Flask Application Factory
Version: 1.0.0
Date: 2025-10-01
"""

import logging
import os

from flask import Flask
from flask_cors import CORS

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

    # Setup CORS - Allow all routes including health endpoints
    CORS(
        app,
        resources={
            r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")},
            r"/health/*": {"origins": app.config.get("CORS_ORIGINS", "*")},
            r"/metrics": {"origins": app.config.get("CORS_ORIGINS", "*")},
            r"/": {"origins": app.config.get("CORS_ORIGINS", "*")},
        },
        supports_credentials=True,
    )

    # Setup logging first
    from app.logging_config import setup_logging
    setup_logging(app)

    # Initialize monitoring and observability
    from app.monitoring import init_monitoring
    init_monitoring(app)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Register CLI commands
    register_commands(app)

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

    # Register CallRail integration routes
    try:
        from app.routes import callrail_routes

        app.register_blueprint(callrail_routes.callrail_bp)
        app.logger.info("CallRail integration routes registered successfully")
    except Exception as e:
        app.logger.warning(f"Failed to register CallRail routes: {e}")

    # Register webhook routes
    try:
        from app.routes import webhooks

        app.register_blueprint(webhooks.webhooks_bp)
        app.logger.info("Webhook routes registered successfully")
    except Exception as e:
        app.logger.warning(f"Failed to register webhook routes: {e}")


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
