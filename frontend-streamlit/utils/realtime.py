"""
Real-Time Updates Utility for Streamlit Dashboard
Version: 2.0.0
Date: 2025-10-09

Provides auto-refresh and real-time event handling for Streamlit pages.
"""

import time
from datetime import datetime
from typing import Callable, Optional

import streamlit as st


def auto_refresh(interval_ms: int = 30000, key: str = "auto_refresh"):
    """
    Auto-refresh Streamlit page at specified interval

    Args:
        interval_ms: Refresh interval in milliseconds (default: 30 seconds)
        key: Unique key for this auto-refresh instance

    Usage:
        # At top of Streamlit page
        auto_refresh(interval_ms=30000)
    """
    # JavaScript for auto-refresh
    refresh_script = f"""
    <script>
        // Auto-refresh page every {interval_ms}ms
        setTimeout(function(){{
            window.parent.location.reload();
        }}, {interval_ms});
    </script>
    """

    st.markdown(refresh_script, unsafe_allow_html=True)


def display_last_updated(key: str = "last_updated"):
    """
    Display last updated timestamp

    Args:
        key: Session state key for storing timestamp
    """
    if key not in st.session_state:
        st.session_state[key] = datetime.now()

    st.caption(f"🔄 Last updated: {st.session_state[key].strftime('%I:%M:%S %p')}")


def create_refresh_button(
    callback: Optional[Callable] = None,
    label: str = "🔄 Refresh Now",
    key: str = "manual_refresh"
) -> bool:
    """
    Create manual refresh button

    Args:
        callback: Optional function to call on refresh
        label: Button label
        key: Unique key for button

    Returns:
        True if button was clicked
    """
    if st.button(label, key=key):
        st.session_state["last_updated"] = datetime.now()

        if callback:
            callback()

        st.rerun()
        return True

    return False


def check_api_status(api_client) -> dict:
    """
    Check API connection status

    Args:
        api_client: APIClient instance

    Returns:
        Status dictionary with connection info
    """
    try:
        health = api_client.health_check()

        if health.get("status") == "healthy":
            return {
                "connected": True,
                "status": "healthy",
                "message": "✅ Connected to backend"
            }
        else:
            return {
                "connected": False,
                "status": "unhealthy",
                "message": "⚠️ Backend degraded"
            }
    except Exception as e:
        return {
            "connected": False,
            "status": "offline",
            "message": f"❌ Backend offline: {str(e)}"
        }


def show_connection_status(api_client):
    """
    Display connection status banner

    Args:
        api_client: APIClient instance
    """
    status = check_api_status(api_client)

    if status["connected"]:
        st.success(status["message"])
    else:
        st.error(status["message"])
        st.info("💡 Make sure backend is running on http://localhost:8001")


def create_realtime_indicator(active: bool = True):
    """
    Create real-time status indicator

    Args:
        active: Whether real-time updates are active
    """
    if active:
        st.markdown("""
        <style>
        .realtime-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            background-color: #00ff00;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        </style>
        <div style="display: flex; align-items: center; gap: 8px;">
            <div class="realtime-indicator"></div>
            <span style="font-size: 12px; color: #888;">Live updates active</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px;">
            <div style="width: 10px; height: 10px; background-color: #ff0000; border-radius: 50%;"></div>
            <span style="font-size: 12px; color: #888;">Live updates paused</span>
        </div>
        """, unsafe_allow_html=True)


def fetch_with_fallback(fetch_func: Callable, fallback_data: dict = None) -> dict:
    """
    Fetch data with fallback to demo data if API fails

    Args:
        fetch_func: Function to fetch data from API
        fallback_data: Fallback data if fetch fails

    Returns:
        Data dictionary
    """
    try:
        data = fetch_func()

        if data:
            return {"success": True, "data": data, "source": "live"}
        else:
            return {"success": False, "data": fallback_data or {}, "source": "demo"}

    except Exception as e:
        st.warning(f"⚠️ API Error: {str(e)}. Showing demo data.")
        return {"success": False, "data": fallback_data or {}, "source": "demo"}


