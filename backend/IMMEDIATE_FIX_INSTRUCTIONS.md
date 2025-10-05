# IMMEDIATE DATABASE FIX INSTRUCTIONS

## CRITICAL: Database Integration is Completely Broken

**Status**: All API routes non-functional due to missing database tables and broken models
**Time to Fix**: 2 hours for immediate functionality, 5-8 days for complete resolution

## STEP 1: Create Database Tables (CRITICAL - DO THIS NOW)

### Option A: Supabase Dashboard (RECOMMENDED)
1. Go to [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Open your project: `tdwpzktihdeuzapxoovk`
3. Click "SQL Editor" in left sidebar
4. Click "New Query"
5. Copy and paste this SQL:

```sql
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

-- Enable Row Level Security (required for Supabase)
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

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

-- Insert sample data for testing
INSERT INTO team_members (first_name, last_name, email, role) VALUES
('John', 'Sales', 'john.sales@iswitchroofs.com', 'sales_representative')
ON CONFLICT (email) DO NOTHING;

-- Get the team member ID for sample lead
INSERT INTO leads (first_name, last_name, phone, email, source, city, state, zip_code) VALUES
('Jane', 'Customer', '248-555-0123', 'jane@example.com', 'website_form', 'Birmingham', 'MI', '48009')
ON CONFLICT DO NOTHING;
```

6. Click "Run" button
7. Verify it says "Success" (should take 10-30 seconds)

### Option B: Command Line (if you have psql)
```bash
# Get the correct DATABASE_URL from .env first, then:
psql $DATABASE_URL -f alembic/versions/database_migration_appointments.sql
```

## STEP 2: Verify Tables Exist

Run this test:
```bash
cd /Users/grayghostdata/Projects/client-roofing/backend
python test_database.py
```

You should see:
```
✅ leads - accessible
✅ customers - accessible
✅ team_members - accessible
✅ appointments - accessible
✅ projects - accessible
```

## STEP 3: Install Missing Dependencies

```bash
cd /Users/grayghostdata/Projects/client-roofing/backend
pip install google-auth-oauthlib scikit-learn psycopg2-binary
```

## STEP 4: Test the Server

```bash
python run.py
```

Should start without the model errors.

## EXPECTED RESULTS AFTER STEP 1

### Before Fix:
```
❌ leads - not accessible
❌ customers - not accessible
❌ No API routes working
```

### After Fix:
```
✅ leads - accessible (with sample data)
✅ customers - accessible
✅ Basic CRUD operations working
✅ Server starts without model errors
```

## WHAT THIS FIXES IMMEDIATELY

1. ✅ Database tables exist
2. ✅ Basic data operations work
3. ✅ Server starts without critical errors
4. ✅ Can begin testing API endpoints

## WHAT STILL NEEDS TO BE FIXED (Days 2-8)

1. ❌ Models are still Pydantic (need SQLAlchemy)
2. ❌ Service layer needs ORM integration
3. ❌ API routes need proper model integration
4. ❌ Advanced features and relationships

## EMERGENCY CONTACT

If you encounter issues:
1. Check Supabase dashboard for error messages
2. Verify all SQL executed successfully
3. Run the test script to confirm table access
4. Check server logs for specific errors

---

**CRITICAL**: Do Step 1 immediately to restore basic functionality
**Time Required**: 30 minutes for database creation + verification