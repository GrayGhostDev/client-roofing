"""
CallRail Integration Module
Handles call tracking, recording import, and webhook processing.

Features:
- OAuth2 authentication with CallRail API
- Call data import and synchronization
- Webhook handling for real-time call events
- Call recording retrieval and storage
- Lead association and interaction logging
"""

import hashlib
import hmac
import base64
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from flask import current_app

from app.utils.supabase_client import SupabaseClient
from app.services.notification import notification_service
from app.services.realtime_service import realtime_service

logger = logging.getLogger(__name__)


class CallRailIntegration:
    """
    CallRail Integration Service

    Handles all interactions with the CallRail API including:
    - Authentication and API key management
    - Call log import and synchronization
    - Webhook configuration and processing
    - Call recording retrieval
    - Lead and customer association
    """

    BASE_URL = "https://api.callrail.com/v3"

    def __init__(self):
        """Initialize CallRail integration with credentials from config."""
        self.api_key = os.getenv("CALLRAIL_API_KEY")
        self.account_id = os.getenv("CALLRAIL_ACCOUNT_ID")
        self.company_id = os.getenv("CALLRAIL_COMPANY_ID")

        if not self.api_key:
            logger.warning("CallRail API key not configured")

        self.supabase = SupabaseClient()
        self._session = None

    @property
    def session(self) -> requests.Session:
        """Get or create requests session with authentication."""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                "Authorization": f"Token token={self.api_key}",
                "Content-Type": "application/json"
            })
        return self._session

    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """
        Test connection to CallRail API.

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            if not self.api_key or not self.account_id:
                return False, "CallRail credentials not configured"

            url = f"{self.BASE_URL}/a/{self.account_id}/calls.json"
            params = {"per_page": 1}

            response = self.session.get(url, params=params)

            if response.status_code == 200:
                logger.info("CallRail connection test successful")
                return True, None
            else:
                error_msg = f"CallRail API error: {response.status_code}"
                logger.error(error_msg)
                return False, error_msg

        except Exception as e:
            error_msg = f"CallRail connection error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def import_calls(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        per_page: int = 100
    ) -> Tuple[bool, Optional[List[Dict]], Optional[str]]:
        """
        Import call logs from CallRail.

        Args:
            start_date: Start date for call import (ISO format)
            end_date: End date for call import (ISO format)
            page: Page number for pagination
            per_page: Number of records per page

        Returns:
            Tuple of (success, calls_data, error_message)
        """
        try:
            if not self.api_key or not self.account_id:
                return False, None, "CallRail credentials not configured"

            url = f"{self.BASE_URL}/a/{self.account_id}/calls.json"

            params = {
                "page": page,
                "per_page": per_page,
                "fields": "id,customer_phone_number,customer_name,duration,start_time,"
                         "answered,recording,transcription,direction,business_phone_number,"
                         "tracking_phone_number,source_name,keywords,lead_status,note"
            }

            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date

            response = self.session.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                calls = data.get("calls", [])

                logger.info(f"Successfully imported {len(calls)} calls from CallRail")
                return True, calls, None
            else:
                error_msg = f"CallRail API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return False, None, error_msg

        except Exception as e:
            error_msg = f"Error importing calls: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    def get_call_details(self, call_id: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Retrieve detailed information for a specific call.

        Args:
            call_id: The CallRail call ID

        Returns:
            Tuple of (success, call_data, error_message)
        """
        try:
            url = f"{self.BASE_URL}/a/{self.account_id}/calls/{call_id}.json"

            response = self.session.get(url)

            if response.status_code == 200:
                call_data = response.json()
                logger.info(f"Retrieved call details for {call_id}")
                return True, call_data, None
            else:
                error_msg = f"CallRail API error: {response.status_code}"
                logger.error(error_msg)
                return False, None, error_msg

        except Exception as e:
            error_msg = f"Error retrieving call details: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    def process_call_to_interaction(self, call_data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Process CallRail call data and create interaction record.

        Args:
            call_data: Call data from CallRail API

        Returns:
            Tuple of (success, interaction_id)
        """
        try:
            # Extract call information
            phone_number = call_data.get("customer_phone_number", "")
            customer_name = call_data.get("customer_name", "")
            duration = call_data.get("duration", 0)
            start_time = call_data.get("start_time")
            answered = call_data.get("answered", False)
            recording_url = call_data.get("recording")
            transcription = call_data.get("transcription", "")
            direction = call_data.get("direction", "inbound")
            source_name = call_data.get("source_name", "")

            # Find associated lead or customer by phone number
            lead_id, customer_id = self._find_entity_by_phone(phone_number)

            # Create interaction record
            interaction_data = {
                "type": "call",
                "direction": direction,
                "lead_id": lead_id,
                "customer_id": customer_id,
                "notes": f"CallRail call from {source_name}" if source_name else "CallRail call",
                "outcome": "completed" if answered else "no_answer",
                "call_duration_seconds": duration,
                "call_recording_url": recording_url,
                "call_from_number": phone_number,
                "call_sid": str(call_data.get("id")),
                "scheduled_at": start_time,
                "completed_at": start_time,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Add transcription to notes if available
            if transcription:
                interaction_data["notes"] += f"\n\nTranscription:\n{transcription}"

            # Insert into database
            result = self.supabase.client.table("interactions").insert(interaction_data).execute()

            if result.data:
                interaction_id = result.data[0].get("id")
                logger.info(f"Created interaction {interaction_id} from CallRail call")

                # Send notification if this is a new lead call
                if lead_id and direction == "inbound":
                    self._send_call_notification(lead_id, call_data)

                return True, interaction_id
            else:
                return False, None

        except Exception as e:
            logger.error(f"Error processing call to interaction: {str(e)}")
            return False, None

    def _find_entity_by_phone(self, phone_number: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Find lead or customer by phone number.

        Args:
            phone_number: Phone number to search for

        Returns:
            Tuple of (lead_id, customer_id)
        """
        try:
            # Clean phone number
            clean_phone = phone_number.replace("+1", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")

            # Search in leads
            lead_result = self.supabase.client.table("leads")\
                .select("id")\
                .ilike("phone", f"%{clean_phone}%")\
                .limit(1)\
                .execute()

            lead_id = lead_result.data[0].get("id") if lead_result.data else None

            # Search in customers
            customer_result = self.supabase.client.table("customers")\
                .select("id")\
                .ilike("phone", f"%{clean_phone}%")\
                .limit(1)\
                .execute()

            customer_id = customer_result.data[0].get("id") if customer_result.data else None

            return lead_id, customer_id

        except Exception as e:
            logger.error(f"Error finding entity by phone: {str(e)}")
            return None, None

    def _send_call_notification(self, lead_id: str, call_data: Dict):
        """Send real-time notification for new call."""
        try:
            # Send push notification via Pusher
            realtime_service.trigger_event(
                channel="leads",
                event="call-received",
                data={
                    "lead_id": lead_id,
                    "phone_number": call_data.get("customer_phone_number"),
                    "source": call_data.get("source_name"),
                    "timestamp": call_data.get("start_time")
                }
            )

            logger.info(f"Sent call notification for lead {lead_id}")

        except Exception as e:
            logger.error(f"Error sending call notification: {str(e)}")

    def setup_webhook(self, webhook_url: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Configure CallRail webhook for real-time call notifications.

        Args:
            webhook_url: URL to receive webhook POST requests

        Returns:
            Tuple of (success, integration_data, error_message)
        """
        try:
            if not self.company_id:
                return False, None, "CallRail company_id not configured"

            url = f"{self.BASE_URL}/a/{self.account_id}/integrations.json"

            payload = {
                "type": "Webhooks",
                "company_id": self.company_id,
                "config": {
                    "post_call_webhook": [webhook_url],
                    "pre_call_webhook": [webhook_url],
                    "call_routing_complete_webhook": [webhook_url]
                }
            }

            response = self.session.post(url, json=payload)

            if response.status_code in [200, 201]:
                integration_data = response.json()
                logger.info(f"Successfully configured CallRail webhook: {webhook_url}")
                return True, integration_data, None
            else:
                error_msg = f"CallRail API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return False, None, error_msg

        except Exception as e:
            error_msg = f"Error setting up webhook: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
        signing_key: str
    ) -> bool:
        """
        Verify webhook request signature from CallRail.

        Args:
            payload: Raw request body as string
            signature: Signature from request header
            signing_key: Signing key from CallRail integration config

        Returns:
            True if signature is valid
        """
        try:
            # Compute HMAC signature
            hmac_obj = hmac.new(
                signing_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha1
            )

            computed_signature = base64.b64encode(hmac_obj.digest()).decode('utf-8')

            # Compare signatures
            return hmac.compare_digest(computed_signature, signature)

        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False

    def process_webhook(self, webhook_data: Dict, webhook_type: str) -> Tuple[bool, Optional[str]]:
        """
        Process incoming webhook from CallRail.

        Args:
            webhook_data: Webhook payload data
            webhook_type: Type of webhook (pre_call, post_call, etc.)

        Returns:
            Tuple of (success, message)
        """
        try:
            logger.info(f"Processing CallRail {webhook_type} webhook")

            if webhook_type == "post_call":
                # Process completed call
                success, interaction_id = self.process_call_to_interaction(webhook_data)

                if success:
                    return True, f"Created interaction {interaction_id}"
                else:
                    return False, "Failed to create interaction"

            elif webhook_type == "pre_call":
                # Real-time call alert
                phone_number = webhook_data.get("customer_phone_number")
                lead_id, _ = self._find_entity_by_phone(phone_number)

                if lead_id:
                    self._send_call_notification(lead_id, webhook_data)
                    return True, "Call notification sent"
                else:
                    logger.info(f"No lead found for incoming call from {phone_number}")
                    return True, "Call received but no lead match"

            elif webhook_type == "call_modified":
                # Handle call updates (notes, tags added after call)
                call_id = webhook_data.get("id")
                changes = webhook_data.get("changes", [])

                logger.info(f"Call {call_id} modified: {changes}")

                # Update interaction record if it exists
                # TODO: Implement update logic

                return True, "Call update processed"

            else:
                logger.warning(f"Unknown webhook type: {webhook_type}")
                return True, "Unknown webhook type"

        except Exception as e:
            error_msg = f"Error processing webhook: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def download_recording(self, recording_url: str) -> Tuple[bool, Optional[bytes], Optional[str]]:
        """
        Download call recording from CallRail.

        Args:
            recording_url: URL to call recording

        Returns:
            Tuple of (success, recording_data, error_message)
        """
        try:
            response = self.session.get(recording_url)

            if response.status_code == 200:
                logger.info(f"Downloaded recording from {recording_url}")
                return True, response.content, None
            else:
                error_msg = f"Error downloading recording: {response.status_code}"
                logger.error(error_msg)
                return False, None, error_msg

        except Exception as e:
            error_msg = f"Error downloading recording: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg


# Singleton instance
callrail_integration = CallRailIntegration()
