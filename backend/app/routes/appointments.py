"""
iSwitch Roofs CRM - Appointments API Routes
Version: 1.0.0
"""

from flask import Blueprint, jsonify

bp = Blueprint('appointments', __name__)


@bp.route('/', methods=['GET'])
def get_appointments():
    """Get all appointments."""
    return jsonify({"message": "Appointments endpoint", "data": []}), 200
