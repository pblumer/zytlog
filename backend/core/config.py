from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Zytlog API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+psycopg://zytlog:zytlog@db:5432/zytlog"

    auth_enabled: bool = True
    auth_disabled_fallback_user_id: int = 1

    keycloak_url: str = "http://keycloak:8080"
    keycloak_realm: str = "zytlog"
    keycloak_issuer: str | None = None
    keycloak_jwks_url: str | None = None
    keycloak_audience: str | None = None
    keycloak_verify_audience: bool = False
    openholidays_base_url: str = "https://openholidaysapi.org"

    @computed_field
    @property
    def keycloak_issuer_resolved(self) -> str:
        if self.keycloak_issuer:
            return self.keycloak_issuer
        base_url = self.keycloak_url.rstrip("/")
        return f"{base_url}/realms/{self.keycloak_realm}"

    @computed_field
    @property
    def keycloak_jwks_url_resolved(self) -> str:
        if self.keycloak_jwks_url:
            return self.keycloak_jwks_url
        return f"{self.keycloak_issuer_resolved}/protocol/openid-connect/certs"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
