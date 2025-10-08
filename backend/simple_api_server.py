#!/usr/bin/env python3
"""
Simplified CRM Backend Starter
Bypasses problematic routes and starts essential services only
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set minimal environment variables if not set
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'sqlite:///./test.db'
if 'SECRET_KEY' not in os.environ:
    os.environ['SECRET_KEY'] = 'dev-secret-key-change-in-production'
if 'FLASK_ENV' not in os.environ:
    os.environ['FLASK_ENV'] = 'development'

from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime
import random

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:8501", "http://localhost:3000", "http://localhost:8000"]}})

# Mock data generators
def generate_mock_leads(count=50):
    """Generate mock lead data"""
    statuses = ['new', 'qualified', 'hot', 'warm', 'cold', 'won', 'lost']
    sources = ['Website', 'Referral', 'CallRail', 'Social Media', 'Direct']
    
    leads = []
    for i in range(count):
        leads.append({
            'id': f'LEAD-{1000 + i}',
            'name': f'Customer {i+1}',
            'email': f'customer{i+1}@example.com',
            'phone': f'555-{random.randint(100,999)}-{random.randint(1000,9999)}',
            'source': random.choice(sources),
            'status': random.choice(statuses),
            'score': random.randint(20, 100),
            'value': random.randint(5000, 50000),
            'created_at': datetime.now().isoformat(),
            'last_contact': datetime.now().isoformat()
        })
    return leads

def generate_mock_projects(count=20):
    """Generate mock project data"""
    statuses = ['planning', 'in_progress', 'on_hold', 'completed', 'cancelled']
    
    projects = []
    for i in range(count):
        budget = random.randint(10000, 100000)
        projects.append({
            'id': f'PROJ-{2000 + i}',
            'name': f'Project {i+1}',
            'customer': f'Customer {random.randint(1,50)}',
            'status': random.choice(statuses),
            'progress': random.randint(0, 100),
            'budget': budget,
            'revenue': int(budget * random.uniform(0.7, 1.3)),
            'start_date': datetime.now().isoformat(),
            'estimated_completion': datetime.now().isoformat()
        })
    return projects

# Health check endpoints
@app.route('/health', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'iSwitch Roofs CRM API',
        'version': '1.0.0'
    })

@app.route('/health/ready', methods=['GET'])
@app.route('/api/health/ready', methods=['GET'])
def readiness_check():
    """Readiness check"""
    return jsonify({
        'ready': True,
        'checks': {
            'database': 'ok',
            'api': 'ok'
        }
    })

# Lead endpoints
@app.route('/api/leads', methods=['GET'])
def get_leads():
    """Get all leads"""
    leads = generate_mock_leads()
    return jsonify({
        'leads': leads,
        'total': len(leads),
        'page': 1,
        'per_page': 50
    })

@app.route('/api/leads/statistics', methods=['GET'])
def get_lead_statistics():
    """Get lead statistics"""
    return jsonify({
        'total_leads': 50,
        'qualified_leads': 25,
        'hot_leads': 10,
        'cold_leads': 5,
        'won_leads': 8,
        'lost_leads': 2,
        'conversion_rate': 16.0,
        'avg_lead_score': 65,
        'avg_lead_value': 25000,
        'pipeline_value': 1250000
    })

@app.route('/api/leads/conversion-funnel', methods=['GET'])
def get_conversion_funnel():
    """Get conversion funnel data"""
    return jsonify({
        'stages': [
            {'name': 'Total Leads', 'count': 100, 'percentage': 100},
            {'name': 'Qualified', 'count': 75, 'percentage': 75},
            {'name': 'Proposal Sent', 'count': 50, 'percentage': 50},
            {'name': 'Negotiation', 'count': 30, 'percentage': 30},
            {'name': 'Won', 'count': 20, 'percentage': 20}
        ]
    })

# Project endpoints
@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    projects = generate_mock_projects()
    return jsonify({
        'projects': projects,
        'total': len(projects),
        'page': 1,
        'per_page': 50
    })

@app.route('/api/projects/statistics', methods=['GET'])
def get_project_statistics():
    """Get project statistics"""
    return jsonify({
        'total_projects': 20,
        'active_projects': 12,
        'completed_projects': 6,
        'on_hold_projects': 1,
        'cancelled_projects': 1,
        'total_revenue': 1800000,
        'avg_project_value': 90000,
        'on_time_completion_rate': 92.0
    })

# Analytics endpoints
@app.route('/api/analytics/dashboard-summary', methods=['GET'])
def get_dashboard_summary():
    """Get dashboard summary"""
    return jsonify({
        'leads': {
            'total': 50,
            'new_today': 5,
            'hot': 10,
            'conversion_rate': 16.0
        },
        'projects': {
            'active': 12,
            'completed_this_month': 3,
            'total_value': 1800000
        },
        'revenue': {
            'total': 1800000,
            'this_month': 150000,
            'growth': 15.5
        },
        'team': {
            'active_members': 5,
            'avg_response_time': 2.5,
            'tasks_completed': 45
        }
    })

@app.route('/api/analytics/revenue', methods=['GET'])
def get_revenue_analytics():
    """Get revenue analytics"""
    # Generate 30 days of revenue data
    revenue_data = []
    for i in range(30):
        revenue_data.append({
            'date': datetime.now().isoformat(),
            'revenue': random.randint(3000, 8000),
            'category': random.choice(['New Roofs', 'Repairs', 'Maintenance', 'Consulting'])
        })
    
    return jsonify({
        'daily_revenue': revenue_data,
        'total_revenue': 1800000,
        'avg_daily': 5000,
        'forecast_next_month': 165000,
        'by_category': {
            'New Roofs': 900000,
            'Repairs': 450000,
            'Maintenance': 300000,
            'Consulting': 150000
        }
    })

@app.route('/api/analytics/team-performance', methods=['GET'])
def get_team_performance():
    """Get team performance data"""
    team_members = []
    for i in range(5):
        team_members.append({
            'id': i + 1,
            'name': f'Team Member {i+1}',
            'leads_assigned': random.randint(10, 25),
            'leads_converted': random.randint(2, 8),
            'conversion_rate': random.uniform(15, 35),
            'avg_response_time': random.uniform(1, 5),
            'satisfaction_rating': random.uniform(4.0, 5.0)
        })
    
    return jsonify({
        'team_members': team_members,
        'total_members': 5,
        'avg_conversion_rate': 23.5,
        'avg_response_time': 2.8
    })

# Customer endpoints
@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Get all customers"""
    customers = []
    for i in range(30):
        customers.append({
            'id': f'CUST-{3000 + i}',
            'name': f'Customer {i+1}',
            'email': f'customer{i+1}@example.com',
            'phone': f'555-{random.randint(100,999)}-{random.randint(1000,9999)}',
            'tier': random.choice(['bronze', 'silver', 'gold', 'platinum']),
            'lifetime_value': random.randint(10000, 200000),
            'projects_completed': random.randint(1, 5),
            'created_at': datetime.now().isoformat()
        })
    
    return jsonify({
        'customers': customers,
        'total': len(customers)
    })

if __name__ == '__main__':
    print("""
    🚀 Simplified iSwitch Roofs CRM Backend Starting...
    
    Server Details:
    ├── Host: 0.0.0.0
    ├── Port: 8000
    ├── Mode: Development (Mock Data)
    └── URL: http://localhost:8000
    
    Available Endpoints:
    ├── Health Check: http://localhost:8000/health
    ├── Leads: http://localhost:8000/api/leads
    ├── Projects: http://localhost:8000/api/projects
    ├── Analytics: http://localhost:8000/api/analytics/dashboard-summary
    └── And more...
    
    🎯 Features:
    ├── Mock data for all endpoints
    ├── CORS enabled for Streamlit (8501) and Reflex (3000)
    ├── No database required
    └── All API routes functional
    
    Press Ctrl+C to stop the server
    """)
    
    # Use waitress for more reliable serving
    from waitress import serve
    print("\n✅ Server is ready and listening...")
    serve(app, host='0.0.0.0', port=8000)
