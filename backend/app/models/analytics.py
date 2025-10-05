"""
iSwitch Roofs CRM - Analytics Data Models
Version: 1.0.0

Comprehensive analytics data models for business intelligence,
KPI tracking, and dashboard visualization.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.base import BaseDBModel


class AnalyticsTimeframe(str, Enum):
    """Analytics timeframe enumeration"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    MTD = "month_to_date"
    QTD = "quarter_to_date"
    YTD = "year_to_date"
    CUSTOM = "custom"


class MetricCategory(str, Enum):
    """Metric category enumeration"""

    LEADS = "leads"
    REVENUE = "revenue"
    CONVERSION = "conversion"
    OPERATIONAL = "operational"
    CUSTOMER = "customer"
    MARKETING = "marketing"
    TEAM = "team"
    WEATHER = "weather"
    SEASONAL = "seasonal"


class ChartType(str, Enum):
    """Chart type enumeration for visualizations"""

    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    DONUT = "donut"
    AREA = "area"
    FUNNEL = "funnel"
    GAUGE = "gauge"
    HEATMAP = "heatmap"
    SCATTER = "scatter"
    TREEMAP = "treemap"


class AlertLevel(str, Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    SUCCESS = "success"


# Core Analytics Models


class KPIDefinition(BaseDBModel):
    """
    KPI definition model for tracking business metrics
    """

    name: str = Field(..., max_length=100, description="KPI name")
    display_name: str = Field(..., max_length=150, description="Display name for dashboard")
    description: str = Field(..., max_length=500, description="KPI description")
    category: MetricCategory = Field(..., description="Metric category")

    # Calculation configuration
    calculation_method: str = Field(..., description="How the KPI is calculated")
    data_source: str = Field(..., description="Primary data source table")
    formula: str | None = Field(None, description="SQL formula or calculation logic")

    # Targets and thresholds
    target_value: float | None = Field(None, description="Target value for this KPI")
    warning_threshold: float | None = Field(None, description="Warning threshold")
    critical_threshold: float | None = Field(None, description="Critical threshold")

    # Display configuration
    unit: str | None = Field(None, description="Unit of measurement (%, $, count)")
    decimal_places: int = Field(default=2, ge=0, le=6, description="Decimal places for display")
    chart_type: ChartType | None = Field(None, description="Preferred chart type")

    # Status
    is_active: bool = Field(default=True, description="Is KPI actively tracked")
    update_frequency: str = Field(default="hourly", description="How often to update")

    # Metadata
    created_by: UUID = Field(..., description="User who created this KPI")
    tags: str | None = Field(None, description="Comma-separated tags")


class MetricValue(BaseDBModel):
    """
    Historical metric values for trend analysis
    """

    kpi_id: UUID = Field(..., description="Reference to KPI definition")
    date: date = Field(..., description="Date of the metric")
    timeframe: AnalyticsTimeframe = Field(..., description="Timeframe of this value")

    # Values
    value: float = Field(..., description="Metric value")
    target: float | None = Field(None, description="Target value for this period")
    previous_value: float | None = Field(None, description="Previous period value")

    # Context
    data_points: int = Field(default=1, description="Number of data points aggregated")
    confidence_score: float | None = Field(
        None, ge=0, le=100, description="Data confidence (0-100)"
    )

    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.utcnow, description="When calculated")
    calculation_duration_ms: int | None = Field(
        None, description="Calculation time in milliseconds"
    )


