from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://clauseiq:clauseiq_dev@localhost:5434/clauseiq"
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "clauseiq_clauses"
    REDIS_URL: str = "redis://localhost:6380/0"
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    STORAGE_DIR: str = "./storage"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # Bare-bones auth (Day 13). Leave APP_PASSWORD unset for local dev --
    # auth becomes a no-op. Set both in any deployed environment.
    APP_PASSWORD: str = ""
    APP_SECRET_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
