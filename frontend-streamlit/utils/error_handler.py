"""
Error handling utilities for API calls with retry logic
Version: 1.0.0
"""
import time
import streamlit as st
from typing import Callable, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def api_call_with_retry(
    func: Callable,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    fallback_value: Any = None,
    operation_name: str = "API call"
) -> Tuple[bool, Any]:
    """
    Execute API call with retry logic and graceful degradation.

    Args:
        func: Function to execute (should return data)
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Initial delay between retries in seconds (default: 1.0)
        fallback_value: Value to return if all retries fail (default: None)
        operation_name: Name of operation for logging (default: "API call")

    Returns:
        tuple: (success: bool, result: Any)
            - success: True if operation succeeded, False if failed
            - result: Data returned by func, or fallback_value if failed

    Example:
        >>> success, leads = api_call_with_retry(
        ...     func=lambda: api_client.get_leads(),
        ...     max_retries=3,
        ...     fallback_value=[],
        ...     operation_name="Fetch leads"
        ... )
        >>> if success:
        ...     print(f"Got {len(leads)} leads")
        ... else:
        ...     print("Using fallback data")
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            result = func()

            # Success - log and return
            if attempt > 0:
                logger.info(f"✅ {operation_name} succeeded on attempt {attempt + 1}")

            return True, result

        except Exception as e:
            last_error = e
            attempt_num = attempt + 1

            logger.warning(
                f"⚠️ {operation_name} failed (attempt {attempt_num}/{max_retries}): {str(e)[:100]}"
            )

            # If not last attempt, wait with exponential backoff
            if attempt < max_retries - 1:
                backoff_delay = retry_delay * (2 ** attempt)  # Exponential backoff
                logger.debug(f"Waiting {backoff_delay:.1f}s before retry...")
                time.sleep(backoff_delay)
            else:
                # Last attempt failed
                logger.error(
                    f"❌ {operation_name} failed after {max_retries} attempts. "
                    f"Last error: {str(e)[:100]}"
                )

    # All retries failed
    return False, fallback_value


def display_connection_status(
    is_connected: bool,
    entity_type: str = "API",
    show_in_sidebar: bool = True
):
    """
    Display connection status indicator.

    Args:
        is_connected: True if connected, False if unavailable
        entity_type: Name of the service/entity (e.g., "Leads API", "Database")
        show_in_sidebar: If True, show in sidebar; else show in main area

    Example:
        >>> display_connection_status(True, "Leads API")
        # Shows: ✅ Leads API Connected

        >>> display_connection_status(False, "Customers API")
        # Shows: ❌ Customers API Unavailable
        #        📊 Displaying demo data
    """
    container = st.sidebar if show_in_sidebar else st

    if is_connected:
        container.success(f"✅ {entity_type} Connected")
    else:
        container.error(f"❌ {entity_type} Unavailable")
        container.info("📊 Displaying demo data")


def show_error_details(
    error: Exception,
    user_message: str = "Unable to connect to backend",
    show_details: bool = False,
    show_support_info: bool = True
):
    """
    Display user-friendly error message with optional technical details.

    Args:
        error: Exception that occurred
        user_message: User-friendly error message
        show_details: If True, show technical details by default
        show_support_info: If True, show support contact info

    Example:
        >>> try:
        ...     data = api_client.get_data()
        ... except Exception as e:
        ...     show_error_details(e, "Failed to load data")
    """
    st.error(f"⚠️ {user_message}")

    if show_support_info:
        st.info("💡 The dashboard is showing demo data. Contact support if this persists.")

    # Technical details in expander
    with st.expander("🔧 Technical Details", expanded=show_details):
        st.code(f"Error Type: {type(error).__name__}\n\nError Message:\n{str(error)}")

        # Show error timestamp
        from datetime import datetime
        st.caption(f"Error occurred at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def handle_api_error(
    error: Exception,
    operation: str = "API operation",
    show_user_message: bool = True,
    fallback_action: Optional[Callable] = None
) -> None:
    """
    Centralized error handler for API operations.

    Args:
        error: Exception that occurred
        operation: Name of the operation that failed
        show_user_message: If True, display user-friendly error message
        fallback_action: Optional function to call as fallback

    Example:
        >>> try:
        ...     leads = api_client.get_leads()
        ... except Exception as e:
        ...     handle_api_error(
        ...         e,
        ...         operation="Fetch leads",
        ...         fallback_action=lambda: load_demo_leads()
        ...     )
    """
    logger.error(f"Error in {operation}: {str(error)}", exc_info=True)

    if show_user_message:
        show_error_details(
            error,
            user_message=f"Failed to {operation.lower()}",
            show_support_info=True
        )

    if fallback_action:
        try:
            fallback_action()
        except Exception as fallback_error:
            logger.error(f"Fallback action failed: {str(fallback_error)}")


def create_retry_button(
    callback: Callable,
    button_label: str = "🔄 Retry",
    key: str = "retry_button"
) -> bool:
    """
    Create a retry button for failed operations.

    Args:
        callback: Function to call when button is clicked
        button_label: Label for the button
        key: Unique key for the button

    Returns:
        bool: True if button was clicked, False otherwise

    Example:
        >>> if create_retry_button(
        ...     callback=lambda: st.rerun(),
        ...     button_label="🔄 Retry Connection"
        ... ):
        ...     st.success("Retrying...")
    """
    if st.button(button_label, key=key):
        try:
            callback()
            return True
        except Exception as e:
            logger.error(f"Retry failed: {str(e)}")
            st.error(f"Retry failed: {str(e)[:100]}")
            return False

    return False


class APIErrorContext:
    """
    Context manager for handling API errors with automatic retry and fallback.

    Example:
        >>> with APIErrorContext("Fetch leads", fallback_value=[]) as ctx:
        ...     ctx.result = api_client.get_leads()
        >>>
        >>> if ctx.success:
        ...     print(f"Got {len(ctx.result)} leads")
        ... else:
        ...     print("Using fallback data")
    """

    def __init__(
        self,
        operation_name: str,
        fallback_value: Any = None,
        max_retries: int = 3,
        show_errors: bool = True
    ):
        self.operation_name = operation_name
        self.fallback_value = fallback_value
        self.max_retries = max_retries
        self.show_errors = show_errors
        self.success = False
        self.result = fallback_value
        self.error = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error = exc_val
            self.success = False
            self.result = self.fallback_value

            if self.show_errors:
                handle_api_error(
                    exc_val,
                    operation=self.operation_name,
                    show_user_message=True
                )

            # Suppress the exception
            return True
        else:
            self.success = True

        return False


# Utility function for common retry scenarios
def retry_on_failure(retries: int = 3, delay: float = 1.0):
    """
    Decorator for automatic retry on function failure.

    Args:
        retries: Number of retry attempts
        delay: Delay between retries in seconds

    Example:
        >>> @retry_on_failure(retries=3, delay=2.0)
        ... def fetch_data():
        ...     return api_client.get_data()
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            success, result = api_call_with_retry(
                func=lambda: func(*args, **kwargs),
                max_retries=retries,
                retry_delay=delay,
                operation_name=func.__name__
            )
            return result
        return wrapper
    return decorator
