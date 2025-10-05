-- Database Migration: Enhanced Appointment Management System
-- File: database_migration_appointments.sql
-- Purpose: Add roofing-specific appointment features and optimization
-- Date: 2025-01-04

-- ===================================
-- 1. ENHANCE EXISTING APPOINTMENTS TABLE
-- ===================================

-- Add roofing-specific columns to existing appointments table
ALTER TABLE appointments
ADD COLUMN weather_dependent BOOLEAN DEFAULT true,
ADD COLUMN weather_check_required BOOLEAN DEFAULT false,
ADD COLUMN backup_date TIMESTAMP WITH TIME ZONE,
ADD COLUMN equipment_required TEXT[],
ADD COLUMN material_samples TEXT[],
ADD COLUMN inspection_scope TEXT,
ADD COLUMN access_requirements TEXT,
ADD COLUMN customer_special_instructions TEXT,
ADD COLUMN preferred_communication VARCHAR(20) DEFAULT 'email',
ADD COLUMN estimated_project_value INTEGER,
ADD COLUMN lead_temperature VARCHAR(10),
ADD COLUMN priority_level INTEGER DEFAULT 3 CHECK (priority_level BETWEEN 1 AND 5),
ADD COLUMN weather_conditions_required JSONB,
ADD COLUMN temperature_range JSONB,
ADD COLUMN wind_speed_limit INTEGER,
ADD COLUMN precipitation_limit DECIMAL(4,2);

-- Update appointment types with roofing-specific values
ALTER TABLE appointments ALTER COLUMN appointment_type TYPE VARCHAR(50);

-- Add check constraint for roofing appointment types
ALTER TABLE appointments
ADD CONSTRAINT chk_roofing_appointment_type
CHECK (appointment_type IN (
    'emergency_inspection',
    'storm_damage_assessment',
    'leak_emergency',
    'initial_consultation',
    'detailed_roof_inspection',
    'drone_inspection',
    'insurance_adjuster_meeting',
    'quote_presentation',
    'contract_signing',
    'project_kickoff',
    'material_delivery',
    'work_start',
    'daily_progress_check',
    'quality_inspection',
    'final_walkthrough',
    'cleanup_inspection',
    'warranty_follow_up',
    'annual_maintenance',
    'customer_satisfaction_survey',
    'insurance_claim_filing',
    'adjuster_coordination',
    'claim_documentation'
));

-- Add indexes for performance
CREATE INDEX idx_appointments_weather_dependent ON appointments(weather_dependent, scheduled_date);
CREATE INDEX idx_appointments_priority_status ON appointments(priority_level, status, scheduled_date);
CREATE INDEX idx_appointments_type_date ON appointments(appointment_type, scheduled_date);

-- ===================================
-- 2. TEAM AVAILABILITY MANAGEMENT
-- ===================================

-- Create team availability slots table
CREATE TABLE team_availability_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_member_id UUID NOT NULL REFERENCES team_members(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    availability_type VARCHAR(20) DEFAULT 'available' CHECK (availability_type IN ('available', 'busy', 'tentative', 'out_of_office')),

    -- Location and travel
    starting_location TEXT,
    travel_radius_miles INTEGER DEFAULT 25,

    -- Capacity management
    max_appointments INTEGER DEFAULT 6,
    current_appointments INTEGER DEFAULT 0,

    -- Break times
    lunch_break_start TIME,
    lunch_break_duration INTEGER DEFAULT 60,
    buffer_between_appointments INTEGER DEFAULT 15,

    -- Equipment and skills
    equipment_available TEXT[],
    certifications TEXT[],
    notes TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(team_member_id, date, start_time)
);

-- Indexes for team availability
CREATE INDEX idx_team_availability_member_date ON team_availability_slots(team_member_id, date);
CREATE INDEX idx_team_availability_type ON team_availability_slots(availability_type, date);

-- ===================================
-- 3. MULTI-TEAM APPOINTMENTS
-- ===================================

