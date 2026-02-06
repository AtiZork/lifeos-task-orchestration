"""
ClassifierAgent - Intent classification and categorization.

This agent analyzes user requests and classifies them into categories,
determining the appropriate workflow to execute.
"""

from datetime import datetime
from typing import Any, Dict

from app.agents.base import BaseAgent
from app.models.agent import ClassificationResult
from app.utils import get_logger, utc_now
from app.utils.exceptions import AgentExecutionException

logger = get_logger(__name__)


class ClassifierAgent(BaseAgent):
    """
    Agent responsible for classifying user intent and suggesting workflows.
    
    In a production system, this would use ML models or LLM APIs.
    For this demonstration, we use rule-based classification.
    """

    def __init__(self) -> None:
        super().__init__(name="classifier")
        
        # Classification rules (in production, replace with ML model)
        self.classification_rules = {
            "email": {
                "keywords": ["email", "inbox", "mail", "message", "send"],
                "category": "email_automation",
                "workflow": "inbox_cleanup_workflow",
            },
            "scheduling": {
                "keywords": ["schedule", "calendar", "meeting", "appointment"],
                "category": "scheduling",
                "workflow": "meeting_scheduler_workflow",
            },
            "data_processing": {
                "keywords": ["analyze", "process", "data", "report", "export"],
                "category": "data_processing",
                "workflow": "data_analysis_workflow",
            },
            "task_management": {
                "keywords": ["task", "todo", "assign", "complete", "prioritize"],
                "category": "task_management",
                "workflow": "task_prioritization_workflow",
            },
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify the user's intent and suggest a workflow.
        
        Args:
            input_data: Must contain 'title' and 'description'
            
        Returns:
            Classification result with category, confidence, and suggested workflow
            
        Raises:
            AgentExecutionException: If classification fails
        """
        start_time = await self._log_execution_start(input_data)

        try:
            # Extract text for classification
            title = input_data.get("title", "").lower()
            description = input_data.get("description", "").lower()
            combined_text = f"{title} {description}"

            # Perform classification
            classification = self._classify_text(combined_text)

            # Build result
            result = ClassificationResult(
                agent_name=self.name,
                success=True,
                category=classification["category"],
                confidence=classification["confidence"],
                suggested_workflow=classification["suggested_workflow"],
                reasoning=classification["reasoning"],
                execution_time_ms=(utc_now() - start_time).total_seconds() * 1000,
                data={
                    "input_length": len(combined_text),
                    "matched_keywords": classification["matched_keywords"],
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

    def _classify_text(self, text: str) -> Dict[str, Any]:
        """
        Classify text using rule-based matching.
        
        In production, replace with ML model or LLM API call.
        
        Args:
            text: Text to classify
            
        Returns:
            Classification result
        """
        best_match = None
        best_score = 0
        matched_keywords: list[str] = []

        # Score each category based on keyword matches
        for rule_name, rule in self.classification_rules.items():
            keywords = rule["keywords"]
            score = sum(1 for keyword in keywords if keyword in text)

            if score > best_score:
                best_score = score
                best_match = rule
                matched_keywords = [kw for kw in keywords if kw in text]

        # If no match found, use default
        if best_match is None:
            return {
                "category": "general",
                "confidence": 0.3,
                "suggested_workflow": "default_workflow",
                "reasoning": "No specific keywords matched; using default workflow",
                "matched_keywords": [],
            }

        # Calculate confidence based on keyword density
        confidence = min(0.95, 0.5 + (best_score * 0.15))

        return {
            "category": best_match["category"],
            "confidence": round(confidence, 2),
            "suggested_workflow": best_match["workflow"],
            "reasoning": f"Matched {best_score} keywords related to {best_match['category']}",
            "matched_keywords": matched_keywords,
        }
