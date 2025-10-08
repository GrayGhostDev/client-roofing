"""
CallRail Integration API Routes
Endpoints for managing CallRail integration and importing call data.
"""

import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

from app.integrations.callrail import callrail_integration
from app.utils.decorators import require_auth, require_roles

logger = logging.getLogger(__name__)

callrail_bp = Blueprint("callrail", __name__, url_prefix="/api/integrations/callrail")


@callrail_bp.route("/test-connection", methods=["GET"])
@require_auth
@require_roles(["admin", "manager"])
def test_connection():
    """
    Test connection to CallRail API.

    Returns:
        200: Connection successful
        500: Connection failed
    """
    try:
        success, error_msg = callrail_integration.test_connection()

        if success:
            return jsonify({
                "status": "success",
                "message": "CallRail API connection successful"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": error_msg or "Connection failed"
            }), 500

    except Exception as e:
        logger.error(f"Error testing CallRail connection: {str(e)}")
        return jsonify({"error": str(e)}), 500


@callrail_bp.route("/import-calls", methods=["POST"])
@require_auth
@require_roles(["admin", "manager"])
def import_calls():
    """
    Import call logs from CallRail.

    Request Body:
        start_date (str, optional): Start date for import (ISO format)
        end_date (str, optional): End date for import (ISO format)
        days_back (int, optional): Number of days to look back (default: 30)

    Returns:
        200: Calls imported successfully
        500: Import failed
    """
    try:
        data = request.get_json() or {}

        # Determine date range
        if "start_date" in data and "end_date" in data:
            start_date = data["start_date"]
            end_date = data["end_date"]
        else:
            days_back = data.get("days_back", 30)
            end_date = datetime.utcnow().isoformat()
            start_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()

        # Import calls
        success, calls, error_msg = callrail_integration.import_calls(
            start_date=start_date,
            end_date=end_date
        )

        if not success:
            return jsonify({
                "status": "error",
                "message": error_msg or "Failed to import calls"
            }), 500

        # Process each call to create interactions
        processed_count = 0
        failed_count = 0

        for call in calls or []:
            success, _ = callrail_integration.process_call_to_interaction(call)
            if success:
                processed_count += 1
            else:
                failed_count += 1

        return jsonify({
            "status": "success",
            "message": f"Imported {len(calls or [])} calls",
            "processed": processed_count,
            "failed": failed_count,
            "total_calls": len(calls or [])
        }), 200

    except Exception as e:
        logger.error(f"Error importing calls: {str(e)}")
        return jsonify({"error": str(e)}), 500


@callrail_bp.route("/call/<call_id>", methods=["GET"])
@require_auth
def get_call_details(call_id):
    """
    Get details for a specific CallRail call.

    Args:
        call_id: CallRail call ID

    Returns:
        200: Call details
        404: Call not found
        500: Error retrieving call
    """
    try:
        success, call_data, error_msg = callrail_integration.get_call_details(call_id)

        if success:
            return jsonify({
                "status": "success",
                "call": call_data
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": error_msg or "Failed to retrieve call"
            }), 404 if "404" in str(error_msg) else 500

    except Exception as e:
        logger.error(f"Error retrieving call details: {str(e)}")
        return jsonify({"error": str(e)}), 500


@callrail_bp.route("/setup-webhook", methods=["POST"])
@require_auth
@require_roles(["admin"])
def setup_webhook():
    """
    Configure CallRail webhook for real-time call notifications.

    Request Body:
        webhook_url (str): Full URL to receive webhook POSTs

    Returns:
        200: Webhook configured successfully
        400: Missing webhook_url
        500: Configuration failed
    """
    try:
        data = request.get_json() or {}
        webhook_url = data.get("webhook_url")

        if not webhook_url:
            return jsonify({
                "status": "error",
                "message": "webhook_url is required"
            }), 400

        success, integration_data, error_msg = callrail_integration.setup_webhook(webhook_url)

        if success:
            return jsonify({
                "status": "success",
                "message": "Webhook configured successfully",
                "integration": integration_data
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": error_msg or "Failed to configure webhook"
            }), 500

    except Exception as e:
        logger.error(f"Error setting up webhook: {str(e)}")
        return jsonify({"error": str(e)}), 500


@callrail_bp.route("/status", methods=["GET"])
@require_auth
def get_status():
    """
    Get CallRail integration status and configuration.

    Returns:
        200: Integration status
    """
    try:
        # Test connection
        connection_ok, error_msg = callrail_integration.test_connection()

        return jsonify({
            "status": "success",
            "integration": {
                "name": "CallRail",
                "configured": bool(callrail_integration.api_key and callrail_integration.account_id),
                "connected": connection_ok,
                "error": error_msg if not connection_ok else None,
                "features": {
                    "call_import": True,
                    "webhook_support": True,
                    "recording_download": True,
                    "real_time_alerts": True
                }
            }
        }), 200

    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({"error": str(e)}), 500
