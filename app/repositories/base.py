"""
Base repository interface.

Defines the contract for data access patterns across the application.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseRepository(ABC):
    """
    Abstract base class for all repositories.
    
    Repositories provide a clean abstraction for data persistence,
    allowing easy swapping between in-memory, Firestore, SQL, etc.
    """

    @abstractmethod
    async def create(self, entity_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new entity."""
        pass

    @abstractmethod
    async def get(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an entity by ID."""
        pass

    @abstractmethod
    async def update(self, entity_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing entity."""
        pass

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete an entity."""
        pass

    @abstractmethod
    async def list(
        self, filters: Optional[Dict[str, Any]] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List entities with optional filtering."""
        pass
