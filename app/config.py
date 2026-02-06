"""
Application configuration management using Pydantic Settings.
Loads configuration from environment variables with validation.
"""

from functools import lru_cache
from typing import Any, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with validation.
    
    All settings can be configured via environment variables.
    Follows 12-factor app principles for cloud-native deployments.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Metadata
    environment: str = Field(default="development", description="Environment name")
    service_name: str = Field(
        default="lifeos-task-orchestration", description="Service name"
    )
    service_version: str = Field(default="1.0.0", description="Service version")
    log_level: str = Field(default="INFO", description="Logging level")

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8080, description="Server port")

    # CORS Configuration
    allowed_origins: str | List[str] = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="Allowed CORS origins (comma-separated string or list)",
    )

    def get_allowed_origins_list(self) -> List[str]:
        """Get allowed_origins as a list."""
        if isinstance(self.allowed_origins, str):
            return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
        return self.allowed_origins

    # GCP Configuration
    gcp_project_id: str = Field(default="", description="GCP Project ID")
    use_firestore: bool = Field(default=False, description="Enable Firestore persistence")
    use_pubsub: bool = Field(default=False, description="Enable Pub/Sub for async tasks")
    pubsub_topic: str = Field(
        default="workflow-execution-tasks", description="Pub/Sub topic name"
    )

    # Agent Configuration
    agent_timeout_seconds: int = Field(
        default=30, description="Agent execution timeout in seconds"
    )
    max_workflow_steps: int = Field(
        default=10, description="Maximum steps in a workflow"
    )
    enable_background_tasks: bool = Field(
        default=True, description="Enable FastAPI background tasks"
    )

    # Feature Flags
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    enable_tracing: bool = Field(default=False, description="Enable distributed tracing")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Using lru_cache ensures we only load settings once across the application.
    This is more efficient than creating new Settings objects repeatedly.
    
    Returns:
        Settings: Cached settings instance
    """
    return Settings()
