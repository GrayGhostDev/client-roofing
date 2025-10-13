"""
iSwitch Roofs CRM - Enhanced Analytics Dashboard
Comprehensive business analytics, KPIs, and performance metrics with LIVE DATA
Version: 2.0.0
Date: 2025-10-09
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.api_client import get_api_client
from utils.realtime import (
    auto_refresh,
    display_last_updated,
    create_realtime_indicator,
    show_connection_status,
    display_data_source_badge
)
from utils.charts import (
    create_kpi_card,
    create_conversion_funnel,
    create_response_time_gauge,
    create_marketing_roi_chart,
    create_revenue_progress_chart,
    create_conversion_by_temperature,
    create_geographic_heatmap
)
from utils.pusher_script import inject_pusher_script, pusher_status_indicator
from utils.notifications import notification_preferences_sidebar

# Page config
# Initialize API client
api_client = get_api_client()

# Auto-refresh every 30 seconds
auto_refresh(interval_ms=30000, key="analytics_refresh")

# Inject Pusher real-time client (subscribes to all analytics channels)
inject_pusher_script(channels=['analytics', 'leads', 'customers', 'projects'], debug=False)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        padding: 20px;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-bottom: 20px;
    }
    .metric-value {
        font-size: 2.5em;
        font-weight: bold;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 1em;
        opacity: 0.9;
    }
    .metric-delta {
        font-size: 0.9em;
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("📊 Enhanced Business Analytics Dashboard")
st.markdown("---")

# Sidebar filters
with st.sidebar:
    st.header("⚙️ Dashboard Settings")

    # Connection status
    show_connection_status(api_client)
    create_realtime_indicator(active=True)
    display_last_updated(key="analytics_last_updated")

    # Pusher status and notification preferences
    pusher_status_indicator()
    notification_preferences_sidebar()

    st.markdown("---")

    # Timeframe selector
    timeframe_options = {
        "Today": "today",
        "This Week": "week_to_date",
        "This Month": "month_to_date",
        "Last Month": "last_month",
        "This Quarter": "quarter_to_date",
        "This Year": "year_to_date"
    }

    timeframe_display = st.selectbox(
        "Timeframe",
        list(timeframe_options.keys()),
        index=2
    )
    timeframe = timeframe_options[timeframe_display]

    # Days for marketing/premium metrics
    days = st.slider("Days for Trend Analysis", 7, 90, 30)

    # Metric selection
    st.subheader("Visible Metrics")
    show_revenue = st.checkbox("Revenue Growth", value=True)
    show_response = st.checkbox("Lead Response Time", value=True)
    show_premium = st.checkbox("Premium Markets", value=True)
    show_marketing = st.checkbox("Marketing ROI", value=True)
    show_conversion = st.checkbox("Conversion Analysis", value=True)

    st.markdown("---")

    # Refresh and export
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

    if st.button("📥 Export Report", use_container_width=True):
        st.info("Export functionality coming soon!")

# Fetch business summary
st.header("🎯 Live Business Metrics")

try:
    summary = api_client.get_business_summary()

    if summary and "success" in summary and summary["success"]:
        display_data_source_badge("live")
        data = summary.get("data", {})

        # ===== REVENUE GROWTH SECTION =====
        if show_revenue:
            st.header("💰 Revenue Growth Path ($6M → $30M)")

            revenue_data = data.get("revenue_growth", {})
            current_month = revenue_data.get("current_month", {})
            year1_progress = revenue_data.get("year_1_progress", {})

            # KPI Cards
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                create_kpi_card(
                    label="Current Month",
                    value=current_month.get("revenue", 0),
                    delta=current_month.get("progress_percent", 0),
                    delta_label=f"{current_month.get('progress_percent', 0):.1f}% of $500K target",
                    target=500000,
                    format_func=lambda x: f"${x/1000:.0f}K",
                    color="#667eea"
                )

            with col2:
                create_kpi_card(
                    label="YTD Revenue",
                    value=revenue_data.get("year_to_date", {}).get("revenue", 0),
                    format_func=lambda x: f"${x/1000000:.2f}M",
                    color="#764ba2"
                )

            with col3:
                create_kpi_card(
                    label="Year 1 Target Gap",
                    value=year1_progress.get("gap", 0),
                    format_func=lambda x: f"${x/1000:.0f}K",
                    color="#f5576c" if year1_progress.get("gap", 0) > 0 else "#43e97b"
                )

            with col4:
                on_track = year1_progress.get("on_track", False)
                create_kpi_card(
                    label="Status",
                    value="✅ On Track" if on_track else "⚠️ Attention Needed",
                    color="#43e97b" if on_track else "#ff9800"
                )

            # Revenue growth chart
            create_revenue_progress_chart(
                current=current_month.get("revenue", 0),
                target_year1=666667,  # $8M/12 months
                target_year2=1500000,  # $18M/12 months
                target_year3=2500000,  # $30M/12 months
                title="Revenue Growth Journey ($6M → $30M)"
            )

            st.markdown("---")

        # ===== LEAD RESPONSE TIME SECTION =====
        if show_response:
            st.header("⏱️ Lead Response Time (2-Minute Target)")

            response_data = data.get("lead_response", {})

            col1, col2 = st.columns(2)

            with col1:
                create_response_time_gauge(
                    avg_time=response_data.get("avg_response_time_seconds", 0),
                    target=120,
                    title="Average Response Time"
                )

            with col2:
                st.subheader("Response Performance")

                total_leads = response_data.get("leads_under_target", 0) + response_data.get("leads_over_target", 0)
                under_target = response_data.get("leads_under_target", 0)
                over_target = response_data.get("leads_over_target", 0)

                col2_1, col2_2 = st.columns(2)
                with col2_1:
                    st.metric("Under 2 Minutes", under_target, f"{response_data.get('percent_under_target', 0):.1f}%")
                with col2_2:
                    st.metric("Over 2 Minutes", over_target, f"{100 - response_data.get('percent_under_target', 0):.1f}%")

                # Impact calculation
                potential_lost = response_data.get("potential_lost_conversions", 0)
                if potential_lost > 0:
                    st.warning(f"⚠️ **Potential Impact**: {potential_lost:.1f} additional conversions possible with <2min response time (78% boost)")
                else:
                    st.success("✅ **Excellent Performance**: Meeting 2-minute target consistently!")

            st.markdown("---")

        # ===== PREMIUM MARKETS SECTION =====
        if show_premium:
            st.header("🏘️ Premium Market Penetration")

            premium_data = data.get("premium_markets", {})

            col1, col2, col3 = st.columns(3)

            with col1:
                st.subheader("Ultra-Premium")
                ultra = premium_data.get("ultra_premium", {})
                st.markdown(f"**Cities**: {', '.join(ultra.get('cities', []))}")
                st.metric("Revenue", f"${ultra.get('revenue', 0):,.0f}", f"{ultra.get('deals_closed', 0)} deals")
                st.metric("Avg Deal Size", f"${ultra.get('avg_deal_size', 0):,.0f}", f"{ultra.get('conversion_rate', 0):.1f}% conversion")

            with col2:
                st.subheader("Professional")
                prof = premium_data.get("professional", {})
                st.markdown(f"**Cities**: {', '.join(prof.get('cities', []))}")
                st.metric("Revenue", f"${prof.get('revenue', 0):,.0f}", f"{prof.get('deals_closed', 0)} deals")
                st.metric("Avg Deal Size", f"${prof.get('avg_deal_size', 0):,.0f}", f"{prof.get('conversion_rate', 0):.1f}% conversion")

            with col3:
                st.subheader("Total Summary")
                summary_prem = premium_data.get("summary", {})
                st.metric("Total Revenue", f"${summary_prem.get('total_revenue', 0):,.0f}")
                st.metric("Total Deals", summary_prem.get("total_deals", 0))
                st.metric("Avg Deal", f"${summary_prem.get('avg_deal_size', 0):,.0f}")
                st.metric("Market Penetration", f"{summary_prem.get('market_penetration_percent', 0):.3f}%")

            st.markdown("---")

        # ===== MARKETING ROI SECTION =====
        if show_marketing:
            st.header("📈 Marketing Channel ROI")

            roi_data = data.get("marketing_roi", {})
            channels = roi_data.get("channels", {})
            roi_summary = roi_data.get("summary", {})

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Leads", roi_summary.get("total_leads", 0))
            with col2:
                st.metric("Conversions", roi_summary.get("total_conversions", 0),
                         f"{roi_summary.get('overall_conversion_rate', 0):.1f}%")
            with col3:
                st.metric("Total Revenue", f"${roi_summary.get('total_revenue', 0):,.0f}")
            with col4:
                st.metric("Overall ROI", f"{roi_summary.get('overall_roi', 0):,.0f}%")

            # Channel comparison chart
            if channels:
                create_marketing_roi_chart(channels)

            # Detailed channel table
            st.subheader("Channel Performance Details")
            channel_df = []
            for channel_name, channel_data in channels.items():
                channel_df.append({
                    "Channel": channel_name,
                    "Leads": channel_data.get("leads_generated", 0),
                    "Conversions": channel_data.get("conversions", 0),
                    "Conv. Rate": f"{channel_data.get('conversion_rate', 0):.1f}%",
                    "Revenue": f"${channel_data.get('revenue', 0):,.0f}",
                    "Cost": f"${channel_data.get('estimated_cost', 0):,.0f}",
                    "Cost/Lead": f"${channel_data.get('cost_per_lead', 0):.2f}",
                    "ROI": f"{channel_data.get('roi_percent', 0):,.0f}%",
                    "Status": "✅" if channel_data.get("status") == "profitable" else "⚠️"
                })

            if channel_df:
                df = pd.DataFrame(channel_df)
                st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown("---")

        # ===== CONVERSION OPTIMIZATION SECTION =====
        if show_conversion:
            st.header("🎯 Conversion Optimization (25-35% Target)")

            conversion_data = data.get("conversion", {})
            overall = conversion_data.get("overall", {})
            by_temp = conversion_data.get("by_temperature", {})
            opportunities = conversion_data.get("optimization_opportunities", [])

            # Overall metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Leads", overall.get("total_leads", 0))
            with col2:
                st.metric("Converted", overall.get("converted", 0))
            with col3:
                rate = overall.get("conversion_rate", 0)
                target = overall.get("target_rate", 25)
                delta = rate - target
                st.metric("Conversion Rate", f"{rate:.1f}%", f"{delta:+.1f}% vs target")
            with col4:
                status = overall.get("status", "unknown")
                color = {"excellent": "🟢", "good": "🟡", "needs_improvement": "🔴"}.get(status, "⚪")
                st.metric("Status", f"{color} {status.replace('_', ' ').title()}")

            # Conversion by temperature
            create_conversion_by_temperature(by_temp)

            # Conversion funnel
            funnel_data = {
                "Total Leads": overall.get("total_leads", 0),
                "Hot Leads": by_temp.get("hot", {}).get("total", 0),
                "Warm Leads": by_temp.get("warm", {}).get("total", 0),
                "Qualified": by_temp.get("hot", {}).get("converted", 0) + by_temp.get("warm", {}).get("converted", 0),
                "Converted": overall.get("converted", 0)
            }
            create_conversion_funnel(funnel_data, target_rate=25.0)

            # Optimization opportunities
            if opportunities:
                st.subheader("🚀 Optimization Opportunities")
                for opp in opportunities:
                    priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(opp.get("priority", "low"), "⚪")
                    st.info(f"{priority_emoji} **{opp.get('type', 'Unknown').replace('_', ' ').title()}** ({opp.get('priority', 'low').upper()} priority)\n\n{opp.get('message', '')}\n\n**Potential Impact**: {opp.get('potential_impact', 'Unknown')}")

            st.markdown("---")

    else:
        display_data_source_badge("demo")
        st.warning("⚠️ Live data temporarily unavailable. Please check backend connection.")

except Exception as e:
    display_data_source_badge("demo")
    st.error(f"❌ Failed to fetch analytics data: {str(e)}")
    st.info("💡 Make sure backend is running on http://localhost:8001")
    st.info("💡 Verify business_metrics blueprint is registered")

# Footer with insights
st.markdown("---")
st.header("💡 Key Insights & Recommendations")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("""
    **2-Minute Response Time**

    Responding to leads within 2 minutes increases conversion by 78%.
    Monitor response times closely and implement automated alerts.
    """)

with col2:
    st.success("""
    **Premium Market Focus**

    Ultra-premium segment ($45K avg) and professional segment ($27K avg)
    are key growth drivers. Prioritize Bloomfield Hills, Birmingham, and Troy.
    """)

with col3:
    st.warning("""
    **Marketing ROI Optimization**

    Community marketing and insurance referrals offer the best ROI.
    Consider reallocating budget from lower-performing channels.
    """)

# System information
st.markdown("---")
st.markdown("""
### 🎯 Dashboard Information
- ✅ **Live Data**: Real-time updates every 30 seconds
- ✅ **Business Alignment**: Metrics aligned with growth strategy ($6M → $30M)
- ✅ **Target Tracking**: 2-min response, 25-35% conversion, premium markets
- ✅ **Actionable Insights**: Optimization opportunities identified automatically

### 📊 Data Sources
- **Backend API**: http://localhost:8001/api/business-metrics/*
- **Database**: Supabase PostgreSQL with connection pooling
- **Cache**: Redis 3-tier caching (30s/5min/1hr TTL)
- **Real-Time**: Pusher WebSocket + SSE streaming
""")
