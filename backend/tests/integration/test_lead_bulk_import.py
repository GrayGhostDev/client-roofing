"""
iSwitch Roofs CRM - Lead Bulk Import Integration Tests
Version: 1.0.0

Tests for lead bulk import endpoint.
"""

import pytest
import json
import io
import pandas as pd
from uuid import uuid4
from unittest.mock import MagicMock, patch


class TestLeadBulkImport:
    """Test suite for lead bulk import functionality."""

    @pytest.mark.integration
    def test_bulk_import_csv_success(self, client, auth_headers, mock_supabase_client):
        """Test successful CSV import of leads."""
        # Create CSV data
        csv_data = """first_name,last_name,email,phone,source,street_address,city,state,zip_code
John,Doe,john@example.com,2485551234,website_form,123 Main St,Birmingham,MI,48009
Jane,Smith,jane@example.com,2485555678,google_ads,456 Oak Ave,Troy,MI,48084
Bob,Johnson,bob@example.com,2485559012,referral,789 Elm Dr,Rochester Hills,MI,48309"""

        # Mock successful inserts
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value.data = [
            {'id': str(uuid4()), 'first_name': 'John', 'last_name': 'Doe'},
            {'id': str(uuid4()), 'first_name': 'Jane', 'last_name': 'Smith'},
            {'id': str(uuid4()), 'first_name': 'Bob', 'last_name': 'Johnson'}
        ]

        response = client.post(
            '/api/leads/bulk-import',
            data={
                'file': (io.BytesIO(csv_data.encode()), 'leads.csv'),
                'skip_duplicates': 'true'
            },
            headers={**auth_headers, 'Content-Type': 'multipart/form-data'}
        )

        assert response.status_code == 201
        data = response.json()
        assert data['total_imported'] == 3
        assert data['success'] == 3
        assert data['failed'] == 0
        assert 'import_id' in data

    @pytest.mark.integration
    def test_bulk_import_excel_success(self, client, auth_headers, mock_supabase_client):
        """Test successful Excel import of leads."""
        # Create Excel data
        df = pd.DataFrame({
            'first_name': ['John', 'Jane'],
            'last_name': ['Doe', 'Smith'],
            'email': ['john@example.com', 'jane@example.com'],
            'phone': ['2485551234', '2485555678'],
            'source': ['website_form', 'google_ads'],
            'property_value': [550000, 450000]
        })

        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)

        # Mock successful inserts
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value.data = [
            {'id': str(uuid4()), 'first_name': 'John'},
            {'id': str(uuid4()), 'first_name': 'Jane'}
        ]

        response = client.post(
            '/api/leads/bulk-import',
            data={
                'file': (excel_buffer, 'leads.xlsx'),
                'auto_score': 'true'
            },
            headers={**auth_headers, 'Content-Type': 'multipart/form-data'}
        )

        assert response.status_code == 201
        data = response.json()
        assert data['total_imported'] == 2
        assert data['success'] == 2

    @pytest.mark.integration
    def test_bulk_import_with_validation_errors(self, client, auth_headers):
        """Test bulk import with validation errors in some rows."""
        csv_data = """first_name,last_name,email,phone,source
John,Doe,invalid-email,2485551234,website_form
Jane,Smith,jane@example.com,invalid-phone,google_ads
Bob,Johnson,bob@example.com,2485559012,invalid_source"""

        response = client.post(
            '/api/leads/bulk-import',
            data={
                'file': (io.BytesIO(csv_data.encode()), 'leads.csv'),
                'validate_strict': 'true'
            },
            headers={**auth_headers, 'Content-Type': 'multipart/form-data'}
        )

        assert response.status_code == 207  # Partial success
        data = response.json()
        assert data['failed'] > 0
        assert 'errors' in data
        assert len(data['errors']) > 0

    @pytest.mark.integration
    def test_bulk_import_duplicate_handling(self, client, auth_headers, mock_supabase_client):
        """Test duplicate handling during import."""
        csv_data = """first_name,last_name,email,phone,source
John,Doe,john@example.com,2485551234,website_form
John,Doe,john@example.com,2485551234,google_ads"""

        # Mock that first insert succeeds, second fails due to duplicate
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {'email': 'john@example.com'}  # Email already exists
        ]

        response = client.post(
            '/api/leads/bulk-import',
            data={
                'file': (io.BytesIO(csv_data.encode()), 'leads.csv'),
                'skip_duplicates': 'false'
            },
            headers={**auth_headers, 'Content-Type': 'multipart/form-data'}
        )

        data = response.json()
        assert data['duplicates'] > 0

    @pytest.mark.integration
    def test_bulk_import_with_auto_scoring(self, client, auth_headers, mock_supabase_client):
        """Test that bulk import automatically scores leads."""
        csv_data = """first_name,last_name,email,phone,source,property_value,zip_code
John,Doe,john@example.com,2485551234,website_form,650000,48009"""

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value.data = [{
            'id': str(uuid4()),
            'first_name': 'John',
            'lead_score': 85,  # High score due to property value and premium zip
            'temperature': 'hot'
        }]

        response = client.post(
            '/api/leads/bulk-import',
            data={
                'file': (io.BytesIO(csv_data.encode()), 'leads.csv'),
                'auto_score': 'true'
            },
            headers={**auth_headers, 'Content-Type': 'multipart/form-data'}
        )

        assert response.status_code == 201
        data = response.json()
        assert data['success'] == 1

    @pytest.mark.integration
    def test_bulk_import_file_size_limit(self, client, auth_headers):
        """Test file size limit for bulk import."""
        # Create a large CSV (simulate)
        large_csv = "first_name,last_name,email,phone,source\n"
        large_csv += "\n".join([f"User{i},Test{i},user{i}@example.com,248555{i:04d},website_form"
                                for i in range(10001)])  # Over 10000 rows

        response = client.post(
            '/api/leads/bulk-import',
            data={
                'file': (io.BytesIO(large_csv.encode()), 'large.csv')
            },
            headers={**auth_headers, 'Content-Type': 'multipart/form-data'}
        )

        assert response.status_code == 400
        assert 'limit' in response.json()['error'].lower()

    @pytest.mark.integration
    def test_bulk_import_invalid_file_format(self, client, auth_headers):
        """Test rejection of invalid file formats."""
        response = client.post(
            '/api/leads/bulk-import',
            data={
                'file': (io.BytesIO(b'not a csv or excel'), 'leads.txt')
            },
            headers={**auth_headers, 'Content-Type': 'multipart/form-data'}
        )

        assert response.status_code == 400
        assert 'format' in response.json()['error'].lower()

    @pytest.mark.integration
    def test_bulk_import_missing_required_fields(self, client, auth_headers):
        """Test import fails when required fields are missing."""
        csv_data = """email,source
john@example.com,website_form
jane@example.com,google_ads"""

        response = client.post(
            '/api/leads/bulk-import',
            data={
                'file': (io.BytesIO(csv_data.encode()), 'leads.csv')
            },
            headers={**auth_headers, 'Content-Type': 'multipart/form-data'}
        )

        assert response.status_code == 400
        data = response.json()
        assert 'required' in data['error'].lower()
        assert 'first_name' in data['error'].lower() or 'missing' in data['error'].lower()

    @pytest.mark.integration
    def test_bulk_import_with_mapping(self, client, auth_headers, mock_supabase_client):
        """Test bulk import with custom field mapping."""
        csv_data = """Name,Email Address,Phone Number,Lead Source
John Doe,john@example.com,2485551234,Website"""

        field_mapping = {
            'Name': 'full_name',
            'Email Address': 'email',
            'Phone Number': 'phone',
            'Lead Source': 'source'
        }

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value.data = [{
            'id': str(uuid4()),
            'first_name': 'John',
            'last_name': 'Doe'
        }]

        response = client.post(
            '/api/leads/bulk-import',
            data={
                'file': (io.BytesIO(csv_data.encode()), 'leads.csv'),
                'field_mapping': json.dumps(field_mapping)
            },
            headers={**auth_headers, 'Content-Type': 'multipart/form-data'}
        )

        assert response.status_code == 201
        data = response.json()
        assert data['success'] == 1

    @pytest.mark.integration
    def test_bulk_import_progress_tracking(self, client, auth_headers, mock_supabase_client):
        """Test that bulk import provides progress tracking."""
        csv_data = """first_name,last_name,email,phone,source
John,Doe,john@example.com,2485551234,website_form
Jane,Smith,jane@example.com,2485555678,google_ads"""

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value.data = [
            {'id': str(uuid4())},
            {'id': str(uuid4())}
        ]

        response = client.post(
            '/api/leads/bulk-import',
            data={
                'file': (io.BytesIO(csv_data.encode()), 'leads.csv'),
                'track_progress': 'true'
            },
            headers={**auth_headers, 'Content-Type': 'multipart/form-data'}
        )

        assert response.status_code == 201
        data = response.json()
        assert 'import_id' in data
        assert 'status_url' in data  # URL to check import status

    @pytest.mark.integration
    def test_bulk_import_without_auth(self, client):
        """Test that bulk import requires authentication."""
        csv_data = "first_name,last_name,email\nJohn,Doe,john@example.com"

        response = client.post(
            '/api/leads/bulk-import',
            data={
                'file': (io.BytesIO(csv_data.encode()), 'leads.csv')
            }
        )

        assert response.status_code in [401, 403]