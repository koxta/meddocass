from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_ignore_empty=True)

    chunk_size: int = 1000
    chunk_overlap: int = 150
    max_upload_mb: int = 20

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "meddocass_docs"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_cache_dir: str = ".cache/fastembed"

    top_k: int = 5
    min_score: float = 0.0

@lru_cache
def get_settings() -> Settings:
    return Settings()
