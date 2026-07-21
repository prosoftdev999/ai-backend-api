from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Backend API"
    app_version: str = "1.0.0"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    database_url: str
    redis_url: str
    celery_broker_url: str
    celery_result_backend: str

    llm_api_key: str
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str
    embedding_model: str

    upload_directory: Path = Path("uploads")
    max_upload_size_mb: int = Field(default=20, ge=1, le=100)
    chunk_size: int = Field(default=1000, ge=100)
    chunk_overlap: int = Field(default=200, ge=0)
    vector_search_limit: int = Field(default=5, ge=1, le=50)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()