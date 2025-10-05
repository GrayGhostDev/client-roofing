#!/bin/bash

# Reflex Environment Cleanup and Setup Script
# This script ensures a clean Reflex development environment

echo "🔧 Reflex Environment Cleanup and Setup"
echo "========================================"

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -i :$port >/dev/null 2>&1; then
        echo "Port $port is in use"
        return 0
    else
        echo "Port $port is free"
        return 1
    fi
}

# Function to kill processes by pattern
kill_processes() {
    local pattern=$1
    local pids=$(pgrep -f "$pattern")
    if [ -n "$pids" ]; then
        echo "Killing processes matching: $pattern"
        echo "PIDs: $pids"
        kill $pids 2>/dev/null || true
        sleep 2
        # Force kill if still running
        for pid in $pids; do
            if kill -0 $pid 2>/dev/null; then
                echo "Force killing PID: $pid"
                kill -9 $pid 2>/dev/null || true
            fi
        done
    else
        echo "No processes found matching: $pattern"
    fi
}

echo ""
echo "Step 1: Current Process Analysis"
echo "--------------------------------"
echo "Current Reflex-related processes:"
ps aux | grep -E "(reflex|python.*frontend)" | grep -v grep || echo "No Reflex processes found"

echo ""
echo "Step 2: Port Status Check"
echo "-------------------------"
check_port 3000
check_port 8001
check_port 8009

echo ""
echo "Step 3: Cleanup Old Processes"
echo "------------------------------"

# Clean up old backend processes
kill_processes "uvicorn.*8009"
kill_processes "python.*8009"

# Clean up any stray Reflex processes (but preserve the main one)
# We'll be more selective here
MAIN_REFLEX_PID=$(pgrep -f "reflex run --frontend-port 3000 --backend-port 8001")
if [ -n "$MAIN_REFLEX_PID" ]; then
    echo "Main Reflex process found: $MAIN_REFLEX_PID (preserving)"
else
    echo "No main Reflex process found"
fi

# Kill any orphaned node/bun processes that aren't part of the main Reflex instance
echo "Cleaning up orphaned build processes..."
ORPHAN_NODE=$(pgrep -f "react-router dev" | grep -v "$MAIN_REFLEX_PID" || true)
ORPHAN_BUN=$(pgrep -f "bun run dev" | grep -v "$MAIN_REFLEX_PID" || true)

if [ -n "$ORPHAN_NODE" ]; then
    echo "Killing orphaned Node processes: $ORPHAN_NODE"
    kill $ORPHAN_NODE 2>/dev/null || true
fi

if [ -n "$ORPHAN_BUN" ]; then
    echo "Killing orphaned Bun processes: $ORPHAN_BUN"
    kill $ORPHAN_BUN 2>/dev/null || true
fi

echo ""
echo "Step 4: Clean Reflex Cache and Temp Files"
echo "------------------------------------------"

# Remove Reflex cache and build artifacts
if [ -d ".web" ]; then
    echo "Cleaning .web directory..."
    rm -rf .web/.next 2>/dev/null || true
    rm -rf .web/node_modules/.cache 2>/dev/null || true
fi

# Clean Python cache
echo "Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

echo ""
echo "Step 5: Verify Clean Environment"
echo "---------------------------------"
sleep 2

echo "Remaining Reflex processes:"
ps aux | grep -E "(reflex|python.*frontend)" | grep -v grep || echo "✅ No stray processes found"

echo ""
echo "Final port status:"
check_port 3000
check_port 8001
check_port 8009

echo ""
echo "Step 6: Environment Ready"
echo "-------------------------"
echo "✅ Cleanup complete!"
echo ""
echo "To start a fresh Reflex instance:"
echo "  source venv/bin/activate"
echo "  reflex run --frontend-port 3000 --backend-port 8001"
echo ""
echo "Current services:"
if check_port 3000; then
    echo "  - Frontend: http://localhost:3000"
fi
if check_port 8001; then
    echo "  - Backend: http://localhost:8001"
fi

echo ""
echo "🎉 Reflex environment is clean and ready!"