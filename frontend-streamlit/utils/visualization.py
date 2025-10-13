"""
Data Processing and Visualization Helpers
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import streamlit as st


def calculate_percentage_change(current: float, previous: float) -> float:
    """Calculate percentage change between two values"""
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100


def format_currency(amount: float) -> str:
    """Format number as currency"""
    return f"${amount:,.2f}"


def format_percentage(value: float) -> str:
    """Format number as percentage"""
    return f"{value:.1f}%"


def create_metric_card(
    label: str,
    value: Any,
    delta: Optional[float] = None,
    delta_color: str = "normal"
) -> None:
    """
    Create a styled metric card
    
    Args:
        label: Metric label
        value: Metric value
        delta: Change value (optional)
        delta_color: Color for delta (normal, inverse, off)
    """
    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color
    )


def create_kpi_cards(metrics: List[Dict[str, Any]]) -> None:
    """
    Create a row of KPI cards
    
    Args:
        metrics: List of metric dictionaries with keys: label, value, delta
    """
    cols = st.columns(len(metrics))
    for idx, metric in enumerate(metrics):
        with cols[idx]:
            create_metric_card(
                label=metric.get('label', ''),
                value=metric.get('value', 0),
                delta=metric.get('delta'),
                delta_color=metric.get('delta_color', 'normal')
            )


def create_line_chart(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: Optional[str] = None
) -> go.Figure:
    """Create a line chart"""
    fig = px.line(
        data,
        x=x,
        y=y,
        title=title,
        color=color,
        markers=True
    )
    
    fig.update_layout(
        hovermode='x unified',
        showlegend=True,
        height=400
    )
    
    return fig


def create_bar_chart(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: Optional[str] = None,
    orientation: str = 'v'
) -> go.Figure:
    """Create a bar chart"""
    fig = px.bar(
        data,
        x=x,
        y=y,
        title=title,
        color=color,
        orientation=orientation
    )
    
    fig.update_layout(
        hovermode='x unified',
        showlegend=True,
        height=400
    )
    
    return fig


def create_pie_chart(
    data: pd.DataFrame,
    values: str,
    names: str,
    title: str
) -> go.Figure:
    """Create a pie chart"""
    fig = px.pie(
        data,
        values=values,
        names=names,
        title=title,
        hole=0.4  # Donut chart
    )
    
    fig.update_layout(
        showlegend=True,
        height=400
    )
    
    return fig


def create_funnel_chart(
    stages: List[str],
    values: List[int],
    title: str
) -> go.Figure:
    """Create a funnel chart"""
    fig = go.Figure(go.Funnel(
        y=stages,
        x=values,
        textinfo="value+percent initial"
    ))
    
    fig.update_layout(
        title=title,
        height=400
    )
    
    return fig


def create_gauge_chart(
    value: float,
    title: str,
    max_value: float = 100,
    thresholds: Optional[Dict[str, float]] = None
) -> go.Figure:
    """
    Create a gauge chart
    
    Args:
        value: Current value
        title: Chart title
        max_value: Maximum value for gauge
        thresholds: Dict with 'low', 'medium', 'high' thresholds
    """
    if thresholds is None:
        thresholds = {'low': 33, 'medium': 66, 'high': 100}
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title={'text': title},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [None, max_value]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, thresholds['low']], 'color': "lightgray"},
                {'range': [thresholds['low'], thresholds['medium']], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': thresholds['high']
            }
        }
    ))
    
    fig.update_layout(height=300)
    
    return fig


def create_heatmap(
    data: pd.DataFrame,
    x: str,
    y: str,
    z: str,
    title: str
) -> go.Figure:
    """Create a heatmap"""
    pivot_table = data.pivot_table(values=z, index=y, columns=x, aggfunc='sum')
    
    fig = px.imshow(
        pivot_table,
        title=title,
        aspect="auto",
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(height=400)
    
    return fig


def export_to_csv(data: pd.DataFrame, filename: str) -> None:
    """Export DataFrame to CSV with download button"""
    csv = data.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


def export_to_excel(data: pd.DataFrame, filename: str) -> None:
    """Export DataFrame to Excel with download button"""
    from io import BytesIO
    
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        data.to_excel(writer, index=False, sheet_name='Data')
    
    st.download_button(
        label="📥 Download Excel",
        data=buffer.getvalue(),
        file_name=f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def generate_date_range(start_date: datetime, end_date: datetime) -> pd.DatetimeIndex:
    """Generate date range for time series"""
    return pd.date_range(start=start_date, end=end_date, freq='D')


def aggregate_by_period(
    data: pd.DataFrame,
    date_column: str,
    value_column: str,
    period: str = 'D'
) -> pd.DataFrame:
    """
    Aggregate data by time period
    
    Args:
        data: DataFrame with data
        date_column: Name of date column
        value_column: Name of value column to aggregate
        period: Period to aggregate by ('D'=day, 'W'=week, 'M'=month)
        
    Returns:
        Aggregated DataFrame
    """
    data[date_column] = pd.to_datetime(data[date_column])
    data.set_index(date_column, inplace=True)
    
    aggregated = data[value_column].resample(period).sum().reset_index()
    
    return aggregated


def calculate_trend(data: pd.Series) -> str:
    """
    Calculate trend direction from series
    
    Returns:
        'up', 'down', or 'stable'
    """
    if len(data) < 2:
        return 'stable'
    
    first_half = data[:len(data)//2].mean()
    second_half = data[len(data)//2:].mean()
    
    change = ((second_half - first_half) / first_half) * 100 if first_half != 0 else 0
    
    if change > 5:
        return 'up'
    elif change < -5:
        return 'down'
    else:
        return 'stable'


def get_trend_emoji(trend: str) -> str:
    """Get emoji for trend direction"""
    return {
        'up': '📈',
        'down': '📉',
        'stable': '➡️'
    }.get(trend, '➡️')


def create_comparison_table(
    data: List[Dict[str, Any]],
    columns: List[str]
) -> pd.DataFrame:
    """Create a formatted comparison table"""
    df = pd.DataFrame(data)
    
    if not df.empty and columns:
        df = df[columns]
    
    return df


def show_loading_message(message: str = "Loading data...") -> None:
    """Display loading message"""
    with st.spinner(message):
        pass


@st.cache_data(ttl=300)  # Cache for 5 minutes
def cached_api_call(func, *args, **kwargs):
    """Cache API calls for better performance"""
    return func(*args, **kwargs)
