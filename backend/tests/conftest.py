"""
iSwitch Roofs CRM - Pytest Configuration
Version: 1.0.0

Global fixtures and test configuration for all tests.
"""

import os
import sys
from typing import Generator, Dict, Any
from datetime import datetime
import pytest
from flask import Flask
from flask.testing import FlaskClient
import factory
from faker import Faker

# Add the parent directory to the path so we can import our app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.config import TestingConfig

# Initialize Faker for test data generation
fake = Faker()


@pytest.fixture(scope='session')
def app() -> Flask:
    """
    Create and configure a Flask app for testing.

    Returns:
        Flask: Configured Flask application for testing
    """
    app = create_app("testing")
    app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "DEBUG": False,
    })

    # Create application context
    with app.app_context():
        # Any app-level setup can go here
        yield app


@pytest.fixture(scope='function')
def client(app: Flask) -> FlaskClient:
    """
    Create a test client for the Flask app.

    Args:
        app: Flask application fixture

    Returns:
        FlaskClient: Test client for making requests
    """
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app: Flask):
    """
    Create a test runner for CLI commands.

    Args:
        app: Flask application fixture

    Returns:
        FlaskCliRunner: Test runner for CLI testing
    """
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def auth_headers() -> Dict[str, str]:
    """
    Create authentication headers with a valid JWT token.

    Returns:
        Dict: Headers with Authorization Bearer token
    """
    # This will be implemented when auth is ready
    # For now, return mock headers
    return {
        "Authorization": "Bearer mock_token_for_testing",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope='function')
def mock_supabase_client(mocker):
    """
    Mock Supabase client for testing without actual database.

    Args:
        mocker: Pytest mocker fixture

    Returns:
        Mock: Mocked Supabase client
    """
    mock_client = mocker.MagicMock()

    # Mock common Supabase operations
    mock_client.table.return_value.select.return_value.execute.return_value.data = []
    mock_client.table.return_value.insert.return_value.execute.return_value.data = [{}]
    mock_client.table.return_value.update.return_value.execute.return_value.data = [{}]
    mock_client.table.return_value.delete.return_value.execute.return_value.data = []

    mocker.patch('app.utils.supabase_client.get_supabase_client', return_value=mock_client)
    return mock_client


@pytest.fixture(scope='function')
def mock_pusher_client(mocker):
    """
    Mock Pusher client for testing real-time events.

    Args:
        mocker: Pytest mocker fixture

    Returns:
        Mock: Mocked Pusher client
    """
    mock_client = mocker.MagicMock()
    mock_client.trigger.return_value = True

    mocker.patch('app.utils.pusher_client.get_pusher_client', return_value=mock_client)
    return mock_client


@pytest.fixture(scope='function')
def sample_lead_data() -> Dict[str, Any]:
    """
    Generate sample lead data for testing.

    Returns:
        Dict: Sample lead data matching LeadCreate schema
    """
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "phone": fake.phone_number()[:15],
        "source": "website_form",
        "street_address": fake.street_address(),
        "city": fake.city(),
        "state": "MI",
        "zip_code": "48301",
        "property_value": 550000,
        "urgency": "immediate",
        "project_description": "Need complete roof replacement due to storm damage",
        "budget_range_min": 15000,
        "budget_range_max": 25000,
        "insurance_claim": True
    }


@pytest.fixture(scope='function')
def sample_customer_data() -> Dict[str, Any]:
    """
    Generate sample customer data for testing.

    Returns:
        Dict: Sample customer data
    """
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "phone": fake.phone_number()[:15],
        "street_address": fake.street_address(),
        "city": fake.city(),
        "state": "MI",
        "zip_code": "48301",
        "customer_type": "residential",
        "lifetime_value": 0,
        "total_projects": 0,
        "referral_source": "lead_conversion"
    }


@pytest.fixture(scope='function')
def sample_project_data() -> Dict[str, Any]:
    """
    Generate sample project data for testing.

    Returns:
        Dict: Sample project data
    """
    return {
        "customer_id": str(fake.uuid4()),
        "name": "Complete Roof Replacement",
        "description": "Full tear-off and replacement with architectural shingles",
        "status": "new",
        "project_type": "replacement",
        "estimated_value": 20000,
        "actual_value": None,
        "start_date": None,
        "end_date": None,
        "materials_cost": 8000,
        "labor_cost": 12000,
        "profit_margin": 40.0
    }


@pytest.fixture(autouse=True)
def reset_database():
    """
    Reset database state before each test.
    This is a placeholder for when we have actual database operations.
    """
    # Before test: setup
    yield
    # After test: teardown


@pytest.fixture
def mock_datetime(mocker):
    """
    Mock datetime for consistent testing.

    Args:
        mocker: Pytest mocker fixture

    Returns:
        Mock: Mocked datetime
    """
    mock_dt = mocker.patch('datetime.datetime')
    mock_dt.utcnow.return_value = datetime(2025, 1, 1, 12, 0, 0)
    mock_dt.now.return_value = datetime(2025, 1, 1, 12, 0, 0)
    return mock_dt


# Markers for categorizing tests
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "performance: Performance tests")