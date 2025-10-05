"""
End-to-End (E2E) Testing for iSwitch Roofs CRM
Tests complete business workflows from lead to customer conversion
"""

import pytest
import json
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from flask import Flask
from flask.testing import FlaskClient


class TestLeadToCustomerWorkflow:
    """Test complete lead to customer conversion workflow."""

    def test_complete_lead_conversion_workflow(self, client: FlaskClient, auth_headers):
        """Test the complete workflow from lead creation to customer conversion."""

        # Step 1: Create a new lead
        lead_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '555-1234',
            'source': 'website_form',
            'street_address': '123 Main St',
            'city': 'Birmingham',
            'state': 'MI',
            'zip_code': '48301',
            'property_value': 650000,
            'urgency': 'high',
            'project_description': 'Complete roof replacement needed',
            'budget_range_min': 20000,
            'budget_range_max': 35000,
            'insurance_claim': True
        }

        with patch('app.services.lead_service.create_lead') as mock_create_lead:
            mock_create_lead.return_value = {
                'id': 'lead-12345',
                **lead_data,
                'status': 'new',
                'lead_score': 85,
                'temperature': 'hot',
                'created_at': datetime.utcnow().isoformat()
            }

            response = client.post('/api/leads', data=json.dumps(lead_data), headers=auth_headers)
            assert response.status_code == 201

            lead = json.loads(response.data)
            lead_id = lead['id']
            assert lead['lead_score'] >= 80  # High-value lead

        # Step 2: Schedule initial consultation appointment
        appointment_data = {
            'title': 'Initial Roof Consultation',
            'description': 'Meet with homeowner to assess roof condition',
            'appointment_type': 'consultation',
            'scheduled_date': (datetime.utcnow() + timedelta(days=2)).isoformat(),
            'duration_minutes': 120,
            'entity_type': 'lead',
            'entity_id': lead_id,
            'assigned_to': 'sales-rep-1',
            'location': '123 Main St, Birmingham, MI 48301'
        }

        with patch('app.services.appointments_service.create_appointment') as mock_create_apt:
            mock_create_apt.return_value = {
                'id': 'apt-001',
                **appointment_data,
                'status': 'scheduled',
                'created_at': datetime.utcnow().isoformat()
            }

            response = client.post('/api/appointments', data=json.dumps(appointment_data), headers=auth_headers)
            assert response.status_code == 201

            appointment = json.loads(response.data)
            appointment_id = appointment['id']

        # Step 3: Add interaction notes from initial contact
        interaction_data = {
            'entity_type': 'lead',
            'entity_id': lead_id,
            'interaction_type': 'call',
            'subject': 'Initial contact - roof assessment needed',
            'content': 'Spoke with homeowner. Storm damage to roof, insurance claim approved. Very motivated to proceed quickly.',
            'follow_up_date': (datetime.utcnow() + timedelta(days=1)).isoformat()
        }

        with patch('app.services.interaction_service.create_interaction') as mock_create_interaction:
            mock_create_interaction.return_value = {
                'id': 'interaction-001',
                **interaction_data,
                'created_at': datetime.utcnow().isoformat(),
                'created_by': 'sales-rep-1'
            }

            response = client.post('/api/interactions', data=json.dumps(interaction_data), headers=auth_headers)
            assert response.status_code == 201

        # Step 4: Update lead status after qualification
        status_update = {
            'status': 'qualified',
            'temperature': 'hot',
            'lead_score': 92,
            'notes': 'High-value prospect with approved insurance claim'
        }

        with patch('app.services.lead_service.update_lead') as mock_update_lead:
            mock_update_lead.return_value = {
                **lead,
                **status_update,
                'updated_at': datetime.utcnow().isoformat()
            }

            response = client.put(f'/api/leads/{lead_id}', data=json.dumps(status_update), headers=auth_headers)
            assert response.status_code == 200

            updated_lead = json.loads(response.data)
            assert updated_lead['status'] == 'qualified'
            assert updated_lead['lead_score'] == 92

        # Step 5: Complete appointment and create project estimate
        appointment_completion = {
            'status': 'completed',
            'completion_notes': 'Roof assessment completed. Full replacement recommended. Customer very interested.',
            'estimated_project_value': 28500,
            'next_steps': 'Prepare detailed estimate and material selection'
        }

        with patch('app.services.appointments_service.update_appointment') as mock_update_apt:
            mock_update_apt.return_value = {
                **appointment,
                **appointment_completion,
                'completed_at': datetime.utcnow().isoformat()
            }

            response = client.put(f'/api/appointments/{appointment_id}',
                                data=json.dumps(appointment_completion), headers=auth_headers)
            assert response.status_code == 200

        # Step 6: Create project for the qualified lead
        project_data = {
            'lead_id': lead_id,
            'name': 'Complete Roof Replacement - 123 Main St',
            'description': 'Full tear-off and replacement with architectural shingles',
            'project_type': 'replacement',
            'estimated_value': 28500,
            'materials_cost': 12000,
            'labor_cost': 14000,
            'profit_margin': 45.0,
            'estimated_start_date': (datetime.utcnow() + timedelta(days=14)).isoformat(),
            'estimated_completion_date': (datetime.utcnow() + timedelta(days=21)).isoformat()
        }

        with patch('app.services.project_service.create_project') as mock_create_project:
            mock_create_project.return_value = {
                'id': 'project-001',
                **project_data,
                'status': 'proposal',
                'created_at': datetime.utcnow().isoformat()
            }

            response = client.post('/api/projects', data=json.dumps(project_data), headers=auth_headers)
            assert response.status_code == 201

            project = json.loads(response.data)
            project_id = project['id']

        # Step 7: Convert lead to customer after project acceptance
        customer_data = {
            'first_name': lead['first_name'],
            'last_name': lead['last_name'],
            'email': lead['email'],
            'phone': lead['phone'],
            'street_address': lead['street_address'],
            'city': lead['city'],
            'state': lead['state'],
            'zip_code': lead['zip_code'],
            'customer_type': 'residential',
            'converted_from_lead_id': lead_id,
            'referral_source': 'lead_conversion'
        }

        with patch('app.services.customer_service.create_customer') as mock_create_customer:
            mock_create_customer.return_value = {
                'id': 'customer-001',
                **customer_data,
                'lifetime_value': 28500,
                'total_projects': 1,
                'customer_status': 'active',
                'created_at': datetime.utcnow().isoformat()
            }

            response = client.post('/api/customers', data=json.dumps(customer_data), headers=auth_headers)
            assert response.status_code == 201

            customer = json.loads(response.data)
            customer_id = customer['id']

        # Step 8: Update project with customer ID and approve
        project_update = {
            'customer_id': customer_id,
            'status': 'approved',
            'actual_value': 28500,
            'start_date': (datetime.utcnow() + timedelta(days=7)).isoformat()
        }

        with patch('app.services.project_service.update_project') as mock_update_project:
            mock_update_project.return_value = {
                **project,
                **project_update,
                'updated_at': datetime.utcnow().isoformat()
            }

            response = client.put(f'/api/projects/{project_id}',
                                data=json.dumps(project_update), headers=auth_headers)
            assert response.status_code == 200

        # Step 9: Update lead status to converted
        conversion_update = {
            'status': 'converted',
            'converted_to_customer_id': customer_id,
            'conversion_date': datetime.utcnow().isoformat()
        }

        with patch('app.services.lead_service.update_lead') as mock_final_update:
            mock_final_update.return_value = {
                **updated_lead,
                **conversion_update,
                'updated_at': datetime.utcnow().isoformat()
            }

            response = client.put(f'/api/leads/{lead_id}',
                                data=json.dumps(conversion_update), headers=auth_headers)
            assert response.status_code == 200

            final_lead = json.loads(response.data)
            assert final_lead['status'] == 'converted'
            assert final_lead['converted_to_customer_id'] == customer_id

        # Verify the complete workflow results
        assert lead_id is not None
        assert appointment_id is not None
        assert project_id is not None
        assert customer_id is not None
        assert final_lead['status'] == 'converted'
        assert customer['converted_from_lead_id'] == lead_id


