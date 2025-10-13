"""
Seed Large Leads Dataset for Performance Testing
Creates 100+ leads with realistic data distribution for testing Phase C performance
Version: 1.0.0
Date: 2025-10-10
"""

import os
import sys
import random
from datetime import datetime, timedelta
from typing import List, Dict

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import get_db
from app.models.lead_sqlalchemy import Lead
from sqlalchemy import text

# Southeast Michigan cities with property values
ULTRA_PREMIUM_CITIES = [
    ("Bloomfield Hills", 750000),
    ("Birmingham", 650000),
    ("Grosse Pointe", 700000)
]

PROFESSIONAL_CITIES = [
    ("Troy", 450000),
    ("Rochester Hills", 420000),
    ("West Bloomfield", 480000)
]

STANDARD_CITIES = [
    ("Warren", 180000),
    ("Sterling Heights", 200000),
    ("Livonia", 220000),
    ("Canton", 240000),
    ("Novi", 260000),
    ("Ann Arbor", 300000),
    ("Farmington Hills", 280000)
]

# Lead sources with realistic distribution
# Valid sources: website_form, google_lsa, google_ads, facebook_ads, referral, door_to_door,
#                storm_response, organic_search, phone_inquiry, email_inquiry, partner_referral, repeat_customer
SOURCES = [
    ("google_lsa", 25),  # 25% Google LSA
    ("facebook_ads", 20),  # 20% Facebook Ads
    ("referral", 20),  # 20% Referrals (includes insurance, real estate, community)
    ("partner_referral", 15),  # 15% Partner referrals
    ("website_form", 10),  # 10% Website forms
    ("phone_inquiry", 10)  # 10% Phone inquiries
]

# First names
FIRST_NAMES = [
    "John", "Michael", "Robert", "David", "William", "James", "Richard", "Joseph",
    "Thomas", "Christopher", "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth",
    "Barbara", "Susan", "Jessica", "Sarah", "Karen", "Nancy", "Lisa", "Betty",
    "Margaret", "Sandra", "Ashley", "Emily", "Donna", "Michelle", "Dorothy",
    "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Paul", "Andrew",
    "Joshua", "Kenneth", "Kevin", "Brian", "George", "Timothy", "Ronald", "Edward",
    "Jason", "Jeffrey", "Ryan", "Jacob", "Nicholas", "Eric", "Jonathan", "Stephen"
]

# Last names
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White",
    "Harris", "Clark", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green", "Adams",
    "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts"
]

# Streets
STREET_NAMES = [
    "Maple", "Oak", "Pine", "Elm", "Cedar", "Main", "Church", "Washington",
    "Park", "Lake", "River", "Hill", "Mill", "Spring", "Forest", "Valley",
    "Ridge", "Meadow", "Garden", "Sunset", "Sunrise", "Highland", "Woodland",
    "Lakeside", "Brookside", "Hillside", "Riverside", "Parkway", "Boulevard"
]

STREET_TYPES = ["St", "Ave", "Dr", "Rd", "Ln", "Ct", "Way", "Blvd"]


def generate_phone() -> str:
    """Generate realistic Michigan phone number"""
    area_codes = ["248", "313", "734", "586", "810", "517", "269"]
    return f"{random.choice(area_codes)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"


def generate_email(first_name: str, last_name: str) -> str:
    """Generate realistic email"""
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com"]
    formats = [
        f"{first_name.lower()}.{last_name.lower()}",
        f"{first_name.lower()}{last_name.lower()}",
        f"{first_name[0].lower()}{last_name.lower()}",
        f"{first_name.lower()}{random.randint(1, 99)}"
    ]
    return f"{random.choice(formats)}@{random.choice(domains)}"


def generate_address(city: str) -> tuple:
    """Generate realistic address"""
    number = random.randint(100, 9999)
    street = random.choice(STREET_NAMES)
    street_type = random.choice(STREET_TYPES)
    return f"{number} {street} {street_type}", city, "MI", f"{random.randint(48000, 48999)}"


