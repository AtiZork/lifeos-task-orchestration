"""
Task service implementation.

Business logic for task management operations.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.agents import ClassifierAgent
from app.models.task import TaskClassification, TaskCreateRequest, TaskResponse, TaskStatus
from app.repositories import TaskRepository
from app.utils import generate_id, get_logger, utc_now
from app.utils.exceptions import TaskNotFoundException

logger = get_logger(__name__)


class TaskService:
    """
    Service layer for task operations.
    
    Coordinates between agents, repositories, and business logic.
    """

    def __init__(
        self,
        task_repository: TaskRepository,
        classifier_agent: ClassifierAgent,
    ) -> None:
        """
        Initialize the task service.
        
        Args:
            task_repository: Repository for task persistence
            classifier_agent: Agent for intent classification
        """
        self.task_repository = task_repository
        self.classifier_agent = classifier_agent
        self.logger = get_logger(__name__)

    async def create_task(self, request: TaskCreateRequest) -> TaskResponse:
        """
        Create a new task.
        
        Flow:
        1. Generate unique task ID
        2. Classify intent using ClassifierAgent
        3. Store task with classification
        4. Return task response
        
        Args:
            request: Task creation request
            
        Returns:
            Created task response
        """
        self.logger.info(f"Creating task: {request.title}")

        # Generate task ID
        task_id = generate_id("task")
        now = utc_now()

        # Classify the task using ClassifierAgent
        classification_result = await self.classifier_agent.execute({
            "title": request.title,
            "description": request.description,
        })

        # Build task classification
        task_classification = TaskClassification(
            category=classification_result["category"],
            confidence=classification_result["confidence"],
            suggested_workflow=classification_result["suggested_workflow"],
        )

        # Estimate completion time (simple heuristic)
        estimated_completion = now + timedelta(minutes=5)

        # Build task data
        task_data = {
            "task_id": task_id,
            "title": request.title,
            "description": request.description,
            "priority": request.priority,
            "status": TaskStatus.CLASSIFIED,
            "progress": 0,
            "classification": task_classification.model_dump(),
            "current_step": None,
            "metadata": request.metadata or {},
            "created_at": now,
            "updated_at": now,
            "estimated_completion": estimated_completion,
        }

        # Store task
        await self.task_repository.create(task_id, task_data)

        self.logger.info(
            f"Task created successfully: {task_id}",
            extra={"task_id": task_id, "category": classification_result["category"]},
        )

        # Return task response
        return TaskResponse(**task_data)

    async def get_task(self, task_id: str) -> TaskResponse:
        """
        Retrieve a task by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task response
            
        Raises:
            TaskNotFoundException: If task doesn't exist
        """
        task_data = await self.task_repository.get(task_id)

        if not task_data:
            raise TaskNotFoundException(task_id)

        return TaskResponse(**task_data)

    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        progress: Optional[int] = None,
        current_step: Optional[str] = None,
    ) -> TaskResponse:
        """
        Update task execution status.
        
        Args:
            task_id: Task identifier
            status: New status
            progress: Optional progress percentage
            current_step: Optional current workflow step
            
        Returns:
            Updated task response
            
        Raises:
            TaskNotFoundException: If task doesn't exist
        """
        # Check if task exists
        existing_task = await self.task_repository.get(task_id)
        if not existing_task:
            raise TaskNotFoundException(task_id)

        # Build update data
        update_data = {
            "status": status,
            "updated_at": utc_now(),
        }

        if progress is not None:
            update_data["progress"] = progress

        if current_step is not None:
            update_data["current_step"] = current_step

        # Update task
        updated_task = await self.task_repository.update(task_id, update_data)

        self.logger.info(
            f"Task status updated: {task_id} -> {status}",
            extra={"task_id": task_id, "status": status},
        )

        return TaskResponse(**updated_task)

    async def list_tasks(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
    ) -> List[TaskResponse]:
        """
        List tasks with optional filtering.
        
        Args:
            filters: Optional filters
            limit: Maximum results
            
        Returns:
            List of tasks
        """
        task_data_list = await self.task_repository.list(filters=filters, limit=limit)
        return [TaskResponse(**task_data) for task_data in task_data_list]

    async def delete_task(self, task_id: str) -> bool:
        """
        Delete a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if deleted, False if not found
        """
        deleted = await self.task_repository.delete(task_id)

        if deleted:
            self.logger.info(f"Task deleted: {task_id}")
        else:
            self.logger.warning(f"Task not found for deletion: {task_id}")

        return deleted