-- Create multi-team appointment coordination table
CREATE TABLE multi_team_appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    primary_appointment_id UUID NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    appointment_type VARCHAR(50) NOT NULL,

    -- Team coordination
    lead_team_member UUID NOT NULL REFERENCES team_members(id),
    required_team_members UUID[] NOT NULL,
    optional_team_members UUID[] DEFAULT '{}',
    minimum_team_size INTEGER DEFAULT 1,

    -- Scheduling constraints
    all_members_required BOOLEAN DEFAULT true,
    coordination_window INTEGER DEFAULT 30,

    -- Logistics
    meeting_point TEXT,
    equipment_assignments JSONB,
    role_assignments JSONB,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for multi-team appointments
CREATE INDEX idx_multi_team_primary ON multi_team_appointments(primary_appointment_id);
CREATE INDEX idx_multi_team_lead ON multi_team_appointments(lead_team_member);
CREATE INDEX idx_multi_team_members ON multi_team_appointments USING GIN(required_team_members);

-- ===================================
-- 4. ENHANCED NOTIFICATION TRACKING
-- ===================================

-- Create notification tracking table
CREATE TABLE notification_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id UUID NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('email', 'sms', 'push', 'phone')),
    notification_type VARCHAR(50) NOT NULL,
    delivery_id VARCHAR(100),

    -- Content tracking
    subject TEXT,
    content JSONB,
    template_used VARCHAR(100),

    -- Status tracking
    status VARCHAR(20) DEFAULT 'sent' CHECK (status IN ('sent', 'delivered', 'failed', 'bounced')),
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    delivered_at TIMESTAMP WITH TIME ZONE,

    -- Engagement tracking
    engagement_type VARCHAR(20) CHECK (engagement_type IN ('opened', 'clicked', 'replied', 'confirmed')),
    engaged_at TIMESTAMP WITH TIME ZONE,

    -- Customer response
    customer_response TEXT,
    response_action VARCHAR(50),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for notification tracking
CREATE INDEX idx_notification_appointment ON notification_tracking(appointment_id, sent_at);
CREATE INDEX idx_notification_status ON notification_tracking(status, sent_at);
CREATE INDEX idx_notification_engagement ON notification_tracking(engagement_type, engaged_at);

-- ===================================
-- 5. WEATHER INTEGRATION
-- ===================================

-- Create weather alerts table
CREATE TABLE weather_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id UUID REFERENCES appointments(id) ON DELETE CASCADE,
    location TEXT NOT NULL,
    alert_date DATE NOT NULL,

    -- Weather data
    weather_type VARCHAR(30) NOT NULL CHECK (weather_type IN ('rain', 'snow', 'wind', 'temperature', 'storm')),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'severe')),
    conditions JSONB NOT NULL,

    -- Alert details
    message TEXT NOT NULL,
    action_required VARCHAR(100),
    automatic_reschedule BOOLEAN DEFAULT false,

    -- Status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'ignored')),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_action VARCHAR(100),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for weather alerts
CREATE INDEX idx_weather_alerts_appointment ON weather_alerts(appointment_id, status);
CREATE INDEX idx_weather_alerts_date_severity ON weather_alerts(alert_date, severity);
CREATE INDEX idx_weather_alerts_type ON weather_alerts(weather_type, status);

-- ===================================
-- 6. APPOINTMENT HISTORY AND ANALYTICS
-- ===================================

-- Enhanced appointment history table
CREATE TABLE appointment_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id UUID NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    action_type VARCHAR(30) NOT NULL CHECK (action_type IN ('created', 'updated', 'rescheduled', 'cancelled', 'completed', 'no_show')),

    -- Change tracking
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[],

    -- Context
    reason TEXT,
    initiated_by UUID REFERENCES team_members(id),
    customer_initiated BOOLEAN DEFAULT false,
    automatic_change BOOLEAN DEFAULT false,

    -- Timing
    original_start TIMESTAMP WITH TIME ZONE,
    original_end TIMESTAMP WITH TIME ZONE,
    new_start TIMESTAMP WITH TIME ZONE,
    new_end TIMESTAMP WITH TIME ZONE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for appointment history
CREATE INDEX idx_appointment_history_appointment ON appointment_history(appointment_id, created_at);
CREATE INDEX idx_appointment_history_action ON appointment_history(action_type, created_at);
CREATE INDEX idx_appointment_history_user ON appointment_history(initiated_by, created_at);

