"""Agent-specific configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    """Agent-specific settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LiteLLM
    litellm_api_key: str = ""
    litellm_api_base: str = "https://openrouter.ai/api/v1"
    litellm_model: str = "openrouter/openai/gpt-4o-mini"

    # Langfuse
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # Agent settings
    max_tool_iterations: int = 10
    temperature: float = 0.7
    max_tokens: int = 4096


@lru_cache
def get_agent_settings() -> AgentSettings:
    """Get cached agent settings instance."""
    return AgentSettings()