def calculate_lead_score(city: str, property_value: int, source: str) -> int:
    """Calculate lead score based on attributes"""
    score = 50  # Base score

    # City score (0-25 points)
    ultra_premium = [c[0] for c in ULTRA_PREMIUM_CITIES]
    professional = [c[0] for c in PROFESSIONAL_CITIES]

    if city in ultra_premium:
        score += 25
    elif city in professional:
        score += 18
    else:
        score += 10

    # Property value score (0-15 points)
    if property_value >= 600000:
        score += 15
    elif property_value >= 400000:
        score += 10
    else:
        score += 5

    # Source score (0-10 points)
    source_scores = {
        "partner_referral": 10,
        "referral": 9,
        "google_lsa": 7,
        "facebook_ads": 6,
        "website_form": 8,
        "phone_inquiry": 7,
        "organic_search": 8,
        "email_inquiry": 6
    }
    score += source_scores.get(source, 5)

    return min(score, 100)


def determine_temperature(lead_score: int) -> str:
    """Determine temperature from lead score"""
    if lead_score >= 85:
        return "hot"
    elif lead_score >= 70:
        return "warm"
    elif lead_score >= 55:
        return "cool"
    else:
        return "cold"


def generate_status() -> str:
    """Generate realistic status distribution"""
    statuses = [
        ("new", 30),
        ("contacted", 25),
        ("qualified", 20),
        ("appointment_scheduled", 10),
        ("inspection_completed", 5),
        ("quote_sent", 5),
        ("negotiation", 3),
        ("won", 1),
        ("lost", 1)
    ]

    total_weight = sum(w for _, w in statuses)
    r = random.randint(1, total_weight)

    cumulative = 0
    for status, weight in statuses:
        cumulative += weight
        if r <= cumulative:
            return status

    return "new"


def generate_lead(index: int) -> Dict:
    """Generate single realistic lead"""
    # Select city with property value distribution
    all_cities = ULTRA_PREMIUM_CITIES + PROFESSIONAL_CITIES + STANDARD_CITIES
    weights = [15, 15, 15, 20, 20, 25, 35, 35, 35, 40, 40, 45, 50]  # Skew toward standard
    city, base_property_value = random.choices(all_cities, weights=weights)[0]

    # Add variance to property value (+/- 20%)
    property_value = int(base_property_value * random.uniform(0.8, 1.2))

    # Select source with distribution
    total_weight = sum(w for _, w in SOURCES)
    r = random.randint(1, total_weight)
    cumulative = 0
    for source, weight in SOURCES:
        cumulative += weight
        if r <= cumulative:
            selected_source = source
            break
    else:
        selected_source = "google_lsa"

    # Generate person details
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    phone = generate_phone()
    email = generate_email(first_name, last_name)
    street_address, city_name, state, zip_code = generate_address(city)

    # Calculate scores
    lead_score = calculate_lead_score(city, property_value, selected_source)
    temperature = determine_temperature(lead_score)
    status = generate_status()

    # Generate timestamps (last 90 days)
    days_ago = random.randint(0, 90)
    created_at = datetime.now() - timedelta(days=days_ago)
    updated_at = created_at + timedelta(days=random.randint(0, min(days_ago, 30)))

    # Notes (20% have notes)
    notes = None
    if random.random() < 0.2:
        note_options = [
            "Interested in premium materials",
            "Needs roof replacement ASAP",
            "Comparing multiple quotes",
            "Referred by neighbor",
            "Insurance claim in progress",
            "Looking for spring installation",
            "Concerned about warranty",
            "Requesting 3D modeling preview"
        ]
        notes = random.choice(note_options)

    return {
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone,
        "email": email,
        "street_address": street_address,
        "city": city_name,
        "state": state,
        "zip_code": zip_code,
        "source": selected_source,
        "status": status,
        "temperature": temperature,
        "lead_score": lead_score,
        "property_value": property_value,
        "notes": notes,
        "created_at": created_at,
        "updated_at": updated_at,
        "is_deleted": False
    }


