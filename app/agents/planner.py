"""
PlannerAgent - Workflow planning and step generation.

This agent takes a workflow name and parameters, then generates
a detailed execution plan with ordered steps.
"""

from datetime import datetime
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.models.agent import PlanningResult
from app.utils import generate_id, get_logger, utc_now
from app.utils.exceptions import AgentExecutionException

logger = get_logger(__name__)


class PlannerAgent(BaseAgent):
    """
    Agent responsible for planning workflow execution.
    
    Generates step-by-step execution plans based on workflow templates.
    In production, this could use AI to optimize execution paths.
    """

    def __init__(self) -> None:
        super().__init__(name="planner")
        
        # Workflow templates (in production, load from database)
        self.workflow_templates = {
            "inbox_cleanup_workflow": {
                "description": "Automate email archival based on age",
                "steps": [
                    {
                        "name": "connect_email",
                        "description": "Connect to email service",
                        "estimated_seconds": 10,
                    },
                    {
                        "name": "fetch_emails",
                        "description": "Fetch emails matching criteria",
                        "estimated_seconds": 30,
                    },
                    {
                        "name": "filter_emails",
                        "description": "Filter emails by age threshold",
                        "estimated_seconds": 15,
                    },
                    {
                        "name": "archive_emails",
                        "description": "Move emails to archive folder",
                        "estimated_seconds": 45,
                    },
                    {
                        "name": "send_summary",
                        "description": "Send summary report",
                        "estimated_seconds": 10,
                    },
                ],
                "dependencies": {
                    "fetch_emails": ["connect_email"],
                    "filter_emails": ["fetch_emails"],
                    "archive_emails": ["filter_emails"],
                    "send_summary": ["archive_emails"],
                },
            },
            "task_prioritization_workflow": {
                "description": "Intelligently prioritize tasks based on context",
                "steps": [
                    {
                        "name": "fetch_tasks",
                        "description": "Fetch all pending tasks",
                        "estimated_seconds": 10,
                    },
                    {
                        "name": "analyze_context",
                        "description": "Analyze task context and deadlines",
                        "estimated_seconds": 20,
                    },
                    {
                        "name": "assign_priorities",
                        "description": "Assign priority scores",
                        "estimated_seconds": 15,
                    },
                ],
                "dependencies": {
                    "analyze_context": ["fetch_tasks"],
                    "assign_priorities": ["analyze_context"],
                },
            },
            "default_workflow": {
                "description": "Default workflow for general tasks",
                "steps": [
                    {
                        "name": "validate_input",
                        "description": "Validate input parameters",
                        "estimated_seconds": 5,
                    },
                    {
                        "name": "execute_task",
                        "description": "Execute the task",
                        "estimated_seconds": 30,
                    },
                    {
                        "name": "return_result",
                        "description": "Return execution result",
                        "estimated_seconds": 5,
                    },
                ],
                "dependencies": {
                    "execute_task": ["validate_input"],
                    "return_result": ["execute_task"],
                },
            },
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an execution plan for the specified workflow.
        
        Args:
            input_data: Must contain 'workflow_name' and optional 'parameters'
            
        Returns:
            Planning result with steps, dependencies, and estimated duration
            
        Raises:
            AgentExecutionException: If planning fails
        """
        start_time = await self._log_execution_start(input_data)

        try:
            workflow_name = input_data.get("workflow_name")
            parameters = input_data.get("parameters", {})

            # Get workflow template
            template = self.workflow_templates.get(workflow_name)
            if not template:
                # Use default workflow
                template = self.workflow_templates["default_workflow"]
                workflow_name = "default_workflow"

            # Generate execution plan
            plan = self._generate_plan(workflow_name, template, parameters)

            # Build result
            result = PlanningResult(
                agent_name=self.name,
                success=True,
                workflow_name=workflow_name,
                steps=plan["steps"],
                estimated_duration_seconds=plan["estimated_duration_seconds"],
                dependencies=template["dependencies"],
                execution_time_ms=(utc_now() - start_time).total_seconds() * 1000,
                data={
                    "total_steps": len(plan["steps"]),
                    "workflow_description": template["description"],
                },
            )

            await self._log_execution_end(start_time, result.model_dump())
            return result.model_dump()

        except Exception as e:
            await self._log_execution_error(e)
            raise AgentExecutionException(
                agent_name=self.name,
                reason=str(e),
            )

    def _generate_plan(
        self, workflow_name: str, template: Dict[str, Any], parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a concrete execution plan from a template.
        
        Args:
            workflow_name: Name of the workflow
            template: Workflow template
            parameters: Workflow parameters
            
        Returns:
            Execution plan with steps and estimated duration
        """
        steps: List[Dict[str, Any]] = []
        total_duration = 0

        for idx, step_template in enumerate(template["steps"]):
            step = {
                "step_id": generate_id("step"),
                "name": step_template["name"],
                "description": step_template["description"],
                "order": idx,
                "parameters": parameters,
                "estimated_seconds": step_template["estimated_seconds"],
            }
            steps.append(step)
            total_duration += step_template["estimated_seconds"]

        return {
            "steps": steps,
            "estimated_duration_seconds": total_duration,
        }
