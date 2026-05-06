from functools import lru_cache

from pydantic import Field, model_validator
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
    jwt_secret_key: str = Field(default="dev-jwt-secret-change-me", alias="JWT_SECRET_KEY")
    jwt_access_expire_minutes: int = Field(default=24 * 60, alias="JWT_ACCESS_EXPIRE_MINUTES")
    jwt_refresh_expire_days: int = Field(default=30, alias="JWT_REFRESH_EXPIRE_DAYS")
    refresh_cookie_name: str = Field(default="refresh_token", alias="REFRESH_COOKIE_NAME")
    initial_free_minutes: int = Field(default=10, alias="INITIAL_FREE_MINUTES")

    @model_validator(mode="after")
    def _validate_jwt_secret(self) -> "Settings":
        _default = "dev-jwt-secret-change-me"
        if self.environment == "production":
            if self.jwt_secret_key == _default:
                raise ValueError("JWT_SECRET_KEY must be changed from the default in production")
            if len(self.jwt_secret_key) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production")
        return self

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
