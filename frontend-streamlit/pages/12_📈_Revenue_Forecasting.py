"""
Revenue Forecasting Dashboard

Train ML models and generate revenue predictions using:
- Prophet (Facebook's time series library)
- ARIMA (statistical forecasting)
- Linear regression with seasonal components
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from utils.auth import require_auth
from utils.api_client import get_api_base_url

# Require authentication
require_auth()

# API base URL
API_BASE = get_api_base_url()

st.title("📈 ML-Powered Revenue Forecasting")
st.markdown("*Train time series models for accurate revenue predictions*")

# Create tabs
tabs = st.tabs(["🧠 Train Model", "🔮 Generate Forecast", "📊 Model Accuracy"])

# ============================================================================
# TAB 1: TRAIN MODEL
# ============================================================================
with tabs[0]:
    st.header("🧠 Train Forecasting Model")
    st.markdown("Train ML models on historical revenue data to enable accurate predictions.")

    col1, col2 = st.columns([2, 1])

    with col2:
        st.subheader("Training Configuration")

        historical_days = st.slider(
            "Historical Data (days)",
            min_value=30,
            max_value=365,
            value=180,
            help="More data = better accuracy (but slower training)"
        )

        model_type = st.selectbox(
            "Model Type",
            options=["auto", "prophet", "arima", "linear"],
            format_func=lambda x: {
                "auto": "Auto-select (Recommended)",
                "prophet": "Prophet (Facebook's time series)",
                "arima": "ARIMA (Statistical)",
                "linear": "Linear Regression"
            }[x],
            help="Auto-select chooses the best model based on data"
        )

        if st.button("Train Model", type="primary", use_container_width=True):
            with st.spinner(f"Training {model_type} model on {historical_days} days of data..."):
                try:
                    response = requests.post(
                        f"{API_BASE}/api/advanced-analytics/ml/revenue/train",
                        json={
                            'historical_days': historical_days,
                            'model_type': model_type
                        }
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.session_state['trained_model'] = result
                        st.success("✅ Model trained successfully!")
                        st.balloons()
                    else:
                        error = response.json().get('error', 'Unknown error')
                        st.error(f"Training failed: {error}")
                except Exception as e:
                    st.error(f"Failed to train model: {str(e)}")

    with col1:
        if 'trained_model' in st.session_state:
            data = st.session_state['trained_model']

            st.success("✅ Model Ready for Predictions")

            # Model info
            col_a, col_b, col_c, col_d = st.columns(4)

            with col_a:
                st.metric("Model Type", data['model_type'].upper())

            with col_b:
                st.metric("Training Days", f"{data['training_days']} days")

            with col_c:
                metrics = data.get('metrics', {})
                mae = metrics.get('mae', 0)
                st.metric("MAE", f"${mae:,.0f}")

            with col_d:
                r_squared = metrics.get('r_squared', 0)
                if r_squared:
                    st.metric("R²", f"{r_squared:.3f}")

            # Training period
            training_period = data.get('training_period', {})
            st.info(f"📅 Training Period: {training_period.get('start_date')} to {training_period.get('end_date')}")

            # Model metrics explanation
            with st.expander("📖 Understanding Model Metrics"):
                st.markdown("""
                **MAE (Mean Absolute Error):** Average prediction error in dollars. Lower is better.

                **R² (R-squared):** How well the model fits the data (0-1). Higher is better.
                - 0.9+ = Excellent fit
                - 0.7-0.9 = Good fit
                - 0.5-0.7 = Moderate fit
                - <0.5 = Poor fit

                **Model Types:**
                - **Prophet:** Best for data with strong seasonal patterns
                - **ARIMA:** Good for statistically stable time series
                - **Linear:** Fast and simple, works for trending data
                """)

        else:
            st.info("👈 Train a model to enable revenue forecasting")

            # Show sample visualization
            st.subheader("Why Train a Model?")
            st.markdown("""
            Machine learning models learn from your historical revenue patterns to:
            - **Predict future revenue** with confidence intervals
            - **Identify trends** and seasonal patterns
            - **Support decision-making** with data-driven forecasts
            - **Plan resources** based on expected demand

            Train a model now to get started! ➡️
            """)

# ============================================================================
# TAB 2: GENERATE FORECAST
# ============================================================================
with tabs[1]:
    st.header("🔮 Generate Revenue Forecast")

    if 'trained_model' not in st.session_state:
        st.warning("⚠️ Please train a model first (see 'Train Model' tab)")
    else:
        col1, col2 = st.columns([3, 1])

        with col2:
            st.subheader("Forecast Configuration")

            days_ahead = st.slider(
                "Forecast Period (days)",
                min_value=7,
                max_value=90,
                value=30,
                help="Number of days to predict into the future"
            )

            include_scenarios = st.checkbox(
                "Include Scenarios",
                value=False,
                help="Add optimistic and pessimistic scenarios"
            )

            if st.button("Generate Forecast", type="primary", use_container_width=True):
                with st.spinner(f"Generating {days_ahead}-day forecast..."):
                    try:
                        response = requests.get(
                            f"{API_BASE}/api/advanced-analytics/ml/revenue/predict",
                            params={
                                'days_ahead': days_ahead,
                                'include_scenarios': include_scenarios
                            }
                        )

                        if response.status_code == 200:
                            result = response.json()
                            st.session_state['forecast'] = result
                            st.success("✅ Forecast generated!")
                        else:
                            error = response.json().get('error', 'Unknown error')
                            st.error(f"Forecast failed: {error}")
                    except Exception as e:
                        st.error(f"Failed to generate forecast: {str(e)}")

        with col1:
            if 'forecast' in st.session_state:
                data = st.session_state['forecast']
                summary = data.get('summary', {})

                # Summary metrics
                col_a, col_b, col_c, col_d = st.columns(4)

                with col_a:
                    total_forecast = summary.get('total_forecast_revenue', 0)
                    st.metric("Total Forecast", f"${total_forecast:,.0f}")

                with col_b:
                    avg_daily = summary.get('average_daily_revenue', 0)
                    st.metric("Avg Daily Revenue", f"${avg_daily:,.0f}")

                with col_c:
                    historical_avg = summary.get('historical_average', 0)
                    st.metric("Historical Avg", f"${historical_avg:,.0f}")

                with col_d:
                    growth_rate = summary.get('projected_growth_rate', 0)
                    st.metric("Projected Growth", f"{growth_rate:+.1f}%")

                # Forecast chart
                forecast_df = pd.DataFrame(data['forecast'])
                forecast_df['date'] = pd.to_datetime(forecast_df['date'])

                fig = go.Figure()

                # Main prediction
                fig.add_trace(go.Scatter(
                    x=forecast_df['date'],
                    y=forecast_df['predicted_revenue'],
                    mode='lines+markers',
                    name='Predicted Revenue',
                    line=dict(color='#1f77b4', width=3),
                    marker=dict(size=6)
                ))

                # Confidence interval
                fig.add_trace(go.Scatter(
                    x=forecast_df['date'].tolist() + forecast_df['date'].tolist()[::-1],
                    y=forecast_df['upper_bound'].tolist() + forecast_df['lower_bound'].tolist()[::-1],
                    fill='toself',
                    fillcolor='rgba(31, 119, 180, 0.2)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name='95% Confidence Interval',
                    showlegend=True
                ))

                # Add scenarios if included
                if include_scenarios and 'optimistic_scenario' in forecast_df.columns:
                    fig.add_trace(go.Scatter(
                        x=forecast_df['date'],
                        y=forecast_df['optimistic_scenario'],
                        mode='lines',
                        name='Optimistic Scenario',
                        line=dict(color='#00cc66', width=2, dash='dash')
                    ))

                    fig.add_trace(go.Scatter(
                        x=forecast_df['date'],
                        y=forecast_df['pessimistic_scenario'],
                        mode='lines',
                        name='Pessimistic Scenario',
                        line=dict(color='#ff6666', width=2, dash='dash')
                    ))

                fig.update_layout(
                    title=f"{days_ahead}-Day Revenue Forecast",
                    xaxis_title="Date",
                    yaxis_title="Revenue ($)",
                    hovermode='x unified',
                    height=500,
                    showlegend=True
                )

                st.plotly_chart(fig, use_container_width=True)

                # Forecast table
                with st.expander("📋 View Forecast Data"):
                    display_cols = ['date', 'predicted_revenue', 'lower_bound', 'upper_bound']
                    if include_scenarios:
                        display_cols.extend(['optimistic_scenario', 'pessimistic_scenario'])

                    st.dataframe(
                        forecast_df[display_cols].style.format({
                            'predicted_revenue': '${:,.0f}',
                            'lower_bound': '${:,.0f}',
                            'upper_bound': '${:,.0f}',
                            'optimistic_scenario': '${:,.0f}',
                            'pessimistic_scenario': '${:,.0f}'
                        }),
                        use_container_width=True,
                        height=400
                    )

                # Download forecast
                csv = forecast_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Forecast (CSV)",
                    data=csv,
                    file_name=f"revenue_forecast_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

            else:
                st.info("👈 Click 'Generate Forecast' to see predictions")

# ============================================================================
# TAB 3: MODEL ACCURACY
# ============================================================================
with tabs[2]:
    st.header("📊 Model Accuracy & Validation")

    if 'trained_model' not in st.session_state:
        st.warning("⚠️ Please train a model first (see 'Train Model' tab)")
    else:
        st.markdown("Evaluate model performance using backtesting on historical data.")

        if st.button("Calculate Accuracy", type="primary"):
            with st.spinner("Running backtesting validation..."):
                try:
                    response = requests.get(
                        f"{API_BASE}/api/advanced-analytics/ml/revenue/accuracy"
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.session_state['accuracy'] = result
                        st.success("✅ Accuracy calculated!")
                    else:
                        error = response.json().get('error', 'Unknown error')
                        st.error(f"Accuracy calculation failed: {error}")
                except Exception as e:
                    st.error(f"Failed to calculate accuracy: {str(e)}")

        if 'accuracy' in st.session_state:
            data = st.session_state['accuracy']
            metrics = data.get('accuracy_metrics', {})

            st.subheader("📈 Accuracy Metrics")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                mae = metrics.get('mae', 0)
                st.metric("MAE", f"${mae:,.0f}", help="Mean Absolute Error")

            with col2:
                mape = metrics.get('mape', 0)
                st.metric("MAPE", f"{mape:.1f}%", help="Mean Absolute Percentage Error")

            with col3:
                rmse = metrics.get('rmse', 0)
                st.metric("RMSE", f"${rmse:,.0f}", help="Root Mean Squared Error")

            with col4:
                r_squared = metrics.get('r_squared', 0)
                st.metric("R²", f"{r_squared:.3f}", help="R-squared coefficient")

            # Accuracy interpretation
            st.subheader("📖 Interpretation")

            # MAPE interpretation
            mape_val = metrics.get('mape', 0)
            if mape_val < 10:
                mape_rating = "🟢 Excellent"
                mape_desc = "High forecast accuracy"
            elif mape_val < 20:
                mape_rating = "🟡 Good"
                mape_desc = "Acceptable forecast accuracy"
            elif mape_val < 30:
                mape_rating = "🟠 Fair"
                mape_desc = "Moderate forecast accuracy"
            else:
                mape_rating = "🔴 Poor"
                mape_desc = "Consider retraining with more data"

            # R² interpretation
            r2_val = metrics.get('r_squared', 0)
            if r2_val >= 0.9:
                r2_rating = "🟢 Excellent fit"
            elif r2_val >= 0.7:
                r2_rating = "🟡 Good fit"
            elif r2_val >= 0.5:
                r2_rating = "🟠 Moderate fit"
            else:
                r2_rating = "🔴 Poor fit"

            col_a, col_b = st.columns(2)

            with col_a:
                st.info(f"""
                **MAPE: {mape_rating}**

                {mape_desc}

                - <10%: Excellent
                - 10-20%: Good
                - 20-30%: Fair
                - >30%: Poor
                """)

            with col_b:
                st.info(f"""
                **R²: {r2_rating}**

                Model explains {r2_val*100:.1f}% of variance

                - 0.9+: Excellent
                - 0.7-0.9: Good
                - 0.5-0.7: Moderate
                - <0.5: Poor
                """)

            # Test period info
            test_days = data.get('test_period_days', 0)
            model_type = data.get('model_type', 'unknown')

            st.markdown(f"**Test Period:** {test_days} days | **Model:** {model_type.upper()}")

            # Recommendations
            st.subheader("💡 Recommendations")

            if mape_val > 20 or r2_val < 0.7:
                st.warning("""
                **Model Performance Could Be Improved:**

                1. **Increase training data:** Use more historical days (180-365)
                2. **Try different model:** Switch between Prophet, ARIMA, or Linear
                3. **Check data quality:** Ensure revenue data is accurate and complete
                4. **Seasonal patterns:** Prophet works best with seasonal data
                """)
            else:
                st.success("""
                **Model Performance is Good!**

                Your model is performing well and can be reliably used for forecasting.
                Continue monitoring accuracy over time and retrain periodically.
                """)

        else:
            st.info("👆 Click 'Calculate Accuracy' to validate model performance")

            # Explanation
            st.markdown("""
            ### What is Backtesting?

            Backtesting validates model accuracy by:

            1. **Splitting data:** Uses last 30 days as test set
            2. **Making predictions:** Model predicts the test period
            3. **Comparing results:** Predictions vs actual revenue
            4. **Calculating metrics:** MAE, MAPE, RMSE, R²

            This ensures the model performs well on unseen data.
            """)

# Footer
st.markdown("---")
st.markdown("*ML models: Prophet (Facebook), ARIMA (statistical), Linear Regression*")
