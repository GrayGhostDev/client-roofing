#!/bin/bash

# Render API Deployment Script
# Uses Render API directly to configure and deploy the backend service

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🚀 Render API Deployment Script"
echo "================================"
echo ""

# Configuration
SERVICE_ID="srv-d3mlmmur433s73abuar0"
DEPLOY_HOOK_KEY="mT_YPrdnfTk"
DEPLOY_HOOK_URL="https://api.render.com/deploy/${SERVICE_ID}?key=${DEPLOY_HOOK_KEY}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo ""
    echo "Please create .env file with your Supabase credentials:"
    echo "  cp .env.production.example .env"
    echo "  # Edit .env with your actual credentials"
    echo ""
    exit 1
fi

echo -e "${BLUE}📋 Step 1: Loading environment variables${NC}"
echo "=========================================="
echo ""

# Source the .env file to get values
set -a
source .env
set +a

# Validate critical variables
MISSING_VARS=0

check_var() {
    local var_name=$1
    local var_value="${!var_name}"

    if [ -z "$var_value" ] || [ "$var_value" = "your-"* ] || [ "$var_value" = "xxxxx"* ] || [ "$var_value" = "postgresql://user:password"* ]; then
        echo -e "${RED}❌ ${var_name} is not set or using placeholder${NC}"
        MISSING_VARS=$((MISSING_VARS + 1))
    else
        # Show first 20 chars for verification
        echo -e "${GREEN}✅ ${var_name}${NC}: ${var_value:0:20}..."
    fi
}

echo "Checking critical environment variables:"
check_var "DATABASE_URL"
check_var "SUPABASE_URL"
check_var "SUPABASE_KEY"
check_var "SUPABASE_SERVICE_ROLE_KEY"

echo ""

if [ $MISSING_VARS -gt 0 ]; then
    echo -e "${RED}❌ $MISSING_VARS required variable(s) missing or using placeholders${NC}"
    echo ""
    echo "Please update your .env file with actual Supabase credentials from:"
    echo "  https://supabase.com/dashboard/project/_/settings/api"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ All critical variables configured${NC}"
echo ""

echo -e "${BLUE}📋 Step 2: Checking current deployment status${NC}"
echo "=============================================="
echo ""

