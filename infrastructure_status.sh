#!/bin/bash

# Infrastructure Status Check Script for Roofing CRM Dashboard

echo "================================================================================"
echo "                    ROOFING CRM INFRASTRUCTURE STATUS CHECK"
echo "================================================================================"
echo ""

PROJECT_ROOT="/Users/grayghostdata/Projects/client-roofing"
BACKEND_PORT=8001
FRONTEND_PORT=3000

# Check if PID files exist
if [ ! -f "$PROJECT_ROOT/.backend_pid" ] || [ ! -f "$PROJECT_ROOT/.frontend_pid" ]; then
    echo "❌ Service PID files not found. Services may not be running."
    echo "   Run infrastructure_recovery.sh to start services."
    exit 1
fi

BACKEND_PID=$(cat "$PROJECT_ROOT/.backend_pid")
FRONTEND_PID=$(cat "$PROJECT_ROOT/.frontend_pid")

echo "📊 SERVICE STATUS:"
echo "=================="

# Check Backend
echo ""
echo "🔧 BACKEND SERVICE (Flask API):"
echo "   PID: $BACKEND_PID"
echo "   Port: $BACKEND_PORT"

if ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo "   Process: ✅ Running"

    # Test connectivity
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$BACKEND_PORT 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        echo "   HTTP Status: ✅ Responding (HTTP $HTTP_CODE)"
    else
        echo "   HTTP Status: ⚠️  Not responding (HTTP $HTTP_CODE)"
    fi

    # Check endpoints
    echo "   Available Endpoints:"
    echo "     • Health Check: http://localhost:$BACKEND_PORT/health"
    echo "     • API Root: http://localhost:$BACKEND_PORT/api/"
    echo "     • Leads API: http://localhost:$BACKEND_PORT/api/leads"
    echo "     • Customers API: http://localhost:$BACKEND_PORT/api/customers"
    echo "     • Projects API: http://localhost:$BACKEND_PORT/api/projects"
else
    echo "   Process: ❌ Not running"
fi

# Check Frontend
echo ""
echo "🎨 FRONTEND SERVICE (Reflex UI):"
echo "   PID: $FRONTEND_PID"
echo "   Port: $FRONTEND_PORT"

if ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo "   Process: ✅ Running"

    # Test connectivity
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$FRONTEND_PORT 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        echo "   HTTP Status: ✅ Responding (HTTP $HTTP_CODE)"
    else
        echo "   HTTP Status: ⚠️  Not responding (HTTP $HTTP_CODE)"
    fi

    # Check pages
    echo "   Available Pages:"
    echo "     • Dashboard: http://localhost:$FRONTEND_PORT/"
    echo "     • Leads: http://localhost:$FRONTEND_PORT/leads"
    echo "     • Customers: http://localhost:$FRONTEND_PORT/customers"
    echo "     • Projects: http://localhost:$FRONTEND_PORT/projects"
    echo "     • Analytics: http://localhost:$FRONTEND_PORT/analytics"
    echo "     • Settings: http://localhost:$FRONTEND_PORT/settings"
else
    echo "   Process: ❌ Not running"
fi

echo ""
echo "🔌 PORT USAGE:"
echo "=============="
echo "   Backend Port $BACKEND_PORT:"
BACKEND_PORT_USAGE=$(lsof -i:$BACKEND_PORT 2>/dev/null | tail -n +2)
if [ ! -z "$BACKEND_PORT_USAGE" ]; then
    echo "     ✅ In use by backend service"
else
    echo "     ❌ Not in use"
fi

echo "   Frontend Port $FRONTEND_PORT:"
FRONTEND_PORT_USAGE=$(lsof -i:$FRONTEND_PORT 2>/dev/null | tail -n +2)
if [ ! -z "$FRONTEND_PORT_USAGE" ]; then
    echo "     ✅ In use by frontend service"
else
    echo "     ❌ Not in use"
fi

echo ""
echo "📝 LOG FILES:"
echo "============="
echo "   Backend logs: $PROJECT_ROOT/backend/backend.log"
if [ -f "$PROJECT_ROOT/backend/backend.log" ]; then
    BACKEND_LOG_SIZE=$(wc -l < "$PROJECT_ROOT/backend/backend.log")
    echo "     📄 $BACKEND_LOG_SIZE lines"
    echo "     📅 Last 3 lines:"
    tail -3 "$PROJECT_ROOT/backend/backend.log" | sed 's/^/        /'
else
    echo "     ❌ Not found"
fi

echo ""
echo "   Frontend logs: $PROJECT_ROOT/frontend-reflex/frontend.log"
if [ -f "$PROJECT_ROOT/frontend-reflex/frontend.log" ]; then
    FRONTEND_LOG_SIZE=$(wc -l < "$PROJECT_ROOT/frontend-reflex/frontend.log")
    echo "     📄 $FRONTEND_LOG_SIZE lines"
    echo "     📅 Last 3 lines:"
    tail -3 "$PROJECT_ROOT/frontend-reflex/frontend.log" | sed 's/^/        /'
else
    echo "     ❌ Not found"
fi

echo ""
echo "⚙️  MANAGEMENT COMMANDS:"
echo "======================="
echo "   Stop services: ./infrastructure_cleanup.sh"
echo "   Restart services: ./infrastructure_recovery.sh"
echo "   Check status: ./infrastructure_status.sh"
echo ""
echo "   Monitor backend logs: tail -f backend/backend.log"
echo "   Monitor frontend logs: tail -f frontend-reflex/frontend.log"
echo ""
echo "   Manual process control:"
echo "     • Stop backend: kill $BACKEND_PID"
echo "     • Stop frontend: kill $FRONTEND_PID"

echo ""
echo "================================================================================"

# Overall status
BACKEND_OK=false
FRONTEND_OK=false

if ps -p $BACKEND_PID > /dev/null 2>&1; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$BACKEND_PORT 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        BACKEND_OK=true
    fi
fi

if ps -p $FRONTEND_PID > /dev/null 2>&1; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$FRONTEND_PORT 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        FRONTEND_OK=true
    fi
fi

if $BACKEND_OK && $FRONTEND_OK; then
    echo "🎉 STATUS: All services are running and responding correctly!"
    echo "   🌐 Access your CRM dashboard at: http://localhost:$FRONTEND_PORT"
    echo "   🔧 Access your API at: http://localhost:$BACKEND_PORT"
elif $BACKEND_OK && ! $FRONTEND_OK; then
    echo "⚠️  STATUS: Backend is running, but frontend needs attention."
    echo "   Try restarting with: ./infrastructure_recovery.sh"
elif ! $BACKEND_OK && $FRONTEND_OK; then
    echo "⚠️  STATUS: Frontend is running, but backend needs attention."
    echo "   Try restarting with: ./infrastructure_recovery.sh"
else
    echo "❌ STATUS: Both services need attention."
    echo "   Run: ./infrastructure_recovery.sh to restart all services"
fi

echo "================================================================================"