from pydantic_settings import BaseSettings

from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Aegis"
    DATABASE_URL: str = "sqlite:///./aegis.db"
    SECRET_KEY: str = "changeme_in_production"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
