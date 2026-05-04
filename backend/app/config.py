"""Application settings — loaded from .env via pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: str = "development"
    app_port: int = 8000
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 1440

    # Database
    database_url: str = "postgresql+asyncpg://ezidatic:ezidatic@localhost:5432/ezidatic"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Storage
    storage_backend: str = "local"
    local_storage_dir: str = "./data/uploads"
    max_file_size_mb: int = 50

    # LLM
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    groq_router_model: str = "llama-3.1-8b-instant"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash-lite"
    gemini_embed_model: str = "gemini-embedding-001"

    openrouter_api_key: str | None = None
    openrouter_model: str = "z-ai/glm-4.5-air:free"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"

    # Vector
    vector_backend: str = "chroma"
    chroma_persist_dir: str = "./data/chroma"

    # CORS
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
