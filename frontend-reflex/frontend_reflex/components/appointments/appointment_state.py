"""Appointment state management and sample data for the complete appointments system."""

import reflex as rx
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta, calendar
import json

# Sample appointment data for demonstration
SAMPLE_APPOINTMENTS = [
    {
        "id": "apt_001",
        "title": "Roof Inspection - Smith Residence",
        "description": "Annual roof inspection for insurance compliance",
        "appointment_type": "inspection",
        "status": "confirmed",
        "scheduled_date": "2024-10-10T09:00:00",
        "duration_minutes": 90,
        "end_time": "10:30",
        "entity_type": "customer",
        "entity_id": "cust_001",
        "assigned_to": "John Mitchell",
        "location": "123 Oak Street, Troy, MI 48084",
        "is_virtual": False,
        "meeting_url": None,
        "preparation_notes": "Bring ladder, drone camera, inspection checklist",
        "outcome_notes": None,
        "reminder_sent": True,
        "confirmed_by_customer": True,
        "created_at": "2024-10-05T14:30:00",
        "updated_at": "2024-10-06T10:15:00"
    },
    {
        "id": "apt_002",
        "title": "Roofing Estimate - Johnson Property",
        "description": "Storm damage assessment and repair estimate",
        "appointment_type": "estimate",
        "status": "scheduled",
        "scheduled_date": "2024-10-11T14:00:00",
        "duration_minutes": 60,
        "end_time": "15:00",
        "entity_type": "lead",
        "entity_id": "lead_001",
        "assigned_to": "Sarah Connor",
        "location": "456 Maple Ave, Birmingham, MI 48009",
        "is_virtual": False,
        "meeting_url": None,
        "preparation_notes": "Review insurance photos, bring estimate forms",
        "outcome_notes": None,
        "reminder_sent": False,
        "confirmed_by_customer": False,
        "created_at": "2024-10-05T16:45:00",
        "updated_at": "2024-10-05T16:45:00"
    },
    {
        "id": "apt_003",
        "title": "Virtual Consultation - Davis Condo",
        "description": "Initial consultation for flat roof replacement",
        "appointment_type": "consultation",
        "status": "confirmed",
        "scheduled_date": "2024-10-09T11:00:00",
        "duration_minutes": 30,
        "end_time": "11:30",
        "entity_type": "lead",
        "entity_id": "lead_002",
        "assigned_to": "Mike Rodriguez",
        "location": None,
        "is_virtual": True,
        "meeting_url": "https://zoom.us/j/1234567890",
        "preparation_notes": "Prepare condo roofing portfolio, cost estimates",
        "outcome_notes": None,
        "reminder_sent": True,
        "confirmed_by_customer": True,
        "created_at": "2024-10-04T09:20:00",
        "updated_at": "2024-10-06T15:30:00"
    },
    {
        "id": "apt_004",
        "title": "Gutter Installation - Wilson House",
        "description": "Install seamless gutters and downspouts",
        "appointment_type": "installation",
        "status": "in_progress",
        "scheduled_date": "2024-10-08T08:00:00",
        "duration_minutes": 240,
        "end_time": "12:00",
        "entity_type": "customer",
        "entity_id": "cust_002",
        "assigned_to": "Installation Team A",
        "location": "789 Pine Street, Rochester Hills, MI 48307",
        "is_virtual": False,
        "meeting_url": None,
        "preparation_notes": "All materials on site, weather looks good",
        "outcome_notes": "Started on time, 50% complete",
        "reminder_sent": True,
        "confirmed_by_customer": True,
        "created_at": "2024-09-25T10:00:00",
        "updated_at": "2024-10-08T10:30:00"
    },
    {
        "id": "apt_005",
        "title": "Follow-up Visit - Brown Residence",
        "description": "Check warranty work completed last month",
        "appointment_type": "follow_up",
        "status": "completed",
        "scheduled_date": "2024-10-07T13:00:00",
        "duration_minutes": 30,
        "end_time": "13:30",
        "entity_type": "customer",
        "entity_id": "cust_003",
        "assigned_to": "John Mitchell",
        "location": "321 Cedar Lane, West Bloomfield, MI 48322",
        "is_virtual": False,
        "meeting_url": None,
        "preparation_notes": "Review warranty work photos",
        "outcome_notes": "Customer satisfied, no issues found",
        "reminder_sent": True,
        "confirmed_by_customer": True,
        "created_at": "2024-10-01T11:00:00",
        "updated_at": "2024-10-07T13:45:00"
    }
]

