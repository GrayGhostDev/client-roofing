-- Phase 4: AI-Powered Intelligence & Automation Database Schema

-- ML Model Predictions Table
CREATE TABLE IF NOT EXISTS ml_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    model_type VARCHAR(50) NOT NULL,
    prediction_value JSONB NOT NULL,
    confidence_score FLOAT,
    features_used JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    model_version VARCHAR(20)
);

CREATE INDEX idx_ml_predictions_lead_id ON ml_predictions(lead_id);
CREATE INDEX idx_ml_predictions_model_type ON ml_predictions(model_type);
CREATE INDEX idx_ml_predictions_created_at ON ml_predictions(created_at DESC);

-- Lead Temperature Tracking
CREATE TABLE IF NOT EXISTS lead_temperature (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    temperature VARCHAR(10) CHECK (temperature IN ('hot', 'warm', 'cold')),
    score INTEGER CHECK (score >= 0 AND score <= 100),
    factors JSONB,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lead_temperature_lead_id ON lead_temperature(lead_id);
CREATE INDEX idx_lead_temperature_score ON lead_temperature(score DESC);

-- Voice Assistant Interactions
CREATE TABLE IF NOT EXISTS voice_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    phone_number VARCHAR(20) NOT NULL,
    call_sid VARCHAR(100),
    direction VARCHAR(10) CHECK (direction IN ('inbound', 'outbound')),
    duration_seconds INTEGER,
    transcript TEXT,
    sentiment_score FLOAT,
    intent VARCHAR(100),
    action_taken VARCHAR(100),
    transferred_to_human BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_voice_interactions_lead_id ON voice_interactions(lead_id);
CREATE INDEX idx_voice_interactions_created_at ON voice_interactions(created_at DESC);

-- Chatbot Conversations
CREATE TABLE IF NOT EXISTS chatbot_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    channel VARCHAR(20) CHECK (channel IN ('website', 'facebook', 'sms', 'whatsapp')),
    session_id VARCHAR(100),
    messages JSONB NOT NULL DEFAULT '[]',
    sentiment_score FLOAT,
    intent VARCHAR(100),
    resolution_status VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chatbot_conversations_lead_id ON chatbot_conversations(lead_id);
CREATE INDEX idx_chatbot_conversations_session_id ON chatbot_conversations(session_id);

-- Email Personalization Tracking
CREATE TABLE IF NOT EXISTS email_personalizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    email_campaign_id UUID,
    personalization_data JSONB,
    generated_content TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    replied_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_email_personalizations_lead_id ON email_personalizations(lead_id);
CREATE INDEX idx_email_personalizations_sent_at ON email_personalizations(sent_at DESC);

-- Multi-Channel Orchestration
CREATE TABLE IF NOT EXISTS channel_orchestration (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    workflow_id VARCHAR(100),
    channel VARCHAR(20),
    scheduled_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20),
    engagement_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_channel_orchestration_lead_id ON channel_orchestration(lead_id);
CREATE INDEX idx_channel_orchestration_scheduled_at ON channel_orchestration(scheduled_at);

-- Auto-Generated Proposals
CREATE TABLE IF NOT EXISTS generated_proposals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    property_data JSONB,
    recommended_materials JSONB,
    pricing_breakdown JSONB,
    financing_options JSONB,
    pdf_url TEXT,
    viewed_at TIMESTAMP WITH TIME ZONE,
    accepted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_generated_proposals_lead_id ON generated_proposals(lead_id);
CREATE INDEX idx_generated_proposals_created_at ON generated_proposals(created_at DESC);

-- Lead Routing History
CREATE TABLE IF NOT EXISTS lead_routing_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    routing_reason VARCHAR(100),
    routing_score FLOAT,
    routing_factors JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lead_routing_history_lead_id ON lead_routing_history(lead_id);
CREATE INDEX idx_lead_routing_history_assigned_to ON lead_routing_history(assigned_to);

-- Sentiment Analysis Results
CREATE TABLE IF NOT EXISTS sentiment_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reference_type VARCHAR(20) CHECK (reference_type IN ('email', 'call', 'sms', 'chat')),
    reference_id UUID NOT NULL,
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    sentiment VARCHAR(20) CHECK (sentiment IN ('positive', 'neutral', 'negative')),
    sentiment_score FLOAT,
    emotions JSONB,
    keywords JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sentiment_analysis_lead_id ON sentiment_analysis(lead_id);
CREATE INDEX idx_sentiment_analysis_reference ON sentiment_analysis(reference_type, reference_id);

-- Model Performance Metrics
CREATE TABLE IF NOT EXISTS model_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_type VARCHAR(50) NOT NULL,
    model_version VARCHAR(20),
    metric_name VARCHAR(50),
    metric_value FLOAT,
    evaluation_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_model_performance_model_type ON model_performance(model_type);
CREATE INDEX idx_model_performance_created_at ON model_performance(created_at DESC);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO iswitch_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO iswitch_app;

