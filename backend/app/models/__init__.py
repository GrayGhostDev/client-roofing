"""
SQLAlchemy Models Package

Import all models here to ensure they are registered with SQLAlchemy
"""

from app.models.alert_sqlalchemy import Alert
from app.models.analytics_sqlalchemy import (
    BusinessAlert,
    ConversionFunnel,
    CustomerAnalytics,
    KPIDefinition,
    MarketingAnalytics,
    MetricValue,
    RevenueAnalytics,
    TeamPerformance,
)
from app.models.appointment_sqlalchemy import Appointment
from app.models.base import Base, BaseModel
from app.models.customer_sqlalchemy import Customer
from app.models.interaction_sqlalchemy import Interaction

# SQLAlchemy models (properly converted)
from app.models.lead_sqlalchemy import Lead
from app.models.notification_sqlalchemy import Notification, NotificationTemplate
from app.models.partnership_sqlalchemy import Partnership
from app.models.project_sqlalchemy import Project
from app.models.review_sqlalchemy import Review
from app.models.team_sqlalchemy import TeamMember

__all__ = [
    "Base",
    "BaseModel",
    "Lead",
    "Customer",
    "Project",
    "Appointment",
    "TeamMember",
    "Interaction",
    "Review",
    "Partnership",
    "Notification",
    "NotificationTemplate",
    "Alert",
    "KPIDefinition",
    "MetricValue",
    "ConversionFunnel",
    "RevenueAnalytics",
    "CustomerAnalytics",
    "TeamPerformance",
    "MarketingAnalytics",
    "BusinessAlert",
]
