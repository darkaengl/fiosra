
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Fiosra Reasoning Infrastructure"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "change-this-in-production-secret-token-key"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # PostgreSQL Connection String (asyncpg)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fiosra_db"

    # Neo4j 5 Connection Settings
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "fiosra_neo4j_password"

    # LLM API Keys
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None

    # Verifiers & Scaffolding
    ENABLE_MATH_CAS: bool = True
    ENABLE_NLI_VERIFIER: bool = False
    DEFAULT_MAX_HINT_LEVEL: int = 3
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
