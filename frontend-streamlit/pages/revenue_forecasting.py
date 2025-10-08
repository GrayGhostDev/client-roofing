"""
Revenue Forecasting Page
Predict future revenue and analyze financial trends
"""

import streamlit as st
import pandas as pd
import numpy as np
from utils.visualization import (
    create_kpi_cards,
    create_line_chart,
    create_bar_chart,
    format_currency,
    export_to_csv,
    export_to_excel
)


def render():
    """Render the revenue forecasting page"""
    st.title("💰 Revenue Forecasting")
    st.markdown("Predict future revenue and analyze financial performance trends")
    
    start_date, end_date = st.session_state.date_range
    
    # Forecast settings
    col1, col2, col3 = st.columns(3)
    
    with col1:
        forecast_period = st.selectbox(
            "Forecast Period",
            ["Next 30 Days", "Next Quarter", "Next 6 Months", "Next Year"]
        )
    
    with col2:
        confidence_level = st.slider(
            "Confidence Level",
            min_value=80,
            max_value=99,
            value=95,
            format="%d%%"
        )
    
    with col3:
        model_type = st.selectbox(
            "Forecasting Model",
            ["Linear Regression", "Moving Average", "Exponential Smoothing"]
        )
    
    st.divider()
    
    # Revenue KPIs
    st.subheader("📊 Revenue Metrics")
    
    revenue_kpis = [
        {'label': 'Current Revenue', 'value': format_currency(850000), 'delta': format_currency(120000)},
        {'label': 'Forecasted Revenue', 'value': format_currency(1100000), 'delta': '+29%'},
        {'label': 'Pipeline Value', 'value': format_currency(450000), 'delta': format_currency(65000)},
        {'label': 'Avg Deal Size', 'value': format_currency(25000), 'delta': format_currency(2500)}
    ]
    
    create_kpi_cards(revenue_kpis)
    
    st.divider()
    
    # Revenue forecast chart
    st.subheader("📈 Revenue Forecast")
    
    # Generate forecast data
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    future_dates = pd.date_range(start=end_date, periods=30, freq='D')
    all_dates = date_range.union(future_dates)
    
    # Historical data
    historical_revenue = [15000 + (i * 500) + np.random.randint(-2000, 3000) for i in range(len(date_range))]
    
    # Forecast data
    base_forecast = historical_revenue[-1]
    forecast_revenue = [base_forecast + (i * 600) + np.random.randint(-1000, 2000) for i in range(len(future_dates))]
    
    # Combine data
    revenue_data = pd.DataFrame({
        'date': list(date_range) + list(future_dates),
        'revenue': historical_revenue + forecast_revenue,
        'type': ['Actual'] * len(date_range) + ['Forecast'] * len(future_dates)
    })
    
    fig = create_line_chart(
        data=revenue_data,
        x='date',
        y='revenue',
        title=f"Revenue Forecast ({forecast_period})",
        color='type'
    )
    st.plotly_chart(fig)
    
    # Confidence intervals
    with st.expander("📊 Confidence Intervals"):
        st.info(f"**{confidence_level}% Confidence Interval**")
        st.write(f"- Lower Bound: {format_currency(sum(forecast_revenue) * 0.85)}")
        st.write(f"- Expected Value: {format_currency(sum(forecast_revenue))}")
        st.write(f"- Upper Bound: {format_currency(sum(forecast_revenue) * 1.15)}")
    
    st.divider()
    
    # Revenue breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💵 Revenue by Category")
        
        category_data = pd.DataFrame([
            {'category': 'New Customers', 'revenue': 350000},
            {'category': 'Existing Customers', 'revenue': 280000},
            {'category': 'Upsells', 'revenue': 150000},
            {'category': 'Renewals', 'revenue': 70000}
        ])
        
        fig = create_bar_chart(
            data=category_data,
            x='category',
            y='revenue',
            title="Revenue Breakdown",
            color='category'
        )
        st.plotly_chart(fig)
    
    with col2:
        st.subheader("📊 Monthly Comparison")
        
        monthly_data = pd.DataFrame([
            {'month': 'Jul', 'revenue': 245000},
            {'month': 'Aug', 'revenue': 280000},
            {'month': 'Sep', 'revenue': 325000},
            {'month': 'Oct', 'revenue': 365000, 'type': 'Forecast'}
        ])
        
        fig = create_bar_chart(
            data=monthly_data,
            x='month',
            y='revenue',
            title="Monthly Revenue Trend",
            color='month'
        )
        st.plotly_chart(fig)
    
    st.divider()
    
    # Key insights
    st.subheader("💡 Financial Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.success("**Growth Trend**\nRevenue increasing at 12% monthly rate")
    
    with col2:
        st.info("**Top Category**\nNew customer acquisition driving 41% of revenue")
    
    with col3:
        st.warning("**Opportunity**\nFocus on upsells for 20% revenue boost")
    
    # Scenario analysis
    st.divider()
    st.subheader("🎯 Scenario Analysis")
    
    scenario_data = pd.DataFrame([
        {
            'scenario': 'Conservative',
            'probability': '30%',
            'revenue': format_currency(950000),
            'growth': '+12%'
        },
        {
            'scenario': 'Expected',
            'probability': '50%',
            'revenue': format_currency(1100000),
            'growth': '+29%'
        },
        {
            'scenario': 'Optimistic',
            'probability': '20%',
            'revenue': format_currency(1300000),
            'growth': '+53%'
        }
    ])
    
    st.dataframe(
        scenario_data,
        ,
        hide_index=True
    )
    
    # Export options
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        export_to_csv(revenue_data, "revenue_forecast")
    
    with col2:
        export_to_excel(revenue_data, "revenue_forecast")
    
    with col3:
        if st.button("🔄 Regenerate Forecast"):
            st.cache_data.clear()
            st.rerun()