class ConversionFunnel(BaseDBModel):
    """
    Conversion funnel analysis model
    """

    name: str = Field(..., max_length=100, description="Funnel name")
    timeframe: AnalyticsTimeframe = Field(..., description="Analysis timeframe")
    start_date: date = Field(..., description="Analysis start date")
    end_date: date = Field(..., description="Analysis end date")

    # Funnel stages with counts
    stage_1_count: int = Field(default=0, description="Leads generated")
    stage_2_count: int = Field(default=0, description="Leads contacted")
    stage_3_count: int = Field(default=0, description="Leads qualified")
    stage_4_count: int = Field(default=0, description="Appointments scheduled")
    stage_5_count: int = Field(default=0, description="Inspections completed")
    stage_6_count: int = Field(default=0, description="Quotes sent")
    stage_7_count: int = Field(default=0, description="Customers converted")

    # Conversion rates between stages
    stage_1_to_2_rate: float = Field(default=0.0, description="Contact rate")
    stage_2_to_3_rate: float = Field(default=0.0, description="Qualification rate")
    stage_3_to_4_rate: float = Field(default=0.0, description="Appointment rate")
    stage_4_to_5_rate: float = Field(default=0.0, description="Inspection rate")
    stage_5_to_6_rate: float = Field(default=0.0, description="Quote rate")
    stage_6_to_7_rate: float = Field(default=0.0, description="Conversion rate")

    # Overall metrics
    overall_conversion_rate: float = Field(default=0.0, description="End-to-end conversion rate")
    avg_days_to_convert: float | None = Field(
        None, description="Average days from lead to customer"
    )

    # Bottleneck analysis
    bottleneck_stage: str | None = Field(None, description="Stage with lowest conversion")
    bottleneck_rate: float | None = Field(None, description="Bottleneck conversion rate")


class RevenueAnalytics(BaseDBModel):
    """
    Revenue analytics and forecasting model
    """

    period_name: str = Field(..., max_length=50, description="Period identifier (e.g., '2025-01')")
    timeframe: AnalyticsTimeframe = Field(..., description="Revenue timeframe")
    start_date: date = Field(..., description="Period start date")
    end_date: date = Field(..., description="Period end date")

    # Revenue metrics
    total_revenue: Decimal = Field(default=0, description="Total actual revenue")
    quoted_revenue: Decimal = Field(default=0, description="Total quoted revenue")
    pipeline_value: Decimal = Field(default=0, description="Pipeline revenue value")

    # Project metrics
    projects_completed: int = Field(default=0, description="Projects completed")
    projects_in_progress: int = Field(default=0, description="Projects in progress")
    avg_project_value: Decimal = Field(default=0, description="Average project value")

    # Profitability
    total_costs: Decimal = Field(default=0, description="Total project costs")
    gross_profit: Decimal = Field(default=0, description="Gross profit")
    gross_margin_pct: float = Field(default=0.0, description="Gross margin percentage")

    # Growth metrics
    revenue_growth_pct: float = Field(default=0.0, description="Revenue growth vs previous period")
    target_achievement_pct: float = Field(default=0.0, description="Achievement vs target")

    # Forecasting
    forecasted_revenue: Decimal | None = Field(None, description="Forecasted revenue")
    forecast_confidence: float | None = Field(None, description="Forecast confidence level")

    # Breakdown by categories
    revenue_by_type: dict[str, float] | None = Field(None, description="Revenue by project type")
    revenue_by_source: dict[str, float] | None = Field(None, description="Revenue by lead source")
    revenue_by_team: dict[str, float] | None = Field(None, description="Revenue by team member")


class CustomerAnalytics(BaseDBModel):
    """
    Customer lifecycle and value analytics
    """

    period_name: str = Field(..., max_length=50, description="Period identifier")
    timeframe: AnalyticsTimeframe = Field(..., description="Analysis timeframe")
    start_date: date = Field(..., description="Period start date")
    end_date: date = Field(..., description="Period end date")

    # Customer acquisition
    new_customers: int = Field(default=0, description="New customers acquired")
    total_customers: int = Field(default=0, description="Total customer base")
    customer_growth_rate: float = Field(default=0.0, description="Customer growth rate")

    # Customer value
    avg_customer_value: Decimal = Field(default=0, description="Average customer value")
    total_ltv: Decimal = Field(default=0, description="Total customer lifetime value")
    avg_ltv: Decimal = Field(default=0, description="Average lifetime value")

    # Retention and satisfaction
    retention_rate: float = Field(default=0.0, description="Customer retention rate")
    repeat_customer_rate: float = Field(default=0.0, description="Repeat customer rate")
    avg_satisfaction: float = Field(default=0.0, description="Average satisfaction score")
    nps_score: float = Field(default=0.0, description="Net Promoter Score")

    # Referrals
    referral_count: int = Field(default=0, description="Referrals generated")
    referral_conversion_rate: float = Field(default=0.0, description="Referral conversion rate")
    referral_value: Decimal = Field(default=0, description="Value from referrals")

    # Segmentation
    premium_customers: int = Field(default=0, description="Premium segment customers")
    standard_customers: int = Field(default=0, description="Standard segment customers")
    vip_customers: int = Field(default=0, description="VIP customers")


