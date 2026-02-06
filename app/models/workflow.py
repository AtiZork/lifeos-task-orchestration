"""
Pydantic models for workflows.

Defines the data structures for workflow execution and management.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStepStatus(str, Enum):
    """Individual workflow step status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowExecuteRequest(BaseModel):
    """Request model for executing a workflow."""

    workflow_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the workflow to execute",
        json_schema_extra={"example": "inbox_cleanup_workflow"},
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Workflow parameters",
        json_schema_extra={"example": {"days_threshold": 30, "archive_folder": "Old Emails"}},
    )
    async_execution: bool = Field(
        default=True,
        description="Execute workflow asynchronously in background",
    )


class WorkflowStep(BaseModel):
    """Representation of a workflow step."""

    step_id: str = Field(..., description="Unique step identifier")
    name: str = Field(..., description="Step name")
    description: str = Field(..., description="Step description")
    status: WorkflowStepStatus = Field(default=WorkflowStepStatus.PENDING)
    order: int = Field(..., description="Execution order")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Step execution result")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)


class WorkflowExecutionResponse(BaseModel):
    """Response model for workflow execution."""

    execution_id: str = Field(..., description="Unique execution identifier")
    workflow_name: str = Field(..., description="Workflow name")
    status: WorkflowStatus = Field(..., description="Execution status")
    steps: List[WorkflowStep] = Field(default_factory=list, description="Workflow steps")
    current_step_index: int = Field(default=0, description="Current step index")
    progress: int = Field(default=0, ge=0, le=100, description="Execution progress percentage")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Final execution result")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    created_at: datetime = Field(..., description="Execution start time")
    updated_at: datetime = Field(..., description="Last update time")
    completed_at: Optional[datetime] = Field(default=None, description="Completion time")
    estimated_duration_seconds: Optional[int] = Field(
        default=None, description="Estimated duration in seconds"
    )


class WorkflowDefinition(BaseModel):
    """Workflow definition model."""

    name: str = Field(..., description="Workflow name")
    description: str = Field(..., description="Workflow description")
    steps: int = Field(..., description="Number of steps")
    avg_duration_seconds: int = Field(..., description="Average execution duration")
    category: str = Field(..., description="Workflow category")


class WorkflowListResponse(BaseModel):
    """Response model for listing available workflows."""

    workflows: List[WorkflowDefinition] = Field(..., description="Available workflows")
    total: int = Field(..., description="Total number of workflows")
