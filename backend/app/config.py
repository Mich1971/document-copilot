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
        extra="ignore",
    )

    supabase_url: HttpUrl
    supabase_anon_key: SecretStr
    supabase_service_role_key: SecretStr

    database_url: SecretStr

    openai_api_key: SecretStr
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = Field(default=1536, ge=1)

    allowed_origins_raw: str = Field(
        default="http://localhost:5173",
        validation_alias="ALLOWED_ORIGINS",
    )

    @computed_field
    @property
    def allowed_origins(self) -> list[str]:
        return _parse_comma_separated(self.allowed_origins_raw)


def _mirror_sdk_env(settings: Settings) -> None:
    # Third-party SDKs read os.environ directly; settings remain the source of truth.
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    _mirror_sdk_env(settings)
    return settings


settings = get_settings()
