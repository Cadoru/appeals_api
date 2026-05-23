from functools import lru_cache

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
    max_upload_size_mb: int = 25
    allowed_extensions: str = ".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg,.gif,.webp,.txt,.zip"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True

    telegram_bot_token: str = ""
    public_base_url: str = "http://localhost:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
