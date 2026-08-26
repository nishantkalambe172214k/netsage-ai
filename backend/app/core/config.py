from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "NetSage AI"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api"
    DATABASE_URL: str = "sqlite:///./netsage.db"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]
    GEMINI_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")


settings = Settings()
