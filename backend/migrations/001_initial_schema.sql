-- iSwitch Roofs CRM Database Schema
-- Version: 1.0.0
-- Date: 2025-10-01

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable PostGIS for geographic data (optional, for future features)
-- CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================================
-- ENUMS
-- ============================================================================

CREATE TYPE lead_status AS ENUM (
    'new',
    'contacted',
    'qualified',
    'appointment_scheduled',
    'inspection_completed',
    'quote_sent',
    'negotiation',
    'won',
    'lost',
    'nurture'
);

CREATE TYPE lead_temperature AS ENUM ('hot', 'warm', 'cool', 'cold');

CREATE TYPE lead_source AS ENUM (
    'website_form',
    'google_lsa',
    'google_ads',
    'facebook_ads',
    'referral',
    'door_to_door',
    'storm_response',
    'organic_search',
    'phone_inquiry',
    'email_inquiry',
    'partner_referral',
    'repeat_customer'
);

CREATE TYPE project_status AS ENUM (
    'quoted',
    'approved',
    'scheduled',
    'in_progress',
    'completed',
    'warranty',
    'cancelled'
);

CREATE TYPE project_type AS ENUM (
    'full_replacement',
    'repair',
    'emergency_repair',
    'inspection',
    'maintenance',
    'insurance_claim'
);

CREATE TYPE interaction_type AS ENUM (
    'phone_call',
    'email',
    'sms',
    'in_person',
    'video_call',
    'note',
    'automated'
);

CREATE TYPE partner_type AS ENUM (
    'insurance_agent',
    'real_estate_agent',
    'property_manager',
    'home_inspector',
    'contractor',
    'supplier'
);

CREATE TYPE team_role AS ENUM (
    'admin',
    'sales_manager',
    'sales_rep',
    'project_manager',
    'field_technician',
    'customer_service'
);

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Team Members Table
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    role team_role NOT NULL,
    territory VARCHAR(100),
    is_active BOOLEAN DEFAULT true,

    -- Performance metrics
    total_leads_assigned INTEGER DEFAULT 0,
    total_closed_deals INTEGER DEFAULT 0,
    total_revenue_generated DECIMAL(12, 2) DEFAULT 0,
    average_deal_size DECIMAL(12, 2) DEFAULT 0,
    conversion_rate DECIMAL(5, 2) DEFAULT 0,
    average_response_time INTEGER, -- in seconds

    -- Availability
    working_hours JSONB, -- {monday: {start: "08:00", end: "18:00"}, ...}

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

-- Leads Table
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Contact Information
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20) NOT NULL,
    alternate_phone VARCHAR(20),

    -- Address
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),

    -- Lead Details
    source lead_source NOT NULL,
    source_detail VARCHAR(255), -- Campaign name, referrer name, etc.
    status lead_status DEFAULT 'new',
    temperature lead_temperature,
    lead_score INTEGER DEFAULT 0 CHECK (lead_score >= 0 AND lead_score <= 100),

    -- Property Information
    property_age INTEGER,
    property_value DECIMAL(12, 2),
    property_type VARCHAR(50),
    roof_age INTEGER,
    current_roofing_material VARCHAR(100),

    -- Qualification Data
    urgency_level VARCHAR(20), -- immediate, 30_days, 90_days, 6_months, exploratory
    budget_range VARCHAR(50), -- under_10k, 10-15k, 15-20k, 20k_plus
    timeline VARCHAR(50),
    is_insurance_claim BOOLEAN DEFAULT false,
    has_existing_damage BOOLEAN DEFAULT false,
    damage_description TEXT,

    -- Assignment
    assigned_to UUID REFERENCES team_members(id),
    assigned_at TIMESTAMPTZ,

    -- Engagement Tracking
    first_contact_at TIMESTAMPTZ,
    last_contact_at TIMESTAMPTZ,
    last_activity_at TIMESTAMPTZ,
    contact_attempts INTEGER DEFAULT 0,
    email_opens INTEGER DEFAULT 0,
    email_clicks INTEGER DEFAULT 0,
    website_visits INTEGER DEFAULT 0,

    -- Competitor Information
    has_other_quotes BOOLEAN,
    competitor_quotes INTEGER DEFAULT 0,
    price_sensitive BOOLEAN DEFAULT false,

    -- Decision Makers
    decision_maker_name VARCHAR(200),
    additional_decision_makers JSONB, -- [{name: "...", role: "spouse"}, ...]

    -- Notes and Tags
    notes TEXT,
    tags VARCHAR(255)[],
    custom_fields JSONB,

    -- Conversion
    converted_to_customer_at TIMESTAMPTZ,
    lost_reason VARCHAR(255),
    lost_to_competitor VARCHAR(255),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_score CHECK (lead_score BETWEEN 0 AND 100),
    CONSTRAINT contact_info CHECK (email IS NOT NULL OR phone IS NOT NULL)
);

