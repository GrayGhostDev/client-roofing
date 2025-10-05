"""
iSwitch Roofs CRM - Real-time API Routes (Pusher)
Version: 1.0.0
"""

import logging

from flask import Blueprint, jsonify, request

from app.services.realtime_service import realtime_service

bp = Blueprint("realtime", __name__)
logger = logging.getLogger(__name__)


@bp.route("/auth", methods=["POST"])
def pusher_auth():
    """
    Authenticate Pusher private/presence channel subscriptions.

    This endpoint is called by the Pusher JavaScript client when a user
    attempts to subscribe to a private or presence channel.
    """
    try:
        if not realtime_service.client:
            return jsonify({"error": "Real-time features not configured"}), 503

        # Get data from request
        socket_id = request.form.get("socket_id")
        channel_name = request.form.get("channel_name")

        if not socket_id or not channel_name:
            return jsonify({"error": "Missing socket_id or channel_name"}), 400

        # TODO: Get authenticated user ID from session/JWT
        # For now, using a placeholder
        user_id = request.headers.get("X-User-ID", "anonymous")

        # Build user data for presence channels
        user_data = {
            "id": user_id,
            "name": request.headers.get("X-User-Name", "Anonymous"),
            "email": request.headers.get("X-User-Email", ""),
        }

        # Authenticate the channel subscription
        auth = realtime_service.authenticate_channel(socket_id, channel_name, user_data)

        if "error" in auth:
            return jsonify(auth), 403

        return jsonify(auth), 200

    except Exception as e:
        logger.error(f"Error authenticating Pusher channel: {str(e)}")
        return jsonify({"error": "Authentication failed"}), 500


@bp.route("/trigger", methods=["POST"])
def trigger_event():
    """
    Manually trigger a real-time event.

    This is an admin/testing endpoint for manually broadcasting events.
    Should be protected with authentication in production.
    """
    try:
        if not realtime_service.client:
            return jsonify({"error": "Real-time features not configured"}), 503

        data = request.get_json()

        if not data or not all(k in data for k in ["channel", "event", "data"]):
            return jsonify({"error": "Missing required fields: channel, event, data"}), 400

        # Trigger the event
        success = realtime_service.trigger_event(
            channel=data["channel"],
            event=data["event"],
            data=data["data"],
            socket_id=data.get("socket_id"),
        )

        if success:
            return jsonify({"message": "Event triggered successfully"}), 200
        else:
            return jsonify({"error": "Failed to trigger event"}), 500

    except Exception as e:
        logger.error(f"Error triggering Pusher event: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route("/status", methods=["GET"])
def realtime_status():
    """Check if real-time features are available."""
    return (
        jsonify(
            {
                "available": realtime_service.client is not None,
                "service": "Pusher",
                "configured": realtime_service.client is not None,
            }
        ),
        200,
    )


@bp.route("/config", methods=["GET"])
def pusher_config():
    """
    Get Pusher configuration for client-side initialization.

    Returns public configuration needed by frontend clients.
    """
    if not realtime_service.client:
        return jsonify({"error": "Real-time features not configured"}), 503

    return (
        jsonify(
            {
                "key": realtime_service.key,
                "cluster": realtime_service.cluster,
                "authEndpoint": "/api/realtime/auth",
            }
        ),
        200,
    )
