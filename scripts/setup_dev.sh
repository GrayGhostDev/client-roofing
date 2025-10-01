#!/bin/bash

# iSwitch Roofs CRM - Development Environment Setup Script
# Version: 1.0.0
# Date: 2025-10-01

set -e  # Exit on error

echo "=================================================="
echo "iSwitch Roofs CRM - Development Setup"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running from project root
if [ ! -f "CLAUDE.md" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    exit 1
fi

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11.0"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python 3.11+ is required. Current version: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python version: $PYTHON_VERSION${NC}"

# Check if .env exists
echo ""
echo -e "${YELLOW}Checking environment configuration...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env file with your actual credentials${NC}"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Create virtual environment
echo ""
echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Created virtual environment${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate
echo -e "${GREEN}✓ Activated virtual environment${NC}"

# Upgrade pip
echo ""
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel
echo -e "${GREEN}✓ Upgraded pip${NC}"

# Install backend dependencies
echo ""
echo -e "${YELLOW}Installing backend dependencies...${NC}"
if [ -f "backend/requirements.txt" ]; then
    pip install -r backend/requirements.txt
    echo -e "${GREEN}✓ Installed backend dependencies${NC}"
else
    echo -e "${YELLOW}⚠️  backend/requirements.txt not found, skipping...${NC}"
fi

# Install Reflex dependencies
echo ""
echo -e "${YELLOW}Installing Reflex frontend dependencies...${NC}"
if [ -f "frontend-reflex/requirements.txt" ]; then
    pip install -r frontend-reflex/requirements.txt
    echo -e "${GREEN}✓ Installed Reflex dependencies${NC}"
else
    echo -e "${YELLOW}⚠️  frontend-reflex/requirements.txt not found, skipping...${NC}"
fi

# Install Streamlit dependencies
echo ""
echo -e "${YELLOW}Installing Streamlit dashboard dependencies...${NC}"
if [ -f "frontend-streamlit/requirements.txt" ]; then
    pip install -r frontend-streamlit/requirements.txt
    echo -e "${GREEN}✓ Installed Streamlit dependencies${NC}"
else
    echo -e "${YELLOW}⚠️  frontend-streamlit/requirements.txt not found, skipping...${NC}"
fi

# Install testing dependencies
echo ""
echo -e "${YELLOW}Installing testing dependencies...${NC}"
pip install pytest pytest-asyncio pytest-cov pytest-mock factory-boy faker playwright black ruff
echo -e "${GREEN}✓ Installed testing dependencies${NC}"

# Install Playwright browsers
echo ""
echo -e "${YELLOW}Installing Playwright browsers...${NC}"
playwright install chromium
echo -e "${GREEN}✓ Installed Playwright browsers${NC}"

# Check Docker
echo ""
echo -e "${YELLOW}Checking Docker installation...${NC}"
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    echo -e "${GREEN}✓ Docker version: $DOCKER_VERSION${NC}"
else
    echo -e "${YELLOW}⚠️  Docker not found. Please install Docker to use containerization${NC}"
fi

# Check k6 for load testing
echo ""
echo -e "${YELLOW}Checking k6 installation...${NC}"
if command -v k6 &> /dev/null; then
    K6_VERSION=$(k6 version | head -n1)
    echo -e "${GREEN}✓ k6 installed: $K6_VERSION${NC}"
else
    echo -e "${YELLOW}⚠️  k6 not found. Install from: https://k6.io/docs/getting-started/installation/${NC}"
fi

# Create necessary directories
echo ""
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p backend/tests/{unit,integration,e2e}
mkdir -p tests/{e2e,load}
mkdir -p frontend-reflex/{assets,.web}
mkdir -p frontend-streamlit/.streamlit
echo -e "${GREEN}✓ Created directories${NC}"

# Run Black and Ruff to check code formatting
echo ""
echo -e "${YELLOW}Checking code formatting...${NC}"
if [ -d "backend/app" ]; then
    black --check backend/app || echo -e "${YELLOW}⚠️  Code formatting issues found. Run 'black backend/app' to fix${NC}"
    ruff check backend/app || echo -e "${YELLOW}⚠️  Linting issues found. Run 'ruff check --fix backend/app' to fix${NC}"
fi

# Print summary
echo ""
echo "=================================================="
echo -e "${GREEN}Development Environment Setup Complete!${NC}"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Supabase credentials"
echo "2. Run migrations: ./scripts/migrate.sh"
echo "3. Seed database: python scripts/seed_database.py"
echo "4. Start backend: cd backend && flask run"
echo "5. Start Reflex frontend: cd frontend-reflex && reflex run"
echo "6. Start Streamlit dashboard: cd frontend-streamlit && streamlit run streamlit_app/app.py"
echo ""
echo "Testing:"
echo "- Run tests: pytest"
echo "- Run with coverage: pytest --cov=backend/app --cov-report=html"
echo "- E2E tests: playwright test tests/e2e"
echo "- Load tests: k6 run tests/load/api_load_test.js"
echo ""
echo "Code Quality:"
echo "- Format code: black backend/app"
echo "- Lint code: ruff check --fix backend/app"
echo ""
echo "Docker:"
echo "- Start services: docker-compose up"
echo "- Stop services: docker-compose down"
echo ""
echo -e "${GREEN}Happy coding!${NC}"
