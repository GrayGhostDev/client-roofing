"""Pusher client utilities for Reflex frontend."""

import reflex as rx
from typing import Dict, Any


def pusher_script() -> rx.Component:
    """Include Pusher JavaScript library."""
    return rx.script(src="https://js.pusher.com/8.2.0/pusher.min.js")


def pusher_init_component() -> rx.Component:
    """Component to initialize Pusher connection on page load."""
    return rx.box(
        # Include Pusher library
        pusher_script(),

        # Initialize Pusher on component mount
        on_mount=rx.call_script("""
            // Wait for Pusher library to load
            function initPusher() {
                if (typeof window.Pusher !== 'undefined') {
                    console.log('Pusher library loaded, initializing...');
                    // Dispatch custom event to trigger state method
                    window.dispatchEvent(new CustomEvent('init-pusher'));
                } else {
                    console.log('Waiting for Pusher library...');
                    setTimeout(initPusher, 100);
                }
            }
            initPusher();
        """),

        # Hidden component, only for initialization
        display="none"
    )


def pusher_connection_status() -> rx.Component:
    """Component to show Pusher connection status."""
    return rx.hstack(
        rx.icon(
            "wifi",
            size=16,
            color="gray",
            id="pusher-status-icon"
        ),
        rx.text(
            "Real-time Starting...",
            size="1",
            color="gray",
            id="pusher-status-text"
        ),
        spacing="1",
        align_items="center"
    )


def pusher_event_listeners() -> rx.Component:
    """Component to set up Pusher event listeners (frontend-only mode)."""

    return rx.box(
        # Add event listeners for custom Pusher events (frontend-only mode)
        on_mount=rx.call_script("""
            // Custom event listeners for Pusher events (frontend-only mode)
            window.addEventListener('init-pusher', function() {
                console.log('Pusher init event received (frontend-only mode)');
                // In frontend-only mode, connect directly to external API
                try {
                    // Try to connect to external backend API at localhost:8001
                    fetch('http://localhost:8001/api/health')
                        .then(response => {
                            if (response.ok) {
                                console.log('External API connected');
                                document.getElementById('pusher-status-text').textContent = 'API Connected';
                                document.getElementById('pusher-status-icon').style.color = 'green';
                            } else {
                                console.log('External API not available');
                                document.getElementById('pusher-status-text').textContent = 'API Offline';
                                document.getElementById('pusher-status-icon').style.color = 'orange';
                            }
                        })
                        .catch(error => {
                            console.log('External API connection failed:', error);
                            document.getElementById('pusher-status-text').textContent = 'API Offline';
                            document.getElementById('pusher-status-icon').style.color = 'red';
                        });
                } catch (error) {
                    console.log('API connection error:', error);
                }
            });

            window.addEventListener('pusher-connected', function() {
                console.log('Pusher connected (frontend-only mode)');
                document.getElementById('pusher-status-text').textContent = 'Real-time Connected';
                document.getElementById('pusher-status-icon').style.color = 'green';
            });

            window.addEventListener('pusher-disconnected', function() {
                console.log('Pusher disconnected (frontend-only mode)');
                document.getElementById('pusher-status-text').textContent = 'Real-time Disconnected';
                document.getElementById('pusher-status-icon').style.color = 'red';
            });

            window.addEventListener('pusher-notification', function(event) {
                console.log('Pusher notification received:', event.detail);
                // Handle notifications in frontend-only mode
            });

            window.addEventListener('pusher-lead-created', function(event) {
                console.log('New lead created:', event.detail);
                // Handle new leads in frontend-only mode
            });

            window.addEventListener('pusher-lead-updated', function(event) {
                console.log('Lead updated:', event.detail);
                // Handle lead updates in frontend-only mode
            });

            console.log('Pusher event listeners set up (frontend-only mode)');
        """),

        # Hidden component, only for event handling
        display="none"
    )