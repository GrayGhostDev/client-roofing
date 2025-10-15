#!/bin/bash
# Comprehensive deployment verification script
# Tests both Render backend and Streamlit frontend configuration

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🔍 iSwitch Roofs CRM - Deployment Verification"
echo "=============================================="
echo ""

# Configuration
RENDER_SERVICE_ID="srv-d3mlmmur433s73abuar0"
BACKEND_URLS=(
    "https://iswitch-roofs-api.onrender.com"
    "https://srv-d3mlmmur433s73abuar0.onrender.com"
)
STREAMLIT_URL="https://iswitchroofs.streamlit.app"

# Track results
ISSUES=0
WARNINGS=0

echo "📋 Step 1: Checking Render Backend Status"
echo "==========================================="
echo ""

# Try to find working backend URL
WORKING_URL=""
for url in "${BACKEND_URLS[@]}"; do
    echo "Testing: $url/health"
    HTTP_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" "$url/health" 2>&1 || echo "000")

    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✅ Backend is live at: $url${NC}"
        WORKING_URL="$url"

        # Get health check response
        HEALTH=$(curl -k -s "$url/health" 2>&1)
        echo "Health response: $HEALTH"

        # Check if database is connected
        if echo "$HEALTH" | grep -q "healthy"; then
            echo -e "${GREEN}✅ Backend reports healthy status${NC}"
        else
            echo -e "${YELLOW}⚠️  Backend may not be fully healthy${NC}"
            WARNINGS=$((WARNINGS + 1))
        fi

        if echo "$HEALTH" | grep -q "database.*connected"; then
            echo -e "${GREEN}✅ Database connection confirmed${NC}"
        else
            echo -e "${YELLOW}⚠️  Database connection status unknown${NC}"
            WARNINGS=$((WARNINGS + 1))
        fi

        break
    elif [ "$HTTP_CODE" = "404" ]; then
        echo -e "${YELLOW}⚠️  Service exists but returns 404 - may still be deploying${NC}"
    elif [ "$HTTP_CODE" = "502" ] || [ "$HTTP_CODE" = "503" ]; then
        echo -e "${YELLOW}⚠️  Service starting up (${HTTP_CODE})${NC}"
    else
        echo -e "${RED}❌ No response from $url (${HTTP_CODE})${NC}"
    fi
done

if [ -z "$WORKING_URL" ]; then
    echo ""
    echo -e "${RED}❌ Backend is not responding${NC}"
    echo ""
    echo "Possible issues:"
    echo "  1. Deployment still in progress (check Render dashboard)"
    echo "  2. Service failed to start (check logs)"
    echo "  3. Environment variables not configured"
    echo ""
    echo "Check Render dashboard:"
    echo "  https://dashboard.render.com/web/$RENDER_SERVICE_ID"
    echo ""
    ISSUES=$((ISSUES + 1))
else
    echo ""
    echo -e "${GREEN}✅ Backend URL confirmed: $WORKING_URL${NC}"
    echo ""

    # Test API endpoints
    echo "Testing API endpoints..."

    # Test leads endpoint
    LEADS_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" "$WORKING_URL/api/leads?limit=1" 2>&1 || echo "000")
    if [ "$LEADS_CODE" = "200" ]; then
        echo -e "${GREEN}✅ Leads API responding (${LEADS_CODE})${NC}"
    else
        echo -e "${YELLOW}⚠️  Leads API returned ${LEADS_CODE}${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi

    # Test customers endpoint
    CUSTOMERS_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" "$WORKING_URL/api/customers?limit=1" 2>&1 || echo "000")
    if [ "$CUSTOMERS_CODE" = "200" ]; then
        echo -e "${GREEN}✅ Customers API responding (${CUSTOMERS_CODE})${NC}"
    else
        echo -e "${YELLOW}⚠️  Customers API returned ${CUSTOMERS_CODE}${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

echo ""
echo "📋 Step 2: Checking Render Configuration"
echo "========================================="
echo ""

# Check render.yaml
if [ -f "backend/render.yaml" ]; then
    echo -e "${GREEN}✅ render.yaml exists${NC}"

    # Verify key configurations
    if grep -q "rootDir: backend" backend/render.yaml; then
        echo -e "${GREEN}✅ rootDir correctly set to 'backend'${NC}"
    else
        echo -e "${RED}❌ rootDir not set correctly${NC}"
        ISSUES=$((ISSUES + 1))
    fi

    if grep -q "healthCheckPath: /health" backend/render.yaml; then
        echo -e "${GREEN}✅ Health check path configured${NC}"
    else
        echo -e "${YELLOW}⚠️  Health check path not found${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi

    if grep -q "autoDeploy: true" backend/render.yaml; then
        echo -e "${GREEN}✅ Auto-deploy enabled${NC}"
    else
        echo -e "${YELLOW}⚠️  Auto-deploy not enabled${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${RED}❌ backend/render.yaml not found${NC}"
    ISSUES=$((ISSUES + 1))
fi

