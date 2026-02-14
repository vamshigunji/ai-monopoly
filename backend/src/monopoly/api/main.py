"""FastAPI application for Monopoly AI Agents backend."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from monopoly.api.routes import router
from monopoly.api.websocket import websocket_router

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan handler for startup and shutdown events.

    This function is called when the application starts and stops.
    Use it for resource initialization and cleanup.
    """
    # Startup
    print("🎲 Monopoly AI Agents backend starting...")
    print("📡 WebSocket endpoint: ws://localhost:8000/ws/game/{game_id}")
    print("🌐 REST API: http://localhost:8000/api")

    yield

    # Shutdown
    print("🛑 Monopoly AI Agents backend shutting down...")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Monopoly AI Agents API",
        description="Backend API for the Monopoly AI Agents game with real-time WebSocket support",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Configure CORS middleware
    default_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    cors_env = os.getenv("CORS_ORIGINS", "")
    extra_origins = [o.strip() for o in cors_env.split(",") if o.strip()]
    allowed_origins = default_origins + extra_origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(router, prefix="/api")
    app.include_router(websocket_router)

    return app


# Create the application instance
app = create_app()


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint - health check."""
    return {
        "service": "Monopoly AI Agents API",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
