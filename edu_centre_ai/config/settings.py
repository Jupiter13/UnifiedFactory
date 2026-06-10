"""Settings and configuration for EDU_CENTRE AI.

Loads configuration from environment variables with sensible defaults.
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings."""

    # Application
    app_name: str = "EDU_CENTRE AI"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False)

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/ai"

    # External Services
    course_service_url: str = "http://course-service:8000"
    question_bank_url: str = "http://question-bank:8000"
    chat_service_url: str = "http://chat-service:8000"

    # Vector Store (Pinecone/Qdrant)
    vector_store_provider: str = "pinecone"  # pinecone or qdrant
    vector_store_url: Optional[str] = None
    vector_store_api_key: Optional[str] = None
    vector_index_name: str = "edu-centre-courses"

    # Database (PostgreSQL)
    database_url: str = "postgresql://user:password@localhost:5432/edu_centre"
    redis_url: str = "redis://localhost:6379/0"

    # LLM Configuration
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1000

    # LangSmith (Observability)
    langsmith_api_key: Optional[str] = None
    langsmith_project: str = "edu-centre-ai"
    langsmith_endpoint: str = "https://api.smith.langchain.com"

    # Observability
    enable_tracing: bool = True
    enable_metrics: bool = True
    metrics_port: int = 9090

    # Security
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"

    # Cache
    cache_ttl_seconds: int = 300  # 5 minutes

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings instance
    """
    return Settings()