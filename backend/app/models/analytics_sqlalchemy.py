"""
iSwitch Roofs CRM - Analytics SQLAlchemy Models
Version: 1.0.0

Comprehensive analytics data models for business intelligence,
KPI tracking, and dashboard visualization.
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, Date, Float, Enum as SQLEnum, Numeric
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from datetime import datetime, date
from enum import Enum
from decimal import Decimal

from app.models.base import BaseModel


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

class KPIDefinition(BaseModel):
    """
    KPI definition model for tracking business metrics
    """
    __tablename__ = 'kpi_definitions'

    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(150), nullable=False)
    description = Column(String(500), nullable=False)
    category = Column(SQLEnum(MetricCategory), nullable=False)

    # Calculation configuration
    calculation_method = Column(Text, nullable=False)
    data_source = Column(String(100), nullable=False)
    formula = Column(Text, nullable=True)

    # Targets and thresholds
    target_value = Column(Float, nullable=True)
    warning_threshold = Column(Float, nullable=True)
    critical_threshold = Column(Float, nullable=True)

    # Display configuration
    unit = Column(String(20), nullable=True)
    decimal_places = Column(Integer, default=2)
    chart_type = Column(SQLEnum(ChartType), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    update_frequency = Column(String(50), default="hourly")

    # Metadata
    created_by = Column(String(36), nullable=False)
    tags = Column(Text, nullable=True)


class MetricValue(BaseModel):
    """
    Historical metric values for trend analysis
    """
    __tablename__ = 'metric_values'

    kpi_id = Column(String(36), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    timeframe = Column(SQLEnum(AnalyticsTimeframe), nullable=False)

    # Values
    value = Column(Float, nullable=False)
    target = Column(Float, nullable=True)
    previous_value = Column(Float, nullable=True)

    # Context
    data_points = Column(Integer, default=1)
    confidence_score = Column(Float, nullable=True)

    # Metadata
    calculated_at = Column(DateTime, default=datetime.utcnow)
    calculation_duration_ms = Column(Integer, nullable=True)


class ConversionFunnel(BaseModel):
    """
    Conversion funnel analysis model
    """
    __tablename__ = 'conversion_funnels'

    name = Column(String(100), nullable=False)
    timeframe = Column(SQLEnum(AnalyticsTimeframe), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Funnel stages with counts
    stage_1_count = Column(Integer, default=0)  # Leads generated
    stage_2_count = Column(Integer, default=0)  # Leads contacted
    stage_3_count = Column(Integer, default=0)  # Leads qualified
    stage_4_count = Column(Integer, default=0)  # Appointments scheduled
    stage_5_count = Column(Integer, default=0)  # Inspections completed
    stage_6_count = Column(Integer, default=0)  # Quotes sent
    stage_7_count = Column(Integer, default=0)  # Customers converted

    # Conversion rates between stages
    stage_1_to_2_rate = Column(Float, default=0.0)
    stage_2_to_3_rate = Column(Float, default=0.0)
    stage_3_to_4_rate = Column(Float, default=0.0)
    stage_4_to_5_rate = Column(Float, default=0.0)
    stage_5_to_6_rate = Column(Float, default=0.0)
    stage_6_to_7_rate = Column(Float, default=0.0)

    # Overall metrics
    overall_conversion_rate = Column(Float, default=0.0)
    avg_days_to_convert = Column(Float, nullable=True)

    # Bottleneck analysis
    bottleneck_stage = Column(String(50), nullable=True)
    bottleneck_rate = Column(Float, nullable=True)


class RevenueAnalytics(BaseModel):
    """
    Revenue analytics and forecasting model
    """
    __tablename__ = 'revenue_analytics'

    period_name = Column(String(50), nullable=False)
    timeframe = Column(SQLEnum(AnalyticsTimeframe), nullable=False)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)

    # Revenue metrics
    total_revenue = Column(Numeric(15, 2), default=0)
    quoted_revenue = Column(Numeric(15, 2), default=0)
    pipeline_value = Column(Numeric(15, 2), default=0)

    # Project metrics
    projects_completed = Column(Integer, default=0)
    projects_in_progress = Column(Integer, default=0)
    avg_project_value = Column(Numeric(15, 2), default=0)

    # Profitability
    total_costs = Column(Numeric(15, 2), default=0)
    gross_profit = Column(Numeric(15, 2), default=0)
    gross_margin_pct = Column(Float, default=0.0)

    # Growth metrics
    revenue_growth_pct = Column(Float, default=0.0)
    target_achievement_pct = Column(Float, default=0.0)

    # Forecasting
    forecasted_revenue = Column(Numeric(15, 2), nullable=True)
    forecast_confidence = Column(Float, nullable=True)


class CustomerAnalytics(BaseModel):
    """
    Customer lifecycle and value analytics
    """
    __tablename__ = 'customer_analytics'

    period_name = Column(String(50), nullable=False)
    timeframe = Column(SQLEnum(AnalyticsTimeframe), nullable=False)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)

    # Customer acquisition
    new_customers = Column(Integer, default=0)
    total_customers = Column(Integer, default=0)
    customer_growth_rate = Column(Float, default=0.0)

    # Customer value
    avg_customer_value = Column(Numeric(15, 2), default=0)
    total_ltv = Column(Numeric(15, 2), default=0)
    avg_ltv = Column(Numeric(15, 2), default=0)

    # Retention and satisfaction
    retention_rate = Column(Float, default=0.0)
    repeat_customer_rate = Column(Float, default=0.0)
    avg_satisfaction = Column(Float, default=0.0)
    nps_score = Column(Float, default=0.0)

    # Referrals
    referral_count = Column(Integer, default=0)
    referral_conversion_rate = Column(Float, default=0.0)
    referral_value = Column(Numeric(15, 2), default=0)

    # Segmentation
    premium_customers = Column(Integer, default=0)
    standard_customers = Column(Integer, default=0)
    vip_customers = Column(Integer, default=0)


class TeamPerformance(BaseModel):
    """
    Team member performance analytics
    """
    __tablename__ = 'team_performance'

    team_member_id = Column(String(36), nullable=False, index=True)
    period_name = Column(String(50), nullable=False)
    timeframe = Column(SQLEnum(AnalyticsTimeframe), nullable=False)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)

    # Lead metrics
    leads_assigned = Column(Integer, default=0)
    leads_contacted = Column(Integer, default=0)
    leads_converted = Column(Integer, default=0)
    lead_conversion_rate = Column(Float, default=0.0)

    # Response metrics
    avg_response_time_minutes = Column(Float, default=0.0)
    response_target_met_pct = Column(Float, default=0.0)

    # Revenue metrics
    revenue_generated = Column(Numeric(15, 2), default=0)
    avg_deal_size = Column(Numeric(15, 2), default=0)
    quota_achievement_pct = Column(Float, default=0.0)

    # Activity metrics
    total_interactions = Column(Integer, default=0)
    appointments_scheduled = Column(Integer, default=0)
    appointments_completed = Column(Integer, default=0)
    appointment_completion_rate = Column(Float, default=0.0)

    # Quality metrics
    customer_satisfaction = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)

    # Performance scoring
    performance_score = Column(Float, default=0.0)
    rank_in_team = Column(Integer, nullable=True)

    # Goals and targets
    leads_target = Column(Integer, nullable=True)
    revenue_target = Column(Numeric(15, 2), nullable=True)
    conversion_target = Column(Float, nullable=True)


class MarketingAnalytics(BaseModel):
    """
    Marketing channel performance and ROI analytics
    """
    __tablename__ = 'marketing_analytics'

    channel_name = Column(String(100), nullable=False)
    period_name = Column(String(50), nullable=False)
    timeframe = Column(SQLEnum(AnalyticsTimeframe), nullable=False)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)

    # Investment metrics
    marketing_spend = Column(Numeric(15, 2), default=0)
    cost_per_click = Column(Numeric(10, 2), nullable=True)
    cost_per_impression = Column(Numeric(10, 4), nullable=True)

    # Lead generation
    leads_generated = Column(Integer, default=0)
    cost_per_lead = Column(Numeric(10, 2), default=0)
    lead_quality_score = Column(Float, default=0.0)

    # Conversion metrics
    leads_converted = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    cost_per_acquisition = Column(Numeric(15, 2), default=0)

    # Revenue impact
    revenue_generated = Column(Numeric(15, 2), default=0)
    roi_percentage = Column(Float, default=0.0)
    payback_period_days = Column(Float, nullable=True)

    # Channel-specific metrics
    impressions = Column(Integer, nullable=True)
    clicks = Column(Integer, nullable=True)
    click_through_rate = Column(Float, nullable=True)

    # Attribution
    first_touch_attribution = Column(Float, default=0.0)
    last_touch_attribution = Column(Float, default=0.0)
    linear_attribution = Column(Float, default=0.0)


class BusinessAlert(BaseModel):
    """
    Business intelligence alerts and notifications
    """
    __tablename__ = 'business_alerts'

    alert_type = Column(String(50), nullable=False)
    level = Column(SQLEnum(AlertLevel), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(String(1000), nullable=False)

    # Triggering conditions
    metric_name = Column(String(100), nullable=False)
    current_value = Column(Float, nullable=False)
    threshold_value = Column(Float, nullable=False)
    threshold_type = Column(String(20), nullable=False)

    # Context
    timeframe = Column(SQLEnum(AnalyticsTimeframe), nullable=False)
    affected_entities = Column(Text, nullable=True)

    # Status
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(36), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)

    # Actions
    recommended_actions = Column(Text, nullable=True)
    action_taken = Column(Text, nullable=True)


# Pydantic schemas for API validation
class KPIDefinitionCreateSchema(BaseModel):
    """Schema for creating a KPI definition"""
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., max_length=100)
    display_name: str = Field(..., max_length=150)
    description: str = Field(..., max_length=500)
    category: MetricCategory
    calculation_method: str
    data_source: str
    formula: Optional[str] = None

    target_value: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    unit: Optional[str] = None
    decimal_places: Optional[int] = 2
    chart_type: Optional[ChartType] = None


class KPIDefinitionResponseSchema(BaseModel):
    """Schema for KPI definition API response"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    display_name: str
    description: str
    category: MetricCategory
    target_value: Optional[float] = None
    unit: Optional[str] = None
    decimal_places: int = 2
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class MetricValueCreateSchema(BaseModel):
    """Schema for creating a metric value"""
    model_config = ConfigDict(from_attributes=True)

    kpi_id: UUID
    date: date
    timeframe: AnalyticsTimeframe
    value: float
    target: Optional[float] = None
    previous_value: Optional[float] = None
    data_points: Optional[int] = 1
    confidence_score: Optional[float] = None


