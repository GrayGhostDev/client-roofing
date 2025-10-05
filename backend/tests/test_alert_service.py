"""
Tests for the 2-minute Alert Service

Tests the critical lead response alert system including triggering,
acknowledgment, response tracking, and escalation.

Author: iSwitch Roofs Development Team
Date: 2025-01-04
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
import threading
import time

from app.services.alert_service import (
    AlertService,
    AlertPriority,
    AlertStatus,
    trigger_lead_alert,
    acknowledge_alert,
    mark_responded
)


@pytest.fixture
def alert_service():
    """Create alert service instance for testing"""
    return AlertService()


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    with patch('app.services.alert_service.redis_client') as mock:
        mock.get.return_value = None
        mock.setex.return_value = True
        mock.scan_keys.return_value = []
        yield mock


@pytest.fixture
def mock_notification():
    """Mock notification service"""
    with patch('app.services.alert_service.notification_service') as mock:
        mock.send_notification.return_value = (True, None)
        yield mock


@pytest.fixture
def mock_realtime():
    """Mock realtime service"""
    with patch('app.services.alert_service.realtime_service') as mock:
        mock.trigger_event.return_value = True
        yield mock


@pytest.fixture
def mock_db():
    """Mock database"""
    with patch('app.services.alert_service.get_supabase_client') as mock_get_supabase:
        mock = MagicMock()
        # Mock users table
        mock.table.return_value.select.return_value.in_.return_value.eq.return_value.execute.return_value.data = [
            {'id': 'user-1', 'name': 'Sales Rep 1', 'role': 'sales_rep', 'status': 'available'},
            {'id': 'user-2', 'name': 'Sales Rep 2', 'role': 'sales_rep', 'status': 'available'}
        ]
        # Mock insert operations
        mock.table.return_value.insert.return_value.execute.return_value = Mock()
        mock_get_supabase.return_value = mock
        yield mock


@pytest.fixture
def sample_lead_data():
    """Sample lead data for testing"""
    return {
        'id': 'lead-123',
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '+12485551234',
        'score': 85,
        'source': 'Google Ads',
        'address': '123 Main St, Birmingham, MI',
        'project_type': 'Full Replacement',
        'urgency': 'high'
    }


class TestAlertService:
    """Test suite for AlertService class"""

    def test_trigger_lead_alert_success(self, alert_service, mock_redis, mock_notification,
                                       mock_realtime, mock_db, sample_lead_data):
        """Test successful alert triggering"""
        # Act
        success, alert_id = alert_service.trigger_lead_alert('lead-123', sample_lead_data)

        # Assert
        assert success is True
        assert alert_id.startswith('alert-')

        # Verify Redis was called to store alert
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0].startswith('alert:')
        assert call_args[0][1] == 3600  # TTL

        # Verify notification was sent
        mock_notification.send_notification.assert_called_once()
        notification_args = mock_notification.send_notification.call_args[1]
        assert notification_args['type'] == 'lead_alert_critical'  # Score 85 = critical
        assert notification_args['channels'] == ['email', 'sms', 'push']
        assert notification_args['priority'] == 'urgent'

        # Verify real-time events were triggered
        assert mock_realtime.trigger_event.call_count == 2  # User channel + team channel

    def test_trigger_lead_alert_no_available_members(self, alert_service, mock_redis,
                                                    mock_notification, mock_realtime, mock_db,
                                                    sample_lead_data):
        """Test alert triggering when no team members are available"""
        # Setup
        mock_db.table.return_value.select.return_value.in_.return_value.eq.return_value.execute.return_value.data = []

        # Act
        success, error = alert_service.trigger_lead_alert('lead-123', sample_lead_data)

        # Assert
        assert success is False
        assert error == "No available team members"

    def test_calculate_priority_critical(self, alert_service):
        """Test priority calculation for critical leads (score >= 80)"""
        priority = alert_service._calculate_priority(85)
        assert priority == AlertPriority.CRITICAL

    def test_calculate_priority_high(self, alert_service):
        """Test priority calculation for high priority leads (score 60-79)"""
        priority = alert_service._calculate_priority(70)
        assert priority == AlertPriority.HIGH

    def test_calculate_priority_normal(self, alert_service):
        """Test priority calculation for normal priority leads (score 40-59)"""
        priority = alert_service._calculate_priority(50)
        assert priority == AlertPriority.NORMAL

    def test_calculate_priority_low(self, alert_service):
        """Test priority calculation for low priority leads (score < 40)"""
        priority = alert_service._calculate_priority(30)
        assert priority == AlertPriority.LOW

    def test_acknowledge_alert_success(self, alert_service, mock_redis, mock_realtime):
        """Test successful alert acknowledgment"""
        # Setup
        alert_data = {
            'alert_id': 'alert-123',
            'lead_id': 'lead-123',
            'status': AlertStatus.PENDING.value,
            'created_at': datetime.utcnow().isoformat()
        }
        mock_redis.get.return_value = json.dumps(alert_data)

        # Act
        success = alert_service.acknowledge_alert('alert-123', 'user-1')

        # Assert
        assert success is True

        # Verify Redis was updated
        mock_redis.setex.assert_called_once()
        updated_data = json.loads(mock_redis.setex.call_args[0][2])
        assert updated_data['status'] == AlertStatus.ACKNOWLEDGED.value
        assert updated_data['acknowledged_by'] == 'user-1'
        assert 'acknowledged_at' in updated_data

        # Verify real-time event was triggered
        mock_realtime.trigger_event.assert_called_once()

    def test_acknowledge_alert_not_found(self, alert_service, mock_redis):
        """Test acknowledging non-existent alert"""
        # Setup
        mock_redis.get.return_value = None

        # Act
        success = alert_service.acknowledge_alert('alert-999', 'user-1')

        # Assert
        assert success is False

    def test_mark_responded_success(self, alert_service, mock_redis, mock_notification,
                                   mock_realtime, mock_db):
        """Test marking alert as responded"""
        # Setup
        alert_data = {
            'alert_id': 'alert-123',
            'lead_id': 'lead-123',
            'status': AlertStatus.ACKNOWLEDGED.value,
            'created_at': (datetime.utcnow() - timedelta(seconds=45)).isoformat()
        }
        mock_redis.get.return_value = json.dumps(alert_data)

        response_data = {
            'action': 'called',
            'outcome': 'interested',
            'notes': 'Customer wants quote'
        }

        # Act
        success = alert_service.mark_responded('alert-123', 'user-1', response_data)

        # Assert
        assert success is True

        # Verify Redis was updated
        mock_redis.setex.assert_called()
        updated_data = json.loads(mock_redis.setex.call_args[0][2])
        assert updated_data['status'] == AlertStatus.RESPONDED.value
        assert updated_data['responded_by'] == 'user-1'
        assert updated_data['response_seconds'] == pytest.approx(45, abs=5)

        # Verify response time was logged
        mock_db.table.assert_called_with('response_metrics')

        # Verify success notification was sent (responded within 2 minutes)
        mock_notification.send_notification.assert_called_once()
        notification_args = mock_notification.send_notification.call_args[1]
        assert notification_args['type'] == 'lead_response_success'

    def test_mark_responded_late_response(self, alert_service, mock_redis, mock_notification,
                                         mock_realtime, mock_db):
        """Test marking alert as responded after deadline"""
        # Setup
        alert_data = {
            'alert_id': 'alert-123',
            'lead_id': 'lead-123',
            'status': AlertStatus.ESCALATED.value,
            'created_at': (datetime.utcnow() - timedelta(seconds=150)).isoformat()  # 2.5 minutes ago
        }
        mock_redis.get.return_value = json.dumps(alert_data)

        response_data = {'action': 'called', 'outcome': 'interested'}

        # Act
        success = alert_service.mark_responded('alert-123', 'user-1', response_data)

        # Assert
        assert success is True

        # Verify response time is > 120 seconds
        updated_data = json.loads(mock_redis.setex.call_args[0][2])
        assert updated_data['response_seconds'] > 120

        # Verify no success notification was sent (late response)
        mock_notification.send_notification.assert_not_called()

    def test_escalate_if_no_response_success(self, alert_service, mock_redis, mock_notification,
                                            mock_realtime, mock_db):
        """Test successful alert escalation"""
        # Setup
        alert_data = {
            'alert_id': 'alert-123',
            'lead_id': 'lead-123',
            'lead_data': {'name': 'John Doe'},
            'status': AlertStatus.ACKNOWLEDGED.value,
            'assigned_to_name': 'Sales Rep 1',
            'created_at': (datetime.utcnow() - timedelta(minutes=2)).isoformat()
        }
        mock_redis.get.return_value = json.dumps(alert_data)

        # Mock escalation recipients
        mock_db.table.return_value.select.return_value.in_.return_value.eq.return_value.execute.return_value.data = [
            {'id': 'manager-1', 'name': 'Sales Manager', 'email': 'manager@example.com', 'phone': '+12485555678'}
        ]

        # Act
        success = alert_service.escalate_if_no_response('alert-123', 'lead-123')

        # Assert
        assert success is True

        # Verify alert status was updated to escalated
        updated_data = json.loads(mock_redis.setex.call_args[0][2])
        assert updated_data['status'] == AlertStatus.ESCALATED.value
        assert 'escalated_at' in updated_data

        # Verify escalation notification was sent
        mock_notification.send_notification.assert_called_once()
        notification_args = mock_notification.send_notification.call_args[1]
        assert notification_args['type'] == 'lead_alert_escalation'
        assert notification_args['channels'] == ['email', 'sms', 'push', 'call']  # Includes phone call
        assert notification_args['priority'] == 'critical'

    def test_escalate_already_responded(self, alert_service, mock_redis, mock_notification):
        """Test escalation skipped if alert already responded"""
        # Setup
        alert_data = {
            'alert_id': 'alert-123',
            'status': AlertStatus.RESPONDED.value
        }
        mock_redis.get.return_value = json.dumps(alert_data)

        # Act
        success = alert_service.escalate_if_no_response('alert-123', 'lead-123')

        # Assert
        assert success is True
        mock_notification.send_notification.assert_not_called()  # No escalation notification

    def test_log_response_time(self, alert_service, mock_redis, mock_db, mock_realtime):
        """Test logging response time metrics"""
        # Setup
        mock_redis.get.return_value = None  # No existing stats

        # Act
        success = alert_service.log_response_time('lead-123', 'user-1', 45.5)

        # Assert
        assert success is True

        # Verify database insert
        mock_db.table.assert_called_with('response_metrics')
        mock_db.table.return_value.insert.assert_called_once()

        # Verify member stats updated in Redis
        mock_redis.setex.assert_called()
        stats_call = mock_redis.setex.call_args
        assert stats_call[0][0] == 'member_stats:user-1'
        stats = json.loads(stats_call[0][2])
        assert stats['total_responses'] == 1
        assert stats['total_response_time'] == 45.5
        assert stats['avg_response_time'] == 45.5
        assert stats['within_target'] == 1
        assert stats['target_rate'] == 100.0

        # Verify analytics event triggered
        mock_realtime.trigger_event.assert_called_once()
        event_args = mock_realtime.trigger_event.call_args[1]
        assert event_args['channel'] == 'analytics'
        assert event_args['event'] == 'response-metric'

    def test_get_team_response_metrics(self, alert_service, mock_db):
        """Test getting team response metrics"""
        # Setup
        mock_metrics = [
            {
                'response_seconds': 45,
                'within_target': True,
                'responded_by': 'user-1',
                'created_at': datetime.utcnow().isoformat()
            },
            {
                'response_seconds': 150,
                'within_target': False,
                'responded_by': 'user-2',
                'created_at': datetime.utcnow().isoformat()
            }
        ]
        mock_db.table.return_value.select.return_value.gte.return_value.execute.return_value.data = mock_metrics

        # Act
        metrics = alert_service.get_team_response_metrics(period_days=7)

        # Assert
        assert metrics['period_days'] == 7
        assert metrics['total_responses'] == 2
        assert metrics['avg_response_time'] == 97.5
        assert metrics['within_target_rate'] == 50.0
        assert metrics['best_response']['response_seconds'] == 45
        assert metrics['worst_response']['response_seconds'] == 150

    def test_find_available_team_member_with_scoring(self, alert_service, mock_redis, mock_db):
        """Test team member selection with workload scoring"""
        # Setup
        mock_db.table.return_value.select.return_value.in_.return_value.eq.return_value.execute.return_value.data = [
            {'id': 'user-1', 'name': 'Rep 1', 'role': 'sales_rep', 'specialties': ['roofing']},
            {'id': 'user-2', 'name': 'Rep 2', 'role': 'sales_rep'}
        ]

        # Set different workloads - return JSON string of stats
        def redis_side_effect(key):
            if 'user-1' in key:
                if 'active_leads' in key:
                    return '3'
                else:
                    return json.dumps({'avg_response_time': 70, 'target_rate': 85})
            else:
                if 'active_leads' in key:
                    return '1'
                else:
                    return json.dumps({'avg_response_time': 50, 'target_rate': 95})

        mock_redis.get.side_effect = redis_side_effect

        # Act
        member = alert_service._find_available_team_member(AlertPriority.HIGH)

        # Assert
        assert member is not None
        assert member['id'] == 'user-2'  # User 2 has lower workload

    def test_escalation_timer_integration(self, alert_service, mock_redis, mock_notification,
                                         mock_realtime, mock_db):
        """Test escalation timer triggers after timeout"""
        # Setup
        alert_service.response_timeout = 0.1  # 100ms for testing

        alert_data = {
            'alert_id': 'alert-test',
            'lead_id': 'lead-test',
            'lead_data': {'name': 'Test Lead'},
            'status': AlertStatus.PENDING.value,
            'assigned_to_name': 'Test Rep',
            'created_at': datetime.utcnow().isoformat()
        }

        mock_redis.get.return_value = json.dumps(alert_data)
        mock_db.table.return_value.select.return_value.in_.return_value.eq.return_value.execute.return_value.data = [
            {'id': 'manager-1', 'name': 'Manager', 'email': 'manager@test.com', 'phone': '+12485551234'}
        ]

        # Act
        alert_service._start_escalation_timer('alert-test', 'lead-test', {})

        # Wait for timer
        time.sleep(0.2)

        # Assert escalation was triggered
        mock_notification.send_notification.assert_called()
        notification_args = mock_notification.send_notification.call_args[1]
        assert notification_args['type'] == 'lead_alert_escalation'


class TestAlertConvenienceFunctions:
    """Test convenience functions"""

    def test_trigger_lead_alert_function(self, mock_redis, mock_notification, mock_realtime, mock_db):
        """Test the convenience trigger_lead_alert function"""
        lead_data = {'id': 'lead-456', 'name': 'Jane Doe', 'score': 75}

        success, alert_id = trigger_lead_alert('lead-456', lead_data)

        assert success is True
        assert alert_id.startswith('alert-')

    def test_acknowledge_alert_function(self, mock_redis, mock_realtime):
        """Test the convenience acknowledge_alert function"""
        alert_data = {
            'alert_id': 'alert-789',
            'status': AlertStatus.PENDING.value,
            'created_at': datetime.utcnow().isoformat()
        }
        mock_redis.get.return_value = json.dumps(alert_data)

        success = acknowledge_alert('alert-789', 'user-3')

        assert success is True

    def test_mark_responded_function(self, mock_redis, mock_realtime, mock_db):
        """Test the convenience mark_responded function"""
        alert_data = {
            'alert_id': 'alert-999',
            'lead_id': 'lead-999',
            'status': AlertStatus.ACKNOWLEDGED.value,
            'created_at': datetime.utcnow().isoformat()
        }
        mock_redis.get.return_value = json.dumps(alert_data)

        response_data = {'action': 'emailed', 'outcome': 'follow_up_scheduled'}
        success = mark_responded('alert-999', 'user-4', response_data)

        assert success is True


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])