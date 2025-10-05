"""
Team Management Service for iSwitch Roofs CRM
Version: 1.0.0
Date: 2025-01-04

Comprehensive team management with performance tracking, territory management,
skill-based routing, and commission calculations.

Features:
- Team member CRUD operations
- Performance tracking and scoring
- Territory and skill-based lead assignment
- Commission calculations with tiered structures
- Real-time availability with Pusher presence
- Shift scheduling and time tracking
"""

import os
import logging
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from decimal import Decimal
import statistics

# Caching
import redis
from functools import lru_cache

# Database
from app.config import get_supabase_client, get_redis_client

# Real-time updates
from app.utils.pusher_client import get_pusher_service

logger = logging.getLogger(__name__)


class TeamRole(str, Enum):
    """Team member roles"""
    ADMIN = "admin"
    MANAGER = "manager"
    SALES_REP = "sales_rep"
    FIELD_TECH = "field_tech"
    ESTIMATOR = "estimator"
    CUSTOMER_SERVICE = "customer_service"


class SkillType(str, Enum):
    """Skill categories for team members"""
    ROOFING_SHINGLE = "roofing_shingle"
    ROOFING_METAL = "roofing_metal"
    ROOFING_FLAT = "roofing_flat"
    ROOFING_TILE = "roofing_tile"
    SALES = "sales"
    ESTIMATION = "estimation"
    PROJECT_MANAGEMENT = "project_management"
    CUSTOMER_SERVICE = "customer_service"
    LANGUAGE_SPANISH = "language_spanish"
    LANGUAGE_ARABIC = "language_arabic"
    CERTIFICATION_GAF = "certification_gaf"
    CERTIFICATION_OWENS = "certification_owens"


class CommissionTier(str, Enum):
    """Commission tier levels"""
    BRONZE = "bronze"  # 0-10% commission
    SILVER = "silver"  # 10-15% commission
    GOLD = "gold"      # 15-20% commission
    PLATINUM = "platinum"  # 20%+ commission