class TestProjectManagementWorkflow:
    """Test complete project management workflow."""

    def test_project_lifecycle_workflow(self, client: FlaskClient, auth_headers):
        """Test complete project lifecycle from creation to completion."""

        # Setup: Create customer first
        customer_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@example.com',
            'phone': '555-5678',
            'street_address': '456 Oak Ave',
            'city': 'Troy',
            'state': 'MI',
            'zip_code': '48084',
            'customer_type': 'residential'
        }

        with patch('app.services.customer_service.create_customer') as mock_customer:
            mock_customer.return_value = {
                'id': 'customer-002',
                **customer_data,
                'created_at': datetime.utcnow().isoformat()
            }

            response = client.post('/api/customers', data=json.dumps(customer_data), headers=auth_headers)
            assert response.status_code == 201
            customer = json.loads(response.data)
            customer_id = customer['id']

        # Step 1: Create new project
        project_data = {
            'customer_id': customer_id,
            'name': 'Roof Repair - 456 Oak Ave',
            'description': 'Storm damage repair and gutter replacement',
            'project_type': 'repair',
            'estimated_value': 8500,
            'materials_cost': 3500,
            'labor_cost': 4200,
            'profit_margin': 35.0
        }

        with patch('app.services.project_service.create_project') as mock_create:
            mock_create.return_value = {
                'id': 'project-002',
                **project_data,
                'status': 'new',
                'created_at': datetime.utcnow().isoformat()
            }

            response = client.post('/api/projects', data=json.dumps(project_data), headers=auth_headers)
            assert response.status_code == 201
            project = json.loads(response.data)
            project_id = project['id']

        # Step 2: Schedule project planning appointment
        planning_appointment = {
            'title': 'Project Planning & Material Selection',
            'appointment_type': 'project_work',
            'scheduled_date': (datetime.utcnow() + timedelta(days=3)).isoformat(),
            'duration_minutes': 90,
            'entity_type': 'project',
            'entity_id': project_id,
            'assigned_to': 'project-manager-1'
        }

        with patch('app.services.appointments_service.create_appointment') as mock_apt:
            mock_apt.return_value = {
                'id': 'apt-planning',
                **planning_appointment,
                'status': 'scheduled',
                'created_at': datetime.utcnow().isoformat()
            }

            response = client.post('/api/appointments', data=json.dumps(planning_appointment), headers=auth_headers)
            assert response.status_code == 201

        # Step 3: Move project to approved status
        approval_update = {
            'status': 'approved',
            'actual_value': 8500,
            'start_date': (datetime.utcnow() + timedelta(days=5)).isoformat(),
            'estimated_completion_date': (datetime.utcnow() + timedelta(days=8)).isoformat(),
            'assigned_team_members': ['crew-leader-1', 'roofer-1', 'roofer-2']
        }

        with patch('app.services.project_service.update_project') as mock_approve:
            mock_approve.return_value = {
                **project,
                **approval_update,
                'updated_at': datetime.utcnow().isoformat()
            }

            response = client.put(f'/api/projects/{project_id}',
                                data=json.dumps(approval_update), headers=auth_headers)
            assert response.status_code == 200

        # Step 4: Start project work
        start_update = {
            'status': 'in_progress',
            'actual_start_date': datetime.utcnow().isoformat()
        }

        with patch('app.services.project_service.update_project') as mock_start:
            mock_start.return_value = {
                **project,
                **approval_update,
                **start_update,
                'updated_at': datetime.utcnow().isoformat()
            }

            response = client.put(f'/api/projects/{project_id}',
                                data=json.dumps(start_update), headers=auth_headers)
            assert response.status_code == 200

        # Step 5: Add progress updates and interactions
        progress_interaction = {
            'entity_type': 'project',
            'entity_id': project_id,
            'interaction_type': 'note',
            'subject': 'Day 1 Progress Update',
            'content': 'Removed damaged shingles and decking. Weather conditions good. On schedule.'
        }

        with patch('app.services.interaction_service.create_interaction') as mock_progress:
            mock_progress.return_value = {
                'id': 'interaction-progress',
                **progress_interaction,
                'created_at': datetime.utcnow().isoformat(),
                'created_by': 'crew-leader-1'
            }

            response = client.post('/api/interactions', data=json.dumps(progress_interaction), headers=auth_headers)
            assert response.status_code == 201

        # Step 6: Complete project
        completion_update = {
            'status': 'completed',
            'completion_date': datetime.utcnow().isoformat(),
            'final_cost': 8350,  # Slightly under estimate
            'completion_notes': 'Project completed successfully. Customer very satisfied.'
        }

        with patch('app.services.project_service.update_project') as mock_complete:
            mock_complete.return_value = {
                **project,
                **approval_update,
                **start_update,
                **completion_update,
                'updated_at': datetime.utcnow().isoformat()
            }

            response = client.put(f'/api/projects/{project_id}',
                                data=json.dumps(completion_update), headers=auth_headers)
            assert response.status_code == 200

            completed_project = json.loads(response.data)
            assert completed_project['status'] == 'completed'

        # Step 7: Request customer review
        review_request = {
            'customer_id': customer_id,
            'project_id': project_id,
            'review_type': 'completion',
            'requested_via': 'email',
            'request_date': datetime.utcnow().isoformat()
        }

        with patch('app.services.reviews_service.request_review') as mock_review:
            mock_review.return_value = {
                'id': 'review-request-001',
                **review_request,
                'status': 'pending',
                'created_at': datetime.utcnow().isoformat()
            }

            response = client.post('/api/reviews/request', data=json.dumps(review_request), headers=auth_headers)
            assert response.status_code == 201

        # Verify workflow completion
        assert project_id is not None
        assert completed_project['status'] == 'completed'
        assert completed_project['final_cost'] <= completed_project['estimated_value']


