"""
Vercel serverless function entry point for Flask application
This wraps the Flask app for Vercel's serverless environment
"""

from app import create_app

# Create Flask app instance
app = create_app('production')

# Vercel requires the app to be named 'app' or exported as a handler
# The app instance will be used by Vercel's Python runtime
