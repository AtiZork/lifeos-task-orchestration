"""API v1 package initialization."""

from fastapi import APIRouter

from app.api.v1 import health, tasks, workflows

# Create API v1 router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])

__all__ = ["api_router"]
