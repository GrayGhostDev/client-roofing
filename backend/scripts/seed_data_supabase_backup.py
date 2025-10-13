#!/usr/bin/env python3
"""
Database Seed Script for iSwitch Roofs CRM
Populates database with realistic test data

Usage:
    python scripts/seed_data.py [OPTIONS]

Options:
    --leads N           Number of leads to seed (default: 100)
    --customers N       Number of customers to seed (default: 50)
    --projects N        Number of projects to seed (default: 75)
    --interactions N    Number of interactions to seed (default: 30)
    --appointments N    Number of appointments to seed (default: 10)
    --partnerships N    Number of partnerships to seed (default: 5)
    --clear-first       Clear existing data before seeding
    --market TYPE       Market type: 'premium' or 'all' (default: all)
"""

import sys
import logging
import random
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_supabase_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Premium market areas (from business strategy docs)
PREMIUM_MARKETS = [
    {"name": "Bloomfield Hills", "zip": "48301", "tier": "ultra_premium", "avg_deal": 50000},
    {"name": "Birmingham", "zip": "48009", "tier": "ultra_premium", "avg_deal": 48000},
    {"name": "Grosse Pointe", "zip": "48236", "tier": "ultra_premium", "avg_deal": 45000},
    {"name": "Troy", "zip": "48084", "tier": "professional", "avg_deal": 28000},
    {"name": "Rochester Hills", "zip": "48309", "tier": "professional", "avg_deal": 26000},
    {"name": "West Bloomfield", "zip": "48322", "tier": "professional", "avg_deal": 27000},
]

# Lead sources (from marketing strategy)
LEAD_SOURCES = [
    {"name": "Google LSA", "cost_per_lead": 75, "conversion_rate": 20},
    {"name": "Facebook Ads", "cost_per_lead": 75, "conversion_rate": 12},
    {"name": "Community Marketing", "cost_per_lead": 17, "conversion_rate": 15},
    {"name": "Insurance Referral", "cost_per_lead": 25, "conversion_rate": 40},
    {"name": "Real Estate Agent", "cost_per_lead": 30, "conversion_rate": 35},
    {"name": "Direct Door Knocking", "cost_per_lead": 100, "conversion_rate": 4},
    {"name": "Website Organic", "cost_per_lead": 10, "conversion_rate": 8},
    {"name": "Nextdoor", "cost_per_lead": 15, "conversion_rate": 18},
]

# First names and last names for realistic data
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson", "Thomas", "Taylor",
    "Moore", "Jackson", "Martin", "Lee", "Thompson", "White", "Harris", "Clark"
]


def generate_phone():
    """Generate realistic phone number"""
    return f"248-{random.randint(200, 999)}-{random.randint(1000, 9999)}"


def generate_email(first_name, last_name):
    """Generate realistic email"""
    domains = ["gmail.com", "yahoo.com", "outlook.com", "icloud.com"]
    return f"{first_name.lower()}.{last_name.lower()}@{random.choice(domains)}"


def clear_existing_data(supabase):
    """Clear all test data before seeding (preserves system data)"""
    logger.info("🗑️  Clearing existing test data...")

    # Order matters due to foreign key constraints
    tables = ['interactions', 'appointments', 'projects', 'partnerships', 'customers', 'leads']

    for table in tables:
        try:
            # Delete all records (Supabase doesn't allow truncate via REST API)
            result = supabase.table(table).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            logger.info(f"   ✅ Cleared {table}")
        except Exception as e:
            logger.warning(f"   ⚠️  Could not clear {table}: {str(e)}")

    logger.info("✅ Existing data cleared")


