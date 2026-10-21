#!/bin/bash
# ==============================================================================
# NexusCommerce AI - Startup Script
# Autonomous Multi-Agent B2B Procurement & Two-Step Authorization Hold & Milestone Captures on PayPal
# ==============================================================================

set -e

PROJECT_DIR="/root/nexuscommerce"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
VENV_DIR="$PROJECT_DIR/venv"

echo "=========================================================="
echo "⚡ NexusCommerce AI - Launching Full Stack System"
echo "=========================================================="

# 1. Check Python Venv
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install -r "$BACKEND_DIR/requirements.txt"
fi

# 2. Start Backend
echo "Starting FastAPI Backend on http://127.0.0.1:8000..."
cd "$BACKEND_DIR"
export PYTHONPATH="$BACKEND_DIR"
nohup "$VENV_DIR/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 > "$PROJECT_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID (logs: $PROJECT_DIR/backend.log)"

# 3. Wait for Backend Health
echo "Waiting for Backend health check..."
for i in {1..15}; do
    if curl -s http://127.0.0.1:8000/api/health > /dev/null; then
        echo "✅ Backend is healthy and listening on http://127.0.0.1:8000"
        break
    fi
    sleep 1
done

# 4. Start Frontend
echo "Starting Vite Frontend on http://0.0.0.0:5173..."
cd "$FRONTEND_DIR"
nohup yarn dev > "$PROJECT_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID (logs: $PROJECT_DIR/frontend.log)"

# Disown processes so they persist when shell exits
disown -a 2>/dev/null || true

echo "=========================================================="
echo "🎉 NexusCommerce AI is UP AND RUNNING!"
echo "👉 Frontend Dashboard: http://localhost:5173"
echo "👉 Backend API & Docs: http://localhost:8000/docs"
echo "👉 Mode: Zero-Key Demo Mode (Ready for Hackathon Judges)"
echo "=========================================================="
