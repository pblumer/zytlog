from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Zytlog API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+psycopg://zytlog:zytlog@db:5432/zytlog"

    keycloak_server_url: str = "http://keycloak:8080"
    keycloak_realm: str = "zytlog"
    keycloak_client_id: str = "zytlog-web"
    keycloak_client_secret: str = "change-me"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
