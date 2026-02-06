"""
Pydantic models for tasks.

Defines the data structures for task creation, retrieval, and management.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    CLASSIFIED = "classified"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskCreateRequest(BaseModel):
    """Request model for creating a new task."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Task title",
        json_schema_extra={"example": "Clean up inbox"},
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Detailed task description",
        json_schema_extra={"example": "Archive emails older than 30 days"},
    )
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        description="Task priority level",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata for the task",
        json_schema_extra={"example": {"category": "email_automation", "user_id": "user_123"}},
    )


class TaskClassification(BaseModel):
    """Task classification result from ClassifierAgent."""

    category: str = Field(..., description="Classified category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    suggested_workflow: str = Field(..., description="Suggested workflow to execute")


class TaskResponse(BaseModel):
    """Response model for task operations."""

    task_id: str = Field(..., description="Unique task identifier")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    priority: TaskPriority = Field(..., description="Task priority")
    status: TaskStatus = Field(..., description="Current task status")
    progress: int = Field(default=0, ge=0, le=100, description="Completion progress percentage")
    classification: Optional[TaskClassification] = Field(
        default=None, description="Classification result"
    )
    current_step: Optional[str] = Field(default=None, description="Current workflow step")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Task metadata")
    created_at: datetime = Field(..., description="Task creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    estimated_completion: Optional[datetime] = Field(
        default=None, description="Estimated completion time"
    )


class TaskListResponse(BaseModel):
    """Response model for listing tasks."""

    tasks: list[TaskResponse] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=20, description="Items per page")
