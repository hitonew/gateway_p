from typing import Dict, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./app.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "changeme"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Infrastructure
    API_PORT: int = 8000

    # Banco Comercio credentials
    bdc_base_url: str = "https://api-homo.bdcconecta.com"
    bdc_client_id: str = ""
    bdc_client_secret: str = ""
    bdc_secret_key: str = ""
    transfer_connector_mode: str = "mock"
    persistence_backend: str = "database"
    
    class Config:
        env_file = ".env"

settings = Settings()
