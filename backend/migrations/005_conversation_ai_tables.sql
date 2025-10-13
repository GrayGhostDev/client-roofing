-- Migration 005: Conversation AI Tables
-- Created: 2025-10-11
-- Purpose: Add voice interactions, chatbot conversations, and AI analytics tables

-- ============================================================================
-- VOICE INTERACTIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS voice_interactions (
    -- Primary Key
    id SERIAL PRIMARY KEY,

    -- External IDs
    bland_call_id VARCHAR(255) UNIQUE,
    lead_id VARCHAR(36) REFERENCES leads(id) ON DELETE SET NULL,
    customer_id VARCHAR(36) REFERENCES customers(id) ON DELETE SET NULL,

    -- Call Details
    phone_number VARCHAR(20) NOT NULL,
    caller_name VARCHAR(255),
    call_duration_seconds INTEGER NOT NULL DEFAULT 0,
    call_started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    call_ended_at TIMESTAMP,

    -- Intent and Classification
    intent VARCHAR(50) NOT NULL,
    intent_confidence FLOAT NOT NULL DEFAULT 0.0,
    outcome VARCHAR(50),

    -- Conversation Content
    transcript TEXT,
    summary TEXT,
    key_phrases JSONB,

    -- Sentiment Analysis
    sentiment VARCHAR(20),
    sentiment_score FLOAT,
    sentiment_confidence FLOAT,
    emotions JSONB,

    -- Lead Qualification
    urgency_level VARCHAR(20),
    urgency_score FLOAT,
    qualification_score FLOAT,
    buying_signals JSONB,
    pain_points JSONB,

    -- Data Collection
    collected_data JSONB,
    address_collected VARCHAR(500),
    roof_age_years INTEGER,
    project_budget FLOAT,
    timeline_preference VARCHAR(100),
    insurance_claim BOOLEAN DEFAULT FALSE,

    -- Appointment Scheduling
    appointment_scheduled BOOLEAN NOT NULL DEFAULT FALSE,
    appointment_date TIMESTAMP,
    appointment_type VARCHAR(100),

    -- Escalation
    escalated_to_human BOOLEAN NOT NULL DEFAULT FALSE,
    escalation_reason VARCHAR(50),
    escalation_timestamp TIMESTAMP,
    assigned_agent_id VARCHAR(36) REFERENCES team_members(id) ON DELETE SET NULL,

    -- Quality Metrics
    quality_score FLOAT,
    quality_dimensions JSONB,
    ai_performance_rating FLOAT,

    -- Follow-up
    follow_up_required BOOLEAN NOT NULL DEFAULT FALSE,
    follow_up_notes TEXT,
    follow_up_completed BOOLEAN NOT NULL DEFAULT FALSE,
    follow_up_completed_at TIMESTAMP,

    -- Recording and Metadata
    recording_url VARCHAR(500),
    call_metadata JSONB,
    gpt5_model_version VARCHAR(50),

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,

    -- Constraints
    CONSTRAINT check_call_duration_positive CHECK (call_duration_seconds >= 0),
    CONSTRAINT check_voice_sentiment_score_range CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0),
    CONSTRAINT check_voice_urgency_score_range CHECK (urgency_score >= 0.0 AND urgency_score <= 10.0),
    CONSTRAINT check_voice_qualification_score_range CHECK (qualification_score >= 0.0 AND qualification_score <= 100.0)
);

-- Voice Interactions Indexes
CREATE INDEX idx_voice_bland_call_id ON voice_interactions(bland_call_id);
CREATE INDEX idx_voice_lead_id ON voice_interactions(lead_id);
CREATE INDEX idx_voice_customer_id ON voice_interactions(customer_id);
CREATE INDEX idx_voice_phone_number ON voice_interactions(phone_number);
CREATE INDEX idx_voice_intent ON voice_interactions(intent);
CREATE INDEX idx_voice_outcome ON voice_interactions(outcome);
CREATE INDEX idx_voice_sentiment ON voice_interactions(sentiment);
CREATE INDEX idx_voice_urgency_level ON voice_interactions(urgency_level);
CREATE INDEX idx_voice_escalated ON voice_interactions(escalated_to_human);
CREATE INDEX idx_voice_call_started ON voice_interactions(call_started_at);
CREATE INDEX idx_voice_created_at ON voice_interactions(created_at);
CREATE INDEX idx_voice_phone_created ON voice_interactions(phone_number, created_at);
CREATE INDEX idx_voice_intent_outcome ON voice_interactions(intent, outcome);
CREATE INDEX idx_voice_escalated_timestamp ON voice_interactions(escalated_to_human, escalation_timestamp);

