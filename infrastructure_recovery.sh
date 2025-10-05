#!/bin/bash

# Infrastructure Recovery Script for Roofing CRM Dashboard
# This script systematically recovers and starts backend and frontend services

set -e  # Exit on any error

echo "=== ROOFING CRM INFRASTRUCTURE RECOVERY ==="
echo "Starting systematic recovery process..."
echo ""

# Define project paths
PROJECT_ROOT="/Users/grayghostdata/Projects/client-roofing"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend-reflex"

# Define service ports
BACKEND_PORT=8000
FRONTEND_PORT=3000

echo "1. CHECKING CURRENT ENVIRONMENT..."
echo "Project Root: $PROJECT_ROOT"
echo "Backend Directory: $BACKEND_DIR"
echo "Frontend Directory: $FRONTEND_DIR"
echo ""

# Check if directories exist
if [ ! -d "$BACKEND_DIR" ]; then
    echo "ERROR: Backend directory not found at $BACKEND_DIR"
    exit 1
fi

if [ ! -d "$FRONTEND_DIR" ]; then
    echo "ERROR: Frontend directory not found at $FRONTEND_DIR"
    exit 1
fi

echo "2. KILLING EXISTING PROCESSES ON PORTS $BACKEND_PORT AND $FRONTEND_PORT..."

# Kill processes on backend port
BACKEND_PID=$(lsof -ti:$BACKEND_PORT 2>/dev/null || echo "")
if [ ! -z "$BACKEND_PID" ]; then
    echo "Killing process on port $BACKEND_PORT (PID: $BACKEND_PID)"
    kill -9 $BACKEND_PID 2>/dev/null || echo "Process already terminated"
else
    echo "No process found on port $BACKEND_PORT"
fi

# Kill processes on frontend port
FRONTEND_PID=$(lsof -ti:$FRONTEND_PORT 2>/dev/null || echo "")
if [ ! -z "$FRONTEND_PID" ]; then
    echo "Killing process on port $FRONTEND_PORT (PID: $FRONTEND_PID)"
    kill -9 $FRONTEND_PID 2>/dev/null || echo "Process already terminated"
else
    echo "No process found on port $FRONTEND_PORT"
fi

# Kill any python processes that might be related to our project
echo "Checking for related Python processes..."
PROJECT_PROCESSES=$(ps aux | grep -E "(flask|reflex|client-roofing)" | grep -v grep | awk '{print $2}' || echo "")
if [ ! -z "$PROJECT_PROCESSES" ]; then
    echo "Found related processes: $PROJECT_PROCESSES"
    echo "$PROJECT_PROCESSES" | xargs kill -9 2>/dev/null || echo "Some processes already terminated"
else
    echo "No related processes found"
fi

echo ""
echo "3. WAITING FOR PORTS TO BE RELEASED..."
sleep 3

# Verify ports are free
BACKEND_CHECK=$(lsof -ti:$BACKEND_PORT 2>/dev/null || echo "")
FRONTEND_CHECK=$(lsof -ti:$FRONTEND_PORT 2>/dev/null || echo "")

if [ ! -z "$BACKEND_CHECK" ]; then
    echo "WARNING: Port $BACKEND_PORT still in use by PID $BACKEND_CHECK"
else
    echo "Port $BACKEND_PORT is now free"
fi

if [ ! -z "$FRONTEND_CHECK" ]; then
    echo "WARNING: Port $FRONTEND_PORT still in use by PID $FRONTEND_CHECK"
else
    echo "Port $FRONTEND_PORT is now free"
fi

echo ""
echo "4. CHECKING BACKEND CONFIGURATION..."

# Check if backend has requirements.txt
if [ ! -f "$BACKEND_DIR/requirements.txt" ]; then
    echo "ERROR: Backend requirements.txt not found"
    exit 1
fi

# Check if backend has main application file
if [ ! -f "$BACKEND_DIR/run.py" ] && [ ! -f "$BACKEND_DIR/app.py" ] && [ ! -f "$BACKEND_DIR/main.py" ]; then
    echo "ERROR: No backend main application file found (run.py, app.py, or main.py)"
    exit 1
fi

# Determine the backend entry point
BACKEND_ENTRY=""
if [ -f "$BACKEND_DIR/run.py" ]; then
    BACKEND_ENTRY="run.py"
elif [ -f "$BACKEND_DIR/app.py" ]; then
    BACKEND_ENTRY="app.py"
elif [ -f "$BACKEND_DIR/main.py" ]; then
    BACKEND_ENTRY="main.py"
fi

echo "Backend entry point: $BACKEND_ENTRY"

echo ""
echo "5. CHECKING FRONTEND CONFIGURATION..."

# Check if frontend has requirements.txt
if [ ! -f "$FRONTEND_DIR/requirements.txt" ]; then
    echo "ERROR: Frontend requirements.txt not found"
    exit 1
fi

# Check if frontend has rxconfig.py (Reflex configuration)
if [ ! -f "$FRONTEND_DIR/rxconfig.py" ]; then
    echo "ERROR: Frontend rxconfig.py not found"
    exit 1
fi

echo "Frontend configuration found"

echo ""
echo "6. CHECKING PYTHON ENVIRONMENTS..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>/dev/null || echo "Python3 not found")
echo "Python version: $PYTHON_VERSION"

# Check if virtual environments exist
BACKEND_VENV="$BACKEND_DIR/venv"
FRONTEND_VENV="$FRONTEND_DIR/venv"

if [ -d "$BACKEND_VENV" ]; then
    echo "Backend virtual environment found at $BACKEND_VENV"
    BACKEND_PYTHON="$BACKEND_VENV/bin/python"
