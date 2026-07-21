import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, HttpUrl, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent


def _parse_comma_separated(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    database_url: str
    openai_api_key: SecretStr

    openai_embedding_model: str = "nvidia/nemotron-3-embed-1b:free"
    openai_embedding_dimensions: int = Field(default=2048, ge=1)
    openrouter_api_key: SecretStr | None = None

    allowed_origins_raw: str = Field(
        default="http://localhost:5173",
        validation_alias="ALLOWED_ORIGINS",
    )

    # Normalize Supabase-style URLs for SQLAlchemy + psycopg v3.
    @computed_field
    @property
    def sqlalchemy_database_url(self) -> str:
        """Normalize Supabase-style URLs for SQLAlchemy + psycopg v3."""
        url = self.database_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg://", 1)
        return url

    @computed_field
    @property
    def allowed_origins(self) -> list[str]:
        return _parse_comma_separated(self.allowed_origins_raw)


def _mirror_sdk_env(settings: Settings) -> None:
    # Third-party SDKs read os.environ directly; settings remain the source of truth.
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key.get_secret_value()
    if settings.openrouter_api_key is not None:
        os.environ["OPENROUTER_API_KEY"] = settings.openrouter_api_key.get_secret_value()

# Cache the settings object to avoid re-reading the environment variables on each request.
@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    _mirror_sdk_env(settings)
    return settings


settings = get_settings()
