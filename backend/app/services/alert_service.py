"""
Alert Service for iSwitch Roofs CRM

This service handles the critical 2-minute lead response system that ensures
immediate notification and escalation for new leads. It coordinates multi-channel
alerts (email, SMS, push notifications) and tracks response times.

Business Context:
- Leads contacted within 2 minutes are 78% more likely to convert
- Multi-channel alerts ensure team members never miss a hot lead
- Automatic escalation ensures every lead gets timely attention
- Response time tracking provides performance metrics

Author: iSwitch Roofs Development Team
Date: 2025-01-04
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from uuid import uuid4
import threading
import time
from enum import Enum

from app.services.notification import notification_service
from app.services.realtime_service import realtime_service
from app.config import get_supabase_client
from app.utils.redis_client import redis_client

logger = logging.getLogger(__name__)


class AlertPriority(Enum):
    """Alert priority levels"""
    CRITICAL = "critical"  # Hot leads (score 80+)
    HIGH = "high"         # Warm leads (score 60-79)
    NORMAL = "normal"     # Standard leads (score 40-59)
    LOW = "low"          # Cold leads (score <40)


class AlertStatus(Enum):
    """Alert status tracking"""
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    RESPONDED = "responded"
    ESCALATED = "escalated"
    EXPIRED = "expired"


class AlertService:
    """
    Manages the 2-minute alert system for lead response

    Key Features:
    - Instant multi-channel alerts for new leads
    - Intelligent team member selection based on availability
    - Automatic escalation if no response within 2 minutes
    - Response time tracking and analytics
    - Round-robin assignment with workload balancing
    """

    def __init__(self):
        self.escalation_threads = {}
        self.response_timeout = 120  # 2 minutes in seconds
        self.escalation_levels = [
            {'time': 0, 'roles': ['sales_rep']},
            {'time': 60, 'roles': ['sales_manager', 'sales_rep']},
            {'time': 120, 'roles': ['operations_manager', 'sales_manager']},
            {'time': 180, 'roles': ['owner', 'operations_manager']}
        ]

    def trigger_lead_alert(self, lead_id: str, lead_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Trigger immediate alert for new lead

        Args:
            lead_id: Unique identifier for the lead
            lead_data: Lead information including score, source, contact info

        Returns:
            Tuple of (success, alert_id or error message)
        """
        try:
            # Generate unique alert ID
            alert_id = f"alert-{uuid4()}"

            # Determine priority based on lead score
            priority = self._calculate_priority(lead_data.get('score', 50))

            # Find available team member
            assigned_to = self._find_available_team_member(priority)

            if not assigned_to:
                logger.error(f"No available team members for lead {lead_id}")
                return False, "No available team members"

            # Store alert in Redis for tracking
            alert_data = {
                'alert_id': alert_id,
                'lead_id': lead_id,
                'lead_data': lead_data,
                'assigned_to': assigned_to['id'],
                'assigned_to_name': assigned_to['name'],
                'created_at': datetime.utcnow().isoformat(),
                'status': AlertStatus.PENDING.value,
                'priority': priority.value,
                'response_deadline': (datetime.utcnow() + timedelta(seconds=self.response_timeout)).isoformat()
            }

            # Store in Redis with TTL
            redis_client.setex(
                f"alert:{alert_id}",
                3600,  # 1 hour TTL
                json.dumps(alert_data)
            )

            # Send immediate multi-channel notification
            notification_data = {
                'alert_id': alert_id,
                'lead_id': lead_id,
                'lead_name': lead_data.get('name', 'Unknown'),
                'lead_phone': lead_data.get('phone', 'N/A'),
                'lead_email': lead_data.get('email', 'N/A'),
                'lead_score': lead_data.get('score', 0),
                'lead_source': lead_data.get('source', 'Unknown'),
                'urgency': 'IMMEDIATE RESPONSE REQUIRED',
                'deadline': '2 MINUTES',
                'address': lead_data.get('address', 'N/A'),
                'project_type': lead_data.get('project_type', 'Unknown')
            }

            # Send high-priority notification
            success, error = notification_service.send_notification(
                type='lead_alert_critical' if priority == AlertPriority.CRITICAL else 'lead_alert',
                data=notification_data,
                recipient_id=assigned_to['id'],
                channels=['email', 'sms', 'push'],
                priority='urgent'
            )

            if not success:
                logger.error(f"Failed to send alert notification: {error}")

            # Broadcast real-time event
            realtime_service.trigger_event(
                channel=f'private-user-{assigned_to["id"]}',
                event='lead-alert',
                data={
                    'alert': alert_data,
                    'action_required': 'respond_immediately'
                }
            )

            # Also broadcast to team channel
            realtime_service.trigger_event(
                channel='team-alerts',
                event='new-lead-assigned',
                data={
                    'lead_id': lead_id,
                    'assigned_to': assigned_to['name'],
                    'deadline': alert_data['response_deadline']
                }
            )

            # Start escalation timer
            self._start_escalation_timer(alert_id, lead_id, lead_data)

            # Log alert creation
            logger.info(f"Alert {alert_id} created for lead {lead_id}, assigned to {assigned_to['name']}")

            # Track in database
            self._record_alert_in_database(alert_id, lead_id, assigned_to['id'], priority.value)

            return True, alert_id

        except Exception as e:
            logger.error(f"Error triggering lead alert: {str(e)}")
            return False, str(e)

    def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """
        Mark alert as acknowledged by team member

        Args:
            alert_id: Alert identifier
            user_id: Team member acknowledging

        Returns:
            Success boolean
        """
        try:
            alert_data = self._get_alert_data(alert_id)
            if not alert_data:
                return False

            # Update status
            alert_data['status'] = AlertStatus.ACKNOWLEDGED.value
            alert_data['acknowledged_by'] = user_id
            alert_data['acknowledged_at'] = datetime.utcnow().isoformat()

            # Update in Redis
            redis_client.setex(
                f"alert:{alert_id}",
                3600,
                json.dumps(alert_data)
            )

            # Broadcast acknowledgment
            realtime_service.trigger_event(
                channel='team-alerts',
                event='alert-acknowledged',
                data={
                    'alert_id': alert_id,
                    'acknowledged_by': user_id
                }
            )

            logger.info(f"Alert {alert_id} acknowledged by {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error acknowledging alert: {str(e)}")
            return False

    def mark_responded(self, alert_id: str, user_id: str, response_data: Dict[str, Any]) -> bool:
        """
        Mark alert as responded and calculate response time

        Args:
            alert_id: Alert identifier
            user_id: Team member who responded
            response_data: Response details (action taken, notes, etc.)

        Returns:
            Success boolean
        """
        try:
            alert_data = self._get_alert_data(alert_id)
            if not alert_data:
                return False

            # Calculate response time
            created_at = datetime.fromisoformat(alert_data['created_at'])
            responded_at = datetime.utcnow()
            response_seconds = (responded_at - created_at).total_seconds()

            # Update alert data
            alert_data['status'] = AlertStatus.RESPONDED.value
            alert_data['responded_by'] = user_id
            alert_data['responded_at'] = responded_at.isoformat()
            alert_data['response_seconds'] = response_seconds
            alert_data['response_data'] = response_data

            # Update in Redis
            redis_client.setex(
                f"alert:{alert_id}",
                3600,
                json.dumps(alert_data)
            )

            # Cancel escalation if running
            self._cancel_escalation(alert_id)

            # Log response time
            self.log_response_time(
                alert_data['lead_id'],
                user_id,
                response_seconds
            )

            # Send success notification if within 2 minutes
            if response_seconds <= self.response_timeout:
                notification_service.send_notification(
                    type='lead_response_success',
                    data={
                        'lead_id': alert_data['lead_id'],
                        'response_time': f"{int(response_seconds)} seconds",
                        'within_target': True
                    },
                    recipient_id=user_id
                )

            # Broadcast response
            realtime_service.trigger_event(
                channel='team-alerts',
                event='alert-responded',
                data={
                    'alert_id': alert_id,
                    'responded_by': user_id,
                    'response_time': response_seconds
                }
            )

            logger.info(f"Alert {alert_id} responded by {user_id} in {response_seconds} seconds")
            return True

        except Exception as e:
            logger.error(f"Error marking alert as responded: {str(e)}")
            return False

    def escalate_if_no_response(self, alert_id: str, lead_id: str, minutes: int = 2) -> bool:
        """
        Escalate alert if no response within specified minutes

        Args:
            alert_id: Alert identifier
            lead_id: Lead identifier
            minutes: Minutes before escalation (default 2)

        Returns:
            Success boolean
        """
        try:
            alert_data = self._get_alert_data(alert_id)
            if not alert_data:
                return False

            # Check if already responded
            if alert_data['status'] == AlertStatus.RESPONDED.value:
                logger.info(f"Alert {alert_id} already responded, skipping escalation")
                return True

            # Update status to escalated
            alert_data['status'] = AlertStatus.ESCALATED.value
            alert_data['escalated_at'] = datetime.utcnow().isoformat()

            # Find escalation recipients
            escalation_level = self._get_escalation_level(alert_data)
            recipients = self._find_escalation_recipients(escalation_level)

            if not recipients:
                logger.error(f"No escalation recipients found for alert {alert_id}")
                return False

            # Send escalation notifications
            for recipient in recipients:
                notification_service.send_notification(
                    type='lead_alert_escalation',
                    data={
                        'alert_id': alert_id,
                        'lead_id': lead_id,
                        'lead_name': alert_data['lead_data'].get('name', 'Unknown'),
                        'original_assigned': alert_data.get('assigned_to_name', 'Unknown'),
                        'escalation_reason': f"No response within {minutes} minutes",
                        'urgency': 'CRITICAL - IMMEDIATE ACTION REQUIRED'
                    },
                    recipient_id=recipient['id'],
                    channels=['email', 'sms', 'push', 'call'],  # Include phone call for escalation
                    priority='critical'
                )

            # Update Redis
            redis_client.setex(
                f"alert:{alert_id}",
                3600,
                json.dumps(alert_data)
            )

            # Broadcast escalation
            realtime_service.trigger_event(
                channel='team-alerts',
                event='alert-escalated',
                data={
                    'alert_id': alert_id,
                    'lead_id': lead_id,
                    'escalated_to': [r['name'] for r in recipients]
                }
            )

            logger.warning(f"Alert {alert_id} escalated after {minutes} minutes")
            return True

        except Exception as e:
            logger.error(f"Error escalating alert: {str(e)}")
            return False

    def log_response_time(self, lead_id: str, responded_by: str, seconds: float) -> bool:
        """
        Log response time metrics for analytics

        Args:
            lead_id: Lead identifier
            responded_by: Team member who responded
            seconds: Response time in seconds

        Returns:
            Success boolean
        """
        try:
            # Store in database
            response_metric = {
                'id': str(uuid4()),
                'lead_id': lead_id,
                'responded_by': responded_by,
                'response_seconds': seconds,
                'response_minutes': seconds / 60,
                'within_target': seconds <= self.response_timeout,
                'created_at': datetime.utcnow()
            }

            supabase = get_supabase_client()
            supabase.table('response_metrics').insert(response_metric).execute()

            # Update team member stats in Redis
            member_key = f"member_stats:{responded_by}"
            stats = redis_client.get(member_key)

            if stats:
                stats = json.loads(stats)
            else:
                stats = {
                    'total_responses': 0,
                    'total_response_time': 0,
                    'within_target': 0,
                    'missed_target': 0
                }

            stats['total_responses'] += 1
            stats['total_response_time'] += seconds
            stats['avg_response_time'] = stats['total_response_time'] / stats['total_responses']

            if seconds <= self.response_timeout:
                stats['within_target'] += 1
            else:
                stats['missed_target'] += 1

            stats['target_rate'] = (stats['within_target'] / stats['total_responses']) * 100

            redis_client.setex(
                member_key,
                86400,  # 24 hour TTL
                json.dumps(stats)
            )

            # Broadcast metrics update
            realtime_service.trigger_event(
                channel='analytics',
                event='response-metric',
                data={
                    'lead_id': lead_id,
                    'responded_by': responded_by,
                    'response_time': seconds,
                    'within_target': seconds <= self.response_timeout
                }
            )

            logger.info(f"Logged response time: {seconds} seconds for lead {lead_id}")
            return True

        except Exception as e:
            logger.error(f"Error logging response time: {str(e)}")
            return False

    def get_team_response_metrics(self, team_id: Optional[str] = None,
                                 period_days: int = 30) -> Dict[str, Any]:
        """
        Get team response time metrics for specified period

        Args:
            team_id: Optional team filter
            period_days: Number of days to analyze

        Returns:
            Dictionary of metrics
        """
        try:
            since = datetime.utcnow() - timedelta(days=period_days)

            supabase = get_supabase_client()
            query = supabase.table('response_metrics').select('*')

            if team_id:
                # Filter by team members
                team_members = self._get_team_members(team_id)
                member_ids = [m['id'] for m in team_members]
                query = query.in_('responded_by', member_ids)

            query = query.gte('created_at', since.isoformat())
            results = query.execute()

            if not results.data:
                return {
                    'period_days': period_days,
                    'total_responses': 0,
                    'avg_response_time': 0,
                    'within_target_rate': 0,
                    'best_response': None,
                    'worst_response': None
                }

            metrics = results.data
            total_responses = len(metrics)
            total_time = sum(m['response_seconds'] for m in metrics)
            within_target = sum(1 for m in metrics if m['within_target'])

            return {
                'period_days': period_days,
                'total_responses': total_responses,
                'avg_response_time': total_time / total_responses if total_responses > 0 else 0,
                'within_target_rate': (within_target / total_responses * 100) if total_responses > 0 else 0,
                'best_response': min(metrics, key=lambda x: x['response_seconds']),
                'worst_response': max(metrics, key=lambda x: x['response_seconds']),
                'hourly_distribution': self._calculate_hourly_distribution(metrics),
                'team_leaderboard': self._calculate_team_leaderboard(metrics)
            }

        except Exception as e:
            logger.error(f"Error getting team response metrics: {str(e)}")
            return {}

    def _calculate_priority(self, score: int) -> AlertPriority:
        """Calculate alert priority based on lead score"""
        if score >= 80:
            return AlertPriority.CRITICAL
        elif score >= 60:
            return AlertPriority.HIGH
        elif score >= 40:
            return AlertPriority.NORMAL
        else:
            return AlertPriority.LOW

    def _find_available_team_member(self, priority: AlertPriority) -> Optional[Dict[str, Any]]:
        """
        Find available team member based on priority and workload

        Uses intelligent routing based on:
        - Current availability status
        - Active lead count
        - Response time performance
        - Skill matching
        """
        try:
            # Get team members based on priority
            if priority == AlertPriority.CRITICAL:
                roles = ['sales_manager', 'senior_sales_rep', 'sales_rep']
            elif priority == AlertPriority.HIGH:
                roles = ['senior_sales_rep', 'sales_rep']
            else:
                roles = ['sales_rep']

            # Get available team members
            supabase = get_supabase_client()
            team_members = supabase.table('users').select('*').in_('role', roles).eq('status', 'available').execute()

            if not team_members.data:
                # No available members, try on-call
                team_members = supabase.table('users').select('*').in_('role', roles).eq('status', 'on_call').execute()

            if not team_members.data:
                return None

            # Score each member based on workload and performance
            scored_members = []
            for member in team_members.data:
                score = self._calculate_member_score(member)
                scored_members.append({
                    'id': member['id'],
                    'name': member['name'],
                    'score': score
                })

            # Sort by score (highest is best)
            scored_members.sort(key=lambda x: x['score'], reverse=True)

            return scored_members[0] if scored_members else None

        except Exception as e:
            logger.error(f"Error finding available team member: {str(e)}")
            return None

    def _calculate_member_score(self, member: Dict[str, Any]) -> float:
        """Calculate member assignment score based on multiple factors"""
        score = 100.0

        # Get current workload
        active_leads = redis_client.get(f"active_leads:{member['id']}")
        if active_leads:
            active_count = int(active_leads)
            score -= (active_count * 10)  # Reduce score for each active lead

        # Get response time stats
        stats_key = f"member_stats:{member['id']}"
        stats = redis_client.get(stats_key)

        if stats:
            stats = json.loads(stats)
            # Bonus for good average response time
            if stats.get('avg_response_time', 0) < 60:
                score += 20
            # Bonus for high target rate
            if stats.get('target_rate', 0) > 90:
                score += 15

        # Skill matching bonus
        if member.get('specialties'):
            score += 10

        return max(score, 0)  # Don't go negative

    def _start_escalation_timer(self, alert_id: str, lead_id: str, lead_data: Dict[str, Any]):
        """Start background thread for escalation timing"""
        def escalation_worker():
            try:
                time.sleep(self.response_timeout)

                # Check if still not responded
                alert_data = self._get_alert_data(alert_id)
                if alert_data and alert_data['status'] != AlertStatus.RESPONDED.value:
                    self.escalate_if_no_response(alert_id, lead_id)

            except Exception as e:
                logger.error(f"Error in escalation worker: {str(e)}")

        thread = threading.Thread(target=escalation_worker)
        thread.daemon = True
        thread.start()

        # Store thread reference
        self.escalation_threads[alert_id] = thread

    def _cancel_escalation(self, alert_id: str):
        """Cancel escalation timer if running"""
        if alert_id in self.escalation_threads:
            # Thread will check status and exit
            del self.escalation_threads[alert_id]

    def _get_alert_data(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Get alert data from Redis"""
        try:
            data = redis_client.get(f"alert:{alert_id}")
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error getting alert data: {str(e)}")
            return None

    def _get_escalation_level(self, alert_data: Dict[str, Any]) -> int:
        """Determine current escalation level"""
        created_at = datetime.fromisoformat(alert_data['created_at'])
        elapsed = (datetime.utcnow() - created_at).total_seconds()

        for i, level in enumerate(self.escalation_levels):
            if elapsed >= level['time']:
                current_level = i

        return current_level

    def _find_escalation_recipients(self, level: int) -> List[Dict[str, Any]]:
        """Find recipients for escalation level"""
        try:
            roles = self.escalation_levels[level]['roles']

            supabase = get_supabase_client()
            recipients = supabase.table('users').select('id', 'name', 'email', 'phone')\
                          .in_('role', roles).eq('status', 'available').execute()

            return recipients.data if recipients.data else []

        except Exception as e:
            logger.error(f"Error finding escalation recipients: {str(e)}")
            return []

    def _record_alert_in_database(self, alert_id: str, lead_id: str,
                                 assigned_to: str, priority: str):
        """Record alert in database for persistence"""
        try:
            alert_record = {
                'id': alert_id,
                'lead_id': lead_id,
                'assigned_to': assigned_to,
                'priority': priority,
                'status': AlertStatus.PENDING.value,
                'created_at': datetime.utcnow()
            }

            supabase = get_supabase_client()
            supabase.table('lead_alerts').insert(alert_record).execute()

        except Exception as e:
            logger.error(f"Error recording alert in database: {str(e)}")

    def _calculate_hourly_distribution(self, metrics: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate response distribution by hour"""
        distribution = {str(h): 0 for h in range(24)}

        for metric in metrics:
            hour = datetime.fromisoformat(metric['created_at']).hour
            distribution[str(hour)] += 1

        return distribution

    def _calculate_team_leaderboard(self, metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate team member leaderboard"""
        member_stats = {}

        for metric in metrics:
            member_id = metric['responded_by']

            if member_id not in member_stats:
                member_stats[member_id] = {
                    'member_id': member_id,
                    'total_responses': 0,
                    'total_time': 0,
                    'within_target': 0
                }

            member_stats[member_id]['total_responses'] += 1
            member_stats[member_id]['total_time'] += metric['response_seconds']

            if metric['within_target']:
                member_stats[member_id]['within_target'] += 1

        # Calculate averages and rates
        leaderboard = []
        for member_id, stats in member_stats.items():
            stats['avg_response_time'] = stats['total_time'] / stats['total_responses']
            stats['target_rate'] = (stats['within_target'] / stats['total_responses']) * 100
            leaderboard.append(stats)

        # Sort by target rate, then by average response time
        leaderboard.sort(key=lambda x: (x['target_rate'], -x['avg_response_time']), reverse=True)

        return leaderboard[:10]  # Top 10

    def _get_team_members(self, team_id: str) -> List[Dict[str, Any]]:
        """Get team members for a specific team"""
        try:
            supabase = get_supabase_client()
            members = supabase.table('team_members').select('user_id').eq('team_id', team_id).execute()
            return [{'id': m['user_id']} for m in members.data] if members.data else []
        except Exception as e:
            logger.error(f"Error getting team members: {str(e)}")
            return []


# Import json for Redis serialization
import json

# Create singleton instance
alert_service = AlertService()


# Exported functions for convenience
def trigger_lead_alert(lead_id: str, lead_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Convenience function to trigger lead alert"""
    return alert_service.trigger_lead_alert(lead_id, lead_data)


def acknowledge_alert(alert_id: str, user_id: str) -> bool:
    """Convenience function to acknowledge alert"""
    return alert_service.acknowledge_alert(alert_id, user_id)


def mark_responded(alert_id: str, user_id: str, response_data: Dict[str, Any]) -> bool:
    """Convenience function to mark alert as responded"""
    return alert_service.mark_responded(alert_id, user_id, response_data)


def get_response_metrics(team_id: Optional[str] = None, period_days: int = 30) -> Dict[str, Any]:
    """Convenience function to get response metrics"""
    return alert_service.get_team_response_metrics(team_id, period_days)