class TeamPerformance(BaseDBModel):
    """
    Team member performance analytics
    """

    team_member_id: UUID = Field(..., description="Team member ID")
    period_name: str = Field(..., max_length=50, description="Performance period")
    timeframe: AnalyticsTimeframe = Field(..., description="Performance timeframe")
    start_date: date = Field(..., description="Period start date")
    end_date: date = Field(..., description="Period end date")

    # Lead metrics
    leads_assigned: int = Field(default=0, description="Leads assigned")
    leads_contacted: int = Field(default=0, description="Leads contacted")
    leads_converted: int = Field(default=0, description="Leads converted")
    lead_conversion_rate: float = Field(default=0.0, description="Lead conversion rate")

    # Response metrics
    avg_response_time_minutes: float = Field(default=0.0, description="Average response time")
    response_target_met_pct: float = Field(default=0.0, description="Response target achievement")

    # Revenue metrics
    revenue_generated: Decimal = Field(default=0, description="Revenue generated")
    avg_deal_size: Decimal = Field(default=0, description="Average deal size")
    quota_achievement_pct: float = Field(default=0.0, description="Quota achievement")

    # Activity metrics
    total_interactions: int = Field(default=0, description="Total customer interactions")
    appointments_scheduled: int = Field(default=0, description="Appointments scheduled")
    appointments_completed: int = Field(default=0, description="Appointments completed")
    appointment_completion_rate: float = Field(
        default=0.0, description="Appointment completion rate"
    )

    # Quality metrics
    customer_satisfaction: float = Field(default=0.0, description="Customer satisfaction score")
    quality_score: float = Field(default=0.0, description="Overall quality score")

    # Performance scoring
    performance_score: float = Field(default=0.0, description="Overall performance score (0-100)")
    rank_in_team: int | None = Field(None, description="Rank within team")

    # Goals and targets
    leads_target: int | None = Field(None, description="Lead generation target")
    revenue_target: Decimal | None = Field(None, description="Revenue target")
    conversion_target: float | None = Field(None, description="Conversion rate target")


class MarketingAnalytics(BaseDBModel):
    """
    Marketing channel performance and ROI analytics
    """

    channel_name: str = Field(..., max_length=100, description="Marketing channel name")
    period_name: str = Field(..., max_length=50, description="Period identifier")
    timeframe: AnalyticsTimeframe = Field(..., description="Analysis timeframe")
    start_date: date = Field(..., description="Period start date")
    end_date: date = Field(..., description="Period end date")

    # Investment metrics
    marketing_spend: Decimal = Field(default=0, description="Total marketing spend")
    cost_per_click: Decimal | None = Field(None, description="Cost per click (if applicable)")
    cost_per_impression: Decimal | None = Field(None, description="Cost per impression")

    # Lead generation
    leads_generated: int = Field(default=0, description="Leads generated")
    cost_per_lead: Decimal = Field(default=0, description="Cost per lead")
    lead_quality_score: float = Field(default=0.0, description="Average lead quality score")

    # Conversion metrics
    leads_converted: int = Field(default=0, description="Leads converted to customers")
    conversion_rate: float = Field(default=0.0, description="Lead to customer conversion rate")
    cost_per_acquisition: Decimal = Field(default=0, description="Customer acquisition cost")

    # Revenue impact
    revenue_generated: Decimal = Field(default=0, description="Revenue attributed to channel")
    roi_percentage: float = Field(default=0.0, description="Return on investment")
    payback_period_days: float | None = Field(None, description="Payback period in days")

    # Channel-specific metrics
    impressions: int | None = Field(None, description="Ad impressions")
    clicks: int | None = Field(None, description="Ad clicks")
    click_through_rate: float | None = Field(None, description="Click-through rate")

    # Attribution
    first_touch_attribution: float = Field(
        default=0.0, description="First-touch attribution weight"
    )
    last_touch_attribution: float = Field(default=0.0, description="Last-touch attribution weight")
    linear_attribution: float = Field(default=0.0, description="Linear attribution weight")


