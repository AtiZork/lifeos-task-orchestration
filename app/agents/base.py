"""
Base agent interface and abstract class.

All agents inherit from this base to ensure consistent behavior.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from datetime import datetime

from app.utils import get_logger, utc_now

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    Agents are autonomous components that perform specific intelligence tasks:
    - Classification: Understanding user intent
    - Planning: Creating execution strategies
    - Execution: Performing actions
    """

    def __init__(self, name: str) -> None:
        """
        Initialize the agent.
        
        Args:
            name: Agent name for logging and identification
        """
        self.name = name
        self.logger = get_logger(f"agent.{name}")

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's primary function.
        
        This method must be implemented by all concrete agents.
        
        Args:
            input_data: Input data for the agent
            
        Returns:
            Execution result dictionary
            
        Raises:
            AgentExecutionException: If execution fails
        """
        pass

    async def _log_execution_start(self, input_data: Dict[str, Any]) -> datetime:
        """Log execution start and return start time."""
        self.logger.info(
            f"Agent '{self.name}' starting execution",
            extra={"input_data": input_data},
        )
        return utc_now()

    async def _log_execution_end(
        self, start_time: datetime, result: Dict[str, Any]
    ) -> None:
        """Log execution completion."""
        duration_ms = (utc_now() - start_time).total_seconds() * 1000
        self.logger.info(
            f"Agent '{self.name}' completed execution in {duration_ms:.2f}ms",
            extra={"result": result, "duration_ms": duration_ms},
        )

    async def _log_execution_error(self, error: Exception) -> None:
        """Log execution error."""
        self.logger.error(
            f"Agent '{self.name}' execution failed: {str(error)}",
            exc_info=True,
        )
