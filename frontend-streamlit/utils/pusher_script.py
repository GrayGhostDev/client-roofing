"""
Pusher Real-Time Integration for Streamlit
Version: 1.0.0
Date: 2025-10-09

Provides JavaScript injection for Pusher WebSocket connections in Streamlit.
"""

import os
import streamlit as st
from typing import List, Optional


def inject_pusher_script(
    channels: List[str] = None,
    pusher_key: str = None,
    pusher_cluster: str = "us2",
    debug: bool = False
):
    """
    Inject Pusher JavaScript client into Streamlit page

    Args:
        channels: List of channels to subscribe to (e.g., ['leads', 'customers'])
        pusher_key: Pusher application key (from environment if not provided)
        pusher_cluster: Pusher cluster (default: us2)
        debug: Enable Pusher debug logging

    Usage:
        # At top of Streamlit page (after auto_refresh)
        inject_pusher_script(
            channels=['leads', 'customers', 'projects'],
            debug=True
        )
    """
    # Get Pusher credentials from environment
    if pusher_key is None:
        pusher_key = os.getenv("PUSHER_KEY", "")

    if not pusher_key:
        st.warning("⚠️ Pusher key not configured. Real-time updates disabled.")
        return

    # Default channels if none provided
    if channels is None:
        channels = ["leads", "customers", "projects", "appointments", "analytics"]

    # Create channels JavaScript array
    channels_js = ",".join([f"'{ch}'" for ch in channels])

    # Pusher JavaScript injection
    pusher_html = f"""
    <script src="https://js.pusher.com/8.4.0-rc2/pusher.min.js"></script>
    <script>
        // Pusher Real-Time Configuration
        (function() {{
            // Check if Pusher is already initialized
            if (window.pusherInitialized) {{
                console.log('[Pusher] Already initialized, skipping...');
                return;
            }}

            console.log('[Pusher] Initializing Pusher client...');

            // Enable Pusher logging for debugging
            {'Pusher.logToConsole = true;' if debug else ''}

            // Initialize Pusher
            const pusher = new Pusher('{pusher_key}', {{
                cluster: '{pusher_cluster}',
                encrypted: true,
                authEndpoint: '/api/pusher/auth',  // For private channels
                forceTLS: true
            }});

            // Store pusher instance globally
            window.pusherClient = pusher;
            window.pusherInitialized = true;

            // Connection event handlers
            pusher.connection.bind('connected', function() {{
                console.log('[Pusher] ✅ Connected successfully');
                // Update connection status in DOM
                const statusEl = document.getElementById('pusher-status');
                if (statusEl) {{
                    statusEl.innerHTML = '🟢 Real-time connected';
                    statusEl.style.color = '#28a745';
                }}
            }});

            pusher.connection.bind('disconnected', function() {{
                console.log('[Pusher] ❌ Disconnected');
                const statusEl = document.getElementById('pusher-status');
                if (statusEl) {{
                    statusEl.innerHTML = '🔴 Real-time disconnected';
                    statusEl.style.color = '#dc3545';
                }}
            }});

            pusher.connection.bind('error', function(err) {{
                console.error('[Pusher] Connection error:', err);
            }});

            // Subscribe to channels
            const channelNames = [{channels_js}];
            const channels = {{}};

            channelNames.forEach(function(channelName) {{
                console.log('[Pusher] Subscribing to channel:', channelName);
                const channel = pusher.subscribe(channelName);
                channels[channelName] = channel;

                // Bind to all events on this channel
                channel.bind_global(function(eventName, data) {{
                    console.log('[Pusher] Event received:', channelName, eventName, data);

                    // Store event in session storage for Streamlit to pick up
                    try {{
                        const events = JSON.parse(sessionStorage.getItem('pusher_events') || '[]');
                        events.push({{
                            channel: channelName,
                            event: eventName,
                            data: data,
                            timestamp: new Date().toISOString()
                        }});

                        // Keep only last 50 events
                        if (events.length > 50) {{
                            events.shift();
                        }}

                        sessionStorage.setItem('pusher_events', JSON.stringify(events));

                        // Show toast notification
                        showPusherToast(eventName, data);

                        // Trigger page refresh if enabled
                        if (sessionStorage.getItem('pusher_auto_refresh') === 'true') {{
                            // Debounce refresh to avoid too many reloads
                            if (!window.pusherRefreshTimeout) {{
                                window.pusherRefreshTimeout = setTimeout(function() {{
                                    console.log('[Pusher] Triggering page refresh...');
                                    window.parent.location.reload();
                                    window.pusherRefreshTimeout = null;
                                }}, 2000);
                            }}
                        }}
                    }} catch (err) {{
                        console.error('[Pusher] Error processing event:', err);
                    }}
                }});
            }});

            // Store channels globally
            window.pusherChannels = channels;

            // Toast notification function
            function showPusherToast(eventName, data) {{
                // Create toast element
                const toast = document.createElement('div');
                toast.className = 'pusher-toast';

                // Determine toast color and icon based on event
                let color = '#17a2b8';
                let icon = '📢';
                let message = eventName;

                if (eventName.includes('created')) {{
                    color = '#28a745';
                    icon = '✨';
                    message = 'New ' + eventName.split(':')[0];
                }} else if (eventName.includes('updated')) {{
                    color = '#ffc107';
                    icon = '🔄';
                    message = 'Updated ' + eventName.split(':')[0];
                }} else if (eventName.includes('alert')) {{
                    color = '#dc3545';
                    icon = '⚠️';
                    message = 'Alert: ' + (data.title || eventName);
                }}

                toast.innerHTML = `
                    <div style="
                        position: fixed;
                        top: 80px;
                        right: 20px;
                        background: ${{color}};
                        color: white;
                        padding: 12px 20px;
                        border-radius: 8px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                        z-index: 9999;
                        font-size: 14px;
                        font-weight: 500;
                        animation: slideIn 0.3s ease-out;
                    ">
                        ${{icon}} ${{message}}
                    </div>
                    <style>
                        @keyframes slideIn {{
                            from {{ transform: translateX(400px); opacity: 0; }}
                            to {{ transform: translateX(0); opacity: 1; }}
                        }}
                    </style>
                `;

                document.body.appendChild(toast);

                // Remove toast after 3 seconds
                setTimeout(function() {{
                    toast.style.opacity = '0';
                    toast.style.transition = 'opacity 0.3s';
                    setTimeout(function() {{
                        document.body.removeChild(toast);
                    }}, 300);
                }}, 3000);
            }}

            console.log('[Pusher] Initialization complete');
        }})();
    </script>
    """

    # Inject the script
    st.markdown(pusher_html, unsafe_allow_html=True)

    # Add Pusher status indicator
    st.markdown("""
    <div id="pusher-status" style="
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 8px 16px;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        font-size: 12px;
        font-weight: 500;
        z-index: 1000;
    ">
        🔄 Connecting to real-time...
    </div>
    """, unsafe_allow_html=True)


