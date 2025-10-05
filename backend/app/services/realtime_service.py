"""
Real-time Service using Pusher
Version: 1.0.0

Handles real-time event broadcasting through Pusher Channels.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any

import pusher
from pusher.errors import PusherError

logger = logging.getLogger(__name__)


class RealtimeService:
    """Service for real-time event broadcasting via Pusher."""

    def __init__(
        self,
        app_id: str | None = None,
        key: str | None = None,
        secret: str | None = None,
        cluster: str | None = None,
    ):
        """
        Initialize Real-time Service.

        Args:
            app_id: Pusher App ID
            key: Pusher Key
            secret: Pusher Secret
            cluster: Pusher Cluster
        """
        self.app_id = app_id or os.environ.get("PUSHER_APP_ID") or "test_app_id"
        self.key = key or os.environ.get("PUSHER_KEY") or "test_key"
        self.secret = secret or os.environ.get("PUSHER_SECRET") or "test_secret"
        self.cluster = cluster or os.environ.get("PUSHER_CLUSTER", "us2")

        # Only create client if we have real credentials (not test defaults)
        if self.app_id == "test_app_id" or self.key == "test_key" or self.secret == "test_secret":
            logger.warning("Pusher credentials not configured, using test mode")
            self.client = None
        else:
            try:
                self.client = pusher.Pusher(
                    app_id=self.app_id,
                    key=self.key,
                    secret=self.secret,
                    cluster=self.cluster,
                    ssl=True,
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Pusher client: {str(e)}")
                self.client = None

        # Channel prefixes
        self.public_prefix = ""
        self.private_prefix = "private-"
        self.presence_prefix = "presence-"

        # Event name limits
        self.max_event_name_length = 200
        self.max_channels_per_trigger = 100
        self.max_data_size = 10240  # 10KB

    def trigger_event(
        self,
        channel: str | list[str],
        event: str,
        data: dict[str, Any],
        socket_id: str | None = None,
    ) -> bool:
        """
        Trigger an event to one or more channels.

        Args:
            channel: Channel name(s) to trigger to
            event: Event name
            data: Event data (will be JSON encoded)
            socket_id: Socket ID to exclude from receiving the event

        Returns:
            True if successful
        """
        if not self.client:
            logger.error("Pusher client not initialized")
            return False

        try:
            # Validate event name
            if len(event) > self.max_event_name_length:
                logger.error(f"Event name too long: {len(event)} > {self.max_event_name_length}")
                return False

            # Validate data size
            data_json = json.dumps(data)
            if len(data_json) > self.max_data_size:
                logger.error(f"Data too large: {len(data_json)} > {self.max_data_size}")
                return False

            # Validate channel count
            channels = channel if isinstance(channel, list) else [channel]
            if len(channels) > self.max_channels_per_trigger:
                logger.error(
                    f"Too many channels: {len(channels)} > {self.max_channels_per_trigger}"
                )
                return False

            # Trigger event
            response = self.client.trigger(
                channels=channel, event_name=event, data=data, socket_id=socket_id
            )

            logger.info(f"Event '{event}' triggered to channel(s): {channel}")
            return True

        except PusherError as e:
            logger.error(f"Pusher error: {e}")
            return False

        except Exception as e:
            logger.error(f"Failed to trigger event: {str(e)}")
            return False

    def trigger_batch(self, events: list[dict[str, Any]]) -> bool:
        """
        Trigger multiple events in a single request.

        Args:
            events: List of event dictionaries with channel, name, data, socket_id

        Returns:
            True if successful
        """
        if not self.client:
            return False

        try:
            # Format events for batch trigger
            batch_events = []
            for event in events[:10]:  # Max 10 events per batch
                batch_event = {
                    "channel": event["channel"],
                    "name": event["name"],
                    "data": event["data"],
                }

                if "socket_id" in event:
                    batch_event["socket_id"] = event["socket_id"]

                batch_events.append(batch_event)

            # Trigger batch
            self.client.trigger_batch(batch_events)

            logger.info(f"Batch triggered: {len(batch_events)} events")
            return True

        except Exception as e:
            logger.error(f"Failed to trigger batch: {str(e)}")
            return False

    def send_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        data: dict[str, Any] | None = None,
        priority: str = "normal",
    ) -> bool:
        """
        Send a real-time notification to a user.

        Args:
            user_id: User ID to send to
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            data: Additional data
            priority: Notification priority

        Returns:
            True if successful
        """
        channel = f"private-user-{user_id}"
        event = "notification"

        notification_data = {
            "type": notification_type,
            "title": title,
            "message": message,
            "priority": priority,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {},
        }

        return self.trigger_event(channel, event, notification_data)

    def broadcast_team_event(self, team_id: str, event_type: str, data: dict[str, Any]) -> bool:
        """
        Broadcast an event to all team members.

        Args:
            team_id: Team ID
            event_type: Type of event
            data: Event data

        Returns:
            True if successful
        """
        channel = f"presence-team-{team_id}"
        return self.trigger_event(channel, event_type, data)

    def update_lead_status(
        self, lead_id: str, status: str, updated_by: str, additional_data: dict | None = None
    ) -> bool:
        """
        Broadcast lead status update.

        Args:
            lead_id: Lead ID
            status: New status
            updated_by: User who updated
            additional_data: Additional update data

        Returns:
            True if successful
        """
        data = {
            "lead_id": lead_id,
            "status": status,
            "updated_by": updated_by,
            "updated_at": datetime.utcnow().isoformat(),
        }

        if additional_data:
            data.update(additional_data)

        return self.trigger_event("leads", "lead-updated", data)

    def notify_appointment_update(
        self, appointment_id: str, action: str, appointment_data: dict[str, Any]
    ) -> bool:
        """
        Notify about appointment updates.

        Args:
            appointment_id: Appointment ID
            action: Action taken (scheduled, rescheduled, cancelled)
            appointment_data: Appointment details

        Returns:
            True if successful
        """
        event = f"appointment-{action}"
        data = {
            "appointment_id": appointment_id,
            "action": action,
            "appointment": appointment_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Send to appointments channel
        channels = ["appointments"]

        # Also send to assigned team member if present
        if "assigned_to" in appointment_data:
            channels.append(f"private-user-{appointment_data['assigned_to']}")

        return self.trigger_event(channels, event, data)

    def authenticate_channel(
        self, socket_id: str, channel: str, user_data: dict[str, Any] | None = None
    ) -> dict[str, str]:
        """
        Authenticate a user for private or presence channel.

        Args:
            socket_id: Client socket ID
            channel: Channel name
            user_data: User data for presence channels

        Returns:
            Authentication response
        """
        if not self.client:
            return {"error": "Pusher client not initialized"}

        try:
            # Check if presence channel
            if channel.startswith(self.presence_prefix):
                if not user_data:
                    return {"error": "User data required for presence channel"}

                auth = self.client.authenticate(
                    channel=channel,
                    socket_id=socket_id,
                    custom_data={
                        "user_id": user_data.get("id"),
                        "user_info": {
                            "name": user_data.get("name"),
                            "email": user_data.get("email"),
                        },
                    },
                )
            else:
                # Private channel
                auth = self.client.authenticate(channel=channel, socket_id=socket_id)

            return auth

        except Exception as e:
            logger.error(f"Failed to authenticate channel: {str(e)}")
            return {"error": str(e)}

    def get_channel_info(self, channel: str, info: list[str] | None = None) -> dict | None:
        """
        Get information about a channel.

        Args:
            channel: Channel name
            info: List of info to retrieve ('user_count', 'subscription_count')

        Returns:
            Channel information or None
        """
        if not self.client:
            return None

        try:
            params = {}
            if info:
                params["info"] = ",".join(info)

            response = self.client.channels_info(channel, params)
            return response

        except Exception as e:
            logger.error(f"Failed to get channel info: {str(e)}")
            return None

    def get_channels_list(
        self, prefix_filter: str | None = None, info: list[str] | None = None
    ) -> dict | None:
        """
        Get list of active channels.

        Args:
            prefix_filter: Filter channels by prefix
            info: List of info to retrieve

        Returns:
            Channels list or None
        """
        if not self.client:
            return None

        try:
            params = {}
            if prefix_filter:
                params["filter_by_prefix"] = prefix_filter
            if info:
                params["info"] = ",".join(info)

            response = self.client.channels_info(params)
            return response

        except Exception as e:
            logger.error(f"Failed to get channels list: {str(e)}")
            return None

    def get_users_in_channel(self, channel: str) -> list[dict] | None:
        """
        Get users in a presence channel.

        Args:
            channel: Presence channel name

        Returns:
            List of users or None
        """
        if not channel.startswith(self.presence_prefix):
            logger.error("Can only get users for presence channels")
            return None

        info = self.get_channel_info(channel, ["user_count", "users"])

        if info and "users" in info:
            return info["users"]

        return None

    def trigger_client_event(
        self, channel: str, event: str, data: dict[str, Any], socket_id: str
    ) -> bool:
        """
        Trigger a client event (from client to client).

        Args:
            channel: Private or presence channel
            event: Event name (must start with 'client-')
            data: Event data
            socket_id: Sender's socket ID

        Returns:
            True if successful
        """
        if not event.startswith("client-"):
            logger.error("Client events must start with 'client-'")
            return False

        if not (
            channel.startswith(self.private_prefix) or channel.startswith(self.presence_prefix)
        ):
            logger.error("Client events only work on private or presence channels")
            return False

        return self.trigger_event(channel, event, data, socket_id)

    def validate_webhook(self, key: str, signature: str, body: str) -> bool:
        """
        Validate a Pusher webhook signature.

        Args:
            key: Webhook key from headers
            signature: Webhook signature from headers
            body: Request body

        Returns:
            True if valid
        """
        if not self.client:
            return False

        try:
            return self.client.validate_webhook(key, signature, body)

        except Exception as e:
            logger.error(f"Failed to validate webhook: {str(e)}")
            return False

    def process_webhook(self, headers: dict, body: str) -> dict | None:
        """
        Process a Pusher webhook.

        Args:
            headers: Request headers
            body: Request body

        Returns:
            Webhook data or None
        """
        # Validate webhook
        key = headers.get("X-Pusher-Key")
        signature = headers.get("X-Pusher-Signature")

        if not self.validate_webhook(key, signature, body):
            logger.error("Invalid webhook signature")
            return None

        try:
            data = json.loads(body)

            # Process events
            events = data.get("events", [])
            for event in events:
                event_name = event.get("name")
                channel = event.get("channel")

                logger.info(f"Webhook event: {event_name} on channel {channel}")

                # Handle specific webhook events
                if event_name == "channel_occupied":
                    # First subscriber to channel
                    pass
                elif event_name == "channel_vacated":
                    # Last subscriber left channel
                    pass
                elif event_name == "member_added":
                    # User joined presence channel
                    pass
                elif event_name == "member_removed":
                    # User left presence channel
                    pass

            return data

        except Exception as e:
            logger.error(f"Failed to process webhook: {str(e)}")
            return None


# Singleton instance
realtime_service = RealtimeService()