-- Voice Interactions Comments
COMMENT ON TABLE voice_interactions IS 'Stores all voice call interactions with AI assistant';
COMMENT ON COLUMN voice_interactions.bland_call_id IS 'External ID from Bland.ai voice platform';
COMMENT ON COLUMN voice_interactions.intent IS 'Detected call intent: quote_request, appointment_schedule, etc.';
COMMENT ON COLUMN voice_interactions.sentiment_score IS 'Sentiment score from -1.0 (very negative) to 1.0 (very positive)';
COMMENT ON COLUMN voice_interactions.urgency_score IS 'Urgency score from 0.0 (low) to 10.0 (critical)';
COMMENT ON COLUMN voice_interactions.qualification_score IS 'Lead qualification score from 0.0 to 100.0';

-- ============================================================================
-- CHAT CONVERSATIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS chat_conversations (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(255) UNIQUE NOT NULL,

    -- External IDs
    lead_id VARCHAR(36) REFERENCES leads(id) ON DELETE SET NULL,
    customer_id VARCHAR(36) REFERENCES customers(id) ON DELETE SET NULL,

    -- User Information
    user_id VARCHAR(255),
    user_name VARCHAR(255),
    user_email VARCHAR(255),
    user_phone VARCHAR(20),

    -- Channel and Platform
    channel VARCHAR(50) NOT NULL,
    platform_metadata JSONB,

    -- Conversation State
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolution_notes TEXT,

    -- Intent and Classification
    primary_intent VARCHAR(50),
    intent_confidence FLOAT,
    detected_intents JSONB,

    -- Sentiment Tracking
    current_sentiment VARCHAR(20),
    sentiment_score FLOAT,
    sentiment_trend VARCHAR(20),

    -- Lead Qualification
    qualification_score FLOAT,
    urgency_score FLOAT,
    buying_signals JSONB,

    -- Collected Data
    collected_data JSONB,
    address VARCHAR(500),
    roof_age INTEGER,
    project_type VARCHAR(100),

    -- Escalation
    escalated BOOLEAN NOT NULL DEFAULT FALSE,
    escalation_reason VARCHAR(50),
    escalated_at TIMESTAMP,
    assigned_agent_id VARCHAR(36) REFERENCES team_members(id) ON DELETE SET NULL,

    -- Conversation Metrics
    total_messages INTEGER NOT NULL DEFAULT 0,
    user_messages INTEGER NOT NULL DEFAULT 0,
    bot_messages INTEGER NOT NULL DEFAULT 0,
    total_duration_seconds INTEGER,
    average_response_time_seconds FLOAT,

    -- Quality Metrics
    quality_score FLOAT,
    customer_satisfaction_score INTEGER,
    nps_score INTEGER,

    -- Photo Analysis
    photos_uploaded INTEGER NOT NULL DEFAULT 0,
    photo_analysis_results JSONB,

    -- Conversion Tracking
    converted_to_lead BOOLEAN NOT NULL DEFAULT FALSE,
    converted_to_appointment BOOLEAN NOT NULL DEFAULT FALSE,
    conversion_value FLOAT,

    -- Session Management
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    session_duration_seconds INTEGER,

    -- AI Configuration
    gpt5_model_version VARCHAR(50),
    ai_configuration JSONB,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,

    -- Constraints
    CONSTRAINT check_chat_sentiment_range CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0),
    CONSTRAINT check_chat_qualification_range CHECK (qualification_score >= 0.0 AND qualification_score <= 100.0),
    CONSTRAINT check_chat_urgency_range CHECK (urgency_score >= 0.0 AND urgency_score <= 10.0)
);

