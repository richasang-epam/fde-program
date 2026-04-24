"""
Main FastAPI application for HR Onboarding Agent.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .core.database import init_db, close_db
from .core.config import settings
from .api import webhook_router, api_router
from .api.middleware import RequestLoggingMiddleware, ErrorHandlingMiddleware, AuthMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered HR Onboarding Coordination Agent",
    debug=settings.debug
)

# Add middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(AuthMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(webhook_router)
app.include_router(api_router)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting HR Onboarding Agent...")

    # Initialize database
    await init_db()

    logger.info("Application started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("Shutting down HR Onboarding Agent...")

    # Close database connections
    await close_db()

    logger.info("Application shut down successfully")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "HR Onboarding Agent API",
        "version": settings.app_version,
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )