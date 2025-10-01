"""
iSwitch Roofs CRM - Customers API Routes
Version: 1.0.0
"""

from flask import Blueprint, jsonify

bp = Blueprint('customers', __name__)


@bp.route('/', methods=['GET'])
def get_customers():
    """Get all customers."""
    return jsonify({"message": "Customers endpoint", "data": []}), 200