def seed_leads(supabase, count=100):
    """Seed leads data"""
    logger.info(f"Seeding {count} leads...")

    leads = []
    for i in range(count):
        market = random.choice(PREMIUM_MARKETS)
        source = random.choice(LEAD_SOURCES)
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)

        # Date within last 90 days
        days_ago = random.randint(0, 90)
        created_at = datetime.utcnow() - timedelta(days=days_ago)

        # Temperature based on source conversion rate and time
        if days_ago < 7:
            temp_choices = ["hot"] * 30 + ["warm"] * 50 + ["cold"] * 20
        elif days_ago < 30:
            temp_choices = ["hot"] * 15 + ["warm"] * 40 + ["cold"] * 45
        else:
            temp_choices = ["hot"] * 5 + ["warm"] * 25 + ["cold"] * 70

        temperature = random.choice(temp_choices)

        # Status based on temperature and age
        if temperature == "hot":
            status_choices = ["converted"] * 40 + ["qualified"] * 30 + ["contacted"] * 20 + ["new"] * 10
        elif temperature == "warm":
            status_choices = ["converted"] * 20 + ["qualified"] * 30 + ["contacted"] * 30 + ["new"] * 20
        else:
            status_choices = ["converted"] * 5 + ["qualified"] * 15 + ["contacted"] * 30 + ["lost"] * 30 + ["new"] * 20

        status = random.choice(status_choices)

        # Lead score (0-100)
        base_score = {"hot": 85, "warm": 65, "cold": 35}[temperature]
        lead_score = base_score + random.randint(-15, 15)
        lead_score = max(0, min(100, lead_score))

        # Response time (2-minute target from business docs)
        if status != "new":
            response_time = random.gauss(150, 120)  # Gaussian around 150 seconds
            response_time = max(30, min(600, response_time))  # Clamp to 30s-10min
        else:
            response_time = None

        lead = {
            "first_name": first_name,
            "last_name": last_name,
            "email": generate_email(first_name, last_name),
            "phone": generate_phone(),
            "address": f"{random.randint(100, 9999)} {random.choice(['Oak', 'Maple', 'Pine', 'Cedar'])} {random.choice(['St', 'Ave', 'Dr', 'Ln'])}",
            "city": market["name"],
            "state": "MI",
            "zip_code": market["zip"],
            "source": source["name"],
            "status": status,
            "temperature": temperature,
            "lead_score": lead_score,
            "notes": f"Interested in roof {random.choice(['repair', 'replacement', 'inspection'])}. Property age: ~{random.randint(15, 40)} years.",
            "created_at": created_at.isoformat(),
            "response_time_minutes": round(response_time / 60, 1) if response_time else None,
            "estimated_project_value": market["avg_deal"] + random.randint(-5000, 10000)
        }

        leads.append(lead)

    # Insert in batches of 50
    batch_size = 50
    for i in range(0, len(leads), batch_size):
        batch = leads[i:i+batch_size]
        try:
            supabase.table("leads").insert(batch).execute()
            logger.info(f"✅ Inserted leads {i+1} to {min(i+batch_size, len(leads))}")
        except Exception as e:
            logger.error(f"❌ Failed to insert lead batch: {str(e)}")

    logger.info(f"✅ Seeded {len(leads)} leads")
    return len(leads)


def seed_customers(supabase, count=50):
    """Seed customers data"""
    logger.info(f"Seeding {count} customers...")

    customers = []
    for i in range(count):
        market = random.choice(PREMIUM_MARKETS)
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)

        # Date within last 180 days
        days_ago = random.randint(30, 180)
        created_at = datetime.utcnow() - timedelta(days=days_ago)

        # Lifetime value (multiple projects possible)
        num_projects = random.choices([1, 2, 3], weights=[70, 25, 5])[0]
        lifetime_value = sum(
            market["avg_deal"] + random.randint(-5000, 10000)
            for _ in range(num_projects)
        )

        customer = {
            "first_name": first_name,
            "last_name": last_name,
            "email": generate_email(first_name, last_name),
            "phone": generate_phone(),
            "address": f"{random.randint(100, 9999)} {random.choice(['Oak', 'Maple', 'Pine', 'Cedar'])} {random.choice(['St', 'Ave', 'Dr', 'Ln'])}",
            "city": market["name"],
            "state": "MI",
            "zip_code": market["zip"],
            "tier": market["tier"],
            "lifetime_value": lifetime_value,
            "referral_source": random.choice([
                "Insurance Agent", "Real Estate Agent", "Property Manager",
                "Previous Customer", "Community Marketing", "Google LSA"
            ]),
            "notes": f"Tier: {market['tier']}. {num_projects} project(s) completed.",
            "created_at": created_at.isoformat()
        }

        customers.append(customer)

    # Insert in batches
    batch_size = 50
    for i in range(0, len(customers), batch_size):
        batch = customers[i:i+batch_size]
        try:
            supabase.table("customers").insert(batch).execute()
            logger.info(f"✅ Inserted customers {i+1} to {min(i+batch_size, len(customers))}")
        except Exception as e:
            logger.error(f"❌ Failed to insert customer batch: {str(e)}")

    logger.info(f"✅ Seeded {len(customers)} customers")
    return len(customers)


