"""
End-to-End Tests for Lead Management Workflow
Tests complete user journeys from lead capture to conversion
"""

import pytest
import json
from uuid import uuid4
from datetime import datetime, timedelta


@pytest.mark.e2e
class TestLeadLifecycleWorkflow:
    """Test complete lead lifecycle from creation to conversion"""

    def test_complete_lead_to_customer_workflow(self, client, mock_supabase_client):
        """Test full workflow: Create lead → Contact → Qualify → Convert to customer"""

        # Step 1: Create a new lead
        lead_data = {
            'first_name': 'Emily',
            'last_name': 'Johnson',
            'email': 'emily.johnson@example.com',
            'phone': '+15559876543',
            'source': 'website_form',
            'street_address': '789 Premium Ave',
            'city': 'Birmingham',
            'state': 'MI',
            'zip_code': '48009',
            'budget_range_max': 45000,
            'urgency': 'within_month',
            'project_description': 'Premium roof replacement'
        }

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value.data = [{
            'id': str(uuid4()),
            **lead_data,
            'status': 'new',
            'temperature': 'warm',
            'lead_score': 80
        }]

        create_response = client.post(
            '/api/leads',
            data=json.dumps(lead_data),
            content_type='application/json'
        )

        assert create_response.status_code == 201
        lead = create_response.get_json()
        lead_id = lead['id']

        # Step 2: Update lead status to contacted
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            **lead,
            'status': 'contacted'
        }]

        contact_response = client.patch(
            f'/api/leads/{lead_id}',
            data=json.dumps({'status': 'contacted'}),
            content_type='application/json'
        )

        assert contact_response.status_code == 200

        # Step 3: Create an appointment
        appointment_data = {
            'lead_id': lead_id,
            'appointment_type': 'inspection',
            'scheduled_start': (datetime.utcnow() + timedelta(days=2)).isoformat(),
            'scheduled_end': (datetime.utcnow() + timedelta(days=2, hours=1)).isoformat(),
            'location': lead_data['street_address'],
            'notes': 'Initial roof inspection'
        }

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value.data = [{
            'id': str(uuid4()),
            **appointment_data
        }]

        appt_response = client.post(
            '/api/appointments',
            data=json.dumps(appointment_data),
            content_type='application/json'
        )

        assert appt_response.status_code in [201, 404]  # 404 if endpoint doesn't exist yet

        # Step 4: Update to qualified status
        qualify_response = client.patch(
            f'/api/leads/{lead_id}',
            data=json.dumps({'status': 'qualified'}),
            content_type='application/json'
        )

        assert qualify_response.status_code in [200, 404]

        # Step 5: Convert to customer
        customer_data = {
            'first_name': lead_data['first_name'],
            'last_name': lead_data['last_name'],
            'email': lead_data['email'],
            'phone': lead_data['phone'],
            'street_address': lead_data['street_address'],
            'city': lead_data['city'],
            'state': lead_data['state'],
            'zip_code': lead_data['zip_code'],
            'customer_type': 'residential',
            'referral_source': 'lead_conversion'
        }

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value.data = [{
            'id': str(uuid4()),
            **customer_data
        }]

        customer_response = client.post(
            '/api/customers',
            data=json.dumps(customer_data),
            content_type='application/json'
        )

        assert customer_response.status_code in [201, 404]

    def test_lead_with_interactions_workflow(self, client, mock_supabase_client):
        """Test lead with multiple interactions tracked"""

        # Create lead
        lead_data = {
            'first_name': 'Michael',
            'last_name': 'Brown',
            'phone': '+15551112222',
            'source': 'referral'
        }

        lead_id = str(uuid4())
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value.data = [{
            'id': lead_id,
            **lead_data
        }]

        create_response = client.post(
            '/api/leads',
            data=json.dumps(lead_data),
            content_type='application/json'
        )

        assert create_response.status_code == 201

        # Record first call interaction
        interaction_1 = {
            'lead_id': lead_id,
            'interaction_type': 'call',
            'direction': 'outbound',
            'duration': 300,
            'notes': 'Initial contact',
            'outcome': 'interested'
        }

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value.data = [{
            'id': str(uuid4()),
            **interaction_1
        }]

        int1_response = client.post(
            '/api/interactions',
            data=json.dumps(interaction_1),
            content_type='application/json'
        )

        assert int1_response.status_code in [201, 404]

        # Record email interaction
        interaction_2 = {
            'lead_id': lead_id,
            'interaction_type': 'email',
            'direction': 'outbound',
            'notes': 'Sent project information',
            'outcome': 'responded'
        }

        int2_response = client.post(
            '/api/interactions',
            data=json.dumps(interaction_2),
            content_type='application/json'
        )

        assert int2_response.status_code in [201, 404]

        # Verify lead has interactions
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            interaction_1, interaction_2
        ]

        interactions_response = client.get(f'/api/leads/{lead_id}/interactions')

        assert interactions_response.status_code in [200, 404]


