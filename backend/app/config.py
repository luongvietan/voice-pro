import logging
from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


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

    stripe_api_key: str | None = Field(default=None, alias="STRIPE_API_KEY")
    stripe_webhook_secret: str | None = Field(default=None, alias="STRIPE_WEBHOOK_SECRET")
    stripe_paid_price_ids: str = Field(
        default="",
        alias="STRIPE_PAID_PRICE_IDS",
        description="Comma-separated Stripe Price IDs that grant paid access.",
    )
    stripe_price_basic: str | None = Field(default=None, alias="STRIPE_PRICE_BASIC")
    stripe_price_pro: str | None = Field(default=None, alias="STRIPE_PRICE_PRO")
    stripe_success_url: str = Field(
        default="http://localhost:5173/?checkout=success",
        alias="STRIPE_SUCCESS_URL",
    )
    stripe_cancel_url: str = Field(
        default="http://localhost:5173/?checkout=cancel",
        alias="STRIPE_CANCEL_URL",
    )

    @model_validator(mode="after")
    def _validate_jwt_secret(self) -> "Settings":
        _default = "dev-jwt-secret-change-me"
        if self.environment == "production":
            if self.jwt_secret_key == _default:
                raise ValueError("JWT_SECRET_KEY must be changed from the default in production")
            if len(self.jwt_secret_key) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production")
            _localhost = "localhost"
            if _localhost in self.stripe_success_url or _localhost in self.stripe_cancel_url:
                logger.warning(
                    "STRIPE_SUCCESS_URL/STRIPE_CANCEL_URL vẫn trỏ về localhost trong môi trường production. "
                    "Đặt STRIPE_SUCCESS_URL và STRIPE_CANCEL_URL đúng domain trước khi chạy production."
                )
        return self

    def resolve_default_checkout_price_id(self) -> str:
        """Giá dùng cho nút Upgrade (ưu tiên PRO → BASIC → id đầu trong STRIPE_PAID_PRICE_IDS)."""
        if self.stripe_price_pro:
            return self.stripe_price_pro
        if self.stripe_price_basic:
            return self.stripe_price_basic
        raw = self.stripe_paid_price_ids.strip()
        if not raw:
            raise ValueError(
                "Thiếu cấu hình giá Checkout: đặt STRIPE_PRICE_PRO, STRIPE_PRICE_BASIC hoặc STRIPE_PAID_PRICE_IDS"
            )
        first = raw.split(",")[0].strip()
        if not first:
            raise ValueError("STRIPE_PAID_PRICE_IDS không hợp lệ")
        return first

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
