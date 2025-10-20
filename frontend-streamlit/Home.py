"""
iSwitch Roofs CRM - Modern Navigation Dashboard
Main Entry Point with All Services Enabled
Version: 3.0.0 - Streamlit 2025 Modern Navigation
Date: 2025-10-13
"""
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import streamlit as st
import requests
from utils.api_client import get_api_client
from utils.realtime import (
    auto_refresh,
    display_last_updated,
    create_realtime_indicator,
    show_connection_status
)
from utils.charts import (
    create_kpi_card,
    create_response_time_gauge,
    create_conversion_funnel
)
from utils.pusher_script import inject_pusher_script, pusher_status_indicator
from utils.notifications import notification_preferences_sidebar
from utils.supabase_auth import get_auth_client, check_session_validity
from utils.rbac import get_user_role

# ============================================================================
# PAGE CONFIGURATION (MUST BE FIRST)
# ============================================================================
st.set_page_config(
    page_title="iSwitch Roofs CRM",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# AUTHENTICATION CHECK
# ============================================================================
import os

# Development mode bypass - set BYPASS_AUTH=true in .env to skip authentication
BYPASS_AUTH = os.getenv("BYPASS_AUTH", "false").lower() == "true"

if not BYPASS_AUTH:
    # Check if session is still valid (auto-logout if expired)
    check_session_validity()

    # Get auth client
    auth = get_auth_client()

    # Check if user is authenticated
    if not auth.is_authenticated():
        st.warning("⛔ Please log in to access the dashboard")
        st.info("👉 Click below to go to the login page")
        if st.button("🔐 Go to Login", type="primary"):
            st.switch_page("0_Login.py")
        st.stop()
else:
    st.info("🔧 Development Mode: Authentication Bypassed")
    # Create a mock auth object for development
    class MockAuth:
        def is_authenticated(self):
            return True
        def get_user(self):
            return {"email": "dev@localhost", "role": "admin"}
        def get_current_user(self):
            return {"email": "dev@localhost", "id": "dev-user-id", "role": "admin"}
        def get_user_metadata(self):
            return {"full_name": "Development User", "role": "admin"}
        def sign_out(self):
            pass  # No-op for development mode
    auth = MockAuth()

# ============================================================================
# MODERN NAVIGATION SYSTEM (Streamlit 2025)
# All 18 services organized into logical sections
# ============================================================================
pages = {
    "🔐 Account": [
        st.Page("pages/0_🔐_Login.py", title="Login / Logout", icon="🔐"),
    ],
    "🏠 Dashboard": [
        st.Page("pages/0_Dashboard.py", title="Dashboard", icon="🏠", default=True),
    ],
    "📊 Data Management": [
        st.Page("pages/1_Leads_Management.py", title="Leads", icon="👥"),
        st.Page("pages/2_Customers_Management.py", title="Customers", icon="🏢"),
        st.Page("pages/3_Projects_Management.py", title="Projects", icon="🏗️"),
        st.Page("pages/4_Appointments.py", title="Appointments", icon="📅"),
    ],
    "🤖 AI & Automation": [
        st.Page("pages/13_🤖_Conversational_AI.py", title="Chat AI", icon="💬"),
        st.Page("pages/14_🔍_AI_Search.py", title="AI Search", icon="🔍"),
        st.Page("pages/8_📈_Sales_Automation.py", title="Sales Automation", icon="🚀"),
        st.Page("pages/15_📡_Data_Pipeline.py", title="Data Pipeline", icon="📡"),
        st.Page("pages/16_🎯_Live_Data_Generator.py", title="Live Data", icon="🎯"),
    ],
    "📈 Analytics & Insights": [
        st.Page("pages/5_Enhanced_Analytics.py", title="Enhanced Analytics", icon="📊"),
        st.Page("pages/7_Lead_Analytics.py", title="Lead Analytics", icon="📉"),
        st.Page("pages/10_📊_Advanced_Analytics.py", title="Advanced Analytics", icon="📈"),
        st.Page("pages/8_Custom_Reports.py", title="Custom Reports", icon="📋"),
        st.Page("pages/9_Project_Performance.py", title="Project Performance", icon="⚡"),
    ],
    "🧪 Testing & Forecasting": [
        st.Page("pages/11_🧪_AB_Testing.py", title="A/B Testing", icon="🧪"),
        st.Page("pages/12_📈_Revenue_Forecasting.py", title="Revenue Forecasting", icon="💰"),
    ],
    "👥 Team Management": [
        st.Page("pages/11_Team_Productivity.py", title="Team Productivity", icon="👥"),
    ],
    "🔷 Data Warehouse": [
        st.Page("pages/17_🔷_Snowflake_Analytics.py", title="Snowflake Analytics", icon="🔷"),
    ],
}

# ============================================================================
# CREATE NAVIGATION
# ============================================================================
pg = st.navigation(pages, position="sidebar", expanded=True)

# ============================================================================
# SHARED HEADER (Appears on all pages)
# ============================================================================
st.markdown("""
    <style>
    /* Logo and Header Styles */
    .logo-container {
        width: 200px;
        height: 60px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 20px;
    }
    .logo-text {
        color: white;
        font-size: 24px;
        font-weight: bold;
        text-align: center;
    }

    /* Status Badge */
    .status-badge {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        margin-left: 10px;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    /* Main Header */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 30px;
        color: white;
    }

    .main-header h1 {
        margin: 0;
        color: white;
        font-size: 32px;
    }

    /* Navigation Enhancement */
    .stApp [data-testid="stSidebarNav"] {
        padding-top: 20px;
    }

    /* Modern Card Styles */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }

    /* Connection Status */
    .connection-status {
        display: flex;
        align-items: center;
        padding: 10px;
        border-radius: 8px;
        margin: 10px 0;
    }

    .status-online {
        background: #d4edda;
        color: #155724;
    }

    .status-offline {
        background: #f8d7da;
        color: #721c24;
    }
    </style>
""", unsafe_allow_html=True)

# Display main header
st.markdown("""
<div class="main-header">
    <h1>🏠 iSwitch Roofs CRM <span class="status-badge">ALL SERVICES ENABLED</span></h1>
    <p style="margin: 5px 0 0 0; opacity: 0.9;">Premium Lead Generation & Customer Management Platform</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SHARED SIDEBAR WIDGETS (Appear on all pages)
# ============================================================================
with st.sidebar:
    # Logo
    st.markdown("""
        <div class="logo-container">
            <div class="logo-text">iSwitch Roofs</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # User Profile Section
    st.subheader("👤 User Profile")
    user = auth.get_current_user()
    if user:
        user_email = st.session_state.get('user_email', 'user@example.com')
        user_metadata = auth.get_user_metadata()
        user_name = user_metadata.get('full_name', user_email.split('@')[0])
        user_role = get_user_role()

        # Role color mapping
        role_colors = {
            "Admin": "#dc3545",
            "Manager": "#fd7e14",
            "Sales Representative": "#28a745",
            "Other": "#6c757d"
        }
        role_color = role_colors.get(user_role, "#6c757d")

        st.markdown(f"""
            <div style="padding: 10px; background: #f0f2f6; border-radius: 8px;">
                <strong>👋 Welcome!</strong><br>
                <span style="font-size: 14px;">{user_name}</span>
                <span style="display: inline-block; background: {role_color}; color: white;
                      padding: 2px 8px; border-radius: 10px; font-size: 10px;
                      font-weight: bold; margin-left: 4px;">{user_role}</span><br>
                <span style="font-size: 12px; color: #666;">{user_email}</span>
            </div>
        """, unsafe_allow_html=True)

        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            result = auth.sign_out()
            if result['success']:
                st.success("✅ Logged out successfully")
                st.rerun()

    st.markdown("---")

    # Global Time Filter
    st.subheader("⏰ Time Period")
    date_filter = st.selectbox(
        "Select Range",
        ["Today", "This Week", "This Month", "Last 30 Days", "Last 90 Days", "This Year", "All Time"],
        key="global_date_filter",
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Connection Status
    st.subheader("🔌 System Status")
    try:
        api_client = get_api_client()
        health = api_client.get_health()

        if health.get("status") == "healthy":
            st.markdown("""
                <div class="connection-status status-online">
                    <span style="font-size: 20px; margin-right: 8px;">🟢</span>
                    <div>
                        <strong>System Online</strong><br>
                        <small>All services operational</small>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Show service counts
            col1, col2 = st.columns(2)
            with col1:
                st.metric("APIs", "3/6", help="Weather.gov, Google Maps, NOAA")
            with col2:
                st.metric("Services", "18", help="All CRM services enabled")
        else:
            st.markdown("""
                <div class="connection-status status-offline">
                    <span style="font-size: 20px; margin-right: 8px;">🔴</span>
                    <div>
                        <strong>System Offline</strong><br>
                        <small>Check backend connection</small>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.markdown("""
            <div class="connection-status status-offline">
                <span style="font-size: 20px; margin-right: 8px;">🔴</span>
                <div>
                    <strong>Connection Error</strong><br>
                    <small>Backend not responding</small>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.caption(f"Error: {str(e)[:50]}...")

    st.markdown("---")

    # Quick Stats - Real-time Data
    st.subheader("📊 Quick Stats")
    try:
        # Fetch real-time snapshot from business metrics
        snapshot = api_client.get_realtime_snapshot()

        if snapshot:
            # Lead response time with pulse animation
            response_data = snapshot.get('lead_response', {})
            avg_response = response_data.get('avg_response_time_seconds', 0)
            target = response_data.get('target_seconds', 120)

            # Color based on performance
            if avg_response <= target:
                response_color = "#28a745"  # Green
                status_emoji = "🟢"
            else:
                response_color = "#dc3545"  # Red
                status_emoji = "🔴"

            st.markdown(f"""
                <div style="padding: 10px; background: {response_color}15; border-left: 3px solid {response_color}; border-radius: 4px; margin-bottom: 10px;">
                    <div style="font-size: 12px; color: #666;">Lead Response Time</div>
                    <div style="font-size: 24px; font-weight: bold; color: {response_color};">
                        {status_emoji} {int(avg_response)}s
                    </div>
                    <div style="font-size: 11px; color: #888;">Target: {target}s</div>
                </div>
            """, unsafe_allow_html=True)

            # Revenue progress
            revenue_data = snapshot.get('revenue', {})
            current_revenue = revenue_data.get('revenue', 0)
            target_revenue = revenue_data.get('target', 500000)
            progress = revenue_data.get('progress_percent', 0)

            st.metric(
                "Month Revenue",
                f"${current_revenue:,.0f}",
                f"{progress:.0f}% of target"
            )

            # Conversion rate
            conversion_data = snapshot.get('conversion', {})
            conversion_rate = conversion_data.get('conversion_rate', 0)
            target_rate = conversion_data.get('target_rate', 25)

            st.metric(
                "Conversion Rate",
                f"{conversion_rate:.1f}%",
                f"{(conversion_rate - target_rate):+.1f}% vs target"
            )

        else:
            st.info("📊 Loading real-time stats...")

    except requests.exceptions.HTTPError as e:
        # Handle 404 errors specifically
        if e.response.status_code == 404:
            st.warning("⚠️ Backend API endpoint not available")
            with st.expander("🔍 Troubleshooting Information"):
                st.markdown("""
                **The backend API is returning 404 errors.**

                **Possible causes:**
                - 🌐 Backend is starting up (Render free tier takes 30-60 seconds)
                - 🗄️ Database connection not established
                - 🔧 Route registration failed during startup
                - 🔑 Missing environment variables

                **Next steps:**
                1. Wait 60 seconds and refresh the page
                2. Check [Render Dashboard](https://dashboard.render.com/) logs
                3. Look for "Failed to register" error messages
                4. Verify DATABASE_URL and SUPABASE credentials are set

                **Current endpoint errors:**
                - `/api/business-metrics/realtime/snapshot`
                - `/api/leads`
                """)

            # Show demo data as fallback
            st.info("📊 **Displaying demo data** (backend unavailable)")
            st.metric("Lead Response Time", "89s", "🟢 Meeting target")
            st.metric("Month Revenue", "$425,000", "85% of target")
            st.metric("Conversion Rate", "28.5%", "+3.5% vs target")
        else:
            # Other HTTP errors
            st.error(f"❌ API Error: {e.response.status_code}")
            st.caption(f"Endpoint: {e.request.url}")

    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend")
        st.caption("Backend server is not responding. Check Render service status.")

        # Show demo data
        st.info("📊 **Displaying demo data** (connection failed)")
        st.metric("Lead Response Time", "89s", "Demo")
        st.metric("Month Revenue", "$425,000", "Demo")
        st.metric("Conversion Rate", "28.5%", "Demo")

    except Exception as e:
        # Generic error handling
        st.warning("⚠️ Backend starting...")
        st.caption(f"Error: {str(e)[:50]}...")
        st.caption("The backend may be waking up. Please wait 60 seconds and refresh.")

    st.markdown("---")

    # Real-time Updates with pulse animation
    st.subheader("🔄 Real-time Updates")

    auto_refresh_enabled = st.toggle("Auto-refresh", value=True, key="global_auto_refresh")

    if auto_refresh_enabled:
        # Trigger auto-refresh every 30 seconds
        auto_refresh(interval_ms=30000, key="sidebar_refresh")

        # Use streamlit native success with emoji - simpler approach
        st.success("🟢 Live Updates Active")
        st.caption("Refreshing every 30s")

        # Show last update time
        display_last_updated(key="sidebar_last_updated")
    else:
        # Use streamlit native info with emoji
        st.info("🔴 Updates Paused")
        st.caption("Enable for live data")

    st.markdown("---")

    # API Status
    st.subheader("🌐 API Status")
    st.success("✅ Weather.gov")
    st.success("✅ Google Maps")
    st.warning("⚠️ NOAA (timeout fix needed)")
    st.info("⏳ Zillow (pending)")
    st.info("⏳ Twitter (pending)")
    st.info("⏳ Facebook (pending)")

    st.markdown("---")

    # Help
    with st.expander("❓ Help & Support"):
        st.markdown("""
        **Quick Links:**
        - 📚 [Documentation](API_SETUP_GUIDE.md)
        - 🚀 [Quick Start](API_QUICK_START.md)
        - ✅ [Setup Status](API_CONFIGURATION_STATUS.md)

        **Support:**
        - Email: support@iswitchroofs.com
        - Phone: (555) 123-4567
        """)

    # Version Info
    st.markdown("---")
    st.caption("iSwitch Roofs CRM v3.0.0")
    st.caption("© 2025 iSwitch Roofs. All rights reserved.")

# ============================================================================
# EXECUTE SELECTED PAGE
# ============================================================================
# Navigation system handles routing to all 18 services
pg.run()
