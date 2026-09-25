from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "GDG AI Grader"
    database_url: str = "sqlite:///./grader.db"
    secret_key: str = "change-this-development-secret"
    access_token_expire_minutes: int = 60
    grader_mode: str = "mock"
    seed_admin_email: str | None = None
    seed_admin_password: str | None = None
    ollama_url: str = "http://ollama:11434"
    ollama_chat_model: str = "llama3.2:3b"
    ollama_embedding_model: str = "nomic-embed-text"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

