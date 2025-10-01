"""
iSwitch Roofs CRM - Validation Utilities
Version: 1.0.0
Date: 2025-10-01
"""

import re
from email_validator import validate_email, EmailNotValidError
import phonenumbers
from typing import Optional, Any, Dict
from datetime import datetime
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


def validate_uuid(uuid_string: str) -> bool:
    """
    Validate if a string is a valid UUID.

    Args:
        uuid_string: String to validate

    Returns:
        True if valid UUID, False otherwise
    """
    try:
        UUID(uuid_string)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def validate_email_address(email: str) -> tuple[bool, Optional[str]]:
    """
    Validate email address format.

    Args:
        email (str): Email address to validate

    Returns:
        tuple: (is_valid, normalized_email or error_message)
    """
    try:
        # Validate and get normalized email
        validation = validate_email(email, check_deliverability=False)
        return True, validation.normalized
    except EmailNotValidError as e:
        return False, str(e)


def validate_phone_number(phone: str, region: str = "US") -> tuple[bool, Optional[str]]:
    """
    Validate and format phone number.

    Args:
        phone (str): Phone number to validate
        region (str): Country code (default: "US")

    Returns:
        tuple: (is_valid, formatted_phone or error_message)
    """
    try:
        # Parse phone number
        parsed = phonenumbers.parse(phone, region)

        # Check if valid
        if not phonenumbers.is_valid_number(parsed):
            return False, "Invalid phone number"

        # Format in E164 format (+1234567890)
        formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        return True, formatted
    except phonenumbers.NumberParseException as e:
        return False, str(e)


def validate_zip_code(zip_code: str) -> tuple[bool, Optional[str]]:
    """
    Validate US ZIP code format (5 digits or 5+4 digits).

    Args:
        zip_code (str): ZIP code to validate

    Returns:
        tuple: (is_valid, normalized_zip or error_message)
    """
    # Remove any spaces or dashes
    zip_code = zip_code.replace(" ", "").replace("-", "")

    # Check for 5-digit or 9-digit format
    if re.match(r"^\d{5}$", zip_code):
        return True, zip_code
    elif re.match(r"^\d{9}$", zip_code):
        # Format as 12345-6789
        return True, f"{zip_code[:5]}-{zip_code[5:]}"
    else:
        return False, "ZIP code must be 5 or 9 digits"


def validate_state_code(state: str) -> tuple[bool, Optional[str]]:
    """
    Validate US state code.

    Args:
        state (str): State code (e.g., "MI", "CA")

    Returns:
        tuple: (is_valid, uppercase_state or error_message)
    """
    valid_states = {
        "AL",
        "AK",
        "AZ",
        "AR",
        "CA",
        "CO",
        "CT",
        "DE",
        "FL",
        "GA",
        "HI",
        "ID",
        "IL",
        "IN",
        "IA",
        "KS",
        "KY",
        "LA",
        "ME",
        "MD",
        "MA",
        "MI",
        "MN",
        "MS",
        "MO",
        "MT",
        "NE",
        "NV",
        "NH",
        "NJ",
        "NM",
        "NY",
        "NC",
        "ND",
        "OH",
        "OK",
        "OR",
        "PA",
        "RI",
        "SC",
        "SD",
        "TN",
        "TX",
        "UT",
        "VT",
        "VA",
        "WA",
        "WV",
        "WI",
        "WY",
        "DC",
    }

    state_upper = state.upper().strip()
    if state_upper in valid_states:
        return True, state_upper
    else:
        return False, "Invalid state code"


def validate_lead_score(score: int) -> tuple[bool, Optional[str]]:
    """
    Validate lead score (0-100).

    Args:
        score (int): Lead score

    Returns:
        tuple: (is_valid, error_message or None)
    """
    if not isinstance(score, int):
        return False, "Lead score must be an integer"

    if score < 0 or score > 100:
        return False, "Lead score must be between 0 and 100"

    return True, None


def validate_date_format(date_str: str, format: str = "%Y-%m-%d") -> tuple[bool, Optional[datetime]]:
    """
    Validate date string format.

    Args:
        date_str (str): Date string to validate
        format (str): Expected date format (default: "%Y-%m-%d")

    Returns:
        tuple: (is_valid, datetime_object or error_message)
    """
    try:
        date_obj = datetime.strptime(date_str, format)
        return True, date_obj
    except ValueError as e:
        return False, str(e)


def validate_budget_range(budget: str) -> tuple[bool, Optional[str]]:
    """
    Validate budget range string.

    Args:
        budget (str): Budget range (e.g., "10-15k", "20k_plus")

    Returns:
        tuple: (is_valid, normalized_budget or error_message)
    """
    valid_ranges = {
        "under_10k",
        "10-15k",
        "15-20k",
        "20k_plus",
    }

    budget_lower = budget.lower().strip()
    if budget_lower in valid_ranges:
        return True, budget_lower
    else:
        return False, f"Invalid budget range. Must be one of: {', '.join(valid_ranges)}"


def validate_urgency_level(urgency: str) -> tuple[bool, Optional[str]]:
    """
    Validate urgency level string.

    Args:
        urgency (str): Urgency level

    Returns:
        tuple: (is_valid, normalized_urgency or error_message)
    """
    valid_urgencies = {
        "immediate",
        "30_days",
        "90_days",
        "6_months",
        "exploratory",
    }

    urgency_lower = urgency.lower().strip()
    if urgency_lower in valid_urgencies:
        return True, urgency_lower
    else:
        return False, f"Invalid urgency level. Must be one of: {', '.join(valid_urgencies)}"


def validate_required_fields(data: Dict[str, Any], required_fields: list) -> tuple[bool, Optional[str]]:
    """
    Validate that all required fields are present and not empty.

    Args:
        data (dict): Data dictionary to validate
        required_fields (list): List of required field names

    Returns:
        tuple: (is_valid, error_message or None)
    """
    missing_fields = []

    for field in required_fields:
        if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            missing_fields.append(field)

    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"

    return True, None


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string input (trim, remove extra whitespace).

    Args:
        text (str): Text to sanitize
        max_length (int, optional): Maximum length to truncate to

    Returns:
        str: Sanitized text
    """
    if not text:
        return ""

    # Strip leading/trailing whitespace
    sanitized = text.strip()

    # Replace multiple spaces with single space
    sanitized = re.sub(r"\s+", " ", sanitized)

    # Truncate if max_length specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length].strip()

    return sanitized


def validate_url(url: str) -> tuple[bool, Optional[str]]:
    """
    Validate URL format.

    Args:
        url (str): URL to validate

    Returns:
        tuple: (is_valid, error_message or None)
    """
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    if url_pattern.match(url):
        return True, None
    else:
        return False, "Invalid URL format"


def validate_currency_amount(amount: float) -> tuple[bool, Optional[str]]:
    """
    Validate currency amount (must be positive).

    Args:
        amount (float): Amount to validate

    Returns:
        tuple: (is_valid, error_message or None)
    """
    if not isinstance(amount, (int, float)):
        return False, "Amount must be a number"

    if amount < 0:
        return False, "Amount cannot be negative"

    return True, None
