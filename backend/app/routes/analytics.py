"""
iSwitch Roofs CRM - Analytics API Routes
Version: 1.0.0
"""

from flask import Blueprint, jsonify

bp = Blueprint('analytics', __name__)


@bp.route('/', methods=['GET'])
def get_analytics():
    """Get analytics data."""
    return jsonify({"message": "Analytics endpoint", "data": {}}), 200


@bp.route('/dashboard', methods=['GET'])
def get_dashboard():
    """Get dashboard analytics."""
    return jsonify({"message": "Analytics dashboard", "data": {}}), 200
