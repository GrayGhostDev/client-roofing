"""
Validation Utilities
Version: 1.0.0

Request validation utilities for API endpoints.
"""

import logging
from functools import wraps
from typing import Any

from flask import jsonify, request
from pydantic import ValidationError

logger = logging.getLogger(__name__)


def validate_request(model: type[Any]):
    """
    Decorator to validate request data against a Pydantic model.

    Args:
        model: Pydantic model class to validate against

    Returns:
        Decorator function
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get JSON data from request
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"error": "No data provided"}), 400
            except Exception:
                return jsonify({"error": "Invalid JSON data"}), 400

            # Validate against model
            try:
                validated = model(**data)
                # Convert back to dict for use in endpoint
                request.validated_data = validated.model_dump()
            except ValidationError as e:
                errors = []
                for error in e.errors():
                    field = ".".join(str(loc) for loc in error["loc"])
                    message = error["msg"]
                    errors.append(f"{field}: {message}")

                return jsonify({"error": "Validation failed", "details": errors}), 400

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def validate_uuid(uuid_string: str) -> bool:
    """
    Validate UUID format.

    Args:
        uuid_string: String to validate

    Returns:
        True if valid UUID
    """
    import re

    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
    )
    return bool(uuid_pattern.match(uuid_string))


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if valid email
    """
    import re

    email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    return bool(email_pattern.match(email))


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.

    Args:
        phone: Phone number to validate

    Returns:
        True if valid phone
    """
    import re

    # Remove non-digits except +
    cleaned = re.sub(r"[^\d+]", "", phone)

    # Check if it's a valid format
    if cleaned.startswith("+"):
        # International format
        return len(cleaned) >= 10 and len(cleaned) <= 16
    else:
        # Assume US format
        return len(cleaned) == 10 or (len(cleaned) == 11 and cleaned.startswith("1"))


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent XSS and injection.

    Args:
        text: Input text to sanitize

    Returns:
        Sanitized text
    """
    import html

    if not text:
        return text

    # HTML escape special characters
    sanitized = html.escape(text)

    # Remove any script tags (extra safety)
    import re

    sanitized = re.sub(r"<script[^>]*>.*?</script>", "", sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r"javascript:", "", sanitized, flags=re.IGNORECASE)

    return sanitized.strip()


def validate_pagination_params(page: int = 1, per_page: int = 50, max_per_page: int = 100) -> tuple:
    """
    Validate and normalize pagination parameters.

    Args:
        page: Page number
        per_page: Items per page
        max_per_page: Maximum allowed items per page

    Returns:
        Tuple of (page, per_page)
    """
    # Ensure positive integers
    page = max(1, int(page))
    per_page = max(1, min(int(per_page), max_per_page))

    return page, per_page


def validate_sort_params(sort: str, allowed_fields: list) -> tuple:
    """
    Validate and parse sort parameters.

    Args:
        sort: Sort string (field:direction)
        allowed_fields: List of allowed sort fields

    Returns:
        Tuple of (field, direction)
    """
    if not sort:
        return None, None

    try:
        parts = sort.split(":")
        field = parts[0]
        direction = parts[1] if len(parts) > 1 else "asc"

        # Validate field
        if field not in allowed_fields:
            return None, None

        # Validate direction
        if direction not in ["asc", "desc"]:
            direction = "asc"

        return field, direction

    except Exception:
        return None, None


def validate_date_range(start_date: str, end_date: str) -> tuple:
    """
    Validate and parse date range.

    Args:
        start_date: Start date string
        end_date: End date string

    Returns:
        Tuple of (start_datetime, end_datetime) or (None, None)
    """
    from datetime import datetime

    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        # Ensure start is before end
        if start and end and start > end:
            start, end = end, start

        return start, end

    except Exception:
        return None, None
