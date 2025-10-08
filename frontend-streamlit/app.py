"""
iSwitch Roofs CRM - Streamlit Analytics Dashboard
Main Application Entry Point
"""

import streamlit as st
from datetime import datetime, timedelta

# Configure page
st.set_page_config(
    page_title="iSwitch Roofs CRM - Analytics Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://iswitchroofs.com/support',
        'Report a bug': 'https://iswitchroofs.com/support/bug-report',
        'About': "# iSwitch Roofs CRM Analytics Dashboard\nVersion 1.0.0"
    }
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stMetric:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transform: translateY(-2px);
        transition: all 0.3s ease;
    }
    h1 {
        color: #1f77b4;
        padding-bottom: 10px;
        border-bottom: 3px solid #1f77b4;
    }
    h2 {
        color: #2c3e50;
        margin-top: 20px;
    }
    .reportview-container .markdown-text-container {
        font-family: 'Arial', sans-serif;
    }
    div[data-testid="stSidebarNav"] {
        background-color: #f8f9fa;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'api_base_url' not in st.session_state:
    st.session_state.api_base_url = "http://localhost:8000/api"

if 'auth_token' not in st.session_state:
    st.session_state.auth_token = None

if 'date_range' not in st.session_state:
    st.session_state.date_range = (
        datetime.now() - timedelta(days=30),
        datetime.now()
    )

# Sidebar navigation
with st.sidebar:
    # Logo using text with styling instead of external image
    st.markdown("""
    <div style='background: linear-gradient(135deg, #1f77b4 0%, #2ca02c 100%); 
                padding: 20px; 
                border-radius: 10px; 
                text-align: center; 
                margin-bottom: 20px;'>
        <h2 style='color: white; margin: 0; font-weight: bold;'>🏠 iSwitch Roofs</h2>
        <p style='color: #e0e0e0; margin: 5px 0 0 0; font-size: 0.9em;'>CRM Dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    st.title("Navigation")
    
    # Page selection
    page = st.radio(
        "Select Dashboard",
        [
            "📊 Overview Dashboard",
            "🎯 Lead Analytics",
            "🏗️ Project Performance",
            "👥 Team Productivity",
            "💰 Revenue Forecasting",
            "📈 Custom Reports"
        ],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # Date range filter
    st.subheader("Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "From",
            value=st.session_state.date_range[0],
            max_value=datetime.now()
        )
    with col2:
        end_date = st.date_input(
            "To",
            value=st.session_state.date_range[1],
            max_value=datetime.now()
        )
    
    st.session_state.date_range = (start_date, end_date)
    
    # Quick date filters
    st.caption("Quick Filters")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Last 7 Days"):
            st.session_state.date_range = (
                datetime.now() - timedelta(days=7),
                datetime.now()
            )
            st.rerun()
        if st.button("Last Month"):
            st.session_state.date_range = (
                datetime.now() - timedelta(days=30),
                datetime.now()
            )
            st.rerun()
    with col2:
        if st.button("Last 14 Days"):
            st.session_state.date_range = (
                datetime.now() - timedelta(days=14),
                datetime.now()
            )
            st.rerun()
        if st.button("Last Quarter"):
            st.session_state.date_range = (
                datetime.now() - timedelta(days=90),
                datetime.now()
            )
            st.rerun()
    
    st.divider()
    
    # Settings
    with st.expander("⚙️ Settings"):
        # Backend API configuration
        api_base_url = st.text_input(
            "Backend API URL",
            value=st.session_state.get("api_base_url", "http://localhost:8001/api"),
            help="Base URL for the CRM backend API"
        )
        if api_base_url != st.session_state.get("api_base_url"):
            st.session_state.api_base_url = api_base_url
        
        auto_refresh = st.checkbox("Auto-refresh (5 min)", value=False)
        if auto_refresh:
            st.info("Dashboard will refresh every 5 minutes")
    
    # Footer
    st.divider()
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("iSwitch Roofs CRM v1.0.0")

# Route to appropriate page
if page == "📊 Overview Dashboard":
    from pages import overview
    overview.render()
elif page == "🎯 Lead Analytics":
    from pages import lead_analytics
    lead_analytics.render()
elif page == "🏗️ Project Performance":
    from pages import project_performance
    project_performance.render()
elif page == "👥 Team Productivity":
    from pages import team_productivity
    team_productivity.render()
elif page == "💰 Revenue Forecasting":
    from pages import revenue_forecasting
    revenue_forecasting.render()
elif page == "📈 Custom Reports":
    from pages import custom_reports
    custom_reports.render()
