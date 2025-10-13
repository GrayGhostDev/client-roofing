-- =====================================================
-- Week 11: Sales Automation Database Schema
-- Phase 4.3 - AI-Powered Sales Automation
-- =====================================================
-- Created: 2025-10-11
-- Purpose: Support multi-channel campaigns, proposals, templates
-- =====================================================

-- =====================================================
-- 1. SALES CAMPAIGNS TABLE
-- =====================================================
-- Track campaign configuration and performance
CREATE TABLE IF NOT EXISTS sales_campaigns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    campaign_type VARCHAR(50) NOT NULL, -- 'drip', 'nurture', 'reactivation', 'onboarding'
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- 'draft', 'active', 'paused', 'completed', 'archived'

    -- Target segment configuration
    target_segment JSONB, -- Lead filtering criteria (e.g., {"lead_source": ["website"], "temperature": ["hot", "warm"]})

    -- Campaign settings
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    timezone VARCHAR(50) DEFAULT 'America/Detroit',

    -- Performance metrics (updated in real-time)
    performance_metrics JSONB DEFAULT '{
        "total_leads": 0,
        "emails_sent": 0,
        "emails_opened": 0,
        "emails_clicked": 0,
        "sms_sent": 0,
        "sms_replied": 0,
        "calls_made": 0,
        "calls_connected": 0,
        "appointments_booked": 0,
        "proposals_generated": 0,
        "deals_closed": 0,
        "revenue_generated": 0
    }'::jsonb,

    -- Ownership
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes for common queries
    CONSTRAINT valid_campaign_type CHECK (campaign_type IN ('drip', 'nurture', 'reactivation', 'onboarding', 'promotional', 'seasonal')),
    CONSTRAINT valid_status CHECK (status IN ('draft', 'active', 'paused', 'completed', 'archived'))
);

-- Indexes for performance
CREATE INDEX idx_sales_campaigns_status ON sales_campaigns(status);
CREATE INDEX idx_sales_campaigns_type ON sales_campaigns(campaign_type);
CREATE INDEX idx_sales_campaigns_dates ON sales_campaigns(start_date, end_date);
CREATE INDEX idx_sales_campaigns_created_by ON sales_campaigns(created_by);

-- =====================================================
-- 2. CAMPAIGN STEPS TABLE
-- =====================================================
-- Define campaign sequences and workflows
CREATE TABLE IF NOT EXISTS campaign_steps (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER NOT NULL REFERENCES sales_campaigns(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL, -- Order of execution (1, 2, 3, etc.)
    step_name VARCHAR(255), -- e.g., "Initial Contact", "Follow-up #1"

    -- Channel configuration
    channel VARCHAR(50) NOT NULL, -- 'email', 'sms', 'phone', 'social', 'direct_mail'

    -- Timing configuration
    delay_days INTEGER DEFAULT 0, -- Days after previous step
    delay_hours INTEGER DEFAULT 0, -- Additional hours
    send_time TIME, -- Preferred send time (e.g., '09:00:00')
    send_days JSONB DEFAULT '["monday", "tuesday", "wednesday", "thursday", "friday"]'::jsonb, -- Days of week to send

    -- Content configuration
    template_id INTEGER, -- References email_templates or sms_templates
    template_type VARCHAR(50), -- 'email', 'sms', 'phone_script'
    custom_content TEXT, -- Override template content
    subject_line VARCHAR(500), -- For emails

    -- Execution conditions (when to execute this step)
    conditions JSONB DEFAULT '{}'::jsonb, -- e.g., {"previous_step_opened": true, "lead_temperature": ["hot", "warm"]}

    -- AI personalization settings
    use_ai_personalization BOOLEAN DEFAULT TRUE,
    personalization_config JSONB DEFAULT '{
        "include_property_data": true,
        "include_weather_context": true,
        "include_social_proof": true,
        "include_urgency": true
    }'::jsonb,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_channel CHECK (channel IN ('email', 'sms', 'phone', 'social', 'direct_mail', 'chat')),
    CONSTRAINT positive_delays CHECK (delay_days >= 0 AND delay_hours >= 0),
    UNIQUE (campaign_id, step_number)
);

