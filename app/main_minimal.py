#!/usr/bin/env python3
"""
Minimal version of main.py that starts without database dependency
This helps diagnose Railway deployment issues
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi import FastAPI
import logging

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Create minimal FastAPI app
app = FastAPI(
    title="Jeen.ai Company Representative Bot",
    description="WhatsApp bot for Jeen.ai company support",
    version="2.0"
)

@app.get("/")
async def root():
    """Root endpoint for basic health check."""
    return {
        "message": "Jeen.ai Company Representative Bot is running",
        "status": "healthy",
        "version": "2.0",
        "port": os.getenv("PORT", "8080"),
        "service": "minimal-test"
    }

@app.get("/readiness")
async def readiness():
    """Simple readiness check for Railway healthcheck."""
    return {
        "status": "ok",
        "service": "jeen-ai-bot-minimal", 
        "port": os.getenv("PORT", "8080"),
        "message": "Bot is ready (minimal mode)"
    }

@app.get("/health")
async def health():
    """Additional health endpoint."""
    return {
        "status": "healthy",
        "checks": {
            "app": "running",
            "mode": "minimal"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting minimal app on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )