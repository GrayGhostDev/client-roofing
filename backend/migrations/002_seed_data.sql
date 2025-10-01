-- Seed Data for iSwitch Roofs CRM
-- Version: 1.0.0
-- Date: 2025-10-01
-- Purpose: Test data for development and testing

-- ============================================================================
-- TEAM MEMBERS
-- ============================================================================

INSERT INTO team_members (id, email, first_name, last_name, phone, role, territory, is_active, working_hours) VALUES
('11111111-1111-1111-1111-111111111111', 'admin@iswitchroofs.com', 'John', 'Admin', '+1234567890', 'admin', 'All', true,
    '{"monday": {"start": "08:00", "end": "18:00"}, "tuesday": {"start": "08:00", "end": "18:00"}, "wednesday": {"start": "08:00", "end": "18:00"}, "thursday": {"start": "08:00", "end": "18:00"}, "friday": {"start": "08:00", "end": "18:00"}}'::jsonb),
('22222222-2222-2222-2222-222222222222', 'sarah.manager@iswitchroofs.com', 'Sarah', 'Johnson', '+1234567891', 'sales_manager', 'All', true,
    '{"monday": {"start": "08:00", "end": "18:00"}, "tuesday": {"start": "08:00", "end": "18:00"}, "wednesday": {"start": "08:00", "end": "18:00"}, "thursday": {"start": "08:00", "end": "18:00"}, "friday": {"start": "08:00", "end": "18:00"}}'::jsonb),
('33333333-3333-3333-3333-333333333333', 'mike.sales@iswitchroofs.com', 'Mike', 'Thompson', '+1234567892', 'sales_rep', 'Oakland County', true,
    '{"monday": {"start": "08:00", "end": "18:00"}, "tuesday": {"start": "08:00", "end": "18:00"}, "wednesday": {"start": "08:00", "end": "18:00"}, "thursday": {"start": "08:00", "end": "18:00"}, "friday": {"start": "08:00", "end": "18:00"}}'::jsonb),
('44444444-4444-4444-4444-444444444444', 'lisa.sales@iswitchroofs.com', 'Lisa', 'Martinez', '+1234567893', 'sales_rep', 'Wayne County', true,
    '{"monday": {"start": "08:00", "end": "18:00"}, "tuesday": {"start": "08:00", "end": "18:00"}, "wednesday": {"start": "08:00", "end": "18:00"}, "thursday": {"start": "08:00", "end": "18:00"}, "friday": {"start": "08:00", "end": "18:00"}}'::jsonb);

-- ============================================================================
-- LEADS (Sample leads with various temperatures and sources)
-- ============================================================================

-- Hot Lead - Emergency repair
INSERT INTO leads (
    id, first_name, last_name, email, phone, address, city, state, zip_code,
    source, status, temperature, lead_score, property_age, property_value,
    urgency_level, budget_range, is_insurance_claim, has_existing_damage,
    assigned_to, first_contact_at
) VALUES (
    'a0000001-0001-0001-0001-000000000001',
    'Robert', 'Williams', 'robert.williams@email.com', '+1248555001',
    '123 Oak Drive', 'Birmingham', 'MI', '48009',
    'website_form', 'contacted', 'hot', 95,
    25, 650000.00, 'immediate', '20k_plus', true, true,
    '33333333-3333-3333-3333-333333333333',
    NOW() - INTERVAL '2 hours'
);

-- Hot Lead - Storm damage with insurance claim
INSERT INTO leads (
    id, first_name, last_name, email, phone, address, city, state, zip_code,
    source, status, temperature, lead_score, property_age, property_value,
    urgency_level, budget_range, is_insurance_claim, has_existing_damage,
    damage_description, assigned_to, first_contact_at
) VALUES (
    'a0000001-0001-0001-0001-000000000002',
    'Jennifer', 'Anderson', 'jennifer.anderson@email.com', '+1248555002',
    '456 Maple Street', 'Bloomfield Hills', 'MI', '48302',
    'storm_response', 'inspection_completed', 'hot', 92,
    30, 850000.00, 'immediate', '20k_plus', true, true,
    'Multiple shingles blown off, visible damage to flashing',
    '33333333-3333-3333-3333-333333333333',
    NOW() - INTERVAL '1 day'
);

-- Warm Lead - Planning replacement
INSERT INTO leads (
    id, first_name, last_name, email, phone, address, city, state, zip_code,
    source, status, temperature, lead_score, property_age, property_value,
    urgency_level, budget_range, assigned_to, first_contact_at
) VALUES (
    'a0000001-0001-0001-0001-000000000003',
    'David', 'Miller', 'david.miller@email.com', '+1248555003',
    '789 Pine Avenue', 'Troy', 'MI', '48083',
    'google_lsa', 'qualified', 'warm', 75,
    18, 425000.00, '30_days', '15-20k',
    '44444444-4444-4444-4444-444444444444',
    NOW() - INTERVAL '3 days'
);