-- Indexes
CREATE INDEX idx_campaign_steps_campaign ON campaign_steps(campaign_id);
CREATE INDEX idx_campaign_steps_order ON campaign_steps(campaign_id, step_number);
CREATE INDEX idx_campaign_steps_channel ON campaign_steps(channel);

-- =====================================================
-- 3. CAMPAIGN EXECUTIONS TABLE
-- =====================================================
-- Track individual campaign execution per lead
CREATE TABLE IF NOT EXISTS campaign_executions (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER NOT NULL REFERENCES sales_campaigns(id) ON DELETE CASCADE,
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    step_id INTEGER NOT NULL REFERENCES campaign_steps(id) ON DELETE CASCADE,

    -- Execution details
    scheduled_at TIMESTAMP NOT NULL, -- When execution was scheduled
    executed_at TIMESTAMP, -- When actually executed (NULL if pending)
    channel VARCHAR(50) NOT NULL, -- 'email', 'sms', 'phone', etc.

    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'scheduled', -- 'scheduled', 'sent', 'delivered', 'opened', 'clicked', 'replied', 'bounced', 'failed', 'skipped'

    -- Engagement tracking
    engagement_data JSONB DEFAULT '{}'::jsonb, -- e.g., {"opens": 2, "clicks": 1, "open_times": ["2025-10-11 10:30:00"], "links_clicked": ["/quote"]}

    -- Content snapshot (what was actually sent)
    content_snapshot JSONB, -- Store actual content sent for audit trail

    -- Response tracking
    response_received BOOLEAN DEFAULT FALSE,
    response_data JSONB, -- Store reply content, sentiment, etc.
    response_at TIMESTAMP,

    -- Delivery metadata
    external_id VARCHAR(255), -- ID from email/SMS provider
    error_message TEXT, -- If delivery failed

    -- AI metrics
    ai_personalization_used BOOLEAN DEFAULT FALSE,
    ai_confidence_score DECIMAL(3, 2), -- 0.00 to 1.00

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_execution_status CHECK (status IN ('scheduled', 'sent', 'delivered', 'opened', 'clicked', 'replied', 'bounced', 'failed', 'skipped', 'paused')),
    CONSTRAINT valid_execution_channel CHECK (channel IN ('email', 'sms', 'phone', 'social', 'direct_mail', 'chat'))
);

-- Indexes for performance
CREATE INDEX idx_campaign_executions_campaign ON campaign_executions(campaign_id);
CREATE INDEX idx_campaign_executions_lead ON campaign_executions(lead_id);
CREATE INDEX idx_campaign_executions_step ON campaign_executions(step_id);
CREATE INDEX idx_campaign_executions_status ON campaign_executions(status);
CREATE INDEX idx_campaign_executions_scheduled ON campaign_executions(scheduled_at);
CREATE INDEX idx_campaign_executions_executed ON campaign_executions(executed_at);
CREATE INDEX idx_campaign_executions_response ON campaign_executions(response_received) WHERE response_received = TRUE;

-- Unique constraint to prevent duplicate executions
CREATE UNIQUE INDEX idx_unique_campaign_lead_step ON campaign_executions(campaign_id, lead_id, step_id);