class TeamService:
    """
    Service for managing team members, performance, and assignments.

    Provides comprehensive team management including skills, territories,
    performance tracking, and commission calculations.
    """

    def __init__(self):
        """Initialize team service"""
        self._supabase = None
        self._redis = None
        self._pusher = None

        # Cache configuration
        self.cache_ttl = {
            'availability': 60,     # 1 minute for real-time availability
            'performance': 300,     # 5 minutes for performance metrics
            'territories': 3600,    # 1 hour for territory data
        }

        # Commission structure
        self.commission_rates = {
            CommissionTier.BRONZE: {
                'min_rate': 0.05,
                'max_rate': 0.10,
                'threshold': 0,
            },
            CommissionTier.SILVER: {
                'min_rate': 0.10,
                'max_rate': 0.15,
                'threshold': 500000,  # $500k in sales
            },
            CommissionTier.GOLD: {
                'min_rate': 0.15,
                'max_rate': 0.20,
                'threshold': 1000000,  # $1M in sales
            },
            CommissionTier.PLATINUM: {
                'min_rate': 0.20,
                'max_rate': 0.25,
                'threshold': 2000000,  # $2M in sales
            },
        }

        # Performance weights
        self.performance_weights = {
            'conversion_rate': 0.30,
            'response_time': 0.20,
            'revenue_generated': 0.25,
            'customer_satisfaction': 0.15,
            'activity_level': 0.10,
        }

    @property
    def supabase(self):
        """Lazy load Supabase client"""
        if self._supabase is None:
            self._supabase = get_supabase_client()
        return self._supabase

    @property
    def redis_client(self):
        """Lazy load Redis client"""
        if self._redis is None:
            self._redis = get_redis_client()
        return self._redis

    @property
    def pusher_service(self):
        """Lazy load Pusher service"""
        if self._pusher is None:
            self._pusher = get_pusher_service()
        return self._pusher

    def create_team_member(self,
                           name: str,
                           email: str,
                           role: str,
                           phone: Optional[str] = None,
                           skills: Optional[List[str]] = None,
                           territories: Optional[List[str]] = None,
                           hire_date: Optional[datetime] = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Create a new team member

        Args:
            name: Team member name
            email: Email address
            role: Team role
            phone: Phone number
            skills: List of skills
            territories: List of assigned territories (zip codes)
            hire_date: Date of hire

        Returns:
            Tuple of (success, team_member_data, error_message)
        """
        try:
            # Validate role
            if role not in [r.value for r in TeamRole]:
                return False, None, f"Invalid role: {role}"

            # Check if email already exists
            existing = self.supabase.table('team_members').select('id').eq('email', email).execute()
            if existing.data:
                return False, None, f"Team member with email {email} already exists"

            # Create team member record
            team_member_data = {
                'name': name,
                'email': email,
                'role': role,
                'phone': phone,
                'skills': skills or [],
                'territories': territories or [],
                'hire_date': (hire_date or datetime.utcnow()).isoformat(),
                'is_active': True,
                'is_available': True,
                'performance_score': 0,
                'commission_tier': CommissionTier.BRONZE,
                'total_sales': 0,
                'created_at': datetime.utcnow().isoformat(),
            }

            result = self.supabase.table('team_members').insert(team_member_data).execute()

            if not result.data:
                return False, None, "Failed to create team member"

            team_member = result.data[0]

            # Initialize performance metrics
            self._initialize_performance_metrics(team_member['id'])

            # Broadcast team member creation
            self._broadcast_team_update('member_added', team_member)

            logger.info(f"Team member created: {team_member['id']}")
            return True, team_member, None

        except Exception as e:
            logger.error(f"Error creating team member: {str(e)}")
            return False, None, str(e)

    def update_team_member(self,
                          member_id: str,
                          updates: Dict) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Update team member information

        Args:
            member_id: Team member ID
            updates: Dictionary of updates

        Returns:
            Tuple of (success, updated_member, error_message)
        """
        try:
            # Get existing member
            result = self.supabase.table('team_members').select('*').eq('id', member_id).execute()

            if not result.data:
                return False, None, "Team member not found"

            # Validate role if being updated
            if 'role' in updates:
                if updates['role'] not in [r.value for r in TeamRole]:
                    return False, None, f"Invalid role: {updates['role']}"

            # Update team member
            updates['updated_at'] = datetime.utcnow().isoformat()

            result = self.supabase.table('team_members').update(updates).eq('id', member_id).execute()

            if not result.data:
                return False, None, "Failed to update team member"

            updated_member = result.data[0]

            # Clear caches
            self._clear_member_cache(member_id)

            # Broadcast update
            self._broadcast_team_update('member_updated', updated_member)

            logger.info(f"Team member updated: {member_id}")
            return True, updated_member, None

        except Exception as e:
            logger.error(f"Error updating team member: {str(e)}")
            return False, None, str(e)

    def get_team_members(self,
                        role: Optional[str] = None,
                        is_active: Optional[bool] = True,
                        territory: Optional[str] = None) -> List[Dict]:
        """
        Get team members with filtering

        Args:
            role: Filter by role
            is_active: Filter by active status
            territory: Filter by territory (zip code)

        Returns:
            List of team members
        """
        try:
            query = self.supabase.table('team_members').select('*')

            if role:
                query = query.eq('role', role)

            if is_active is not None:
                query = query.eq('is_active', is_active)

            if territory:
                query = query.contains('territories', [territory])

            result = query.execute()

            team_members = result.data if result.data else []

            # Add real-time availability status
            for member in team_members:
                member['is_online'] = self._check_online_status(member['id'])
                member['current_workload'] = self._get_current_workload(member['id'])

            return team_members

        except Exception as e:
            logger.error(f"Error getting team members: {str(e)}")
            return []

    def assign_lead_to_member(self,
                             lead_id: str,
                             lead_data: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Assign lead to best available team member based on skills and territory

        Args:
            lead_id: Lead ID
            lead_data: Lead information (location, requirements, etc.)

        Returns:
            Tuple of (success, assigned_member_id, error_message)
        """
        try:
            # Get lead location (zip code)
            location = lead_data.get('zip_code')
            required_skills = lead_data.get('required_skills', [])

            # Find available team members
            available_members = self._find_available_members(location, required_skills)

            if not available_members:
                return False, None, "No available team members for this lead"

            # Score and rank members
            scored_members = []
            for member in available_members:
                score = self._calculate_assignment_score(member, lead_data)
                scored_members.append((score, member))

            # Sort by score (highest first)
            scored_members.sort(key=lambda x: x[0], reverse=True)

            # Assign to best match
            best_member = scored_members[0][1]

            # Update lead assignment
            update_result = self.supabase.table('leads').update({
                'assigned_to': best_member['id'],
                'assigned_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
            }).eq('id', lead_id).execute()

            if not update_result.data:
                return False, None, "Failed to update lead assignment"

            # Update member workload
            self._update_workload(best_member['id'], 1)

            # Send notification via Pusher
            self.pusher_service.send_notification(
                best_member['id'],
                "New Lead Assigned",
                f"You have been assigned a new lead in {location}",
                "info"
            )

            # Broadcast assignment
            self.pusher_service.broadcast_lead_assigned(
                lead_id,
                best_member['id'],
                'system'
            )

            logger.info(f"Lead {lead_id} assigned to {best_member['id']}")
            return True, best_member['id'], None

        except Exception as e:
            logger.error(f"Error assigning lead: {str(e)}")
            return False, None, str(e)

    def calculate_performance(self,
                            member_id: str,
                            start_date: datetime,
                            end_date: datetime) -> Dict:
        """
        Calculate comprehensive performance metrics for a team member

        Args:
            member_id: Team member ID
            start_date: Period start date
            end_date: Period end date

        Returns:
            Performance metrics dictionary
        """
        try:
            # Check cache first
            cache_key = f"performance:{member_id}:{start_date.date()}:{end_date.date()}"
            cached = self._get_cached_data(cache_key)
            if cached:
                return cached

            # Get leads handled
            leads_result = self.supabase.table('leads').select(
                'id', 'status', 'response_time_minutes', 'lead_score'
            ).eq('assigned_to', member_id).gte('created_at', start_date.isoformat()).lte('created_at', end_date.isoformat()).execute()

            leads = leads_result.data if leads_result.data else []

            # Calculate conversion metrics
            total_leads = len(leads)
            converted = len([l for l in leads if l.get('status') == 'converted'])
            conversion_rate = (converted / max(total_leads, 1)) * 100

            # Response time metrics
            response_times = [l.get('response_time_minutes', 0) for l in leads if l.get('response_time_minutes')]
            avg_response_time = statistics.mean(response_times) if response_times else 0

            # Get revenue generated
            projects_result = self.supabase.table('projects').select(
                'quoted_amount', 'actual_amount', 'status'
            ).eq('sales_rep_id', member_id).gte('created_at', start_date.isoformat()).lte('created_at', end_date.isoformat()).execute()

            projects = projects_result.data if projects_result.data else []

            total_revenue = sum(
                float(p.get('actual_amount', 0))
                for p in projects
                if p.get('status') == 'completed'
            )

            # Get customer satisfaction
            reviews_result = self.supabase.table('reviews').select('rating').eq('team_member_id', member_id).gte('created_at', start_date.isoformat()).lte('created_at', end_date.isoformat()).execute()

            ratings = [r.get('rating', 0) for r in (reviews_result.data if reviews_result.data else [])]
            avg_rating = statistics.mean(ratings) if ratings else 0

            # Get activity level
            interactions_result = self.supabase.table('interactions').select('id').eq('team_member_id', member_id).gte('created_at', start_date.isoformat()).lte('created_at', end_date.isoformat()).execute()

            total_activities = len(interactions_result.data) if interactions_result.data else 0

            # Calculate performance score
            performance_score = self._calculate_performance_score({
                'conversion_rate': conversion_rate,
                'avg_response_time': avg_response_time,
                'total_revenue': total_revenue,
                'avg_rating': avg_rating,
                'total_activities': total_activities,
            })

            metrics = {
                'member_id': member_id,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                },
                'leads': {
                    'total': total_leads,
                    'converted': converted,
                    'conversion_rate': round(conversion_rate, 2),
                },
                'response': {
                    'avg_time_minutes': round(avg_response_time, 2),
                    'under_2_min': len([r for r in response_times if r < 2]),
                },
                'revenue': {
                    'total': round(total_revenue, 2),
                    'per_lead': round(total_revenue / max(total_leads, 1), 2),
                },
                'satisfaction': {
                    'avg_rating': round(avg_rating, 2),
                    'review_count': len(ratings),
                },
                'activity': {
                    'total_interactions': total_activities,
                    'daily_average': round(total_activities / max((end_date - start_date).days, 1), 2),
                },
                'performance_score': round(performance_score, 2),
            }

            # Cache results
            self._cache_data(cache_key, metrics, self.cache_ttl['performance'])

            return metrics

        except Exception as e:
            logger.error(f"Error calculating performance: {str(e)}")
            return {}

    def calculate_commission(self,
                            member_id: str,
                            start_date: datetime,
                            end_date: datetime) -> Dict:
        """
        Calculate commission for a team member

        Args:
            member_id: Team member ID
            start_date: Period start date
            end_date: Period end date

        Returns:
            Commission calculation details
        """
        try:
            # Get team member details
            member_result = self.supabase.table('team_members').select(
                'commission_tier', 'total_sales', 'role'
            ).eq('id', member_id).execute()

            if not member_result.data:
                return {'error': 'Team member not found'}

            member = member_result.data[0]

            # Get completed projects in period
            projects_result = self.supabase.table('projects').select(
                'actual_amount', 'margin_percentage', 'completed_at'
            ).eq('sales_rep_id', member_id).eq('status', 'completed').gte('completed_at', start_date.isoformat()).lte('completed_at', end_date.isoformat()).execute()

            projects = projects_result.data if projects_result.data else []

            # Calculate base commission
            total_revenue = sum(float(p.get('actual_amount', 0)) for p in projects)

            # Get commission tier and rate
            tier = CommissionTier(member.get('commission_tier', CommissionTier.BRONZE))
            tier_config = self.commission_rates[tier]

            # Calculate rate based on performance
            performance = self.calculate_performance(member_id, start_date, end_date)
            performance_score = performance.get('performance_score', 50)

            # Scale commission rate based on performance
            rate_range = tier_config['max_rate'] - tier_config['min_rate']
            commission_rate = tier_config['min_rate'] + (rate_range * (performance_score / 100))

            # Calculate commission
            base_commission = total_revenue * commission_rate

            # Add bonuses
            bonuses = 0

            # Fast response bonus (all leads responded < 2 min)
            if performance.get('response', {}).get('avg_time_minutes', 999) < 2:
                bonuses += 500

            # High conversion bonus (> 30% conversion)
            if performance.get('leads', {}).get('conversion_rate', 0) > 30:
                bonuses += 1000

            # Customer satisfaction bonus (> 4.5 rating)
            if performance.get('satisfaction', {}).get('avg_rating', 0) > 4.5:
                bonuses += 750

            total_commission = base_commission + bonuses

            # Check for tier upgrade
            total_sales = float(member.get('total_sales', 0)) + total_revenue
            next_tier = self._get_next_tier(total_sales)

            return {
                'member_id': member_id,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                },
                'revenue': {
                    'total': round(total_revenue, 2),
                    'project_count': len(projects),
                },
                'commission': {
                    'tier': tier,
                    'rate': round(commission_rate * 100, 2),
                    'base': round(base_commission, 2),
                    'bonuses': round(bonuses, 2),
                    'total': round(total_commission, 2),
                },
                'performance_score': round(performance_score, 2),
                'next_tier': {
                    'tier': next_tier,
                    'required_sales': self.commission_rates[next_tier]['threshold'] if next_tier != tier else None,
                    'current_sales': round(total_sales, 2),
                },
            }

        except Exception as e:
            logger.error(f"Error calculating commission: {str(e)}")
            return {'error': str(e)}

    def update_availability(self,
                          member_id: str,
                          is_available: bool,
                          reason: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Update team member availability

        Args:
            member_id: Team member ID
            is_available: Availability status
            reason: Reason for unavailability

        Returns:
            Tuple of (success, error_message)
        """
        try:
            updates = {
                'is_available': is_available,
                'availability_updated_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
            }

            if reason and not is_available:
                updates['unavailable_reason'] = reason

            result = self.supabase.table('team_members').update(updates).eq('id', member_id).execute()

            if not result.data:
                return False, "Failed to update availability"

            # Update Pusher presence channel
            if is_available:
                self._join_presence_channel(member_id)
            else:
                self._leave_presence_channel(member_id)

            # Broadcast availability change
            self.pusher_service.trigger(
                'presence-team',
                'availability_changed',
                {
                    'member_id': member_id,
                    'is_available': is_available,
                    'timestamp': datetime.utcnow().isoformat(),
                }
            )

            # Clear cache
            cache_key = f"availability:{member_id}"
            self.redis_client.delete(cache_key)

            logger.info(f"Availability updated for {member_id}: {is_available}")
            return True, None

        except Exception as e:
            logger.error(f"Error updating availability: {str(e)}")
            return False, str(e)

    def get_team_territories(self) -> Dict[str, List[str]]:
        """
        Get all territory assignments

        Returns:
            Dictionary of member_id to list of territories
        """
        try:
            # Check cache
            cache_key = "territories:all"
            cached = self._get_cached_data(cache_key)
            if cached:
                return cached

            result = self.supabase.table('team_members').select(
                'id', 'name', 'territories'
            ).eq('is_active', True).execute()

            territories = {}
            for member in (result.data if result.data else []):
                if member.get('territories'):
                    territories[member['id']] = {
                        'name': member['name'],
                        'territories': member['territories'],
                    }

            # Cache results
            self._cache_data(cache_key, territories, self.cache_ttl['territories'])

            return territories

        except Exception as e:
            logger.error(f"Error getting territories: {str(e)}")
            return {}

    # Private helper methods
    def _initialize_performance_metrics(self, member_id: str):
        """Initialize performance metrics for new team member"""
        try:
            self.supabase.table('team_performance').insert({
                'team_member_id': member_id,
                'performance_score': 0,
                'total_leads': 0,
                'converted_leads': 0,
                'total_revenue': 0,
                'avg_response_time': 0,
                'avg_customer_rating': 0,
                'created_at': datetime.utcnow().isoformat(),
            }).execute()
        except Exception as e:
            logger.error(f"Error initializing performance metrics: {str(e)}")

    def _find_available_members(self, location: str, required_skills: List[str]) -> List[Dict]:
        """Find available team members for a location and skill set"""
        try:
            query = self.supabase.table('team_members').select('*').eq('is_active', True).eq('is_available', True)

            # Filter by territory if specified
            if location:
                query = query.contains('territories', [location])

            result = query.execute()
            members = result.data if result.data else []

            # Filter by skills if required
            if required_skills:
                members = [
                    m for m in members
                    if any(skill in m.get('skills', []) for skill in required_skills)
                ]

            return members

        except Exception as e:
            logger.error(f"Error finding available members: {str(e)}")
            return []

    def _calculate_assignment_score(self, member: Dict, lead_data: Dict) -> float:
        """Calculate score for lead assignment"""
        score = 0

        # Territory match (40 points)
        if lead_data.get('zip_code') in member.get('territories', []):
            score += 40

        # Skill match (30 points)
        required_skills = lead_data.get('required_skills', [])
        member_skills = member.get('skills', [])
        skill_match_ratio = len(set(required_skills) & set(member_skills)) / max(len(required_skills), 1)
        score += skill_match_ratio * 30

        # Performance score (20 points)
        score += (member.get('performance_score', 0) / 100) * 20

        # Workload balance (10 points) - favor members with fewer current leads
        current_workload = self._get_current_workload(member['id'])
        if current_workload < 5:
            score += 10
        elif current_workload < 10:
            score += 5

        return score

    def _calculate_performance_score(self, metrics: Dict) -> float:
        """Calculate weighted performance score"""
        score = 0

        # Conversion rate (30%)
        conv_rate = metrics.get('conversion_rate', 0)
        score += min(30, (conv_rate / 30) * 30)  # Target: 30% conversion

        # Response time (20%)
        response_time = metrics.get('avg_response_time', 999)
        response_score = max(0, 20 - (response_time / 10))
        score += response_score

        # Revenue (25%)
        revenue = metrics.get('total_revenue', 0)
        revenue_score = min(25, (revenue / 100000) * 25)  # Scale to $100k
        score += revenue_score

        # Customer satisfaction (15%)
        rating = metrics.get('avg_rating', 0)
        score += (rating / 5) * 15

        # Activity level (10%)
        activities = metrics.get('total_activities', 0)
        activity_score = min(10, (activities / 100) * 10)  # Scale to 100 activities
        score += activity_score

        return min(100, score)

    def _get_next_tier(self, total_sales: float) -> CommissionTier:
        """Determine next commission tier based on total sales"""
        if total_sales >= self.commission_rates[CommissionTier.PLATINUM]['threshold']:
            return CommissionTier.PLATINUM
        elif total_sales >= self.commission_rates[CommissionTier.GOLD]['threshold']:
            return CommissionTier.GOLD
        elif total_sales >= self.commission_rates[CommissionTier.SILVER]['threshold']:
            return CommissionTier.SILVER
        else:
            return CommissionTier.BRONZE

    def _get_current_workload(self, member_id: str) -> int:
        """Get current number of active leads for a team member"""
        try:
            result = self.supabase.table('leads').select('id').eq('assigned_to', member_id).in_('status', ['new', 'contacted', 'qualified']).execute()
            return len(result.data) if result.data else 0
        except:
            return 0

    def _update_workload(self, member_id: str, change: int):
        """Update team member workload cache"""
        try:
            cache_key = f"workload:{member_id}"
            current = self.redis_client.get(cache_key)
            new_workload = (int(current) if current else 0) + change
            self.redis_client.setex(cache_key, 3600, new_workload)
        except Exception as e:
            logger.error(f"Error updating workload: {str(e)}")

    def _check_online_status(self, member_id: str) -> bool:
        """Check if team member is online via Pusher presence"""
        try:
            cache_key = f"online:{member_id}"
            cached = self.redis_client.get(cache_key)
            if cached is not None:
                return cached == b'1'

            # In production, this would check Pusher presence channel
            # For now, return True if available
            result = self.supabase.table('team_members').select('is_available').eq('id', member_id).execute()
            is_online = result.data[0]['is_available'] if result.data else False

            self.redis_client.setex(cache_key, 60, '1' if is_online else '0')
            return is_online

        except:
            return False

    def _join_presence_channel(self, member_id: str):
        """Join Pusher presence channel"""
        try:
            # This would be handled client-side in production
            # Server tracks presence state
            cache_key = f"presence:{member_id}"
            self.redis_client.setex(cache_key, 3600, '1')
        except Exception as e:
            logger.error(f"Error joining presence channel: {str(e)}")

    def _leave_presence_channel(self, member_id: str):
        """Leave Pusher presence channel"""
        try:
            cache_key = f"presence:{member_id}"
            self.redis_client.delete(cache_key)
        except Exception as e:
            logger.error(f"Error leaving presence channel: {str(e)}")

    def _broadcast_team_update(self, event_type: str, data: Dict):
        """Broadcast team update via Pusher"""
        try:
            if self.pusher_service.is_available():
                self.pusher_service.trigger(
                    'team',
                    event_type,
                    data
                )
        except Exception as e:
            logger.error(f"Error broadcasting team update: {str(e)}")

    def _get_cached_data(self, key: str) -> Optional[Dict]:
        """Get data from Redis cache"""
        try:
            if self.redis_client:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
        except Exception as e:
            logger.error(f"Error getting cached data: {str(e)}")
        return None

    def _cache_data(self, key: str, data: Dict, ttl: int):
        """Cache data in Redis"""
        try:
            if self.redis_client:
                self.redis_client.setex(key, ttl, json.dumps(data))
        except Exception as e:
            logger.error(f"Error caching data: {str(e)}")

    def _clear_member_cache(self, member_id: str):
        """Clear all caches for a team member"""
        try:
            patterns = [
                f"performance:{member_id}:*",
                f"availability:{member_id}",
                f"workload:{member_id}",
                f"online:{member_id}",
            ]
            for pattern in patterns:
                for key in self.redis_client.scan_iter(match=pattern):
                    self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Error clearing member cache: {str(e)}")


# Create singleton instance
team_service = TeamService()