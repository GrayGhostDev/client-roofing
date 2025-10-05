# Analytics Dashboard - iSwitch Roofs CRM

## Overview

The Analytics Dashboard provides comprehensive business insights and performance metrics for the roofing CRM system. It includes KPI tracking, conversion funnel analysis, revenue analytics, and team performance monitoring.

## Features

### 📊 Key Performance Indicators (KPIs)
- **Business Health Score**: Overall business performance gauge (0-100)
- **Revenue Metrics**: Total revenue, pipeline value, average deal size
- **Lead Metrics**: Total leads, response time, conversion rate
- **Operational Metrics**: Active team members, projects, completion rates

### 🔄 Conversion Funnel Analysis
- **7-Stage Pipeline**: Lead → Contact → Qualify → Inspect → Quote → Close → Customer
- **Stage-to-Stage Conversion**: Detailed conversion rates between stages
- **Bottleneck Identification**: Visual highlighting of drop-off points
- **Actionable Insights**: Recommended improvements based on data

### 💰 Revenue Analytics
- **Trend Visualization**: Monthly/quarterly/yearly revenue trends
- **Source Breakdown**: Revenue attribution by lead source
- **Project Value Distribution**: Analysis of project size ranges
- **Revenue Forecasting**: Conservative, realistic, and optimistic projections

### 👥 Team Performance
- **Individual Performance Cards**: Metrics for each team member
- **Team Leaderboard**: Rankings with performance ratings
- **Goal Tracking**: Progress toward quotas and targets
- **Activity Feed**: Recent achievements and milestones

## File Structure

```
frontend-reflex/frontend_reflex/components/analytics/
├── __init__.py                 # Package initialization
├── analytics_dashboard.py     # Main dashboard page
├── kpi_cards.py               # KPI display components
├── conversion_funnel.py       # Funnel visualization
├── revenue_charts.py          # Revenue analytics
└── team_performance.py       # Team metrics
```

## Component Architecture

### Analytics Dashboard (`analytics_dashboard.py`)
- Main page container with navigation
- Filter controls for date ranges and data segmentation
- View mode tabs (Overview, Detailed, Team)
- Error handling and loading states

### KPI Cards (`kpi_cards.py`)
- Business health gauge with color-coded scoring
- Individual KPI cards with trend indicators
- Clickable cards for drill-down analysis
- Responsive grid layout

### Conversion Funnel (`conversion_funnel.py`)
- Visual funnel representation with stage bars
- Percentage-based width calculations
- Conversion rate highlighting
- Insights and recommendations

### Revenue Charts (`revenue_charts.py`)
- Mock chart visualizations (ready for charting library integration)
- Revenue trend analysis
- Source attribution breakdown
- Project value distribution
- Forecasting with confidence intervals

### Team Performance (`team_performance.py`)
- Individual team member cards with ratings
- Leaderboard with rankings and achievements
- Goal tracking with progress bars
- Activity feed for recent accomplishments

## State Management

### Analytics State Variables
```python
# Data storage
analytics_data: Dict[str, Any] = {}
kpi_data: Dict[str, Any] = {}
conversion_funnel_data: Dict[str, Any] = {}
revenue_data: Dict[str, Any] = {}
team_performance_data: Dict[str, Any] = {}

# UI state
analytics_loading: bool = False
analytics_view_mode: str = "overview"
analytics_selected_metric: str = ""

# Filters
analytics_date_range: str = "last_30_days"
analytics_start_date: str = ""
analytics_end_date: str = ""
analytics_lead_source_filter: str = "all"
analytics_team_member_filter: str = "all"
analytics_project_type_filter: str = "all"
```

### Key Methods
```python
# Data loading
async def load_analytics_data()

# Filter management
def set_analytics_date_range(date_range: str)
def set_analytics_view_mode(view_mode: str)
def clear_analytics_filters()

# Computed properties
@rx.var def analytics_kpi_summary() -> Dict[str, Any]
@rx.var def analytics_conversion_stages() -> List[Dict[str, Any]]
@rx.var def analytics_revenue_trends() -> List[Dict[str, Any]]
@rx.var def analytics_team_leaderboard() -> List[Dict[str, Any]]

# Export functionality
async def export_analytics_report(report_type: str = "pdf")
```

## API Integration

The dashboard integrates with the following backend endpoints:

```
GET /api/analytics/kpis                    # KPI summary data
GET /api/analytics/conversion-funnel       # Funnel stage data
GET /api/analytics/revenue                 # Revenue analytics
GET /api/analytics/team-performance        # Team metrics
POST /api/analytics/export                 # Report export
```

### Query Parameters
- `date_range`: "last_7_days", "last_30_days", "last_90_days", "last_year", "custom"
- `start_date`: Custom start date (YYYY-MM-DD)
- `end_date`: Custom end date (YYYY-MM-DD)
- `lead_source`: Filter by lead source
- `team_member`: Filter by team member
- `project_type`: Filter by project type

## Usage

### Accessing the Dashboard
1. Navigate to `/analytics` in the application
2. Click "View Analytics" from the main dashboard
3. Use navigation links to switch between modules

### Filtering Data
1. Select date range from dropdown (last 7 days, 30 days, etc.)
2. Choose "custom" for specific date range selection
3. Apply filters for lead source, team member, or project type
4. Click "Apply Filters" to refresh data

### View Modes
- **Overview**: High-level dashboard with key metrics
- **Detailed**: In-depth analysis with expanded charts
- **Team**: Team-focused metrics and performance tracking

### Exporting Reports
1. Click "Export Report" button
2. Choose format (PDF, Excel)
3. Report generates with current filter settings

## Customization

### Adding New KPIs
1. Update `analytics_kpi_summary` computed property
2. Add new KPI card in `kpi_cards_section()`
3. Update backend API to provide new metric

### Custom Charts
Replace mock visualizations in revenue_charts.py with actual charting library:
```python
# Example with plotly or recharts
import plotly.graph_objects as go

def revenue_trend_chart():
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=revenue))
    return rx.plotly(data=fig)
```

### New Filters
1. Add filter state variable to AppState
2. Create filter UI component
3. Update API calls to include new parameter

## Responsive Design

The dashboard is built with responsive design principles:
- Grid layouts adjust to screen size
- Cards stack vertically on mobile
- Text sizes scale appropriately
- Interactive elements maintain touch targets

## Performance Considerations

- **Data Caching**: Uses `@rx.var(cache=True)` for computed properties
- **Lazy Loading**: Components load data on mount
- **Efficient Updates**: State updates trigger minimal re-renders
- **Mock Data**: Provides fallback data when API unavailable

## Future Enhancements

### Planned Features
- Real-time data updates with WebSocket integration
- Interactive charts with drill-down capabilities
- Advanced filtering with date comparisons
- Scheduled report generation
- Dashboard customization and widget arrangement
- Mobile app integration

### Integration Opportunities
- Customer communication tracking
- Project timeline correlation
- Financial system integration
- Marketing automation metrics
- Weather impact analysis for roofing seasonality

## Testing

Run the test script to verify implementation:
```bash
cd frontend-reflex
python ../test_analytics.py
```

## Dependencies

- **Reflex**: Frontend framework
- **httpx**: HTTP client for API calls
- **typing**: Type hints support

## Support

For issues or questions:
1. Check the test script output for component verification
2. Review browser console for JavaScript errors
3. Verify API endpoints are responding correctly
4. Ensure all required state variables are initialized

---

**Created for iSwitch Roofs CRM**
Analytics Dashboard v1.0 - Comprehensive business intelligence for roofing contractors