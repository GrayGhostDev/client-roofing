#!/usr/bin/env python3
"""
Local PostgreSQL Database Seed Script for iSwitch Roofs CRM
Populates database with realistic test data

Usage:
    python scripts/seed_local_postgres.py [OPTIONS]

Options:
    --leads N           Number of leads to seed (default: 50)
    --clear-first       Clear existing data before seeding
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

from app.database import SessionLocal
from app.models.lead_sqlalchemy import Lead
from app.models.lead_schemas import LeadSource, LeadStatus, LeadTemperature

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
LEAD_SOURCES_DATA = [
    {"source": LeadSource.GOOGLE_LSA, "cost_per_lead": 75, "conversion_rate": 20, "weight": 0.25},
    {"source": LeadSource.FACEBOOK_ADS, "cost_per_lead": 75, "conversion_rate": 12, "weight": 0.20},
    {"source": LeadSource.REFERRAL, "cost_per_lead": 25, "conversion_rate": 40, "weight": 0.15},
    {"source": LeadSource.WEBSITE_FORM, "cost_per_lead": 10, "conversion_rate": 8, "weight": 0.15},
    {"source": LeadSource.PARTNER_REFERRAL, "cost_per_lead": 15, "conversion_rate": 18, "weight": 0.10},
    {"source": LeadSource.GOOGLE_ADS, "cost_per_lead": 80, "conversion_rate": 15, "weight": 0.10},
    {"source": LeadSource.DOOR_TO_DOOR, "cost_per_lead": 65, "conversion_rate": 10, "weight": 0.05},
]

# First names and last names for realistic data
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley"
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
    domains = ["gmail.com", "yahoo.com", "outlook.com", "icloud.com", "me.com"]
    return f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99)}@{random.choice(domains)}"


def get_weighted_source():
    """Get random lead source based on weights"""
    sources = [s["source"] for s in LEAD_SOURCES_DATA]
    weights = [s["weight"] for s in LEAD_SOURCES_DATA]
    return random.choices(sources, weights=weights, k=1)[0]


def generate_lead(market=None):
    """Generate a single lead with realistic data"""
    if market is None:
        market = random.choice(PREMIUM_MARKETS)

    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    source = get_weighted_source()

    # Generate realistic lead temperature based on source
    source_quality = {
        LeadSource.REFERRAL: [LeadTemperature.HOT] * 60 + [LeadTemperature.WARM] * 30 + [LeadTemperature.COLD] * 10,
        LeadSource.GOOGLE_LSA: [LeadTemperature.HOT] * 40 + [LeadTemperature.WARM] * 50 + [LeadTemperature.COLD] * 10,
        LeadSource.FACEBOOK_ADS: [LeadTemperature.HOT] * 20 + [LeadTemperature.WARM] * 50 + [LeadTemperature.COLD] * 30,
        LeadSource.WEBSITE_FORM: [LeadTemperature.HOT] * 15 + [LeadTemperature.WARM] * 45 + [LeadTemperature.COLD] * 40,
    }

    temp_options = source_quality.get(source, [LeadTemperature.WARM] * 50 + [LeadTemperature.COLD] * 50)
    temperature = random.choice(temp_options)

    # Status distribution
    statuses = [
        (LeadStatus.NEW, 0.30),
        (LeadStatus.CONTACTED, 0.25),
        (LeadStatus.QUALIFIED, 0.20),
        (LeadStatus.PROPOSAL, 0.15),
        (LeadStatus.NEGOTIATION, 0.05),
        (LeadStatus.WON, 0.03),
        (LeadStatus.LOST, 0.02),
    ]
    status = random.choices([s[0] for s in statuses], weights=[s[1] for s in statuses], k=1)[0]

    # Generate created_at within last 90 days
    days_ago = random.randint(0, 90)
    created_at = datetime.utcnow() - timedelta(days=days_ago)

    # Calculate lead score (0-100)
    base_score = 50
    if temperature == LeadTemperature.HOT:
        base_score += random.randint(30, 45)
    elif temperature == LeadTemperature.WARM:
        base_score += random.randint(10, 25)
    else:
        base_score -= random.randint(10, 30)

    lead_score = max(0, min(100, base_score))

    lead = Lead(
        id=str(uuid4()),
        first_name=first_name,
        last_name=last_name,
        email=generate_email(first_name, last_name),
        phone=generate_phone(),
        source=source,
        status=status,
        temperature=temperature,
        lead_score=lead_score,
        property_address=f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Maple', 'Cedar', 'Pine'])} {random.choice(['St', 'Ave', 'Dr', 'Ln', 'Ct'])}, {market['name']}, MI {market['zip']}",
        property_value=market['avg_deal'] * random.uniform(0.8, 1.5),
        roof_age_years=random.randint(8, 35),
        roof_type=random.choice(["asphalt_shingle", "architectural_shingle", "metal", "tile", "slate"]),
        estimated_project_value=market['avg_deal'] * random.uniform(0.7, 1.3),
        notes=f"Lead from {source.value}. Property in {market['tier']} tier market.",
        created_at=created_at,
        updated_at=created_at,
    )

    return lead


def seed_leads(db, count=50, clear_first=False):
    """Seed leads table with test data"""
    if clear_first:
        logger.info("🗑️  Clearing existing leads...")
        db.query(Lead).delete()
        db.commit()
        logger.info("✅ Existing leads cleared")

    logger.info(f"🌱 Seeding {count} leads...")

    leads_added = 0
    for i in range(count):
        try:
            lead = generate_lead()
            db.add(lead)

            # Commit in batches of 10
            if (i + 1) % 10 == 0:
                db.commit()
                leads_added += 10
                logger.info(f"   ✅ Added {leads_added}/{count} leads...")

        except Exception as e:
            logger.error(f"   ❌ Error adding lead {i+1}: {str(e)}")
            db.rollback()

    # Final commit
    db.commit()

    logger.info(f"✅ Successfully seeded {count} leads")

    # Show summary stats
    total_leads = db.query(Lead).count()
    hot_leads = db.query(Lead).filter(Lead.temperature == LeadTemperature.HOT).count()
    warm_leads = db.query(Lead).filter(Lead.temperature == LeadTemperature.WARM).count()
    cold_leads = db.query(Lead).filter(Lead.temperature == LeadTemperature.COLD).count()

    logger.info("\n📊 Database Summary:")
    logger.info(f"   Total Leads: {total_leads}")
    logger.info(f"   🔥 Hot: {hot_leads} ({hot_leads/total_leads*100:.1f}%)")
    logger.info(f"   🌡️  Warm: {warm_leads} ({warm_leads/total_leads*100:.1f}%)")
    logger.info(f"   ❄️  Cold: {cold_leads} ({cold_leads/total_leads*100:.1f}%)")


def main():
    """Main seed function"""
    parser = argparse.ArgumentParser(description="Seed local PostgreSQL database with test data")
    parser.add_argument("--leads", type=int, default=50, help="Number of leads to seed")
    parser.add_argument("--clear-first", action="store_true", help="Clear existing data before seeding")

    args = parser.parse_args()

    logger.info("🚀 Starting database seed...")
    logger.info(f"   Database: Local PostgreSQL")
    logger.info(f"   Leads to add: {args.leads}")
    logger.info(f"   Clear first: {args.clear_first}")

    db = SessionLocal()

    try:
        seed_leads(db, count=args.leads, clear_first=args.clear_first)
        logger.info("\n✅ Database seeding completed successfully!")

    except Exception as e:
        logger.error(f"\n❌ Seeding failed: {str(e)}")
        db.rollback()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
