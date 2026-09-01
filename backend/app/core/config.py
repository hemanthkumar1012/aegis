from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Aegis"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite:///./aegis.db"
    SECRET_KEY: Optional[str] = None
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CREDENTIAL_TTL_DAYS: int = 90
    REDIS_URL: str = "redis://localhost:6379/0"
    ADMIN_PASSWORD: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()

if settings.ENVIRONMENT.lower() == "production":
    if not settings.SECRET_KEY or settings.SECRET_KEY in ["", "changeme_in_production", "supersecretkey", "dev_secret_key_only"]:
        raise ValueError("CRITICAL: Missing or insecure SECRET_KEY in production. Refusing to start.")
    if not settings.ADMIN_PASSWORD or settings.ADMIN_PASSWORD in ["", "admin", "changeme", "password", "dev_admin_password"]:
        raise ValueError("CRITICAL: Missing or insecure ADMIN_PASSWORD in production. Refusing to start.")
    if "*" in settings.cors_origin_list:
        raise ValueError("CRITICAL: Wildcard CORS_ORIGINS not allowed in production.")
else:
    if not settings.SECRET_KEY:
        settings.SECRET_KEY = "dev_secret_key_only"
    if not settings.ADMIN_PASSWORD:
        settings.ADMIN_PASSWORD = "dev_admin_password"
