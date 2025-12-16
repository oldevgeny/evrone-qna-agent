"""Global application configuration using pydantic-settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "QnA Agent API"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/qna.db"

    # LiteLLM
    litellm_api_key: str = ""
    litellm_api_base: str = "https://openrouter.ai/api/v1"
    litellm_model: str = "openrouter/openai/gpt-4o-mini"

    # Langfuse
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # Knowledge Base
    knowledge_base_path: Path = Path("./knowledge")

    # Server
    host: str = "0.0.0.0"  # nosec B104 - intentional for containerized deployment
    port: int = 8000


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
