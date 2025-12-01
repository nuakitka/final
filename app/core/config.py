from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # ИСПРАВЛЕНИЕ: Переименовано в DATABASE_URL, чтобы совпадать с app/models/__init__.py
    DATABASE_URL: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    debug: bool = False
    
    # Современный синтаксис Pydantic для Config
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()