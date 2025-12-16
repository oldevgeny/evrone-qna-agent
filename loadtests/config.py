"""Load test configuration using pydantic-settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoadTestSettings(BaseSettings):
    """Load test configuration from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="LOADTEST_",
        env_file=".env.loadtest",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Target configuration
    host: str = Field(default="http://localhost:8000", description="Target host URL")

    # Mock LLM configuration
    mock_llm_enabled: bool = Field(
        default=True,
        description="Enable LLM response mocking",
    )
    mock_llm_delay_ms: int = Field(
        default=100,
        description="Simulated LLM response delay in milliseconds",
    )
    mock_llm_response: str = Field(
        default="This is a mocked AI response for load testing.",
        description="Default mock LLM response content",
    )

    # Test thresholds
    p95_response_time_ms: int = Field(
        default=500,
        description="95th percentile response time threshold",
    )
    p99_response_time_ms: int = Field(
        default=1000,
        description="99th percentile response time threshold",
    )
    max_error_rate_percent: float = Field(
        default=1.0,
        description="Maximum acceptable error rate percentage",
    )

    # Scenario defaults
    default_users: int = Field(default=10, description="Default concurrent users")
    default_spawn_rate: int = Field(default=2, description="Users spawned per second")
    default_run_time: str = Field(default="1m", description="Default test duration")


class SmokeTestConfig(BaseSettings):
    """Smoke test specific configuration."""

    model_config = SettingsConfigDict(env_prefix="SMOKE_")

    users: int = 1
    spawn_rate: int = 1
    run_time: str = "30s"


class LoadTestConfig(BaseSettings):
    """Load test specific configuration."""

    model_config = SettingsConfigDict(env_prefix="LOAD_")

    users: int = 50
    spawn_rate: int = 5
    run_time: str = "5m"


class StressTestConfig(BaseSettings):
    """Stress test specific configuration."""

    model_config = SettingsConfigDict(env_prefix="STRESS_")

    users: int = 200
    spawn_rate: int = 20
    run_time: str = "10m"


class SpikeTestConfig(BaseSettings):
    """Spike test specific configuration."""

    model_config = SettingsConfigDict(env_prefix="SPIKE_")

    initial_users: int = 10
    spike_users: int = 100
    spawn_rate: int = 50
    run_time: str = "5m"


@lru_cache
def get_loadtest_settings() -> LoadTestSettings:
    """Get cached load test settings."""
    return LoadTestSettings()