class MetricValueResponseSchema(BaseModel):
    """Schema for metric value API response"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    kpi_id: str
    date: date
    timeframe: AnalyticsTimeframe
    value: float
    target: Optional[float] = None
    previous_value: Optional[float] = None
    calculated_at: datetime


class RevenueAnalyticsResponseSchema(BaseModel):
    """Schema for revenue analytics API response"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    period_name: str
    timeframe: AnalyticsTimeframe
    start_date: date
    end_date: date
    total_revenue: Decimal
    quoted_revenue: Decimal
    pipeline_value: Decimal
    projects_completed: int
    projects_in_progress: int
    avg_project_value: Decimal
    gross_profit: Decimal
    gross_margin_pct: float
    revenue_growth_pct: float
    target_achievement_pct: float


class TeamPerformanceResponseSchema(BaseModel):
    """Schema for team performance API response"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    team_member_id: str
    period_name: str
    timeframe: AnalyticsTimeframe
    leads_assigned: int
    leads_contacted: int
    leads_converted: int
    lead_conversion_rate: float
    revenue_generated: Decimal
    avg_deal_size: Decimal
    quota_achievement_pct: float
    performance_score: float
    rank_in_team: Optional[int] = None


# Request Models
class AnalyticsRequest(BaseModel):
    """Base analytics request model"""
    timeframe: AnalyticsTimeframe = AnalyticsTimeframe.MTD
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    filters: Optional[Dict[str, Any]] = None
    group_by: Optional[List[str]] = None


class KPIRequest(AnalyticsRequest):
    """KPI calculation request"""
    kpi_names: Optional[List[str]] = None
    include_trends: bool = True
    include_targets: bool = True
    include_breakdown: bool = False


class RevenueAnalysisRequest(AnalyticsRequest):
    """Revenue analysis request"""
    include_forecast: bool = True
    forecast_months: int = 3
    include_breakdown: bool = True
    include_profitability: bool = True


class TeamPerformanceRequest(AnalyticsRequest):
    """Team performance request"""
    team_member_ids: Optional[List[UUID]] = None
    include_rankings: bool = True
    include_targets: bool = True
    include_activities: bool = True