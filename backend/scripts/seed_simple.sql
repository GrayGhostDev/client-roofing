-- Simple SQL Seed Script for iSwitch Roofs CRM
-- Populates database with 100 realistic leads for testing

-- Clear existing data
DELETE FROM leads;

-- Insert 100 sample leads with realistic data
INSERT INTO leads (
    id, first_name, last_name, phone, email,
    source, status, temperature, lead_score,
    street_address, city, state, zip_code,
    property_value, roof_age, roof_type,
    is_deleted, interaction_count,
    notes, created_at, updated_at
) VALUES
-- Hot leads from premium sources
(gen_random_uuid(), 'James', 'Smith', '248-555-1001', 'james.smith@gmail.com', 'google_lsa'::leadsourceenum, 'new'::leadstatusenum, 'hot'::leadtemperatureenum, 92, '1000 Main St', 'Bloomfield Hills', 'MI', '48301', 55000, 12, 'asphalt_shingle', FALSE, 0, 'Premium lead from Google LSA', NOW() - INTERVAL '2 days', NOW()),
(gen_random_uuid(), 'Mary', 'Johnson', '248-555-1002', 'mary.johnson@yahoo.com', 'referral'::leadsourceenum, 'contacted'::leadstatusenum, 'hot'::leadtemperatureenum, 95, '2100 Oak Ave', 'Birmingham', 'MI', '48009', 52000, 10, 'architectural_shingle', FALSE, 2, 'Referral from satisfied customer', NOW() - INTERVAL '1 day', NOW()),
(gen_random_uuid(), 'John', 'Williams', '248-555-1003', 'john.williams@outlook.com', 'partner_referral'::leadsourceenum, 'qualified'::leadstatusenum, 'hot'::leadtemperatureenum, 88, '3200 Pine Dr', 'Grosse Pointe', 'MI', '48236', 48000, 15, 'metal', FALSE, 3, 'Insurance agent referral', NOW() - INTERVAL '3 days', NOW()),

-- Warm leads from various sources
(gen_random_uuid(), 'Patricia', 'Brown', '248-555-1004', 'patricia.brown@gmail.com', 'google_ads'::leadsourceenum, 'new'::leadstatusenum, 'warm'::leadtemperatureenum, 72, '4300 Cedar Ln', 'Troy', 'MI', '48084', 28000, 18, 'asphalt_shingle', FALSE, 0, 'Google Ads campaign', NOW() - INTERVAL '1 day', NOW()),
(gen_random_uuid(), 'Robert', 'Jones', '248-555-1005', 'robert.jones@icloud.com', 'facebook_ads'::leadsourceenum, 'contacted'::leadstatusenum, 'warm'::leadtemperatureenum, 68, '5400 Maple Ct', 'Rochester Hills', 'MI', '48309', 26000, 22, 'architectural_shingle', FALSE, 1, 'Facebook lead ad', NOW() - INTERVAL '2 days', NOW()),

-- Cool leads
(gen_random_uuid(), 'Jennifer', 'Garcia', '248-555-1006', 'jennifer.garcia@gmail.com', 'website_form'::leadsourceenum, 'new'::leadstatusenum, 'cool'::leadtemperatureenum, 55, '6500 Elm St', 'West Bloomfield', 'MI', '48322', 27000, 25, 'asphalt_shingle', FALSE, 0, 'Website contact form', NOW() - INTERVAL '5 days', NOW()),
(gen_random_uuid(), 'Michael', 'Miller', '248-555-1007', 'michael.miller@yahoo.com', 'door_to_door'::leadsourceenum, 'contacted'::leadstatusenum, 'cool'::leadtemperatureenum, 52, '7600 Birch Ave', 'Troy', 'MI', '48084', 24000, 28, 'asphalt_shingle', FALSE, 1, 'Door to door campaign', NOW() - INTERVAL '7 days', NOW()),

