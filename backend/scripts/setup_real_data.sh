#!/bin/bash

# =============================================================================
# Real Data Sources Setup Script
# =============================================================================
# This script helps configure and test real data source integrations
# for the iSwitch Roofs CRM live data collection system.
#
# Usage: bash scripts/setup_real_data.sh
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$BACKEND_DIR/.env"
ENV_EXAMPLE="$BACKEND_DIR/.env.example"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Real Data Sources Setup${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# =============================================================================
# STEP 1: Check SSL Certificates
# =============================================================================

echo -e "${YELLOW}[1/7] Checking SSL certificates...${NC}"

if python3 -c "import ssl; print(ssl.get_default_verify_paths())" &> /dev/null; then
    echo -e "${GREEN}✓ Python SSL configuration found${NC}"

    # Test SSL connectivity
    if python3 -c "import requests; requests.get('https://www.weather.gov')" &> /dev/null 2>&1; then
        echo -e "${GREEN}✓ SSL connections working${NC}"
    else
        echo -e "${RED}✗ SSL certificate verification failing${NC}"
        echo -e "${YELLOW}  To fix:${NC}"
        echo -e "  cd /Applications/Python\\ 3.*/Install\\ Certificates.command"
        echo -e "  sudo ./Install\\ Certificates.command"
        echo ""
    fi
else
    echo -e "${RED}✗ SSL configuration not found${NC}"
fi

echo ""

# =============================================================================
# STEP 2: Check .env Configuration
# =============================================================================

echo -e "${YELLOW}[2/7] Checking environment configuration...${NC}"

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}  .env file not found${NC}"

    if [ -f "$ENV_EXAMPLE" ]; then
        echo -e "${BLUE}  Creating .env from .env.example...${NC}"
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        echo -e "${GREEN}✓ Created .env file${NC}"
    else
        echo -e "${RED}✗ No .env.example found${NC}"
    fi
fi

# Check for required API keys
echo -e "${BLUE}  Checking API key configuration...${NC}"

check_env_var() {
    local var_name=$1
    local var_value=$(grep "^${var_name}=" "$ENV_FILE" 2>/dev/null | cut -d '=' -f2- | tr -d '"' | tr -d "'")

    if [ -z "$var_value" ] || [ "$var_value" = "your-key-here" ] || [ "$var_value" = "YOUR_KEY_HERE" ]; then
        echo -e "${RED}    ✗ $var_name not configured${NC}"
        return 1
    else
        echo -e "${GREEN}    ✓ $var_name configured${NC}"
        return 0
    fi
}

# Check each API key
NOAA_CONFIGURED=false
ZILLOW_CONFIGURED=false
TWITTER_CONFIGURED=false
FACEBOOK_CONFIGURED=false
GMAPS_CONFIGURED=false

check_env_var "NOAA_API_TOKEN" && NOAA_CONFIGURED=true || true
check_env_var "ZILLOW_API_KEY" && ZILLOW_CONFIGURED=true || true
check_env_var "TWITTER_BEARER_TOKEN" && TWITTER_CONFIGURED=true || true
check_env_var "FACEBOOK_ACCESS_TOKEN" && FACEBOOK_CONFIGURED=true || true
check_env_var "GOOGLE_MAPS_API_KEY" && GMAPS_CONFIGURED=true || true

echo ""

# =============================================================================
# STEP 3: API Registration Instructions
# =============================================================================

echo -e "${YELLOW}[3/7] API Registration Status & Instructions${NC}"
echo ""

if [ "$NOAA_CONFIGURED" = false ]; then
    echo -e "${BLUE}📊 NOAA Storm Data API (FREE)${NC}"
    echo -e "   Status: ${RED}Not Configured${NC}"
    echo -e "   Register: https://www.ncdc.noaa.gov/cdo-web/token"
    echo -e "   1. Visit registration URL"
    echo -e "   2. Enter your email"
    echo -e "   3. Check email for token"
    echo -e "   4. Add to .env: NOAA_API_TOKEN=your-token"
    echo ""
fi

if [ "$ZILLOW_CONFIGURED" = false ]; then
    echo -e "${BLUE}🏠 Zillow Property Data API (FREE - 1,000 calls/day)${NC}"
    echo -e "   Status: ${RED}Not Configured${NC}"
    echo -e "   Register: https://www.zillow.com/howto/api/APIOverview.htm"
    echo -e "   1. Create Zillow account"
    echo -e "   2. Request API access"
    echo -e "   3. Add to .env: ZILLOW_API_KEY=your-key"
    echo ""
fi

if [ "$TWITTER_CONFIGURED" = false ]; then
    echo -e "${BLUE}🐦 Twitter API v2 (FREE - 500K tweets/month)${NC}"
    echo -e "   Status: ${RED}Not Configured${NC}"
    echo -e "   Register: https://developer.twitter.com/en/portal/dashboard"
    echo -e "   1. Create Twitter Developer account"
    echo -e "   2. Create project and app"
    echo -e "   3. Get Bearer Token"
    echo -e "   4. Add to .env: TWITTER_BEARER_TOKEN=your-token"
    echo ""
fi

if [ "$FACEBOOK_CONFIGURED" = false ]; then
    echo -e "${BLUE}📘 Facebook Graph API (FREE basic access)${NC}"
    echo -e "   Status: ${RED}Not Configured${NC}"
    echo -e "   Register: https://developers.facebook.com/"
    echo -e "   1. Create Facebook Developer account"
    echo -e "   2. Create app"
    echo -e "   3. Get access token"
    echo -e "   4. Add to .env: FACEBOOK_ACCESS_TOKEN=your-token"
    echo ""