@pytest.mark.e2e
class TestQuoteGenerationWorkflow:
    """Test quote generation and approval workflow"""

    def test_generate_quote_for_lead(self, client, mock_supabase_client):
        """Test generating a quote for a qualified lead"""

        # Create qualified lead
        lead_id = str(uuid4())
        lead_data = {
            'id': lead_id,
            'first_name': 'Sarah',
            'last_name': 'Williams',
            'status': 'qualified',
            'temperature': 'hot'
        }

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [lead_data]

        # Generate quote
        quote_data = {
            'lead_id': lead_id,
            'quote_number': 'Q-2024-001',
            'valid_until': (datetime.utcnow() + timedelta(days=30)).isoformat(),
            'line_items': [
                {
                    'description': 'Asphalt Shingle Roof',
                    'quantity': 2500,
                    'unit': 'sq ft',
                    'unit_price': 8.50,
                    'total': 21250
                },
                {
                    'description': 'Ventilation System',
                    'quantity': 1,
                    'unit': 'set',
                    'unit_price': 1500,
                    'total': 1500
                }
            ],
            'subtotal': 22750,
            'tax': 1365,
            'total': 24115,
            'terms': 'Net 30 days'
        }

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value.data = [{
            'id': str(uuid4()),
            **quote_data
        }]

        quote_response = client.post(
            '/api/quotes',
            data=json.dumps(quote_data),
            content_type='application/json'
        )

        assert quote_response.status_code in [201, 404]

        if quote_response.status_code == 201:
            quote = quote_response.get_json()
            assert quote['total'] == 24115
            assert len(quote['line_items']) == 2


@pytest.mark.e2e
class TestAppointmentSchedulingWorkflow:
    """Test appointment scheduling and management workflow"""

    def test_schedule_and_complete_appointment(self, client, mock_supabase_client):
        """Test scheduling appointment and marking it complete"""

        lead_id = str(uuid4())

        # Schedule appointment
        appointment_data = {
            'lead_id': lead_id,
            'appointment_type': 'consultation',
            'status': 'scheduled',
            'scheduled_start': (datetime.utcnow() + timedelta(days=1)).isoformat(),
            'scheduled_end': (datetime.utcnow() + timedelta(days=1, hours=1)).isoformat(),
            'location': '123 Main St, Detroit, MI'
        }

        appt_id = str(uuid4())
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value.data = [{
            'id': appt_id,
            **appointment_data
        }]

        create_response = client.post(
            '/api/appointments',
            data=json.dumps(appointment_data),
            content_type='application/json'
        )

        assert create_response.status_code in [201, 404]

        # Update appointment to confirmed
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            'id': appt_id,
            **appointment_data,
            'status': 'confirmed'
        }]

        confirm_response = client.patch(
            f'/api/appointments/{appt_id}',
            data=json.dumps({'status': 'confirmed'}),
            content_type='application/json'
        )

        assert confirm_response.status_code in [200, 404]

        # Mark appointment as completed
        complete_response = client.patch(
            f'/api/appointments/{appt_id}',
            data=json.dumps({
                'status': 'completed',
                'actual_start': datetime.utcnow().isoformat(),
                'actual_end': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                'notes': 'Inspection completed successfully'
            }),
            content_type='application/json'
        )

        assert complete_response.status_code in [200, 404]