class WeatherImpactAnalytics(BaseDBModel):
    """
    Weather impact on roofing business analytics
    """

    date: date = Field(..., description="Weather data date")
    location_zip: str = Field(..., max_length=10, description="Location ZIP code")

    # Weather data
    weather_condition: str = Field(..., max_length=50, description="Weather condition")
    temperature_high: float | None = Field(None, description="High temperature (F)")
    temperature_low: float | None = Field(None, description="Low temperature (F)")
    precipitation_inches: float = Field(default=0.0, description="Precipitation in inches")
    wind_speed_mph: float | None = Field(None, description="Wind speed in MPH")

    # Storm tracking
    is_storm_day: bool = Field(default=False, description="Was this a storm day")
    storm_severity: str | None = Field(None, description="Storm severity (mild/moderate/severe)")
    hail_reported: bool = Field(default=False, description="Hail reported")
    hail_size_inches: float | None = Field(None, description="Hail size in inches")

    # Business impact
    leads_generated: int = Field(default=0, description="Leads generated this day")
    emergency_calls: int = Field(default=0, description="Emergency calls received")
    inspections_scheduled: int = Field(default=0, description="Inspections scheduled")
    work_days_lost: float = Field(default=0.0, description="Work days lost due to weather")

    # Correlation metrics
    weather_lead_correlation: float | None = Field(
        None, description="Weather-lead correlation coefficient"
    )
    seasonal_factor: float | None = Field(None, description="Seasonal adjustment factor")


class BusinessAlert(BaseDBModel):
    """
    Business intelligence alerts and notifications
    """

    alert_type: str = Field(..., max_length=50, description="Type of alert")
    level: AlertLevel = Field(..., description="Alert severity level")
    title: str = Field(..., max_length=200, description="Alert title")
    message: str = Field(..., max_length=1000, description="Alert message")

    # Triggering conditions
    metric_name: str = Field(..., max_length=100, description="Metric that triggered alert")
    current_value: float = Field(..., description="Current metric value")
    threshold_value: float = Field(..., description="Threshold that was breached")
    threshold_type: str = Field(..., description="above/below/equals")

    # Context
    timeframe: AnalyticsTimeframe = Field(..., description="Timeframe of the metric")
    affected_entities: str | None = Field(None, description="Entities affected by this alert")

    # Status
    is_acknowledged: bool = Field(default=False, description="Has alert been acknowledged")
    acknowledged_by: UUID | None = Field(None, description="User who acknowledged")
    acknowledged_at: datetime | None = Field(None, description="When acknowledged")
    is_resolved: bool = Field(default=False, description="Has underlying issue been resolved")
    resolved_at: datetime | None = Field(None, description="When resolved")

    # Actions
    recommended_actions: str | None = Field(None, description="Recommended actions")
    action_taken: str | None = Field(None, description="Action taken")


class DashboardConfig(BaseDBModel):
    """
    Dashboard configuration model
    """

    name: str = Field(..., max_length=100, description="Dashboard name")
    description: str | None = Field(None, max_length=500, description="Dashboard description")
    dashboard_type: str = Field(..., description="executive/operational/team/marketing")

    # Access control
    created_by: UUID = Field(..., description="Dashboard creator")
    is_public: bool = Field(default=False, description="Is dashboard public")
    allowed_roles: str | None = Field(None, description="Comma-separated allowed roles")

    # Configuration
    layout: dict[str, Any] = Field(..., description="Dashboard layout configuration")
    widgets: list[dict[str, Any]] = Field(..., description="Widget configurations")
    default_timeframe: AnalyticsTimeframe = Field(
        default=AnalyticsTimeframe.MTD, description="Default timeframe"
    )
    auto_refresh_seconds: int = Field(default=300, description="Auto refresh interval")

    # Status
    is_active: bool = Field(default=True, description="Is dashboard active")
    last_accessed: datetime | None = Field(None, description="Last access time")
    access_count: int = Field(default=0, description="Number of times accessed")


# Request/Response Models


class AnalyticsRequest(BaseModel):
    """Base analytics request model"""

    timeframe: AnalyticsTimeframe = AnalyticsTimeframe.MTD
    start_date: date | None = None
    end_date: date | None = None
    filters: dict[str, Any] | None = None
    group_by: list[str] | None = None


