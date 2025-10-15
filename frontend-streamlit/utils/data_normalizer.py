"""
Data normalization utilities for API responses
Ensures consistent field names and data structures across the application
"""

from typing import Dict, List, Any
from datetime import datetime


def normalize_customer_fields(customer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize customer field names for UI consistency

    Backend may return different field names (status vs customer_status,
    project_count vs total_projects), this ensures consistency.

    Args:
        customer: Raw customer data from API

    Returns:
        dict: Normalized customer data
    """
    # Normalize status field
    customer['customer_status'] = customer.get('status', customer.get('customer_status', 'active'))

    # Normalize project count
    customer['total_projects'] = customer.get('project_count', customer.get('total_projects', 0))

    # Build full address from components
    address_parts = [
        customer.get('street_address', ''),
        customer.get('city', ''),
        customer.get('state', ''),
        customer.get('zip_code', '')
    ]
    customer['address'] = ' '.join(filter(None, address_parts)).strip()

    # Ensure required fields have defaults
    customer.setdefault('first_name', '')
    customer.setdefault('last_name', '')
    customer.setdefault('email', '')
    customer.setdefault('phone', '')
    customer.setdefault('lifetime_value', 0.0)
    customer.setdefault('property_type', 'residential')

    return customer


def normalize_lead_fields(lead: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize lead field names for UI consistency

    Args:
        lead: Raw lead data from API

    Returns:
        dict: Normalized lead data
    """
    # Normalize status field
    lead['lead_status'] = lead.get('status', lead.get('lead_status', 'new'))

    # Normalize source field
    lead['lead_source'] = lead.get('source', lead.get('lead_source', 'unknown'))

    # Ensure temperature field exists
    lead.setdefault('temperature', 'cold')
    lead.setdefault('score', 0)

    # Build full name
    first_name = lead.get('first_name', '')
    last_name = lead.get('last_name', '')
    lead['full_name'] = f"{first_name} {last_name}".strip()

    # Ensure required fields
    lead.setdefault('email', '')
    lead.setdefault('phone', '')
    lead.setdefault('notes', '')

    return lead


def normalize_project_fields(project: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize project field names for UI consistency

    Args:
        project: Raw project data from API

    Returns:
        dict: Normalized project data
    """
    # Normalize status field
    project['project_status'] = project.get('status', project.get('project_status', 'planning'))

    # Ensure value is float
    if 'value' in project:
        try:
            project['value'] = float(project['value'])
        except (ValueError, TypeError):
            project['value'] = 0.0

    project.setdefault('value', 0.0)
    project.setdefault('name', 'Untitled Project')
    project.setdefault('description', '')
    project.setdefault('customer_id', None)

    # Normalize date fields
    for date_field in ['start_date', 'end_date', 'completion_date']:
        if date_field in project and project[date_field]:
            # Ensure date is string format
            if isinstance(project[date_field], datetime):
                project[date_field] = project[date_field].isoformat()

    return project


def normalize_appointment_fields(appointment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize appointment field names for UI consistency

    Args:
        appointment: Raw appointment data from API

    Returns:
        dict: Normalized appointment data
    """
    # Normalize status field
    appointment['appointment_status'] = appointment.get(
        'status',
        appointment.get('appointment_status', 'scheduled')
    )

    appointment.setdefault('title', 'Appointment')
    appointment.setdefault('description', '')
    appointment.setdefault('location', '')
    appointment.setdefault('customer_id', None)
    appointment.setdefault('lead_id', None)

    # Normalize datetime fields
    for dt_field in ['scheduled_time', 'start_time', 'end_time']:
        if dt_field in appointment and appointment[dt_field]:
            if isinstance(appointment[dt_field], datetime):
                appointment[dt_field] = appointment[dt_field].isoformat()

    return appointment


def normalize_customer_list(customers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize a list of customers

    Args:
        customers: List of raw customer data

    Returns:
        list: List of normalized customers
    """
    return [normalize_customer_fields(c) for c in customers]


def normalize_lead_list(leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize a list of leads

    Args:
        leads: List of raw lead data

    Returns:
        list: List of normalized leads
    """
    return [normalize_lead_fields(l) for l in leads]


def normalize_project_list(projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize a list of projects

    Args:
        projects: List of raw project data

    Returns:
        list: List of normalized projects
    """
    return [normalize_project_fields(p) for p in projects]


def normalize_appointment_list(appointments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize a list of appointments

    Args:
        appointments: List of raw appointment data

    Returns:
        list: List of normalized appointments
    """
    return [normalize_appointment_fields(a) for a in appointments]


def extract_api_data(response: Dict[str, Any], key: str = None) -> Any:
    """
    Extract data from API response with multiple fallback keys

    Handles various API response formats:
    - {data: [...]}
    - {customers: [...], total: 10}
    - {leads: [...]}
    - Direct list [...]

    Args:
        response: API response dictionary
        key: Specific key to look for (e.g., 'customers', 'leads')

    Returns:
        Extracted data (list or dict)
    """
    if isinstance(response, list):
        return response

    if not isinstance(response, dict):
        return []

    # Try specific key first if provided
    if key and key in response:
        return response[key]

    # Common fallback keys
    fallback_keys = ['data', 'results', 'items']
    for fallback_key in fallback_keys:
        if fallback_key in response:
            return response[fallback_key]

    # If no standard key found, return empty list
    return []
