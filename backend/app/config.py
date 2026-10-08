from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://wqd:wqd_dev_pwd@localhost:5434/wqd"
    cors_origins: str = "http://localhost:3003"


@lru_cache
def get_settings() -> Settings:
    return Settings()
