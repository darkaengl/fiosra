from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "Fiosra Reasoning Infrastructure"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "change-this-in-production-secret-token-key"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # PostgreSQL Connection String (asyncpg)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fiosra_db"

    # LLM API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # Verifiers & Scaffolding
    ENABLE_MATH_CAS: bool = True
    ENABLE_NLI_VERIFIER: bool = False
    DEFAULT_MAX_HINT_LEVEL: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