def seed_projects(supabase, customer_ids, count=75):
    """Seed projects data"""
    logger.info(f"Seeding {count} projects...")

    project_types = [
        "Roof Replacement", "Roof Repair", "Roof Inspection",
        "Gutter Installation", "Siding Repair", "Emergency Repair"
    ]

    projects = []
    for i in range(count):
        customer_id = random.choice(customer_ids)
        market = random.choice(PREMIUM_MARKETS)

        # Date within last 120 days
        days_ago = random.randint(0, 120)
        created_at = datetime.utcnow() - timedelta(days=days_ago)

        # Status based on age
        if days_ago < 30:
            status_choices = ["approved", "in_progress", "quoted", "planning"]
        elif days_ago < 60:
            status_choices = ["in_progress", "completed", "approved"]
        else:
            status_choices = ["completed", "completed", "completed", "cancelled"]

        status = random.choice(status_choices)

        # Quote and actual amounts
        quoted_amount = market["avg_deal"] + random.randint(-5000, 10000)
        actual_amount = quoted_amount if status == "completed" else quoted_amount + random.randint(-2000, 2000)

        # Margin (target: 35-45% from business docs)
        margin = random.uniform(30, 50)

        project = {
            "customer_id": customer_id,
            "project_type": random.choice(project_types),
            "status": status,
            "quoted_amount": quoted_amount,
            "actual_amount": actual_amount if status == "completed" else None,
            "margin_percentage": margin,
            "start_date": (created_at + timedelta(days=random.randint(7, 21))).isoformat() if status in ["in_progress", "completed"] else None,
            "completion_date": (created_at + timedelta(days=random.randint(30, 60))).isoformat() if status == "completed" else None,
            "notes": f"Premium market: {market['name']}. Project type: {random.choice(project_types)}.",
            "created_at": created_at.isoformat()
        }

        projects.append(project)

    # Insert in batches
    batch_size = 50
    for i in range(0, len(projects), batch_size):
        batch = projects[i:i+batch_size]
        try:
            supabase.table("projects").insert(batch).execute()
            logger.info(f"✅ Inserted projects {i+1} to {min(i+batch_size, len(projects))}")
        except Exception as e:
            logger.error(f"❌ Failed to insert project batch: {str(e)}")

    logger.info(f"✅ Seeded {len(projects)} projects")
    return len(projects)


def seed_interactions(supabase, lead_ids, customer_ids, count=30):
    """Seed interactions data"""
    logger.info(f"Seeding {count} interactions...")

    interaction_types = ["call", "email", "meeting", "note", "text"]

    interactions = []
    for i in range(count):
        # 60% linked to leads, 40% to customers
        if random.random() < 0.6 and lead_ids:
            entity_type = "lead"
            entity_id = random.choice(lead_ids)
        elif customer_ids:
            entity_type = "customer"
            entity_id = random.choice(customer_ids)
        else:
            continue

        # Date within last 60 days
        days_ago = random.randint(0, 60)
        created_at = datetime.utcnow() - timedelta(days=days_ago)

        interaction_type = random.choice(interaction_types)

        # Generate realistic content
        subjects = [
            "Initial contact - discussed roofing needs",
            "Follow-up call - answered questions",
            "Site visit scheduled",
            "Quote discussion",
            "Insurance claim assistance",
            "Material selection meeting",
            "Project timeline review",
            "Final walkthrough scheduled"
        ]

        # 40% have follow-up dates
        has_followup = random.random() < 0.4
        follow_up_date = (datetime.utcnow() + timedelta(days=random.randint(1, 14))).isoformat() if has_followup else None

        interaction = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "interaction_type": interaction_type,
            "subject": random.choice(subjects),
            "content": f"Detailed notes from {interaction_type}. Customer engagement: {random.choice(['high', 'medium', 'low'])}",
            "follow_up_date": follow_up_date,
            "created_at": created_at.isoformat()
        }

        interactions.append(interaction)

    # Insert in batches
    batch_size = 50
    for i in range(0, len(interactions), batch_size):
        batch = interactions[i:i+batch_size]
        try:
            supabase.table("interactions").insert(batch).execute()
            logger.info(f"✅ Inserted interactions {i+1} to {min(i+batch_size, len(interactions))}")
        except Exception as e:
            logger.error(f"❌ Failed to insert interaction batch: {str(e)}")

    logger.info(f"✅ Seeded {len(interactions)} interactions ({sum(1 for i in interactions if i['follow_up_date']) } with follow-ups)")
    return len(interactions)