-- =====================================================
-- 4. SALES PROPOSALS TABLE
-- =====================================================
-- Track proposal generation and performance
CREATE TABLE IF NOT EXISTS sales_proposals (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,

    -- Proposal identification
    proposal_number VARCHAR(50) UNIQUE NOT NULL, -- e.g., "PROP-2025-10-001"
    version INTEGER DEFAULT 1, -- Support multiple versions

    -- Property intelligence
    property_data JSONB NOT NULL, -- Address, home value, roof type, square footage, etc.
    property_intelligence JSONB, -- AI-generated insights about property

    -- Material recommendations
    material_recommendations JSONB NOT NULL, -- Array of material options with specs and pricing
    recommended_tier VARCHAR(50), -- 'ultra_premium', 'professional', 'standard'

    -- Pricing
    pricing_options JSONB NOT NULL, -- Good/Better/Best tiers with detailed breakdowns
    selected_option VARCHAR(50), -- Which tier customer selected
    final_price DECIMAL(10, 2),
    discount_applied DECIMAL(10, 2) DEFAULT 0.00,

    -- Financing
    financing_options JSONB, -- Available financing plans
    financing_selected JSONB, -- Customer's financing choice

    -- Social proof
    social_proof JSONB, -- Nearby projects, testimonials, before/after photos

    -- Content
    custom_notes TEXT, -- Sales rep custom notes
    terms_and_conditions TEXT,
    warranty_details TEXT,

    -- Files
    pdf_url TEXT, -- URL to generated PDF
    pdf_generated_at TIMESTAMP,
    attachments JSONB, -- Additional files (blueprints, photos, etc.)

    -- Tracking
    view_count INTEGER DEFAULT 0,
    last_viewed_at TIMESTAMP,
    view_history JSONB DEFAULT '[]'::jsonb, -- Array of view events with timestamps

    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- 'draft', 'sent', 'viewed', 'accepted', 'rejected', 'expired', 'revised'

    -- Dates
    sent_at TIMESTAMP,
    accepted_at TIMESTAMP,
    rejected_at TIMESTAMP,
    expires_at TIMESTAMP, -- Proposal expiration for urgency

    -- Rejection tracking
    rejection_reason TEXT,
    competitor_chosen VARCHAR(255),

    -- Ownership
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- AI generation metrics
    ai_generated BOOLEAN DEFAULT TRUE,
    generation_time_seconds DECIMAL(5, 2), -- How long AI took to generate
    ai_model_used VARCHAR(100), -- e.g., "gpt-4-turbo"

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_proposal_status CHECK (status IN ('draft', 'sent', 'viewed', 'accepted', 'rejected', 'expired', 'revised')),
    CONSTRAINT valid_tier CHECK (recommended_tier IN ('ultra_premium', 'professional', 'standard', 'economy') OR recommended_tier IS NULL)
);

-- Indexes
CREATE INDEX idx_sales_proposals_lead ON sales_proposals(lead_id);
CREATE INDEX idx_sales_proposals_project ON sales_proposals(project_id);
CREATE INDEX idx_sales_proposals_status ON sales_proposals(status);
CREATE INDEX idx_sales_proposals_number ON sales_proposals(proposal_number);
CREATE INDEX idx_sales_proposals_created ON sales_proposals(created_at);
CREATE INDEX idx_sales_proposals_expires ON sales_proposals(expires_at);
CREATE INDEX idx_sales_proposals_accepted ON sales_proposals(accepted_at) WHERE accepted_at IS NOT NULL;

-- =====================================================
-- 5. EMAIL TEMPLATES TABLE
-- =====================================================
-- Reusable email templates with performance tracking
CREATE TABLE IF NOT EXISTS email_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL, -- 'initial_contact', 'follow_up', 'proposal', 'nurture', 'reactivation', 'promotional'

    -- Template content
    subject_line TEXT NOT NULL,
    html_content TEXT NOT NULL,
    plain_text_content TEXT, -- Fallback for email clients

    -- Personalization
    variables JSONB DEFAULT '[]'::jsonb, -- Array of available variables: ["first_name", "property_address", "home_value", etc.]
    use_ai_enhancement BOOLEAN DEFAULT TRUE, -- Whether to enhance with GPT-5

    -- A/B testing
    is_control_version BOOLEAN DEFAULT FALSE,
    variant_of INTEGER REFERENCES email_templates(id) ON DELETE SET NULL, -- Link to parent template for A/B tests

    -- Performance metrics (updated from campaign_executions)
    performance_metrics JSONB DEFAULT '{
        "sent_count": 0,
        "delivered_count": 0,
        "open_count": 0,
        "click_count": 0,
        "reply_count": 0,
        "bounce_count": 0,
        "unsubscribe_count": 0,
        "open_rate": 0.0,
        "click_rate": 0.0,
        "reply_rate": 0.0
    }'::jsonb,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_approved BOOLEAN DEFAULT FALSE, -- Requires approval for compliance
    approved_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMP,

    -- Ownership
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_email_category CHECK (category IN ('initial_contact', 'follow_up', 'proposal', 'nurture', 'reactivation', 'promotional', 'transactional', 'survey'))
);

