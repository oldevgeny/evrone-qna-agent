"""Knowledge base configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class KnowledgeSettings(BaseSettings):
    """Knowledge base settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    knowledge_base_path: Path = Path("./knowledge")


@lru_cache
def get_knowledge_settings() -> KnowledgeSettings:
    """Get cached knowledge settings instance."""
    return KnowledgeSettings()
