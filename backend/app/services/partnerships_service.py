"""
Partnerships Service Module

Handles partner relationship management including:
- Partner onboarding and management
- Referral tracking and attribution
- Commission calculations
- Performance analytics
- Partner portal access
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json
import uuid
import hashlib
from decimal import Decimal
from collections import defaultdict
import statistics
from functools import wraps
import os
import logging

# Third-party imports
from cachetools import TTLCache
import redis
import bcrypt

# Local imports
from app.utils.supabase_client import SupabaseClient
from app.utils.pusher_client import PusherClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PartnershipsService:
    """Service for managing partner relationships and referrals"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PartnershipsService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._supabase = None
        self._pusher = None
        self._redis = None
        self._cache = TTLCache(maxsize=100, ttl=300)  # 5 minute cache

        # Partner categories with commission structures
        self.partner_categories = {
            'insurance_agent': {
                'name': 'Insurance Agent',
                'base_commission': 0.10,  # 10% base commission
                'tier_multipliers': {
                    'bronze': 1.0,     # 0-5 referrals/month
                    'silver': 1.1,     # 6-10 referrals/month
                    'gold': 1.2,       # 11-20 referrals/month
                    'platinum': 1.3    # 20+ referrals/month
                }
            },
            'real_estate_agent': {
                'name': 'Real Estate Agent',
                'base_commission': 0.08,  # 8% base commission
                'tier_multipliers': {
                    'bronze': 1.0,
                    'silver': 1.15,
                    'gold': 1.25,
                    'platinum': 1.35
                }
            },
            'property_manager': {
                'name': 'Property Manager',
                'base_commission': 0.12,  # 12% base commission
                'tier_multipliers': {
                    'bronze': 1.0,
                    'silver': 1.1,
                    'gold': 1.2,
                    'platinum': 1.3
                }
            },
            'contractor': {
                'name': 'General Contractor',
                'base_commission': 0.07,  # 7% base commission
                'tier_multipliers': {
                    'bronze': 1.0,
                    'silver': 1.15,
                    'gold': 1.3,
                    'platinum': 1.4
                }
            },
            'home_inspector': {
                'name': 'Home Inspector',
                'base_commission': 0.09,  # 9% base commission
                'tier_multipliers': {
                    'bronze': 1.0,
                    'silver': 1.1,
                    'gold': 1.2,
                    'platinum': 1.35
                }
            }
        }

        # Referral status workflow
        self.referral_statuses = [
            'pending',      # Initial referral received
            'contacted',    # Customer contacted
            'scheduled',    # Appointment scheduled
            'quoted',       # Quote provided
            'won',          # Contract signed
            'completed',    # Project completed
            'paid',         # Commission paid
            'lost',         # Lost opportunity
            'cancelled'     # Cancelled referral
        ]

    @property
    def supabase(self):
        """Lazy initialization of Supabase client"""
        if self._supabase is None:
            self._supabase = SupabaseClient()
        return self._supabase

    @property
    def pusher(self):
        """Lazy initialization of Pusher client"""
        if self._pusher is None:
            self._pusher = PusherClient()
        return self._pusher

    @property
    def redis_client(self):
        """Lazy initialization of Redis client"""
        if self._redis is None:
            try:
                self._redis = redis.StrictRedis(
                    host=os.environ.get('REDIS_HOST', 'localhost'),
                    port=int(os.environ.get('REDIS_PORT', 6379)),
                    db=0,
                    decode_responses=True
                )
                self._redis.ping()
            except:
                logger.warning("Redis not available, using in-memory cache only")
                self._redis = None
        return self._redis

    def _cache_result(self, key: str, data: Any, ttl: int = 300):
        """Cache result in Redis and memory"""
        self._cache[key] = data
        if self.redis_client:
            try:
                self.redis_client.setex(key, ttl, json.dumps(data))
            except:
                pass

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached result from Redis or memory"""
        if key in self._cache:
            return self._cache[key]

        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            except:
                pass

        return None

    # Partner Management

    def create_partner(self, partner_data: Dict) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Create a new partner"""
        try:
            # Validate required fields
            required_fields = ['company_name', 'contact_name', 'email', 'phone', 'category']
            for field in required_fields:
                if field not in partner_data:
                    return False, None, f"Missing required field: {field}"

            # Validate category
            category = partner_data['category']
            if category not in self.partner_categories:
                return False, None, f"Invalid category: {category}"

            # Check if email already exists
            existing = self.supabase.client.table('partners').select('*').eq(
                'email', partner_data['email']
            ).execute()

            if existing.data:
                return False, None, "Partner with this email already exists"

            # Generate partner code
            partner_code = self._generate_partner_code(partner_data['company_name'])

            # Generate API key for portal access
            api_key = self._generate_api_key()

            # Hash password if provided
            password_hash = None
            if partner_data.get('password'):
                password_hash = bcrypt.hashpw(
                    partner_data['password'].encode('utf-8'),
                    bcrypt.gensalt()
                ).decode('utf-8')

            # Create partner record
            partner = {
                'company_name': partner_data['company_name'],
                'contact_name': partner_data['contact_name'],
                'email': partner_data['email'],
                'phone': partner_data['phone'],
                'category': category,
                'partner_code': partner_code,
                'api_key': api_key,
                'password_hash': password_hash,
                'address': partner_data.get('address'),
                'website': partner_data.get('website'),
                'license_number': partner_data.get('license_number'),
                'insurance_info': partner_data.get('insurance_info'),
                'tax_id': partner_data.get('tax_id'),
                'payment_method': partner_data.get('payment_method', 'check'),
                'payment_details': partner_data.get('payment_details', {}),
                'commission_rate': self.partner_categories[category]['base_commission'],
                'tier': 'bronze',
                'status': 'pending_approval',
                'onboarding_completed': False,
                'agreement_signed': False,
                'metadata': partner_data.get('metadata', {}),
                'created_at': datetime.utcnow().isoformat()
            }

            result = self.supabase.client.table('partners').insert(partner).execute()

            if result.data:
                partner_id = result.data[0]['id']

                # Create onboarding tasks
                self._create_onboarding_tasks(partner_id)

                # Send welcome notification
                self.pusher.trigger('partners', 'new-partner', {
                    'partner_id': partner_id,
                    'company_name': partner['company_name'],
                    'category': category
                })

                return True, {
                    'partner_id': partner_id,
                    'partner_code': partner_code,
                    'api_key': api_key
                }, None
            else:
                return False, None, "Failed to create partner"

        except Exception as e:
            logger.error(f"Create partner error: {e}")
            return False, None, str(e)

    def _generate_partner_code(self, company_name: str) -> str:
        """Generate unique partner referral code"""
        base = company_name.upper().replace(' ', '')[:3]
        random_suffix = uuid.uuid4().hex[:4].upper()
        return f"{base}-{random_suffix}"

    def _generate_api_key(self) -> str:
        """Generate API key for partner portal"""
        return f"pk_{uuid.uuid4().hex}"

    def _create_onboarding_tasks(self, partner_id: str):
        """Create onboarding checklist for new partner"""
        tasks = [
            {'task': 'Complete partner agreement', 'status': 'pending'},
            {'task': 'Provide insurance documentation', 'status': 'pending'},
            {'task': 'Set up payment information', 'status': 'pending'},
            {'task': 'Complete training module', 'status': 'pending'},
            {'task': 'Receive marketing materials', 'status': 'pending'},
            {'task': 'First referral bonus eligibility', 'status': 'pending'}
        ]

        for task in tasks:
            self.supabase.client.table('partner_onboarding').insert({
                'partner_id': partner_id,
                'task': task['task'],
                'status': task['status'],
                'created_at': datetime.utcnow().isoformat()
            }).execute()

    def update_partner(self, partner_id: str, updates: Dict) -> Tuple[bool, Optional[str]]:
        """Update partner information"""
        try:
            # Don't allow updating certain fields
            protected_fields = ['id', 'partner_code', 'api_key', 'created_at']
            for field in protected_fields:
                updates.pop(field, None)

            # Update password if provided
            if 'password' in updates:
                updates['password_hash'] = bcrypt.hashpw(
                    updates['password'].encode('utf-8'),
                    bcrypt.gensalt()
                ).decode('utf-8')
                del updates['password']

            updates['updated_at'] = datetime.utcnow().isoformat()

            result = self.supabase.client.table('partners').update(updates).eq(
                'id', partner_id
            ).execute()

            if result.data:
                # Clear cache
                cache_key = f"partner:{partner_id}"
                if cache_key in self._cache:
                    del self._cache[cache_key]

                return True, None
            else:
                return False, "Partner not found"

        except Exception as e:
            logger.error(f"Update partner error: {e}")
            return False, str(e)

    def get_partner(self, partner_id: str = None, partner_code: str = None,
                   email: str = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Get partner by ID, code, or email"""
        try:
            cache_key = f"partner:{partner_id or partner_code or email}"
            cached = self._get_cached(cache_key)
            if cached:
                return True, cached, None

            query = self.supabase.client.table('partners').select('*')

            if partner_id:
                query = query.eq('id', partner_id)
            elif partner_code:
                query = query.eq('partner_code', partner_code)
            elif email:
                query = query.eq('email', email)
            else:
                return False, None, "Must provide partner_id, partner_code, or email"

            result = query.single().execute()

            if result.data:
                # Get performance metrics
                metrics = self._calculate_partner_metrics(result.data['id'])
                result.data['metrics'] = metrics

                self._cache_result(cache_key, result.data)
                return True, result.data, None
            else:
                return False, None, "Partner not found"

        except Exception as e:
            logger.error(f"Get partner error: {e}")
            return False, None, str(e)

    def _calculate_partner_metrics(self, partner_id: str) -> Dict:
        """Calculate partner performance metrics"""
        try:
            # Get all referrals
            referrals = self.supabase.client.table('referrals').select('*').eq(
                'partner_id', partner_id
            ).execute()

            if not referrals.data:
                return {
                    'total_referrals': 0,
                    'conversion_rate': 0,
                    'total_revenue': 0,
                    'total_commission': 0,
                    'average_project_value': 0,
                    'current_month_referrals': 0,
                    'pending_commission': 0
                }

            # Calculate metrics
            total_referrals = len(referrals.data)
            won_referrals = [r for r in referrals.data if r.get('status') == 'won']
            completed_referrals = [r for r in referrals.data if r.get('status') == 'completed']

            conversion_rate = (len(won_referrals) / total_referrals * 100) if total_referrals > 0 else 0

            total_revenue = sum(float(r.get('project_value', 0)) for r in completed_referrals)
            total_commission = sum(float(r.get('commission_amount', 0)) for r in completed_referrals)

            avg_project_value = (total_revenue / len(completed_referrals)) if completed_referrals else 0

            # Current month referrals
            current_month = datetime.utcnow().month
            current_year = datetime.utcnow().year
            current_month_referrals = [
                r for r in referrals.data
                if datetime.fromisoformat(r['created_at']).month == current_month
                and datetime.fromisoformat(r['created_at']).year == current_year
            ]

            # Pending commission
            pending_referrals = [r for r in referrals.data if r.get('status') in ['won', 'completed'] and not r.get('commission_paid')]
            pending_commission = sum(float(r.get('commission_amount', 0)) for r in pending_referrals)

            return {
                'total_referrals': total_referrals,
                'conversion_rate': round(conversion_rate, 1),
                'total_revenue': round(total_revenue, 2),
                'total_commission': round(total_commission, 2),
                'average_project_value': round(avg_project_value, 2),
                'current_month_referrals': len(current_month_referrals),
                'pending_commission': round(pending_commission, 2),
                'won_referrals': len(won_referrals),
                'completed_referrals': len(completed_referrals)
            }

        except Exception as e:
            logger.error(f"Calculate partner metrics error: {e}")
            return {}

    # Referral Management

    def create_referral(self, referral_data: Dict) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Create a new referral"""
        try:
            # Validate required fields
            required_fields = ['partner_id', 'customer_name', 'customer_email', 'customer_phone']
            for field in required_fields:
                if field not in referral_data:
                    return False, None, f"Missing required field: {field}"

            # Validate partner exists
            partner = self.supabase.client.table('partners').select('*').eq(
                'id', referral_data['partner_id']
            ).single().execute()

            if not partner.data:
                return False, None, "Partner not found"

            if partner.data.get('status') != 'active':
                return False, None, "Partner is not active"

            # Generate referral code
            referral_code = self._generate_referral_code()

            # Create referral
            referral = {
                'partner_id': referral_data['partner_id'],
                'partner_code': partner.data['partner_code'],
                'referral_code': referral_code,
                'customer_name': referral_data['customer_name'],
                'customer_email': referral_data['customer_email'],
                'customer_phone': referral_data['customer_phone'],
                'customer_address': referral_data.get('customer_address'),
                'service_type': referral_data.get('service_type', 'roof_replacement'),
                'urgency': referral_data.get('urgency', 'normal'),
                'notes': referral_data.get('notes'),
                'status': 'pending',
                'source': referral_data.get('source', 'partner_portal'),
                'metadata': referral_data.get('metadata', {}),
                'created_at': datetime.utcnow().isoformat()
            }

            result = self.supabase.client.table('referrals').insert(referral).execute()

            if result.data:
                referral_id = result.data[0]['id']

                # Create lead from referral
                lead_id = self._create_lead_from_referral(referral, partner.data)

                # Update referral with lead_id
                self.supabase.client.table('referrals').update({
                    'lead_id': lead_id
                }).eq('id', referral_id).execute()

                # Send notifications
                self.pusher.trigger('referrals', 'new-referral', {
                    'referral_id': referral_id,
                    'partner_name': partner.data['company_name'],
                    'customer_name': referral['customer_name']
                })

                # Update partner tier if needed
                self._update_partner_tier(referral_data['partner_id'])

                return True, {
                    'referral_id': referral_id,
                    'referral_code': referral_code,
                    'lead_id': lead_id
                }, None
            else:
                return False, None, "Failed to create referral"

        except Exception as e:
            logger.error(f"Create referral error: {e}")
            return False, None, str(e)

    def _generate_referral_code(self) -> str:
        """Generate unique referral tracking code"""
        return f"REF-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    def _create_lead_from_referral(self, referral: Dict, partner: Dict) -> str:
        """Create a lead record from referral"""
        try:
            lead = {
                'name': referral['customer_name'],
                'email': referral['customer_email'],
                'phone': referral['customer_phone'],
                'address': referral.get('customer_address'),
                'source': 'partner_referral',
                'source_details': {
                    'partner_id': partner['id'],
                    'partner_name': partner['company_name'],
                    'referral_code': referral['referral_code']
                },
                'service_interest': referral.get('service_type'),
                'urgency': referral.get('urgency'),
                'status': 'new',
                'score': 80,  # High score for partner referrals
                'created_at': datetime.utcnow().isoformat()
            }

            result = self.supabase.client.table('leads').insert(lead).execute()
            return result.data[0]['id'] if result.data else None

        except Exception as e:
            logger.error(f"Create lead from referral error: {e}")
            return None

    def update_referral_status(self, referral_id: str, status: str,
                              project_value: float = None) -> Tuple[bool, Optional[str]]:
        """Update referral status and calculate commission"""
        try:
            if status not in self.referral_statuses:
                return False, f"Invalid status: {status}"

            # Get referral
            referral = self.supabase.client.table('referrals').select('*').eq(
                'id', referral_id
            ).single().execute()

            if not referral.data:
                return False, "Referral not found"

            # Get partner
            partner = self.supabase.client.table('partners').select('*').eq(
                'id', referral.data['partner_id']
            ).single().execute()

            if not partner.data:
                return False, "Partner not found"

            updates = {
                'status': status,
                f'{status}_at': datetime.utcnow().isoformat()
            }

            # Calculate commission for won/completed status
            if status in ['won', 'completed'] and project_value:
                updates['project_value'] = project_value
                commission = self._calculate_commission(
                    project_value,
                    partner.data['category'],
                    partner.data['tier']
                )
                updates['commission_amount'] = commission
                updates['commission_rate'] = partner.data['commission_rate']

            # Update referral
            result = self.supabase.client.table('referrals').update(updates).eq(
                'id', referral_id
            ).execute()

            if result.data:
                # Send notification
                self.pusher.trigger(f'partner-{referral.data["partner_id"]}', 'referral-updated', {
                    'referral_id': referral_id,
                    'status': status,
                    'project_value': project_value,
                    'commission': updates.get('commission_amount')
                })

                # Log status change
                self.supabase.client.table('referral_status_log').insert({
                    'referral_id': referral_id,
                    'old_status': referral.data['status'],
                    'new_status': status,
                    'changed_at': datetime.utcnow().isoformat(),
                    'metadata': {
                        'project_value': project_value,
                        'commission': updates.get('commission_amount')
                    }
                }).execute()

                return True, None
            else:
                return False, "Failed to update referral"

        except Exception as e:
            logger.error(f"Update referral status error: {e}")
            return False, str(e)

    def _calculate_commission(self, project_value: float, category: str, tier: str) -> float:
        """Calculate commission based on project value, category, and tier"""
        if category not in self.partner_categories:
            return 0

        base_rate = self.partner_categories[category]['base_commission']
        tier_multiplier = self.partner_categories[category]['tier_multipliers'].get(tier, 1.0)

        commission = project_value * base_rate * tier_multiplier
        return round(commission, 2)

    def _update_partner_tier(self, partner_id: str):
        """Update partner tier based on monthly performance"""
        try:
            # Get current month referrals
            current_month = datetime.utcnow().month
            current_year = datetime.utcnow().year

            referrals = self.supabase.client.table('referrals').select('*').eq(
                'partner_id', partner_id
            ).execute()

            monthly_referrals = [
                r for r in referrals.data
                if datetime.fromisoformat(r['created_at']).month == current_month
                and datetime.fromisoformat(r['created_at']).year == current_year
            ]

            # Determine tier
            count = len(monthly_referrals)
            if count >= 20:
                new_tier = 'platinum'
            elif count >= 11:
                new_tier = 'gold'
            elif count >= 6:
                new_tier = 'silver'
            else:
                new_tier = 'bronze'

            # Update if changed
            partner = self.supabase.client.table('partners').select('tier').eq(
                'id', partner_id
            ).single().execute()

            if partner.data and partner.data['tier'] != new_tier:
                self.supabase.client.table('partners').update({
                    'tier': new_tier,
                    'tier_updated_at': datetime.utcnow().isoformat()
                }).eq('id', partner_id).execute()

                # Send notification
                self.pusher.trigger(f'partner-{partner_id}', 'tier-updated', {
                    'new_tier': new_tier,
                    'monthly_referrals': count
                })

        except Exception as e:
            logger.error(f"Update partner tier error: {e}")

    # Commission Management

    def process_commission_payment(self, partner_id: str, referral_ids: List[str] = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Process commission payment for partner"""
        try:
            # Get unpaid commissions
            query = self.supabase.client.table('referrals').select('*').eq(
                'partner_id', partner_id
            ).in_('status', ['completed']).eq('commission_paid', False)

            if referral_ids:
                query = query.in_('id', referral_ids)

            referrals = query.execute()

            if not referrals.data:
                return False, None, "No unpaid commissions found"

            # Calculate total
            total_commission = sum(float(r.get('commission_amount', 0)) for r in referrals.data)
            referral_count = len(referrals.data)

            # Create payment record
            payment = {
                'partner_id': partner_id,
                'amount': total_commission,
                'referral_count': referral_count,
                'referral_ids': [r['id'] for r in referrals.data],
                'payment_method': 'pending',
                'status': 'pending',
                'created_at': datetime.utcnow().isoformat()
            }

            result = self.supabase.client.table('commission_payments').insert(payment).execute()

            if result.data:
                payment_id = result.data[0]['id']

                # Mark referrals as paid
                for referral in referrals.data:
                    self.supabase.client.table('referrals').update({
                        'commission_paid': True,
                        'commission_payment_id': payment_id,
                        'commission_paid_at': datetime.utcnow().isoformat()
                    }).eq('id', referral['id']).execute()

                return True, {
                    'payment_id': payment_id,
                    'amount': total_commission,
                    'referral_count': referral_count
                }, None
            else:
                return False, None, "Failed to create payment record"

        except Exception as e:
            logger.error(f"Process commission payment error: {e}")
            return False, None, str(e)

    def mark_payment_complete(self, payment_id: str, transaction_id: str = None) -> Tuple[bool, Optional[str]]:
        """Mark commission payment as complete"""
        try:
            updates = {
                'status': 'completed',
                'transaction_id': transaction_id,
                'paid_at': datetime.utcnow().isoformat()
            }

            result = self.supabase.client.table('commission_payments').update(updates).eq(
                'id', payment_id
            ).execute()

            if result.data:
                # Get payment details
                payment = result.data[0]

                # Send notification
                self.pusher.trigger(f'partner-{payment["partner_id"]}', 'payment-completed', {
                    'payment_id': payment_id,
                    'amount': payment['amount'],
                    'transaction_id': transaction_id
                })

                return True, None
            else:
                return False, "Payment not found"

        except Exception as e:
            logger.error(f"Mark payment complete error: {e}")
            return False, str(e)

    # Partner Portal

    def authenticate_partner(self, email: str, password: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Authenticate partner for portal access"""
        try:
            # Get partner by email
            partner = self.supabase.client.table('partners').select('*').eq(
                'email', email
            ).single().execute()

            if not partner.data:
                return False, None, "Invalid credentials"

            # Check password
            if not partner.data.get('password_hash'):
                return False, None, "Password not set"

            if not bcrypt.checkpw(password.encode('utf-8'),
                                 partner.data['password_hash'].encode('utf-8')):
                return False, None, "Invalid credentials"

            # Check if active
            if partner.data.get('status') != 'active':
                return False, None, "Partner account is not active"

            # Generate session token
            session_token = uuid.uuid4().hex

            # Store session
            self.supabase.client.table('partner_sessions').insert({
                'partner_id': partner.data['id'],
                'token': session_token,
                'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat(),
                'created_at': datetime.utcnow().isoformat()
            }).execute()

            # Get metrics
            metrics = self._calculate_partner_metrics(partner.data['id'])

            return True, {
                'partner': {
                    'id': partner.data['id'],
                    'company_name': partner.data['company_name'],
                    'contact_name': partner.data['contact_name'],
                    'email': partner.data['email'],
                    'category': partner.data['category'],
                    'tier': partner.data['tier'],
                    'partner_code': partner.data['partner_code']
                },
                'session_token': session_token,
                'metrics': metrics
            }, None

        except Exception as e:
            logger.error(f"Authenticate partner error: {e}")
            return False, None, str(e)

    def validate_partner_session(self, session_token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Validate partner portal session"""
        try:
            session = self.supabase.client.table('partner_sessions').select('*').eq(
                'token', session_token
            ).single().execute()

            if not session.data:
                return False, None, "Invalid session"

            # Check expiration
            expires_at = datetime.fromisoformat(session.data['expires_at'])
            if expires_at < datetime.utcnow():
                return False, None, "Session expired"

            # Get partner
            partner = self.supabase.client.table('partners').select('*').eq(
                'id', session.data['partner_id']
            ).single().execute()

            if not partner.data:
                return False, None, "Partner not found"

            return True, partner.data, None

        except Exception as e:
            logger.error(f"Validate session error: {e}")
            return False, None, str(e)

    def get_partner_dashboard(self, partner_id: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Get partner dashboard data"""
        try:
            cache_key = f"partner_dashboard:{partner_id}"
            cached = self._get_cached(cache_key)
            if cached:
                return True, cached, None

            # Get partner info
            partner = self.supabase.client.table('partners').select('*').eq(
                'id', partner_id
            ).single().execute()

            if not partner.data:
                return False, None, "Partner not found"

            # Get metrics
            metrics = self._calculate_partner_metrics(partner_id)

            # Get recent referrals
            recent_referrals = self.supabase.client.table('referrals').select('*').eq(
                'partner_id', partner_id
            ).order('created_at', desc=True).limit(10).execute()

            # Get commission history
            commission_history = self.supabase.client.table('commission_payments').select('*').eq(
                'partner_id', partner_id
            ).order('created_at', desc=True).limit(10).execute()

            # Get performance trends
            trends = self._calculate_partner_trends(partner_id)

            # Get marketing materials
            materials = self.supabase.client.table('marketing_materials').select('*').eq(
                'active', True
            ).execute()

            dashboard = {
                'partner': partner.data,
                'metrics': metrics,
                'recent_referrals': recent_referrals.data,
                'commission_history': commission_history.data,
                'trends': trends,
                'marketing_materials': materials.data,
                'referral_link': f"https://iswitchroofs.com/ref/{partner.data['partner_code']}"
            }

            # Cache result
            self._cache_result(cache_key, dashboard, ttl=300)

            return True, dashboard, None

        except Exception as e:
            logger.error(f"Get partner dashboard error: {e}")
            return False, None, str(e)

    def _calculate_partner_trends(self, partner_id: str) -> Dict:
        """Calculate partner performance trends"""
        try:
            # Get last 6 months of data
            six_months_ago = datetime.utcnow() - timedelta(days=180)

            referrals = self.supabase.client.table('referrals').select('*').eq(
                'partner_id', partner_id
            ).gte('created_at', six_months_ago.isoformat()).execute()

            if not referrals.data:
                return {'monthly_referrals': [], 'monthly_revenue': [], 'monthly_commission': []}

            # Group by month
            monthly_data = defaultdict(lambda: {
                'referrals': 0,
                'revenue': 0,
                'commission': 0
            })

            for referral in referrals.data:
                month_key = datetime.fromisoformat(referral['created_at']).strftime('%Y-%m')
                monthly_data[month_key]['referrals'] += 1

                if referral.get('status') == 'completed':
                    monthly_data[month_key]['revenue'] += float(referral.get('project_value', 0))
                    monthly_data[month_key]['commission'] += float(referral.get('commission_amount', 0))

            # Format for charts
            months = sorted(monthly_data.keys())
            trends = {
                'months': months,
                'monthly_referrals': [monthly_data[m]['referrals'] for m in months],
                'monthly_revenue': [monthly_data[m]['revenue'] for m in months],
                'monthly_commission': [monthly_data[m]['commission'] for m in months]
            }

            return trends

        except Exception as e:
            logger.error(f"Calculate partner trends error: {e}")
            return {}

    # Analytics

    def get_partnerships_analytics(self) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Get comprehensive partnership program analytics"""
        try:
            cache_key = "partnerships:analytics"
            cached = self._get_cached(cache_key)
            if cached:
                return True, cached, None

            # Get all partners
            partners = self.supabase.client.table('partners').select('*').execute()

            # Get all referrals
            referrals = self.supabase.client.table('referrals').select('*').execute()

            if not partners.data:
                return True, {'message': 'No partners found'}, None

            # Calculate overall metrics
            total_partners = len(partners.data)
            active_partners = len([p for p in partners.data if p.get('status') == 'active'])

            total_referrals = len(referrals.data) if referrals.data else 0
            won_referrals = len([r for r in referrals.data if r.get('status') == 'won']) if referrals.data else 0
            completed_referrals = len([r for r in referrals.data if r.get('status') == 'completed']) if referrals.data else 0

            # Revenue and commission
            total_revenue = sum(float(r.get('project_value', 0)) for r in referrals.data if r.get('status') == 'completed') if referrals.data else 0
            total_commission = sum(float(r.get('commission_amount', 0)) for r in referrals.data if r.get('commission_amount')) if referrals.data else 0
            pending_commission = sum(float(r.get('commission_amount', 0)) for r in referrals.data if r.get('commission_amount') and not r.get('commission_paid')) if referrals.data else 0

            # Category breakdown
            category_stats = defaultdict(lambda: {
                'partners': 0,
                'referrals': 0,
                'revenue': 0,
                'commission': 0
            })

            for partner in partners.data:
                category = partner.get('category')
                if category:
                    category_stats[category]['partners'] += 1

            if referrals.data:
                for referral in referrals.data:
                    # Find partner category
                    partner = next((p for p in partners.data if p['id'] == referral.get('partner_id')), None)
                    if partner:
                        category = partner.get('category')
                        if category:
                            category_stats[category]['referrals'] += 1
                            if referral.get('status') == 'completed':
                                category_stats[category]['revenue'] += float(referral.get('project_value', 0))
                                category_stats[category]['commission'] += float(referral.get('commission_amount', 0))

            # Top performers
            partner_performance = []
            for partner in partners.data:
                partner_referrals = [r for r in referrals.data if r.get('partner_id') == partner['id']] if referrals.data else []
                if partner_referrals:
                    partner_performance.append({
                        'partner_id': partner['id'],
                        'company_name': partner['company_name'],
                        'category': partner['category'],
                        'total_referrals': len(partner_referrals),
                        'conversion_rate': len([r for r in partner_referrals if r.get('status') in ['won', 'completed']]) / len(partner_referrals) * 100,
                        'total_revenue': sum(float(r.get('project_value', 0)) for r in partner_referrals if r.get('status') == 'completed'),
                        'total_commission': sum(float(r.get('commission_amount', 0)) for r in partner_referrals if r.get('commission_amount'))
                    })

            # Sort by revenue
            top_performers = sorted(partner_performance, key=lambda x: x['total_revenue'], reverse=True)[:10]

            analytics = {
                'summary': {
                    'total_partners': total_partners,
                    'active_partners': active_partners,
                    'total_referrals': total_referrals,
                    'won_referrals': won_referrals,
                    'completed_referrals': completed_referrals,
                    'overall_conversion_rate': round((won_referrals / total_referrals * 100) if total_referrals > 0 else 0, 1),
                    'total_revenue': round(total_revenue, 2),
                    'total_commission': round(total_commission, 2),
                    'pending_commission': round(pending_commission, 2),
                    'average_project_value': round((total_revenue / completed_referrals) if completed_referrals > 0 else 0, 2)
                },
                'category_breakdown': dict(category_stats),
                'top_performers': top_performers,
                'tier_distribution': self._calculate_tier_distribution(partners.data)
            }

            # Cache result
            self._cache_result(cache_key, analytics, ttl=600)

            return True, analytics, None

        except Exception as e:
            logger.error(f"Get partnerships analytics error: {e}")
            return False, None, str(e)

    def _calculate_tier_distribution(self, partners: List[Dict]) -> Dict:
        """Calculate distribution of partners by tier"""
        distribution = defaultdict(int)
        for partner in partners:
            tier = partner.get('tier', 'bronze')
            distribution[tier] += 1
        return dict(distribution)


# Create singleton instance
partnerships_service = PartnershipsService()