-- Chat Conversations Indexes
CREATE INDEX idx_chat_conversation_id ON chat_conversations(conversation_id);
CREATE INDEX idx_chat_lead_id ON chat_conversations(lead_id);
CREATE INDEX idx_chat_customer_id ON chat_conversations(customer_id);
CREATE INDEX idx_chat_user_id ON chat_conversations(user_id);
CREATE INDEX idx_chat_channel ON chat_conversations(channel);
CREATE INDEX idx_chat_is_active ON chat_conversations(is_active);
CREATE INDEX idx_chat_is_resolved ON chat_conversations(is_resolved);
CREATE INDEX idx_chat_primary_intent ON chat_conversations(primary_intent);
CREATE INDEX idx_chat_current_sentiment ON chat_conversations(current_sentiment);
CREATE INDEX idx_chat_escalated ON chat_conversations(escalated);
CREATE INDEX idx_chat_started_at ON chat_conversations(started_at);
CREATE INDEX idx_chat_last_activity_at ON chat_conversations(last_activity_at);
CREATE INDEX idx_chat_created_at ON chat_conversations(created_at);
CREATE INDEX idx_chat_channel_active ON chat_conversations(channel, is_active);
CREATE INDEX idx_chat_started_channel ON chat_conversations(started_at, channel);
CREATE INDEX idx_chat_escalated_at ON chat_conversations(escalated, escalated_at);

-- Chat Conversations Comments
COMMENT ON TABLE chat_conversations IS 'Stores chatbot conversations across multiple channels';
COMMENT ON COLUMN chat_conversations.channel IS 'Channel type: website_chat, facebook_messenger, sms, email';
COMMENT ON COLUMN chat_conversations.sentiment_trend IS 'Sentiment trend: improving, declining, stable';
COMMENT ON COLUMN chat_conversations.customer_satisfaction_score IS 'CSAT score: 1-5';
COMMENT ON COLUMN chat_conversations.nps_score IS 'Net Promoter Score: -100 to 100';

-- ============================================================================
-- CONVERSATION MESSAGES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS conversation_messages (
    -- Primary Key
    id SERIAL PRIMARY KEY,

    -- Foreign Keys
    conversation_id INTEGER NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,

    -- Message Content
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(50) NOT NULL DEFAULT 'text',

    -- Message Metadata
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sequence_number INTEGER NOT NULL,

    -- AI-Specific Fields
    model_used VARCHAR(50),
    reasoning_effort VARCHAR(20),
    verbosity VARCHAR(20),
    tokens_used INTEGER,
    processing_time_ms INTEGER,

    -- Tool Calls
    tool_calls JSONB,
    tool_call_results JSONB,

    -- Sentiment (for user messages)
    sentiment VARCHAR(20),
    sentiment_score FLOAT,
    emotions JSONB,

    -- Intent (for user messages)
    detected_intent VARCHAR(100),
    intent_confidence FLOAT,

    -- Image/File Attachments
    has_attachments BOOLEAN NOT NULL DEFAULT FALSE,
    attachment_urls JSONB,
    attachment_metadata JSONB,

    -- Buying Signals
    contains_buying_signal BOOLEAN NOT NULL DEFAULT FALSE,
    buying_signals JSONB,

    -- Quality Indicators
    message_quality_score FLOAT,
    is_coherent BOOLEAN,
    is_relevant BOOLEAN,

    -- Metadata
    metadata JSONB,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT check_msg_sentiment_range CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0)
);

-- Conversation Messages Indexes
CREATE INDEX idx_msg_conversation_id ON conversation_messages(conversation_id);
CREATE INDEX idx_msg_role ON conversation_messages(role);
CREATE INDEX idx_msg_timestamp ON conversation_messages(timestamp);
CREATE INDEX idx_msg_conversation_timestamp ON conversation_messages(conversation_id, timestamp);
CREATE INDEX idx_msg_conversation_sequence ON conversation_messages(conversation_id, sequence_number);
CREATE INDEX idx_msg_role_timestamp ON conversation_messages(role, timestamp);

-- Conversation Messages Comments
COMMENT ON TABLE conversation_messages IS 'Individual messages in chatbot conversations';
COMMENT ON COLUMN conversation_messages.role IS 'Message role: user, assistant, system, tool';
COMMENT ON COLUMN conversation_messages.content_type IS 'Content type: text, image, file, etc.';
COMMENT ON COLUMN conversation_messages.tool_calls IS 'GPT-5 tool calls made by assistant';

