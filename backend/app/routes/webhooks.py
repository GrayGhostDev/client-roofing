"""
Webhook endpoints for third-party integrations.
Handles incoming webhook requests from CallRail, BirdEye, and other services.
"""

import logging
from flask import Blueprint, request, jsonify

from app.integrations.callrail import callrail_integration

logger = logging.getLogger(__name__)

webhooks_bp = Blueprint("webhooks", __name__, url_prefix="/api/webhooks")


@webhooks_bp.route("/callrail/post-call", methods=["POST"])
def callrail_post_call():
    """
    Handle CallRail post-call webhook.
    Triggered after a call completes with recording and transcription.
    """
    try:
        # Get webhook data
        webhook_data = request.get_json()

        # Verify signature if signing_key is configured
        signing_key = request.headers.get("X-CallRail-Signature-Key")
        signature = request.headers.get("X-CallRail-Signature")

        if signing_key and signature:
            payload = request.get_data(as_text=True)
            if not callrail_integration.verify_webhook_signature(payload, signature, signing_key):
                logger.warning("Invalid CallRail webhook signature")
                return jsonify({"error": "Invalid signature"}), 403

        # Process webhook
        success, message = callrail_integration.process_webhook(webhook_data, "post_call")

        if success:
            return jsonify({"status": "success", "message": message}), 200
        else:
            return jsonify({"status": "error", "message": message}), 500

    except Exception as e:
        logger.error(f"Error processing CallRail post-call webhook: {str(e)}")
        return jsonify({"error": str(e)}), 500


@webhooks_bp.route("/callrail/pre-call", methods=["POST"])
def callrail_pre_call():
    """
    Handle CallRail pre-call webhook.
    Triggered when an inbound call is received, before connection.
    """
    try:
        webhook_data = request.get_json()

        # Verify signature
        signing_key = request.headers.get("X-CallRail-Signature-Key")
        signature = request.headers.get("X-CallRail-Signature")

        if signing_key and signature:
            payload = request.get_data(as_text=True)
            if not callrail_integration.verify_webhook_signature(payload, signature, signing_key):
                return jsonify({"error": "Invalid signature"}), 403

        # Process webhook
        success, message = callrail_integration.process_webhook(webhook_data, "pre_call")

        if success:
            return jsonify({"status": "success", "message": message}), 200
        else:
            return jsonify({"status": "error", "message": message}), 500

    except Exception as e:
        logger.error(f"Error processing CallRail pre-call webhook: {str(e)}")
        return jsonify({"error": str(e)}), 500


@webhooks_bp.route("/callrail/call-modified", methods=["POST"])
def callrail_call_modified():
    """
    Handle CallRail call-modified webhook.
    Triggered when a call record is updated after the call ends.
    """
    try:
        webhook_data = request.get_json()

        # Verify signature
        signing_key = request.headers.get("X-CallRail-Signature-Key")
        signature = request.headers.get("X-CallRail-Signature")

        if signing_key and signature:
            payload = request.get_data(as_text=True)
            if not callrail_integration.verify_webhook_signature(payload, signature, signing_key):
                return jsonify({"error": "Invalid signature"}), 403

        # Process webhook
        success, message = callrail_integration.process_webhook(webhook_data, "call_modified")

        if success:
            return jsonify({"status": "success", "message": message}), 200
        else:
            return jsonify({"status": "error", "message": message}), 500

    except Exception as e:
        logger.error(f"Error processing CallRail call-modified webhook: {str(e)}")
        return jsonify({"error": str(e)}), 500


@webhooks_bp.route("/callrail/routing-complete", methods=["POST"])
def callrail_routing_complete():
    """
    Handle CallRail call-routing-complete webhook.
    Triggered when an inbound call has been routed to its destination.
    """
    try:
        webhook_data = request.get_json()

        # Verify signature
        signing_key = request.headers.get("X-CallRail-Signature-Key")
        signature = request.headers.get("X-CallRail-Signature")

        if signing_key and signature:
            payload = request.get_data(as_text=True)
            if not callrail_integration.verify_webhook_signature(payload, signature, signing_key):
                return jsonify({"error": "Invalid signature"}), 403

        # Process webhook (same as pre-call for now)
        success, message = callrail_integration.process_webhook(webhook_data, "pre_call")

        if success:
            return jsonify({"status": "success", "message": message}), 200
        else:
            return jsonify({"status": "error", "message": message}), 500

    except Exception as e:
        logger.error(f"Error processing CallRail routing-complete webhook: {str(e)}")
        return jsonify({"error": str(e)}), 500


@webhooks_bp.route("/test", methods=["POST", "GET"])
def test_webhook():
    """Test endpoint to verify webhook configuration."""
    if request.method == "POST":
        data = request.get_json() or {}
        logger.info(f"Test webhook received: {data}")
        return jsonify({
            "status": "success",
            "message": "Test webhook received",
            "data": data
        }), 200
    else:
        return jsonify({
            "status": "success",
            "message": "Webhook endpoint is operational"
        }), 200