def seed_leads(count: int = 100):
    """Seed database with specified number of leads"""
    print(f"🌱 Seeding {count} leads for performance testing...")

    db = next(get_db())

    try:
        # Check existing count
        result = db.execute(text("SELECT COUNT(*) FROM leads WHERE is_deleted = false"))
        existing_count = result.scalar()
        print(f"📊 Current leads in database: {existing_count}")

        if existing_count >= 100:
            print(f"✅ Database already has {existing_count} leads. Skipping seed.")
            response = input("Do you want to add more leads anyway? (yes/no): ")
            if response.lower() != "yes":
                return

        # Generate leads
        print(f"🔨 Generating {count} leads with realistic distribution...")
        leads_data = [generate_lead(i) for i in range(count)]

        # Distribution summary
        by_city = {}
        by_source = {}
        by_temperature = {}
        by_status = {}

        for lead in leads_data:
            by_city[lead['city']] = by_city.get(lead['city'], 0) + 1
            by_source[lead['source']] = by_source.get(lead['source'], 0) + 1
            by_temperature[lead['temperature']] = by_temperature.get(lead['temperature'], 0) + 1
            by_status[lead['status']] = by_status.get(lead['status'], 0) + 1

        print("\n📈 Distribution Summary:")
        print(f"  Cities: {dict(sorted(by_city.items(), key=lambda x: x[1], reverse=True))}")
        print(f"  Sources: {dict(sorted(by_source.items(), key=lambda x: x[1], reverse=True))}")
        print(f"  Temperature: {by_temperature}")
        print(f"  Status: {dict(sorted(by_status.items(), key=lambda x: x[1], reverse=True))}")

        # Insert leads
        print(f"\n💾 Inserting {count} leads into database...")

        for i, lead_data in enumerate(leads_data, 1):
            lead = Lead(**lead_data)
            db.add(lead)

            if i % 25 == 0:
                print(f"  Inserted {i}/{count} leads...")

        db.commit()

        # Verify
        result = db.execute(text("SELECT COUNT(*) FROM leads WHERE is_deleted = false"))
        new_count = result.scalar()

        print(f"\n✅ Successfully seeded {count} leads!")
        print(f"📊 Total leads in database: {new_count}")

        # Show sample statistics
        print("\n📊 Sample Statistics:")

        # Hot leads
        result = db.execute(text("SELECT COUNT(*) FROM leads WHERE temperature = 'hot' AND is_deleted = false"))
        hot_count = result.scalar()
        print(f"  🔥 Hot leads: {hot_count} ({hot_count/new_count*100:.1f}%)")

        # Premium cities
        premium_cities = ["Bloomfield Hills", "Birmingham", "Grosse Pointe", "Troy", "Rochester Hills", "West Bloomfield"]
        placeholders = ', '.join([f"'{city}'" for city in premium_cities])
        result = db.execute(text(f"SELECT COUNT(*) FROM leads WHERE city IN ({placeholders}) AND is_deleted = false"))
        premium_count = result.scalar()
        print(f"  ⭐ Premium market leads: {premium_count} ({premium_count/new_count*100:.1f}%)")

        # Average property value
        result = db.execute(text("SELECT AVG(property_value) FROM leads WHERE is_deleted = false"))
        avg_value = result.scalar()
        print(f"  💰 Average property value: ${avg_value:,.0f}")

        # Average lead score
        result = db.execute(text("SELECT AVG(lead_score) FROM leads WHERE is_deleted = false"))
        avg_score = result.scalar()
        print(f"  📈 Average lead score: {avg_score:.1f}/100")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding leads: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed large leads dataset for performance testing")
    parser.add_argument("--count", type=int, default=100, help="Number of leads to generate (default: 100)")
    args = parser.parse_args()

    print("=" * 80)
    print("PHASE C: LARGE LEADS DATASET SEEDER")
    print("=" * 80)
    print()

    seed_leads(count=args.count)

    print()
    print("=" * 80)
    print("✅ SEEDING COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Test dashboard performance with 100+ leads")
    print("  2. Verify auto-refresh performance (30-second interval)")
    print("  3. Test filtering and search with large dataset")
    print("  4. Monitor API response times (<500ms target)")
    print()
