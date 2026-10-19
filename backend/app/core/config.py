from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Campus Repair System API"
    debug: bool = False
    api_prefix: str = "/api"
    database_url: str = "mysql+aiomysql://repair:repair@localhost:3307/repair_system"
    jwt_secret: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    scheduler_enabled: bool = True
    scheduler_timezone: str = "Asia/Shanghai"
    auto_close_cron_hour: int = 3
    auto_close_cron_minute: int = 30
    auto_close_timeout_hours: int = 48


@lru_cache
def get_settings() -> Settings:
    return Settings()
