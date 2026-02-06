"""API dependencies and dependency injection."""

from functools import lru_cache

from app.agents import ClassifierAgent, ExecutorAgent, PlannerAgent
from app.config import get_settings
from app.repositories import TaskRepository, WorkflowRepository
from app.services import TaskService, WorkflowService

# Singletons for agents and repositories
_task_repository: TaskRepository | None = None
_workflow_repository: WorkflowRepository | None = None
_classifier_agent: ClassifierAgent | None = None
_planner_agent: PlannerAgent | None = None
_executor_agent: ExecutorAgent | None = None
_task_service: TaskService | None = None
_workflow_service: WorkflowService | None = None


def get_task_repository() -> TaskRepository:
    """Get or create TaskRepository singleton."""
    global _task_repository
    if _task_repository is None:
        _task_repository = TaskRepository()
    return _task_repository


def get_workflow_repository() -> WorkflowRepository:
    """Get or create WorkflowRepository singleton."""
    global _workflow_repository
    if _workflow_repository is None:
        _workflow_repository = WorkflowRepository()
    return _workflow_repository


def get_classifier_agent() -> ClassifierAgent:
    """Get or create ClassifierAgent singleton."""
    global _classifier_agent
    if _classifier_agent is None:
        _classifier_agent = ClassifierAgent()
    return _classifier_agent


def get_planner_agent() -> PlannerAgent:
    """Get or create PlannerAgent singleton."""
    global _planner_agent
    if _planner_agent is None:
        _planner_agent = PlannerAgent()
    return _planner_agent


def get_executor_agent() -> ExecutorAgent:
    """Get or create ExecutorAgent singleton."""
    global _executor_agent
    if _executor_agent is None:
        settings = get_settings()
        _executor_agent = ExecutorAgent(timeout_seconds=settings.agent_timeout_seconds)
    return _executor_agent


def get_task_service() -> TaskService:
    """Get or create TaskService singleton."""
    global _task_service
    if _task_service is None:
        _task_service = TaskService(
            task_repository=get_task_repository(),
            classifier_agent=get_classifier_agent(),
        )
    return _task_service


def get_workflow_service() -> WorkflowService:
    """Get or create WorkflowService singleton."""
    global _workflow_service
    if _workflow_service is None:
        _workflow_service = WorkflowService(
            workflow_repository=get_workflow_repository(),
            planner_agent=get_planner_agent(),
            executor_agent=get_executor_agent(),
        )
    return _workflow_service