# Try to get current service status
echo "Checking service health..."
HEALTH_CHECK=$(curl -k -s -w "\n%{http_code}" "https://${SERVICE_ID}.onrender.com/health" 2>&1 || echo "000")
HTTP_CODE=$(echo "$HEALTH_CHECK" | tail -1)
RESPONSE_BODY=$(echo "$HEALTH_CHECK" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Service is currently live and healthy${NC}"
    echo "Response: $RESPONSE_BODY"
elif [ "$HTTP_CODE" = "404" ]; then
    echo -e "${YELLOW}⚠️  Service exists but returns 404 - may need redeployment${NC}"
elif [ "$HTTP_CODE" = "502" ] || [ "$HTTP_CODE" = "503" ]; then
    echo -e "${YELLOW}⚠️  Service is starting up (${HTTP_CODE})${NC}"
else
    echo -e "${RED}❌ Service is not responding (${HTTP_CODE})${NC}"
fi

echo ""

echo -e "${BLUE}📋 Step 3: Environment Variables Configuration${NC}"
echo "==============================================="
echo ""

echo "⚠️  IMPORTANT: Render CLI cannot set environment variables in non-interactive mode."
echo "You need to set these manually in the Render Dashboard:"
echo ""
echo "1. Go to: https://dashboard.render.com/web/${SERVICE_ID}"
echo "2. Click 'Environment' tab"
echo "3. Add/Update these variables:"
echo ""

cat << EOF
DATABASE_URL=${DATABASE_URL}
SUPABASE_URL=${SUPABASE_URL}
SUPABASE_KEY=${SUPABASE_KEY}
SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
EOF

# Check for optional Pusher variables
if [ -n "$PUSHER_APP_ID" ] && [ "$PUSHER_APP_ID" != "1234567" ]; then
    echo "PUSHER_APP_ID=${PUSHER_APP_ID}"
    echo "PUSHER_KEY=${PUSHER_KEY}"
    echo "PUSHER_SECRET=${PUSHER_SECRET}"
fi

# Check for optional Redis variables
if [ -n "$REDIS_URL" ] && [ "$REDIS_URL" != "redis://"* ]; then
    echo "REDIS_URL=${REDIS_URL}"
fi

echo ""
echo "4. Save changes (this will trigger automatic redeployment)"
echo ""

read -p "Have you set these environment variables in Render Dashboard? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⚠️  Please set environment variables first, then run this script again${NC}"
    echo ""
    echo "Render Dashboard: https://dashboard.render.com/web/${SERVICE_ID}"
    exit 1
fi

echo -e "${BLUE}📋 Step 4: Triggering deployment${NC}"
echo "================================="
echo ""

echo "Triggering deployment via webhook..."
DEPLOY_RESPONSE=$(curl -k -s -X POST "$DEPLOY_HOOK_URL" 2>&1)

if echo "$DEPLOY_RESPONSE" | grep -q "id"; then
    echo -e "${GREEN}✅ Deployment triggered successfully${NC}"
    echo "Response: $DEPLOY_RESPONSE"

    # Extract deployment ID if possible
    if command -v jq &> /dev/null; then
        DEPLOY_ID=$(echo "$DEPLOY_RESPONSE" | jq -r '.id // empty')
        if [ -n "$DEPLOY_ID" ]; then
            echo ""
            echo "Deployment ID: $DEPLOY_ID"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  Deployment may have been triggered${NC}"
    echo "Response: $DEPLOY_RESPONSE"
fi

echo ""

echo -e "${BLUE}📋 Step 5: Monitoring deployment${NC}"
echo "================================"
echo ""

echo "Waiting for deployment to complete (this may take 3-5 minutes)..."
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
        echo -e "${GREEN}✅ Service is live and healthy!${NC}"
        echo "Response: $RESPONSE_BODY"
        SUCCESS=1
        break
    elif [ "$HTTP_CODE" = "502" ] || [ "$HTTP_CODE" = "503" ]; then
        echo -e "${YELLOW}⏳ Service is starting up (${HTTP_CODE})...${NC}"
    elif [ "$HTTP_CODE" = "404" ]; then
        echo -e "${YELLOW}⏳ Waiting for deployment (${HTTP_CODE})...${NC}"
    else
        echo -e "${RED}⚠️  Unexpected response (${HTTP_CODE})${NC}"
    fi

    if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
        sleep 15
    fi
done

echo ""

if [ $SUCCESS -eq 1 ]; then
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo ""
    echo "Your backend is live at:"
    echo "  https://${SERVICE_ID}.onrender.com"
    echo "  https://iswitch-roofs-api.onrender.com"
    echo ""
    echo "Health check: https://${SERVICE_ID}.onrender.com/health"
    echo ""

    echo -e "${BLUE}📋 Step 6: Testing API endpoints${NC}"
    echo "================================="
    echo ""

    # Test leads endpoint
    echo "Testing /api/leads endpoint..."
    LEADS_RESPONSE=$(curl -k -s -w "\n%{http_code}" "https://${SERVICE_ID}.onrender.com/api/leads?limit=1" 2>&1 || echo "000")
    LEADS_CODE=$(echo "$LEADS_RESPONSE" | tail -1)

    if [ "$LEADS_CODE" = "200" ]; then
        echo -e "${GREEN}✅ Leads API is working (${LEADS_CODE})${NC}"
    else
        echo -e "${YELLOW}⚠️  Leads API returned ${LEADS_CODE}${NC}"
    fi

    # Test customers endpoint
    echo "Testing /api/customers endpoint..."
    CUSTOMERS_RESPONSE=$(curl -k -s -w "\n%{http_code}" "https://${SERVICE_ID}.onrender.com/api/customers?limit=1" 2>&1 || echo "000")
    CUSTOMERS_CODE=$(echo "$CUSTOMERS_RESPONSE" | tail -1)

    if [ "$CUSTOMERS_CODE" = "200" ]; then
        echo -e "${GREEN}✅ Customers API is working (${CUSTOMERS_CODE})${NC}"
    else
        echo -e "${YELLOW}⚠️  Customers API returned ${CUSTOMERS_CODE}${NC}"
    fi

    echo ""

    echo -e "${BLUE}📋 Next Steps${NC}"
    echo "============="
    echo ""
    echo "1. Update Streamlit Cloud secrets:"
    echo "   - Go to: https://share.streamlit.io/"
    echo "   - Select your app: iswitchroofs"
    echo "   - Update secrets with:"
    echo ""
    echo "   [api]"
    echo "   api_base_url = \"https://${SERVICE_ID}.onrender.com\""
    echo "   ml_api_base_url = \"https://${SERVICE_ID}.onrender.com\""
    echo ""
    echo "2. Test your CRM application:"
    echo "   - Visit: https://iswitchroofs.streamlit.app"
    echo "   - Test lead creation, customer management, etc."
    echo ""
    echo "3. Monitor logs for errors:"
    echo "   - Render logs: https://dashboard.render.com/web/${SERVICE_ID}/logs"
    echo "   - Streamlit logs: Check app console"
    echo ""
else
    echo -e "${RED}❌ Deployment did not complete in expected time${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Check deployment status:"
    echo "   https://dashboard.render.com/web/${SERVICE_ID}"
    echo ""
    echo "2. Review deployment logs for errors"
    echo ""
    echo "3. Verify environment variables are set correctly"
    echo ""
    echo "4. Try accessing the service directly:"
    echo "   https://${SERVICE_ID}.onrender.com/health"
    echo ""
fi
