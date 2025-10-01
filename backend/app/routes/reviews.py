"""
iSwitch Roofs CRM - Reviews API Routes
Version: 1.0.0
"""

from flask import Blueprint, jsonify

bp = Blueprint('reviews', __name__)


@bp.route('/', methods=['GET'])
def get_reviews():
    """Get all reviews."""
    return jsonify({"message": "Reviews endpoint", "data": []}), 200
