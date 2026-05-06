from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(
        default="postgresql+psycopg2://voicepro:voicepro@localhost:5432/voicepro",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:5173", alias="CORS_ORIGINS")
    sentry_dsn: str | None = Field(default=None, alias="SENTRY_DSN")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    @property
    def cors_origins_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if not origins:
            raise ValueError(
                "CORS_ORIGINS is empty. Set at least one allowed origin (e.g. http://localhost:5173)."
            )
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
