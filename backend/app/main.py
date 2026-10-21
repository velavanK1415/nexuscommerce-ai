"""
NexusCommerce AI - Backend Application
Autonomous Multi-Agent B2B Procurement & Two-Step Authorization & Milestone Captures on PayPal.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging

from app.core.orchestrator import NexusOrchestrator
from app.core.polling_service import PollingFallbackService
from app.api import (
    mandates,
    negotiate,
    escrow,
    evidence,
    webhooks,
    analytics,
    demo,
    video_merge,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("nexus.main")

app = FastAPI(
    title="NexusCommerce AI - Autonomous B2B Procurement & PayPal Milestone Engine",
    description="Autonomous Multi-Agent B2B Procurement & Two-Step Authorization & Milestone Captures on PayPal with Tamper-Evident Evidence Bundles and AG Studio Analytics.",
    version="2.0.0",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Orchestrator & Polling Fallback Service
orchestrator = NexusOrchestrator()
polling_service = PollingFallbackService(
    paypal_provider=orchestrator.paypal_provider,
    orders_store=orchestrator.orders,
)

# Register routers
app.include_router(mandates.router)
app.include_router(negotiate.router)
app.include_router(escrow.router)
app.include_router(evidence.router)
app.include_router(webhooks.router)
app.include_router(analytics.router)
app.include_router(demo.router)
app.include_router(video_merge.router)


# Mount production frontend static assets if built
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist) and os.path.isdir(os.path.join(frontend_dist, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")


@app.get("/api/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "active_mandates": len(orchestrator.mandates),
        "active_orders": len(orchestrator.orders),
        "demo_mode": orchestrator.paypal_provider.is_demo_mode(),
    }


@app.post("/api/polling/reconcile-all")
async def manual_reconcile():
    """Trigger manual polling reconciliation across all active orders."""
    res = await polling_service.reconcile_all_active()
    return {"reconciled_count": len(res), "results": res}


@app.get("/{full_path:path}")
async def serve_spa_or_root(full_path: str):
    if os.path.exists(frontend_dist):
        file_path = os.path.join(frontend_dist, full_path)
        if full_path and os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)

    return {
        "service": "NexusCommerce AI",
        "description": "Autonomous Multi-Agent B2B Procurement & Two-Step Authorization & Milestone Captures on PayPal",
        "version": "2.0.0",
        "documentation": "/docs",
        "mode": "Zero-Key Demo" if orchestrator.paypal_provider.is_demo_mode() else "Live PayPal v2",
    }
