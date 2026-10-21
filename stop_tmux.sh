#!/bin/bash
# ==============================================================================
# NexusCommerce AI - Stop persistent background session
# ==============================================================================

tmux kill-session -t nexus 2>/dev/null || true
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "vite --host" 2>/dev/null || true
pkill -f "cloudflared tunnel" 2>/dev/null || true

echo "✅ NexusCommerce AI services stopped."
