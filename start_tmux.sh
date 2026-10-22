#!/bin/bash
# ==============================================================================
# NexusCommerce AI - Persistent Background Launcher (tmux)
# Keeps the entire stack running 24/7 even after Antigravity or terminal exits
# ==============================================================================

set -e

PROJECT_DIR="/root/nexuscommerce"
VENV_DIR="$PROJECT_DIR/venv"

echo "=========================================================="
echo "⚡ Starting NexusCommerce AI in Persistent tmux session"
echo "=========================================================="

# 1. Kill any existing nexus tmux session or lingering processes
tmux kill-session -t nexus 2>/dev/null || true
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "vite --host" 2>/dev/null || true
pkill -f "cloudflared tunnel" 2>/dev/null || true
sleep 1

# 2. Launch Backend in Window 0
tmux new-session -d -s nexus -n "backend" \
  "cd $PROJECT_DIR/backend && export PYTHONPATH=$PROJECT_DIR/backend && exec $VENV_DIR/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 2>&1 | tee $PROJECT_DIR/backend.log"

# 3. Launch Frontend in Window 1
tmux new-window -t nexus -n "frontend" \
  "cd $PROJECT_DIR/frontend && exec yarn dev --host 0.0.0.0 --port 5173 2>&1 | tee $PROJECT_DIR/frontend.log"

# 4. Launch Cloudflare Tunnel in Window 2 (using HTTP/2 TCP protocol with auto-retry loop)
tmux new-window -t nexus -n "tunnel" \
  "bash -c 'while true; do echo \"Attempting Cloudflare quick tunnel connection...\"; /usr/local/bin/cloudflared tunnel --protocol http2 --url http://127.0.0.1:5173 2>&1 | tee $PROJECT_DIR/tunnel.log; sleep 2; done'"

echo "Waiting for services to initialize..."
sleep 5

# 5. Extract Cloudflare Public URL
PUBLIC_URL=""
for i in {1..15}; do
  if [ -f "$PROJECT_DIR/tunnel.log" ]; then
    PUBLIC_URL=$(grep -o "https://[a-zA-Z0-9-]*\.trycloudflare\.com" "$PROJECT_DIR/tunnel.log" | grep -v "api.trycloudflare.com" | head -n 1 || true)
    if [ -n "$PUBLIC_URL" ]; then
      echo "$PUBLIC_URL" > "$PROJECT_DIR/public_url.txt"
      break
    fi
  fi
  sleep 1
done

echo "=========================================================="
echo "🎉 NexusCommerce AI is RUNNING PERMANENTLY IN THE BACKGROUND!"
echo "=========================================================="
echo "👉 Local Frontend: http://localhost:5173"
echo "👉 Local Backend:  http://localhost:8000/docs"
if [ -n "$PUBLIC_URL" ]; then
  echo "👉 Public HTTPS:   $PUBLIC_URL"
fi
echo "=========================================================="
echo "ℹ️ This tmux session ('nexus') will STAY RUNNING even if you"
echo "   close Antigravity, close Termux terminal, or exit."
echo "   • To attach:  tmux attach -t nexus"
echo "   • To detach:  Press Ctrl+B, then D"
echo "   • To stop:    /root/nexuscommerce/stop_tmux.sh"
echo "=========================================================="
