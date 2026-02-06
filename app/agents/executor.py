"""
ExecutorAgent - Workflow step execution.

This agent executes planned workflow steps and manages execution state.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.models.agent import ExecutionResult
from app.utils import get_logger
from app.utils.exceptions import AgentExecutionException, TimeoutException

logger = get_logger(__name__)


class ExecutorAgent(BaseAgent):
    """
    Agent responsible for executing workflow steps.
    
    Manages step execution, tracks progress, and handles failures.
    In production, this could integrate with external services and APIs.
    """

    def __init__(self, timeout_seconds: int = 30) -> None:
        super().__init__(name="executor")
        self.timeout_seconds = timeout_seconds

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute all steps in a workflow plan.
        
        Args:
            input_data: Must contain 'execution_id' and 'steps'
            
        Returns:
            Execution result with step results and final output
            
        Raises:
            AgentExecutionException: If execution fails
            TimeoutException: If execution exceeds timeout
        """
        start_time = await self._log_execution_start(input_data)

        try:
            execution_id = input_data.get("execution_id")
            steps = input_data.get("steps", [])

            # Execute all steps
            step_results = await self._execute_steps(steps)

            # Determine overall success
            success = all(result["success"] for result in step_results)
            completed_steps = sum(1 for result in step_results if result["success"])

            # Build final result
            final_result = {
                "execution_id": execution_id,
                "total_steps": len(steps),
                "completed_steps": completed_steps,
                "success": success,
                "summary": self._generate_summary(step_results),
            }

            # Build result model
            result = ExecutionResult(
                agent_name=self.name,
                success=success,
                execution_id=execution_id,
                completed_steps=completed_steps,
                total_steps=len(steps),
                step_results=step_results,
                final_result=final_result,
                execution_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
                data={
                    "success_rate": completed_steps / len(steps) if steps else 0,
                },
            )

            await self._log_execution_end(start_time, result.model_dump())
            return result.model_dump()

        except asyncio.TimeoutError:
            await self._log_execution_error(TimeoutException("workflow_execution", self.timeout_seconds))
            raise TimeoutException("workflow_execution", self.timeout_seconds)
        except Exception as e:
            await self._log_execution_error(e)
            raise AgentExecutionException(
                agent_name=self.name,
                reason=str(e),
            )

    async def _execute_steps(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute workflow steps in order.
        
        Args:
            steps: List of steps to execute
            
        Returns:
            List of step results
        """
        step_results = []

        for step in steps:
            self.logger.info(f"Executing step: {step['name']}")
            
            try:
                # Simulate step execution
                result = await self._execute_single_step(step)
                step_results.append(result)
                
                # If step failed, stop execution
                if not result["success"]:
                    self.logger.warning(f"Step {step['name']} failed, stopping workflow")
                    break
                    
            except Exception as e:
                self.logger.error(f"Step {step['name']} raised exception: {str(e)}")
                step_results.append({
                    "step_id": step["step_id"],
                    "step_name": step["name"],
                    "success": False,
                    "error": str(e),
                    "result": None,
                })
                break

        return step_results

    async def _execute_single_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single workflow step.
        
        In production, this would:
        - Call external APIs
        - Interact with databases
        - Perform complex computations
        - Integrate with cloud services
        
        For this demonstration, we simulate execution with delays.
        
        Args:
            step: Step definition
            
        Returns:
            Step execution result
        """
        step_id = step["step_id"]
        step_name = step["name"]
        estimated_seconds = step.get("estimated_seconds", 1)

        # Simulate work with a delay (cap at 2 seconds for demo)
        await asyncio.sleep(min(estimated_seconds / 10, 2))

        # Simulate step execution result
        result = {
            "step_id": step_id,
            "step_name": step_name,
            "success": True,
            "result": {
                "message": f"Step '{step_name}' completed successfully",
                "data": {
                    "step_description": step.get("description", ""),
                    "parameters": step.get("parameters", {}),
                },
            },
            "error": None,
        }

        self.logger.info(f"Step {step_name} completed successfully")
        return result

    def _generate_summary(self, step_results: List[Dict[str, Any]]) -> str:
        """
        Generate a human-readable summary of execution results.
        
        Args:
            step_results: List of step execution results
            
        Returns:
            Summary string
        """
        total = len(step_results)
        successful = sum(1 for r in step_results if r["success"])
        failed = total - successful

        if failed == 0:
            return f"All {total} steps completed successfully"
        elif successful == 0:
            return f"All {total} steps failed"
        else:
            return f"{successful} of {total} steps completed ({failed} failed)"
