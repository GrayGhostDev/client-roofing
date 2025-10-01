"""
iSwitch Roofs CRM - Partnerships API Routes
Version: 1.0.0
"""

from flask import Blueprint, jsonify

bp = Blueprint('partnerships', __name__)


@bp.route('/', methods=['GET'])
def get_partnerships():
    """Get all partnerships."""
    return jsonify({"message": "Partnerships endpoint", "data": []}), 200