-- Warm Lead - Referral from partner
INSERT INTO leads (
    id, first_name, last_name, email, phone, address, city, state, zip_code,
    source, source_detail, status, temperature, lead_score, property_age, property_value,
    urgency_level, budget_range, assigned_to, first_contact_at
) VALUES (
    'a0000001-0001-0001-0001-000000000004',
    'Susan', 'Davis', 'susan.davis@email.com', '+1248555004',
    '321 Cedar Lane', 'Rochester Hills', 'MI', '48309',
    'partner_referral', 'State Farm Agent - John Smith', 'contacted', 'warm', 78,
    22, 475000.00, '90_days', '15-20k',
    '33333333-3333-3333-3333-333333333333',
    NOW() - INTERVAL '5 days'
);

-- Cool Lead - Exploratory
INSERT INTO leads (
    id, first_name, last_name, email, phone, address, city, state, zip_code,
    source, status, temperature, lead_score, property_age, property_value,
    urgency_level, budget_range, assigned_to, first_contact_at
) VALUES (
    'a0000001-0001-0001-0001-000000000005',
    'Michael', 'Brown', 'michael.brown@email.com', '+1248555005',
    '654 Elm Street', 'West Bloomfield', 'MI', '48322',
    'organic_search', 'new', 'cool', 55,
    12, 380000.00, '6_months', '10-15k',
    '44444444-4444-4444-4444-444444444444',
    NULL
);

-- Cool Lead - Price shopping
INSERT INTO leads (
    id, first_name, last_name, email, phone, address, city, state, zip_code,
    source, status, temperature, lead_score, property_age, property_value,
    urgency_level, budget_range, has_other_quotes, competitor_quotes, price_sensitive,
    assigned_to, first_contact_at
) VALUES (
    'a0000001-0001-0001-0001-000000000006',
    'Patricia', 'Wilson', 'patricia.wilson@email.com', '+1248555006',
    '987 Birch Road', 'Grosse Pointe', 'MI', '48230',
    'google_ads', 'contacted', 'cool', 52,
    16, 520000.00, '90_days', '10-15k', true, 2, true,
    '44444444-4444-4444-4444-444444444444',
    NOW() - INTERVAL '7 days'
);

-- Cold Lead - Just browsing
INSERT INTO leads (
    id, first_name, last_name, email, phone, address, city, state, zip_code,
    source, status, temperature, lead_score, property_age, property_value,
    urgency_level, budget_range, assigned_to
) VALUES (
    'a0000001-0001-0001-0001-000000000007',
    'James', 'Moore', 'james.moore@email.com', '+1248555007',
    '147 Spruce Court', 'Novi', 'MI', '48375',
    'facebook_ads', 'new', 'cold', 38,
    8, 295000.00, 'exploratory', 'under_10k',
    '33333333-3333-3333-3333-333333333333'
);

-- ============================================================================
-- CUSTOMERS (Converted leads)
-- ============================================================================

INSERT INTO customers (
    id, lead_id, first_name, last_name, email, phone,
    address, city, state, zip_code,
    account_status, customer_since, lifetime_value, total_projects,
    satisfaction_score, has_left_review, review_rating
) VALUES (
    'c0000001-0001-0001-0001-000000000001',
    NULL, -- Can link to a lead if needed
    'Thomas', 'Taylor', 'thomas.taylor@email.com', '+1248555010',
    '111 Customer Lane', 'Birmingham', 'MI', '48009',
    'active', '2024-03-15', 45000.00, 1,
    9, true, 5
);

INSERT INTO customers (
    id, lead_id, first_name, last_name, email, phone,
    address, city, state, zip_code,
    account_status, customer_since, lifetime_value, total_projects,
    satisfaction_score, has_left_review, review_rating, has_referred_others, total_referrals
) VALUES (
    'c0000001-0001-0001-0001-000000000002',
    NULL,
    'Nancy', 'Jackson', 'nancy.jackson@email.com', '+1248555011',
    '222 Customer Drive', 'Bloomfield Hills', 'MI', '48302',
    'active', '2024-01-10', 52000.00, 1,
    10, true, 5, true, 3
);

-- ============================================================================
-- PROJECTS
-- ============================================================================

