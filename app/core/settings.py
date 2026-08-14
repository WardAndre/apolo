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

    asset_storage_dir: str = "storage/assets"
    asset_public_path: str = "/assets"
    placeholder_asset_seconds: int = 20

    playout_manifest_path: str = "storage/playout/liquidsoap_queue.m3u"
    playout_asset_root: str = "/app/storage/assets"

    hls_output_dir: str = "storage/hls"
    hls_public_path: str = "/hls"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()