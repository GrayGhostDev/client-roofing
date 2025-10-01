"""
iSwitch Roofs CRM - Projects API Routes
Version: 1.0.0
"""

from flask import Blueprint, jsonify

bp = Blueprint('projects', __name__)


@bp.route('/', methods=['GET'])
def get_projects():
    """Get all projects."""
    return jsonify({"message": "Projects endpoint", "data": []}), 200