-- Indexes
CREATE INDEX idx_email_templates_category ON email_templates(category);
CREATE INDEX idx_email_templates_active ON email_templates(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_email_templates_variant ON email_templates(variant_of);
CREATE INDEX idx_email_templates_created ON email_templates(created_at);

-- =====================================================
-- 6. SMS TEMPLATES TABLE
-- =====================================================
-- Reusable SMS templates
CREATE TABLE IF NOT EXISTS sms_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL, -- 'initial_contact', 'follow_up', 'appointment_reminder', 'quick_question'

    -- Template content
    message_content TEXT NOT NULL, -- Max 160 characters recommended
    character_count INTEGER,

    -- Personalization
    variables JSONB DEFAULT '[]'::jsonb,
    use_ai_enhancement BOOLEAN DEFAULT TRUE,

    -- Performance metrics
    performance_metrics JSONB DEFAULT '{
        "sent_count": 0,
        "delivered_count": 0,
        "reply_count": 0,
        "opt_out_count": 0,
        "reply_rate": 0.0
    }'::jsonb,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_approved BOOLEAN DEFAULT FALSE,
    approved_by INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_sms_category CHECK (category IN ('initial_contact', 'follow_up', 'appointment_reminder', 'quick_question', 'proposal_followup', 'thank_you'))
);

-- Indexes
CREATE INDEX idx_sms_templates_category ON sms_templates(category);
CREATE INDEX idx_sms_templates_active ON sms_templates(is_active) WHERE is_active = TRUE;

-- =====================================================
-- 7. LEAD ENGAGEMENT SCORES TABLE
-- =====================================================
-- Track real-time engagement scoring for smart cadence
CREATE TABLE IF NOT EXISTS lead_engagement_scores (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Overall engagement score (0-100)
    engagement_score INTEGER NOT NULL DEFAULT 50,
    engagement_level VARCHAR(50) NOT NULL DEFAULT 'medium', -- 'very_high', 'high', 'medium', 'low', 'very_low'

    -- Channel-specific scores
    email_engagement_score INTEGER DEFAULT 50,
    sms_engagement_score INTEGER DEFAULT 50,
    phone_engagement_score INTEGER DEFAULT 50,

    -- Behavioral signals
    email_opens_last_7_days INTEGER DEFAULT 0,
    email_clicks_last_7_days INTEGER DEFAULT 0,
    sms_replies_last_7_days INTEGER DEFAULT 0,
    calls_answered_last_7_days INTEGER DEFAULT 0,
    website_visits_last_7_days INTEGER DEFAULT 0,

    -- Timing intelligence
    best_contact_day VARCHAR(20), -- 'monday', 'tuesday', etc.
    best_contact_time TIME, -- e.g., '14:00:00'
    preferred_channel VARCHAR(50), -- 'email', 'sms', 'phone'

    -- Cadence optimization
    last_contact_at TIMESTAMP,
    next_recommended_contact_at TIMESTAMP,
    contact_frequency_days INTEGER DEFAULT 3, -- Adaptive frequency

    -- Buying signals
    hot_lead_signals JSONB DEFAULT '[]'::jsonb, -- Array of detected signals
    buying_intent_score INTEGER DEFAULT 0, -- 0-100

    -- Sentiment
    overall_sentiment VARCHAR(50) DEFAULT 'neutral', -- 'very_positive', 'positive', 'neutral', 'negative', 'very_negative'
    sentiment_trend VARCHAR(50) DEFAULT 'stable', -- 'improving', 'stable', 'declining'

    -- Timestamps
    calculated_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_engagement_level CHECK (engagement_level IN ('very_high', 'high', 'medium', 'low', 'very_low')),
    CONSTRAINT valid_scores CHECK (engagement_score BETWEEN 0 AND 100),
    UNIQUE (lead_id)
);

