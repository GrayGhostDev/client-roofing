#!/bin/bash

# Set Render Environment Variables via API
# Uses Render API directly to configure environment variables

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Setting Render Environment Variables${NC}"
echo "========================================"
echo ""

# Configuration
RENDER_API_KEY="rnd_Y1ixjTCoQoyWU3j4DOT3VaJbsPlX"
SERVICE_ID="srv-d3mlmmur433s73abuar0"
API_BASE="https://api.render.com/v1"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    exit 1
fi

echo -e "${YELLOW}⚠️  IMPORTANT: Your .env file has LOCAL development URLs${NC}"
echo "For production deployment, you need CLOUD Supabase URLs:"
echo ""
echo "1. SUPABASE_URL should be: https://[PROJECT-ID].supabase.co"
echo "2. DATABASE_URL should be: postgresql://postgres.[PROJECT-REF]:[PASSWORD]@[HOST]:6543/postgres"
echo ""
echo "Current .env values:"
grep -E "^(DATABASE_URL|SUPABASE_URL)" .env | sed 's/=.*/=***REDACTED***/'
echo ""

read -p "Do you have production Supabase URLs? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Please update .env with production Supabase URLs first:${NC}"
    echo ""
    echo "1. Go to: https://supabase.com/dashboard/project/_/settings/api"
    echo "2. Copy 'Project URL' → SUPABASE_URL"
    echo "3. Copy 'anon public' key → SUPABASE_KEY"
    echo "4. Copy 'service_role' key → SUPABASE_SERVICE_KEY"
    echo ""
    echo "5. Go to: https://supabase.com/dashboard/project/_/settings/database"
    echo "6. Copy 'Connection pooling' URI → DATABASE_URL"
    echo "   (Use port 6543, 'Transaction' mode)"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

echo -e "${BLUE}Setting environment variables via Render API...${NC}"
echo ""

# Function to set an environment variable
set_env_var() {
    local key=$1
    local value=$2
    local display_value="${value:0:30}..."

    echo -e "Setting ${BLUE}${key}${NC}: ${display_value}"

    # Render API expects JSON array of env var objects
    # We need to fetch current vars, update, and send all back
    RESPONSE=$(curl -k -s -X PATCH "${API_BASE}/services/${SERVICE_ID}/env-vars" \
        -H "Authorization: Bearer ${RENDER_API_KEY}" \
        -H "Content-Type: application/json" \
        -d "[{\"key\": \"${key}\", \"value\": \"${value}\"}]" 2>&1)

    if echo "$RESPONSE" | grep -q "error"; then
        echo -e "${RED}❌ Failed to set ${key}${NC}"
        echo "Response: $RESPONSE"
        return 1
    else
        echo -e "${GREEN}✅ ${key} set successfully${NC}"
        return 0
    fi
}

# Set environment variables
echo "1/4: Setting DATABASE_URL..."
if set_env_var "DATABASE_URL" "$DATABASE_URL"; then
    echo ""
else
    echo -e "${RED}Failed. Check API key and service ID.${NC}"
    exit 1
fi

echo "2/4: Setting SUPABASE_URL..."
set_env_var "SUPABASE_URL" "$SUPABASE_URL"
echo ""

echo "3/4: Setting SUPABASE_KEY..."
set_env_var "SUPABASE_KEY" "$SUPABASE_KEY"
echo ""

echo "4/4: Setting SUPABASE_SERVICE_ROLE_KEY..."
# Note: .env has SUPABASE_SERVICE_KEY but backend expects SUPABASE_SERVICE_ROLE_KEY
set_env_var "SUPABASE_SERVICE_ROLE_KEY" "$SUPABASE_SERVICE_KEY"
echo ""

echo -e "${GREEN}✅ All environment variables set successfully!${NC}"
echo ""
echo -e "${BLUE}Triggering deployment...${NC}"

# Trigger deployment
DEPLOY_RESPONSE=$(curl -k -s -X POST \
    "https://api.render.com/deploy/${SERVICE_ID}?key=mT_YPrdnfTk" 2>&1)

if echo "$DEPLOY_RESPONSE" | grep -q "id"; then
    echo -e "${GREEN}✅ Deployment triggered${NC}"
else
    echo -e "${YELLOW}⚠️  Deployment may have been triggered${NC}"
fi

echo ""
echo -e "${BLUE}Monitoring deployment (this takes 3-5 minutes)...${NC}"
echo "Checking health endpoint every 15 seconds..."
echo ""

MAX_ATTEMPTS=20
ATTEMPT=0
SUCCESS=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    echo "Attempt $ATTEMPT/$MAX_ATTEMPTS..."

    HEALTH_CHECK=$(curl -k -s -w "\n%{http_code}" "https://${SERVICE_ID}.onrender.com/health" 2>&1 || echo "000")
    HTTP_CODE=$(echo "$HEALTH_CHECK" | tail -1)
    RESPONSE_BODY=$(echo "$HEALTH_CHECK" | head -n -1)

    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✅ Backend is healthy!${NC}"
        echo "Response: $RESPONSE_BODY"
        SUCCESS=1
        break
    elif [ "$HTTP_CODE" = "502" ] || [ "$HTTP_CODE" = "503" ]; then
        echo -e "${YELLOW}⏳ Service starting (${HTTP_CODE})...${NC}"
    elif [ "$HTTP_CODE" = "404" ]; then
        echo -e "${YELLOW}⏳ Deploying (${HTTP_CODE})...${NC}"
    else
        echo -e "${YELLOW}⏳ Waiting (${HTTP_CODE})...${NC}"
    fi

    if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
        sleep 15
    fi
done

echo ""

if [ $SUCCESS -eq 1 ]; then
    echo -e "${GREEN}🎉 Backend deployment successful!${NC}"
    echo ""
    echo "Your backend is live at:"
    echo "  https://${SERVICE_ID}.onrender.com"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Update Streamlit Cloud secrets:"
    echo "   - Go to: https://share.streamlit.io/"
    echo "   - Update: api_base_url = \"https://${SERVICE_ID}.onrender.com\""
    echo ""
    echo "2. Test your app: https://iswitchroofs.streamlit.app"
    echo ""
else
    echo -e "${RED}❌ Deployment did not complete in expected time${NC}"
    echo "Check: https://dashboard.render.com/web/${SERVICE_ID}"
fi
