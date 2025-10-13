"""
Performance monitoring utilities
Version: 1.0.0
"""
import time
import streamlit as st
from functools import wraps
from typing import Callable, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def measure_time(func_name: str = None, threshold_warning: float = 2.0):
    """
    Decorator to measure function execution time.

    Args:
        func_name: Optional custom name for the function (uses func.__name__ if not provided)
        threshold_warning: Show warning if execution time exceeds this (in seconds)

    Example:
        >>> @measure_time("Fetch leads", threshold_warning=1.0)
        ... def get_leads():
        ...     return api_client.get_leads()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start

            name = func_name or func.__name__
            logger.info(f"⏱️ {name}: {elapsed:.3f}s")

            # Store in session state for display
            if 'performance_metrics' not in st.session_state:
                st.session_state.performance_metrics = {}

            st.session_state.performance_metrics[name] = {
                'elapsed': elapsed,
                'timestamp': datetime.now()
            }

            # Show slow queries warning
            if elapsed > threshold_warning:
                st.warning(f"⚠️ Slow operation: {name} took {elapsed:.1f}s")

            return result
        return wrapper
    return decorator


class PerformanceTimer:
    """
    Context manager for measuring code block execution time.

    Example:
        >>> with PerformanceTimer("Load data") as timer:
        ...     data = load_large_dataset()
        >>> print(f"Loaded in {timer.elapsed:.2f}s")
    """

    def __init__(self, operation_name: str, log_result: bool = True):
        self.operation_name = operation_name
        self.log_result = log_result
        self.start_time = None
        self.elapsed = 0

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.time() - self.start_time

        if self.log_result:
            logger.info(f"⏱️ {self.operation_name}: {self.elapsed:.3f}s")

        # Store in session state
        if 'performance_metrics' not in st.session_state:
            st.session_state.performance_metrics = {}

        st.session_state.performance_metrics[self.operation_name] = {
            'elapsed': self.elapsed,
            'timestamp': datetime.now()
        }

        return False


def display_performance_metrics(show_in_sidebar: bool = True, expanded: bool = False):
    """
    Display performance metrics in an expander.

    Args:
        show_in_sidebar: If True, show in sidebar; else show in main area
        expanded: If True, expander is open by default

    Example:
        >>> display_performance_metrics(show_in_sidebar=True, expanded=False)
    """
    container = st.sidebar if show_in_sidebar else st

    if 'performance_metrics' not in st.session_state or not st.session_state.performance_metrics:
        return

    with container.expander("📊 Performance Metrics", expanded=expanded):
        # Page load time
        page_load_time = st.session_state.get('page_load_time', 0)
        if page_load_time > 0:
            st.metric("Page Load Time", f"{page_load_time:.2f}s")

        # API response time
        api_response_time = st.session_state.get('api_response_time', 0)
        if api_response_time > 0:
            st.metric("API Response Time", f"{api_response_time:.0f}ms")

        # Record count
        record_count = st.session_state.get('record_count', 0)
        if record_count > 0:
            st.metric("Records Loaded", record_count)

        # Individual operation metrics
        metrics = st.session_state.performance_metrics
        if metrics:
            st.caption("Recent Operations:")
            for operation, data in list(metrics.items())[-5:]:  # Show last 5
                elapsed = data['elapsed']
                color = "🟢" if elapsed < 0.5 else "🟡" if elapsed < 2.0 else "🔴"
                st.caption(f"{color} {operation}: {elapsed:.3f}s")


def track_page_load():
    """
    Track page load time by measuring from session start.
    Call this at the beginning of each page.

    Example:
        >>> track_page_load()
        >>> # ... rest of page code
    """
    if 'page_start_time' not in st.session_state:
        st.session_state.page_start_time = time.time()

    # Calculate page load time
    current_time = time.time()
    st.session_state.page_load_time = current_time - st.session_state.page_start_time


def track_api_call(func: Callable, operation_name: str = "API call") -> Any:
    """
    Track API call performance and store metrics.

    Args:
        func: API function to call
        operation_name: Name of the operation for tracking

    Returns:
        Result from the API call

    Example:
        >>> leads = track_api_call(
        ...     lambda: api_client.get_leads(),
        ...     operation_name="Fetch leads"
        ... )
    """
    start = time.time()

    try:
        result = func()
        elapsed = (time.time() - start) * 1000  # Convert to milliseconds

        # Store metrics
        st.session_state.api_response_time = elapsed

        # Log if slow
        if elapsed > 500:
            logger.warning(f"Slow API call ({operation_name}): {elapsed:.0f}ms")

        return result

    except Exception as e:
        elapsed = (time.time() - start) * 1000
        logger.error(f"API call failed ({operation_name}) after {elapsed:.0f}ms: {str(e)}")
        raise


def get_performance_summary() -> dict:
    """
    Get summary of performance metrics.

    Returns:
        dict: Performance summary with averages and totals

    Example:
        >>> summary = get_performance_summary()
        >>> print(f"Average load time: {summary['avg_load_time']:.2f}s")
    """
    metrics = st.session_state.get('performance_metrics', {})

    if not metrics:
        return {
            'avg_load_time': 0,
            'total_operations': 0,
            'slowest_operation': None,
            'fastest_operation': None
        }

    times = [m['elapsed'] for m in metrics.values()]
    operations = list(metrics.keys())

    summary = {
        'avg_load_time': sum(times) / len(times) if times else 0,
        'total_operations': len(metrics),
        'slowest_operation': operations[times.index(max(times))] if times else None,
        'fastest_operation': operations[times.index(min(times))] if times else None,
        'total_time': sum(times)
    }

    return summary


def clear_performance_metrics():
    """
    Clear all stored performance metrics.
    Useful for resetting tracking on new page load.

    Example:
        >>> clear_performance_metrics()
    """
    if 'performance_metrics' in st.session_state:
        st.session_state.performance_metrics = {}

    st.session_state.page_load_time = 0
    st.session_state.api_response_time = 0
    st.session_state.record_count = 0


def show_performance_warning(threshold_ms: float = 500):
    """
    Show performance warning if API calls are slow.

    Args:
        threshold_ms: Threshold in milliseconds to trigger warning

    Example:
        >>> show_performance_warning(threshold_ms=1000)
    """
    api_time = st.session_state.get('api_response_time', 0)

    if api_time > threshold_ms:
        st.warning(
            f"⚠️ Slow API response detected ({api_time:.0f}ms). "
            f"Consider optimizing database queries or adding indexes."
        )


def benchmark_operation(func: Callable, iterations: int = 10, name: str = "Operation") -> dict:
    """
    Benchmark an operation by running it multiple times.

    Args:
        func: Function to benchmark
        iterations: Number of times to run the function
        name: Name of the operation

    Returns:
        dict: Benchmark results with min, max, avg, median times

    Example:
        >>> results = benchmark_operation(
        ...     lambda: api_client.get_leads(),
        ...     iterations=5,
        ...     name="Get Leads"
        ... )
        >>> print(f"Average: {results['avg']:.3f}s")
    """
    times = []

    with st.spinner(f"Benchmarking {name} ({iterations} iterations)..."):
        for i in range(iterations):
            start = time.time()
            func()
            elapsed = time.time() - start
            times.append(elapsed)

    times.sort()

    results = {
        'min': min(times),
        'max': max(times),
        'avg': sum(times) / len(times),
        'median': times[len(times) // 2],
        'total': sum(times),
        'iterations': iterations
    }

    logger.info(f"Benchmark {name}: {results}")

    return results
