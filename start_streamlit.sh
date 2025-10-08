#!/bin/bash
# Start Streamlit Dashboard with Proxy Bypass
# Bypasses Proxyman for local API connections

echo "🚀 Starting iSwitch Roofs CRM - Streamlit Dashboard"
echo ""
echo "Configuration:"
echo "├── API URL: http://localhost:8000/api"
echo "├── Dashboard URL: http://localhost:8501"
echo "├── Proxy: Bypassed for localhost"
echo ""

# Set environment to bypass proxy
export NO_PROXY="localhost,127.0.0.1,*.local"
export no_proxy="localhost,127.0.0.1,*.local"

# Navigate to frontend directory
cd "$(dirname "$0")/frontend-streamlit"

# Check if backend is running
echo "Checking backend connection..."
if curl -s --connect-timeout 2 http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is running on port 8000"
else
    echo "⚠️  Warning: Backend not responding on port 8000"
    echo "   Start backend first: cd backend && python run.py"
    echo ""
fi

echo ""
echo "Starting Streamlit dashboard..."
echo "Press Ctrl+C to stop"
echo ""

# Start Streamlit
streamlit run app.py --server.headless=true
