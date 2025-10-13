"""
Reusable UI components for Streamlit dashboard
Version: 1.0.0
"""
import streamlit as st
from contextlib import contextmanager
from typing import Callable, Optional


@contextmanager
def loading_spinner(message: str = "Loading..."):
    """
    Context manager for loading spinner.

    Args:
        message: Message to display while loading

    Example:
        >>> with loading_spinner("Loading leads..."):
        ...     leads = api_client.get_leads()
    """
    placeholder = st.empty()
    with placeholder:
        with st.spinner(message):
            yield
    placeholder.empty()


def show_skeleton_loader(rows: int = 5):
    """
    Display skeleton loader while data loads.

    Args:
        rows: Number of skeleton rows to show

    Example:
        >>> show_skeleton_loader(rows=10)
    """
    st.markdown(
        """
        <style>
        @keyframes loading {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        .skeleton-loader {
            height: 50px;
            background: linear-gradient(
                90deg,
                #f0f0f0 25%,
                #e0e0e0 50%,
                #f0f0f0 75%
            );
            background-size: 200% 100%;
            animation: loading 1.5s infinite;
            margin: 10px 0;
            border-radius: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    for i in range(rows):
        st.markdown('<div class="skeleton-loader"></div>', unsafe_allow_html=True)


def show_empty_state(
    icon: str,
    message: str,
    action_label: Optional[str] = None,
    action_callback: Optional[Callable] = None,
    description: Optional[str] = None
):
    """
    Display empty state with optional action button.

    Args:
        icon: Emoji icon to display
        message: Main message to show
        action_label: Label for action button (optional)
        action_callback: Function to call when button is clicked (optional)
        description: Additional description text (optional)

    Example:
        >>> show_empty_state(
        ...     icon="📋",
        ...     message="No leads found",
        ...     description="Get started by creating your first lead",
        ...     action_label="Create First Lead",
        ...     action_callback=lambda: st.session_state.update({'show_create_form': True})
        ... )
    """
    st.markdown(
        f"""
        <div style="text-align: center; padding: 60px 20px;">
            <div style="font-size: 64px; margin-bottom: 20px;">{icon}</div>
            <h3 style="color: #666; margin-bottom: 10px;">{message}</h3>
            {f'<p style="color: #999; font-size: 14px;">{description}</p>' if description else ''}
        </div>
        """,
        unsafe_allow_html=True
    )

    if action_label and action_callback:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(action_label, key=f"empty_state_action_{action_label}"):
                action_callback()


def display_data_source_badge(mode: str = "demo", show_in_sidebar: bool = False):
    """
    Display data source badge (LIVE or DEMO).

    Args:
        mode: "live" or "demo"
        show_in_sidebar: If True, show in sidebar; else show in main area

    Example:
        >>> display_data_source_badge("live")
        # Shows: 🟢 LIVE DATA

        >>> display_data_source_badge("demo")
        # Shows: 🟡 DEMO MODE
    """
    container = st.sidebar if show_in_sidebar else st

    if mode == "live":
        container.success("🟢 **LIVE DATA**")
    else:
        container.warning("🟡 **DEMO MODE**")


def show_last_updated(timestamp: str = None, show_in_sidebar: bool = True):
    """
    Display last updated timestamp.

    Args:
        timestamp: Formatted timestamp string (uses current time if None)
        show_in_sidebar: If True, show in sidebar

    Example:
        >>> show_last_updated("2025-10-10 12:34:56")
    """
    from datetime import datetime

    if timestamp is None:
        timestamp = datetime.now().strftime('%H:%M:%S')

    container = st.sidebar if show_in_sidebar else st
    container.caption(f"🕐 Last updated: {timestamp}")


def create_metric_card(
    title: str,
    value: str,
    delta: Optional[str] = None,
    delta_color: str = "normal",
    icon: Optional[str] = None
):
    """
    Create a styled metric card.

    Args:
        title: Metric title
        value: Metric value
        delta: Change indicator (optional)
        delta_color: "normal", "inverse", or "off"
        icon: Emoji icon (optional)

    Example:
        >>> create_metric_card(
        ...     title="Total Leads",
        ...     value="142",
        ...     delta="+12 this week",
        ...     icon="📊"
        ... )
    """
    if icon:
        title = f"{icon} {title}"

    st.metric(label=title, value=value, delta=delta, delta_color=delta_color)


def show_info_banner(
    message: str,
    banner_type: str = "info",
    dismissable: bool = False,
    key: str = "info_banner"
):
    """
    Show informational banner at top of page.

    Args:
        message: Message to display
        banner_type: "info", "warning", "error", "success"
        dismissable: If True, show dismiss button
        key: Unique key for the banner

    Example:
        >>> show_info_banner(
        ...     "System maintenance scheduled for tonight",
        ...     banner_type="warning",
        ...     dismissable=True
        ... )
    """
    if dismissable:
        if f"{key}_dismissed" in st.session_state and st.session_state[f"{key}_dismissed"]:
            return

    banner_func = {
        "info": st.info,
        "warning": st.warning,
        "error": st.error,
        "success": st.success
    }.get(banner_type, st.info)

    col1, col2 = st.columns([10, 1])
    with col1:
        banner_func(message)

    if dismissable:
        with col2:
            if st.button("✖", key=f"{key}_dismiss_btn"):
                st.session_state[f"{key}_dismissed"] = True
                st.rerun()


def create_progress_bar(
    current: int,
    total: int,
    label: str = "Progress",
    show_percentage: bool = True
):
    """
    Create progress bar with label.

    Args:
        current: Current progress value
        total: Total value (100%)
        label: Label for progress bar
        show_percentage: If True, show percentage text

    Example:
        >>> create_progress_bar(
        ...     current=75,
        ...     total=100,
        ...     label="Lead Processing"
        ... )
    """
    percentage = (current / total * 100) if total > 0 else 0

    if show_percentage:
        st.caption(f"{label}: {percentage:.1f}% ({current}/{total})")
    else:
        st.caption(label)

    st.progress(min(percentage / 100, 1.0))


def show_status_indicator(
    status: str,
    status_map: Optional[dict] = None
):
    """
    Show colored status indicator.

    Args:
        status: Status value
        status_map: Optional mapping of status to (icon, color)

    Example:
        >>> show_status_indicator("completed", {
        ...     "completed": ("✅", "green"),
        ...     "pending": ("⏳", "orange"),
        ...     "failed": ("❌", "red")
        ... })
    """
    default_map = {
        "active": ("🟢", "green"),
        "inactive": ("⚫", "gray"),
        "pending": ("🟡", "orange"),
        "completed": ("✅", "green"),
        "failed": ("❌", "red"),
        "warning": ("⚠️", "orange")
    }

    mapping = status_map or default_map
    icon, color = mapping.get(status.lower(), ("⚪", "gray"))

    st.markdown(f"{icon} **{status.title()}**")


def create_collapsible_section(
    title: str,
    content_func: Callable,
    expanded: bool = False,
    icon: Optional[str] = None
):
    """
    Create collapsible section with title and content.

    Args:
        title: Section title
        content_func: Function that renders content
        expanded: If True, section is expanded by default
        icon: Optional emoji icon

    Example:
        >>> create_collapsible_section(
        ...     title="Advanced Filters",
        ...     content_func=lambda: render_filters(),
        ...     expanded=False,
        ...     icon="🔍"
        ... )
    """
    if icon:
        title = f"{icon} {title}"

    with st.expander(title, expanded=expanded):
        content_func()


def show_loading_overlay(message: str = "Processing..."):
    """
    Show full-page loading overlay.

    Args:
        message: Loading message

    Example:
        >>> show_loading_overlay("Generating report...")
    """
    st.markdown(
        f"""
        <div style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            flex-direction: column;
        ">
            <div style="font-size: 48px; margin-bottom: 20px;">⏳</div>
            <div style="font-size: 20px; color: #666;">{message}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def create_action_buttons(
    buttons: list[tuple[str, Callable]],
    layout: str = "horizontal"
):
    """
    Create group of action buttons.

    Args:
        buttons: List of (label, callback) tuples
        layout: "horizontal" or "vertical"

    Example:
        >>> create_action_buttons([
        ...     ("Save", save_data),
        ...     ("Cancel", cancel_action),
        ...     ("Delete", delete_data)
        ... ], layout="horizontal")
    """
    if layout == "horizontal":
        cols = st.columns(len(buttons))
        for col, (label, callback) in zip(cols, buttons):
            with col:
                if st.button(label, key=f"action_{label}"):
                    callback()
    else:
        for label, callback in buttons:
            if st.button(label, key=f"action_{label}", use_container_width=True):
                callback()
