#!/bin/bash

# Phase 4 Setup Script: AI-Powered Intelligence & Automation
# This script initializes the Phase 4 development environment

set -e  # Exit on error

echo "================================================"
echo "Phase 4 Setup: AI-Powered Intelligence & Automation"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}Project Root: $PROJECT_ROOT${NC}"
echo ""

# Step 1: Create directory structure
echo -e "${YELLOW}Step 1: Creating Phase 4 directory structure...${NC}"

mkdir -p backend/app/ml
mkdir -p backend/app/integrations/ai
mkdir -p backend/app/workflows/automation
mkdir -p backend/app/services/intelligence
mkdir -p backend/app/templates/proposals
mkdir -p backend/tests/ml
mkdir -p backend/tests/integration/phase4
mkdir -p docs/phase4/api
mkdir -p docs/phase4/training
mkdir -p frontend-streamlit/pages/phase4
mkdir -p frontend-streamlit/components/ai

echo -e "${GREEN}✓ Directory structure created${NC}"
echo ""

# Step 2: Install Python dependencies
echo -e "${YELLOW}Step 2: Installing Phase 4 Python dependencies...${NC}"

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install ML/AI dependencies
pip install --upgrade pip wheel setuptools

echo "Installing core ML libraries (using Python 3.13 compatible versions)..."
# Python 3.13 requires scikit-learn 1.5.2+ (latest stable versions for 2025)
pip install scikit-learn==1.7.2
pip install pandas==2.2.3
pip install numpy==2.2.1

# TensorFlow installation (Python 3.13 compatible)
if [[ $(uname -m) == 'arm64' ]]; then
    echo "Installing TensorFlow for Apple Silicon..."
    pip install tensorflow-macos==2.18.0 || echo "Warning: TensorFlow installation failed, continuing..."
else
    echo "Installing TensorFlow for x86_64..."
    pip install tensorflow==2.18.0 || echo "Warning: TensorFlow installation failed, continuing..."
fi

echo "Installing AI/NLP libraries (2025 Python 3.13 compatible versions)..."
pip install openai==1.59.8
pip install anthropic==0.44.0
pip install transformers==4.48.3
pip install sentence-transformers==3.4.0
pip install nltk==3.9.1
# SpaCy: Python 3.13 not yet supported, will be added in future release
echo "Note: SpaCy skipped - Python 3.13 support pending (use spaCy 3.7.x with Python 3.12 if needed)"

echo "Installing integration libraries (latest 2025 compatible versions)..."
pip install 'twilio>=9.4.0'
pip install 'sendgrid>=6.11.0'
pip install 'stripe>=13.0.0,<14.0.0'
pip install 'googlemaps>=4.10.0'

echo "Installing AWS libraries (latest 2025 compatible versions)..."
pip install 'boto3>=1.36.0'
pip install 'sagemaker>=2.230.0'

echo "Installing testing libraries (latest 2025 compatible versions)..."
pip install 'pytest>=8.3.0'
pip install 'pytest-asyncio>=0.25.0'
pip install 'pytest-cov>=6.0.0'
pip install 'locust>=2.30.0'

echo "Installing utilities (latest 2025 compatible versions)..."
pip install 'redis>=5.2.0'
pip install 'celery>=5.4.0'
pip install 'pydantic>=2.10.0'
pip install 'python-dotenv>=1.0.0'

# Update requirements.txt
pip freeze > requirements.txt

echo -e "${GREEN}✓ Python dependencies installed${NC}"
echo ""

cd "$PROJECT_ROOT"

# Step 3: Create environment template
echo -e "${YELLOW}Step 3: Creating Phase 4 environment template...${NC}"

cat > backend/.env.phase4.example << 'EOF'
# Phase 4: AI-Powered Intelligence & Automation Environment Variables

# OpenAI Configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_MAX_TOKENS=4000

# Anthropic Claude Configuration
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-opus-20240229

# Voice AI Configuration (Choose one)
ROBYLON_API_KEY=...
ROBYLON_WEBHOOK_SECRET=...
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...

# Twilio Configuration
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=...
TWILIO_SMS_WEBHOOK_URL=...

# Zillow API
ZILLOW_API_KEY=...
ZILLOW_BASE_URL=https://api.zillow.com/v1

# Weather API
WEATHER_API_KEY=...
WEATHER_BASE_URL=https://api.weather.com/v1

# Google Maps API
GOOGLE_MAPS_API_KEY=...

# AWS SageMaker
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
SAGEMAKER_ROLE_ARN=...
SAGEMAKER_BUCKET=...

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1
REDIS_PASSWORD=

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# ML Model Configuration
ML_MODEL_PATH=./models
ML_CACHE_ENABLED=true
ML_CACHE_TTL=3600

# Feature Flags
FEATURE_NBA_ENGINE=true
FEATURE_CLV_PREDICTION=true
FEATURE_CHURN_PREDICTION=true
FEATURE_VOICE_ASSISTANT=true
FEATURE_CHATBOT=true
FEATURE_EMAIL_PERSONALIZATION=true
FEATURE_AUTO_PROPOSALS=true