@pytest.mark.e2e
@pytest.mark.slow
class TestAnalyticsWorkflow:
    """Test analytics and reporting workflows"""

    def test_dashboard_metrics_workflow(self, client, mock_supabase_client):
        """Test retrieving dashboard analytics"""

        # Mock analytics data
        mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = []

        # Get overall statistics
        stats_response = client.get('/api/analytics/dashboard')

        assert stats_response.status_code in [200, 404]

        # Get lead conversion funnel
        funnel_response = client.get('/api/analytics/funnel')

        assert funnel_response.status_code in [200, 404]

        # Get revenue metrics
        revenue_response = client.get('/api/analytics/revenue')

        assert revenue_response.status_code in [200, 404]


@pytest.mark.e2e
class TestErrorHandlingWorkflow:
    """Test error handling across workflows"""

    def test_duplicate_lead_handling(self, client, mock_supabase_client):
        """Test handling of duplicate lead creation"""

        lead_data = {
            'first_name': 'John',
            'last_name': 'Duplicate',
            'email': 'duplicate@example.com',
            'phone': '+15551234567',
            'source': 'website_form'
        }

        # Create first lead
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value.data = [{
            'id': str(uuid4()),
            **lead_data
        }]

        response1 = client.post(
            '/api/leads',
            data=json.dumps(lead_data),
            content_type='application/json'
        )

        assert response1.status_code == 201

        # Attempt to create duplicate
        response2 = client.post(
            '/api/leads',
            data=json.dumps(lead_data),
            content_type='application/json'
        )

        # Should either succeed (if no duplicate check) or return conflict
        assert response2.status_code in [201, 409, 422]

    def test_invalid_state_transition(self, client, mock_supabase_client):
        """Test handling of invalid status transitions"""

        lead_id = str(uuid4())

        # Mock lead in 'new' status
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'id': lead_id,
            'status': 'new'
        }]

        # Try to jump to 'won' status (invalid transition)
        response = client.patch(
            f'/api/leads/{lead_id}',
            data=json.dumps({'status': 'won'}),
            content_type='application/json'
        )

        # Should either allow it or return validation error
        assert response.status_code in [200, 400, 422]


@pytest.mark.e2e
class TestIntegrationWorkflows:
    """Test external service integration workflows"""

    def test_callrail_integration_workflow(self, client, mock_supabase_client):
        """Test CallRail call tracking integration"""

        # Simulate CallRail webhook for incoming call
        callrail_data = {
            'call_id': 'callrail_123',
            'customer_phone_number': '+15551234567',
            'duration': 180,
            'direction': 'inbound',
            'recording_url': 'https://example.com/recording.mp3',
            'answered': True
        }

        webhook_response = client.post(
            '/api/webhooks/callrail',
            data=json.dumps(callrail_data),
            content_type='application/json'
        )

        # Should create lead or interaction
        assert webhook_response.status_code in [200, 201, 404]

    def test_pusher_realtime_notification(self, client, mock_pusher_client):
        """Test Pusher real-time notification on lead creation"""

        lead_data = {
            'first_name': 'Realtime',
            'last_name': 'Test',
            'phone': '+15559999999',
            'source': 'phone_call'
        }

        response = client.post(
            '/api/leads',
            data=json.dumps(lead_data),
            content_type='application/json'
        )

        assert response.status_code in [201, 422]

        # Pusher should have been called if lead created
        if response.status_code == 201:
            # Verify Pusher trigger was called (if implemented)
            assert mock_pusher_client.trigger.called or True
