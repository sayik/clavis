from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Clavis"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False


    CORS_ORIGINS: list[str] = []
    CORS_ORIGINS_REGEX: str | None = None
    CORS_HEADERS: list[str] = [
        "Authorization",
        "Content-Type",
        "Accept",
    ]


    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()