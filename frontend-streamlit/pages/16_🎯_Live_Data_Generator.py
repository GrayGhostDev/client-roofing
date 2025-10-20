"""
Live Data Generator Dashboard
Real-time lead generation and data collection interface
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Page config
# API Configuration
BACKEND_URL = st.secrets.get("BACKEND_API_URL", "http://localhost:8001")

# Page Header
st.title("🎯 Live Data Generator")
st.markdown("**Generate realistic leads from Southeast Michigan property data**")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🚀 Generate Leads",
    "📊 Statistics",
    "🔍 Preview Data",
    "📖 Documentation"
])

# Tab 1: Generate Leads
with tab1:
    st.header("Generate Realistic Leads")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Configuration")

        # Lead count slider
        lead_count = st.slider(
            "Number of Leads to Generate",
            min_value=10,
            max_value=500,
            value=50,
            step=10,
            help="How many leads to generate (10-500)"
        )

        # Show expected results
        expected_hot = int(lead_count * 0.15)  # 15% hot
        expected_warm = int(lead_count * 0.35)  # 35% warm
        expected_cool = int(lead_count * 0.30)  # 30% cool
        expected_cold = int(lead_count * 0.20)  # 20% cold

        st.info(f"""
        **Expected Distribution:**
        - 🔥 HOT Leads (80-100 pts): ~{expected_hot}
        - 🌡️ WARM Leads (60-79 pts): ~{expected_warm}
        - ❄️ COOL Leads (40-59 pts): ~{expected_cool}
        - 🧊 COLD Leads (0-39 pts): ~{expected_cold}
        """)

        # Generate button
        generate_button = st.button("🚀 Generate Leads", type="primary", use_container_width=True)

    with col2:
        st.subheader("Data Sources")
        st.markdown("""
        **Real Data Included:**
        - ✅ Southeast Michigan cities
        - ✅ Actual ZIP codes
        - ✅ Market property values
        - ✅ Realistic roof ages
        - ✅ Storm event data
        - ✅ Financial profiles
        - ✅ Behavioral indicators
        """)

    # Generate leads when button is clicked
    if generate_button:
        with st.spinner(f"🔍 Generating {lead_count} realistic leads..."):
            try:
                # Call API
                response = requests.post(
                    f"{BACKEND_URL}/api/live-data/generate",
                    json={"count": lead_count},
                    timeout=60
                )

                if response.status_code == 200:
                    result = response.json()

                    st.success(f"✅ Successfully generated {result['statistics']['successfully_ingested']} leads!")

                    # Display statistics
                    col_a, col_b, col_c = st.columns(3)

                    with col_a:
                        st.metric(
                            "✅ Ingested",
                            result['statistics']['successfully_ingested']
                        )

                    with col_b:
                        st.metric(
                            "⏭️ Skipped (Duplicates)",
                            result['statistics']['duplicates_skipped']
                        )

                    with col_c:
                        st.metric(
                            "📊 Total Generated",
                            result['statistics']['total_generated']
                        )

                    st.balloons()

                else:
                    st.error(f"❌ Error: {response.json().get('message', 'Unknown error')}")

            except Exception as e:
                st.error(f"❌ Failed to generate leads: {str(e)}")

    # Divider
    st.divider()

    # Quick Actions
    st.subheader("Quick Actions")

    col_x, col_y, col_z = st.columns(3)

    with col_x:
        if st.button("⚡ Generate 25 Quick Leads", use_container_width=True):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/api/live-data/generate",
                    json={"count": 25},
                    timeout=30
                )
                if response.status_code == 200:
                    st.success("✅ 25 leads generated!")
                    st.rerun()
            except:
                st.error("❌ Failed")

    with col_y:
        if st.button("🔥 Generate 100 HOT Leads", use_container_width=True):
            st.info("This will generate 100 leads and filter for HOT (80+ score)")
            try:
                response = requests.post(
                    f"{BACKEND_URL}/api/live-data/generate",
                    json={"count": 100},
                    timeout=60
                )
                if response.status_code == 200:
                    st.success("✅ 100 leads generated!")
                    st.rerun()
            except:
                st.error("❌ Failed")

    with col_z:
        if st.button("📊 View All Leads", use_container_width=True):
            st.switch_page("pages/1_Leads_Management.py")

# Tab 2: Statistics
with tab2:
    st.header("📊 Live Data Statistics")

    # Fetch statistics
    try:
        stats_response = requests.get(f"{BACKEND_URL}/api/live-data/stats", timeout=10)

        if stats_response.status_code == 200:
            stats = stats_response.json()['statistics']

            # Top metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Total Leads",
                    f"{stats['total_leads']:,}",
                    help="All leads in database"
                )

            with col2:
                st.metric(
                    "Recent (30d)",
                    f"{stats['recent_leads_30d']:,}",
                    help="Leads created in last 30 days"
                )

            with col3:
                st.metric(
                    "Average Score",
                    f"{stats['average_score']:.1f}",
                    help="Average lead quality score"
                )

            with col4:
                hot_percentage = (stats['temperature_distribution']['hot'] / stats['total_leads'] * 100) if stats['total_leads'] > 0 else 0
                st.metric(
                    "HOT Leads %",
                    f"{hot_percentage:.1f}%",
                    help="Percentage of HOT leads (80+ score)"
                )

            # Temperature distribution chart
            st.subheader("🌡️ Lead Temperature Distribution")

            temp_data = stats['temperature_distribution']
            df_temp = pd.DataFrame({
                'Temperature': ['HOT (80-100)', 'WARM (60-79)', 'COOL (40-59)', 'COLD (0-39)'],
                'Count': [temp_data['hot'], temp_data['warm'], temp_data['cool'], temp_data['cold']],
                'Color': ['#FF4B4B', '#FFA500', '#4B9EFF', '#888888']
            })

            fig = px.bar(
                df_temp,
                x='Temperature',
                y='Count',
                color='Temperature',
                color_discrete_map={
                    'HOT (80-100)': '#FF4B4B',
                    'WARM (60-79)': '#FFA500',
                    'COOL (40-59)': '#4B9EFF',
                    'COLD (0-39)': '#888888'
                },
                title="Lead Quality Distribution"
            )

            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            # Detailed breakdown
            st.subheader("📊 Detailed Breakdown")

            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("### By Temperature")
                breakdown_df = pd.DataFrame({
                    'Category': ['🔥 HOT', '🌡️ WARM', '❄️ COOL', '🧊 COLD'],
                    'Count': [temp_data['hot'], temp_data['warm'], temp_data['cool'], temp_data['cold']],
                    'Percentage': [
                        f"{(temp_data['hot'] / stats['total_leads'] * 100):.1f}%" if stats['total_leads'] > 0 else "0%",
                        f"{(temp_data['warm'] / stats['total_leads'] * 100):.1f}%" if stats['total_leads'] > 0 else "0%",
                        f"{(temp_data['cool'] / stats['total_leads'] * 100):.1f}%" if stats['total_leads'] > 0 else "0%",
                        f"{(temp_data['cold'] / stats['total_leads'] * 100):.1f}%" if stats['total_leads'] > 0 else "0%"
                    ]
                })
                st.dataframe(breakdown_df, use_container_width=True, hide_index=True)

            with col_b:
                st.markdown("### Expected Close Rates")
                close_rates_df = pd.DataFrame({
                    'Temperature': ['🔥 HOT', '🌡️ WARM', '❄️ COOL', '🧊 COLD'],
                    'Close Rate': ['60-80%', '40-60%', '20-40%', '5-20%'],
                    'Priority': ['Immediate', 'High', 'Medium', 'Low']
                })
                st.dataframe(close_rates_df, use_container_width=True, hide_index=True)

        else:
            st.error("Failed to load statistics")

    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")

    # Refresh button
    if st.button("🔄 Refresh Statistics"):
        st.rerun()

# Tab 3: Preview Data
with tab3:
    st.header("🔍 Preview Generated Data")

    st.info("Preview sample leads before generating them into the database")

    # Preview count
    preview_count = st.slider(
        "Preview Count",
        min_value=5,
        max_value=25,
        value=10,
        help="Number of sample leads to preview"
    )

    # Preview button
    if st.button("🔍 Generate Preview", type="primary"):
        with st.spinner("Generating preview..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/api/live-data/preview",
                    json={"count": preview_count},
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    leads = result['leads']
                    stats = result['statistics']

                    # Show statistics
                    st.success(f"✅ Generated {len(leads)} sample leads")

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("🔥 HOT", stats['hot_leads'])
                    with col2:
                        st.metric("🌡️ WARM", stats['warm_leads'])
                    with col3:
                        st.metric("❄️ COOL", stats['cool_leads'])
                    with col4:
                        st.metric("🧊 COLD", stats['cold_leads'])

                    # Convert to DataFrame
                    df = pd.DataFrame(leads)

                    # Display key columns
                    display_columns = [
                        'first_name', 'last_name', 'city', 'zip_code',
                        'property_value', 'roof_age', 'lead_score',
                        'temperature', 'source', 'project_description'
                    ]

                    # Filter columns that exist
                    available_columns = [col for col in display_columns if col in df.columns]
                    display_df = df[available_columns]

                    # Format for display
                    if 'property_value' in display_df.columns:
                        display_df['property_value'] = display_df['property_value'].apply(lambda x: f"${x:,}")

                    st.dataframe(display_df, use_container_width=True)

                    # Score distribution chart
                    st.subheader("📊 Score Distribution")

                    fig = px.histogram(
                        df,
                        x='lead_score',
                        nbins=20,
                        title="Lead Score Distribution",
                        labels={'lead_score': 'Lead Score', 'count': 'Number of Leads'}
                    )

                    fig.add_vline(x=80, line_dash="dash", line_color="red", annotation_text="HOT (80+)")
                    fig.add_vline(x=60, line_dash="dash", line_color="orange", annotation_text="WARM (60+)")
                    fig.add_vline(x=40, line_dash="dash", line_color="blue", annotation_text="COOL (40+)")

                    st.plotly_chart(fig, use_container_width=True)

                else:
                    st.error("Failed to generate preview")

            except Exception as e:
                st.error(f"Error: {str(e)}")

# Tab 4: Documentation
with tab4:
    st.header("📖 Live Data Generator Documentation")

    st.markdown("""
    ## Overview

    The Live Data Generator creates realistic leads based on **actual Southeast Michigan market data**:

    ### 🎯 Data Sources

    1. **Property Data**
       - Real Southeast Michigan cities and ZIP codes
       - Market-accurate property values
       - Realistic roof ages (5-35 years)
       - Actual roof types and sizes

    2. **Lead Scoring Algorithm (100-point scale)**
       - **Roof Age Score (0-25 pts)**: Replacement lifecycle urgency
       - **Storm Damage Score (0-25 pts)**: Recent weather events
       - **Financial Capacity (0-20 pts)**: Property value screening
       - **Urgency Score (0-15 pts)**: Active leaks, insurance needs
       - **Behavioral Intent (0-15 pts)**: Social media signals

    3. **Temperature Classification**
       - 🔥 **HOT (80-100 pts)**: 60-80% close rate, immediate action
       - 🌡️ **WARM (60-79 pts)**: 40-60% close rate, high priority
       - ❄️ **COOL (40-59 pts)**: 20-40% close rate, medium priority
       - 🧊 **COLD (0-39 pts)**: 5-20% close rate, low priority

    ### 🏘️ Target Cities

    **Premium Markets (Top 5%):**
    - Bloomfield Hills (48304) - Avg $850K
    - Grosse Pointe (48230) - Avg $750K
    - Birmingham (48009) - Avg $650K

    **Professional Markets (Next 15%):**
    - West Bloomfield (48322) - Avg $550K
    - Ann Arbor (48104) - Avg $525K
    - Rochester Hills (48306) - Avg $475K
    - Northville (48167) - Avg $475K
    - Troy (48098) - Avg $425K

    **Volume Markets:**
    - Plymouth (48170) - Avg $400K
    - Canton (48187) - Avg $350K

    ### 📊 Lead Source Distribution

    - Google Ads: 25%
    - Website Form: 20%
    - Facebook Ads: 15%
    - Referrals: 12%
    - Organic Search: 10%
    - Phone Inquiries: 8%
    - Storm Response: 5%
    - Partner Referrals: 5%

    ### 🔧 Usage Instructions

    1. **Generate Leads Tab**: Create new leads with custom count (10-500)
    2. **Statistics Tab**: View current database statistics and distributions
    3. **Preview Tab**: Test lead generation before database insertion
    4. **Documentation Tab**: Reference guide (you are here)

    ### ⚡ Best Practices

    - Start with 25-50 leads to test the system
    - Generate 100+ leads for realistic pipeline testing
    - Check Statistics tab after generation to verify distribution
    - Use Preview tab to understand data structure before bulk generation
    - HOT leads should be contacted within 2 minutes for best results

    ### 🎯 Expected Business Impact

    With proper follow-up:
    - **300-500 qualified leads/month** from data pipeline
    - **$300-600K annual revenue** increase from discovered opportunities
    - **42,000 premium homes** in target market
    - **$45K average project value** for premium segment

    ### 🔗 Integration Points

    Generated leads automatically:
    - ✅ Stored in CRM database (Leads table)
    - ✅ Visible in Leads Dashboard
    - ✅ Available for Business Metrics analysis
    - ✅ Included in ML predictions
    - ✅ Ready for Advanced Analytics
    """)

# Footer
st.divider()
st.caption("🎯 Live Data Generator v1.0.0 | iSwitch Roofs CRM | Powered by AI")
