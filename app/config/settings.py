from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Clavis"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "LT9z2SAASdVsh5B0fdX3LWkVo7XuF6F54o4fHeZA3f9U"

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    CORS_ORIGINS_REGEX: str | None = None
    CORS_HEADERS: list[str] = [
        "Authorization",
        "Content-Type",
        "Accept",
    ]

    openai_api_key: str | None = None

    openai_model: str = "gpt-5.6"
    openai_transcription_model: str = "gpt-4o-transcribe"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
