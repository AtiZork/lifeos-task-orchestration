"""Utility helper functions for the application."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique identifier with optional prefix.
    
    Args:
        prefix: Optional prefix for the ID (e.g., 'task', 'workflow')
        
    Returns:
        Unique identifier string
        
    Examples:
        >>> generate_id("task")
        'task_a1b2c3d4...'
        >>> generate_id()
        'a1b2c3d4...'
    """
    unique_id = uuid.uuid4().hex[:12]
    return f"{prefix}_{unique_id}" if prefix else unique_id


def generate_correlation_id() -> str:
    """
    Generate a correlation ID for request tracing.
    
    Returns:
        Correlation ID string
    """
    return f"corr_{uuid.uuid4().hex[:16]}"


def utc_now() -> datetime:
    """
    Get current UTC timestamp.
    
    Returns:
        Current UTC datetime
    """
    return datetime.now(timezone.utc)


def to_dict(obj: Any) -> Dict[str, Any]:
    """
    Convert a Pydantic model or object to dictionary.
    
    Args:
        obj: Object to convert
        
    Returns:
        Dictionary representation
    """
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    elif hasattr(obj, "dict"):
        return obj.dict()
    return dict(obj)


def sanitize_string(value: str, max_length: int = 500) -> str:
    """
    Sanitize a string by trimming and removing potentially harmful characters.
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    # Trim whitespace
    sanitized = value.strip()
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized
