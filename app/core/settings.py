from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Projeto Apolo"
    app_env: Literal["development", "test", "production"] = "development"
    generator_backend: Literal["mock", "simulated_ml", "ml_pipeline"] = "mock"
    ml_provider: Literal["simulated_vertex"] = "simulated_vertex"
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/projeto_apolo"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()