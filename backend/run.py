#!/usr/bin/env python3
"""
iSwitch Roofs CRM - Development Server Entry Point
Version: 1.0.0
Date: 2025-10-05

This file serves as the entry point for running the Flask development server.
Usage: python run.py
"""

import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from app import create_app


def main():
    """Main entry point for the Flask application."""

    # Create Flask app instance
    app = create_app()

    # Get configuration from environment or use defaults
    host = app.config.get("API_HOST", "0.0.0.0")
    port = int(app.config.get("API_PORT", 8000))
    debug = app.config.get("DEBUG", True)

    print(
        f"""
    🚀 iSwitch Roofs CRM Backend Server Starting...

    Server Details:
    ├── Host: {host}
    ├── Port: {port}
    ├── Debug: {debug}
    ├── Environment: {app.config.get('ACTIVE_CONFIG', 'development')}
    └── URL: http://{host}:{port}

    Available Endpoints:
    ├── Health Check: http://{host}:{port}/health
    ├── API Root: http://{host}:{port}/api/
    └── Documentation: http://{host}:{port}/api/docs

    🔗 Frontend Integration:
    ├── Reflex Frontend: http://localhost:3000
    └── CORS Origins: {app.config.get('CORS_ORIGINS', [])}

    📊 Services Status:
    ├── Supabase: {'✅ Connected' if app.config.get('SUPABASE_URL') else '❌ Not configured'}
    ├── Pusher: {'✅ Connected' if app.config.get('PUSHER_KEY') else '❌ Not configured'}
    └── Database: {'✅ Ready' if app.config.get('DATABASE_URL') else '❌ Not configured'}

    💡 Press CTRL+C to stop the server
    """
    )

    try:
        # Run the Flask development server
        app.run(host=host, port=port, debug=debug, threaded=True, use_reloader=debug)
    except KeyboardInterrupt:
        print("\n👋 Server stopped gracefully")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
