#!/bin/bash
# Deploy iSwitch Roofs Backend to Render.com using CLI
# This script automates the entire deployment process

set -e  # Exit on error

echo "🚀 iSwitch Roofs CRM - Render Deployment Script"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Render CLI is installed
echo "📋 Step 1: Checking Render CLI installation..."
if ! command -v render &> /dev/null; then
    echo -e "${RED}❌ Render CLI is not installed${NC}"
    echo ""
    echo "Install with:"
    echo "  brew install render"
    echo ""
    echo "Or download from: https://render.com/docs/cli"
    exit 1
fi
echo -e "${GREEN}✅ Render CLI is installed${NC}"
echo ""

# Check authentication
echo "📋 Step 2: Checking Render authentication..."
if ! render whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not authenticated with Render${NC}"
    echo ""
    echo "Please authenticate by running:"
    echo -e "${BLUE}  render login${NC}"
    echo ""
    echo "This will open your browser to authenticate."
    echo "After authenticating, run this script again."
    exit 1
fi

USER_EMAIL=$(render whoami -o json | grep -o '"email":"[^"]*"' | cut -d'"' -f4)
echo -e "${GREEN}✅ Authenticated as: ${USER_EMAIL}${NC}"
echo ""

# Check for required environment variables file
echo "📋 Step 3: Checking environment variables..."
ENV_FILE=".env.production"

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠️  $ENV_FILE not found${NC}"
    echo ""
    echo "Creating template $ENV_FILE file..."
    cat > "$ENV_FILE" << 'EOF'
# iSwitch Roofs Backend - Production Environment Variables
# Fill in these values before deploying

# Database (Required - Get from Supabase Dashboard)
DATABASE_URL=postgresql://user:password@host:5432/database
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Optional (if using these services)
PUSHER_APP_ID=your-pusher-app-id
PUSHER_KEY=your-pusher-key
PUSHER_SECRET=your-pusher-secret
REDIS_URL=redis://username:password@host:port/0
EOF
    echo -e "${YELLOW}⚠️  Please edit $ENV_FILE with your actual values${NC}"
    echo "Then run this script again."
    exit 1
fi

# Validate required environment variables
echo "Validating required environment variables..."
REQUIRED_VARS=("DATABASE_URL" "SUPABASE_URL" "SUPABASE_KEY")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^${var}=" "$ENV_FILE" || grep -q "^${var}=.*xxx.*" "$ENV_FILE"; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${RED}❌ Missing or invalid environment variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    echo ""
    echo "Please update $ENV_FILE with valid values"
    exit 1
fi

echo -e "${GREEN}✅ Environment variables validated${NC}"
echo ""

# Navigate to backend directory
echo "📋 Step 4: Preparing deployment..."
cd backend

# Check if render.yaml exists
if [ ! -f "render.yaml" ]; then
    echo -e "${RED}❌ render.yaml not found in backend directory${NC}"
    exit 1
fi
echo -e "${GREEN}✅ render.yaml found${NC}"
echo ""

# Deploy to Render
echo "📋 Step 5: Deploying to Render..."
echo ""
echo -e "${BLUE}🚀 Starting deployment...${NC}"
echo ""

# Deploy using render.yaml
if render services create --yaml render.yaml; then
    echo ""
    echo -e "${GREEN}✅ Service created successfully!${NC}"
    echo ""

    # Get service info
    echo "📊 Getting service information..."
    SERVICE_NAME="iswitch-roofs-api"

    # Wait a moment for service to initialize
    sleep 3

    # Try to get service URL
    if render services list -o json | grep -q "$SERVICE_NAME"; then
        echo ""
        echo -e "${GREEN}✅ Service is live!${NC}"
        echo ""
        echo "🔗 Service URL: https://${SERVICE_NAME}.onrender.com"
        echo ""
        echo "📋 Next steps:"
        echo "  1. Set environment variables:"
        echo "     render config:set --service $SERVICE_NAME --env-file ../.env.production"
        echo ""
        echo "  2. Test health endpoint:"
        echo "     curl https://${SERVICE_NAME}.onrender.com/health"
        echo ""
        echo "  3. Update Streamlit secrets with API URL"
        echo ""
    fi
else
    echo -e "${YELLOW}⚠️  Service may already exist. Updating instead...${NC}"

    # Try to update existing service
    if render services update iswitch-roofs-api --yaml render.yaml; then
        echo -e "${GREEN}✅ Service updated successfully!${NC}"
    else
        echo -e "${RED}❌ Deployment failed${NC}"
        echo ""
        echo "Try manual deployment:"
        echo "  1. render login"
        echo "  2. render services create --yaml backend/render.yaml"
        exit 1
    fi
fi

# Set environment variables
echo ""
echo "📋 Step 6: Setting environment variables..."
cd ..
if render config:set --service iswitch-roofs-api --env-file .env.production 2>/dev/null; then
    echo -e "${GREEN}✅ Environment variables set${NC}"
else
    echo -e "${YELLOW}⚠️  Could not set environment variables automatically${NC}"
    echo "Please set them manually in Render Dashboard:"
    echo "  https://dashboard.render.com/web/iswitch-roofs-api/env"
fi

echo ""
echo "================================================"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "================================================"
echo ""
echo "📝 Summary:"
echo "  ✅ Backend deployed to Render"
echo "  🔗 API URL: https://iswitch-roofs-api.onrender.com"
echo "  📊 Dashboard: https://dashboard.render.com/"
echo ""
echo "🧪 Test your API:"
echo "  curl https://iswitch-roofs-api.onrender.com/health"
echo ""
echo "📋 Next: Update Streamlit Cloud secrets"
echo "  Go to: https://share.streamlit.io/"
echo "  Add: api_base_url = \"https://iswitch-roofs-api.onrender.com\""
echo ""
