"""
Stats API Routes - Real Data Aggregation
Provides summary statistics from database
"""
from flask import Blueprint, jsonify
from sqlalchemy import func, case
from datetime import datetime, timedelta
from app.database import get_db
from app.models.lead_sqlalchemy import Lead
from app.models.customer_sqlalchemy import Customer
from app.models.project_sqlalchemy import Project
from app.models.appointment_sqlalchemy import Appointment

stats_bp = Blueprint('stats', __name__, url_prefix='/api/stats')


@stats_bp.route('/summary', methods=['GET'])
def get_summary_stats():
    """
    Get summary statistics for dashboard
    Returns real data aggregated from database
    """
    db = next(get_db())
    try:
        # Current date ranges
        today = datetime.now().date()
        month_start = datetime(today.year, today.month, 1).date()
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)

        # LEADS STATISTICS
        total_leads = db.query(func.count(Lead.id)).scalar() or 0

        # Leads created today
        leads_today = db.query(func.count(Lead.id)).filter(
            func.date(Lead.created_at) == today
        ).scalar() or 0

        # HOT leads (lead_score >= 80)
        hot_leads = db.query(func.count(Lead.id)).filter(
            Lead.lead_score >= 80
        ).scalar() or 0

        # HOT leads created today
        hot_today = db.query(func.count(Lead.id)).filter(
            func.date(Lead.created_at) == today,
            Lead.lead_score >= 80
        ).scalar() or 0

        # CONVERSION RATE
        # Leads that became customers this month
        converted_this_month = db.query(func.count(Customer.id)).filter(
            func.date(Customer.created_at) >= month_start
        ).scalar() or 0

        # Total leads this month
        leads_this_month = db.query(func.count(Lead.id)).filter(
            func.date(Lead.created_at) >= month_start
        ).scalar() or 0

        conversion_rate = (converted_this_month / leads_this_month * 100) if leads_this_month > 0 else 0

        # Conversion rate last month for delta
        converted_last_month = db.query(func.count(Customer.id)).filter(
            func.date(Customer.created_at) >= last_month_start,
            func.date(Customer.created_at) < month_start
        ).scalar() or 0

        leads_last_month = db.query(func.count(Lead.id)).filter(
            func.date(Lead.created_at) >= last_month_start,
            func.date(Lead.created_at) < month_start
        ).scalar() or 0

        conversion_rate_last_month = (converted_last_month / leads_last_month * 100) if leads_last_month > 0 else 0
        conversion_delta = conversion_rate - conversion_rate_last_month

        # PROJECTS STATISTICS
        active_projects = db.query(func.count(Project.id)).filter(
            Project.status.in_(['in_progress', 'scheduled', 'inspection'])
        ).scalar() or 0

        projects_this_month = db.query(func.count(Project.id)).filter(
            func.date(Project.created_at) >= month_start
        ).scalar() or 0

        # REVENUE STATISTICS
        # Sum of project final_amount for completed projects this month
        monthly_revenue = db.query(
            func.coalesce(func.sum(Project.final_amount), 0)
        ).filter(
            func.date(Project.updated_at) >= month_start,
            Project.status == 'completed'
        ).scalar() or 0

        # Revenue last month
        revenue_last_month = db.query(
            func.coalesce(func.sum(Project.final_amount), 0)
        ).filter(
            func.date(Project.updated_at) >= last_month_start,
            func.date(Project.updated_at) < month_start,
            Project.status == 'completed'
        ).scalar() or 0

        revenue_delta = monthly_revenue - revenue_last_month

        # RESPONSE TIME (average in minutes)
        # Use pre-calculated response_time_minutes field
        avg_response_minutes = db.query(
            func.avg(Lead.response_time_minutes)
        ).filter(
            Lead.response_time_minutes.isnot(None)
        ).scalar() or 0

        # CONVERSION FUNNEL DATA
        contacted_leads = db.query(func.count(Lead.id)).filter(
            Lead.status.in_(['contacted', 'qualified', 'negotiation', 'won'])
        ).scalar() or 0

        # Appointments set
        appointments_set = db.query(func.count(Appointment.id)).scalar() or 0

        # Proposals sent (leads in negotiation or won status)
        proposals_sent = db.query(func.count(Lead.id)).filter(
            Lead.status.in_(['quote_sent', 'negotiation', 'won'])
        ).scalar() or 0

        # Closed deals (converted customers)
        closed_deals = db.query(func.count(Customer.id)).scalar() or 0

        # Compile response
        stats = {
            'total_leads': total_leads,
            'leads_today': leads_today,
            'hot_leads': hot_leads,
            'hot_today': hot_today,
            'conversion_rate': round(conversion_rate, 1),
            'conversion_delta': round(conversion_delta, 1),
            'active_projects': active_projects,
            'projects_this_month': projects_this_month,
            'monthly_revenue': float(monthly_revenue),
            'revenue_delta': float(revenue_delta),
            'avg_response_time': round(avg_response_minutes, 1),
            'contacted_leads': contacted_leads,
            'appointments_set': appointments_set,
            'proposals_sent': proposals_sent,
            'closed_deals': closed_deals,
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(stats), 200

    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch statistics',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
    finally:
        db.close()


@stats_bp.route('/kpis', methods=['GET'])
def get_kpis():
    """
    Get key performance indicators
    """
    db = next(get_db())
    try:
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # Lead velocity (leads per day over last 30 days)
        leads_last_30_days = db.query(func.count(Lead.id)).filter(
            func.date(Lead.created_at) >= month_ago
        ).scalar() or 0
        lead_velocity = round(leads_last_30_days / 30, 1)

        # Conversion velocity (customers per day over last 30 days)
        customers_last_30_days = db.query(func.count(Customer.id)).filter(
            func.date(Customer.created_at) >= month_ago
        ).scalar() or 0
        conversion_velocity = round(customers_last_30_days / 30, 1)

        # Average deal size
        avg_deal_size = db.query(
            func.avg(Project.final_amount)
        ).filter(
            Project.status == 'completed'
        ).scalar() or 0

        # Customer lifetime value
        total_customer_value = db.query(
            func.coalesce(func.sum(Project.final_amount), 0)
        ).join(Customer).scalar() or 0

        total_customers = db.query(func.count(Customer.id)).scalar() or 1
        customer_ltv = total_customer_value / total_customers

        kpis = {
            'lead_velocity': lead_velocity,
            'conversion_velocity': conversion_velocity,
            'avg_deal_size': float(avg_deal_size),
            'customer_ltv': float(customer_ltv),
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(kpis), 200

    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch KPIs',
            'message': str(e)
        }), 500
    finally:
        db.close()
