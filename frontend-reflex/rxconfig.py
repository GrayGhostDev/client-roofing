import reflex as rx

config = rx.Config(
    app_name="frontend_reflex",
    # Backend connection for API calls
    backend_port=8002,
    frontend_port=3000,
    # State manager configuration for working dashboard
    state_manager_mode="memory",  # Use in-memory state for development
    # Performance settings
    compile=True,
    telemetry_enabled=False,
    # Disable sitemap plugin to remove warnings
    disable_plugins=['reflex.plugins.sitemap.SitemapPlugin'],
)