# Sample customer data
SAMPLE_CUSTOMERS = [
    {
        "id": "cust_001",
        "first_name": "Robert",
        "last_name": "Smith",
        "phone": "(248) 555-0123",
        "email": "robert.smith@email.com",
        "address": "123 Oak Street, Troy, MI 48084",
        "property_type": "residential",
        "created_at": "2024-01-15T10:00:00",
        "lifetime_value": 15600.00,
        "total_projects": 2,
        "last_project_date": "2024-08-15",
        "customer_status": "active",
        "notes": "Prefers morning appointments, has two dogs"
    },
    {
        "id": "cust_002",
        "first_name": "Lisa",
        "last_name": "Wilson",
        "phone": "(248) 555-0456",
        "email": "lisa.wilson@email.com",
        "address": "789 Pine Street, Rochester Hills, MI 48307",
        "property_type": "residential",
        "created_at": "2024-03-22T14:30:00",
        "lifetime_value": 8900.00,
        "total_projects": 1,
        "last_project_date": "2024-09-10",
        "customer_status": "active",
        "notes": "New customer, very detail-oriented"
    }
]

# Sample team members
SAMPLE_TEAM_MEMBERS = [
    {
        "id": "team_001",
        "name": "John Mitchell",
        "initials": "JM",
        "role": "Lead Inspector",
        "status": "available",
        "appointments_today": 2,
        "email": "john.mitchell@iswitchroofs.com"
    },
    {
        "id": "team_002",
        "name": "Sarah Connor",
        "initials": "SC",
        "role": "Sales Estimator",
        "status": "busy",
        "appointments_today": 4,
        "email": "sarah.connor@iswitchroofs.com"
    },
    {
        "id": "team_003",
        "name": "Mike Rodriguez",
        "initials": "MR",
        "role": "Project Manager",
        "status": "available",
        "appointments_today": 1,
        "email": "mike.rodriguez@iswitchroofs.com"
    },
    {
        "id": "team_004",
        "name": "Installation Team A",
        "initials": "TA",
        "role": "Installation Crew",
        "status": "busy",
        "appointments_today": 1,
        "email": "team-a@iswitchroofs.com"
    }
]

# Sample appointment alerts
SAMPLE_APPOINTMENT_ALERTS = [
    {
        "id": "alert_001",
        "type": "confirmation",
        "priority": "high",
        "message": "Johnson Property estimate needs confirmation (2 days overdue)",
        "time": "2 hours ago",
        "appointment_id": "apt_002"
    },
    {
        "id": "alert_002",
        "type": "reminder",
        "priority": "medium",
        "message": "Send reminder for Smith inspection tomorrow",
        "time": "30 minutes ago",
        "appointment_id": "apt_001"
    }
]

# Sample time slots for scheduling
def generate_time_slots():
    """Generate available time slots for appointment scheduling."""
    slots = []
    start_hour = 8  # 8 AM
    end_hour = 17   # 5 PM

    for hour in range(start_hour, end_hour):
        for minute in [0, 30]:  # 30-minute intervals
            time_str = f"{hour:02d}:{minute:02d}"
            slots.append(time_str)

    return slots

# Business hours for calendar display
BUSINESS_HOURS = [f"{h:02d}:00" for h in range(8, 18)]  # 8 AM to 6 PM

