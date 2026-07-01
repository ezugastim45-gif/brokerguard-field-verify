"""Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Supabase (optional for testing)
    supabase_url: str = "https://test.supabase.co"
    supabase_key: str = "test-key"
    supabase_service_role_key: str = "test-service-key"
    supabase_bucket: str = "field-verifications"

    # OpenStreetMap
    osm_tile_server: str = "https://tile.openstreetmap.org"
    osm_user_agent: str = "BrokerGuardFieldVerify/0.1.0"
    osm_cache_dir: str = "./cache/osm_tiles"
    osm_cache_ttl: int = 86400  # 24 hours in seconds

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8002
    api_title: str = "BrokerGuard Field Verify API"
    api_version: str = "0.1.0"
    api_debug: bool = False

    # Security
    secret_key: str = "test-secret-key-change-in-production"
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8001"]
    require_api_key: bool = False  # true en produccion (X-API-Key vs api_keys)

    # Hash
    hash_algorithm: str = "sha256"

    # PDF
    pdf_font: str = "Helvetica"
    pdf_logo_path: str = "./assets/logo.png"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"


settings = Settings()