else
    echo "No backend virtual environment found, using system Python"
    BACKEND_PYTHON="python3"
fi

if [ -d "$FRONTEND_VENV" ]; then
    echo "Frontend virtual environment found at $FRONTEND_VENV"
    FRONTEND_PYTHON="$FRONTEND_VENV/bin/python"
else
    echo "No frontend virtual environment found, using system Python"
    FRONTEND_PYTHON="python3"
fi

echo ""
echo "7. VERIFYING ENVIRONMENT VARIABLES..."

# Check if .env file exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "Environment file found at $PROJECT_ROOT/.env"

    # Check for critical environment variables
    if grep -q "DATABASE_URL" "$PROJECT_ROOT/.env"; then
        echo "✓ DATABASE_URL found in environment"
    else
        echo "⚠ DATABASE_URL not found in environment"
    fi

    if grep -q "SUPABASE_URL" "$PROJECT_ROOT/.env"; then
        echo "✓ SUPABASE_URL found in environment"
    else
        echo "⚠ SUPABASE_URL not found in environment"
    fi
else
    echo "⚠ No .env file found, using .env.example as reference"
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        echo "Copying .env.example to .env..."
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo "Please update .env with your actual configuration values"
    fi
fi

echo ""
echo "8. STARTING BACKEND SERVICE..."

cd "$BACKEND_DIR"

# Install backend dependencies if needed
echo "Installing backend dependencies..."
$BACKEND_PYTHON -m pip install -r requirements.txt

# Start backend service
echo "Starting backend on port $BACKEND_PORT..."
echo "Command: $BACKEND_PYTHON $BACKEND_ENTRY"
echo "Starting in background..."

# Start backend in background with output redirection
nohup $BACKEND_PYTHON $BACKEND_ENTRY > backend.log 2>&1 &
BACKEND_PID=$!

echo "Backend started with PID: $BACKEND_PID"
echo "Backend log file: $BACKEND_DIR/backend.log"

# Wait a moment for backend to start
sleep 5

# Check if backend is running
if ps -p $BACKEND_PID > /dev/null; then
    echo "✓ Backend process is running"

    # Test backend endpoint
    echo "Testing backend connectivity on port $BACKEND_PORT..."
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$BACKEND_PORT" | grep -E "200|404|500" > /dev/null; then
        echo "✓ Backend is responding on port $BACKEND_PORT"
    else
        echo "⚠ Backend may not be responding yet (this is normal during startup)"
    fi
else
    echo "✗ Backend process failed to start"
    echo "Backend log:"
    tail -20 "$BACKEND_DIR/backend.log"
    exit 1
fi

echo ""
echo "9. STARTING FRONTEND SERVICE..."

cd "$FRONTEND_DIR"

# Install frontend dependencies if needed
echo "Installing frontend dependencies..."
$FRONTEND_PYTHON -m pip install -r requirements.txt

# Start frontend service
echo "Starting frontend on port $FRONTEND_PORT..."
echo "Starting in background..."

# Start frontend in background with output redirection
nohup $FRONTEND_PYTHON -m reflex run --port $FRONTEND_PORT > frontend.log 2>&1 &
FRONTEND_PID=$!

echo "Frontend started with PID: $FRONTEND_PID"
echo "Frontend log file: $FRONTEND_DIR/frontend.log"

# Wait a moment for frontend to start
sleep 10

# Check if frontend is running
if ps -p $FRONTEND_PID > /dev/null; then
    echo "✓ Frontend process is running"

    # Test frontend endpoint
    echo "Testing frontend connectivity on port $FRONTEND_PORT..."
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$FRONTEND_PORT" | grep -E "200|404" > /dev/null; then
        echo "✓ Frontend is responding on port $FRONTEND_PORT"
    else
        echo "⚠ Frontend may not be responding yet (this is normal during startup)"
    fi
else
    echo "✗ Frontend process failed to start"
    echo "Frontend log:"
    tail -20 "$FRONTEND_DIR/frontend.log"
    exit 1
fi

echo ""
echo "10. INFRASTRUCTURE RECOVERY COMPLETE!"
echo ""
echo "=== SERVICE STATUS ==="
echo "Backend PID: $BACKEND_PID (Port $BACKEND_PORT)"
echo "Frontend PID: $FRONTEND_PID (Port $FRONTEND_PORT)"
echo ""
echo "=== ACCESS URLS ==="
echo "Backend API: http://localhost:$BACKEND_PORT"
echo "Frontend UI: http://localhost:$FRONTEND_PORT"
echo ""
echo "=== LOG FILES ==="
echo "Backend logs: $BACKEND_DIR/backend.log"
echo "Frontend logs: $FRONTEND_DIR/frontend.log"
echo ""
echo "=== MONITORING COMMANDS ==="
echo "Check backend status: ps -p $BACKEND_PID"
echo "Check frontend status: ps -p $FRONTEND_PID"
echo "View backend logs: tail -f $BACKEND_DIR/backend.log"
echo "View frontend logs: tail -f $FRONTEND_DIR/frontend.log"
echo "Check port usage: lsof -i:$BACKEND_PORT -i:$FRONTEND_PORT"
echo ""
echo "=== SHUTDOWN COMMANDS ==="
echo "Stop backend: kill $BACKEND_PID"
echo "Stop frontend: kill $FRONTEND_PID"
echo "Emergency stop all: pkill -f 'python.*client-roofing'"
echo ""

# Save process IDs for later reference
echo "$BACKEND_PID" > "$PROJECT_ROOT/.backend_pid"
echo "$FRONTEND_PID" > "$PROJECT_ROOT/.frontend_pid"

echo "Process IDs saved to .backend_pid and .frontend_pid files"
echo "Infrastructure recovery completed successfully!"