-- Indexes
CREATE INDEX idx_lead_engagement_lead ON lead_engagement_scores(lead_id);
CREATE INDEX idx_lead_engagement_score ON lead_engagement_scores(engagement_score);
CREATE INDEX idx_lead_engagement_level ON lead_engagement_scores(engagement_level);
CREATE INDEX idx_lead_engagement_next_contact ON lead_engagement_scores(next_recommended_contact_at);

-- =====================================================
-- 8. PROPERTY INTELLIGENCE CACHE TABLE
-- =====================================================
-- Cache property intelligence data to reduce API calls
CREATE TABLE IF NOT EXISTS property_intelligence_cache (
    id SERIAL PRIMARY KEY,
    address TEXT NOT NULL,
    normalized_address TEXT NOT NULL, -- Standardized format for matching
    zip_code VARCHAR(10),

    -- Property data
    property_data JSONB NOT NULL, -- Raw data from Zillow API
    home_value DECIMAL(12, 2),
    year_built INTEGER,
    square_footage INTEGER,
    lot_size INTEGER,
    bedrooms INTEGER,
    bathrooms DECIMAL(3, 1),
    property_type VARCHAR(100),

    -- Roof intelligence
    estimated_roof_age INTEGER,
    estimated_roof_replacement_date DATE,
    roof_material VARCHAR(100),
    roof_condition VARCHAR(50), -- 'excellent', 'good', 'fair', 'poor'

    -- Market intelligence
    neighborhood_avg_home_value DECIMAL(12, 2),
    neighborhood_data JSONB,
    market_trend VARCHAR(50), -- 'hot', 'rising', 'stable', 'cooling'

    -- Weather risk
    weather_risk_score INTEGER, -- 0-100
    recent_weather_events JSONB,

    -- Recommended tier
    recommended_pricing_tier VARCHAR(50), -- 'ultra_premium', 'professional', 'standard'

    -- Cache metadata
    data_source VARCHAR(100), -- 'zillow', 'public_records', 'manual'
    is_verified BOOLEAN DEFAULT FALSE,
    last_verified_at TIMESTAMP,

    -- Timestamps
    cached_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '30 days'),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE (normalized_address)
);

-- Indexes
CREATE INDEX idx_property_intelligence_address ON property_intelligence_cache(normalized_address);
CREATE INDEX idx_property_intelligence_zip ON property_intelligence_cache(zip_code);
CREATE INDEX idx_property_intelligence_value ON property_intelligence_cache(home_value);
CREATE INDEX idx_property_intelligence_expires ON property_intelligence_cache(expires_at);

-- =====================================================
-- 9. CAMPAIGN ANALYTICS MATERIALIZED VIEW
-- =====================================================
-- Pre-computed analytics for dashboard performance
CREATE MATERIALIZED VIEW IF NOT EXISTS campaign_analytics_summary AS
SELECT
    c.id AS campaign_id,
    c.name AS campaign_name,
    c.campaign_type,
    c.status,
    c.created_at,

    -- Lead counts
    COUNT(DISTINCT ce.lead_id) AS total_leads,

    -- Email metrics
    SUM(CASE WHEN ce.channel = 'email' AND ce.status = 'sent' THEN 1 ELSE 0 END) AS emails_sent,
    SUM(CASE WHEN ce.channel = 'email' AND ce.status = 'opened' THEN 1 ELSE 0 END) AS emails_opened,
    SUM(CASE WHEN ce.channel = 'email' AND ce.status = 'clicked' THEN 1 ELSE 0 END) AS emails_clicked,

    -- SMS metrics
    SUM(CASE WHEN ce.channel = 'sms' AND ce.status = 'sent' THEN 1 ELSE 0 END) AS sms_sent,
    SUM(CASE WHEN ce.channel = 'sms' AND ce.response_received = TRUE THEN 1 ELSE 0 END) AS sms_replied,

    -- Engagement metrics
    SUM(CASE WHEN ce.response_received = TRUE THEN 1 ELSE 0 END) AS total_responses,

    -- Conversion metrics
    COUNT(DISTINCT CASE WHEN sp.id IS NOT NULL THEN ce.lead_id END) AS proposals_generated,
    COUNT(DISTINCT CASE WHEN sp.status = 'accepted' THEN ce.lead_id END) AS deals_closed,

    -- Rates
    CASE
        WHEN SUM(CASE WHEN ce.channel = 'email' AND ce.status = 'sent' THEN 1 ELSE 0 END) > 0
        THEN ROUND(100.0 * SUM(CASE WHEN ce.channel = 'email' AND ce.status = 'opened' THEN 1 ELSE 0 END) /
                   SUM(CASE WHEN ce.channel = 'email' AND ce.status = 'sent' THEN 1 ELSE 0 END), 2)
        ELSE 0
    END AS email_open_rate,

    CASE
        WHEN COUNT(DISTINCT ce.lead_id) > 0
        THEN ROUND(100.0 * COUNT(DISTINCT CASE WHEN sp.status = 'accepted' THEN ce.lead_id END) /
                   COUNT(DISTINCT ce.lead_id), 2)
        ELSE 0
    END AS conversion_rate