-- ============================================================================
-- SENTIMENT ANALYSES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS sentiment_analyses (
    -- Primary Key
    id SERIAL PRIMARY KEY,

    -- Foreign Keys (one of these will be set)
    voice_interaction_id INTEGER REFERENCES voice_interactions(id) ON DELETE CASCADE,
    chat_conversation_id INTEGER REFERENCES chat_conversations(id) ON DELETE CASCADE,
    message_id INTEGER REFERENCES conversation_messages(id) ON DELETE CASCADE,

    -- Analysis Type
    analysis_type VARCHAR(50) NOT NULL,
    analysis_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Sentiment Results
    sentiment_level VARCHAR(20) NOT NULL,
    sentiment_score FLOAT NOT NULL,
    confidence_score FLOAT NOT NULL,

    -- Emotional Analysis
    primary_emotion VARCHAR(50),
    emotions JSONB NOT NULL,
    emotional_intensity FLOAT,

    -- Urgency Analysis
    urgency_level VARCHAR(20) NOT NULL,
    urgency_score FLOAT NOT NULL,
    urgency_indicators JSONB,

    -- Intent and Signals
    buying_signals JSONB,
    buying_signal_strength FLOAT,
    pain_points JSONB,
    concerns JSONB,

    -- Sentiment Trends
    sentiment_trend VARCHAR(20),
    sentiment_volatility FLOAT,
    trend_data JSONB,

    -- Alert Triggers
    alert_triggered BOOLEAN NOT NULL DEFAULT FALSE,
    alert_reason VARCHAR(100),
    alert_severity VARCHAR(20),

    -- Customer Satisfaction Indicators
    satisfaction_indicators JSONB,
    dissatisfaction_indicators JSONB,

    -- AI Model Info
    model_used VARCHAR(50) NOT NULL,
    model_version VARCHAR(50),
    processing_time_ms INTEGER,

    -- Additional Context
    analyzed_text_length INTEGER,
    context_metadata JSONB,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT check_sentiment_analysis_score_range CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0),
    CONSTRAINT check_sentiment_urgency_range CHECK (urgency_score >= 0.0 AND urgency_score <= 10.0)
);

-- Sentiment Analyses Indexes
CREATE INDEX idx_sentiment_voice_id ON sentiment_analyses(voice_interaction_id);
CREATE INDEX idx_sentiment_chat_id ON sentiment_analyses(chat_conversation_id);
CREATE INDEX idx_sentiment_message_id ON sentiment_analyses(message_id);
CREATE INDEX idx_sentiment_level ON sentiment_analyses(sentiment_level);
CREATE INDEX idx_sentiment_urgency_level ON sentiment_analyses(urgency_level);
CREATE INDEX idx_sentiment_analysis_timestamp ON sentiment_analyses(analysis_timestamp);
CREATE INDEX idx_sentiment_alert_triggered ON sentiment_analyses(alert_triggered);
CREATE INDEX idx_sentiment_voice_timestamp ON sentiment_analyses(voice_interaction_id, analysis_timestamp);
CREATE INDEX idx_sentiment_chat_timestamp ON sentiment_analyses(chat_conversation_id, analysis_timestamp);
CREATE INDEX idx_sentiment_level_timestamp ON sentiment_analyses(sentiment_level, analysis_timestamp);
CREATE INDEX idx_sentiment_alert ON sentiment_analyses(alert_triggered, alert_severity);

-- Sentiment Analyses Comments
COMMENT ON TABLE sentiment_analyses IS 'Detailed sentiment analysis results for conversations';
COMMENT ON COLUMN sentiment_analyses.analysis_type IS 'Analysis type: message, conversation, thread';
COMMENT ON COLUMN sentiment_analyses.sentiment_level IS 'Sentiment level: very_negative, negative, neutral, positive, very_positive';
COMMENT ON COLUMN sentiment_analyses.urgency_level IS 'Urgency level: low, medium, high, critical';

