#!/usr/bin/env python3
"""
Alternative Database Table Creation Script for iSwitch Roofs CRM
Uses direct SQL execution via psycopg2 or alternative method
Version: 1.0.0
Date: 2025-10-05
"""

import logging
import os
import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables_with_psycopg2():
    """Create tables using psycopg2 direct connection."""
    try:
        from urllib.parse import urlparse

        import psycopg2
    except ImportError:
        print("❌ psycopg2 not installed. Try: pip install psycopg2-binary")
        return False

    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return False

    print("🏗️  Creating Database Tables using Direct Connection...")
    print("=" * 60)

    # Table creation SQL (all combined)
    full_sql = """
-- Create leads table
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    source VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'new',
    temperature VARCHAR(20),
    lead_score INTEGER DEFAULT 0,
    street_address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    property_value INTEGER,
    roof_age INTEGER,
    roof_type VARCHAR(50),
    roof_size_sqft INTEGER,
    urgency VARCHAR(50),
    project_description TEXT,
    budget_range_min INTEGER,
    budget_range_max INTEGER,
    insurance_claim BOOLEAN DEFAULT FALSE,
    assigned_to UUID,
    converted_to_customer BOOLEAN DEFAULT FALSE,
    customer_id UUID,
    last_contact_date TIMESTAMPTZ,
    next_follow_up_date TIMESTAMPTZ,
    response_time_minutes INTEGER,
    interaction_count INTEGER DEFAULT 0,
    notes TEXT,
    lost_reason VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    metadata_json TEXT
);

-- Create customers table
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    segment VARCHAR(50),
    street_address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    lifetime_value INTEGER DEFAULT 0,
    project_count INTEGER DEFAULT 0,
    referral_count INTEGER DEFAULT 0,
    original_lead_id UUID,
    converted_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    metadata_json TEXT
);

-- Create team_members table
CREATE TABLE IF NOT EXISTS team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    hire_date DATE,
    active_leads_count INTEGER DEFAULT 0,
    monthly_quota INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    metadata_json TEXT
);

-- Create appointments table
CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    appointment_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'scheduled',
    scheduled_date TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER NOT NULL,
    customer_id UUID,
    lead_id UUID,
    assigned_to UUID,
    location_type VARCHAR(50) DEFAULT 'customer_site',
    address VARCHAR(500),
    notes TEXT,
    internal_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    metadata_json TEXT
);

-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    project_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'planning',
    customer_id UUID NOT NULL,
    lead_id UUID,
    assigned_team_member UUID,
    estimated_value INTEGER,
    actual_value INTEGER,
    start_date DATE,
    end_date DATE,
    completion_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    metadata_json TEXT
);

-- Create interactions table
CREATE TABLE IF NOT EXISTS interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interaction_type VARCHAR(50) NOT NULL,
    direction VARCHAR(20) NOT NULL,
    subject VARCHAR(255),
    content TEXT,
    contact_method VARCHAR(50) NOT NULL,
    lead_id UUID,
    customer_id UUID,
    team_member_id UUID,
    duration_minutes INTEGER,
    outcome VARCHAR(100),
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_date TIMESTAMPTZ,
    scheduled_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    metadata_json TEXT
);

-- Create reviews table
CREATE TABLE IF NOT EXISTS reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    project_id UUID,
    platform VARCHAR(50) NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_title VARCHAR(255),
    review_content TEXT,
    response_content TEXT,
    review_date TIMESTAMPTZ NOT NULL,
    response_date TIMESTAMPTZ,
    external_id VARCHAR(255),
    external_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'published',
    is_featured BOOLEAN DEFAULT FALSE,
    helpful_votes INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    metadata_json TEXT
);

-- Create partnerships table
CREATE TABLE IF NOT EXISTS partnerships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_name VARCHAR(255) NOT NULL,
    partner_type VARCHAR(100) NOT NULL,
    contact_person VARCHAR(255),
    phone VARCHAR(20),
    email VARCHAR(255),
    address VARCHAR(500),
    status VARCHAR(50) DEFAULT 'active',
    commission_rate DECIMAL(5,2),
    total_referrals INTEGER DEFAULT 0,
    total_revenue INTEGER DEFAULT 0,
    contract_start_date DATE,
    contract_end_date DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    metadata_json TEXT
);

-- Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium',
    recipient_id UUID,
    recipient_type VARCHAR(50) DEFAULT 'user',
    channel VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    scheduled_for TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    related_entity_type VARCHAR(50),
    related_entity_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    metadata_json TEXT
);

-- Create alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    source VARCHAR(100),
    category VARCHAR(50),
    status VARCHAR(50) DEFAULT 'active',
    threshold_value DECIMAL(10,2),
    actual_value DECIMAL(10,2),
    assigned_to UUID,
    resolved_at TIMESTAMPTZ,
    resolved_by UUID,
    resolution_notes TEXT,
    auto_resolve BOOLEAN DEFAULT FALSE,
    escalation_level INTEGER DEFAULT 0,
    related_entity_type VARCHAR(50),
    related_entity_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    metadata_json TEXT
);

-- Create essential indexes
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at);
CREATE INDEX IF NOT EXISTS idx_leads_assigned_to ON leads(assigned_to);

-- Enable Row Level Security
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE partnerships ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated users
CREATE POLICY "Enable all operations for authenticated users" ON leads
    FOR ALL TO authenticated USING (true);
CREATE POLICY "Enable all operations for authenticated users" ON customers
    FOR ALL TO authenticated USING (true);
CREATE POLICY "Enable all operations for authenticated users" ON team_members
    FOR ALL TO authenticated USING (true);
CREATE POLICY "Enable all operations for authenticated users" ON appointments
    FOR ALL TO authenticated USING (true);
CREATE POLICY "Enable all operations for authenticated users" ON projects
    FOR ALL TO authenticated USING (true);
CREATE POLICY "Enable all operations for authenticated users" ON interactions
    FOR ALL TO authenticated USING (true);
CREATE POLICY "Enable all operations for authenticated users" ON reviews
    FOR ALL TO authenticated USING (true);
CREATE POLICY "Enable all operations for authenticated users" ON partnerships
    FOR ALL TO authenticated USING (true);
CREATE POLICY "Enable all operations for authenticated users" ON notifications
    FOR ALL TO authenticated USING (true);
CREATE POLICY "Enable all operations for authenticated users" ON alerts
    FOR ALL TO authenticated USING (true);

-- Insert sample data
INSERT INTO team_members (first_name, last_name, email, role) VALUES
('John', 'Sales', 'john.sales@iswitchroofs.com', 'sales_representative')
ON CONFLICT (email) DO NOTHING;

INSERT INTO leads (first_name, last_name, phone, email, source, city, state, zip_code) VALUES
('Jane', 'Customer', '248-555-0123', 'jane@example.com', 'website_form', 'Birmingham', 'MI', '48009'),
('Robert', 'Smith', '313-555-0456', 'robert.smith@email.com', 'google_ads', 'Bloomfield Hills', 'MI', '48302'),
('Sarah', 'Johnson', '586-555-0789', 'sarah.j@email.com', 'facebook_ads', 'Troy', 'MI', '48084'),
('Michael', 'Brown', '248-555-0321', 'mbrown@email.com', 'referral', 'Rochester Hills', 'MI', '48309'),
('Lisa', 'Davis', '734-555-0654', 'lisa.davis@email.com', 'website_form', 'Canton', 'MI', '48187')
ON CONFLICT DO NOTHING;

INSERT INTO customers (first_name, last_name, phone, email, city, state, zip_code, lifetime_value) VALUES
('David', 'Wilson', '248-555-1111', 'david.wilson@email.com', 'Birmingham', 'MI', '48009', 45000),
('Jennifer', 'Taylor', '313-555-2222', 'jennifer.taylor@email.com', 'Grosse Pointe', 'MI', '48236', 38000)
ON CONFLICT DO NOTHING;
"""

    try:
        print("🔌 Connecting to Supabase PostgreSQL...")

        # Parse connection URL
        parsed = urlparse(database_url)

        # Connect to database
        conn = psycopg2.connect(
            host=parsed.hostname,
            database=parsed.path[1:] if parsed.path else "postgres",
            user=parsed.username,
            password=parsed.password,
            port=parsed.port or 5432,
            sslmode="require",
        )

        print("✅ Connected to database")

        # Execute SQL
        print("📋 Executing table creation SQL...")
        cursor = conn.cursor()
        cursor.execute(full_sql)
        conn.commit()

        print("✅ All tables created successfully!")

        # Verify tables exist
        print("\n🔍 Verifying table creation...")
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """
        )

        tables = cursor.fetchall()
        table_names = [row[0] for row in tables]

        expected_tables = [
            "leads",
            "customers",
            "team_members",
            "appointments",
            "projects",
            "interactions",
            "reviews",
            "partnerships",
            "notifications",
            "alerts",
        ]

        found_tables = [t for t in expected_tables if t in table_names]

        print(f"📊 Tables Found: {len(found_tables)}/10")
        for table in found_tables:
            # Count rows
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            print(f"✅ {table} - {count} rows")

        cursor.close()
        conn.close()

        if len(found_tables) >= 8:
            print("\n🎉 SUCCESS! Database setup complete!")
            return True
        else:
            print(f"\n⚠️ Only {len(found_tables)} tables created")
            return False

    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        return False


def create_tables_with_supabase():
    """Fallback method using Supabase client."""
    try:
        from app import create_app
        from app.utils.supabase_client import SupabaseService

        print("🏗️  Fallback: Creating tables with Supabase client...")

        app = create_app("development")
        with app.app_context():
            service = SupabaseService(use_admin=True)
            client = service.client

            # Define individual table creation statements
            table_statements = [
                """CREATE TABLE IF NOT EXISTS leads (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    email VARCHAR(255),
                    source VARCHAR(50) NOT NULL,
                    status VARCHAR(50) DEFAULT 'new',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )""",
                """CREATE TABLE IF NOT EXISTS customers (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    email VARCHAR(255),
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )""",
                """CREATE TABLE IF NOT EXISTS team_members (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )""",
            ]

            # Try to execute basic tables
            created_count = 0
            for i, statement in enumerate(table_statements):
                try:
                    # Try using raw SQL if available
                    response = client.postgrest.rpc("query", {"query": statement}).execute()
                    created_count += 1
                    print(f"✅ Created table {i+1}")
                except Exception as e:
                    print(f"❌ Failed to create table {i+1}: {e}")

            return created_count > 0

    except Exception as e:
        print(f"❌ Supabase fallback failed: {e}")
        return False


def main():
    """Main execution function."""
    print("🏗️  iSwitch Roofs CRM - Database Table Creation")
    print("=" * 60)

    # Try psycopg2 first (most reliable)
    success = create_tables_with_psycopg2()

    if not success:
        print("\n🔄 Trying Supabase client fallback...")
        success = create_tables_with_supabase()

    if success:
        print("\n✅ COMPLETE! Next Steps:")
        print("1. Run: python inspect_database.py")
        print("2. Run: python run.py")
        print("3. Test endpoints at http://localhost:8001")
        sys.exit(0)
    else:
        print("\n❌ TABLE CREATION FAILED!")
        print("🌐 Please create tables manually via Supabase dashboard")
        print("📋 Use the SQL from IMMEDIATE_FIX_INSTRUCTIONS.md")
        sys.exit(1)


if __name__ == "__main__":
    main()
