from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_recycle_seconds: int = 3600
    db_echo: bool = False

    app_name: str = "Feedback Platform"
    debug: bool = False
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    access_token_expire_minutes: int = 60 * 24

    database_url: str = "sqlite+aiosqlite:///./feedback.db"

    upload_dir: str = "uploads"
    max_upload_size_mb: int = 10
    max_appeal_text_length: int = 5000
    allowed_extensions: str = ".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg,.gif,.webp,.txt,.zip"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True

    telegram_bot_token: str = ""
<<<<<<< HEAD

    # URL веб-портала (фронтенд) для ссылок в уведомлениях
    portal_url: str = Field(
        default="http://localhost:3000",
        validation_alias=AliasChoices("PORTAL_URL", "PUBLIC_BASE_URL", "portal_url"),
    )
    cors_origins: list[str] = ["http://localhost:3000"]
=======
    public_base_url: str = "http://localhost:8000"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
>>>>>>> 976dc1d6ed553e2a0c0b985766cfd3e7a107c95e


@lru_cache
def get_settings() -> Settings:
    return Settings()
