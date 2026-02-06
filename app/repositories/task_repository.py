"""
Task repository implementation.

Handles persistence for task entities. Uses in-memory storage by default,
with easy migration path to Firestore or Cloud SQL.
"""

import asyncio
from typing import Any, Dict, List, Optional

from app.repositories.base import BaseRepository
from app.utils import get_logger
from app.utils.exceptions import TaskNotFoundException

logger = get_logger(__name__)


class TaskRepository(BaseRepository):
    """
    Repository for task persistence.
    
    In-memory implementation for demonstration.
    In production, replace with Firestore or Cloud SQL.
    """

    def __init__(self) -> None:
        """Initialize the repository with in-memory storage."""
        self._storage: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        logger.info("TaskRepository initialized with in-memory storage")

    async def create(self, entity_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new task.
        
        Args:
            entity_id: Task ID
            data: Task data
            
        Returns:
            Created task data
        """
        async with self._lock:
            self._storage[entity_id] = data
            logger.info(f"Task created: {entity_id}")
            return data

    async def get(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a task by ID.
        
        Args:
            entity_id: Task ID
            
        Returns:
            Task data if found, None otherwise
        """
        async with self._lock:
            return self._storage.get(entity_id)

    async def update(self, entity_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing task.
        
        Args:
            entity_id: Task ID
            data: Updated task data
            
        Returns:
            Updated task data
            
        Raises:
            TaskNotFoundException: If task doesn't exist
        """
        async with self._lock:
            if entity_id not in self._storage:
                raise TaskNotFoundException(entity_id)

            # Merge updates with existing data
            self._storage[entity_id].update(data)
            logger.info(f"Task updated: {entity_id}")
            return self._storage[entity_id]

    async def delete(self, entity_id: str) -> bool:
        """
        Delete a task.
        
        Args:
            entity_id: Task ID
            
        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            if entity_id in self._storage:
                del self._storage[entity_id]
                logger.info(f"Task deleted: {entity_id}")
                return True
            return False

    async def list(
        self, filters: Optional[Dict[str, Any]] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List tasks with optional filtering.
        
        Args:
            filters: Optional filters (e.g., {'status': 'pending'})
            limit: Maximum number of results
            
        Returns:
            List of tasks
        """
        tasks = list(self._storage.values())

        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                tasks = [t for t in tasks if t.get(key) == value]

        # Apply limit
        return tasks[:limit]

    async def count(self) -> int:
        """
        Count total tasks.
        
        Returns:
            Total number of tasks
        """
        return len(self._storage)