-- Customers Table
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID UNIQUE REFERENCES leads(id),

    -- Customer Information (denormalized from lead for performance)
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20) NOT NULL,
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),

    -- Customer Status
    account_status VARCHAR(50) DEFAULT 'active', -- active, inactive, past_customer
    customer_since DATE NOT NULL,

    -- Business Metrics
    lifetime_value DECIMAL(12, 2) DEFAULT 0,
    total_projects INTEGER DEFAULT 0,
    total_spent DECIMAL(12, 2) DEFAULT 0,
    average_project_value DECIMAL(12, 2) DEFAULT 0,

    -- Satisfaction & Reviews
    satisfaction_score INTEGER CHECK (satisfaction_score BETWEEN 1 AND 10),
    nps_score INTEGER CHECK (nps_score BETWEEN -100 AND 100),
    has_left_review BOOLEAN DEFAULT false,
    review_rating INTEGER CHECK (review_rating BETWEEN 1 AND 5),

    -- Referrals
    referral_source VARCHAR(255),
    has_referred_others BOOLEAN DEFAULT false,
    total_referrals INTEGER DEFAULT 0,

    -- Communication Preferences
    preferred_contact_method VARCHAR(50), -- phone, email, sms
    marketing_opt_in BOOLEAN DEFAULT true,
    sms_opt_in BOOLEAN DEFAULT false,

    -- Additional Data
    notes TEXT,
    tags VARCHAR(255)[],
    custom_fields JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Projects Table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id),

    -- Project Details
    project_name VARCHAR(255),
    project_type project_type NOT NULL,
    status project_status DEFAULT 'quoted',

    -- Financial
    quoted_amount DECIMAL(12, 2) NOT NULL,
    final_amount DECIMAL(12, 2),
    deposit_amount DECIMAL(12, 2),
    amount_paid DECIMAL(12, 2) DEFAULT 0,
    balance_due DECIMAL(12, 2),

    -- Insurance
    is_insurance_claim BOOLEAN DEFAULT false,
    insurance_company VARCHAR(255),
    claim_number VARCHAR(100),
    claim_amount DECIMAL(12, 2),
    deductible_amount DECIMAL(12, 2),

    -- Scheduling
    quote_date DATE,
    approval_date DATE,
    scheduled_start_date DATE,
    actual_start_date DATE,
    estimated_completion_date DATE,
    actual_completion_date DATE,

    -- Materials
    roofing_material VARCHAR(255),
    material_color VARCHAR(100),
    square_footage INTEGER,
    warranty_years INTEGER,
    manufacturer VARCHAR(255),

    -- Team Assignment
    sales_rep_id UUID REFERENCES team_members(id),
    project_manager_id UUID REFERENCES team_members(id),
    lead_technician_id UUID REFERENCES team_members(id),

    -- Documentation
    before_photos TEXT[], -- URLs to photos
    after_photos TEXT[],
    contract_url TEXT,
    invoice_url TEXT,
    warranty_document_url TEXT,

    -- Quality & Completion
    quality_check_passed BOOLEAN,
    customer_walkthrough_completed BOOLEAN DEFAULT false,
    customer_signature_date DATE,
    final_inspection_date DATE,

    -- Notes
    notes TEXT,
    internal_notes TEXT,
    custom_fields JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Interactions Table (All customer touchpoints)
CREATE TABLE interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Reference (can be lead or customer)
    lead_id UUID REFERENCES leads(id),
    customer_id UUID REFERENCES customers(id),
    project_id UUID REFERENCES projects(id),

    -- Interaction Details
    interaction_type interaction_type NOT NULL,
    channel VARCHAR(50), -- phone, email, sms, in_person, automated
    subject VARCHAR(255),
    description TEXT NOT NULL,

    -- Participants
    initiated_by UUID REFERENCES team_members(id),
    team_member_id UUID REFERENCES team_members(id),

    -- Metadata
    duration_seconds INTEGER, -- for calls and meetings
    sentiment_score INTEGER CHECK (sentiment_score BETWEEN -5 AND 5),
    outcome VARCHAR(255), -- connected, voicemail, no_answer, scheduled_follow_up, etc.

    -- Follow-up
    requires_follow_up BOOLEAN DEFAULT false,
    follow_up_date TIMESTAMPTZ,
    follow_up_completed BOOLEAN DEFAULT false,

    -- Automation
    is_automated BOOLEAN DEFAULT false,
    automation_workflow_id UUID,

    -- Attachments
    attachments TEXT[], -- URLs

    -- Timestamps
    interaction_date TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT interaction_reference CHECK (
        lead_id IS NOT NULL OR customer_id IS NOT NULL
    )
);

