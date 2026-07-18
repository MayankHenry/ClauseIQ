"""
Centralized app configuration, loaded from environment variables (with a
.env file supported for local dev). Import `settings` anywhere you need
a config value instead of hardcoding connection strings.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://clauseiq:clauseiq_dev@localhost:5434/clauseiq"
    REDIS_URL: str = "redis://localhost:6380/0"
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "clauseiq_clauses"


    # bge-small is used by default for fast local dev (~130MB download, CPU-friendly).
    # Swap to "BAAI/bge-large-en-v1.5" later for production-quality retrieval —
    # nothing else in the codebase needs to change, since embedding dimension
    # is auto-detected at runtime rather than hardcoded.
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"

    STORAGE_DIR: str = "./storage"

    class Config:
        env_file = ".env"


settings = Settings()