class TestAppointmentSchedulingWorkflow:
    """Test complete appointment scheduling and management workflow."""

    def test_appointment_lifecycle_workflow(self, client: FlaskClient, auth_headers):
        """Test complete appointment lifecycle."""

        # Step 1: Create appointment
        appointment_data = {
            'title': 'Roof Inspection',
            'description': 'Annual roof maintenance inspection',
            'appointment_type': 'inspection',
            'scheduled_date': (datetime.utcnow() + timedelta(days=1)).isoformat(),
            'duration_minutes': 60,
            'entity_type': 'customer',
            'entity_id': 'customer-003',
            'assigned_to': 'inspector-1',
            'location': '789 Pine St, Rochester Hills, MI'
        }

        with patch('app.services.appointments_service.create_appointment') as mock_create:
            mock_create.return_value = {
                'id': 'apt-inspection',
                **appointment_data,
                'status': 'scheduled',
                'created_at': datetime.utcnow().isoformat()
            }

            response = client.post('/api/appointments', data=json.dumps(appointment_data), headers=auth_headers)
            assert response.status_code == 201
            appointment = json.loads(response.data)
            appointment_id = appointment['id']

        # Step 2: Confirm appointment
        confirmation_update = {
            'status': 'confirmed',
            'confirmation_date': datetime.utcnow().isoformat(),
            'confirmation_method': 'phone',
            'notes': 'Customer confirmed availability and access instructions provided'
        }

        with patch('app.services.appointments_service.update_appointment') as mock_confirm:
            mock_confirm.return_value = {
                **appointment,
                **confirmation_update,
                'updated_at': datetime.utcnow().isoformat()
            }

            response = client.put(f'/api/appointments/{appointment_id}',
                                data=json.dumps(confirmation_update), headers=auth_headers)
            assert response.status_code == 200

        # Step 3: Start appointment
        start_update = {
            'status': 'in_progress',
            'actual_start_time': datetime.utcnow().isoformat()
        }

        with patch('app.services.appointments_service.update_appointment') as mock_start:
            mock_start.return_value = {
                **appointment,
                **confirmation_update,
                **start_update,
                'updated_at': datetime.utcnow().isoformat()
            }

            response = client.put(f'/api/appointments/{appointment_id}',
                                data=json.dumps(start_update), headers=auth_headers)
            assert response.status_code == 200

        # Step 4: Complete appointment with findings
        completion_update = {
            'status': 'completed',
            'actual_end_time': (datetime.utcnow() + timedelta(minutes=55)).isoformat(),
            'completion_notes': 'Roof in good condition. Minor gutter cleaning recommended.',
            'follow_up_required': True,
            'follow_up_date': (datetime.utcnow() + timedelta(days=180)).isoformat(),
            'recommendations': 'Schedule gutter cleaning in spring'
        }

        with patch('app.services.appointments_service.update_appointment') as mock_complete:
            mock_complete.return_value = {
                **appointment,
                **confirmation_update,
                **start_update,
                **completion_update,
                'updated_at': datetime.utcnow().isoformat()
            }

            response = client.put(f'/api/appointments/{appointment_id}',
                                data=json.dumps(completion_update), headers=auth_headers)
            assert response.status_code == 200

            completed_appointment = json.loads(response.data)
            assert completed_appointment['status'] == 'completed'

        # Step 5: Schedule follow-up if needed
        if completed_appointment.get('follow_up_required'):
            followup_data = {
                'title': 'Follow-up Roof Maintenance',
                'description': 'Gutter cleaning and maintenance check',
                'appointment_type': 'maintenance',
                'scheduled_date': completed_appointment['follow_up_date'],
                'duration_minutes': 30,
                'entity_type': 'customer',
                'entity_id': appointment_data['entity_id'],
                'assigned_to': 'maintenance-crew-1',
                'parent_appointment_id': appointment_id
            }

            with patch('app.services.appointments_service.create_appointment') as mock_followup:
                mock_followup.return_value = {
                    'id': 'apt-followup',
                    **followup_data,
                    'status': 'scheduled',
                    'created_at': datetime.utcnow().isoformat()
                }

                response = client.post('/api/appointments', data=json.dumps(followup_data), headers=auth_headers)
                assert response.status_code == 201

        # Verify workflow
        assert completed_appointment['status'] == 'completed'
        assert completed_appointment.get('follow_up_required') is True