-- Partnerships Table
CREATE TABLE partnerships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Partner Information
    partner_type partner_type NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(200),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(20),

    -- Address
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),

    -- Agreement Details
    agreement_start_date DATE,
    agreement_end_date DATE,
    is_active BOOLEAN DEFAULT true,

    -- Commission Structure
    commission_type VARCHAR(50), -- percentage, flat_fee, tiered
    commission_rate DECIMAL(5, 2),
    commission_amount DECIMAL(10, 2),
    payment_terms TEXT,

    -- Performance Tracking
    total_referrals INTEGER DEFAULT 0,
    converted_referrals INTEGER DEFAULT 0,
    conversion_rate DECIMAL(5, 2) DEFAULT 0,
    total_revenue_generated DECIMAL(12, 2) DEFAULT 0,
    total_commission_paid DECIMAL(12, 2) DEFAULT 0,

    -- Relationship Management
    relationship_manager_id UUID REFERENCES team_members(id),
    last_contact_date DATE,
    next_followup_date DATE,

    -- Notes
    notes TEXT,
    tags VARCHAR(255)[],
    custom_fields JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Reviews Table
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    project_id UUID REFERENCES projects(id),

    -- Review Details
    platform VARCHAR(100), -- google, facebook, yelp, birdeye, internal
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_title VARCHAR(255),
    review_text TEXT,

    -- Response
    has_response BOOLEAN DEFAULT false,
    response_text TEXT,
    response_date TIMESTAMPTZ,
    responded_by UUID REFERENCES team_members(id),

    -- Display
    is_featured BOOLEAN DEFAULT false,
    is_public BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,

    -- Metadata
    review_url TEXT,
    external_review_id VARCHAR(255),
    helpful_count INTEGER DEFAULT 0,

    -- Timestamps
    review_date TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Appointments Table
CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id),
    customer_id UUID REFERENCES customers(id),

    -- Appointment Details
    appointment_type VARCHAR(100), -- inspection, consultation, follow_up, installation
    scheduled_datetime TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER DEFAULT 60,

    -- Assignment
    assigned_to UUID NOT NULL REFERENCES team_members(id),

    -- Status
    status VARCHAR(50) DEFAULT 'scheduled', -- scheduled, confirmed, completed, cancelled, no_show
    confirmation_sent BOOLEAN DEFAULT false,
    reminder_sent BOOLEAN DEFAULT false,

    -- Location
    location_address VARCHAR(255),
    location_city VARCHAR(100),
    location_state VARCHAR(2),
    location_zip VARCHAR(10),
    location_notes TEXT,

    -- Outcome
    completed_at TIMESTAMPTZ,
    no_show BOOLEAN DEFAULT false,
    no_show_count INTEGER DEFAULT 0,
    cancellation_reason VARCHAR(255),
    outcome_notes TEXT,

    -- Follow-up
    follow_up_required BOOLEAN DEFAULT false,
    follow_up_notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT appointment_reference CHECK (
        lead_id IS NOT NULL OR customer_id IS NOT NULL
    )
);

-- Marketing Campaigns Table
CREATE TABLE marketing_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Campaign Details
    campaign_name VARCHAR(255) NOT NULL,
    campaign_type VARCHAR(100), -- google_ads, facebook_ads, email, direct_mail
    channel VARCHAR(100),

    -- Budget & Spend
    budget DECIMAL(12, 2),
    actual_spend DECIMAL(12, 2) DEFAULT 0,

    -- Dates
    start_date DATE NOT NULL,
    end_date DATE,
    is_active BOOLEAN DEFAULT true,

    -- Performance Metrics
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    leads_generated INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,

    -- ROI Metrics
    cost_per_lead DECIMAL(10, 2) DEFAULT 0,
    cost_per_conversion DECIMAL(10, 2) DEFAULT 0,
    conversion_rate DECIMAL(5, 2) DEFAULT 0,
    revenue_generated DECIMAL(12, 2) DEFAULT 0,
    roi DECIMAL(8, 2) DEFAULT 0,

    -- Targeting
    target_audience JSONB,
    geographic_target VARCHAR(255)[],

    -- Campaign Manager
    campaign_manager_id UUID REFERENCES team_members(id),

    -- Notes
    description TEXT,
    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Automation Workflows Table