-- ============================================================================
-- CONVERSATION QUALITY TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS conversation_quality (
    -- Primary Key
    id SERIAL PRIMARY KEY,

    -- Foreign Keys (one of these will be set)
    voice_interaction_id INTEGER REFERENCES voice_interactions(id) ON DELETE CASCADE,
    chat_conversation_id INTEGER REFERENCES chat_conversations(id) ON DELETE CASCADE,

    -- Analysis Metadata
    analysis_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    analyzed_by VARCHAR(50) NOT NULL,

    -- Overall Quality
    overall_score FLOAT NOT NULL,
    quality_grade VARCHAR(2) NOT NULL,

    -- Quality Dimensions
    professionalism_score FLOAT NOT NULL,
    professionalism_notes TEXT,

    responsiveness_score FLOAT NOT NULL,
    responsiveness_notes TEXT,

    clarity_score FLOAT NOT NULL,
    clarity_notes TEXT,

    helpfulness_score FLOAT NOT NULL,
    helpfulness_notes TEXT,

    resolution_score FLOAT NOT NULL,
    resolution_notes TEXT,

    -- Additional Quality Metrics
    accuracy_score FLOAT,
    empathy_score FLOAT,
    efficiency_score FLOAT,

    -- Strengths and Weaknesses
    strengths JSONB,
    weaknesses JSONB,
    improvement_opportunities JSONB,

    -- Compliance
    followed_best_practices BOOLEAN,
    compliance_issues JSONB,

    -- Customer Experience
    customer_effort_score FLOAT,
    customer_satisfaction_score INTEGER,
    net_promoter_score INTEGER,

    -- AI Performance
    ai_accuracy FLOAT,
    ai_relevance FLOAT,
    ai_coherence FLOAT,
    ai_mistakes JSONB,

    -- Conversation Metrics
    total_turns INTEGER,
    average_response_time FLOAT,
    conversation_duration_seconds INTEGER,

    -- Issue Detection
    issues_detected BOOLEAN NOT NULL DEFAULT FALSE,
    issue_types JSONB,
    issue_severity VARCHAR(20),

    -- Training Recommendations
    training_needed BOOLEAN NOT NULL DEFAULT FALSE,
    training_topics JSONB,

    -- Detailed Analysis
    full_analysis JSONB,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT check_quality_overall_score CHECK (overall_score >= 0.0 AND overall_score <= 100.0),
    CONSTRAINT check_quality_professionalism CHECK (professionalism_score >= 0.0 AND professionalism_score <= 100.0)
);

-- Conversation Quality Indexes
CREATE INDEX idx_quality_voice_id ON conversation_quality(voice_interaction_id);
CREATE INDEX idx_quality_chat_id ON conversation_quality(chat_conversation_id);
CREATE INDEX idx_quality_overall_score ON conversation_quality(overall_score);
CREATE INDEX idx_quality_grade ON conversation_quality(quality_grade);
CREATE INDEX idx_quality_analysis_timestamp ON conversation_quality(analysis_timestamp);
CREATE INDEX idx_quality_voice_timestamp ON conversation_quality(voice_interaction_id, analysis_timestamp);
CREATE INDEX idx_quality_chat_timestamp ON conversation_quality(chat_conversation_id, analysis_timestamp);

-- Conversation Quality Comments
COMMENT ON TABLE conversation_quality IS 'Conversation quality analysis and scoring';
COMMENT ON COLUMN conversation_quality.overall_score IS 'Overall quality score: 0.0 to 100.0';
COMMENT ON COLUMN conversation_quality.quality_grade IS 'Quality grade: A+, A, B+, B, C+, C, D, F';
COMMENT ON COLUMN conversation_quality.customer_effort_score IS 'Customer Effort Score (CES): 1.0 to 7.0';

-- ============================================================================
-- UPDATE TRIGGERS FOR UPDATED_AT
-- ============================================================================

-- Voice Interactions trigger
CREATE OR REPLACE FUNCTION update_voice_interactions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_voice_interactions_updated_at
    BEFORE UPDATE ON voice_interactions
    FOR EACH ROW
    EXECUTE FUNCTION update_voice_interactions_updated_at();

-- Chat Conversations trigger
CREATE OR REPLACE FUNCTION update_chat_conversations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_chat_conversations_updated_at
    BEFORE UPDATE ON chat_conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_chat_conversations_updated_at();

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON voice_interactions TO iswitch_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON chat_conversations TO iswitch_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON conversation_messages TO iswitch_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON sentiment_analyses TO iswitch_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON conversation_quality TO iswitch_user;

GRANT USAGE, SELECT ON SEQUENCE voice_interactions_id_seq TO iswitch_user;
GRANT USAGE, SELECT ON SEQUENCE chat_conversations_id_seq TO iswitch_user;
GRANT USAGE, SELECT ON SEQUENCE conversation_messages_id_seq TO iswitch_user;
GRANT USAGE, SELECT ON SEQUENCE sentiment_analyses_id_seq TO iswitch_user;
GRANT USAGE, SELECT ON SEQUENCE conversation_quality_id_seq TO iswitch_user;

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

SELECT 'Migration 005: Conversation AI Tables - COMPLETED' as status;