def seed_appointments(supabase, lead_ids, customer_ids, project_ids, count=10):
    """Seed appointments data"""
    logger.info(f"Seeding {count} appointments...")

    appointment_types = ["consultation", "inspection", "estimate", "project_work", "follow_up"]

    appointments = []
    for i in range(count):
        # Distribute across entities
        entity_choice = random.random()
        if entity_choice < 0.4 and lead_ids:
            entity_type = "lead"
            entity_id = random.choice(lead_ids)
        elif entity_choice < 0.7 and customer_ids:
            entity_type = "customer"
            entity_id = random.choice(customer_ids)
        elif project_ids:
            entity_type = "project"
            entity_id = random.choice(project_ids)
        else:
            continue

        # 60% upcoming, 40% past
        is_upcoming = random.random() < 0.6

        if is_upcoming:
            # Schedule within next 30 days
            days_ahead = random.randint(1, 30)
            scheduled_date = datetime.utcnow() + timedelta(days=days_ahead)
            status = random.choice(["scheduled", "confirmed"])
        else:
            # Past appointments
            days_ago = random.randint(1, 60)
            scheduled_date = datetime.utcnow() - timedelta(days=days_ago)
            status = random.choice(["completed", "completed", "completed", "cancelled"])

        appointment_type = random.choice(appointment_types)
        duration = random.choice([30, 60, 90, 120])

        appointment = {
            "title": f"{appointment_type.replace('_', ' ').title()} - {entity_type.title()} #{i+1}",
            "description": f"Scheduled {appointment_type} for property assessment",
            "appointment_type": appointment_type,
            "scheduled_date": scheduled_date.isoformat(),
            "duration_minutes": duration,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "status": status,
            "created_at": (scheduled_date - timedelta(days=random.randint(1, 5))).isoformat()
        }

        appointments.append(appointment)

    # Insert in batches
    batch_size = 50
    for i in range(0, len(appointments), batch_size):
        batch = appointments[i:i+batch_size]
        try:
            supabase.table("appointments").insert(batch).execute()
            logger.info(f"✅ Inserted appointments {i+1} to {min(i+batch_size, len(appointments))}")
        except Exception as e:
            logger.error(f"❌ Failed to insert appointment batch: {str(e)}")

    upcoming_count = sum(1 for a in appointments if a['status'] in ['scheduled', 'confirmed'])
    completed_count = sum(1 for a in appointments if a['status'] == 'completed')

    logger.info(f"✅ Seeded {len(appointments)} appointments ({upcoming_count} upcoming, {completed_count} completed)")
    return len(appointments)


def seed_partnerships(supabase, count=5):
    """Seed partnerships data"""
    logger.info(f"Seeding {count} partnerships...")

    partnership_types = ["insurance_agent", "real_estate_agent", "property_manager", "contractor", "supplier"]

    partnership_names = [
        "State Farm - John Anderson",
        "Keller Williams - Sarah Miller",
        "ABC Property Management",
        "Quality Contractors Inc",
        "Premium Building Supply Co"
    ]

    partnerships = []
    for i in range(count):
        # Date within last 12 months
        months_ago = random.randint(0, 12)
        created_at = datetime.utcnow() - timedelta(days=months_ago * 30)

        # Generate referral stats based on partnership age
        partnership_age_months = months_ago
        base_referrals = partnership_age_months * random.randint(2, 8)
        referral_count = base_referrals + random.randint(-5, 15)
        referral_count = max(0, referral_count)

        # Revenue from referrals
        avg_deal = random.choice([25000, 30000, 35000, 40000, 45000])
        total_revenue = referral_count * avg_deal * random.uniform(0.6, 0.9)

        partnership = {
            "name": partnership_names[i] if i < len(partnership_names) else f"Partner {i+1}",
            "partnership_type": partnership_types[i] if i < len(partnership_types) else random.choice(partnership_types),
            "contact_email": f"partner{i+1}@example.com",
            "contact_phone": generate_phone(),
            "status": "active" if random.random() < 0.8 else "inactive",
            "referral_count": referral_count,
            "total_revenue_generated": int(total_revenue),
            "commission_rate": random.uniform(5, 15),
            "notes": f"Partnership established {partnership_age_months} months ago. Generating {referral_count} referrals",
            "created_at": created_at.isoformat()
        }

        partnerships.append(partnership)

    # Insert all partnerships
    try:
        supabase.table("partnerships").insert(partnerships).execute()
        logger.info(f"✅ Inserted {len(partnerships)} partnerships")
    except Exception as e:
        logger.error(f"❌ Failed to insert partnerships: {str(e)}")

    total_referrals = sum(p['referral_count'] for p in partnerships)
    total_revenue = sum(p['total_revenue_generated'] for p in partnerships)

    logger.info(f"✅ Seeded {len(partnerships)} partnerships ({total_referrals} total referrals, ${total_revenue:,} revenue)")
    return len(partnerships)