CREATE TABLE automation_workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Workflow Details
    workflow_name VARCHAR(255) NOT NULL,
    workflow_type VARCHAR(100), -- follow_up, nurture, emergency, appointment_reminder
    trigger_type VARCHAR(100), -- new_lead, status_change, time_based, manual
    is_active BOOLEAN DEFAULT true,

    -- Configuration
    configuration JSONB NOT NULL, -- Complete workflow definition
    conditions JSONB, -- Conditions to enter workflow

    -- Execution
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5, 2) DEFAULT 0,

    -- Timing
    last_executed_at TIMESTAMPTZ,
    average_execution_time_ms INTEGER,

    -- Owner
    created_by UUID REFERENCES team_members(id),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Leads indexes
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_temperature ON leads(temperature);
CREATE INDEX idx_leads_source ON leads(source);
CREATE INDEX idx_leads_assigned_to ON leads(assigned_to);
CREATE INDEX idx_leads_score ON leads(lead_score DESC);
CREATE INDEX idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_phone ON leads(phone);
CREATE INDEX idx_leads_zip ON leads(zip_code);
CREATE INDEX idx_leads_city ON leads(city);

-- Customers indexes
CREATE INDEX idx_customers_lead_id ON customers(lead_id);
CREATE INDEX idx_customers_account_status ON customers(account_status);
CREATE INDEX idx_customers_lifetime_value ON customers(lifetime_value DESC);
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_phone ON customers(phone);

-- Projects indexes
CREATE INDEX idx_projects_customer_id ON projects(customer_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_type ON projects(project_type);
CREATE INDEX idx_projects_sales_rep ON projects(sales_rep_id);
CREATE INDEX idx_projects_completion_date ON projects(actual_completion_date);

-- Interactions indexes
CREATE INDEX idx_interactions_lead_id ON interactions(lead_id);
CREATE INDEX idx_interactions_customer_id ON interactions(customer_id);
CREATE INDEX idx_interactions_type ON interactions(interaction_type);
CREATE INDEX idx_interactions_date ON interactions(interaction_date DESC);
CREATE INDEX idx_interactions_follow_up ON interactions(follow_up_date) WHERE requires_follow_up = true;

-- Appointments indexes
CREATE INDEX idx_appointments_lead_id ON appointments(lead_id);
CREATE INDEX idx_appointments_customer_id ON appointments(customer_id);
CREATE INDEX idx_appointments_assigned_to ON appointments(assigned_to);
CREATE INDEX idx_appointments_scheduled ON appointments(scheduled_datetime);
CREATE INDEX idx_appointments_status ON appointments(status);

-- Partnerships indexes
CREATE INDEX idx_partnerships_type ON partnerships(partner_type);
CREATE INDEX idx_partnerships_active ON partnerships(is_active);
CREATE INDEX idx_partnerships_company ON partnerships(company_name);

-- Reviews indexes
CREATE INDEX idx_reviews_customer_id ON reviews(customer_id);
CREATE INDEX idx_reviews_rating ON reviews(rating);
CREATE INDEX idx_reviews_platform ON reviews(platform);
CREATE INDEX idx_reviews_featured ON reviews(is_featured) WHERE is_featured = true;

-- Marketing campaigns indexes
CREATE INDEX idx_campaigns_active ON marketing_campaigns(is_active);
CREATE INDEX idx_campaigns_type ON marketing_campaigns(campaign_type);
CREATE INDEX idx_campaigns_dates ON marketing_campaigns(start_date, end_date);

-- Team members indexes
CREATE INDEX idx_team_email ON team_members(email);
CREATE INDEX idx_team_role ON team_members(role);
CREATE INDEX idx_team_active ON team_members(is_active);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Update timestamp triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_interactions_updated_at BEFORE UPDATE ON interactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_partnerships_updated_at BEFORE UPDATE ON partnerships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reviews_updated_at BEFORE UPDATE ON reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON marketing_campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON automation_workflows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_team_updated_at BEFORE UPDATE ON team_members
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE partnerships ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE marketing_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE automation_workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;

-- Policies will be created based on authentication implementation
-- Example policy (to be customized):
-- CREATE POLICY "Team members can view all leads" ON leads
--     FOR SELECT
--     USING (auth.role() = 'authenticated');

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE leads IS 'All prospective customers and their qualification data';
COMMENT ON TABLE customers IS 'Converted leads who have become paying customers';
COMMENT ON TABLE projects IS 'Roofing projects from quote to completion';
COMMENT ON TABLE interactions IS 'All touchpoints with leads and customers';
COMMENT ON TABLE partnerships IS 'Strategic partners providing referrals';
COMMENT ON TABLE reviews IS 'Customer reviews and testimonials';
COMMENT ON TABLE appointments IS 'Scheduled inspections and meetings';
COMMENT ON TABLE marketing_campaigns IS 'Marketing campaign tracking and ROI';
COMMENT ON TABLE automation_workflows IS 'Automated workflow configurations';
COMMENT ON TABLE team_members IS 'Sales and operations team members';
