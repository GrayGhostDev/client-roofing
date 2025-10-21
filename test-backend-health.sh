#!/bin/bash
# =============================================================================
# Backend Health Check Script
# Tests Render backend connectivity and endpoint availability
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Correct Backend URL (Service ID: srv-d3mlmmur433s73abuar0)
BACKEND_URL="https://srv-d3mlmmur433s73abuar0.onrender.com"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Backend Health Check${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Backend URL:${NC} ${BACKEND_URL}"
echo ""

# Unset any proxy settings that might interfere
unset http_proxy
unset https_proxy
unset HTTP_PROXY
unset HTTPS_PROXY

# =============================================================================
# Test 1: Health Endpoint
# =============================================================================
echo -e "${BLUE}Test 1: Health Endpoint${NC}"
echo -e "Testing: ${BACKEND_URL}/health"
echo ""

HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "${BACKEND_URL}/health" 2>&1)
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ SUCCESS${NC} - Health endpoint responding"
    echo -e "Response: ${RESPONSE_BODY}"
elif [ "$HTTP_CODE" = "404" ]; then
    echo -e "${RED}❌ 404 NOT FOUND${NC} - Health endpoint doesn't exist"
    echo -e "${YELLOW}⚠️  Backend is running but /health route not defined${NC}"
    echo -e "Trying root endpoint instead..."
elif [ -z "$HTTP_CODE" ]; then
    echo -e "${RED}❌ CONNECTION FAILED${NC}"
    echo -e "Error: ${RESPONSE_BODY}"
    echo -e "${YELLOW}⚠️  Backend may be sleeping (Render free tier)${NC}"
    echo -e "${YELLOW}⚠️  First request takes 30-60 seconds to wake up${NC}"
else
    echo -e "${YELLOW}⚠️  HTTP ${HTTP_CODE}${NC}"
    echo -e "Response: ${RESPONSE_BODY}"
fi
echo ""

# =============================================================================
# Test 2: Root Endpoint
# =============================================================================
echo -e "${BLUE}Test 2: Root Endpoint${NC}"
echo -e "Testing: ${BACKEND_URL}/"
echo ""

ROOT_RESPONSE=$(curl -s -w "\n%{http_code}" "${BACKEND_URL}/" 2>&1)
HTTP_CODE=$(echo "$ROOT_RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$ROOT_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ SUCCESS${NC} - Backend is responding"
    echo -e "Response: ${RESPONSE_BODY}"
elif [ "$HTTP_CODE" = "404" ]; then
    echo -e "${YELLOW}⚠️  404${NC} - Root endpoint not defined (expected)"
    echo -e "${GREEN}✅ Backend is reachable${NC}"
else
    echo -e "${YELLOW}⚠️  HTTP ${HTTP_CODE}${NC}"
    echo -e "Response: ${RESPONSE_BODY}"
fi
echo ""

# =============================================================================
# Test 3: API Leads Endpoint
# =============================================================================
echo -e "${BLUE}Test 3: Leads Endpoint${NC}"
echo -e "Testing: ${BACKEND_URL}/api/leads?limit=1"
echo ""

# Note: Quotes around URL to prevent zsh globbing issues with ?
LEADS_RESPONSE=$(curl -s -w "\n%{http_code}" "${BACKEND_URL}/api/leads?limit=1" 2>&1)
HTTP_CODE=$(echo "$LEADS_RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$LEADS_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ SUCCESS${NC} - Leads endpoint working!"
    echo -e "Response preview: ${RESPONSE_BODY:0:200}..."
elif [ "$HTTP_CODE" = "404" ]; then
    echo -e "${RED}❌ 404 NOT FOUND${NC} - Leads route not registered"
    echo -e "${YELLOW}⚠️  This is the main issue - routes aren't being registered${NC}"
    echo -e "${YELLOW}⚠️  Check Render logs for 'Failed to register leads routes'${NC}"
elif [ "$HTTP_CODE" = "500" ]; then
    echo -e "${RED}❌ 500 INTERNAL SERVER ERROR${NC}"
    echo -e "${YELLOW}⚠️  Backend has internal errors - check Render logs${NC}"
    echo -e "Response: ${RESPONSE_BODY}"
else
    echo -e "${YELLOW}⚠️  HTTP ${HTTP_CODE}${NC}"
    echo -e "Response: ${RESPONSE_BODY}"
fi
echo ""

# =============================================================================
# Test 4: Business Metrics Endpoint
# =============================================================================
echo -e "${BLUE}Test 4: Business Metrics Endpoint${NC}"
echo -e "Testing: ${BACKEND_URL}/api/business-metrics/realtime/snapshot"
echo ""

METRICS_RESPONSE=$(curl -s -w "\n%{http_code}" "${BACKEND_URL}/api/business-metrics/realtime/snapshot" 2>&1)
HTTP_CODE=$(echo "$METRICS_RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$METRICS_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ SUCCESS${NC} - Business metrics endpoint working!"
    echo -e "Response preview: ${RESPONSE_BODY:0:200}..."
elif [ "$HTTP_CODE" = "404" ]; then
    echo -e "${RED}❌ 404 NOT FOUND${NC} - Business metrics route not registered"
    echo -e "${YELLOW}⚠️  Check Render logs for 'Failed to register business metrics routes'${NC}"
elif [ "$HTTP_CODE" = "500" ]; then
    echo -e "${RED}❌ 500 INTERNAL SERVER ERROR${NC}"
    echo -e "Response: ${RESPONSE_BODY}"
else
    echo -e "${YELLOW}⚠️  HTTP ${HTTP_CODE}${NC}"
    echo -e "Response: ${RESPONSE_BODY}"
fi
echo ""

# =============================================================================
# Summary
# =============================================================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Backend URL:${NC} ${BACKEND_URL}"
echo -e "${YELLOW}Service ID:${NC} srv-d3mlmmur433s73abuar0"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo -e "1. ${YELLOW}Update Streamlit Cloud Secrets${NC}"
echo -e "   Go to: https://share.streamlit.io/"
echo -e "   Settings → Secrets"
echo -e "   Change URLs to: ${BACKEND_URL}"
echo ""
echo -e "2. ${YELLOW}Check Render Logs${NC}"
echo -e "   Go to: https://dashboard.render.com/"
echo -e "   Find service: srv-d3mlmmur433s73abuar0"
echo -e "   Check logs for errors during route registration"
echo ""
echo -e "3. ${YELLOW}Verify Environment Variables${NC}"
echo -e "   Render → Settings → Environment"
echo -e "   Ensure these are set:"
echo -e "   - DATABASE_URL"
echo -e "   - SUPABASE_URL"
echo -e "   - SUPABASE_KEY"
echo -e "   - SECRET_KEY"
echo -e "   - JWT_SECRET_KEY"
echo ""
echo -e "${BLUE}========================================${NC}"