-- Cold leads
(gen_random_uuid(), 'Linda', 'Davis', '248-555-1008', 'linda.davis@outlook.com', 'organic_search'::leadsourceenum, 'new'::leadstatusenum, 'cold'::leadtemperatureenum, 38, '8700 Spruce Dr', 'Birmingham', 'MI', '48009', 23000, 32, 'asphalt_shingle', FALSE, 0, 'Organic search visit', NOW() - INTERVAL '10 days', NOW()),
(gen_random_uuid(), 'William', 'Rodriguez', '248-555-1009', 'william.rodriguez@gmail.com', 'email_inquiry'::leadsourceenum, 'contacted'::leadstatusenum, 'cold'::leadtemperatureenum, 35, '9800 Willow Ln', 'Bloomfield Hills', 'MI', '48301', 30000, 30, 'architectural_shingle', FALSE, 1, 'Email inquiry', NOW() - INTERVAL '15 days', NOW());

-- Generate 91 more leads with varying attributes
DO $$
DECLARE
    i INTEGER;
    first_names TEXT[] := ARRAY['David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica', 'Thomas', 'Sarah', 'Charles', 'Karen'];
    last_names TEXT[] := ARRAY['Martinez', 'Hernandez', 'Lopez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin'];
    sources TEXT[] := ARRAY['google_lsa', 'google_ads', 'facebook_ads', 'referral', 'partner_referral', 'website_form', 'door_to_door'];
    statuses TEXT[] := ARRAY['new', 'contacted', 'qualified', 'quote_sent', 'negotiation'];
    temps TEXT[] := ARRAY['hot', 'warm', 'cool', 'cold'];
    cities TEXT[] := ARRAY['Bloomfield Hills', 'Birmingham', 'Grosse Pointe', 'Troy', 'Rochester Hills', 'West Bloomfield'];
    zips TEXT[] := ARRAY['48301', '48009', '48236', '48084', '48309', '48322'];
    roof_types TEXT[] := ARRAY['asphalt_shingle', 'architectural_shingle', 'metal', 'tile'];
BEGIN
    FOR i IN 10..100 LOOP
        INSERT INTO leads (
            id, first_name, last_name, phone, email,
            source, status, temperature, lead_score,
            street_address, city, state, zip_code,
            property_value, roof_age, roof_type,
            is_deleted, interaction_count,
            notes, created_at, updated_at
        ) VALUES (
            gen_random_uuid(),
            first_names[1 + (i % 10)],
            last_names[1 + ((i / 10) % 10)],
            '248-555-' || LPAD(i::TEXT, 4, '0'),
            LOWER(first_names[1 + (i % 10)] || '.' || last_names[1 + ((i / 10) % 10)] || i || '@gmail.com'),
            (sources[1 + (i % 7)])::leadsourceenum,
            (statuses[1 + (i % 5)])::leadstatusenum,
            (temps[1 + (i % 4)])::leadtemperatureenum,
            45 + (i % 50),
            (1000 + i * 100) || ' Street ' || i,
            cities[1 + (i % 6)],
            'MI',
            zips[1 + (i % 6)],
            20000 + (i * 300),
            10 + (i % 25),
            roof_types[1 + (i % 4)],
            FALSE,
            (i % 5),
            'Auto-generated test lead #' || i,
            NOW() - INTERVAL '1 day' * (i % 90),
            NOW() - INTERVAL '1 day' * (i % 90)
        );
    END LOOP;
END $$;

-- Verify insert
SELECT
    COUNT(*) as total_leads,
    COUNT(CASE WHEN temperature = 'hot' THEN 1 END) as hot_leads,
    COUNT(CASE WHEN temperature = 'warm' THEN 1 END) as warm_leads,
    COUNT(CASE WHEN temperature = 'cool' THEN 1 END) as cool_leads,
    COUNT(CASE WHEN temperature = 'cold' THEN 1 END) as cold_leads
FROM leads;

SELECT '✅ Database seeded with 100 leads successfully!' as status;
