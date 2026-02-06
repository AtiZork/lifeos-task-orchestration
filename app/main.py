"""
LifeOS Task Orchestration Service - Main Application

FastAPI application entry point with middleware, CORS, and exception handling.
"""

from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __service_name__, __version__
from app.api.v1 import api_router
from app.config import get_settings
from app.utils import generate_correlation_id, get_logger, setup_logging
from app.utils.logger import correlation_id_ctx
from app.utils.exceptions import (
    AgentExecutionException,
    LifeOSException,
    TaskNotFoundException,
    TimeoutException,
    ValidationException,
    WorkflowExecutionException,
    WorkflowNotFoundException,
)

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    
    Manages startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {__service_name__} v{__version__}")
    settings = get_settings()
    logger.info(
        f"Environment: {settings.environment}",
        extra={"environment": settings.environment},
    )
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {__service_name__}")


# Create FastAPI application
app = FastAPI(
    title="LifeOS Task Orchestration Service",
    description=(
        "A cloud-native FastAPI backend service for intelligent task and workflow execution. "
        "Part of Akaion's LifeOS platform - an AI-powered operating system that orchestrates "
        "tools, data, and workflows through intelligent agents."
    ),
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Get settings
settings = get_settings()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins_list() if not settings.is_production else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Correlation ID middleware
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Middleware to add correlation ID to each request."""
    # Get from header or generate new
    correlation_id = request.headers.get("X-Correlation-ID") or generate_correlation_id()
    
    # Set in context for logger
    token = correlation_id_ctx.set(correlation_id)
    
    try:
        response = await call_next(request)
        # Add to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        return response
    finally:
        # Reset context
        correlation_id_ctx.reset(token)



# Exception handlers
@app.exception_handler(TaskNotFoundException)
async def task_not_found_handler(
    request: Request, exc: TaskNotFoundException
) -> JSONResponse:
    """Handle TaskNotFoundException with proper HTTP response."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "type": "https://lifeos.akaion.dev/errors/task-not-found",
            "title": "Task Not Found",
            "status": 404,
            "detail": exc.message,
            "instance": str(request.url),
        },
    )


@app.exception_handler(WorkflowNotFoundException)
async def workflow_not_found_handler(
    request: Request, exc: WorkflowNotFoundException
) -> JSONResponse:
    """Handle WorkflowNotFoundException with proper HTTP response."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "type": "https://lifeos.akaion.dev/errors/workflow-not-found",
            "title": "Workflow Not Found",
            "status": 404,
            "detail": exc.message,
            "instance": str(request.url),
        },
    )


@app.exception_handler(ValidationException)
async def validation_exception_handler(
    request: Request, exc: ValidationException
) -> JSONResponse:
    """Handle ValidationException with proper HTTP response."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "type": "https://lifeos.akaion.dev/errors/validation-error",
            "title": "Validation Error",
            "status": 400,
            "detail": exc.message,
            "instance": str(request.url),
            "errors": [
                {
                    "field": exc.field,
                    "message": exc.reason,
                }
            ],
        },
    )


@app.exception_handler(AgentExecutionException)
async def agent_execution_exception_handler(
    request: Request, exc: AgentExecutionException
) -> JSONResponse:
    """Handle AgentExecutionException with proper HTTP response."""
    logger.error(
        f"Agent execution failed: {exc.agent_name}",
        extra={"agent_name": exc.agent_name, "reason": exc.reason},
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "https://lifeos.akaion.dev/errors/agent-execution-error",
            "title": "Agent Execution Error",
            "status": 500,
            "detail": exc.message,
            "instance": str(request.url),
        },
    )


@app.exception_handler(WorkflowExecutionException)
async def workflow_execution_exception_handler(
    request: Request, exc: WorkflowExecutionException
) -> JSONResponse:
    """Handle WorkflowExecutionException with proper HTTP response."""
    logger.error(
        f"Workflow execution failed: {exc.workflow_name}",
        extra={
            "workflow_name": exc.workflow_name,
            "step": exc.step,
            "reason": exc.reason,
        },
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "https://lifeos.akaion.dev/errors/workflow-execution-error",
            "title": "Workflow Execution Error",
            "status": 500,
            "detail": exc.message,
            "instance": str(request.url),
        },
    )


@app.exception_handler(TimeoutException)
async def timeout_exception_handler(
    request: Request, exc: TimeoutException
) -> JSONResponse:
    """Handle TimeoutException with proper HTTP response."""
    logger.error(
        f"Operation timed out: {exc.operation}",
        extra={"operation": exc.operation, "timeout_seconds": exc.timeout_seconds},
    )
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={
            "type": "https://lifeos.akaion.dev/errors/timeout-error",
            "title": "Operation Timeout",
            "status": 504,
            "detail": exc.message,
            "instance": str(request.url),
        },
    )


@app.exception_handler(LifeOSException)
async def lifeos_exception_handler(
    request: Request, exc: LifeOSException
) -> JSONResponse:
    """Handle generic LifeOSException with proper HTTP response."""
    logger.error(f"LifeOS error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "https://lifeos.akaion.dev/errors/internal-error",
            "title": "Internal Error",
            "status": 500,
            "detail": exc.message,
            "instance": str(request.url),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(
        f"Unexpected error: {str(exc)}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "https://lifeos.akaion.dev/errors/internal-error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred",
            "instance": str(request.url),
        },
    )


# Include API routers
app.include_router(api_router, prefix="/api/v1")


# Root endpoint
@app.get("/", response_model=Dict[str, Any])
async def root() -> Dict[str, Any]:
    """
    Root endpoint with service information.
    
    Returns:
        Service metadata
    """
    return {
        "service": __service_name__,
        "version": __version__,
        "description": "LifeOS Task Orchestration Service",
        "documentation": "/docs",
        "health": "/api/v1/health",
    }