class KPIRequest(AnalyticsRequest):
    """KPI calculation request"""

    kpi_names: list[str] | None = None
    include_trends: bool = True
    include_targets: bool = True
    include_breakdown: bool = False


class FunnelAnalysisRequest(AnalyticsRequest):
    """Funnel analysis request"""

    funnel_type: str = "lead_conversion"
    include_sources: bool = True
    include_temperature: bool = True
    include_bottlenecks: bool = True


class RevenueAnalysisRequest(AnalyticsRequest):
    """Revenue analysis request"""

    include_forecast: bool = True
    forecast_months: int = 3
    include_breakdown: bool = True
    include_profitability: bool = True


class TeamPerformanceRequest(AnalyticsRequest):
    """Team performance request"""

    team_member_ids: list[UUID] | None = None
    include_rankings: bool = True
    include_targets: bool = True
    include_activities: bool = True


class MarketingROIRequest(AnalyticsRequest):
    """Marketing ROI analysis request"""

    channels: list[str] | None = None
    include_attribution: bool = True
    include_campaign_details: bool = False


class WeatherCorrelationRequest(AnalyticsRequest):
    """Weather correlation analysis request"""

    zip_codes: list[str] | None = None
    include_storm_impact: bool = True
    correlation_metrics: list[str] | None = None


# Response Models


class KPIResponse(BaseModel):
    """KPI calculation response"""

    timeframe: AnalyticsTimeframe
    kpis: dict[str, Any]
    trends: dict[str, list[dict]] | None = None
    targets: dict[str, float] | None = None
    alerts: list[dict] | None = None
    generated_at: datetime


class FunnelAnalysisResponse(BaseModel):
    """Funnel analysis response"""

    funnel: ConversionFunnel
    breakdown: dict[str, Any] | None = None
    bottlenecks: list[dict] | None = None
    recommendations: list[str] | None = None


class RevenueAnalysisResponse(BaseModel):
    """Revenue analysis response"""

    revenue_analytics: RevenueAnalytics
    forecast: dict[str, Any] | None = None
    breakdown: dict[str, Any] | None = None
    trends: list[dict] | None = None


class TeamPerformanceResponse(BaseModel):
    """Team performance response"""

    performances: list[TeamPerformance]
    team_rankings: list[dict] | None = None
    team_averages: dict[str, float] | None = None
    improvement_areas: list[dict] | None = None


class MarketingROIResponse(BaseModel):
    """Marketing ROI response"""

    marketing_analytics: list[MarketingAnalytics]
    overall_roi: float | None = None
    channel_rankings: list[dict] | None = None
    attribution_analysis: dict[str, Any] | None = None


class WeatherCorrelationResponse(BaseModel):
    """Weather correlation response"""

    weather_analytics: list[WeatherImpactAnalytics]
    correlations: dict[str, float] | None = None
    seasonal_patterns: dict[str, Any] | None = None
    storm_impact_summary: dict[str, Any] | None = None


class DashboardResponse(BaseModel):
    """Complete dashboard response"""

    dashboard_config: DashboardConfig
    kpis: dict[str, Any]
    charts: list[dict[str, Any]]
    alerts: list[BusinessAlert]
    last_updated: datetime
    next_update: datetime | None = None


# Utility Models


class ChartConfiguration(BaseModel):
    """Chart configuration for dashboard widgets"""

    chart_type: ChartType
    title: str
    data_source: str
    x_axis: str
    y_axis: str
    color_scheme: str | None = None
    show_legend: bool = True
    show_grid: bool = True
    height: int = 400
    width: int | None = None


class FilterConfiguration(BaseModel):
    """Filter configuration for analytics"""

    field_name: str
    filter_type: str  # equals, contains, greater_than, less_than, between, in
    values: list[Any]
    is_required: bool = False


class ExportRequest(BaseModel):
    """Analytics export request"""

    export_format: str = "json"  # json, csv, xlsx, pdf
    timeframe: AnalyticsTimeframe = AnalyticsTimeframe.MTD
    metrics: list[str]
    include_charts: bool = False
    email_to: str | None = None