-- ===================================
-- 7. CUSTOMER SCHEDULING PREFERENCES
-- ===================================

-- Create customer scheduling preferences table
CREATE TABLE customer_scheduling_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,

    -- Time preferences
    preferred_days TEXT[] DEFAULT '{}', -- ['monday', 'tuesday', 'friday']
    preferred_times VARCHAR(20) DEFAULT 'morning', -- 'morning', 'afternoon', 'evening'
    avoid_times JSONB, -- [{"day": "friday", "start": "17:00", "end": "19:00"}]

    -- Communication preferences
    contact_preference VARCHAR(20) DEFAULT 'email' CHECK (contact_preference IN ('sms', 'email', 'phone')),
    reminder_preference INTEGER DEFAULT 24, -- hours before
    notification_channels TEXT[] DEFAULT '{"email"}',

    -- Scheduling rules
    reschedule_limit INTEGER DEFAULT 2,
    auto_confirm BOOLEAN DEFAULT false,
    buffer_time_minutes INTEGER DEFAULT 15,

    -- Special requirements
    special_instructions TEXT,
    access_notes TEXT, -- Gate codes, parking, pets
    equipment_restrictions TEXT[], -- Allergies to materials, etc.

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(customer_id)
);

-- Indexes for customer preferences
CREATE INDEX idx_customer_preferences_customer ON customer_scheduling_preferences(customer_id);
CREATE INDEX idx_customer_preferences_contact ON customer_scheduling_preferences(contact_preference);

-- ===================================
-- 8. SCHEDULING ANALYTICS VIEWS
-- ===================================

-- Create view for appointment efficiency metrics
CREATE VIEW appointment_efficiency_metrics AS
SELECT
    tm.id as team_member_id,
    tm.first_name || ' ' || tm.last_name as team_member_name,
    tm.role,
    DATE_TRUNC('week', a.scheduled_date) as week_start,
    COUNT(*) as total_appointments,
    COUNT(CASE WHEN a.status = 'completed' THEN 1 END) as completed_appointments,
    COUNT(CASE WHEN a.status = 'cancelled' THEN 1 END) as cancelled_appointments,
    COUNT(CASE WHEN a.status = 'no_show' THEN 1 END) as no_shows,
    ROUND(
        COUNT(CASE WHEN a.status = 'completed' THEN 1 END)::DECIMAL /
        NULLIF(COUNT(*), 0) * 100, 2
    ) as completion_rate,
    AVG(a.duration_minutes) as avg_appointment_duration,
    SUM(a.duration_minutes) as total_scheduled_minutes,
    AVG(a.estimated_project_value) as avg_project_value,
    SUM(a.estimated_project_value) as total_estimated_value
FROM appointments a
JOIN team_members tm ON a.assigned_to = tm.id
WHERE a.scheduled_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY tm.id, tm.first_name, tm.last_name, tm.role, DATE_TRUNC('week', a.scheduled_date);

-- Create view for weather impact analysis
CREATE VIEW weather_impact_analysis AS
SELECT
    DATE_TRUNC('month', a.scheduled_date) as month,
    a.appointment_type,
    COUNT(*) as total_appointments,
    COUNT(CASE WHEN a.weather_dependent = true THEN 1 END) as weather_dependent_count,
    COUNT(CASE WHEN wa.id IS NOT NULL THEN 1 END) as weather_alerts_count,
    COUNT(CASE WHEN a.status = 'cancelled' AND ah.reason ILIKE '%weather%' THEN 1 END) as weather_cancellations,
    ROUND(
        COUNT(CASE WHEN a.status = 'cancelled' AND ah.reason ILIKE '%weather%' THEN 1 END)::DECIMAL /
        NULLIF(COUNT(CASE WHEN a.weather_dependent = true THEN 1 END), 0) * 100, 2
    ) as weather_cancellation_rate
