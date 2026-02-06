"""
Workflow service implementation.

Business logic for workflow execution and orchestration.
"""

from typing import Any, Dict, List

from app.agents import ExecutorAgent, PlannerAgent
from app.models.workflow import (
    WorkflowDefinition,
    WorkflowExecuteRequest,
    WorkflowExecutionResponse,
    WorkflowStatus,
    WorkflowStep,
    WorkflowStepStatus,
)
from app.repositories import WorkflowRepository
from app.utils import generate_id, get_logger, utc_now
from app.utils.exceptions import WorkflowNotFoundException

logger = get_logger(__name__)


class WorkflowService:
    """
    Service layer for workflow operations.
    
    Coordinates workflow planning and execution through agents.
    """

    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        planner_agent: PlannerAgent,
        executor_agent: ExecutorAgent,
    ) -> None:
        """
        Initialize the workflow service.
        
        Args:
            workflow_repository: Repository for workflow persistence
            planner_agent: Agent for workflow planning
            executor_agent: Agent for workflow execution
        """
        self.workflow_repository = workflow_repository
        self.planner_agent = planner_agent
        self.executor_agent = executor_agent
        self.logger = get_logger(__name__)

    async def execute_workflow(
        self, request: WorkflowExecuteRequest
    ) -> WorkflowExecutionResponse:
        """
        Execute a workflow.
        
        Flow:
        1. Generate execution ID
        2. Use PlannerAgent to create execution plan
        3. Use ExecutorAgent to execute steps
        4. Store and return execution results
        
        Args:
            request: Workflow execution request
            
        Returns:
            Workflow execution response
        """
        self.logger.info(f"Executing workflow: {request.workflow_name}")

        # Generate execution ID
        execution_id = generate_id("exec")
        now = utc_now()

        # Plan the workflow using PlannerAgent
        planning_result = await self.planner_agent.execute({
            "workflow_name": request.workflow_name,
            "parameters": request.parameters,
        })

        # Convert planned steps to workflow steps
        workflow_steps = [
            WorkflowStep(
                step_id=step["step_id"],
                name=step["name"],
                description=step["description"],
                order=step["order"],
                status=WorkflowStepStatus.PENDING,
            )
            for step in planning_result["steps"]
        ]

        # Create initial execution record
        execution_data = {
            "execution_id": execution_id,
            "workflow_name": request.workflow_name,
            "status": WorkflowStatus.QUEUED,
            "steps": [step.model_dump() for step in workflow_steps],
            "current_step_index": 0,
            "progress": 0,
            "result": None,
            "error": None,
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
            "estimated_duration_seconds": planning_result["estimated_duration_seconds"],
        }

        # Store execution
        await self.workflow_repository.create(execution_id, execution_data)

        # If async execution, return immediately
        if request.async_execution:
            self.logger.info(f"Workflow queued for async execution: {execution_id}")
            return WorkflowExecutionResponse(**execution_data)

        # Otherwise, execute synchronously
        execution_result = await self._execute_workflow_sync(
            execution_id, planning_result["steps"]
        )

        return execution_result

    async def _execute_workflow_sync(
        self, execution_id: str, planned_steps: List[Dict[str, Any]]
    ) -> WorkflowExecutionResponse:
        """
        Execute workflow synchronously.
        
        Args:
            execution_id: Execution identifier
            planned_steps: Planned workflow steps
            
        Returns:
            Workflow execution response
        """
        # Update status to running
        await self.workflow_repository.update(
            execution_id,
            {
                "status": WorkflowStatus.RUNNING,
                "updated_at": utc_now(),
            },
        )

        # Execute using ExecutorAgent
        execution_result = await self.executor_agent.execute({
            "execution_id": execution_id,
            "steps": planned_steps,
        })

        # Determine final status
        final_status = (
            WorkflowStatus.COMPLETED if execution_result["success"] else WorkflowStatus.FAILED
        )

        # Calculate progress
        completed_steps = execution_result["completed_steps"]
        total_steps = execution_result["total_steps"]
        progress = int((completed_steps / total_steps) * 100) if total_steps > 0 else 0

        # Update execution record
        now = utc_now()
        updated_data = await self.workflow_repository.update(
            execution_id,
            {
                "status": final_status,
                "progress": progress,
                "result": execution_result.get("final_result"),
                "error": execution_result.get("error"),
                "updated_at": now,
                "completed_at": now,
            },
        )

        self.logger.info(
            f"Workflow execution completed: {execution_id} ({final_status})",
            extra={"execution_id": execution_id, "status": final_status},
        )

        return WorkflowExecutionResponse(**updated_data)

    async def get_execution(self, execution_id: str) -> WorkflowExecutionResponse:
        """
        Get workflow execution status.
        
        Args:
            execution_id: Execution identifier
            
        Returns:
            Workflow execution response
            
        Raises:
            WorkflowNotFoundException: If execution not found
        """
        execution_data = await self.workflow_repository.get(execution_id)

        if not execution_data:
            raise WorkflowNotFoundException(execution_id)

        return WorkflowExecutionResponse(**execution_data)

    async def list_available_workflows(self) -> List[WorkflowDefinition]:
        """
        List available workflow definitions.
        
        In production, this would load from a database or configuration.
        
        Returns:
            List of workflow definitions
        """
        # Hardcoded for demonstration
        workflows = [
            WorkflowDefinition(
                name="inbox_cleanup_workflow",
                description="Automate email archival based on age",
                steps=5,
                avg_duration_seconds=120,
                category="email_automation",
            ),
            WorkflowDefinition(
                name="task_prioritization_workflow",
                description="Intelligently prioritize tasks based on context",
                steps=3,
                avg_duration_seconds=30,
                category="task_management",
            ),
            WorkflowDefinition(
                name="meeting_scheduler_workflow",
                description="Schedule meetings based on availability",
                steps=4,
                avg_duration_seconds=60,
                category="scheduling",
            ),
            WorkflowDefinition(
                name="data_analysis_workflow",
                description="Process and analyze data with AI insights",
                steps=6,
                avg_duration_seconds=180,
                category="data_processing",
            ),
        ]

        return workflows
