"""
iSwitch Roofs CRM - Main Dashboard Page
Real-time KPIs and Activity Feed with AI Assistant
"""
import streamlit as st
from utils.api_client import get_api_client
from utils.auth import require_auth, get_user_metadata
from utils.realtime import (
    auto_refresh,
    display_last_updated
)
from utils.charts import (
    create_kpi_card,
    create_response_time_gauge,
    create_conversion_funnel
)
from utils.pusher_script import inject_pusher_script, pusher_status_indicator
from utils.crm_chatbot import render_compact_chatbot

# Require authentication
require_auth()

# Get user info for personalization
user_metadata = get_user_metadata()
user_name = user_metadata.get('full_name', 'User')

# Initialize API client
api_client = get_api_client()

# Auto-refresh every 30 seconds
auto_refresh(interval_ms=30000, key="home_refresh")

# Inject Pusher real-time client
inject_pusher_script(channels=['analytics', 'leads', 'customers', 'projects', 'appointments'], debug=False)

# Welcome Section
st.markdown(f"""
### 👋 Welcome back, {user_name}!

**All 18 services are now enabled and accessible from the sidebar navigation!**

Navigate through the sections to access:
- 📊 **Data Management**: Leads, Customers, Projects, Appointments
- 🤖 **AI & Automation**: Chat AI, AI Search, Sales Automation, Data Pipeline, Live Data Generator
- 📈 **Analytics & Insights**: Enhanced Analytics, Lead Analytics, Advanced Analytics, Custom Reports, Project Performance
- 🧪 **Testing & Forecasting**: A/B Testing, Revenue Forecasting
- 👥 **Team Management**: Team Productivity
""")

st.markdown("---")

# CRM Assistant Chatbot
render_compact_chatbot()

st.markdown("---")

# Real-time KPIs
st.subheader("📊 Real-Time Key Performance Indicators")

# Pusher status
pusher_status_indicator()

try:
    # Fetch stats from API - try multiple endpoints
    try:
        # Try leads stats
        response = api_client.get("/stats/summary")
    except:
        # If that fails, aggregate from individual endpoints
        response = None

    # If response is valid, use it; otherwise create mock data
    if response and response.status_code == 200:
        data = response.json()
    else:
        # Fetch individual stats and aggregate
        try:
            leads_resp = api_client.get("/leads?limit=1")
            leads_data = leads_resp.json() if leads_resp.status_code == 200 else {}
            total_leads = len(leads_data.get('leads', []))
        except:
            total_leads = 0

        # Create aggregated data
        data = {
            'total_leads': total_leads,
            'leads_today': 0,
            'hot_leads': 0,
            'hot_today': 0,
            'conversion_rate': 0.0,
            'conversion_delta': 0.0,
            'active_projects': 0,
            'projects_this_month': 0,
            'monthly_revenue': 0,
            'revenue_delta': 0,
            'avg_response_time': 0,
            'contacted_leads': 0,
            'appointments_set': 0,
            'proposals_sent': 0,
            'closed_deals': 0
        }

    if data:

        # Display metrics in columns
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            create_kpi_card(
                "Total Leads",
                data.get('total_leads', 0),
                delta=f"+{data.get('leads_today', 0)} today",
                icon="👥"
            )

        with col2:
            create_kpi_card(
                "HOT Leads",
                data.get('hot_leads', 0),
                delta=f"+{data.get('hot_today', 0)} today",
                icon="🔥"
            )

        with col3:
            create_kpi_card(
                "Conversion Rate",
                f"{data.get('conversion_rate', 0):.1f}%",
                delta=f"{data.get('conversion_delta', 0):+.1f}% vs last month",
                icon="📈"
            )

        with col4:
            create_kpi_card(
                "Active Projects",
                data.get('active_projects', 0),
                delta=f"{data.get('projects_this_month', 0)} this month",
                icon="🏗️"
            )

        with col5:
            create_kpi_card(
                "Monthly Revenue",
                f"${data.get('monthly_revenue', 0)/1000:.0f}K",
                delta=f"+${data.get('revenue_delta', 0)/1000:.0f}K vs last month",
                icon="💰"
            )

        st.markdown("---")

        # Response Time and Conversion Funnel
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("⏱️ Response Time Performance")
            avg_response = data.get('avg_response_time', 0)
            create_response_time_gauge(avg_response, target=120)

            if avg_response <= 120:
                st.success(f"✅ Excellent! Average response: {avg_response:.0f} seconds")
            elif avg_response <= 300:
                st.warning(f"⚠️ Good! Average response: {avg_response:.0f} seconds")
            else:
                st.error(f"❌ Needs improvement! Average response: {avg_response:.0f} seconds")

        with col2:
            st.subheader("🔄 Conversion Funnel")
            funnel_data = {
                'Leads': data.get('total_leads', 0),
                'Contacted': data.get('contacted_leads', 0),
                'Appointments': data.get('appointments_set', 0),
                'Proposals': data.get('proposals_sent', 0),
                'Closed': data.get('closed_deals', 0)
            }
            create_conversion_funnel(funnel_data)

        st.markdown("---")

        # Recent Activity
        st.subheader("🔔 Recent Activity")

        # Fetch recent leads
        leads_response = api_client.get("/leads", params={'limit': 5, 'sort_by': 'created_at', 'order': 'desc'})
        if leads_response.status_code == 200:
            recent_leads = leads_response.json()

            if recent_leads:
                for lead in recent_leads:
                    temp = lead.get('temperature', 'COLD')
                    temp_color = {
                        'HOT': '🔴',
                        'WARM': '🟡',
                        'COOL': '🔵',
                        'COLD': '⚪'
                    }.get(temp, '⚪')

                    st.info(f"{temp_color} **New Lead**: {lead.get('name', 'Unknown')} - {lead.get('city', 'Unknown')} - Score: {lead.get('score', 0)}/100")
            else:
                st.info("No recent leads. Generate new leads from the Live Data Generator!")

        # Display last updated
        display_last_updated()

    else:
        st.error(f"Failed to fetch dashboard data: {response.status_code}")
        st.info("Make sure the backend is running: `cd backend && python3 run.py`")

except Exception as e:
    st.error(f"Connection error: {str(e)}")
    st.info("**Backend Connection Required**")
    st.code("""
# Start the backend server:
cd backend
python3 run.py

# In another terminal, start Streamlit:
cd frontend-streamlit
streamlit run Home.py
    """)

# Quick Actions
st.markdown("---")
st.subheader("⚡ Quick Actions")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("➕ New Lead", type="primary", use_container_width=True):
        st.info("Navigate to **Leads Management** to create new leads")

with col2:
    if st.button("📊 View Analytics", use_container_width=True):
        st.info("Navigate to **Enhanced Analytics** for detailed insights")

with col3:
    if st.button("🎯 Generate Leads", use_container_width=True):
        st.info("Navigate to **Live Data Generator** to generate real leads")

with col4:
    if st.button("🤖 AI Chat", use_container_width=True):
        st.info("Navigate to **Conversational AI** to chat with AI")
