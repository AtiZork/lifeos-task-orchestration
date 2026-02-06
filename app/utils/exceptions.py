"""Custom exceptions for the LifeOS Task Orchestration Service."""


class LifeOSException(Exception):
    """Base exception for all LifeOS errors."""

    def __init__(self, message: str, error_code: str = "LIFEOS_ERROR") -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class TaskNotFoundException(LifeOSException):
    """Raised when a task is not found."""

    def __init__(self, task_id: str) -> None:
        super().__init__(
            message=f"Task not found: {task_id}",
            error_code="TASK_NOT_FOUND",
        )
        self.task_id = task_id


class WorkflowNotFoundException(LifeOSException):
    """Raised when a workflow is not found."""

    def __init__(self, workflow_name: str) -> None:
        super().__init__(
            message=f"Workflow not found: {workflow_name}",
            error_code="WORKFLOW_NOT_FOUND",
        )
        self.workflow_name = workflow_name


class AgentExecutionException(LifeOSException):
    """Raised when an agent fails to execute."""

    def __init__(self, agent_name: str, reason: str) -> None:
        super().__init__(
            message=f"Agent '{agent_name}' execution failed: {reason}",
            error_code="AGENT_EXECUTION_FAILED",
        )
        self.agent_name = agent_name
        self.reason = reason


class WorkflowExecutionException(LifeOSException):
    """Raised when a workflow execution fails."""

    def __init__(self, workflow_name: str, step: str, reason: str) -> None:
        super().__init__(
            message=f"Workflow '{workflow_name}' failed at step '{step}': {reason}",
            error_code="WORKFLOW_EXECUTION_FAILED",
        )
        self.workflow_name = workflow_name
        self.step = step
        self.reason = reason


class ValidationException(LifeOSException):
    """Raised when input validation fails."""

    def __init__(self, field: str, reason: str) -> None:
        super().__init__(
            message=f"Validation failed for '{field}': {reason}",
            error_code="VALIDATION_ERROR",
        )
        self.field = field
        self.reason = reason


class TimeoutException(LifeOSException):
    """Raised when an operation times out."""

    def __init__(self, operation: str, timeout_seconds: int) -> None:
        super().__init__(
            message=f"Operation '{operation}' timed out after {timeout_seconds} seconds",
            error_code="TIMEOUT_ERROR",
        )
        self.operation = operation
        self.timeout_seconds = timeout_seconds
