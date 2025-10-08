"""
UptimeRobot Monitoring Setup
Configures UptimeRobot monitors for application endpoints
"""

import logging
import os
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class UptimeRobotClient:
    """
    Client for UptimeRobot API
    """

    def __init__(self, api_key: str):
        """
        Initialize UptimeRobot client

        Args:
            api_key: UptimeRobot API key
        """
        self.api_key = api_key
        self.base_url = "https://api.uptimerobot.com/v2"
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache",
        }

    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to UptimeRobot API

        Args:
            endpoint: API endpoint
            data: Request data

        Returns:
            Response data
        """
        data["api_key"] = self.api_key
        data["format"] = "json"

        url = f"{self.base_url}/{endpoint}"

        try:
            response = requests.post(url, headers=self.headers, data=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"UptimeRobot API request failed: {str(e)}")
            raise

    def get_monitors(self) -> List[Dict[str, Any]]:
        """
        Get all monitors

        Returns:
            List of monitors
        """
        data = {"logs": "0", "all_time_uptime_ratio": "1"}
        response = self._make_request("getMonitors", data)

        if response.get("stat") == "ok":
            return response.get("monitors", [])
        else:
            logger.error(f"Failed to get monitors: {response}")
            return []

    def create_monitor(
        self,
        friendly_name: str,
        url: str,
        monitor_type: int = 1,
        interval: int = 300,
        alert_contacts: Optional[str] = None,
        http_method: int = 1,
        timeout: int = 30,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new monitor

        Args:
            friendly_name: Monitor display name
            url: URL to monitor
            monitor_type: Monitor type (1=HTTP(s), 2=Keyword, 3=Ping, 4=Port)
            interval: Check interval in seconds (300, 600, 900, 1800, 3600)
            alert_contacts: Alert contact IDs (comma-separated)
            http_method: HTTP method (1=HEAD, 2=GET, 3=POST, 4=PUT, 5=PATCH, 6=DELETE, 7=OPTIONS)
            timeout: Request timeout in seconds

        Returns:
            Created monitor data or None if failed
        """
        data = {
            "friendly_name": friendly_name,
            "url": url,
            "type": monitor_type,
            "interval": interval,
            "timeout": timeout,
            "http_method": http_method,
        }

        if alert_contacts:
            data["alert_contacts"] = alert_contacts

        try:
            response = self._make_request("newMonitor", data)

            if response.get("stat") == "ok":
                logger.info(f"Monitor created successfully: {friendly_name}")
                return response.get("monitor")
            else:
                logger.error(f"Failed to create monitor: {response}")
                return None
        except Exception as e:
            logger.error(f"Error creating monitor: {str(e)}")
            return None

    def update_monitor(
        self, monitor_id: int, **kwargs
    ) -> bool:
        """
        Update an existing monitor

        Args:
            monitor_id: Monitor ID to update
            **kwargs: Fields to update

        Returns:
            True if successful
        """
        data = {"id": monitor_id}
        data.update(kwargs)

        try:
            response = self._make_request("editMonitor", data)

            if response.get("stat") == "ok":
                logger.info(f"Monitor updated successfully: {monitor_id}")
                return True
            else:
                logger.error(f"Failed to update monitor: {response}")
                return False
        except Exception as e:
            logger.error(f"Error updating monitor: {str(e)}")
            return False

    def delete_monitor(self, monitor_id: int) -> bool:
        """
        Delete a monitor

        Args:
            monitor_id: Monitor ID to delete

        Returns:
            True if successful
        """
        data = {"id": monitor_id}

        try:
            response = self._make_request("deleteMonitor", data)

            if response.get("stat") == "ok":
                logger.info(f"Monitor deleted successfully: {monitor_id}")
                return True
            else:
                logger.error(f"Failed to delete monitor: {response}")
                return False
        except Exception as e:
            logger.error(f"Error deleting monitor: {str(e)}")
            return False

    def get_alert_contacts(self) -> List[Dict[str, Any]]:
        """
        Get all alert contacts

        Returns:
            List of alert contacts
        """
        response = self._make_request("getAlertContacts", {})

        if response.get("stat") == "ok":
            return response.get("alert_contacts", [])
        else:
            logger.error(f"Failed to get alert contacts: {response}")
            return []


def setup_monitors(
    base_url: str,
    api_key: str,
    alert_contacts: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Setup UptimeRobot monitors for the application

    Args:
        base_url: Base URL of the application (e.g., https://api.iswitchroofs.com)
        api_key: UptimeRobot API key
        alert_contacts: Alert contact IDs (comma-separated)

    Returns:
        List of created/updated monitors
    """
    client = UptimeRobotClient(api_key)

    # Define monitors to create
    monitors_config = [
        {
            "friendly_name": "iSwitch Roofs CRM - Main Health Check",
            "url": f"{base_url}/health",
            "interval": 300,  # 5 minutes
            "http_method": 1,  # HEAD
            "description": "Basic health check endpoint",
        },
        {
            "friendly_name": "iSwitch Roofs CRM - Readiness Check",
            "url": f"{base_url}/health/ready",
            "interval": 300,  # 5 minutes
            "http_method": 2,  # GET
            "description": "Readiness probe with database check",
        },
        {
            "friendly_name": "iSwitch Roofs CRM - API Liveness",
            "url": f"{base_url}/health/live",
            "interval": 180,  # 3 minutes
            "http_method": 1,  # HEAD
            "description": "Liveness probe for service availability",
        },
        {
            "friendly_name": "iSwitch Roofs CRM - Lead API",
            "url": f"{base_url}/api/leads",
            "interval": 600,  # 10 minutes
            "http_method": 1,  # HEAD
            "description": "Lead management API endpoint",
        },
        {
            "friendly_name": "iSwitch Roofs CRM - Metrics Endpoint",
            "url": f"{base_url}/metrics",
            "interval": 600,  # 10 minutes
            "http_method": 2,  # GET
            "description": "Application metrics endpoint",
        },
    ]

    created_monitors = []

    # Get existing monitors
    existing_monitors = client.get_monitors()
    existing_names = {m["friendly_name"]: m for m in existing_monitors}

    for config in monitors_config:
        monitor_name = config["friendly_name"]

        # Check if monitor already exists
        if monitor_name in existing_names:
            logger.info(f"Monitor already exists: {monitor_name}")
            created_monitors.append(existing_names[monitor_name])
            continue

        # Create new monitor
        monitor = client.create_monitor(
            friendly_name=config["friendly_name"],
            url=config["url"],
            interval=config["interval"],
            http_method=config["http_method"],
            alert_contacts=alert_contacts,
        )

        if monitor:
            created_monitors.append(monitor)

    return created_monitors


def main():
    """
    Main function to setup UptimeRobot monitoring
    """
    # Load configuration from environment
    api_key = os.getenv("UPTIMEROBOT_API_KEY")
    base_url = os.getenv("APP_BASE_URL", "https://api.iswitchroofs.com")

    if not api_key:
        logger.error("UPTIMEROBOT_API_KEY not set in environment")
        return

    logger.info(f"Setting up UptimeRobot monitors for: {base_url}")

    # Setup monitors
    monitors = setup_monitors(base_url, api_key)

    logger.info(f"Successfully configured {len(monitors)} monitors")

    # Print monitor details
    for monitor in monitors:
        logger.info(
            f"  - {monitor.get('friendly_name')}: {monitor.get('url')} "
            f"(Status: {monitor.get('status', 'N/A')})"
        )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    main()
