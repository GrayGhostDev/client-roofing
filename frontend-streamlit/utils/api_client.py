"""
API Client for iSwitch Roofs CRM Backend
Handles all API communication
"""

import requests
import streamlit as st
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class APIClient:
    """Client for communicating with the CRM backend API"""
    
    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        """
        Initialize API client
        
        Args:
            base_url: Base URL for API (e.g., http://localhost:8000/api)
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
        return response.get('data', [])
    
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
        return response.get('data', [])
    
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
        return response.get('data', [])
    
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


@st.cache_resource
def get_api_client() -> APIClient:
    """Get cached API client instance"""
    return APIClient(
        base_url=st.session_state.get('api_base_url', 'http://localhost:8000/api'),
        auth_token=st.session_state.get('auth_token')
    )
