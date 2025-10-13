"""
iSwitch Roofs CRM - Modern Dashboard (Streamlit 2025)
Main Entry Point with st.navigation, st.dialog, st.fragment, and st.toast
Version: 3.0.0
Date: 2025-10-12
"""
import streamlit as st
from datetime import datetime
from utils.api_client import get_api_client
from utils.auth import require_auth

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="iSwitch Roofs CRM",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Require authentication
require_auth()

# Initialize API client
api_client = get_api_client()

# ============================================================================
# MODERN NAVIGATION WITH ST.NAVIGATION (2025)
# ============================================================================

# Define pages with icons and organized sections
pages = {
    "": [  # Top-level pages (no section header)
        st.Page("Home.py", title="Dashboard", icon="🏠", default=True),
    ],
    "📊 Data Management": [
        st.Page("pages/1_Leads_Management.py", title="Leads", icon="👥"),
        st.Page("pages/2_Customers_Management.py", title="Customers", icon="🏢"),
        st.Page("pages/3_Projects_Management.py", title="Projects", icon="🏗️"),
        st.Page("pages/4_Appointments.py", title="Appointments", icon="📅"),
        st.Page("pages/6_Interactions.py", title="Interactions", icon="💬"),
        st.Page("pages/7_Reviews.py", title="Reviews", icon="⭐"),
    ],
    "🤖 AI & Automation": [
        st.Page("pages/13_🤖_Conversational_AI.py", title="Chat AI", icon="💬"),
        st.Page("pages/14_🔍_AI_Search.py", title="AI Search", icon="🔍"),
        st.Page("pages/15_📡_Data_Pipeline.py", title="Data Pipeline", icon="📡"),
        st.Page("pages/16_🎯_Live_Data_Generator.py", title="Live Data", icon="🎯"),
        st.Page("pages/8_📈_Sales_Automation.py", title="Sales Automation", icon="🤖"),
    ],
    "📈 Analytics & Insights": [
        st.Page("pages/5_Enhanced_Analytics.py", title="Enhanced Analytics", icon="📊"),
        st.Page("pages/10_📊_Advanced_Analytics.py", title="Advanced Analytics", icon="📈"),
        st.Page("pages/11_🧪_AB_Testing.py", title="A/B Testing", icon="🧪"),
        st.Page("pages/12_📈_Revenue_Forecasting.py", title="Forecasting", icon="💹"),
    ],
}

# Create navigation (top navigation for modern feel)
pg = st.navigation(pages, position="sidebar", expanded=True)

# ============================================================================
# SHARED HEADER & WIDGETS (Across all pages)
# ============================================================================

# Logo and branding
st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 20px;
    color: white;
}
.main-header h1 {
    margin: 0;
    color: white !important;
}
.status-badge {
    display: inline-block;
    padding: 5px 15px;
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.2);
    font-size: 0.9em;
    margin-left: 10px;
}
</style>
<div class="main-header">
    <h1>🏠 iSwitch Roofs CRM <span class="status-badge">LIVE</span></h1>
    <p style="margin: 5px 0 0 0; opacity: 0.9;">Real-Time Lead Management & Analytics</p>
</div>
""", unsafe_allow_html=True)

# Sidebar: Shared widgets across pages (using keys for session state)
with st.sidebar:
    st.markdown("### Quick Filters")

    # Date range filter (shared across pages)
    date_option = st.selectbox(
        "Time Period",
        ["Today", "This Week", "This Month", "This Quarter", "This Year", "All Time"],
        key="global_date_filter"
    )

    # Status filter (shared)
    show_archived = st.checkbox(
        "Show Archived",
        value=False,
        key="show_archived"
    )

    st.markdown("---")
    st.markdown("### System Status")

    # Connection status indicator
    try:
        health = api_client.get_health()
        if health.get("status") == "healthy":
            st.success("🟢 System Online")
        else:
            st.warning("🟡 Degraded Performance")
    except:
        st.error("🔴 System Offline")

    # Quick stats
    st.metric("Session Time", f"{datetime.now().strftime('%H:%M:%S')}")

    st.markdown("---")

    # Quick actions
    st.markdown("### Quick Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("⚙️ Settings", use_container_width=True):
            st.toast("Settings panel coming soon!", icon="⚙️")

# ============================================================================
# RUN SELECTED PAGE
# ============================================================================

# Execute the current page
pg.run()
