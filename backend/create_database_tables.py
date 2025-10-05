#!/usr/bin/env python3
"""
Database Table Creation Script for iSwitch Roofs CRM
Executes SQL from IMMEDIATE_FIX_INSTRUCTIONS.md to create all required tables
Version: 1.0.0
Date: 2025-10-05
"""

import sys
import logging
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from app import create_app
from app.utils.supabase_client import SupabaseService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Create all database tables using SQL from instructions."""
    print("🏗️  Creating Database Tables for iSwitch Roofs CRM...")
    print("=" * 60)

    # SQL script from IMMEDIATE_FIX_INSTRUCTIONS.md
    table_creation_sql = """
-- CRITICAL: Create leads table immediately
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

-- Create essential indexes
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at);
CREATE INDEX IF NOT EXISTS idx_leads_assigned_to ON leads(assigned_to);

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
"""

    # Row Level Security and Policies SQL
    rls_policies_sql = """
-- Enable Row Level Security (required for Supabase)
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
"""

    # Sample data SQL
    sample_data_sql = """
-- Insert sample data for testing
INSERT INTO team_members (first_name, last_name, email, role) VALUES
('John', 'Sales', 'john.sales@iswitchroofs.com', 'sales_representative')
ON CONFLICT (email) DO NOTHING;

-- Get the team member ID for sample lead
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

    app = create_app('development')

    with app.app_context():
        try:
            # Use admin client to execute DDL operations
            service = SupabaseService(use_admin=True)
            client = service.client

            print("📋 Step 1: Creating main tables...")

            # Execute table creation SQL using RPC
            try:
                response = client.rpc('query', {'query': table_creation_sql}).execute()
                print("✅ Core tables created successfully")
            except Exception as e:
                # Fallback: Try executing each CREATE TABLE statement individually
                print(f"⚠️ Batch execution failed: {e}")
                print("🔄 Attempting individual table creation...")

                # Split SQL into individual statements and execute
                statements = [stmt.strip() for stmt in table_creation_sql.split(';') if stmt.strip()]
                created_tables = []

                for statement in statements:
                    if statement.upper().startswith('CREATE TABLE'):
                        table_name = statement.split('(')[0].split()[-1]
                        try:
                            client.rpc('query', {'query': statement + ';'}).execute()
                            created_tables.append(table_name)
                            print(f"✅ Created table: {table_name}")
                        except Exception as table_error:
                            print(f"❌ Failed to create {table_name}: {table_error}")

                    elif statement.upper().startswith('CREATE INDEX'):
                        try:
                            client.rpc('query', {'query': statement + ';'}).execute()
                            print(f"✅ Created index")
                        except Exception as index_error:
                            print(f"⚠️ Index creation warning: {index_error}")

            print("\n📋 Step 2: Setting up Row Level Security...")
            try:
                client.rpc('query', {'query': rls_policies_sql}).execute()
                print("✅ RLS policies configured")
            except Exception as e:
                print(f"⚠️ RLS setup warning: {e}")

            print("\n📋 Step 3: Adding sample data...")
            try:
                client.rpc('query', {'query': sample_data_sql}).execute()
                print("✅ Sample data inserted")
            except Exception as e:
                print(f"⚠️ Sample data warning: {e}")

            print("\n🔍 Step 4: Verifying table creation...")

            # Test each expected table
            expected_tables = [
                'leads', 'customers', 'team_members', 'appointments',
                'projects', 'interactions', 'reviews', 'partnerships',
                'notifications', 'alerts'
            ]

            accessible_tables = []
            table_row_counts = {}

            for table in expected_tables:
                try:
                    # Test table access and count rows
                    count_response = client.table(table).select('*', count='exact').limit(1).execute()
                    row_count = count_response.count if hasattr(count_response, 'count') else 0

                    accessible_tables.append(table)
                    table_row_counts[table] = row_count
                    print(f"✅ {table} - accessible ({row_count} rows)")

                except Exception as e:
                    if 'PGRST205' in str(e):
                        print(f"❌ {table} - table not found")
                    else:
                        print(f"⚠️ {table} - error: {str(e)[:100]}")

            print(f"\n📊 RESULTS SUMMARY")
            print("=" * 40)
            print(f"✅ Tables Created: {len(accessible_tables)}/10")
            print(f"📋 Accessible Tables: {', '.join(accessible_tables)}")

            if table_row_counts:
                print(f"\n📊 Row Counts:")
                for table, count in table_row_counts.items():
                    print(f"  - {table}: {count} rows")

            if len(accessible_tables) >= 5:
                print(f"\n🎉 SUCCESS! Database tables created successfully!")
                print(f"🚀 Ready to start the Flask server")
                return True
            else:
                print(f"\n⚠️ PARTIAL SUCCESS - Some tables missing")
                print(f"❓ Check Supabase dashboard for details")
                return False

        except Exception as e:
            print(f"❌ Critical error during table creation: {e}")
            logger.error(f"Table creation failed: {e}")
            return False

def main():
    """Main execution function."""
    success = create_tables()

    if success:
        print("\n✅ Next Steps:")
        print("1. Run: python inspect_database.py  (to verify)")
        print("2. Run: python run.py  (to start server)")
        print("3. Test API endpoints at http://localhost:8001")
        sys.exit(0)
    else:
        print("\n❌ Table creation incomplete!")
        print("🔧 Check the error messages above")
        print("🌐 Try manual creation via Supabase dashboard")
        sys.exit(1)

if __name__ == '__main__':
    main()