"""
Workflow repository implementation.

Handles persistence for workflow execution entities.
"""

import asyncio
from typing import Any, Dict, List, Optional

from app.repositories.base import BaseRepository
from app.utils import get_logger
from app.utils.exceptions import WorkflowNotFoundException

logger = get_logger(__name__)


class WorkflowRepository(BaseRepository):
    """
    Repository for workflow execution persistence.
    
    In-memory implementation for demonstration.
    In production, replace with Firestore or Cloud SQL.
    """

    def __init__(self) -> None:
        """Initialize the repository with in-memory storage."""
        self._storage: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        logger.info("WorkflowRepository initialized with in-memory storage")

    async def create(self, entity_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new workflow execution.
        
        Args:
            entity_id: Execution ID
            data: Workflow execution data
            
        Returns:
            Created workflow data
        """
        async with self._lock:
            self._storage[entity_id] = data
            logger.info(f"Workflow execution created: {entity_id}")
            return data

    async def get(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a workflow execution by ID.
        
        Args:
            entity_id: Execution ID
            
        Returns:
            Workflow execution data if found, None otherwise
        """
        async with self._lock:
            return self._storage.get(entity_id)

    async def update(self, entity_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing workflow execution.
        
        Args:
            entity_id: Execution ID
            data: Updated workflow data
            
        Returns:
            Updated workflow data
            
        Raises:
            WorkflowNotFoundException: If workflow doesn't exist
        """
        async with self._lock:
            if entity_id not in self._storage:
                raise WorkflowNotFoundException(entity_id)

            # Merge updates with existing data
            self._storage[entity_id].update(data)
            logger.info(f"Workflow execution updated: {entity_id}")
            return self._storage[entity_id]

    async def delete(self, entity_id: str) -> bool:
        """
        Delete a workflow execution.
        
        Args:
            entity_id: Execution ID
            
        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            if entity_id in self._storage:
                del self._storage[entity_id]
                logger.info(f"Workflow execution deleted: {entity_id}")
                return True
            return False

    async def list(
        self, filters: Optional[Dict[str, Any]] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List workflow executions with optional filtering.
        
        Args:
            filters: Optional filters (e.g., {'status': 'running'})
            limit: Maximum number of results
            
        Returns:
            List of workflow executions
        """
        workflows = list(self._storage.values())

        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                workflows = [w for w in workflows if w.get(key) == value]

        # Apply limit
        return workflows[:limit]

    async def count(self) -> int:
        """
        Count total workflow executions.
        
        Returns:
            Total number of workflow executions
        """
        return len(self._storage)
