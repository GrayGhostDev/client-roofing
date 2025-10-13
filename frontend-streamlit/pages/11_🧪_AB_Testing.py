"""
A/B Testing Dashboard

Create and manage A/B tests for ML models, features, and workflows.
Includes statistical significance testing and experiment analysis.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import requests
import json
from utils.auth import require_auth
from utils.api_client import get_api_base_url

# Require authentication
require_auth()

# API base URL
API_BASE = get_api_base_url()

st.title("🧪 A/B Testing Framework")
st.markdown("*Test model variants, features, and workflows with statistical rigor*")

# Create tabs
tabs = st.tabs(["📝 Create Experiment", "📊 Active Experiments", "📈 Results & Analysis"])

# ============================================================================
# TAB 1: CREATE EXPERIMENT
# ============================================================================
with tabs[0]:
    st.header("📝 Create New A/B Test")

    with st.form("create_experiment"):
        col1, col2 = st.columns(2)

        with col1:
            exp_name = st.text_input("Experiment Name*", placeholder="e.g., Lead Scoring Model V2 Test")
            hypothesis = st.text_area("Hypothesis*", placeholder="What are you testing?", height=100)
            metric = st.selectbox(
                "Primary Success Metric*",
                options=["conversion_rate", "revenue", "response_time", "lead_quality_score"],
                format_func=lambda x: {
                    "conversion_rate": "Conversion Rate",
                    "revenue": "Revenue",
                    "response_time": "Response Time",
                    "lead_quality_score": "Lead Quality Score"
                }[x]
            )

        with col2:
            description = st.text_area("Description*", placeholder="Detailed experiment description", height=100)
            min_sample_size = st.number_input("Min Sample Size per Variant", min_value=50, max_value=10000, value=100)
            significance_level = st.selectbox(
                "Significance Level",
                options=[0.01, 0.05, 0.10],
                index=1,
                format_func=lambda x: f"{x} (p-value)"
            )

        st.subheader("Variants Configuration")

        num_variants = st.number_input("Number of Variants", min_value=2, max_value=5, value=2)

        variants = []
        traffic_allocation = {}

        for i in range(num_variants):
            st.markdown(f"**Variant {i+1}**")
            col_a, col_b, col_c, col_d = st.columns([2, 2, 1, 3])

            with col_a:
                variant_id = st.text_input(
                    f"ID",
                    value=f"{'control' if i == 0 else f'treatment_{i}'}",
                    key=f"variant_id_{i}"
                )

            with col_b:
                variant_name = st.text_input(
                    f"Name",
                    value=f"{'Control' if i == 0 else f'Treatment {i}'}",
                    key=f"variant_name_{i}"
                )

            with col_c:
                traffic = st.number_input(
                    f"Traffic %",
                    min_value=0,
                    max_value=100,
                    value=int(100 / num_variants),
                    key=f"traffic_{i}"
                )

            with col_d:
                variant_type = st.selectbox(
                    f"Type",
                    options=["control", "treatment"],
                    index=0 if i == 0 else 1,
                    key=f"type_{i}"
                )

            # Configuration (optional JSON)
            config_json = st.text_area(
                f"Configuration (JSON, optional)",
                value="{}",
                height=68,  # Minimum height required by Streamlit
                key=f"config_{i}"
            )

            try:
                config = json.loads(config_json)
            except:
                config = {}

            variants.append({
                "id": variant_id,
                "name": variant_name,
                "type": variant_type,
                "config": config
            })

            traffic_allocation[variant_id] = traffic / 100

        submitted = st.form_submit_button("Create Experiment", type="primary")

        if submitted:
            if not exp_name or not hypothesis or not description:
                st.error("Please fill in all required fields (marked with *)")
            elif sum(traffic_allocation.values()) != 1.0:
                st.error(f"Traffic allocation must sum to 100% (currently {sum(traffic_allocation.values())*100:.0f}%)")
            else:
                experiment_config = {
                    "name": exp_name,
                    "description": description,
                    "hypothesis": hypothesis,
                    "metric": metric,
                    "variants": variants,
                    "traffic_allocation": traffic_allocation,
                    "min_sample_size": min_sample_size,
                    "significance_level": significance_level
                }

                try:
                    response = requests.post(
                        f"{API_BASE}/api/advanced-analytics/ab-testing/experiments",
                        json=experiment_config
                    )

                    if response.status_code == 201:
                        result = response.json()
                        st.success(f"✅ Experiment created! ID: {result['experiment_id']}")
                        st.balloons()
                    else:
                        st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Failed to create experiment: {str(e)}")

# ============================================================================
# TAB 2: ACTIVE EXPERIMENTS
# ============================================================================
with tabs[1]:
    st.header("📊 Active Experiments")

    # In a real implementation, you'd fetch a list of experiments
    # For now, allow user to input experiment ID
    experiment_id = st.text_input("Enter Experiment ID", placeholder="exp_20250101120000_abc12345")

    if experiment_id:
        col1, col2 = st.columns([2, 1])

        with col2:
            if st.button("Load Experiment"):
                try:
                    response = requests.get(
                        f"{API_BASE}/api/advanced-analytics/ab-testing/experiments/{experiment_id}/summary"
                    )

                    if response.status_code == 200:
                        data = response.json()
                        st.session_state[f'exp_{experiment_id}'] = data
                        st.success("✅ Experiment loaded!")
                    else:
                        st.error(f"Error: {response.json().get('error', 'Not found')}")
                except Exception as e:
                    st.error(f"Failed to load experiment: {str(e)}")

        with col1:
            if f'exp_{experiment_id}' in st.session_state:
                data = st.session_state[f'exp_{experiment_id}']

                st.subheader(data['name'])
                st.markdown(f"**Description:** {data['description']}")
                st.markdown(f"**Hypothesis:** {data['hypothesis']}")
                st.markdown(f"**Primary Metric:** {data['metric']}")

                # Metrics
                col_a, col_b, col_c, col_d = st.columns(4)
                with col_a:
                    st.metric("Total Samples", f"{data['total_samples']:,}")
                with col_b:
                    st.metric("Conversion Rate", f"{data['overall_conversion_rate']:.1f}%")
                with col_c:
                    min_met = "✅" if data['min_samples_met'] else "⏳"
                    st.metric("Min Samples Met", min_met)
                with col_d:
                    st.metric("Required per Variant", f"{data['min_sample_size']:,}")

                # Samples per variant
                st.subheader("📊 Traffic Distribution")
                samples_df = pd.DataFrame([
                    {"Variant": k, "Samples": v}
                    for k, v in data['samples_per_variant'].items()
                ])

                fig = px.bar(
                    samples_df,
                    x='Variant',
                    y='Samples',
                    title="Samples per Variant",
                    color='Samples',
                    color_continuous_scale='Blues'
                )

                st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 3: RESULTS & ANALYSIS
# ============================================================================
with tabs[2]:
    st.header("📈 Experiment Analysis & Results")

    experiment_id_analyze = st.text_input("Experiment ID to Analyze", placeholder="exp_20250101120000_abc12345")

    col1, col2 = st.columns([3, 1])

    with col2:
        confidence_level = st.selectbox(
            "Confidence Level",
            options=[0.80, 0.90, 0.95, 0.99],
            index=2,
            format_func=lambda x: f"{int(x*100)}%"
        )

        if st.button("Analyze Experiment", type="primary"):
            if not experiment_id_analyze:
                st.error("Please enter an experiment ID")
            else:
                try:
                    response = requests.get(
                        f"{API_BASE}/api/advanced-analytics/ab-testing/experiments/{experiment_id_analyze}/analyze",
                        params={'confidence_level': confidence_level}
                    )

                    if response.status_code == 200:
                        data = response.json()
                        st.session_state[f'analysis_{experiment_id_analyze}'] = data
                        st.success("✅ Analysis complete!")
                    else:
                        st.error(f"Error: {response.json().get('error', 'Not found')}")
                except Exception as e:
                    st.error(f"Failed to analyze experiment: {str(e)}")

    with col1:
        if experiment_id_analyze and f'analysis_{experiment_id_analyze}' in st.session_state:
            data = st.session_state[f'analysis_{experiment_id_analyze}']

            # Status and recommendation
            status = data['status']
            recommendation = data['recommendation']

            if status == 'winner_identified':
                st.success(f"🎉 Winner Identified!")
                winner = data['winner']
                st.info(f"**Winner:** {winner['variant_name']} with {winner['lift_vs_control']:+.1f}% lift")
            elif status == 'no_significant_difference':
                st.warning("⚠️ No Significant Difference Found")
            else:
                st.info(f"⏳ {status.replace('_', ' ').title()}")

            st.markdown(f"**Recommendation:** {recommendation}")

            # Variant comparison
            variants_df = pd.DataFrame(data['variants'])

            if not variants_df.empty:
                st.subheader("📊 Variant Performance")

                # Metrics display
                cols = st.columns(len(variants_df))
                for idx, (_, variant) in enumerate(variants_df.iterrows()):
                    with cols[idx]:
                        is_winner = variant['is_winner']
                        icon = "🏆" if is_winner else ""

                        st.metric(
                            f"{icon} {variant['variant_name']}",
                            f"{variant['conversion_rate']:.1f}%",
                            f"{variant['lift_vs_control']:+.1f}%" if variant['lift_vs_control'] != 0 else "Control"
                        )
                        st.caption(f"n={variant['sample_size']:,}")
                        if variant['is_significant']:
                            st.success("Significant ✓")

                # Comparison chart
                fig = go.Figure()

                for idx, row in variants_df.iterrows():
                    fig.add_trace(go.Bar(
                        name=row['variant_name'],
                        x=['Conversion Rate'],
                        y=[row['conversion_rate']],
                        error_y=dict(
                            type='data',
                            array=[(row['confidence_interval'][1] - row['confidence_interval'][0]) / 2]
                        ),
                        marker_color='#00cc66' if row['is_winner'] else '#4CAF50' if row['is_significant'] else '#999'
                    ))

                fig.update_layout(
                    title=f"Variant Comparison ({int(confidence_level*100)}% Confidence Intervals)",
                    yaxis_title="Conversion Rate (%)",
                    barmode='group',
                    height=400
                )

                st.plotly_chart(fig, use_container_width=True)

                # Detailed table
                st.subheader("📋 Detailed Results")
                st.dataframe(
                    variants_df[[
                        'variant_name', 'sample_size', 'conversion_rate',
                        'lift_vs_control', 'p_value', 'is_significant', 'is_winner'
                    ]].style.format({
                        'conversion_rate': '{:.2f}%',
                        'lift_vs_control': '{:+.2f}%',
                        'p_value': '{:.4f}'
                    }).applymap(
                        lambda x: 'background-color: #d4edda' if x == True else '',
                        subset=['is_winner']
                    ),
                    use_container_width=True
                )

                # Select winner
                if status == 'winner_identified':
                    st.subheader("🏆 Select Winner")

                    winner_variant = st.selectbox(
                        "Confirm Winner",
                        options=variants_df['variant_id'].tolist(),
                        format_func=lambda x: variants_df[variants_df['variant_id'] == x]['variant_name'].values[0]
                    )

                    if st.button("Confirm and Complete Experiment"):
                        try:
                            response = requests.post(
                                f"{API_BASE}/api/advanced-analytics/ab-testing/experiments/{experiment_id_analyze}/select-winner",
                                json={'winner_variant_id': winner_variant}
                            )

                            if response.status_code == 200:
                                st.success("✅ Winner selected and experiment completed!")
                                st.balloons()
                            else:
                                st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                        except Exception as e:
                            st.error(f"Failed to select winner: {str(e)}")

# Footer
st.markdown("---")
st.markdown("*Statistical significance testing with Chi-square tests and confidence intervals*")
