"""
Enhanced Chart Components for Streamlit Dashboard
Version: 2.0.0
Date: 2025-10-09

Provides business-specific chart components with real-time updates.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st
from typing import Dict, List, Any


def create_kpi_card(
    label: str,
    value: Any,
    delta: float = None,
    delta_label: str = "",
    target: float = None,
    format_func: callable = None,
    color: str = "#667eea",
    icon: str = None
):
    """
    Create an enhanced KPI card with gradient and progress

    Args:
        label: KPI label
        value: KPI value
        delta: Change value
        delta_label: Delta description
        target: Target value for progress bar
        format_func: Function to format value
        color: Primary color
        icon: Optional emoji icon to display
    """
    # Format value
    if format_func:
        display_value = format_func(value)
    else:
        display_value = str(value)

    # Calculate progress if target provided
    progress_html = ""
    if target and isinstance(value, (int, float)):
        progress_pct = min(100, (value / target) * 100)
        progress_html = f'<div style="width: 100%; height: 4px; background-color: rgba(102, 126, 234, 0.2); border-radius: 2px; margin-top: 8px;"><div style="width: {progress_pct}%; height: 100%; background: linear-gradient(90deg, {color} 0%, #764ba2 100%); border-radius: 2px;"></div></div>'

    # Delta display
    delta_html = ""
    if delta is not None or delta_label:
        # Handle both numeric and string deltas
        if isinstance(delta, (int, float)):
            delta_color = "#28a745" if delta >= 0 else "#dc3545"
            delta_icon = "↑" if delta >= 0 else "↓"
            delta_text = delta_label if delta_label else str(delta)
        elif isinstance(delta, str):
            # For string deltas, use the delta value itself
            delta_color = "#6c757d"
            delta_icon = ""
            delta_text = delta
        else:
            # Just delta_label provided
            delta_color = "#6c757d"
            delta_icon = ""
            delta_text = delta_label

        delta_html = f'<div style="color: {delta_color}; font-size: 14px; font-weight: 600; margin-top: 4px;">{delta_icon} {delta_text}</div>'

    # Icon display
    icon_html = ""
    if icon:
        icon_html = f'<div style="font-size: 24px; opacity: 0.9; margin-bottom: 8px;">{icon}</div>'

    # Build complete HTML
    card_html = f'''
    <div style="background: linear-gradient(135deg, {color} 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
        {icon_html}
        <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">{label}</div>
        <div style="font-size: 32px; font-weight: bold; margin-bottom: 4px;">{display_value}</div>
        {delta_html}
        {progress_html}
    </div>
    '''

    # Render card
    st.markdown(card_html, unsafe_allow_html=True)


def create_conversion_funnel(data: Dict[str, int], target_rate: float = 25.0):
    """
    Create conversion funnel chart

    Args:
        data: Dictionary of stage -> count
        target_rate: Target conversion rate percentage
    """
    if not data:
        st.warning("No funnel data available")
        return

    stages = list(data.keys())
    values = list(data.values())

    # Calculate conversion rates
    conversion_rates = []
    for i in range(len(values) - 1):
        rate = (values[i+1] / values[i] * 100) if values[i] > 0 else 0
        conversion_rates.append(rate)

    fig = go.Figure(go.Funnel(
        y=stages,
        x=values,
        textposition="inside",
        textinfo="value+percent initial",
        marker={
            "color": ["#667eea", "#764ba2", "#f093fb", "#4facfe", "#00f2fe"],
            "line": {"width": 2, "color": "white"}
        }
    ))

    fig.update_layout(
        title="Lead Conversion Funnel",
        height=400,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # Show conversion rates
    st.markdown("#### Stage-to-Stage Conversion")
    for i, rate in enumerate(conversion_rates):
        status = "🟢" if rate >= target_rate else "🟡" if rate >= (target_rate * 0.7) else "🔴"
        st.write(f"{status} {stages[i]} → {stages[i+1]}: **{rate:.1f}%**")


def create_geographic_heatmap(data: List[Dict[str, Any]]):
    """
    Create geographic distribution heatmap

    Args:
        data: List of geographic data points with city, count, revenue
    """
    if not data:
        st.warning("No geographic data available")
        return

    df = pd.DataFrame(data)

    fig = px.scatter_geo(
        df,
        lat="lat" if "lat" in df.columns else None,
        lon="lon" if "lon" in df.columns else None,
        size="revenue" if "revenue" in df.columns else "count",
        color="tier" if "tier" in df.columns else None,
        hover_name="city",
        hover_data={"revenue": ":$,.0f", "count": True},
        title="Premium Market Distribution"
    )

    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)


def create_response_time_gauge(
    avg_time: float,
    target: float = 120,
    title: str = "Avg Lead Response Time"
):
    """
    Create gauge chart for response time (2-minute target)

    Args:
        avg_time: Average response time in seconds
        target: Target time in seconds
        title: Chart title
    """
    # Determine color based on performance
    if avg_time <= target:
        color = "#28a745"  # Green
    elif avg_time <= target * 1.5:
        color = "#ffc107"  # Yellow
    else:
        color = "#dc3545"  # Red

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=avg_time,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 20}},
        delta={'reference': target, 'suffix': 's'},
        number={'suffix': 's'},
        gauge={
            'axis': {'range': [None, target * 2], 'ticksuffix': 's'},
            'bar': {'color': color},
            'steps': [
                {'range': [0, target], 'color': 'rgba(40, 167, 69, 0.2)'},
                {'range': [target, target * 1.5], 'color': 'rgba(255, 193, 7, 0.2)'},
                {'range': [target * 1.5, target * 2], 'color': 'rgba(220, 53, 69, 0.2)'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': target
            }
        }
    ))

    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)


def create_marketing_roi_chart(channels: Dict[str, Dict[str, Any]]):
    """
    Create marketing channel ROI comparison chart

    Args:
        channels: Dictionary of channel -> metrics
    """
    if not channels:
        st.warning("No marketing data available")
        return

    df = pd.DataFrame.from_dict(channels, orient='index')
    df['channel'] = df.index

    # Create subplot with 2 charts
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Leads Generated by Channel', 'ROI % by Channel'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}]]
    )

    # Leads chart
    fig.add_trace(
        go.Bar(
            x=df['channel'],
            y=df['leads_generated'],
            name='Leads',
            marker_color='#667eea',
            text=df['leads_generated'],
            textposition='outside'
        ),
        row=1, col=1
    )

    # ROI chart with color based on profitability
    colors = ['#28a745' if roi > 0 else '#dc3545' for roi in df['roi_percent']]

    fig.add_trace(
        go.Bar(
            x=df['channel'],
            y=df['roi_percent'],
            name='ROI %',
            marker_color=colors,
            text=[f"{roi:.0f}%" for roi in df['roi_percent']],
            textposition='outside'
        ),
        row=1, col=2
    )

    fig.update_layout(
        height=400,
        showlegend=False,
        title_text="Marketing Channel Performance"
    )

    fig.update_xaxes(tickangle=45)

    st.plotly_chart(fig, use_container_width=True)


def create_revenue_progress_chart(
    current: float,
    target_year1: float,
    target_year2: float,
    target_year3: float,
    title: str = "Revenue Growth Path"
):
    """
    Create revenue growth progress chart ($6M → $30M)

    Args:
        current: Current monthly revenue
        target_year1: Year 1 target ($8M annually = $667K/month)
        target_year2: Year 2 target ($18M annually = $1.5M/month)
        target_year3: Year 3 target ($30M annually = $2.5M/month)
        title: Chart title
    """
    categories = ['Current', 'Year 1 Target', 'Year 2 Target', 'Year 3 Target']
    values = [current, target_year1, target_year2, target_year3]

    # Determine which stage we're at
    current_stage_index = 0
    if current >= target_year1:
        current_stage_index = 1
    if current >= target_year2:
        current_stage_index = 2
    if current >= target_year3:
        current_stage_index = 3

    colors = [
        '#28a745' if i <= current_stage_index else '#e9ecef'
        for i in range(len(categories))
    ]

    fig = go.Figure(data=[
        go.Bar(
            x=categories,
            y=values,
            marker_color=colors,
            text=[f"${v/1000:.0f}K" for v in values],
            textposition='outside'
        )
    ])

    fig.update_layout(
        title=title,
        yaxis_title="Monthly Revenue",
        height=400,
        showlegend=False
    )

    fig.update_yaxis(tickformat='$,.0f')

    st.plotly_chart(fig, use_container_width=True)


def create_conversion_by_temperature(data: Dict[str, Dict[str, Any]]):
    """
    Create conversion rate by lead temperature chart

    Args:
        data: Dictionary of temperature -> metrics
    """
    if not data:
        st.warning("No temperature data available")
        return

    temperatures = list(data.keys())
    rates = [data[temp].get('rate', 0) for temp in temperatures]
    totals = [data[temp].get('total', 0) for temp in temperatures]

    colors = {
        'hot': '#dc3545',
        'warm': '#ffc107',
        'cold': '#17a2b8'
    }

    fig = go.Figure()

    for i, temp in enumerate(temperatures):
        fig.add_trace(go.Bar(
            name=temp.capitalize(),
            x=[temp],
            y=[rates[i]],
            marker_color=colors.get(temp, '#6c757d'),
            text=f"{rates[i]:.1f}%<br>{totals[i]} leads",
            textposition='outside'
        ))

    fig.update_layout(
        title="Conversion Rate by Lead Temperature",
        yaxis_title="Conversion Rate (%)",
        height=400,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)


def create_timeline_chart(events: List[Dict[str, Any]]):
    """
    Create timeline chart for project milestones

    Args:
        events: List of events with date, title, type
    """
    if not events:
        st.warning("No timeline data available")
        return

    df = pd.DataFrame(events)

    fig = px.timeline(
        df,
        x_start="start_date",
        x_end="end_date",
        y="project_name",
        color="status",
        hover_data=["value"],
        title="Project Timeline"
    )

    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
