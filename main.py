"""
CallPilot API - Main Entry Point

AI Voice Agent API for Medical Appointment Scheduling.

Run with: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import app_config
from src.api.routes.calendar import router as calendar_router

# Initialize FastAPI app
app = FastAPI(
    title="CallPilot API",
    description="AI Voice Agent API for Medical Appointment Scheduling",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - allow all origins for development
# Restrict in production!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(calendar_router)


# ============== Health Check ==============

@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": app_config.app_name,
        "version": "1.0.0"
    }


@app.get("/", tags=["Health"])
def root():
    """Root endpoint with API info."""
    return {
        "service": app_config.app_name,
        "description": "AI Voice Agent API for Medical Appointment Scheduling",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "calendar_status": "GET /api/calendar/status",
            "auth_url": "GET /api/calendar/auth-url",
            "check_availability": "POST /api/calendar/check-availability",
            "appointments": "/api/calendar/appointments"
        }
    }


# ============== Run Server ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=app_config.host,
        port=app_config.port,
        reload=app_config.debug
    )