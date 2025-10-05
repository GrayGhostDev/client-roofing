# CRITICAL: Database Setup Instructions

## IMMEDIATE ACTION REQUIRED

The database tables must be created **RIGHT NOW** to fix the broken API. Follow these steps exactly:

## Step 1: Access Supabase Dashboard

1. Go to: **https://supabase.com/dashboard**
2. Login with your Supabase account
3. Select your project: **`tdwpzktihdeuzapxoovk`** (iSwitch Roofs)
4. Click **"SQL Editor"** in the left sidebar
5. Click **"New Query"**

## Step 2: Execute Table Creation SQL

Copy and paste the **ENTIRE** contents of the file `create_tables.sql` (located in the same directory as this file) into the SQL Editor.

**OR** use this consolidated SQL:

```sql
-- iSwitch Roofs CRM Database Tables Creation Script
-- Execute this SQL in Supabase Dashboard > SQL Editor

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

-- Create policies (allow all operations for authenticated users)
CREATE POLICY "Enable all operations for authenticated users" ON leads FOR ALL TO authenticated USING (true);
CREATE POLICY "Enable all operations for authenticated users" ON customers FOR ALL TO authenticated USING (true);
CREATE POLICY "Enable all operations for authenticated users" ON team_members FOR ALL TO authenticated USING (true);
CREATE POLICY "Enable all operations for authenticated users" ON appointments FOR ALL TO authenticated USING (true);
CREATE POLICY "Enable all operations for authenticated users" ON projects FOR ALL TO authenticated USING (true);
CREATE POLICY "Enable all operations for authenticated users" ON interactions FOR ALL TO authenticated USING (true);
CREATE POLICY "Enable all operations for authenticated users" ON reviews FOR ALL TO authenticated USING (true);
CREATE POLICY "Enable all operations for authenticated users" ON partnerships FOR ALL TO authenticated USING (true);
CREATE POLICY "Enable all operations for authenticated users" ON notifications FOR ALL TO authenticated USING (true);
CREATE POLICY "Enable all operations for authenticated users" ON alerts FOR ALL TO authenticated USING (true);

-- Insert sample data
INSERT INTO team_members (first_name, last_name, email, role) VALUES
('John', 'Sales', 'john.sales@iswitchroofs.com', 'sales_representative')
ON CONFLICT (email) DO NOTHING;

INSERT INTO leads (first_name, last_name, phone, email, source, city, state, zip_code, status, lead_score) VALUES
('Jane', 'Customer', '248-555-0123', 'jane@example.com', 'website_form', 'Birmingham', 'MI', '48009', 'new', 75),
('Robert', 'Smith', '313-555-0456', 'robert.smith@email.com', 'google_ads', 'Bloomfield Hills', 'MI', '48302', 'contacted', 85),
('Sarah', 'Johnson', '586-555-0789', 'sarah.j@email.com', 'facebook_ads', 'Troy', 'MI', '48084', 'qualified', 65),
('Michael', 'Brown', '248-555-0321', 'mbrown@email.com', 'referral', 'Rochester Hills', 'MI', '48309', 'new', 90),
('Lisa', 'Davis', '734-555-0654', 'lisa.davis@email.com', 'website_form', 'Canton', 'MI', '48187', 'contacted', 55);

INSERT INTO customers (first_name, last_name, phone, email, city, state, zip_code, lifetime_value, status) VALUES
('David', 'Wilson', '248-555-1111', 'david.wilson@email.com', 'Birmingham', 'MI', '48009', 45000, 'active'),
('Jennifer', 'Taylor', '313-555-2222', 'jennifer.taylor@email.com', 'Grosse Pointe', 'MI', '48236', 38000, 'active');

-- Success indicator
SELECT 'SUCCESS: All tables created and sample data inserted!' as message;
```

## Step 3: Execute the SQL

1. **Paste ALL the SQL above** into the Supabase SQL Editor
2. Click the **"Run"** button (or press Ctrl+Enter)
3. Wait for execution (should take 10-30 seconds)
4. You should see **"Success"** message at the bottom
5. The last query should return: **"SUCCESS: All tables created and sample data inserted!"**

## Step 4: Verify Tables Were Created

After running the SQL, verify by clicking on **"Table Editor"** in the left sidebar. You should see these 10 tables:

1. ✅ **leads** (5 sample records)
2. ✅ **customers** (2 sample records)
3. ✅ **team_members** (1 sample record)
4. ✅ **appointments** (empty)
5. ✅ **projects** (empty)
6. ✅ **interactions** (empty)
7. ✅ **reviews** (empty)
8. ✅ **partnerships** (empty)
9. ✅ **notifications** (empty)
10. ✅ **alerts** (empty)

## Step 5: Test the Fix

Run the verification script:

```bash
cd /Users/grayghostdata/Projects/client-roofing/backend
python inspect_database.py
```

**Expected Output:**
```
✅ leads - accessible (5 rows)
✅ customers - accessible (2 rows)
✅ team_members - accessible (1 rows)
✅ appointments - accessible (0 rows)
✅ projects - accessible (0 rows)
✅ interactions - accessible (0 rows)
✅ reviews - accessible (0 rows)
✅ partnerships - accessible (0 rows)
✅ notifications - accessible (0 rows)
✅ alerts - accessible (0 rows)
```

## Step 6: Start the Server

If all tables are accessible:

```bash
cd /Users/grayghostdata/Projects/client-roofing/backend
python run.py
```

**Expected:**
- Server starts at `http://localhost:8001`
- No critical model errors in the logs
- API endpoints should work

## TROUBLESHOOTING

### If SQL Execution Fails:

1. **Check for syntax errors** - Make sure you copied the ENTIRE SQL block
2. **Try smaller chunks** - Execute one table at a time if needed
3. **Check permissions** - Make sure you're using the service role key
4. **Refresh dashboard** - Sometimes tables appear after refresh

### If Tables Don't Appear:

1. Click **"Table Editor"** in left sidebar
2. Refresh the page
3. Check that you selected the correct project
4. Verify in **Database > Tables** section

### If Verification Fails:

1. Make sure all 10 tables exist in Supabase dashboard
2. Check that RLS policies were created
3. Verify sample data was inserted
4. Try the verification script again

## EXPECTED RESULTS

**BEFORE FIX:**
```
❌ leads - not accessible
❌ customers - not accessible
❌ No API routes working
❌ Server won't start properly
```

**AFTER FIX:**
```
✅ leads - accessible (5 rows)
✅ customers - accessible (2 rows)
✅ All 10 tables created
✅ Server starts without errors
✅ API endpoints functional
```

## CRITICAL SUCCESS METRICS

- **10/10 tables exist** in Supabase
- **7+ rows of sample data** total
- **`inspect_database.py` shows all tables accessible**
- **`python run.py` starts without critical errors**
- **API calls to `/api/leads` return data**

---

⚠️ **IMPORTANT**: This is the CRITICAL first step. Without these tables, the entire API is non-functional. Execute this immediately before proceeding with any other development work.