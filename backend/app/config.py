"""Application configuration using Pydantic Settings."""
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    openai_api_key: str
    database_url: str = "sqlite:///./procurement.db"
    upload_dir: Path = Path("./app/uploads")
    max_upload_size_mb: int = 10
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost:8080"
    app_name: str = "Procurement Request System"
    app_version: str = "1.0.0"

    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
