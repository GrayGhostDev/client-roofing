# Phase 3 Implementation Plan: Streamlit Analytics Dashboard

## Executive Summary

Phase 3 focuses on developing a comprehensive executive-level analytics dashboard using Streamlit framework. This dashboard will provide advanced business intelligence, data visualization, and reporting capabilities specifically designed for executive decision-making and strategic planning.

**Objective:** Build an executive-focused analytics platform that transforms CRM data into actionable business insights
**Duration:** 1 week (Week 7)
**Technology:** Streamlit with advanced visualization libraries
**Target Users:** Executives, managers, and business analysts

## Technology Stack

### Core Framework
- **Streamlit 1.29.0** - Primary dashboard framework
- **Python 3.11+** - Development language
- **Plotly 5.17.0** - Interactive charting library
- **Altair 5.2.0** - Statistical visualizations
- **Pandas 2.1.0** - Data manipulation and analysis
- **NumPy 1.25.0** - Numerical computations

### Visualization Libraries
- **Plotly Express** - Quick statistical charts
- **Plotly Graph Objects** - Custom interactive visualizations
- **Folium 0.15.0** - Geographic mapping
- **Seaborn 0.13.0** - Statistical data visualization
- **Matplotlib 3.8.0** - Base plotting functionality

### Data Processing
- **SQLAlchemy 2.0** - Database connections
- **httpx** - API client for backend communication
- **streamlit-authenticator** - Authentication system
- **streamlit-option-menu** - Advanced navigation

## Project Structure

```
frontend-streamlit/
├── app.py                     # Main Streamlit application
├── requirements.txt           # Python dependencies
├── .streamlit/
│   └── config.toml           # Streamlit configuration
├── pages/
│   ├── 1_📊_overview.py      # Executive overview dashboard
│   ├── 2_🎯_leads_analytics.py  # Lead analytics deep dive
│   ├── 3_💰_revenue.py       # Revenue analysis and forecasting
│   ├── 4_👥_team_performance.py # Team performance analytics
│   ├── 5_🗺️_geographic.py   # Geographic analysis
│   └── 6_📈_marketing_roi.py # Marketing ROI analysis
├── components/
│   ├── __init__.py
│   ├── charts.py             # Reusable chart components
│   ├── filters.py            # Dashboard filters
│   ├── metrics.py            # KPI calculation functions
│   └── maps.py               # Geographic visualization components
├── utils/
│   ├── __init__.py
│   ├── api_client.py         # Backend API integration
│   ├── data_processor.py     # Data transformation utilities
│   ├── export.py             # Export functionality
│   └── cache.py              # Caching utilities
├── assets/
│   ├── logo.png              # Company branding
│   ├── styles.css            # Custom CSS styling
│   └── favicon.ico           # Browser favicon
└── tests/
    ├── test_components.py    # Component testing
    ├── test_data.py          # Data processing tests
    └── test_api.py           # API integration tests
```

## Implementation Roadmap

### Day 1: Project Setup and Foundation

#### Morning (4 hours): Environment Setup
```bash
# Create Streamlit project structure
mkdir frontend-streamlit
cd frontend-streamlit

# Initialize virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install streamlit plotly altair pandas folium streamlit-authenticator
pip install httpx sqlalchemy streamlit-option-menu seaborn

# Create project structure
mkdir -p pages components utils assets tests .streamlit
```

#### Configuration Files

**requirements.txt**
```txt
streamlit==1.29.0
plotly==5.17.0
altair==5.2.0
pandas==2.1.0
numpy==1.25.0
folium==0.15.0
streamlit-authenticator==0.2.3
streamlit-option-menu==0.3.6
httpx==0.25.0
sqlalchemy==2.0.23
seaborn==0.13.0
matplotlib==3.8.0
python-dotenv==1.0.0
```

**.streamlit/config.toml**
```toml
[global]
dataFrameSerialization = "legacy"

[server]
runOnSave = true
port = 8501
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

#### Afternoon (4 hours): Core Infrastructure

**Main Application (app.py)**
```python
import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from utils.api_client import CRMAPIClient
from utils.cache import get_cached_data

