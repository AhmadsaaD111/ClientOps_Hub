from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "ClientOps Hub API"
    api_v1_prefix: str = "/api"

    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60 * 24
    algorithm: str = "HS256"

    database_url: str = "sqlite:///./clientops.db"
    cors_origins: str = "http://localhost:5173,http://localhost:5174"

    @property
    def cors_origins_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]

        # Vite commonly falls back to 5174 when 5173 is already in use.
        if "http://localhost:5173" in origins and "http://localhost:5174" not in origins:
            origins.append("http://localhost:5174")
        if "http://localhost:5174" in origins and "http://localhost:5173" not in origins:
            origins.append("http://localhost:5173")

        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