echo ""
echo "📋 Step 3: Verifying Streamlit Configuration"
echo "============================================="
echo ""

# Check Streamlit app
echo "Testing: $STREAMLIT_URL"
STREAMLIT_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" "$STREAMLIT_URL" 2>&1 || echo "000")

if [ "$STREAMLIT_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Streamlit app is accessible${NC}"

    # Check if app shows errors
    STREAMLIT_CONTENT=$(curl -k -s "$STREAMLIT_URL" 2>&1)
    if echo "$STREAMLIT_CONTENT" | grep -qi "connection.*refused\|connection.*error\|failed.*connect"; then
        echo -e "${RED}❌ Streamlit app shows connection errors${NC}"
        echo "   This means Streamlit secrets need to be updated"
        ISSUES=$((ISSUES + 1))
    else
        echo -e "${GREEN}✅ No obvious connection errors detected${NC}"
    fi
else
    echo -e "${RED}❌ Streamlit app not accessible (${STREAMLIT_CODE})${NC}"
    ISSUES=$((ISSUES + 1))
fi

# Check Streamlit files
echo ""
echo "Checking Streamlit configuration files..."

if [ -f "frontend-streamlit/Home.py" ]; then
    echo -e "${GREEN}✅ Home.py exists${NC}"
else
    echo -e "${RED}❌ Home.py not found${NC}"
    ISSUES=$((ISSUES + 1))
fi

if [ -f "frontend-streamlit/requirements.txt" ]; then
    echo -e "${GREEN}✅ requirements.txt exists${NC}"

    # Check for critical dependencies
    if grep -q "streamlit" frontend-streamlit/requirements.txt; then
        echo -e "${GREEN}✅ streamlit dependency listed${NC}"
    fi

    if grep -q "streamlit-aggrid==1.1.9" frontend-streamlit/requirements.txt; then
        echo -e "${GREEN}✅ streamlit-aggrid 1.1.9 (fixes altair conflict)${NC}"
    else
        echo -e "${YELLOW}⚠️  streamlit-aggrid version may need updating${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${RED}❌ requirements.txt not found${NC}"
    ISSUES=$((ISSUES + 1))
fi

echo ""
echo "📋 Step 4: Configuration File Checks"
echo "====================================="
echo ""

# Check app.py redirect
if [ -f "frontend-streamlit/app.py" ]; then
    echo -e "${GREEN}✅ app.py redirect exists${NC}"
    if grep -q "import Home" frontend-streamlit/app.py; then
        echo -e "${GREEN}✅ app.py correctly redirects to Home.py${NC}"
    else
        echo -e "${YELLOW}⚠️  app.py may not redirect correctly${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${YELLOW}⚠️  app.py not found (may need to update Streamlit main file setting)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# Check .streamlit config
if [ -f "frontend-streamlit/.streamlit/config.toml" ]; then
    echo -e "${GREEN}✅ .streamlit/config.toml exists${NC}"
else
    echo -e "${YELLOW}⚠️  .streamlit/config.toml not found${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""
echo "=============================================="
echo "📊 Verification Summary"
echo "=============================================="
echo ""

if [ $ISSUES -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}🎉 All checks passed!${NC}"
    echo ""
    echo "Your deployment appears to be configured correctly."
    if [ -n "$WORKING_URL" ]; then
        echo ""
        echo "Backend URL: $WORKING_URL"
        echo "Frontend URL: $STREAMLIT_URL"
        echo ""
        echo "Next steps:"
        echo "  1. Verify Streamlit secrets are updated with backend URL"
        echo "  2. Test your CRM features in the browser"
        echo "  3. Monitor logs for any runtime errors"
    fi
elif [ $ISSUES -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Configuration complete with ${WARNINGS} warning(s)${NC}"
    echo ""
    echo "Your deployment should work, but there are some minor issues to address."
else
    echo -e "${RED}❌ Found ${ISSUES} critical issue(s) and ${WARNINGS} warning(s)${NC}"
    echo ""
    echo "Action Required:"
    echo ""

    if [ -z "$WORKING_URL" ]; then
        echo "1. Check Render Dashboard:"
        echo "   https://dashboard.render.com/web/$RENDER_SERVICE_ID"
        echo ""
        echo "2. Verify deployment status:"
        echo "   - Is deployment complete?"
        echo "   - Are there build errors in logs?"
        echo "   - Are environment variables set?"
        echo ""
        echo "3. Required environment variables in Render:"
        echo "   - DATABASE_URL"
        echo "   - SUPABASE_URL"
        echo "   - SUPABASE_KEY"
        echo "   - SUPABASE_SERVICE_ROLE_KEY"
        echo ""
    fi

    echo "4. Check Streamlit secrets:"
    echo "   https://share.streamlit.io/"
    echo "   Update api_base_url with your backend URL"
    echo ""
fi

echo ""
echo "=============================================="
echo ""

# Exit with appropriate code
if [ $ISSUES -gt 0 ]; then
    exit 1
else
    exit 0
fi