def main():
    """Main seeding function"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Seed iSwitch Roofs CRM database with realistic test data')
    parser.add_argument('--leads', type=int, default=100, help='Number of leads to seed (default: 100)')
    parser.add_argument('--customers', type=int, default=50, help='Number of customers to seed (default: 50)')
    parser.add_argument('--projects', type=int, default=75, help='Number of projects to seed (default: 75)')
    parser.add_argument('--interactions', type=int, default=30, help='Number of interactions to seed (default: 30)')
    parser.add_argument('--appointments', type=int, default=10, help='Number of appointments to seed (default: 10)')
    parser.add_argument('--partnerships', type=int, default=5, help='Number of partnerships to seed (default: 5)')
    parser.add_argument('--clear-first', action='store_true', help='Clear existing data before seeding')
    parser.add_argument('--market', choices=['premium', 'all'], default='all', help='Market type to focus on')

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("iSwitch Roofs CRM - Database Seeding")
    logger.info("=" * 60)
    logger.info(f"Configuration:")
    logger.info(f"   Leads: {args.leads}")
    logger.info(f"   Customers: {args.customers}")
    logger.info(f"   Projects: {args.projects}")
    logger.info(f"   Interactions: {args.interactions}")
    logger.info(f"   Appointments: {args.appointments}")
    logger.info(f"   Partnerships: {args.partnerships}")
    logger.info(f"   Market: {args.market}")
    logger.info(f"   Clear existing: {args.clear_first}")
    logger.info("=" * 60)

    try:
        supabase = get_supabase_client()

        # Clear existing data if requested
        if args.clear_first:
            clear_existing_data(supabase)

        # Filter markets if premium-only
        global PREMIUM_MARKETS
        if args.market == 'premium':
            PREMIUM_MARKETS = [m for m in PREMIUM_MARKETS if m['tier'] == 'ultra_premium']
            logger.info(f"📍 Using premium markets only: {[m['name'] for m in PREMIUM_MARKETS]}")

        # Seed partnerships first (needed for lead attribution)
        partnerships_count = seed_partnerships(supabase, count=args.partnerships)

        # Seed leads
        leads_count = seed_leads(supabase, count=args.leads)

        # Get lead IDs for relationships
        leads_result = supabase.table("leads").select("id").execute()
        lead_ids = [l["id"] for l in leads_result.data] if leads_result.data else []

        # Seed customers
        customers_count = seed_customers(supabase, count=args.customers)

        # Get customer IDs for projects
        customers_result = supabase.table("customers").select("id").execute()
        customer_ids = [c["id"] for c in customers_result.data] if customers_result.data else []

        # Seed projects
        if customer_ids:
            projects_count = seed_projects(supabase, customer_ids, count=args.projects)
        else:
            logger.warning("⚠️  No customers found, skipping projects")
            projects_count = 0

        # Get project IDs for appointments
        projects_result = supabase.table("projects").select("id").execute()
        project_ids = [p["id"] for p in projects_result.data] if projects_result.data else []

        # Seed interactions
        interactions_count = seed_interactions(supabase, lead_ids, customer_ids, count=args.interactions)

        # Seed appointments
        appointments_count = seed_appointments(supabase, lead_ids, customer_ids, project_ids, count=args.appointments)

        logger.info("=" * 60)
        logger.info("✅ Database seeding completed successfully!")
        logger.info("=" * 60)
        logger.info(f"   Partnerships: {partnerships_count}")
        logger.info(f"   Leads: {leads_count}")
        logger.info(f"   Customers: {customers_count}")
        logger.info(f"   Projects: {projects_count}")
        logger.info(f"   Interactions: {interactions_count}")
        logger.info(f"   Appointments: {appointments_count}")
        logger.info("")
        logger.info("📊 You can now start the backend and Streamlit dashboard!")
        logger.info("")

    except Exception as e:
        logger.error(f"❌ Database seeding failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