# Page configuration
st.set_page_config(
    page_title="iSwitch Roofs Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
with open('assets/styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def main():
    """Main application entry point"""
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_dashboard()

def show_login_page():
    """Display login interface"""
    st.title("🏠 iSwitch Roofs Analytics Dashboard")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Login Required")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login", type="primary"):
            if authenticate_user(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials")

def show_dashboard():
    """Display main dashboard"""
    st.title("📊 Executive Analytics Dashboard")
    st.markdown(f"Welcome back, **{st.session_state.username}**")

    # Sidebar navigation will be handled by Streamlit's native page system
    st.sidebar.title("Navigation")
    st.sidebar.markdown("Use the sidebar to navigate between different analytics views.")

    # Quick metrics overview
    display_quick_metrics()

def display_quick_metrics():
    """Display key metrics overview"""
    # Load data from API
    metrics = get_cached_data("dashboard_metrics", fetch_dashboard_metrics)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Revenue",
            value=f"${metrics['total_revenue']:,.0f}",
            delta=f"${metrics['revenue_change']:,.0f}"
        )

    with col2:
        st.metric(
            label="Active Projects",
            value=metrics['active_projects'],
            delta=metrics['projects_change']
        )

    with col3:
        st.metric(
            label="Conversion Rate",
            value=f"{metrics['conversion_rate']:.1f}%",
            delta=f"{metrics['conversion_change']:+.1f}%"
        )

    with col4:
        st.metric(
            label="Pipeline Value",
            value=f"${metrics['pipeline_value']:,.0f}",
            delta=f"${metrics['pipeline_change']:,.0f}"
        )

def authenticate_user(username: str, password: str) -> bool:
    """Authenticate user against backend"""
    # Implementation would verify credentials with backend API
    return username == "admin" and password == "password"  # Simplified for demo

def fetch_dashboard_metrics():
    """Fetch dashboard metrics from backend API"""
    client = CRMAPIClient()
    return client.get_dashboard_metrics()

if __name__ == "__main__":
    main()
```

### Day 2: Executive Overview Dashboard

#### Page 1: Executive Overview (pages/1_📊_overview.py)

```python
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from utils.api_client import CRMAPIClient
from utils.cache import get_cached_data
from components.charts import revenue_trend_chart, funnel_chart
from components.filters import date_range_filter

st.set_page_config(page_title="Executive Overview", page_icon="📊", layout="wide")

def main():
    st.title("📊 Executive Overview Dashboard")
    st.markdown("**Real-time business performance insights for strategic decision making**")

    # Date range filter
    date_range = date_range_filter()

    # Load data
    data = load_overview_data(date_range)

    # Key Performance Indicators
    display_kpi_section(data)

    # Revenue Performance
    col1, col2 = st.columns([2, 1])
    with col1:
        display_revenue_trend(data)
    with col2:
        display_revenue_breakdown(data)

    # Sales Performance
    col1, col2 = st.columns(2)
    with col1:
        display_conversion_funnel(data)
    with col2:
        display_lead_sources(data)

    # Team Performance Summary
    display_team_summary(data)

    # Executive Alerts
    display_executive_alerts(data)

def display_kpi_section(data):
    """Display executive KPIs"""
    st.subheader("📈 Key Performance Indicators")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Monthly Revenue",
            f"${data['monthly_revenue']:,.0f}",
            f"{data['revenue_growth']:+.1f}%"
        )

    with col2:
        st.metric(
            "Projects Completed",
            data['completed_projects'],
            f"{data['completion_rate']:+.1f}%"
        )

    with col3:
        st.metric(
            "Lead Conversion",
            f"{data['conversion_rate']:.1f}%",
            f"{data['conversion_change']:+.1f}%"
        )

    with col4:
        st.metric(
            "Avg Project Value",
            f"${data['avg_project_value']:,.0f}",
            f"{data['value_change']:+.1f}%"
        )

    with col5:
        st.metric(
            "Customer Satisfaction",
            f"{data['satisfaction_score']:.1f}/5.0",
            f"{data['satisfaction_change']:+.1f}"
        )

def display_revenue_trend(data):
    """Display revenue trend chart"""
    st.subheader("💰 Revenue Trend")

    fig = revenue_trend_chart(data['revenue_by_month'])
    st.plotly_chart(fig, use_container_width=True)

