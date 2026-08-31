from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Aegis"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite:///./aegis.db"
    SECRET_KEY: str = "changeme_in_production"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CREDENTIAL_TTL_DAYS: int = 90
    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()

if settings.ENVIRONMENT.lower() == "production":
    if settings.SECRET_KEY in ["", "changeme_in_production", "supersecretkey"]:
        raise ValueError("CRITICAL: Insecure SECRET_KEY in production. Refusing to start.")
    if "*" in settings.cors_origin_list:
        raise ValueError("CRITICAL: Wildcard CORS_ORIGINS not allowed in production.")