FROM sales_campaigns c
LEFT JOIN campaign_executions ce ON c.id = ce.campaign_id
LEFT JOIN sales_proposals sp ON ce.lead_id = sp.lead_id
GROUP BY c.id, c.name, c.campaign_type, c.status, c.created_at;

-- Index on materialized view
CREATE INDEX idx_campaign_analytics_campaign ON campaign_analytics_summary(campaign_id);
CREATE INDEX idx_campaign_analytics_status ON campaign_analytics_summary(status);

-- =====================================================
-- 10. FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to update campaign performance metrics
CREATE OR REPLACE FUNCTION update_campaign_performance_metrics()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE sales_campaigns
    SET performance_metrics = jsonb_set(
        performance_metrics,
        ARRAY[
            CASE NEW.channel
                WHEN 'email' THEN
                    CASE NEW.status
                        WHEN 'sent' THEN 'emails_sent'
                        WHEN 'opened' THEN 'emails_opened'
                        WHEN 'clicked' THEN 'emails_clicked'
                        ELSE NULL
                    END
                WHEN 'sms' THEN
                    CASE NEW.status
                        WHEN 'sent' THEN 'sms_sent'
                        WHEN 'replied' THEN 'sms_replied'
                        ELSE NULL
                    END
                WHEN 'phone' THEN 'calls_made'
                ELSE NULL
            END
        ],
        to_jsonb(
            COALESCE((performance_metrics->
                CASE NEW.channel
                    WHEN 'email' THEN
                        CASE NEW.status
                            WHEN 'sent' THEN 'emails_sent'
                            WHEN 'opened' THEN 'emails_opened'
                            WHEN 'clicked' THEN 'emails_clicked'
                            ELSE 'emails_sent'
                        END
                    WHEN 'sms' THEN
                        CASE NEW.status
                            WHEN 'sent' THEN 'sms_sent'
                            WHEN 'replied' THEN 'sms_replied'
                            ELSE 'sms_sent'
                        END
                    WHEN 'phone' THEN 'calls_made'
                    ELSE 'emails_sent'
                END
            )::integer, 0) + 1
        )
    ),
    updated_at = NOW()
    WHERE id = NEW.campaign_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update campaign metrics
CREATE TRIGGER trigger_update_campaign_performance
    AFTER INSERT OR UPDATE ON campaign_executions
    FOR EACH ROW
    EXECUTE FUNCTION update_campaign_performance_metrics();

-- Function to refresh campaign analytics
CREATE OR REPLACE FUNCTION refresh_campaign_analytics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY campaign_analytics_summary;
END;
$$ LANGUAGE plpgsql;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to all tables
CREATE TRIGGER trigger_sales_campaigns_updated_at BEFORE UPDATE ON sales_campaigns FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_campaign_steps_updated_at BEFORE UPDATE ON campaign_steps FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_campaign_executions_updated_at BEFORE UPDATE ON campaign_executions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_sales_proposals_updated_at BEFORE UPDATE ON sales_proposals FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_email_templates_updated_at BEFORE UPDATE ON email_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_sms_templates_updated_at BEFORE UPDATE ON sms_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_lead_engagement_scores_updated_at BEFORE UPDATE ON lead_engagement_scores FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_property_intelligence_cache_updated_at BEFORE UPDATE ON property_intelligence_cache FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 11. INITIAL DATA SEEDING
-- =====================================================