INSERT INTO projects (
    id, customer_id, project_name, project_type, status,
    quoted_amount, final_amount, deposit_amount, amount_paid,
    is_insurance_claim, insurance_company, claim_amount,
    quote_date, approval_date, scheduled_start_date, actual_start_date,
    actual_completion_date, roofing_material, square_footage, warranty_years,
    sales_rep_id, quality_check_passed
) VALUES (
    'p0000001-0001-0001-0001-000000000001',
    'c0000001-0001-0001-0001-000000000001',
    'Taylor Residence - Full Roof Replacement',
    'full_replacement', 'completed',
    45000.00, 45000.00, 13500.00, 45000.00,
    false, NULL, NULL,
    '2024-02-15', '2024-02-20', '2024-03-10', '2024-03-10',
    '2024-03-15', 'Architectural Shingles - GAF Timberline HDZ',
    2800, 50,
    '33333333-3333-3333-3333-333333333333',
    true
);

INSERT INTO projects (
    id, customer_id, project_name, project_type, status,
    quoted_amount, final_amount, deposit_amount, amount_paid,
    is_insurance_claim, insurance_company, claim_number, claim_amount,
    quote_date, approval_date, scheduled_start_date, actual_start_date,
    actual_completion_date, roofing_material, square_footage, warranty_years,
    sales_rep_id, quality_check_passed
) VALUES (
    'p0000001-0001-0001-0001-000000000002',
    'c0000001-0001-0001-0001-000000000002',
    'Jackson Residence - Storm Damage Repair',
    'insurance_claim', 'completed',
    52000.00, 52000.00, 0.00, 52000.00,
    true, 'State Farm', 'SF-2024-123456', 52000.00,
    '2023-12-15', '2024-01-05', '2024-01-08', '2024-01-08',
    '2024-01-10', 'Premium Architectural Shingles - Owens Corning Duration',
    3200, 50,
    '33333333-3333-3333-3333-333333333333',
    true
);

-- ============================================================================
-- INTERACTIONS
-- ============================================================================

-- Initial contact for hot lead
INSERT INTO interactions (
    lead_id, interaction_type, channel, subject, description,
    team_member_id, duration_seconds, outcome, sentiment_score
) VALUES (
    'a0000001-0001-0001-0001-000000000001',
    'phone_call', 'phone', 'Initial Contact - Emergency Repair',
    'Customer called about leak in living room. Urgent repair needed. Scheduled same-day inspection.',
    '33333333-3333-3333-3333-333333333333',
    420, 'scheduled_follow_up', 4
);

-- Follow-up email
INSERT INTO interactions (
    lead_id, interaction_type, channel, subject, description,
    team_member_id, is_automated
) VALUES (
    'a0000001-0001-0001-0001-000000000001',
    'email', 'email', 'Inspection Confirmation',
    'Sent automated confirmation email with inspection details and what to expect.',
    '33333333-3333-3333-3333-333333333333',
    true
);

-- ============================================================================
-- APPOINTMENTS
-- ============================================================================

INSERT INTO appointments (
    id, lead_id, appointment_type, scheduled_datetime, duration_minutes,
    assigned_to, status, location_address, location_city, location_state, location_zip
) VALUES (
    'ap000001-0001-0001-0001-000000000001',
    'a0000001-0001-0001-0001-000000000001',
    'inspection', NOW() + INTERVAL '4 hours', 60,
    '33333333-3333-3333-3333-333333333333',
    'confirmed',
    '123 Oak Drive', 'Birmingham', 'MI', '48009'
);

INSERT INTO appointments (
    id, lead_id, appointment_type, scheduled_datetime, duration_minutes,
    assigned_to, status, completed_at, location_address, location_city, location_state, location_zip
) VALUES (
    'ap000001-0001-0001-0001-000000000002',
    'a0000001-0001-0001-0001-000000000002',
    'inspection', NOW() - INTERVAL '1 day', 90,
    '33333333-3333-3333-3333-333333333333',
    'completed',
    NOW() - INTERVAL '23 hours',
    '456 Maple Street', 'Bloomfield Hills', 'MI', '48302'
);

-- ============================================================================
-- PARTNERSHIPS
-- ============================================================================

INSERT INTO partnerships (
    id, partner_type, company_name, contact_name, contact_email, contact_phone,
    city, state, agreement_start_date, is_active,
    commission_type, commission_rate, total_referrals, converted_referrals,
    relationship_manager_id
) VALUES (
    'pr000001-0001-0001-0001-000000000001',
    'insurance_agent', 'State Farm - John Smith Agency', 'John Smith',
    'john.smith@statefarm.com', '+1248555100',
    'Birmingham', 'MI', '2024-01-01', true,
    'percentage', 5.00, 12, 8,
    '22222222-2222-2222-2222-222222222222'
);

INSERT INTO partnerships (
    id, partner_type, company_name, contact_name, contact_email, contact_phone,
    city, state, agreement_start_date, is_active,
    commission_type, commission_amount, total_referrals, converted_referrals,
    relationship_manager_id
) VALUES (
    'pr000001-0001-0001-0001-000000000002',
    'real_estate_agent', 'Keller Williams - Sarah Johnson', 'Sarah Johnson',
    'sarah.j@kw.com', '+1248555101',
    'Troy', 'MI', '2024-02-01', true,
    'flat_fee', 250.00, 8, 5,
    '22222222-2222-2222-2222-222222222222'
);

