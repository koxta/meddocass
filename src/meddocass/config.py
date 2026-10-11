from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_ignore_empty=True)

    chunk_size: int = 1000
    chunk_overlap: int = 150
    max_upload_mb: int = 20

@lru_cache
def get_settings() -> Settings:
    return Settings()