FROM appointments a
LEFT JOIN weather_alerts wa ON a.id = wa.appointment_id
LEFT JOIN appointment_history ah ON a.id = ah.appointment_id AND ah.action_type = 'cancelled'
WHERE a.scheduled_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', a.scheduled_date), a.appointment_type;

-- Create view for customer satisfaction metrics
CREATE VIEW customer_satisfaction_metrics AS
SELECT
    c.id as customer_id,
    c.first_name || ' ' || c.last_name as customer_name,
    c.segment,
    COUNT(a.id) as total_appointments,
    COUNT(CASE WHEN a.status = 'completed' THEN 1 END) as completed_appointments,
    COUNT(CASE WHEN a.status = 'no_show' THEN 1 END) as no_shows,
    COUNT(CASE WHEN ah.action_type = 'rescheduled' THEN 1 END) as reschedules,
    AVG(CASE WHEN nt.engagement_type = 'replied' THEN 1 ELSE 0 END) as response_rate,
    ROUND(
        COUNT(CASE WHEN a.status = 'completed' THEN 1 END)::DECIMAL /
        NULLIF(COUNT(a.id), 0) * 100, 2
    ) as completion_rate
FROM customers c
LEFT JOIN appointments a ON c.id = a.customer_id::uuid
LEFT JOIN appointment_history ah ON a.id = ah.appointment_id
LEFT JOIN notification_tracking nt ON a.id = nt.appointment_id
WHERE a.scheduled_date >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY c.id, c.first_name, c.last_name, c.segment;

-- ===================================
-- 9. PERFORMANCE OPTIMIZATION INDEXES
-- ===================================

-- Composite indexes for common query patterns
CREATE INDEX idx_appointments_team_status_date ON appointments(assigned_to, status, scheduled_date);
CREATE INDEX idx_appointments_customer_type_date ON appointments(customer_id, appointment_type, scheduled_date);
CREATE INDEX idx_appointments_priority_date ON appointments(priority_level DESC, scheduled_date);
CREATE INDEX idx_appointments_weather_date ON appointments(weather_dependent, scheduled_date) WHERE weather_dependent = true;

-- Partial indexes for active appointments
CREATE INDEX idx_appointments_active ON appointments(scheduled_date, assigned_to)
WHERE status IN ('scheduled', 'confirmed');

-- Partial indexes for upcoming appointments
CREATE INDEX idx_appointments_upcoming ON appointments(scheduled_date, customer_id, status)
WHERE scheduled_date > NOW();

-- GIN indexes for array and JSONB columns
CREATE INDEX idx_appointments_equipment_gin ON appointments USING GIN(equipment_required);
CREATE INDEX idx_weather_conditions_gin ON appointments USING GIN(weather_conditions_required);
CREATE INDEX idx_notification_content_gin ON notification_tracking USING GIN(content);

-- ===================================
-- 10. STORED PROCEDURES FOR COMMON OPERATIONS
-- ===================================

-- Function to check appointment availability
CREATE OR REPLACE FUNCTION check_appointment_availability(
    p_team_member_id UUID,
    p_start_time TIMESTAMP WITH TIME ZONE,
    p_duration_minutes INTEGER,
    p_exclude_appointment_id UUID DEFAULT NULL
) RETURNS JSONB AS $$
DECLARE
    conflict_count INTEGER;
    conflict_details JSONB;
    business_hours JSONB;
    result JSONB;