# Performance Settings
ML_BATCH_SIZE=32
ML_MAX_WORKERS=4
API_RATE_LIMIT=100
API_TIMEOUT=30000

EOF

echo -e "${GREEN}✓ Environment template created at backend/.env.phase4.example${NC}"
echo ""

# Step 4: Initialize database migrations
echo -e "${YELLOW}Step 4: Creating Phase 4 database migration...${NC}"

cat > backend/migrations/004_phase4_ai_features.sql << 'EOF'
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

EOF

echo -e "${GREEN}✓ Database migration created${NC}"
echo ""

# Step 5: Create initial Python module files
echo -e "${YELLOW}Step 5: Creating initial Python module files...${NC}"

# ML module __init__.py
cat > backend/app/ml/__init__.py << 'EOF'
"""
Phase 4: Machine Learning Module
AI-Powered Intelligence & Automation
"""

from .next_best_action import NextBestActionModel
from .clv_prediction import CLVPredictionModel
from .churn_prediction import ChurnPredictionModel

__all__ = [
    'NextBestActionModel',
    'CLVPredictionModel',
    'ChurnPredictionModel'
]
EOF

# AI integrations __init__.py
cat > backend/app/integrations/ai/__init__.py << 'EOF'
"""
Phase 4: AI Integrations Module
Third-party AI service integrations
"""

__all__ = []
EOF

# Workflows __init__.py
cat > backend/app/workflows/__init__.py << 'EOF'
"""
Phase 4: Workflow Automation Module
Multi-channel orchestration and smart workflows
"""

__all__ = []
EOF

# Services intelligence __init__.py
cat > backend/app/services/intelligence/__init__.py << 'EOF'
"""
Phase 4: Intelligence Services Module
Intelligent routing, scoring, and analysis
"""

__all__ = []
EOF

echo -e "${GREEN}✓ Python module files created${NC}"
echo ""

# Step 6: Create README for Phase 4
cat > docs/phase4/README.md << 'EOF'
# Phase 4: AI-Powered Intelligence & Automation

## Overview
This phase implements advanced AI and machine learning capabilities to transform the iSwitch Roofs CRM into an intelligent, automated sales and customer service platform.

## Key Features

### 4.1 Predictive Lead Scoring & Intelligence
- **Next Best Action (NBA) Engine**: AI recommends optimal actions for each lead
- **Customer Lifetime Value (CLV) Prediction**: Identify high-value customers
- **Churn Prediction**: Proactive retention campaigns
- **Lead Temperature Classification**: Hot/Warm/Cold auto-scoring

### 4.2 Conversational AI & Voice Assistants
- **24/7 AI Voice Assistant**: Never miss a call
- **GPT-4 Chatbot**: Multi-channel (website, Facebook, SMS)
- **Sentiment Analysis**: Real-time communication monitoring
- **Voice-to-CRM Logging**: Automatic call transcription and CRM updates

### 4.3 AI-Powered Sales Automation
- **Hyper-Personalized Emails**: AI-generated custom content
- **Multi-Channel Orchestration**: Email, SMS, phone, social coordination
- **Smart Follow-Up Cadence**: Adaptive engagement timing
- **Auto-Generated Proposals**: 5-minute quote generation

### 4.4 Intelligent Lead Routing & Assignment
- **Skills-Based Routing**: Match leads to best-fit sales reps
- **Load Balancing**: Real-time capacity monitoring
- **VIP Fast-Track**: Ultra-premium lead prioritization
- **Geographic Intelligence**: GPS-based territory optimization

## Success Metrics
- 35% conversion rate improvement
- 40% efficiency gain
- $2.5M+ annual revenue impact
- <2 minute lead response time (100%)

## Documentation
- [Execution Plan](../PHASE_4_EXECUTION_PLAN.md)
- [Agent Assignments](../PHASE_4_AGENT_ASSIGNMENTS.md)
- [API Documentation](./api/)
- [Training Materials](./training/)

## Timeline
**Duration**: 4 weeks (Weeks 8-12)
**Investment**: $72,000
**ROI**: 15x

EOF

echo -e "${GREEN}✓ Phase 4 README created${NC}"
echo ""

# Step 7: Summary
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Phase 4 Setup Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Next Steps:"
echo "1. Copy backend/.env.phase4.example to backend/.env and configure API keys"
echo "2. Run database migration: psql -U postgres -d iswitch_roofs -f backend/migrations/004_phase4_ai_features.sql"
echo "3. Review execution plan: docs/PHASE_4_EXECUTION_PLAN.md"
echo "4. Review agent assignments: docs/PHASE_4_AGENT_ASSIGNMENTS.md"
echo "5. Begin Week 8 development sprints"
echo ""
echo -e "${BLUE}Happy coding! 🚀${NC}"
