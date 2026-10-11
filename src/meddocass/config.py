from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_ignore_empty=True)

    app_name: str = "MedDocAss"
    log_level: str = "INFO"

    chunk_size: int = 1000
    chunk_overlap: int = 150
    max_upload_mb: int = 20

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "meddocass_docs"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_cache_dir: str = ".cache/fastembed"

    top_k: int = 5
    min_score: float = 0.0

    llm_model: str = "anthropic:claude-haiku-5-5"
    llm_temperature: float | None = None
    llm_max_tokens: int = 4000
    llm_timeout_s: float = 120
    anthropic_api_key: SecretStr | None = None

@lru_cache
def get_settings() -> Settings:
    return Settings()
