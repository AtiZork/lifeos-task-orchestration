"""
Workflow execution endpoints.

Handles workflow execution and status retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_workflow_service
from app.models.workflow import (
    WorkflowDefinition,
    WorkflowExecuteRequest,
    WorkflowExecutionResponse,
    WorkflowListResponse,
)
from app.services import WorkflowService
from app.utils import get_logger
from app.utils.exceptions import WorkflowNotFoundException

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/execute",
    response_model=WorkflowExecutionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Execute Workflow",
    description="Execute a workflow with specified parameters",
)
async def execute_workflow(
    request: WorkflowExecuteRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowExecutionResponse:
    """
    Execute a workflow.
    
    The workflow will be planned using PlannerAgent and executed using ExecutorAgent.
    Supports both synchronous and asynchronous execution modes.
    
    Args:
        request: Workflow execution request
        workflow_service: Injected workflow service
        
    Returns:
        Workflow execution response
        
    Raises:
        HTTPException: If workflow execution fails
    """
    try:
        execution = await workflow_service.execute_workflow(request)
        logger.info(
            f"Workflow execution started: {execution.execution_id}",
            extra={
                "execution_id": execution.execution_id,
                "workflow_name": request.workflow_name,
                "async": request.async_execution,
            },
        )
        return execution
    except Exception as e:
        logger.error(
            f"Failed to execute workflow {request.workflow_name}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Workflow execution failed",
                "message": str(e),
                "workflow_name": request.workflow_name,
            },
        )


@router.get(
    "/executions/{execution_id}",
    response_model=WorkflowExecutionResponse,
    summary="Get Workflow Execution",
    description="Retrieve workflow execution status and results",
)
async def get_workflow_execution(
    execution_id: str,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowExecutionResponse:
    """
    Get workflow execution status.
    
    Args:
        execution_id: Execution identifier
        workflow_service: Injected workflow service
        
    Returns:
        Workflow execution details
        
    Raises:
        HTTPException: If execution not found
    """
    try:
        execution = await workflow_service.get_execution(execution_id)
        return execution
    except WorkflowNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Workflow execution not found",
                "execution_id": execution_id,
            },
        )
    except Exception as e:
        logger.error(
            f"Failed to get workflow execution {execution_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "Failed to retrieve workflow execution",
            },
        )


@router.get(
    "",
    response_model=WorkflowListResponse,
    summary="List Workflows",
    description="List available workflow definitions",
)
async def list_workflows(
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowListResponse:
    """
    List available workflows.
    
    Returns all workflow definitions that can be executed.
    
    Args:
        workflow_service: Injected workflow service
        
    Returns:
        List of available workflows
    """
    try:
        workflows = await workflow_service.list_available_workflows()
        return WorkflowListResponse(
            workflows=workflows,
            total=len(workflows),
        )
    except Exception as e:
        logger.error(f"Failed to list workflows: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "Failed to list workflows",
            },
        )
