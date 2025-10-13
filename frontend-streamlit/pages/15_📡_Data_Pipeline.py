"""
📡 Data Pipeline Dashboard
Monitor and control the automated lead discovery pipeline
"""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
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
.pipeline-container {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 30px;
    border-radius: 15px;
    margin-bottom: 20px;
    color: white;
}
.source-card {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 10px;
    padding: 15px;
    margin: 10px 0;
}
.source-enabled {
    border-left: 4px solid #28a745;
}
.source-disabled {
    border-left: 4px solid #dc3545;
}
.metric-card {
    background-color: white;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.stage-indicator {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 8px;
}
.stage-success {
    background-color: #28a745;
}
.stage-running {
    background-color: #ffc107;
    animation: pulse 1.5s infinite;
}
.stage-pending {
    background-color: #6c757d;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'pipeline_running' not in st.session_state:
    st.session_state.pipeline_running = False
if 'last_results' not in st.session_state:
    st.session_state.last_results = None

# Title
st.title("📡 Automated Lead Discovery Pipeline")
st.markdown("*AI-powered system for discovering and scoring roofing leads from multiple data sources*")
st.markdown("---")

# ============================================================================
# PIPELINE CONTROL
# ============================================================================

st.markdown('<div class="pipeline-container">', unsafe_allow_html=True)
st.markdown("### 🎯 Pipeline Control")

col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    # City selection
    default_cities = [
        "Bloomfield Hills", "Birmingham", "Grosse Pointe",
        "Troy", "Rochester Hills", "West Bloomfield",
        "Ann Arbor", "Canton", "Plymouth", "Northville"
    ]

    selected_cities = st.multiselect(
        "Target Cities",
        default_cities,
        default=default_cities[:6]
    )

with col2:
    # Filters
    min_home_value = st.number_input(
        "Min Home Value ($)",
        min_value=300000,
        max_value=2000000,
        value=500000,
        step=50000
    )

    max_roof_age = st.slider(
        "Max Roof Age (years)",
        min_value=5,
        max_value=50,
        value=20
    )

with col3:
    date_range = st.number_input(
        "Days to Search",
        min_value=7,
        max_value=180,
        value=30
    )

    run_button = st.button(
        "🚀 Run Pipeline",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.pipeline_running
    )

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# RUN PIPELINE
# ============================================================================

if run_button and selected_cities:
    st.session_state.pipeline_running = True

    with st.spinner("🤖 AI is discovering leads across multiple data sources..."):
        try:
            # Call pipeline API
            response = requests.post(
                f"{API_BASE}/api/data-pipeline/run",
                json={
                    "cities": selected_cities,
                    "min_home_value": min_home_value,
                    "max_roof_age": max_roof_age,
                    "date_range_days": date_range
                },
                headers={"Content-Type": "application/json"},
                timeout=300  # 5 minutes
            )

            if response.status_code == 200:
                results = response.json()
                st.session_state.last_results = results
                st.session_state.pipeline_running = False

                if results.get("status") == "success":
                    st.success(f"✅ Pipeline complete! Ingested {results.get('total_ingested_leads', 0)} leads")
                else:
                    st.error(f"❌ Pipeline failed: {results.get('error', 'Unknown error')}")
            else:
                st.error(f"❌ Pipeline request failed: {response.status_code}")
                st.session_state.pipeline_running = False

        except requests.exceptions.Timeout:
            st.error("⏱️ Pipeline timed out after 5 minutes")
            st.session_state.pipeline_running = False
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.session_state.pipeline_running = False

# ============================================================================
# PIPELINE RESULTS
# ============================================================================

if st.session_state.last_results:
    results = st.session_state.last_results

    st.markdown("---")
    st.subheader("📊 Pipeline Execution Results")

    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Total Raw Leads",
            results.get("total_raw_leads", 0)
        )

    with col2:
        st.metric(
            "Enriched Leads",
            results.get("total_enriched_leads", 0)
        )

    with col3:
        st.metric(
            "Validated Leads",
            results.get("total_validated_leads", 0)
        )

    with col4:
        st.metric(
            "Ingested Leads",
            results.get("total_ingested_leads", 0)
        )

    with col5:
        duration = results.get("duration_seconds", 0)
        st.metric(
            "Duration",
            f"{duration:.1f}s"
        )

    # Deduplication rate
    dedup_rate = results.get("deduplication_rate", 0)
    st.info(f"📈 Deduplication Rate: {dedup_rate:.1f}% (removed duplicates)")

    # Pipeline stages
    st.markdown("### 🔄 Pipeline Stages")

    stages = results.get("stages", {})

    for stage_name, stage_data in stages.items():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**{stage_name.replace('_', ' ').title()}**")
            st.caption(f"Sources: {', '.join(stage_data.get('sources', []))}")

        with col2:
            st.metric("Leads Found", stage_data.get("leads_found", 0))

# ============================================================================
# DATA SOURCES STATUS
# ============================================================================

st.markdown("---")
st.subheader("🌐 Data Sources")

try:
    response = requests.get(f"{API_BASE}/api/data-pipeline/status", timeout=10)

    if response.status_code == 200:
        status_data = response.json()
        data_sources = status_data.get("data_sources", {})

        # Group by type
        sources_by_type = {}
        for name, info in data_sources.items():
            source_type = info.get("type", "unknown")
            if source_type not in sources_by_type:
                sources_by_type[source_type] = []
            sources_by_type[source_type].append((name, info))

        # Display by type
        for source_type, sources in sources_by_type.items():
            st.markdown(f"#### {source_type.replace('_', ' ').title()}")

            cols = st.columns(3)
            for idx, (name, info) in enumerate(sources):
                with cols[idx % 3]:
                    enabled = info.get("enabled", False)
                    priority = info.get("priority", 0)

                    css_class = "source-enabled" if enabled else "source-disabled"
                    status_text = "✅ Enabled" if enabled else "⚠️ Disabled"

                    st.markdown(f'<div class="source-card {css_class}">', unsafe_allow_html=True)
                    st.markdown(f"**{name.replace('_', ' ').title()}**")
                    st.markdown(f"Status: {status_text}")
                    st.markdown(f"Priority: {'⭐' * priority}")
                    st.markdown('</div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Failed to load data sources: {str(e)}")

# ============================================================================
# LEAD SCORING CALCULATOR
# ============================================================================

st.markdown("---")
st.subheader("🎯 Lead Scoring Calculator")
st.markdown("*Test the lead scoring algorithm with custom inputs*")

with st.expander("Calculate Lead Score"):
    col1, col2 = st.columns(2)

    with col1:
        test_roof_age = st.number_input("Roof Age (years)", 0, 50, 22)
        test_home_value = st.number_input("Home Value ($)", 200000, 2000000, 750000, 50000)
        test_hail = st.number_input("Hail Size (inches)", 0.0, 5.0, 2.0, 0.5)
        test_wind = st.number_input("Wind Speed (mph)", 0, 150, 75, 5)

    with col2:
        test_leak = st.checkbox("Has Active Leak")
        test_intent = st.selectbox(
            "Intent Level",
            ["none", "active_search", "information_gathering", "problem_reporting"]
        )
        test_engagement = st.selectbox(
            "Engagement Level",
            ["none", "low", "medium", "high"]
        )

    if st.button("Calculate Score", use_container_width=True):
        try:
            score_response = requests.post(
                f"{API_BASE}/api/data-pipeline/score-lead",
                json={
                    "roof_age": test_roof_age,
                    "home_value": test_home_value,
                    "hail_size": test_hail,
                    "wind_speed": test_wind,
                    "has_leak": test_leak,
                    "intent": test_intent,
                    "engagement_level": test_engagement
                },
                timeout=10
            )

            if score_response.status_code == 200:
                score_data = score_response.json()

                col1, col2, col3 = st.columns(3)

                with col1:
                    total_score = score_data.get("total_score", 0)
                    st.metric("Total Score", f"{total_score}/100")

                with col2:
                    temp = score_data.get("temperature", "cool")
                    temp_emoji = {
                        "hot": "🔥",
                        "warm": "😊",
                        "cool": "😐",
                        "cold": "❄️"
                    }
                    st.metric("Temperature", f"{temp_emoji.get(temp, '')} {temp.upper()}")

                with col3:
                    confidence = score_data.get("confidence", 0)
                    st.metric("Confidence", f"{confidence:.0%}")

                # Breakdown
                st.markdown("**Score Breakdown:**")
                breakdown = score_data.get("breakdown", {})

                for component, score in breakdown.items():
                    component_name = component.replace("_", " ").title()
                    st.progress(score / 25, text=f"{component_name}: {score}")

                # Reasons
                st.markdown("**Scoring Factors:**")
                for reason in score_data.get("reasons", []):
                    st.markdown(f"- {reason}")

        except Exception as e:
            st.error(f"Failed to calculate score: {str(e)}")

# ============================================================================
# DOCUMENTATION
# ============================================================================

st.markdown("---")
st.subheader("📚 Pipeline Documentation")

with st.expander("How the Pipeline Works"):
    st.markdown("""
    ### 7-Stage Lead Discovery Process

    #### Stage 1: Property Discovery
    - County property assessor records
    - Building permit databases
    - Tax assessor data
    - Identifies properties by age, value, and roof condition

    #### Stage 2: Storm Damage Detection
    - NOAA Storm Events Database
    - Weather Underground API
    - Insurance claim data
    - Maps storm paths to premium properties

    #### Stage 3: Social Media Monitoring
    - Facebook local groups
    - Nextdoor neighborhoods
    - Twitter/X local search
    - Identifies active homeowners seeking roofing services

    #### Stage 4: Market Intelligence
    - Competitor website analysis
    - Review platform mining (unhappy customers)
    - Real estate listings (new homeowners)
    - HomeAdvisor/Angi project leads

    #### Stage 5: Lead Enrichment & Scoring
    - AI-powered lead scoring (0-100 points)
    - 5 scoring components:
        - Roof Age (0-25 points)
        - Storm Damage (0-25 points)
        - Financial Capacity (0-20 points)
        - Urgency (0-15 points)
        - Behavioral Intent (0-15 points)

    #### Stage 6: Deduplication & Validation
    - Remove duplicate leads across sources
    - Validate contact information
    - Verify minimum data quality
    - Check against existing CRM records

    #### Stage 7: Automated Ingestion
    - Import validated leads into CRM
    - Assign temperature (hot/warm/cool/cold)
    - Generate initial notes with scoring factors
    - Ready for sales team follow-up
    """)

with st.expander("Lead Scoring Algorithm"):
    st.markdown("""
    ### 🎯 iSwitchRoofs Lead Scoring Formula

    **Total Score: 0-100 points**

    #### 1. Roof Age Score (0-25 points)
    - Age 21+ years: 25 points (urgent replacement)
    - Age 16-20 years: 20 points (decision phase)
    - Age 11-15 years: 10 points (consideration)
    - Age 6-10 years: 5 points (planning)
    - Age 0-5 years: 0 points (too new)

    #### 2. Storm Damage Score (0-25 points)
    - Major storm (>2" hail, >80 mph wind): 25 points
    - Moderate storm (1-2" hail, 60-80 mph): 15 points
    - Minor storm (<1" hail, <60 mph): 5 points
    - Insurance claim filed: +5 bonus points

    #### 3. Financial Capacity Score (0-20 points)
    - Home value >$750K: 20 points (ultra-premium)
    - Home value $500-750K: 15 points (premium target)
    - Home value $300-500K: 10 points (mid-tier)
    - Home value <$300K: 5 points
    - Recent home purchase: +5 bonus points

    #### 4. Urgency Score (0-15 points)
    - Active leak: 15 points (URGENT)
    - Requesting quotes: 12 points (ready to buy)
    - Visible damage: 10 points
    - General inquiry: 5 points

    #### 5. Behavioral Score (0-15 points)
    - Social media post seeking roofer: 15 points
    - Requested inspection: 12 points
    - Engaged with content: 10 points
    - Website visit only: 5 points

    #### Temperature Mapping
    - **HOT (80-100)**: Immediate action, high probability
    - **WARM (60-79)**: Ready to engage, good probability
    - **COOL (40-59)**: Early stage, nurture needed
    - **COLD (0-39)**: Long-term nurture
    """)

with st.expander("Data Sources & APIs"):
    st.markdown("""
    ### 🌐 Integrated Data Sources

    #### Public Databases (Free)
    - County Property Assessor Records
    - Building Permit Databases
    - NOAA Storm Events Database
    - National Weather Service Alerts

    #### Paid APIs
    - Weather Underground ($0.001/request)
    - Insurance Claims Data ($0.50/request)
    - Zillow/Real Estate APIs ($0.10/request)

    #### Social Media APIs
    - Facebook Graph API (free with limits)
    - Twitter API v2 (free tier available)
    - Nextdoor (manual/scraping)

    #### Web Scraping
    - Competitor websites
    - Google My Business reviews
    - Yelp reviews
    - Real estate listings

    **Total Estimated Cost**: $50-200/month depending on volume
    """)

# Footer
st.markdown("---")
st.caption("🤖 Powered by AI | Automated Lead Discovery System")
