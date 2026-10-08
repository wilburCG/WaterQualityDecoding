from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://wqd:wqd_dev_pwd@localhost:5434/wqd"
    cors_origins: str = "http://localhost:3003"
    secret_key: str = "wqd-dev-secret-change-me"
    token_expire_days: int = 14
    # 种子管理员：首次启动 seed 时若该邮箱不存在则创建
    admin_email: str = "admin@wqd.local"
    admin_password: str = "wqd-admin-2026"


@lru_cache
def get_settings() -> Settings:
    return Settings()
