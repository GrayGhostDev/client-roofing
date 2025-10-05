"""
SMS Service using Twilio
Version: 1.0.0

Handles SMS delivery through Twilio API with scheduling, opt-out management, and tracking.
"""

import logging
import os
import re
from datetime import datetime
from typing import Any

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

logger = logging.getLogger(__name__)


class SMSService:
    """Service for sending SMS messages via Twilio."""

    def __init__(
        self,
        account_sid: str | None = None,
        auth_token: str | None = None,
        from_number: str | None = None,
    ):
        """
        Initialize SMS Service.

        Args:
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token
            from_number: Twilio phone number to send from
        """
        self.account_sid = account_sid or os.environ.get("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.environ.get("TWILIO_AUTH_TOKEN")
        self.from_number = from_number or os.environ.get("TWILIO_PHONE_NUMBER")

        if not all([self.account_sid, self.auth_token, self.from_number]):
            logger.warning("Twilio credentials not fully configured")
            self.client = None
        else:
            self.client = Client(self.account_sid, self.auth_token)

        # Message settings
        self.max_message_length = 1600  # Maximum SMS length
        self.default_country_code = "+1"  # Default to US

        # Opt-out keywords
        self.opt_out_keywords = ["STOP", "STOPALL", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"]
        self.opt_in_keywords = ["START", "YES", "UNSTOP", "SUBSCRIBE"]

    def send_sms(
        self,
        to_phone: str,
        message: str,
        from_number: str | None = None,
        messaging_service_sid: str | None = None,
        media_url: list[str] | None = None,
        callback_url: str | None = None,
        send_at: datetime | None = None,
        validity_period: int | None = None,
    ) -> tuple[bool, str | None, dict | None]:
        """
        Send an SMS message via Twilio.

        Args:
            to_phone: Recipient phone number
            message: Message text
            from_number: Sender phone number (defaults to configured)
            messaging_service_sid: Messaging Service SID for advanced features
            media_url: List of media URLs for MMS
            callback_url: Status callback URL
            send_at: Schedule send time (requires Messaging Service)
            validity_period: How long to attempt delivery (seconds)

        Returns:
            Tuple of (success, message_sid, response_data)
        """
        if not self.client:
            logger.error("Twilio client not initialized")
            return False, None, {"error": "SMS service not configured"}

        try:
            # Format phone number
            to_phone = self._format_phone_number(to_phone)

            # Validate message length
            if len(message) > self.max_message_length:
                logger.warning(
                    f"Message truncated from {len(message)} to {self.max_message_length} characters"
                )
                message = message[: self.max_message_length]

            # Prepare message parameters
            params = {"body": message, "to": to_phone}

            # Set from number or messaging service
            if messaging_service_sid:
                params["messaging_service_sid"] = messaging_service_sid
            else:
                params["from_"] = from_number or self.from_number

            # Add media URLs for MMS
            if media_url:
                params["media_url"] = media_url

            # Add status callback
            if callback_url:
                params["status_callback"] = callback_url

            # Add validity period
            if validity_period:
                params["validity_period"] = validity_period

            # Schedule message (requires Messaging Service)
            if send_at and messaging_service_sid:
                params["send_at"] = send_at.isoformat()
                params["schedule_type"] = "fixed"

            # Send message
            message_instance = self.client.messages.create(**params)

            logger.info(f"SMS sent to {to_phone} (SID: {message_instance.sid})")

            return (
                True,
                message_instance.sid,
                {
                    "sid": message_instance.sid,
                    "status": message_instance.status,
                    "date_created": (
                        message_instance.date_created.isoformat()
                        if message_instance.date_created
                        else None
                    ),
                    "price": message_instance.price,
                    "price_unit": message_instance.price_unit,
                    "num_segments": message_instance.num_segments,
                },
            )

        except TwilioRestException as e:
            logger.error(f"Twilio API error: {e}")
            return False, None, {"error": str(e), "code": e.code, "status": e.status}

        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return False, None, {"error": str(e)}

    def send_bulk_sms(
        self,
        recipients: list[str],
        message: str,
        personalized: bool = False,
        personalization_data: dict[str, dict] | None = None,
    ) -> dict[str, Any]:
        """
        Send SMS to multiple recipients.

        Args:
            recipients: List of phone numbers
            message: Message text (can include {variables} for personalization)
            personalized: Whether to personalize messages
            personalization_data: Data for personalization by phone number

        Returns:
            Dictionary with send results
        """
        if not self.client:
            return {"success": False, "error": "SMS service not configured"}

        results = {"total": len(recipients), "sent": 0, "failed": 0, "errors": []}

        for phone in recipients:
            try:
                # Personalize message if needed
                sms_message = message
                if personalized and personalization_data and phone in personalization_data:
                    for key, value in personalization_data[phone].items():
                        sms_message = sms_message.replace(f"{{{key}}}", str(value))

                # Send SMS
                success, sid, data = self.send_sms(phone, sms_message)

                if success:
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(
                        {"phone": phone, "error": data.get("error", "Unknown error")}
                    )

            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"phone": phone, "error": str(e)})

        results["success"] = results["failed"] == 0
        return results

    def get_message_status(self, message_sid: str) -> dict[str, Any] | None:
        """
        Get the status of a sent message.

        Args:
            message_sid: Twilio message SID

        Returns:
            Message data or None
        """
        if not self.client:
            return None

        try:
            message = self.client.messages(message_sid).fetch()

            return {
                "sid": message.sid,
                "status": message.status,
                "to": message.to,
                "from": message.from_,
                "body": message.body,
                "date_sent": message.date_sent.isoformat() if message.date_sent else None,
                "date_updated": message.date_updated.isoformat() if message.date_updated else None,
                "error_code": message.error_code,
                "error_message": message.error_message,
                "num_segments": message.num_segments,
                "price": message.price,
                "price_unit": message.price_unit,
            }

        except Exception as e:
            logger.error(f"Failed to get message status: {str(e)}")
            return None

    def cancel_scheduled_message(self, message_sid: str) -> bool:
        """
        Cancel a scheduled message.

        Args:
            message_sid: Twilio message SID

        Returns:
            True if successful
        """
        if not self.client:
            return False

        try:
            message = self.client.messages(message_sid).update(status="canceled")
            return message.status == "canceled"

        except Exception as e:
            logger.error(f"Failed to cancel message: {str(e)}")
            return False

    def handle_incoming_sms(self, from_phone: str, body: str) -> str:
        """
        Handle incoming SMS messages (for opt-out management).

        Args:
            from_phone: Sender's phone number
            body: Message body

        Returns:
            Response message
        """
        body_upper = body.upper().strip()

        # Check for opt-out
        if any(keyword in body_upper for keyword in self.opt_out_keywords):
            # Add to opt-out list (would integrate with database)
            logger.info(f"Opt-out received from {from_phone}")
            return "You have been unsubscribed from SMS notifications. Reply START to resubscribe."

        # Check for opt-in
        if any(keyword in body_upper for keyword in self.opt_in_keywords):
            # Remove from opt-out list
            logger.info(f"Opt-in received from {from_phone}")
            return "You have been subscribed to SMS notifications. Reply STOP to unsubscribe."

        # Default response
        return "Thank you for your message. A team member will respond soon."

    def create_twiml_response(self, message: str) -> str:
        """
        Create TwiML response for webhooks.

        Args:
            message: Response message

        Returns:
            TwiML XML string
        """
        response = MessagingResponse()
        response.message(message)
        return str(response)

    def _format_phone_number(self, phone: str) -> str:
        """
        Format phone number to E.164 format.

        Args:
            phone: Phone number in various formats

        Returns:
            E.164 formatted phone number
        """
        # Remove all non-digit characters except +
        cleaned = re.sub(r"[^\d+]", "", phone)

        # If already in E.164 format
        if cleaned.startswith("+"):
            return cleaned

        # US number without country code
        if len(cleaned) == 10:
            return f"{self.default_country_code}{cleaned}"

        # US number with 1
        if len(cleaned) == 11 and cleaned.startswith("1"):
            return f"+{cleaned}"

        # Assume it needs default country code
        return f"{self.default_country_code}{cleaned}"

    def validate_phone_number(self, phone: str) -> bool:
        """
        Validate phone number format.

        Args:
            phone: Phone number to validate

        Returns:
            True if valid
        """
        if not self.client:
            # Basic validation only
            formatted = self._format_phone_number(phone)
            return len(formatted) >= 10 and formatted.startswith("+")

        try:
            # Use Twilio Lookup API for validation
            phone_number = self.client.lookups.phone_numbers(
                self._format_phone_number(phone)
            ).fetch()

            return phone_number.phone_number is not None

        except Exception:
            return False

    def get_phone_info(self, phone: str) -> dict[str, Any] | None:
        """
        Get information about a phone number using Twilio Lookup.

        Args:
            phone: Phone number

        Returns:
            Phone information or None
        """
        if not self.client:
            return None

        try:
            phone_number = self.client.lookups.v2.phone_numbers(
                self._format_phone_number(phone)
            ).fetch(fields="carrier,caller_name")

            return {
                "phone_number": phone_number.phone_number,
                "national_format": phone_number.national_format,
                "country_code": phone_number.country_code,
                "carrier": phone_number.carrier,
                "caller_name": phone_number.caller_name,
            }

        except Exception as e:
            logger.error(f"Failed to lookup phone number: {str(e)}")
            return None

    def check_deliverability(self, phone: str) -> bool:
        """
        Check if phone number can receive SMS.

        Args:
            phone: Phone number

        Returns:
            True if deliverable
        """
        info = self.get_phone_info(phone)

        if not info:
            return False

        # Check carrier type
        carrier = info.get("carrier", {})
        carrier_type = carrier.get("type", "")

        # Mobile and voip numbers can typically receive SMS
        return carrier_type in ["mobile", "voip"]

    def calculate_message_segments(self, message: str) -> int:
        """
        Calculate number of SMS segments for a message.

        Args:
            message: Message text

        Returns:
            Number of segments
        """
        length = len(message)

        # GSM 7-bit encoding
        if self._is_gsm_encoded(message):
            if length <= 160:
                return 1
            else:
                # Multi-part messages use 153 chars per segment
                return (length + 152) // 153

        # Unicode encoding (UCS-2)
        else:
            if length <= 70:
                return 1
            else:
                # Multi-part messages use 67 chars per segment
                return (length + 66) // 67

    def _is_gsm_encoded(self, message: str) -> bool:
        """
        Check if message can be GSM 7-bit encoded.

        Args:
            message: Message text

        Returns:
            True if GSM encodable
        """
        # GSM 7-bit default alphabet and extensions
        gsm_chars = (
            "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ"
            " !\"#¤%&'()*+,-./0123456789:;<=>?"
            "¡ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_"
            "§abcdefghijklmnopqrstuvwxyz{|}~"
            "äöñüà\f^{}\\[~]|€ÄÖÑÜà"
        )

        return all(char in gsm_chars for char in message)


# Singleton instance
sms_service = SMSService()
