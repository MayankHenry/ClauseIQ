"""
SQLAlchemy engine + session factory. Use `get_db()` as a FastAPI dependency
in API routes; use `SessionLocal()` directly in Celery tasks and scripts
where there's no request/dependency-injection context.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
