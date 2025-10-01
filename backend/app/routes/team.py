"""
iSwitch Roofs CRM - Team API Routes
Version: 1.0.0
"""

from flask import Blueprint, jsonify

bp = Blueprint('team', __name__)


@bp.route('/', methods=['GET'])
def get_team_members():
    """Get all team members."""
    return jsonify({"message": "Team endpoint", "data": []}), 200