BEGIN
    -- Check for time conflicts
    SELECT COUNT(*),
           JSONB_AGG(
               JSONB_BUILD_OBJECT(
                   'appointment_id', id,
                   'start_time', scheduled_date,
                   'end_time', end_time,
                   'type', appointment_type
               )
           )
    INTO conflict_count, conflict_details
    FROM appointments
    WHERE assigned_to = p_team_member_id
      AND status IN ('scheduled', 'confirmed')
      AND (p_exclude_appointment_id IS NULL OR id != p_exclude_appointment_id)
      AND (
          (scheduled_date <= p_start_time AND end_time > p_start_time) OR
          (scheduled_date < p_start_time + INTERVAL '1 minute' * p_duration_minutes AND end_time >= p_start_time + INTERVAL '1 minute' * p_duration_minutes) OR
          (scheduled_date >= p_start_time AND end_time <= p_start_time + INTERVAL '1 minute' * p_duration_minutes)
      );

    -- Build result
    result := JSONB_BUILD_OBJECT(
        'available', conflict_count = 0,
        'conflicts', COALESCE(conflict_details, '[]'::JSONB),
        'conflict_count', conflict_count
    );

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to get team member availability for a date range
CREATE OR REPLACE FUNCTION get_team_availability(
    p_team_member_id UUID,
    p_start_date DATE,
    p_end_date DATE
) RETURNS TABLE(
    available_date DATE,
    available_slots JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ts.date,
        JSONB_AGG(
            JSONB_BUILD_OBJECT(
                'start_time', ts.start_time,
                'end_time', ts.end_time,
                'availability_type', ts.availability_type,
                'max_appointments', ts.max_appointments,
                'current_appointments', ts.current_appointments,
                'slots_remaining', ts.max_appointments - ts.current_appointments
            )
            ORDER BY ts.start_time
        ) as available_slots
    FROM team_availability_slots ts
    WHERE ts.team_member_id = p_team_member_id
      AND ts.date BETWEEN p_start_date AND p_end_date
      AND ts.availability_type = 'available'
    GROUP BY ts.date
    ORDER BY ts.date;
END;
$$ LANGUAGE plpgsql;

-- Function to update appointment statistics
CREATE OR REPLACE FUNCTION update_appointment_statistics()
RETURNS TRIGGER AS $$
BEGIN
    -- Update team member appointment counts
    IF TG_OP = 'INSERT' OR (TG_OP = 'UPDATE' AND OLD.assigned_to != NEW.assigned_to) THEN
        -- Update new assigned team member
        UPDATE team_members
        SET active_leads_count = (
            SELECT COUNT(*)
            FROM appointments
            WHERE assigned_to = NEW.assigned_to
              AND status IN ('scheduled', 'confirmed')
              AND scheduled_date >= CURRENT_DATE
        )
        WHERE id = NEW.assigned_to;

        -- Update old assigned team member if changed
        IF TG_OP = 'UPDATE' AND OLD.assigned_to != NEW.assigned_to THEN
            UPDATE team_members
            SET active_leads_count = (
                SELECT COUNT(*)
                FROM appointments
                WHERE assigned_to = OLD.assigned_to
                  AND status IN ('scheduled', 'confirmed')
                  AND scheduled_date >= CURRENT_DATE
            )
            WHERE id = OLD.assigned_to;
        END IF;
    END IF;

    -- Update availability slot counts
    IF TG_OP = 'INSERT' OR (TG_OP = 'UPDATE' AND (OLD.scheduled_date != NEW.scheduled_date OR OLD.assigned_to != NEW.assigned_to)) THEN
        UPDATE team_availability_slots
        SET current_appointments = (
            SELECT COUNT(*)
            FROM appointments
            WHERE assigned_to = NEW.assigned_to
              AND DATE(scheduled_date) = team_availability_slots.date
              AND status IN ('scheduled', 'confirmed')
        )
        WHERE team_member_id = NEW.assigned_to
          AND date = DATE(NEW.scheduled_date);
    END IF;

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Create triggers
CREATE TRIGGER trigger_update_appointment_statistics
    AFTER INSERT OR UPDATE OR DELETE ON appointments
    FOR EACH ROW
    EXECUTE FUNCTION update_appointment_statistics();

-- ===================================
-- 11. DATA MIGRATION FOR EXISTING RECORDS
-- ===================================

-- Update existing appointments with default roofing-specific values
UPDATE appointments
SET
    weather_dependent = CASE
        WHEN appointment_type IN ('roof_inspection', 'site_visit', 'progress_check', 'final_walkthrough')
        THEN true
        ELSE false
    END,
    priority_level = CASE
        WHEN appointment_type = 'emergency_inspection' THEN 1
        WHEN appointment_type IN ('initial_consultation', 'quote_presentation') THEN 2
        WHEN appointment_type IN ('roof_inspection', 'site_visit') THEN 3
        ELSE 4
    END,
    preferred_communication = 'email';

-- Create default availability slots for existing team members
INSERT INTO team_availability_slots (team_member_id, date, start_time, end_time, max_appointments)
SELECT
    tm.id,
    generate_series(CURRENT_DATE, CURRENT_DATE + INTERVAL '30 days', '1 day')::DATE,
    '08:00:00'::TIME,
    '17:00:00'::TIME,
    6
FROM team_members tm
WHERE tm.status = 'active'
ON CONFLICT (team_member_id, date, start_time) DO NOTHING;

-- Create default scheduling preferences for existing customers
INSERT INTO customer_scheduling_preferences (customer_id, preferred_days, preferred_times, contact_preference)
SELECT
    id,
    ARRAY['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
    'morning',
    'email'
FROM customers
WHERE status = 'active'
ON CONFLICT (customer_id) DO NOTHING;

-- ===================================
-- 12. SECURITY AND PERMISSIONS
-- ===================================

-- Create RLS policies for appointment access
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;

-- Policy: Team members can only see their own appointments or if they have manager role
CREATE POLICY appointment_access_policy ON appointments
    FOR ALL
    TO authenticated
    USING (
        assigned_to = auth.uid() OR
        EXISTS (
            SELECT 1 FROM team_members
            WHERE id = auth.uid()
              AND role IN ('manager', 'admin', 'owner')
        )
    );

-- Policy: Customers can only see their own appointments
CREATE POLICY customer_appointment_policy ON appointments
    FOR SELECT
    TO authenticated
    USING (
        customer_id::text = auth.uid()::text
    );

-- Grant appropriate permissions
GRANT SELECT, INSERT, UPDATE ON appointments TO authenticated;
GRANT SELECT, INSERT, UPDATE ON team_availability_slots TO authenticated;
GRANT SELECT, INSERT, UPDATE ON multi_team_appointments TO authenticated;
GRANT SELECT, INSERT ON notification_tracking TO authenticated;
GRANT SELECT, INSERT, UPDATE ON weather_alerts TO authenticated;
GRANT SELECT, INSERT ON appointment_history TO authenticated;
GRANT SELECT, UPDATE ON customer_scheduling_preferences TO authenticated;

-- ===================================
-- 13. PERFORMANCE MONITORING
-- ===================================

-- Create performance monitoring table
CREATE TABLE appointment_performance_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operation VARCHAR(50) NOT NULL,
    execution_time_ms INTEGER NOT NULL,
    query_type VARCHAR(30) NOT NULL,
    parameters JSONB,
    team_member_id UUID,
    appointment_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for performance monitoring
CREATE INDEX idx_performance_log_operation ON appointment_performance_log(operation, created_at);

-- ===================================
-- 14. VALIDATION AND CONSTRAINTS
-- ===================================

-- Add constraints to ensure data integrity
ALTER TABLE appointments
ADD CONSTRAINT chk_end_time_after_start
CHECK (end_time > scheduled_date);

ALTER TABLE appointments
ADD CONSTRAINT chk_duration_positive
CHECK (duration_minutes > 0);

ALTER TABLE appointments
ADD CONSTRAINT chk_priority_valid
CHECK (priority_level BETWEEN 1 AND 5);

ALTER TABLE team_availability_slots
ADD CONSTRAINT chk_end_time_after_start_time
CHECK (end_time > start_time);

ALTER TABLE team_availability_slots
ADD CONSTRAINT chk_max_appointments_positive
CHECK (max_appointments > 0);

ALTER TABLE customer_scheduling_preferences
ADD CONSTRAINT chk_reminder_hours_positive
CHECK (reminder_preference > 0);

-- ===================================
-- MIGRATION COMPLETION LOG
-- ===================================

-- Log successful migration
INSERT INTO appointment_performance_log (operation, execution_time_ms, query_type, parameters)
VALUES ('migration_completed', 0, 'DDL', '{"version": "1.0", "tables_created": 8, "indexes_created": 25}');

-- Create migration tracking
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    description TEXT
);

INSERT INTO schema_migrations (version, description)
VALUES ('20250104_appointment_enhancements', 'Enhanced appointment management system with roofing-specific features');

COMMIT;