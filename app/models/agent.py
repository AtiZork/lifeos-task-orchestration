"""
Pydantic models for agents.

Defines the data structures for agent interactions and results.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentResult(BaseModel):
    """Base result model for agent execution."""

    agent_name: str = Field(..., description="Name of the agent")
    success: bool = Field(..., description="Whether execution was successful")
    data: Dict[str, Any] = Field(default_factory=dict, description="Result data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")


class ClassificationResult(AgentResult):
    """Result from ClassifierAgent."""

    category: str = Field(..., description="Classified category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    suggested_workflow: str = Field(..., description="Suggested workflow name")
    reasoning: Optional[str] = Field(default=None, description="Classification reasoning")


class PlanningResult(AgentResult):
    """Result from PlannerAgent."""

    workflow_name: str = Field(..., description="Planned workflow name")
    steps: List[Dict[str, Any]] = Field(..., description="Planned workflow steps")
    estimated_duration_seconds: int = Field(..., description="Estimated execution time")
    dependencies: Dict[str, List[str]] = Field(
        default_factory=dict, description="Step dependencies"
    )


class ExecutionResult(AgentResult):
    """Result from ExecutorAgent."""

    execution_id: str = Field(..., description="Execution identifier")
    completed_steps: int = Field(..., description="Number of completed steps")
    total_steps: int = Field(..., description="Total number of steps")
    step_results: List[Dict[str, Any]] = Field(
        default_factory=list, description="Individual step results"
    )
    final_result: Optional[Dict[str, Any]] = Field(
        default=None, description="Final execution result"
    )
