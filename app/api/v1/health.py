"""
Health check endpoints.

Provides health and readiness probes for orchestration platforms.
"""

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app import __service_name__, __version__

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(..., description="Current timestamp")


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check if the service is healthy and ready to accept requests",
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns basic service information and status.
    Used by Cloud Run and other orchestration platforms for health probes.
    """
    return HealthResponse(
        status="healthy",
        service=__service_name__,
        version=__version__,
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/ready",
    response_model=HealthResponse,
    summary="Readiness Check",
    description="Check if the service is ready to handle requests",
)
async def readiness_check() -> HealthResponse:
    """
    Readiness check endpoint.
    
    In production, this would check:
    - Database connectivity
    - External service availability
    - Cache availability
    
    For this demonstration, returns the same as health check.
    """
    return HealthResponse(
        status="ready",
        service=__service_name__,
        version=__version__,
        timestamp=datetime.now(timezone.utc),
    )
