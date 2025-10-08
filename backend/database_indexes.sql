-- Database Index Creation Script
-- Generated: 2025-10-06T16:30:10.537016
-- Run this script in your Supabase SQL editor

-- Filtering hot/warm leads by status is very common
CREATE INDEX IF NOT EXISTS idx_leads_status_temperature ON leads (status, temperature);

-- Sorting leads by creation date for dashboards
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads (created_at);

-- Team members frequently filter their assigned leads
CREATE INDEX IF NOT EXISTS idx_leads_assigned_to_status ON leads (assigned_to, status);

-- Lead source reporting and analytics
CREATE INDEX IF NOT EXISTS idx_leads_source ON leads (source);

-- Phone number lookup for call tracking
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers (phone);

-- Email lookup for communications
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers (email);

-- Active project tracking and scheduling
CREATE INDEX IF NOT EXISTS idx_projects_status_start_date ON projects (status, start_date);

-- Foreign key relationship queries
CREATE INDEX IF NOT EXISTS idx_projects_customer_id ON projects (customer_id);

-- Lead interaction timeline queries
CREATE INDEX IF NOT EXISTS idx_interactions_lead_id_created_at ON interactions (lead_id, created_at);

-- Customer interaction history
CREATE INDEX IF NOT EXISTS idx_interactions_customer_id_created_at ON interactions (customer_id, created_at);

-- Upcoming appointments dashboard
CREATE INDEX IF NOT EXISTS idx_appointments_scheduled_time_status ON appointments (scheduled_time, status);

-- Team member schedule queries
CREATE INDEX IF NOT EXISTS idx_appointments_assigned_to ON appointments (assigned_to);

-- Review analytics and trending
CREATE INDEX IF NOT EXISTS idx_reviews_rating_created_at ON reviews (rating, created_at);

-- Active team member queries by role
CREATE INDEX IF NOT EXISTS idx_team_members_role_is_active ON team_members (role, is_active);

-- Unread notification queries
CREATE INDEX IF NOT EXISTS idx_notifications_user_id_read_created_at ON notifications (user_id, read, created_at);