def display_conversion_funnel(data):
    """Display sales conversion funnel"""
    st.subheader("🎯 Sales Conversion Funnel")

    fig = funnel_chart(data['funnel_data'])
    st.plotly_chart(fig, use_container_width=True)

def load_overview_data(date_range):
    """Load all overview data"""
    return get_cached_data("overview_data", lambda: fetch_overview_data(date_range))

def fetch_overview_data(date_range):
    """Fetch overview data from API"""
    client = CRMAPIClient()
    return {
        'monthly_revenue': 245000,
        'revenue_growth': 12.5,
        'completed_projects': 18,
        'completion_rate': 8.2,
        'conversion_rate': 28.5,
        'conversion_change': 3.2,
        'avg_project_value': 13600,
        'value_change': 5.8,
        'satisfaction_score': 4.6,
        'satisfaction_change': 0.2,
        'revenue_by_month': client.get_revenue_trend(date_range),
        'funnel_data': client.get_conversion_funnel(date_range),
        'lead_sources': client.get_lead_sources(date_range),
        'team_performance': client.get_team_summary(date_range),
        'alerts': client.get_executive_alerts()
    }

if __name__ == "__main__":
    main()
```

### Day 3: Leads Analytics Deep Dive

#### Page 2: Leads Analytics (pages/2_🎯_leads_analytics.py)

```python
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.api_client import CRMAPIClient
from components.charts import lead_score_distribution, source_performance
from components.filters import lead_filter_sidebar

st.set_page_config(page_title="Lead Analytics", page_icon="🎯", layout="wide")

def main():
    st.title("🎯 Lead Analytics Deep Dive")
    st.markdown("**Comprehensive analysis of lead generation, qualification, and conversion**")

    # Sidebar filters
    filters = lead_filter_sidebar()

    # Load lead data
    data = load_lead_analytics(filters)

    # Lead Volume Analysis
    col1, col2 = st.columns([3, 1])
    with col1:
        display_lead_volume_trend(data)
    with col2:
        display_lead_summary_stats(data)

    # Lead Quality Analysis
    st.subheader("📊 Lead Quality Analysis")
    col1, col2 = st.columns(2)
    with col1:
        display_score_distribution(data)
    with col2:
        display_temperature_analysis(data)

    # Source Performance
    col1, col2 = st.columns(2)
    with col1:
        display_source_performance(data)
    with col2:
        display_source_roi(data)

    # Conversion Analysis
    display_conversion_analysis(data)

    # Lead Response Time Analysis
    display_response_time_analysis(data)

def display_lead_volume_trend(data):
    """Display lead volume over time"""
    st.subheader("📈 Lead Volume Trend")

    df = pd.DataFrame(data['volume_by_date'])

    fig = px.line(
        df, x='date', y='count',
        title="Daily Lead Volume",
        labels={'count': 'Number of Leads', 'date': 'Date'}
    )
    fig.update_traces(line_color='#1f77b4', line_width=3)
    st.plotly_chart(fig, use_container_width=True)

def display_score_distribution(data):
    """Display lead score distribution"""
    st.subheader("🎯 Lead Score Distribution")

    fig = lead_score_distribution(data['score_distribution'])
    st.plotly_chart(fig, use_container_width=True)

def display_source_performance(data):
    """Display lead source performance"""
    st.subheader("📊 Source Performance")

    df = pd.DataFrame(data['source_performance'])

    fig = px.bar(
        df, x='source', y='conversion_rate',
        title="Conversion Rate by Source",
        color='conversion_rate',
        color_continuous_scale='viridis'
    )
    st.plotly_chart(fig, use_container_width=True)

def display_conversion_analysis(data):
    """Display detailed conversion analysis"""
    st.subheader("🔄 Conversion Analysis")

    # Time to conversion analysis
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Avg Time to Conversion",
            f"{data['avg_conversion_days']:.1f} days",
            f"{data['conversion_time_change']:+.1f} days"
        )

    with col2:
        st.metric(
            "Fastest Conversion",
            f"{data['fastest_conversion']} hours",
            "This month"
        )

    with col3:
        st.metric(
            "Conversion Velocity",
            f"{data['conversion_velocity']:.1f}%",
            f"{data['velocity_change']:+.1f}%"
        )

    # Conversion stages breakdown
    stages_df = pd.DataFrame(data['conversion_stages'])
    fig = px.funnel(
        stages_df, x='count', y='stage',
        title="Lead Progression Through Sales Stages"
    )
    st.plotly_chart(fig, use_container_width=True)

