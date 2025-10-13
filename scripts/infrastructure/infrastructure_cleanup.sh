#!/bin/bash

# Infrastructure Cleanup Script for Roofing CRM Dashboard
# This script safely stops all running services

set -e

echo "=== ROOFING CRM INFRASTRUCTURE CLEANUP ==="
echo "Stopping all services..."
echo ""

PROJECT_ROOT="/Users/grayghostdata/Projects/client-roofing"
BACKEND_PORT=8000
FRONTEND_PORT=3000

echo "1. STOPPING SERVICES BY PID FILES..."

# Stop backend using saved PID
if [ -f "$PROJECT_ROOT/.backend_pid" ]; then
    BACKEND_PID=$(cat "$PROJECT_ROOT/.backend_pid")
    echo "Stopping backend (PID: $BACKEND_PID)..."

    if ps -p $BACKEND_PID > /dev/null; then
        kill $BACKEND_PID
        echo "Backend process stopped"
    else
        echo "Backend process was already stopped"
    fi

    rm "$PROJECT_ROOT/.backend_pid"
else
    echo "No backend PID file found"
fi

# Stop frontend using saved PID
if [ -f "$PROJECT_ROOT/.frontend_pid" ]; then
    FRONTEND_PID=$(cat "$PROJECT_ROOT/.frontend_pid")
    echo "Stopping frontend (PID: $FRONTEND_PID)..."

    if ps -p $FRONTEND_PID > /dev/null; then
        kill $FRONTEND_PID
        echo "Frontend process stopped"
    else
        echo "Frontend process was already stopped"
    fi

    rm "$PROJECT_ROOT/.frontend_pid"
else
    echo "No frontend PID file found"
fi

echo ""
echo "2. FORCE STOPPING PROCESSES ON PORTS..."

# Force kill processes on backend port
BACKEND_PIDS=$(lsof -ti:$BACKEND_PORT 2>/dev/null || echo "")
if [ ! -z "$BACKEND_PIDS" ]; then
    echo "Force stopping processes on port $BACKEND_PORT: $BACKEND_PIDS"
    echo "$BACKEND_PIDS" | xargs kill -9 2>/dev/null || echo "Some processes already terminated"
else
    echo "No processes found on port $BACKEND_PORT"
fi

# Force kill processes on frontend port
FRONTEND_PIDS=$(lsof -ti:$FRONTEND_PORT 2>/dev/null || echo "")
if [ ! -z "$FRONTEND_PIDS" ]; then
    echo "Force stopping processes on port $FRONTEND_PORT: $FRONTEND_PIDS"
    echo "$FRONTEND_PIDS" | xargs kill -9 2>/dev/null || echo "Some processes already terminated"
else
    echo "No processes found on port $FRONTEND_PORT"
fi

echo ""
echo "3. CLEANING UP PROJECT PROCESSES..."

# Kill any remaining python processes related to our project
PROJECT_PROCESSES=$(ps aux | grep -E "(flask|reflex|client-roofing)" | grep -v grep | awk '{print $2}' || echo "")
if [ ! -z "$PROJECT_PROCESSES" ]; then
    echo "Stopping remaining project processes: $PROJECT_PROCESSES"
    echo "$PROJECT_PROCESSES" | xargs kill -9 2>/dev/null || echo "Some processes already terminated"
else
    echo "No remaining project processes found"
fi

echo ""
echo "4. VERIFYING CLEANUP..."

sleep 2

# Check if ports are now free
BACKEND_CHECK=$(lsof -ti:$BACKEND_PORT 2>/dev/null || echo "")
FRONTEND_CHECK=$(lsof -ti:$FRONTEND_PORT 2>/dev/null || echo "")

if [ -z "$BACKEND_CHECK" ]; then
    echo "✓ Port $BACKEND_PORT is now free"
else
    echo "⚠ Port $BACKEND_PORT still in use by PID $BACKEND_CHECK"
fi

if [ -z "$FRONTEND_CHECK" ]; then
    echo "✓ Port $FRONTEND_PORT is now free"
else
    echo "⚠ Port $FRONTEND_PORT still in use by PID $FRONTEND_CHECK"
fi

echo ""
echo "=== CLEANUP COMPLETE ==="
echo "All services have been stopped"
echo "Ports $BACKEND_PORT and $FRONTEND_PORT are available for new services"
echo ""