fi

if [ "$GMAPS_CONFIGURED" = false ]; then
    echo -e "${BLUE}🗺️  Google Maps API (FREE - \$200/month credit)${NC}"
    echo -e "   Status: ${RED}Not Configured${NC}"
    echo -e "   Register: https://console.cloud.google.com/"
    echo -e "   1. Create Google Cloud project"
    echo -e "   2. Enable Geocoding API"
    echo -e "   3. Create API key"
    echo -e "   4. Add to .env: GOOGLE_MAPS_API_KEY=your-key"
    echo ""
fi

# =============================================================================
# STEP 4: Test External API Connectivity
# =============================================================================

echo -e "${YELLOW}[4/7] Testing external API connectivity...${NC}"

# Test Weather.gov (no auth required)
echo -e "${BLUE}  Testing Weather.gov API...${NC}"
if curl -s --max-time 5 "https://api.weather.gov/alerts/active?area=MI" > /dev/null 2>&1; then
    echo -e "${GREEN}    ✓ Weather.gov API accessible${NC}"
else
    echo -e "${RED}    ✗ Weather.gov API not accessible${NC}"
fi

# Test NOAA (requires token)
if [ "$NOAA_CONFIGURED" = true ]; then
    echo -e "${BLUE}  Testing NOAA API...${NC}"
    NOAA_TOKEN=$(grep "^NOAA_API_TOKEN=" "$ENV_FILE" | cut -d '=' -f2- | tr -d '"' | tr -d "'")
    if curl -s --max-time 5 -H "token: $NOAA_TOKEN" "https://www.ncdc.noaa.gov/cdo-web/api/v2/datasets" > /dev/null 2>&1; then
        echo -e "${GREEN}    ✓ NOAA API accessible with token${NC}"
    else
        echo -e "${RED}    ✗ NOAA API authentication failed${NC}"
    fi
fi

echo ""

# =============================================================================
# STEP 5: Test Database Connection
# =============================================================================

echo -e "${YELLOW}[5/7] Testing database connection...${NC}"

cd "$BACKEND_DIR"

if python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from app.database import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM leads'))
        count = result.scalar()
        print(f'✓ Database connected: {count} leads in database')
        sys.exit(0)
except Exception as e:
    print(f'✗ Database connection failed: {e}')
    sys.exit(1)
" 2>&1 | while read line; do
    if [[ $line == ✓* ]]; then
        echo -e "${GREEN}  $line${NC}"
    else
        echo -e "${RED}  $line${NC}"
    fi
done; then
    echo ""
else
    echo -e "${RED}  Database not accessible${NC}"
    echo ""
fi

# =============================================================================
# STEP 6: Test Redis Connection
# =============================================================================

echo -e "${YELLOW}[6/7] Testing Redis connection...${NC}"

REDIS_URL=$(grep "^REDIS_URL=" "$ENV_FILE" 2>/dev/null | cut -d '=' -f2- | tr -d '"' | tr -d "'")

if [ -z "$REDIS_URL" ]; then
    echo -e "${YELLOW}  Redis URL not configured (optional)${NC}"
else
    if redis-cli -u "$REDIS_URL" PING > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ Redis connected${NC}"
    else
        echo -e "${YELLOW}  ✗ Redis not accessible (caching disabled)${NC}"
    fi
fi

echo ""

# =============================================================================
# STEP 7: Summary and Next Steps
# =============================================================================

echo -e "${YELLOW}[7/7] Setup Summary${NC}"
echo ""

# Count configured APIs
CONFIGURED_COUNT=0
[ "$NOAA_CONFIGURED" = true ] && ((CONFIGURED_COUNT++))
[ "$ZILLOW_CONFIGURED" = true ] && ((CONFIGURED_COUNT++))
[ "$TWITTER_CONFIGURED" = true ] && ((CONFIGURED_COUNT++))
[ "$FACEBOOK_CONFIGURED" = true ] && ((CONFIGURED_COUNT++))
[ "$GMAPS_CONFIGURED" = true ] && ((CONFIGURED_COUNT++))

echo -e "${BLUE}API Configuration:${NC} $CONFIGURED_COUNT/5 sources configured"
echo ""

if [ $CONFIGURED_COUNT -eq 0 ]; then
    echo -e "${RED}⚠️  No API keys configured - system will generate sample data only${NC}"
    echo ""
    echo -e "${YELLOW}Priority Action Items:${NC}"
    echo -e "  1. Register for FREE APIs (NOAA, Weather.gov)"
    echo -e "  2. Add API keys to .env file"
    echo -e "  3. Run this script again to verify"
    echo -e "  4. Test data collection: python3 scripts/test_real_apis.py"
elif [ $CONFIGURED_COUNT -lt 5 ]; then
    echo -e "${YELLOW}⚠️  Partial configuration - some data sources unavailable${NC}"
    echo ""
    echo -e "${YELLOW}Recommended Next Steps:${NC}"
    echo -e "  1. Register for remaining APIs"
    echo -e "  2. Test configured sources: python3 scripts/test_real_apis.py"
    echo -e "  3. Monitor data quality in dashboard"
else
    echo -e "${GREEN}✅ All API sources configured!${NC}"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo -e "  1. Test data collection: python3 scripts/test_real_apis.py"
    echo -e "  2. Start backend: python3 run.py"
    echo -e "  3. Generate real leads: Visit Data Pipeline page"
    echo -e "  4. Monitor results: Visit Live Data Generator page"
fi

echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Setup Complete${NC}"
echo -e "${BLUE}================================${NC}"