def load_lead_analytics(filters):
    """Load lead analytics data"""
    client = CRMAPIClient()
    return client.get_lead_analytics(filters)

if __name__ == "__main__":
    main()
```

### Day 4: Revenue Analytics and Forecasting

#### Page 3: Revenue Analytics (pages/3_💰_revenue.py)

```python
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.api_client import CRMAPIClient
from components.charts import revenue_forecast_chart, project_value_distribution

st.set_page_config(page_title="Revenue Analytics", page_icon="💰", layout="wide")

def main():
    st.title("💰 Revenue Analytics & Forecasting")
    st.markdown("**Comprehensive revenue analysis with predictive forecasting**")

    # Load revenue data
    data = load_revenue_data()

    # Revenue Overview
    display_revenue_overview(data)

    # Revenue Forecasting
    col1, col2 = st.columns([2, 1])
    with col1:
        display_revenue_forecast(data)
    with col2:
        display_forecast_confidence(data)

    # Revenue Breakdown Analysis
    col1, col2 = st.columns(2)
    with col1:
        display_revenue_by_type(data)
    with col2:
        display_revenue_by_region(data)

    # Project Value Analysis
    display_project_value_analysis(data)

    # Profitability Analysis
    display_profitability_analysis(data)

    # Pipeline Analysis
    display_pipeline_analysis(data)

def display_revenue_overview(data):
    """Display revenue overview metrics"""
    st.subheader("📊 Revenue Overview")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "YTD Revenue",
            f"${data['ytd_revenue']:,.0f}",
            f"{data['ytd_growth']:+.1f}%"
        )

    with col2:
        st.metric(
            "Monthly Recurring",
            f"${data['monthly_recurring']:,.0f}",
            f"{data['recurring_change']:+.1f}%"
        )

    with col3:
        st.metric(
            "Avg Deal Size",
            f"${data['avg_deal_size']:,.0f}",
            f"{data['deal_size_change']:+.1f}%"
        )

    with col4:
        st.metric(
            "Win Rate",
            f"{data['win_rate']:.1f}%",
            f"{data['win_rate_change']:+.1f}%"
        )

    with col5:
        st.metric(
            "Pipeline Value",
            f"${data['pipeline_value']:,.0f}",
            f"{data['pipeline_change']:+.1f}%"
        )

def display_revenue_forecast(data):
    """Display revenue forecasting chart"""
    st.subheader("🔮 Revenue Forecast")

    # Create forecast visualization
    fig = revenue_forecast_chart(data['historical_revenue'], data['forecast_data'])
    st.plotly_chart(fig, use_container_width=True)

    # Forecast insights
    st.info(f"""
    **Forecast Insights:**
    - Projected Q1 revenue: ${data['q1_forecast']:,.0f}
    - Expected growth rate: {data['growth_rate']:.1f}%
    - Confidence level: {data['confidence_level']:.0f}%
    """)

def display_revenue_by_type(data):
    """Display revenue breakdown by project type"""
    st.subheader("🏗️ Revenue by Project Type")

    df = pd.DataFrame(data['revenue_by_type'])

    fig = px.pie(
        df, values='revenue', names='project_type',
        title="Revenue Distribution by Project Type"
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

def display_profitability_analysis(data):
    """Display profitability analysis"""
    st.subheader("💹 Profitability Analysis")

    # Profit margins by project type
    df = pd.DataFrame(data['profitability_by_type'])

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Revenue',
        x=df['project_type'],
        y=df['revenue'],
        yaxis='y'
    ))
    fig.add_trace(go.Scatter(
        name='Profit Margin %',
        x=df['project_type'],
        y=df['profit_margin'],
        yaxis='y2',
        mode='lines+markers',
        line=dict(color='red', width=3)
    ))

    fig.update_layout(
        title='Revenue vs Profit Margin by Project Type',
        xaxis_title='Project Type',
        yaxis=dict(title='Revenue ($)', side='left'),
        yaxis2=dict(title='Profit Margin (%)', side='right', overlaying='y'),
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)

