"""
Task management endpoints.

Handles task creation, retrieval, and status updates.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_task_service
from app.models.task import (
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskStatus,
)
from app.services import TaskService
from app.utils import get_logger
from app.utils.exceptions import TaskNotFoundException, ValidationException

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Task",
    description="Create a new task with intelligent intent classification",
)
async def create_task(
    request: TaskCreateRequest,
    task_service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """
    Create a new task.
    
    The task will be automatically classified using the ClassifierAgent,
    which determines the appropriate workflow to execute.
    
    Args:
        request: Task creation request
        task_service: Injected task service
        
    Returns:
        Created task with classification results
        
    Raises:
        HTTPException: If validation fails or service error occurs
    """
    try:
        task = await task_service.create_task(request)
        logger.info(f"Task created via API: {task.task_id}")
        return task
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Validation failed", "message": str(e)},
        )
    except Exception as e:
        logger.error(f"Failed to create task: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": "Failed to create task"},
        )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get Task",
    description="Retrieve a task by its ID",
)
async def get_task(
    task_id: str,
    task_service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """
    Get task by ID.
    
    Args:
        task_id: Task identifier
        task_service: Injected task service
        
    Returns:
        Task details
        
    Raises:
        HTTPException: If task not found
    """
    try:
        task = await task_service.get_task(task_id)
        return task
    except TaskNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Task not found", "task_id": task_id},
        )
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": "Failed to retrieve task"},
        )


@router.get(
    "",
    response_model=TaskListResponse,
    summary="List Tasks",
    description="List tasks with optional filtering",
)
async def list_tasks(
    status_filter: Optional[TaskStatus] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    page: int = Query(1, ge=1, description="Page number"),
    task_service: TaskService = Depends(get_task_service),
) -> TaskListResponse:
    """
    List tasks with optional filtering.
    
    Args:
        status_filter: Optional status filter
        limit: Maximum number of results
        page: Page number for pagination
        task_service: Injected task service
        
    Returns:
        List of tasks
    """
    try:
        # Build filters
        filters = {}
        if status_filter:
            filters["status"] = status_filter

        # Get tasks
        tasks = await task_service.list_tasks(filters=filters, limit=limit)

        return TaskListResponse(
            tasks=tasks,
            total=len(tasks),
            page=page,
            page_size=limit,
        )
    except Exception as e:
        logger.error(f"Failed to list tasks: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": "Failed to list tasks"},
        )


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Task",
    description="Delete a task by its ID",
)
async def delete_task(
    task_id: str,
    task_service: TaskService = Depends(get_task_service),
) -> None:
    """
    Delete a task.
    
    Args:
        task_id: Task identifier
        task_service: Injected task service
        
    Raises:
        HTTPException: If task not found
    """
    try:
        deleted = await task_service.delete_task(task_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Task not found", "task_id": task_id},
            )
        logger.info(f"Task deleted via API: {task_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete task {task_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": "Failed to delete task"},
        )
