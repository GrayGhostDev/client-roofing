"""
API Client for iSwitch Roofs CRM Backend
Handles all API communication with retry logic and robust error handling
Version: 2.0 - Production Ready
"""

import os
import requests
import streamlit as st
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Import configuration utilities
from .config import (
    get_api_base_url,
    get_health_check_url,
    APIConfig
)
from .data_normalizer import (
    normalize_customer_list,
    normalize_lead_list,
    normalize_project_list,
    normalize_appointment_list,
    extract_api_data
)

logger = logging.getLogger(__name__)


def create_session_with_retries() -> requests.Session:
    """
    Create requests session with automatic retry logic

    Retries on:
    - Connection errors
    - Timeout errors
    - 429 (Too Many Requests)
    - 500, 502, 503, 504 (Server errors)

    Returns:
        requests.Session: Configured session with retry adapter
    """
    session = requests.Session()

    retry_strategy = Retry(
        total=APIConfig.MAX_RETRIES,
        backoff_factor=APIConfig.BACKOFF_FACTOR,
        status_forcelist=APIConfig.RETRY_STATUS_CODES,
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"]
    )

    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=20
    )

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def make_api_request(endpoint: str, method: str = 'GET', params=None, json_data=None, timeout=30):
    """Make an API request with error handling"""
    base_url = get_api_base_url()
    url = f"{base_url}{endpoint}"

    try:
        if method == 'GET':
            response = requests.get(url, params=params, timeout=timeout)
        elif method == 'POST':
            response = requests.post(url, json=json_data, timeout=timeout)
        elif method == 'PUT':
            response = requests.put(url, json=json_data, timeout=timeout)
        elif method == 'DELETE':
            response = requests.delete(url, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise


class APIClient:
    """Client for communicating with the CRM backend API"""

    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        """
        Initialize API client

        Args:
            base_url: Base URL for API (e.g., http://localhost:8001/api)
            auth_token: Optional JWT authentication token
        """
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.session = requests.Session()

        if auth_token:
            self.session.headers.update({
                'Authorization': f'Bearer {auth_token}'
            })

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Make HTTP request to API

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., /leads)
            params: Query parameters
            json: JSON body for POST/PUT requests
            timeout: Request timeout in seconds

        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            st.error(f"API Error: {str(e)}")
            return {}

    def get(self, endpoint: str, params: Optional[Dict] = None, timeout: int = 30):
        """
        Generic GET request method

        Args:
            endpoint: API endpoint (e.g., '/api/leads')
            params: Query parameters
            timeout: Request timeout in seconds

        Returns:
            requests.Response object
        """
        url = f"{self.base_url}{endpoint}"
        return self.session.get(url, params=params, timeout=timeout)

    def get_health(self) -> Dict:
        """
        Check backend health status

        Returns:
            Health status dictionary
        """
        try:
            # Health endpoint is at root level, not under /api
            health_url = self.base_url.replace('/api', '') + '/health'
            response = self.session.get(health_url, timeout=5)
            response.raise_for_status()
            return response.json()
        except:
            return {"status": "unhealthy"}

    # Lead endpoints
    def get_leads(
        self,
        status: Optional[str] = None,
        source: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get leads with optional filters"""
        params = {'limit': limit}

        if status:
            params['status'] = status
        if source:
            params['source'] = source
        if start_date:
            params['start_date'] = start_date.isoformat()
        if end_date:
            params['end_date'] = end_date.isoformat()

        response = self._make_request('GET', '/leads', params=params)
        # Backend returns {leads: [...]} not {data: [...]}
        return response.get('leads', response.get('data', []))

    def get_lead_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """Get lead statistics"""
        params = {}
        if start_date:
            params['start_date'] = start_date.isoformat()
        if end_date:
            params['end_date'] = end_date.isoformat()

        response = self._make_request('GET', '/leads/stats', params=params)
        return response.get('data', {})

    def get_lead_conversion_funnel(self) -> List[Dict]:
        """Get lead conversion funnel data"""
        response = self._make_request('GET', '/analytics/lead-funnel')
        return response.get('data', [])

    def create_lead(self, lead_data: Dict) -> Dict:
        """Create a new lead"""
        response = self._make_request('POST', '/leads', json=lead_data)
        return response

    def update_lead(self, lead_id: str, lead_data: Dict) -> Dict:
        """Update an existing lead"""
        response = self._make_request('PUT', f'/leads/{lead_id}', json=lead_data)
        return response

    def delete_lead(self, lead_id: str) -> Dict:
        """Soft delete a lead"""
        response = self._make_request('DELETE', f'/leads/{lead_id}')
        return response

    def get_hot_leads(self, limit: int = 50) -> List[Dict]:
        """Get hot temperature leads"""
        response = self._make_request('GET', '/leads/hot', params={'limit': limit})
        return response.get('data', [])

    # Customer endpoints
    def get_customers(
        self,
        tier: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get customers"""
        params = {'limit': limit}
        if tier:
            params['tier'] = tier

        response = self._make_request('GET', '/customers', params=params)
        # Backend may return {customers: [...]} or {data: [...]}
        return response.get('customers', response.get('data', []))

    def get_customer(self, customer_id: str) -> Dict:
        """Get single customer by ID"""
        response = self._make_request('GET', f'/customers/{customer_id}')
        return response.get('data', {})

    def create_customer(self, customer_data: Dict) -> Dict:
        """Create a new customer"""
        response = self._make_request('POST', '/customers', json=customer_data)
        return response

    def get_customer_projects(self, customer_id: str) -> List[Dict]:
        """Get projects for a specific customer"""
        response = self._make_request('GET', f'/customers/{customer_id}/projects')
        return response.get('data', [])

    def update_customer(self, customer_id: str, customer_data: Dict) -> Dict:
        """Update an existing customer"""
        response = self._make_request('PUT', f'/customers/{customer_id}', json=customer_data)
        return response

    def delete_customer(self, customer_id: str) -> Dict:
        """Soft delete a customer"""
        response = self._make_request('DELETE', f'/customers/{customer_id}')
        return response

    # Project endpoints
    def get_projects(
        self,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get projects with optional filters"""
        params = {'limit': limit}

        if status:
            params['status'] = status
        if start_date:
            params['start_date'] = start_date.isoformat()
        if end_date:
            params['end_date'] = end_date.isoformat()

        response = self._make_request('GET', '/projects', params=params)
        # Backend may return {projects: [...]} or {data: [...]}
        return response.get('projects', response.get('data', []))

    def get_project(self, project_id: str) -> Dict:
        """Get single project by ID"""
        response = self._make_request('GET', f'/projects/{project_id}')
        return response.get('data', {})

    def create_project(self, project_data: Dict) -> Dict:
        """Create a new project"""
        response = self._make_request('POST', '/projects', json=project_data)
        return response

    def update_project(self, project_id: str, project_data: Dict) -> Dict:
        """Update an existing project"""
        response = self._make_request('PUT', f'/projects/{project_id}', json=project_data)
        return response

    def get_project_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        timeframe: str = 'month_to_date'
    ) -> Dict:
        """Get project statistics - uses timeframe parameter"""
        # Analytics dashboard requires timeframe parameter, not date range
        params = {'timeframe': timeframe}

        # Use analytics dashboard for project statistics
        response = self._make_request('GET', '/analytics/dashboard', params=params)
        return response.get('data', {})

    def delete_project(self, project_id: str) -> Dict:
        """Soft delete a project"""
        response = self._make_request('DELETE', f'/projects/{project_id}')
        return response

    def get_project_stats(self, timeframe: str = 'month_to_date') -> Dict:
        """Get project statistics from dedicated stats endpoint"""
        response = self._make_request('GET', '/projects/stats', params={'timeframe': timeframe})
        return response.get('data', {})

    # Appointment endpoints
    def get_appointments(
        self,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get appointments with optional filters"""
        params = {'limit': limit}

        if status:
            params['status'] = status
        if start_date:
            params['start_date'] = start_date.isoformat()
        if end_date:
            params['end_date'] = end_date.isoformat()

        response = self._make_request('GET', '/appointments', params=params)
        # Backend may return {appointments: [...]} or {data: [...]}
        return response.get('appointments', response.get('data', []))

    def get_appointment(self, appointment_id: str) -> Dict:
        """Get single appointment by ID"""
        response = self._make_request('GET', f'/appointments/{appointment_id}')
        return response.get('data', {})

    def create_appointment(self, appointment_data: Dict) -> Dict:
        """Create a new appointment"""
        response = self._make_request('POST', '/appointments', json=appointment_data)
        return response

    def update_appointment(self, appointment_id: str, appointment_data: Dict) -> Dict:
        """Update an existing appointment"""
        response = self._make_request('PUT', f'/appointments/{appointment_id}', json=appointment_data)
        return response

    def delete_appointment(self, appointment_id: str) -> Dict:
        """Cancel/delete an appointment"""
        response = self._make_request('DELETE', f'/appointments/{appointment_id}')
        return response

    # Analytics endpoints
    def get_revenue_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        timeframe: str = 'month_to_date'
    ) -> Dict:
        """Get revenue analytics - uses timeframe parameter"""
        # Analytics dashboard requires timeframe parameter, not date range
        params = {'timeframe': timeframe}

        # Use analytics dashboard for revenue data
        response = self._make_request('GET', '/analytics/dashboard', params=params)
        return response.get('data', {})

    def get_team_performance(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        timeframe: str = 'month_to_date'
    ) -> List[Dict]:
        """Get team performance metrics - uses timeframe parameter"""
        # Team performance also needs timeframe parameter
        params = {'timeframe': timeframe}

        response = self._make_request('GET', '/analytics/team-performance', params=params)
        return response.get('data', [])

    def get_dashboard_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        timeframe: str = 'month_to_date'
    ) -> Dict:
        """Get dashboard summary data - uses timeframe parameter"""
        # Analytics dashboard requires timeframe parameter, not date range
        params = {'timeframe': timeframe}

        response = self._make_request('GET', '/analytics/dashboard', params=params)
        return response.get('data', {})

    # Health check
    def health_check(self) -> Dict:
        """Check API health"""
        try:
            response = requests.get(
                f"{self.base_url.replace('/api', '')}/health",
                timeout=5
            )
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)}

    # Business metrics endpoints
    def get_premium_markets(self, days: int = 30) -> Dict:
        """Get premium market metrics"""
        response = self._make_request('GET', '/business-metrics/premium-markets', params={'days': days})
        return response.get('data', {})

    def get_lead_response_metrics(self) -> Dict:
        """Get lead response time metrics (2-minute target)"""
        response = self._make_request('GET', '/business-metrics/lead-response')
        return response.get('data', {})

    def get_marketing_roi(self, days: int = 30) -> Dict:
        """Get marketing channel ROI"""
        response = self._make_request('GET', '/business-metrics/marketing-roi', params={'days': days})
        return response.get('data', {})

    def get_conversion_optimization(self) -> Dict:
        """Get conversion optimization metrics"""
        response = self._make_request('GET', '/business-metrics/conversion-optimization')
        return response.get('data', {})

    def get_revenue_growth(self) -> Dict:
        """Get revenue growth progress"""
        response = self._make_request('GET', '/business-metrics/revenue-growth')
        return response.get('data', {})

    def get_realtime_snapshot(self) -> Dict:
        """Get real-time metrics snapshot"""
        response = self._make_request('GET', '/business-metrics/realtime/snapshot')
        return response.get('data', {})

    def get_business_summary(self) -> Dict:
        """Get comprehensive business metrics summary"""
        response = self._make_request('GET', '/business-metrics/summary')
        return response.get('data', {})

    # ========================================================================
    # CONVERSATIONAL AI ENDPOINTS (Phase 4.2)
    # ========================================================================

    # Voice AI endpoints
    def get_voice_calls(self, limit: int = 50, offset: int = 0) -> Dict:
        """Get voice AI call records"""
        response = self._make_request('GET', '/conversation/voice/calls', params={'limit': limit, 'offset': offset})
        return response

    def get_voice_call(self, call_id: str) -> Dict:
        """Get specific voice call details"""
        response = self._make_request('GET', f'/conversation/voice/call/{call_id}')
        return response

    def get_voice_analytics(self) -> Dict:
        """Get voice AI analytics"""
        response = self._make_request('GET', '/conversation/voice/analytics')
        return response

    # Chatbot endpoints
    def get_chatbot_conversations(self, limit: int = 50, offset: int = 0) -> Dict:
        """Get chatbot conversation records"""
        response = self._make_request('GET', '/conversation/chatbot/conversations', params={'limit': limit, 'offset': offset})
        return response

    def get_chatbot_conversation(self, conversation_id: str) -> Dict:
        """Get specific chatbot conversation"""
        response = self._make_request('GET', f'/conversation/chatbot/conversation/{conversation_id}')
        return response

    # Sentiment analysis endpoints
    def get_sentiment_analysis(self, analysis_id: str) -> Dict:
        """Get specific sentiment analysis"""
        response = self._make_request('GET', f'/conversation/sentiment/{analysis_id}')
        return response

    def get_sentiment_alerts(self, limit: int = 20) -> Dict:
        """Get sentiment alerts"""
        response = self._make_request('GET', '/conversation/sentiment/alerts', params={'limit': limit})
        return response

    def get_sentiment_trends(self, days: int = 30) -> Dict:
        """Get sentiment trends"""
        response = self._make_request('GET', '/conversation/sentiment/trends', params={'days': days})
        return response

    # Conversation analytics endpoints
    def get_conversation_analytics_overview(self) -> Dict:
        """Get conversation analytics overview"""
        response = self._make_request('GET', '/conversation/analytics/overview')
        return response

    def get_conversation_performance(self) -> Dict:
        """Get conversation performance metrics"""
        response = self._make_request('GET', '/conversation/analytics/performance')
        return response

    def get_conversation_quality(self) -> Dict:
        """Get conversation quality metrics"""
        response = self._make_request('GET', '/conversation/analytics/quality')
        return response

    # Call transcription endpoints
    def get_call_transcript(self, call_id: str) -> Dict:
        """Get call transcript"""
        response = self._make_request('GET', f'/transcription/call/{call_id}')
        return response

    def transcribe_call(self, call_id: str, audio_url: Optional[str] = None) -> Dict:
        """Transcribe a call"""
        data = {'audio_url': audio_url} if audio_url else {}
        response = self._make_request('POST', f'/transcription/call/{call_id}', json=data)
        return response

    def process_call_end_to_end(self, call_id: str) -> Dict:
        """Process call with full transcription, action extraction, etc."""
        response = self._make_request('POST', f'/transcription/call/{call_id}/process')
        return response

    def get_transcription_analytics(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """Get transcription analytics"""
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        response = self._make_request('GET', '/transcription/analytics', params=params)
        return response


@st.cache_resource
def get_api_client() -> APIClient:
    """
    Get cached API client instance

    Uses config.py to get API URL from:
    1. Environment variables (BACKEND_API_URL, ML_API_BASE_URL)
    2. Streamlit secrets (api_base_url, ml_api_base_url)
    3. Development fallback (localhost only if STREAMLIT_ENV=development)

    Returns:
        APIClient: Configured API client instance
    """
    # Use config.py function to get API URL from secrets/env
    base_url = get_api_base_url()

    # Ensure it has /api suffix
    if not base_url.endswith('/api'):
        base_url = f"{base_url}/api"

    return APIClient(
        base_url=base_url,
        auth_token=st.session_state.get('auth_token')
    )