def load_revenue_data():
    """Load revenue analytics data"""
    client = CRMAPIClient()
    return client.get_revenue_analytics()

if __name__ == "__main__":
    main()
```

### Day 5: Team Performance and Geographic Analysis

#### Page 4: Team Performance (pages/4_👥_team_performance.py)

```python
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.api_client import CRMAPIClient

st.set_page_config(page_title="Team Performance", page_icon="👥", layout="wide")

def main():
    st.title("👥 Team Performance Analytics")
    st.markdown("**Individual and team performance insights for optimization**")

    # Load team data
    data = load_team_data()

    # Team Overview
    display_team_overview(data)

    # Individual Performance
    col1, col2 = st.columns([2, 1])
    with col1:
        display_individual_performance(data)
    with col2:
        display_top_performers(data)

    # Performance Trends
    col1, col2 = st.columns(2)
    with col1:
        display_response_time_analysis(data)
    with col2:
        display_activity_heatmap(data)

    # Goal Tracking
    display_goal_tracking(data)

def display_team_overview(data):
    """Display team overview metrics"""
    st.subheader("🎯 Team Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Team Size",
            data['team_size'],
            f"{data['team_change']:+d} this month"
        )

    with col2:
        st.metric(
            "Avg Response Time",
            f"{data['avg_response_time']:.1f} min",
            f"{data['response_improvement']:+.1f} min"
        )

    with col3:
        st.metric(
            "Team Conversion Rate",
            f"{data['team_conversion_rate']:.1f}%",
            f"{data['conversion_improvement']:+.1f}%"
        )

    with col4:
        st.metric(
            "Total Team Revenue",
            f"${data['team_revenue']:,.0f}",
            f"{data['revenue_growth']:+.1f}%"
        )

def display_individual_performance(data):
    """Display individual team member performance"""
    st.subheader("📊 Individual Performance")

    # Performance comparison chart
    df = pd.DataFrame(data['individual_performance'])

    fig = px.scatter(
        df, x='leads_handled', y='conversion_rate',
        size='revenue_generated', color='response_time',
        hover_name='team_member',
        title="Team Member Performance Matrix",
        labels={
            'leads_handled': 'Leads Handled',
            'conversion_rate': 'Conversion Rate (%)',
            'revenue_generated': 'Revenue Generated',
            'response_time': 'Avg Response Time (min)'
        }
    )
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
```

#### Page 5: Geographic Analysis (pages/5_🗺️_geographic.py)

```python
import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px
import pandas as pd
from utils.api_client import CRMAPIClient

st.set_page_config(page_title="Geographic Analysis", page_icon="🗺️", layout="wide")

def main():
    st.title("🗺️ Geographic Analysis")
    st.markdown("**Location-based insights for market penetration and expansion**")

    # Load geographic data
    data = load_geographic_data()

    # Interactive Map
    display_interactive_map(data)

    # Market Analysis
    col1, col2 = st.columns(2)
    with col1:
        display_market_penetration(data)
    with col2:
        display_expansion_opportunities(data)

    # Regional Performance
    display_regional_performance(data)

def display_interactive_map(data):
    """Display interactive map with leads and projects"""
    st.subheader("🗺️ Interactive Service Area Map")

    # Create base map centered on service area
    m = folium.Map(location=[42.3314, -83.0458], zoom_start=10)  # Detroit area

    # Add markers for different data points
    for lead in data['leads_by_location']:
        folium.CircleMarker(
            location=[lead['lat'], lead['lon']],
            radius=5,
            popup=f"Lead: {lead['name']}<br>Score: {lead['score']}",
            color='blue' if lead['score'] >= 80 else 'orange',
            fillOpacity=0.7
        ).add_to(m)

    for project in data['projects_by_location']:
        folium.Marker(
            location=[project['lat'], project['lon']],
            popup=f"Project: {project['name']}<br>Value: ${project['value']:,.0f}",
            icon=folium.Icon(color='green', icon='home')
        ).add_to(m)

    # Display map
    map_data = st_folium(m, width=700, height=500)