class TestAnalyticsReportingWorkflow:
    """Test analytics and reporting workflow."""

    def test_monthly_performance_report_generation(self, client: FlaskClient, auth_headers):
        """Test generating comprehensive monthly performance report."""

        # Step 1: Get dashboard metrics
        with patch('app.services.analytics_service.get_dashboard_metrics') as mock_dashboard:
            mock_dashboard.return_value = {
                'total_leads': 45,
                'qualified_leads': 28,
                'converted_leads': 12,
                'active_projects': 8,
                'completed_projects': 15,
                'total_revenue': 425000,
                'average_project_value': 28333,
                'conversion_rate': 26.7
            }

            response = client.get('/api/analytics/dashboard', headers=auth_headers)
            assert response.status_code == 200
            dashboard_data = json.loads(response.data)

        # Step 2: Get lead conversion funnel
        with patch('app.services.analytics_service.get_conversion_funnel') as mock_funnel:
            mock_funnel.return_value = {
                'stages': [
                    {'stage': 'new', 'count': 45, 'percentage': 100},
                    {'stage': 'contacted', 'count': 38, 'percentage': 84.4},
                    {'stage': 'qualified', 'count': 28, 'percentage': 62.2},
                    {'stage': 'proposal', 'count': 20, 'percentage': 44.4},
                    {'stage': 'converted', 'count': 12, 'percentage': 26.7}
                ]
            }

            response = client.get('/api/analytics/conversion-funnel', headers=auth_headers)
            assert response.status_code == 200
            funnel_data = json.loads(response.data)

        # Step 3: Get revenue trends
        with patch('app.services.analytics_service.get_revenue_trends') as mock_revenue:
            mock_revenue.return_value = {
                'period': 'monthly',
                'data': [
                    {'month': '2025-01', 'revenue': 385000, 'projects': 14},
                    {'month': '2025-02', 'revenue': 425000, 'projects': 15},
                    {'month': '2025-03', 'revenue': 395000, 'projects': 13}
                ],
                'growth_rate': 10.4
            }

            response = client.get('/api/analytics/revenue-trends?period=monthly', headers=auth_headers)
            assert response.status_code == 200
            revenue_data = json.loads(response.data)

        # Step 4: Get team performance
        with patch('app.services.analytics_service.get_team_performance') as mock_team:
            mock_team.return_value = {
                'team_members': [
                    {'name': 'John Sales', 'leads_converted': 8, 'revenue_generated': 240000},
                    {'name': 'Jane Rep', 'leads_converted': 4, 'revenue_generated': 185000}
                ],
                'top_performer': 'John Sales'
            }

            response = client.get('/api/analytics/team-performance', headers=auth_headers)
            assert response.status_code == 200
            team_data = json.loads(response.data)

        # Verify all analytics data is accessible
        assert dashboard_data['conversion_rate'] > 20
        assert len(funnel_data['stages']) == 5
        assert revenue_data['growth_rate'] > 0
        assert len(team_data['team_members']) >= 2