-- Insert default email templates
INSERT INTO email_templates (name, description, category, subject_line, html_content, variables, is_active, is_approved, approved_at, created_at) VALUES
('Initial Contact - Premium', 'First touchpoint for premium properties', 'initial_contact',
'{{first_name}}, your {{property_type}} roof in {{neighborhood}}',
'<html><body><p>Hi {{first_name}},</p><p>I noticed your beautiful {{property_type}} home at {{address}}. As a roofing specialist serving {{neighborhood}}, I wanted to reach out because homes like yours (built in {{year_built}}) typically need roof attention around now.</p><p>{{weather_context}}</p><p>{{social_proof}}</p><p>Would you be open to a free, no-obligation roof inspection?</p><p><a href="{{scheduling_link}}">Schedule Inspection</a></p></body></html>',
'["first_name", "property_type", "address", "neighborhood", "year_built", "weather_context", "social_proof", "scheduling_link"]'::jsonb,
TRUE, TRUE, NOW(), NOW()),

('Follow-Up #1 - Did You See Our Email', 'First follow-up after no response', 'follow_up',
'{{first_name}}, quick question about your roof',
'<html><body><p>Hi {{first_name}},</p><p>I wanted to follow up on my previous email about your {{property_type}} home at {{address}}.</p><p>Have you had a chance to consider a roof inspection? Many homeowners in {{neighborhood}} are proactively checking their roofs after {{weather_event}}.</p><p><a href="{{scheduling_link}}">Schedule Free Inspection</a></p></body></html>',
'["first_name", "property_type", "address", "neighborhood", "weather_event", "scheduling_link"]'::jsonb,
TRUE, TRUE, NOW(), NOW()),

('Proposal Delivery', 'Email to deliver proposal PDF', 'proposal',
'Your custom roofing proposal for {{address}}',
'<html><body><p>Hi {{first_name}},</p><p>Thank you for the opportunity to provide a proposal for your {{property_type}} home at {{address}}.</p><p>I''ve prepared three carefully selected options designed specifically for homes like yours in {{neighborhood}}.</p><p><a href="{{proposal_link}}">View Your Proposal</a></p><p>The proposal includes:</p><ul><li>Detailed scope of work</li><li>Premium material options</li><li>Flexible financing plans</li><li>Testimonials from your neighbors</li></ul><p>Questions? Call me directly at {{phone}}.</p></body></html>',
'["first_name", "property_type", "address", "neighborhood", "proposal_link", "phone"]'::jsonb,
TRUE, TRUE, NOW(), NOW());

-- Insert default SMS templates
INSERT INTO sms_templates (name, description, category, message_content, character_count, variables, is_active, is_approved, created_at) VALUES
('Quick Follow-Up', 'Short SMS after email', 'follow_up',
'Hi {{first_name}}, {{rep_name}} from iSwitch Roofs. Saw my email about your roof? Reply YES for a free inspection this week. {{scheduling_link}}',
145,
'["first_name", "rep_name", "scheduling_link"]'::jsonb,
TRUE, TRUE, NOW()),

('Appointment Reminder', 'Reminder day before appointment', 'appointment_reminder',
'Hi {{first_name}}! Reminder: Your roof inspection is tomorrow at {{time}}. See you then! Reply CANCEL if you need to reschedule.',
130,
'["first_name", "time"]'::jsonb,
TRUE, TRUE, NOW());

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================
-- Week 11 database schema ready for sales automation
-- Total tables: 9 (8 new + 1 materialized view)
-- Total indexes: 45+
-- Total triggers: 9
-- Total functions: 3
-- =====================================================