def display_market_penetration(data):
    """Display market penetration analysis"""
    st.subheader("📊 Market Penetration")

    df = pd.DataFrame(data['market_penetration'])

    fig = px.bar(
        df, x='zip_code', y='penetration_rate',
        title="Market Penetration by ZIP Code",
        color='penetration_rate',
        color_continuous_scale='viridis'
    )
    st.plotly_chart(fig, use_container_width=True)

def load_geographic_data():
    """Load geographic analytics data"""
    client = CRMAPIClient()
    return client.get_geographic_analytics()

if __name__ == "__main__":
    main()
```

### Day 6: Marketing ROI and Advanced Features

#### Utility Components

**components/charts.py**
```python
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def revenue_trend_chart(data):
    """Create revenue trend chart"""
    df = pd.DataFrame(data)

    fig = px.line(
        df, x='month', y='revenue',
        title="Revenue Trend Over Time",
        markers=True
    )
    fig.update_traces(line_color='#1f77b4', line_width=3)
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Revenue ($)",
        hovermode='x unified'
    )
    return fig

def funnel_chart(data):
    """Create conversion funnel chart"""
    df = pd.DataFrame(data)

    fig = px.funnel(
        df, x='count', y='stage',
        title="Sales Conversion Funnel"
    )
    return fig

def revenue_forecast_chart(historical, forecast):
    """Create revenue forecast chart with confidence intervals"""
    fig = go.Figure()

    # Historical data
    fig.add_trace(go.Scatter(
        x=historical['date'],
        y=historical['revenue'],
        mode='lines+markers',
        name='Historical',
        line=dict(color='blue', width=3)
    ))

    # Forecast
    fig.add_trace(go.Scatter(
        x=forecast['date'],
        y=forecast['predicted'],
        mode='lines+markers',
        name='Forecast',
        line=dict(color='red', width=3, dash='dash')
    ))

    # Confidence interval
    fig.add_trace(go.Scatter(
        x=forecast['date'] + forecast['date'][::-1],
        y=forecast['upper_bound'] + forecast['lower_bound'][::-1],
        fill='tonexty',
        fillcolor='rgba(255,0,0,0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Confidence Interval'
    ))

    fig.update_layout(
        title="Revenue Forecast with Confidence Intervals",
        xaxis_title="Date",
        yaxis_title="Revenue ($)",
        hovermode='x unified'
    )

    return fig
```

**utils/api_client.py**
```python
import httpx
import asyncio
from typing import Dict, List, Any
import os
from datetime import datetime, timedelta

class CRMAPIClient:
    """API client for connecting to CRM backend"""

    def __init__(self):
        self.base_url = os.getenv("API_BASE_URL", "http://localhost:5000")
        self.timeout = 30.0

    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make async request to API"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()
            return response.json()

    def get_dashboard_metrics(self) -> Dict:
        """Get dashboard overview metrics"""
        return asyncio.run(self._make_request("/api/analytics/dashboard"))

    def get_revenue_analytics(self) -> Dict:
        """Get revenue analytics data"""
        return asyncio.run(self._make_request("/api/analytics/revenue"))

    def get_lead_analytics(self, filters: Dict) -> Dict:
        """Get lead analytics with filters"""
        return asyncio.run(self._make_request("/api/analytics/leads", params=filters))

    def get_team_performance(self) -> Dict:
        """Get team performance data"""
        return asyncio.run(self._make_request("/api/analytics/team-performance"))

    def get_geographic_analytics(self) -> Dict:
        """Get geographic analysis data"""
        return asyncio.run(self._make_request("/api/analytics/geographic"))
```

### Day 7: Testing, Optimization, and Deployment

#### Testing Framework

**tests/test_components.py**
```python
import pytest
import pandas as pd
from components.charts import revenue_trend_chart, funnel_chart

def test_revenue_trend_chart():
    """Test revenue trend chart creation"""
    data = [
        {"month": "Jan", "revenue": 100000},
        {"month": "Feb", "revenue": 120000},
        {"month": "Mar", "revenue": 110000}
    ]

    fig = revenue_trend_chart(data)
    assert fig.data[0].x == ["Jan", "Feb", "Mar"]
    assert fig.data[0].y == [100000, 120000, 110000]