-- ============================================================================
-- REVIEWS
-- ============================================================================

INSERT INTO reviews (
    customer_id, project_id, platform, rating, review_title, review_text,
    is_featured, is_public, review_date
) VALUES (
    'c0000001-0001-0001-0001-000000000001',
    'p0000001-0001-0001-0001-000000000001',
    'google', 5,
    'Outstanding Service!',
    'iSwitch Roofs did an amazing job on our home. Professional team, completed on time, and the roof looks fantastic. Highly recommend!',
    true, true, '2024-03-20'
);

INSERT INTO reviews (
    customer_id, project_id, platform, rating, review_title, review_text,
    has_response, response_text, responded_by, response_date,
    is_featured, is_public, review_date
) VALUES (
    'c0000001-0001-0001-0001-000000000002',
    'p0000001-0001-0001-0001-000000000002',
    'google', 5,
    'Perfect Insurance Claim Handling',
    'They handled everything with our insurance company. No stress, no hassle. The new roof looks beautiful and we couldn''t be happier!',
    true,
    'Thank you Nancy! We''re thrilled you had such a positive experience. It''s our pleasure to make the insurance process as smooth as possible.',
    '22222222-2222-2222-2222-222222222222',
    '2024-01-15',
    true, true, '2024-01-12'
);

-- ============================================================================
-- MARKETING CAMPAIGNS
-- ============================================================================

INSERT INTO marketing_campaigns (
    id, campaign_name, campaign_type, channel, budget, actual_spend,
    start_date, end_date, is_active,
    impressions, clicks, leads_generated, conversions,
    campaign_manager_id
) VALUES (
    'mc000001-0001-0001-0001-000000000001',
    'Spring 2024 - Storm Season Prep',
    'google_ads', 'search', 5000.00, 3200.00,
    '2024-03-01', '2024-05-31', true,
    25000, 1250, 32, 8,
    '22222222-2222-2222-2222-222222222222'
);

INSERT INTO marketing_campaigns (
    id, campaign_name, campaign_type, channel, budget, actual_spend,
    start_date, end_date, is_active,
    impressions, clicks, leads_generated, conversions,
    campaign_manager_id
) VALUES (
    'mc000001-0001-0001-0001-000000000002',
    'Facebook - Premium Neighborhoods',
    'facebook_ads', 'social', 3000.00, 2100.00,
    '2024-04-01', '2024-06-30', true,
    45000, 890, 18, 4,
    '22222222-2222-2222-2222-222222222222'
);

-- ============================================================================
-- AUTOMATION WORKFLOWS
-- ============================================================================

INSERT INTO automation_workflows (
    id, workflow_name, workflow_type, trigger_type, is_active,
    configuration, execution_count, success_count,
    created_by
) VALUES (
    'aw000001-0001-0001-0001-000000000001',
    '2-Minute Lead Response',
    'follow_up', 'new_lead', true,
    '{"steps": [{"action": "send_sms", "delay_seconds": 0, "template": "new_lead_acknowledgment"}, {"action": "assign_rep", "delay_seconds": 0}, {"action": "create_task", "delay_seconds": 0, "task_type": "call_lead"}]}'::jsonb,
    156, 152,
    '22222222-2222-2222-2222-222222222222'
);

INSERT INTO automation_workflows (
    id, workflow_name, workflow_type, trigger_type, is_active,
    configuration, execution_count, success_count,
    created_by
) VALUES (
    'aw000001-0001-0001-0001-000000000002',
    'Hot Lead Nurture Sequence',
    'nurture', 'status_change', true,
    '{"trigger_conditions": {"temperature": "hot"}, "steps": [{"action": "send_email", "delay_hours": 24, "template": "hot_lead_day1"}, {"action": "send_sms", "delay_hours": 48, "template": "hot_lead_day2"}, {"action": "create_task", "delay_hours": 72, "task_type": "follow_up_call"}]}'::jsonb,
    45, 43,
    '22222222-2222-2222-2222-222222222222'
);

-- Update team member metrics
UPDATE team_members SET
    total_leads_assigned = 4,
    total_closed_deals = 2,
    total_revenue_generated = 97000.00,
    average_deal_size = 48500.00,
    conversion_rate = 50.00,
    average_response_time = 180
WHERE id = '33333333-3333-3333-3333-333333333333';

UPDATE team_members SET
    total_leads_assigned = 3,
    total_closed_deals = 0,
    total_revenue_generated = 0.00,
    average_deal_size = 0.00,
    conversion_rate = 0.00,
    average_response_time = 240
WHERE id = '44444444-4444-4444-4444-444444444444';