class AppointmentStateExtension:
    """Extension methods for appointment state management."""

    @staticmethod
    def get_sample_appointments():
        """Return sample appointments data."""
        return SAMPLE_APPOINTMENTS

    @staticmethod
    def get_sample_customers():
        """Return sample customers data."""
        return SAMPLE_CUSTOMERS

    @staticmethod
    def get_sample_team_members():
        """Return sample team members data."""
        return SAMPLE_TEAM_MEMBERS

    @staticmethod
    def get_sample_alerts():
        """Return sample appointment alerts."""
        return SAMPLE_APPOINTMENT_ALERTS

    @staticmethod
    def get_time_slots():
        """Return available time slots."""
        return generate_time_slots()

    @staticmethod
    def get_business_hours():
        """Return business hours."""
        return BUSINESS_HOURS

    @staticmethod
    def filter_appointments_by_date(appointments, target_date):
        """Filter appointments by specific date."""
        filtered = []
        for apt in appointments:
            apt_date = apt["scheduled_date"].split('T')[0] if 'T' in apt["scheduled_date"] else apt["scheduled_date"]
            if apt_date == target_date:
                filtered.append(apt)
        return filtered

    @staticmethod
    def filter_appointments_by_status(appointments, status):
        """Filter appointments by status."""
        if status == "all":
            return appointments
        return [apt for apt in appointments if apt["status"] == status]

    @staticmethod
    def filter_appointments_by_type(appointments, appointment_type):
        """Filter appointments by type."""
        if appointment_type == "all":
            return appointments
        return [apt for apt in appointments if apt["appointment_type"] == appointment_type]

    @staticmethod
    def get_calendar_days_for_month(year, month):
        """Generate calendar days for month view."""
        cal = calendar.monthcalendar(year, month)
        today = datetime.now().date()

        days = []
        for week in cal:
            for day in week:
                if day == 0:
                    continue

                date_obj = datetime(year, month, day).date()
                is_today = date_obj == today
                is_other_month = False  # Since we're in the target month

                # Get appointments for this day
                date_str = date_obj.strftime("%Y-%m-%d")
                day_appointments = AppointmentStateExtension.filter_appointments_by_date(
                    SAMPLE_APPOINTMENTS, date_str
                )

                days.append({
                    "date": str(day),
                    "full_date": date_str,
                    "is_today": is_today,
                    "is_other_month": is_other_month,
                    "appointments": day_appointments
                })

        return days

    @staticmethod
    def get_week_days(start_date):
        """Generate week days for week view."""
        days = []
        for i in range(7):  # 7 days in a week
            date_obj = start_date + timedelta(days=i)
            date_str = date_obj.strftime("%Y-%m-%d")

            # Get appointments for this day
            day_appointments = AppointmentStateExtension.filter_appointments_by_date(
                SAMPLE_APPOINTMENTS, date_str
            )

            # Generate hour slots with appointments
            hour_slots = []
            for hour in range(8, 18):  # Business hours
                hour_appointments = [
                    apt for apt in day_appointments
                    if apt["scheduled_date"].split('T')[1][:2] == f"{hour:02d}" if 'T' in apt["scheduled_date"]
                ]

                hour_slots.append({
                    "datetime": f"{date_str}T{hour:02d}:00:00",
                    "appointments": hour_appointments
                })

            days.append({
                "day_name": date_obj.strftime("%a"),
                "date": date_str,
                "is_today": date_obj.date() == datetime.now().date(),
                "hour_slots": hour_slots
            })

        return days

    @staticmethod
    def get_appointment_counts():
        """Get appointment counts for dashboard widgets."""
        today = datetime.now().date().strftime("%Y-%m-%d")
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).date().strftime("%Y-%m-%d")
        week_end = (datetime.now() + timedelta(days=6-datetime.now().weekday())).date().strftime("%Y-%m-%d")
        month_start = datetime.now().replace(day=1).date().strftime("%Y-%m-%d")

        # Count today's appointments
        todays_count = len(AppointmentStateExtension.filter_appointments_by_date(SAMPLE_APPOINTMENTS, today))

        # Count this week's appointments
        week_count = 0
        for apt in SAMPLE_APPOINTMENTS:
            apt_date = apt["scheduled_date"].split('T')[0] if 'T' in apt["scheduled_date"] else apt["scheduled_date"]
            if week_start <= apt_date <= week_end:
                week_count += 1

        # Count pending confirmations
        pending_count = len([apt for apt in SAMPLE_APPOINTMENTS if not apt["confirmed_by_customer"]])

        # Count completed this month
        completed_count = 0
        for apt in SAMPLE_APPOINTMENTS:
            apt_date = apt["scheduled_date"].split('T')[0] if 'T' in apt["scheduled_date"] else apt["scheduled_date"]
            if apt_date >= month_start and apt["status"] == "completed":
                completed_count += 1

        return {
            "today": todays_count,
            "week": week_count,
            "pending": pending_count,
            "completed": completed_count
        }

# You can extend the main AppState with these methods by adding them to state.py
# These are helper functions and sample data for the appointment system