def test_funnel_chart():
    """Test funnel chart creation"""
    data = [
        {"stage": "Leads", "count": 100},
        {"stage": "Qualified", "count": 60},
        {"stage": "Proposals", "count": 30},
        {"stage": "Won", "count": 15}
    ]

    fig = funnel_chart(data)
    assert len(fig.data) == 1
    assert fig.data[0].x == [100, 60, 30, 15]
```

#### Performance Optimization

**utils/cache.py**
```python
import streamlit as st
from datetime import timedelta
import hashlib
import json

@st.cache_data(ttl=300)  # 5 minute cache
def get_cached_data(cache_key: str, fetch_function):
    """Cache data with TTL"""
    return fetch_function()

@st.cache_data(ttl=3600)  # 1 hour cache for less frequently changing data
def get_cached_reference_data(cache_key: str, fetch_function):
    """Cache reference data with longer TTL"""
    return fetch_function()

def clear_cache():
    """Clear all cached data"""
    st.cache_data.clear()
```

## Production Deployment

### Deployment Configuration

**Docker Support**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**Environment Variables**
```bash
# .env file
API_BASE_URL=https://api.iswitchroofs.com
STREAMLIT_PORT=8501
CACHE_TTL=300
DEBUG_MODE=false
```

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Initial Load Time | <3 seconds | Time to interactive |
| Chart Render Time | <1 second | Plotly chart display |
| Data Refresh | <2 seconds | API call + render |
| Memory Usage | <500MB | Sustained operation |
| Cache Hit Rate | >80% | Repeated data requests |

## Success Criteria

### Functional Requirements ✅
- [x] Executive dashboard with key metrics
- [x] Interactive charts and visualizations
- [x] Real-time data integration
- [x] Export capabilities
- [x] Mobile-responsive design
- [x] Authentication system
- [x] Multi-page navigation

### Performance Requirements ✅
- [x] Sub-3 second load times
- [x] Smooth chart interactions
- [x] Efficient data caching
- [x] Responsive user interface
- [x] Stable long-running sessions

### Business Requirements ✅
- [x] Executive-level insights
- [x] Actionable analytics
- [x] Professional presentation
- [x] Data-driven decision support
- [x] Strategic planning capabilities

## Phase 3 Deliverables

### Core Deliverables
1. **Complete Streamlit Application** - Multi-page analytics dashboard
2. **Interactive Visualizations** - 20+ charts and graphs
3. **Executive Reports** - Automated report generation
4. **Real-time Integration** - Live data from CRM backend
5. **Mobile Optimization** - Responsive design for all devices

### Technical Deliverables
1. **Component Library** - Reusable chart and filter components
2. **API Integration** - Complete backend connectivity
3. **Caching System** - Performance optimization
4. **Testing Suite** - Comprehensive test coverage
5. **Deployment Package** - Docker and cloud-ready deployment

### Documentation Deliverables
1. **User Guide** - Executive dashboard usage instructions
2. **Technical Documentation** - Development and maintenance guide
3. **API Documentation** - Backend integration specifications
4. **Deployment Guide** - Production deployment procedures

## Conclusion

Phase 3 will deliver a comprehensive, executive-level analytics dashboard that transforms raw CRM data into actionable business insights. The Streamlit framework provides the perfect balance of power and simplicity for rapid development of professional analytics interfaces.

**Key Success Factors:**
- **Executive Focus** - Designed specifically for strategic decision-making
- **Real-time Data** - Live integration with CRM backend
- **Professional Presentation** - Enterprise-grade visualizations
- **Mobile Accessibility** - Full functionality across devices
- **Performance Optimized** - Fast, responsive user experience

The implementation plan ensures delivery of a production-ready analytics platform that will significantly enhance the business intelligence capabilities of the iSwitch Roofs CRM system.

---

**Document Version:** 1.0
**Last Updated:** January 17, 2025
**Author:** Development Team
**Review Status:** Complete
**Implementation Target:** Week 7 (1 week duration)