def get_pusher_events() -> List[dict]:
    """
    Retrieve Pusher events from session storage

    Returns:
        List of recent Pusher events

    Note: This uses JavaScript to read from sessionStorage,
    so events are only available after page refresh
    """
    # In a real Streamlit app, you'd need to use st.session_state
    # or a custom component to bridge JavaScript -> Python

    # For now, return empty list and rely on auto-refresh to update data
    return []


def enable_pusher_auto_refresh(enabled: bool = True):
    """
    Enable/disable automatic page refresh on Pusher events

    Args:
        enabled: Whether to enable auto-refresh
    """
    script = f"""
    <script>
        sessionStorage.setItem('pusher_auto_refresh', '{str(enabled).lower()}');
        console.log('[Pusher] Auto-refresh', '{str(enabled).lower()}');
    </script>
    """
    st.markdown(script, unsafe_allow_html=True)


def pusher_status_indicator():
    """
    Display Pusher connection status in sidebar
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔄 Real-Time Status")

    # Add a placeholder that will be updated by JavaScript
    st.sidebar.markdown("""
    <div id="pusher-sidebar-status" style="
        padding: 10px;
        background: #f8f9fa;
        border-radius: 8px;
        text-align: center;
        font-size: 13px;
    ">
        <div class="realtime-indicator" style="
            display: inline-block;
            width: 8px;
            height: 8px;
            background-color: #ffc107;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        "></div>
        <span>Connecting...</span>

        <style>
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
        </style>
    </div>
    """, unsafe_allow_html=True)

    # Auto-refresh toggle
    auto_refresh_enabled = st.sidebar.checkbox(
        "Auto-refresh on events",
        value=True,
        help="Automatically refresh the page when real-time events are received"
    )

    enable_pusher_auto_refresh(auto_refresh_enabled)