class TestSystemIntegrationWorkflow:
    """Test system integration and real-time updates."""

    def test_real_time_notification_workflow(self, client: FlaskClient, auth_headers):
        """Test real-time notifications across the system."""

        # This would test Pusher integration for real-time updates
        with patch('app.services.realtime_service.broadcast_update') as mock_broadcast:
            # Create a lead (should trigger real-time update)
            lead_data = {
                'first_name': 'Real',
                'last_name': 'Time',
                'email': 'realtime@test.com',
                'phone': '555-9999',
                'source': 'referral'
            }

            with patch('app.services.lead_service.create_lead') as mock_create:
                mock_create.return_value = {
                    'id': 'lead-realtime',
                    **lead_data,
                    'created_at': datetime.utcnow().isoformat()
                }

                response = client.post('/api/leads', data=json.dumps(lead_data), headers=auth_headers)
                assert response.status_code == 201

            # Verify real-time broadcast was called
            mock_broadcast.assert_called_once()

    def test_audit_trail_workflow(self, client: FlaskClient, auth_headers):
        """Test audit trail creation for all major operations."""

        with patch('app.middleware.audit_middleware.create_audit_log') as mock_audit:
            # Perform various operations that should be audited
            operations = [
                ('POST', '/api/leads', {'first_name': 'Audit', 'last_name': 'Test'}),
                ('PUT', '/api/leads/test-id', {'status': 'qualified'}),
                ('DELETE', '/api/leads/test-id', {})
            ]

            for method, endpoint, data in operations:
                if method == 'POST':
                    client.post(endpoint, data=json.dumps(data), headers=auth_headers)
                elif method == 'PUT':
                    client.put(endpoint, data=json.dumps(data), headers=auth_headers)
                elif method == 'DELETE':
                    client.delete(endpoint, headers=auth_headers)

            # Verify audit logs were created
            assert mock_audit.call_count >= len(operations)


# E2E test markers
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.integration,
    pytest.mark.slow
]