def display_data_source_badge(source: str = "live"):
    """
    Display badge indicating data source

    Args:
        source: Data source ("live", "demo", "cached")
    """
    colors = {
        "live": "#28a745",
        "demo": "#ffc107",
        "cached": "#17a2b8"
    }

    icons = {
        "live": "🟢",
        "demo": "🟡",
        "cached": "🔵"
    }

    color = colors.get(source, "#6c757d")
    icon = icons.get(source, "⚪")

    st.markdown(f"""
    <div style="
        display: inline-block;
        background-color: {color};
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
        margin-bottom: 10px;
    ">
        {icon} {source.upper()} DATA
    </div>
    """, unsafe_allow_html=True)


class RealtimeMetrics:
    """
    Class for managing real-time metrics display
    """

    def __init__(self, api_client):
        """Initialize with API client"""
        self.api_client = api_client
        self.last_update = None

    def get_snapshot(self) -> dict:
        """Get current real-time snapshot"""
        try:
            data = self.api_client.get_realtime_snapshot()
            self.last_update = datetime.now()
            return data
        except Exception as e:
            st.error(f"Failed to fetch real-time data: {str(e)}")
            return {}

    def display_metrics(self, metrics: dict):
        """Display real-time metrics in a compact format"""
        if not metrics:
            st.warning("No real-time data available")
            return

        # Create columns for metrics
        col1, col2, col3, col4 = st.columns(4)

        # Lead response time
        with col1:
            response = metrics.get("lead_response", {})
            avg_time = response.get("avg_response_time_seconds", 0)
            target = response.get("target_seconds", 120)

            if avg_time <= target:
                st.metric(
                    "Avg Response Time",
                    f"{int(avg_time)}s",
                    f"-{int(target - avg_time)}s vs target",
                    delta_color="normal"
                )
            else:
                st.metric(
                    "Avg Response Time",
                    f"{int(avg_time)}s",
                    f"+{int(avg_time - target)}s over target",
                    delta_color="inverse"
                )

        # Current month revenue
        with col2:
            revenue = metrics.get("revenue", {})
            current = revenue.get("revenue", 0)
            target_rev = revenue.get("target", 500000)
            progress = revenue.get("progress_percent", 0)

            st.metric(
                "Month Revenue",
                f"${current:,.0f}",
                f"{progress:.1f}% of target"
            )

        # Conversion rate
        with col3:
            conversion = metrics.get("conversion", {})
            rate = conversion.get("conversion_rate", 0)
            target_rate = conversion.get("target_rate", 25)

            st.metric(
                "Conversion Rate",
                f"{rate:.1f}%",
                f"{rate - target_rate:+.1f}% vs target"
            )

        # Status indicator
        with col4:
            status = metrics.get("status", "unknown")

            if status == "healthy":
                st.metric("System Status", "🟢 Healthy", "All systems operational")
            else:
                st.metric("System Status", "🟡 Degraded", "Some issues detected")

        # Show last update time
        if self.last_update:
            st.caption(f"🔄 Updated: {self.last_update.strftime('%I:%M:%S %p')}")


def setup_page_config(
    page_title: str,
    page_icon: str = "📊",
    layout: str = "wide",
    auto_refresh_interval: int = 30000
):
    """
    Setup page configuration with real-time updates

    Args:
        page_title: Page title
        page_icon: Page icon emoji
        layout: Layout mode (wide/centered)
        auto_refresh_interval: Auto-refresh interval in ms (0 to disable)
    """
    # Note: st.set_page_config must be called first, so this should be called
    # at the very top of the Streamlit script

    # Set page config (this should already be done in main script)
    # st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)

    # Add auto-refresh if enabled
    if auto_refresh_interval > 0:
        auto_refresh(interval_ms=auto_refresh_interval)

    # Initialize session state for real-time features
    if "realtime_enabled" not in st.session_state:
        st.session_state.realtime_enabled = True

    if "last_updated" not in st.session_state:
        st.session_state.last_updated = datetime.now()
