"""
🔍 AI-Powered Search Dashboard
Natural language interface for searching CRM data using OpenAI GPT-4o

Features:
- Natural language query processing
- Intelligent search across all data types
- Quick action buttons for common searches
- Search suggestions and examples
- Real-time results with AI-interpreted intent
"""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from typing import Dict, List
from utils.auth import require_auth
from utils.api_client import get_api_base_url

# Require authentication
require_auth()

# API base URL
API_BASE = get_api_base_url()

# Custom CSS
st.markdown("""
<style>
.search-container {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 40px;
    border-radius: 15px;
    margin-bottom: 30px;
    color: white;
}
.search-input {
    font-size: 1.2em;
    padding: 15px;
    border-radius: 10px;
    border: none;
    width: 100%;
}
.quick-action-btn {
    padding: 10px 20px;
    border-radius: 8px;
    border: none;
    margin: 5px;
    cursor: pointer;
    font-weight: 600;
    transition: transform 0.2s;
}
.quick-action-btn:hover {
    transform: scale(1.05);
}
.result-card {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 10px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.result-header {
    font-size: 1.2em;
    font-weight: bold;
    margin-bottom: 10px;
    color: #333;
}
.result-meta {
    color: #666;
    font-size: 0.9em;
    margin-bottom: 10px;
}
.intent-badge {
    background-color: #667eea;
    color: white;
    padding: 5px 15px;
    border-radius: 20px;
    display: inline-block;
    font-size: 0.9em;
    margin: 5px 5px 5px 0;
}
.example-query {
    background-color: #e9ecef;
    padding: 10px 15px;
    border-radius: 8px;
    margin: 5px 0;
    cursor: pointer;
    transition: background-color 0.2s;
}
.example-query:hover {
    background-color: #dee2e6;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'current_query' not in st.session_state:
    st.session_state.current_query = ""
if 'search_results' not in st.session_state:
    st.session_state.search_results = None

# Title and description
st.title("🔍 AI-Powered Search")
st.markdown("*Ask questions in natural language and get intelligent results across all your CRM data*")
st.markdown("---")

# ============================================================================
# SEARCH INTERFACE
# ============================================================================

# Main search container
st.markdown('<div class="search-container">', unsafe_allow_html=True)
st.markdown("### 💬 Ask Me Anything")
st.markdown("*Search for leads, customers, projects, calls, appointments, and more using natural language*")

# Search input
col1, col2 = st.columns([5, 1])
with col1:
    search_query = st.text_input(
        "Search Query",
        placeholder="e.g., Show me all hot leads from this week...",
        key="search_input",
        label_visibility="collapsed",
        value=st.session_state.current_query
    )
with col2:
    search_button = st.button("🔍 Search", type="primary", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# QUICK ACTIONS
# ============================================================================

st.subheader("⚡ Quick Actions")
st.markdown("*Click any button to run a predefined search*")

try:
    response = requests.get(f"{API_BASE}/api/ai-search/quick-actions", timeout=5)
    if response.status_code == 200:
        quick_actions = response.json().get('quick_actions', [])

        # Display quick action buttons in columns
        cols = st.columns(4)
        for idx, action in enumerate(quick_actions):
            with cols[idx % 4]:
                if st.button(
                    action['label'],
                    key=f"quick_{action['id']}",
                    use_container_width=True
                ):
                    st.session_state.current_query = action['query']
                    search_query = action['query']
                    search_button = True
except Exception as e:
    st.warning("Quick actions temporarily unavailable")

st.markdown("---")

# ============================================================================
# SEARCH EXECUTION
# ============================================================================

if search_button and search_query:
    with st.spinner("🤖 AI is analyzing your query..."):
        try:
            # Call AI search API
            response = requests.post(
                f"{API_BASE}/api/ai-search/search",
                json={"query": search_query},
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            if response.status_code == 200:
                search_data = response.json()
                st.session_state.search_results = search_data
                st.session_state.current_query = search_query

                # Add to search history
                st.session_state.search_history.insert(0, {
                    "query": search_query,
                    "timestamp": datetime.now(),
                    "result_count": search_data.get('result_count', 0)
                })

                # Keep only last 10 searches
                st.session_state.search_history = st.session_state.search_history[:10]

                st.success("✅ Search complete!")
            else:
                error_data = response.json()
                st.error(f"Search failed: {error_data.get('error', 'Unknown error')}")

        except requests.exceptions.Timeout:
            st.error("⏱️ Search timed out. Please try a simpler query.")
        except Exception as e:
            st.error(f"❌ Search error: {str(e)}")

# ============================================================================
# DISPLAY SEARCH RESULTS
# ============================================================================

if st.session_state.search_results:
    results_data = st.session_state.search_results

    # Display AI interpretation
    st.subheader("🧠 AI Interpretation")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Entity Type",
            results_data.get('intent', {}).get('entity_type', 'Unknown').title()
        )
    with col2:
        st.metric(
            "Results Found",
            results_data.get('result_count', 0)
        )
    with col3:
        intent_desc = results_data.get('intent', {}).get('intent_description', 'N/A')
        st.info(f"**Intent**: {intent_desc}")

    # Display filters applied
    filters = results_data.get('intent', {}).get('filters', {})
    if filters:
        st.markdown("**Filters Applied:**")
        filter_badges = []
        for key, value in filters.items():
            if isinstance(value, dict):
                filter_badges.append(f"<span class='intent-badge'>{key}: {value}</span>")
            else:
                filter_badges.append(f"<span class='intent-badge'>{key}: {value}</span>")
        st.markdown(" ".join(filter_badges), unsafe_allow_html=True)

    st.markdown("---")

    # Display results
    results = results_data.get('results', [])

    if results:
        st.subheader(f"📋 Search Results ({len(results)} found)")

        for result in results:
            result_type = result.get('type', 'unknown')

            # Create result card
            with st.container():
                st.markdown('<div class="result-card">', unsafe_allow_html=True)

                # Header based on type
                if result_type == 'lead':
                    icon = "👤"
                    title = result.get('name', 'Unknown Lead')
                    subtitle = f"Status: {result.get('status', 'N/A')} | Temperature: {result.get('temperature', 'N/A')}"
                elif result_type == 'customer':
                    icon = "🏠"
                    title = result.get('name', 'Unknown Customer')
                    subtitle = f"Tier: {result.get('tier', 'N/A')} | LTV: ${result.get('lifetime_value', 0):,.2f}"
                elif result_type == 'project':
                    icon = "🏗️"
                    title = result.get('title', 'Unknown Project')
                    subtitle = f"Status: {result.get('status', 'N/A')} | Value: ${result.get('project_value', 0):,.2f}"
                elif result_type == 'voice_call':
                    icon = "📞"
                    title = result.get('caller_name', 'Unknown Caller')
                    subtitle = f"Duration: {result.get('duration_seconds', 0)}s | Sentiment: {result.get('sentiment', 'N/A')}"
                elif result_type == 'appointment':
                    icon = "📅"
                    title = result.get('title', 'Unknown Appointment')
                    subtitle = f"Type: {result.get('appointment_type', 'N/A')} | Status: {result.get('status', 'N/A')}"
                else:
                    icon = "📄"
                    title = "Result"
                    subtitle = ""

                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"<div class='result-header'>{icon} {title}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='result-meta'>{subtitle}</div>", unsafe_allow_html=True)

                    # Additional details based on type
                    if result_type == 'lead':
                        st.write(f"📧 {result.get('email', 'N/A')} | 📱 {result.get('phone', 'N/A')}")
                        st.write(f"Lead Score: {result.get('lead_score', 0)}/100 | Source: {result.get('source', 'N/A')}")
                    elif result_type == 'voice_call':
                        st.write(f"📱 {result.get('phone_number', 'N/A')}")
                        if result.get('summary'):
                            st.write(f"*{result.get('summary')[:150]}...*")

                with col2:
                    created_at = result.get('created_at') or result.get('call_started_at') or result.get('started_at') or result.get('scheduled_at')
                    if created_at:
                        st.caption(f"🕐 {created_at[:10]}")

                    if st.button("View Details", key=f"view_{result.get('id')}", use_container_width=True):
                        st.info(f"View details for {result_type} ID: {result.get('id')}")

                st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.info("No results found matching your query. Try rephrasing or use one of the example queries below.")

# ============================================================================
# SEARCH EXAMPLES
# ============================================================================

st.markdown("---")
st.subheader("💡 Example Searches")
st.markdown("*Click any example to use it as your search query*")

try:
    response = requests.get(f"{API_BASE}/api/ai-search/examples", timeout=5)
    if response.status_code == 200:
        examples_data = response.json()
        categories = examples_data.get('categories', [])

        # Create tabs for each category
        tab_names = [cat['category'] for cat in categories]
        tabs = st.tabs(tab_names)

        for idx, category in enumerate(categories):
            with tabs[idx]:
                st.markdown(f"### {category['icon']} {category['category']}")

                for example in category['examples']:
                    if st.button(
                        example,
                        key=f"example_{category['category']}_{example[:20]}",
                        use_container_width=True
                    ):
                        st.session_state.current_query = example
                        st.rerun()

except Exception as e:
    st.warning("Example queries temporarily unavailable")

# ============================================================================
# SEARCH HISTORY SIDEBAR
# ============================================================================

with st.sidebar:
    st.header("📜 Recent Searches")

    if st.session_state.search_history:
        for idx, search in enumerate(st.session_state.search_history):
            with st.expander(f"🔍 {search['query'][:40]}..."):
                st.write(f"**Query**: {search['query']}")
                st.write(f"**Results**: {search['result_count']}")
                st.write(f"**Time**: {search['timestamp'].strftime('%H:%M:%S')}")

                if st.button("Repeat Search", key=f"repeat_{idx}"):
                    st.session_state.current_query = search['query']
                    st.rerun()
    else:
        st.info("No search history yet")

    st.markdown("---")

    # Tips
    st.header("💡 Search Tips")
    st.markdown("""
    **How to search:**
    - Use natural language
    - Be specific about what you want
    - Mention time frames (today, this week, etc.)
    - Include status filters (hot, new, active, etc.)

    **Examples:**
    - "Show me hot leads from today"
    - "Find customers in Bloomfield Hills"
    - "List projects over $100k"
    - "Get calls with negative sentiment"
    """)

# Footer
st.markdown("---")
st.caption("🤖 Powered by OpenAI GPT-4o | Natural Language Understanding")
