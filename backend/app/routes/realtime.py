"""
iSwitch Roofs CRM - Real-time API Routes (Pusher)
Version: 1.0.0
"""

from flask import Blueprint, request, jsonify, current_app
from backend.app.utils.pusher_client import get_pusher_service
import logging

bp = Blueprint('realtime', __name__)
logger = logging.getLogger(__name__)


@bp.route('/auth', methods=['POST'])
def pusher_auth():
    """
    Authenticate Pusher private/presence channel subscriptions.

    This endpoint is called by the Pusher JavaScript client when a user
    attempts to subscribe to a private or presence channel.
    """
    try:
        pusher_service = get_pusher_service()

        if not pusher_service.is_available():
            return jsonify({"error": "Real-time features not configured"}), 503

        # Get data from request
        socket_id = request.form.get('socket_id')
        channel_name = request.form.get('channel_name')

        if not socket_id or not channel_name:
            return jsonify({"error": "Missing socket_id or channel_name"}), 400

        # TODO: Get authenticated user ID from session/JWT
        # For now, using a placeholder
        user_id = request.headers.get('X-User-ID', 'anonymous')

        # Authenticate the channel subscription
        auth = pusher_service.authenticate_channel(socket_id, channel_name, user_id)

        if "error" in auth:
            return jsonify(auth), 403

        return jsonify(auth), 200

    except Exception as e:
        logger.error(f"Error authenticating Pusher channel: {str(e)}")
        return jsonify({"error": "Authentication failed"}), 500


@bp.route('/trigger', methods=['POST'])
def trigger_event():
    """
    Manually trigger a real-time event.

    This is an admin/testing endpoint for manually broadcasting events.
    Should be protected with authentication in production.
    """
    try:
        pusher_service = get_pusher_service()

        if not pusher_service.is_available():
            return jsonify({"error": "Real-time features not configured"}), 503

        data = request.get_json()

        if not data or not all(k in data for k in ['channel', 'event', 'data']):
            return jsonify({"error": "Missing required fields: channel, event, data"}), 400

        # Trigger the event
        success = pusher_service.trigger(
            channel=data['channel'],
            event=data['event'],
            data=data['data'],
            socket_id=data.get('socket_id')
        )

        if success:
            return jsonify({"message": "Event triggered successfully"}), 200
        else:
            return jsonify({"error": "Failed to trigger event"}), 500

    except Exception as e:
        logger.error(f"Error triggering Pusher event: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route('/status', methods=['GET'])
def realtime_status():
    """Check if real-time features are available."""
    pusher_service = get_pusher_service()

    return jsonify({
        "available": pusher_service.is_available(),
        "service": "Pusher",
        "configured": pusher_service.client is not None
    }), 200


@bp.route('/config', methods=['GET'])
def pusher_config():
    """
    Get Pusher configuration for client-side initialization.

    Returns public configuration needed by frontend clients.
    """
    pusher_service = get_pusher_service()

    if not pusher_service.is_available():
        return jsonify({"error": "Real-time features not configured"}), 503

    return jsonify({
        "key": current_app.config.get('PUSHER_KEY'),
        "cluster": current_app.config.get('PUSHER_CLUSTER'),
        "authEndpoint": "/api/realtime/auth"
    }), 200
