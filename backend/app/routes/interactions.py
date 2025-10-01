"""
iSwitch Roofs CRM - Interactions API Routes
Version: 1.0.0
"""

from flask import Blueprint, jsonify

bp = Blueprint('interactions', __name__)


@bp.route('/', methods=['GET'])
def get_interactions():
    """Get all interactions."""
    return jsonify({"message": "Interactions endpoint", "data": []}), 200
