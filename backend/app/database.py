"""Database engine and session handling (SQLAlchemy 2.x)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import DATABASE_URL

IN_MEMORY_URLS = {"sqlite://", "sqlite:///:memory:"}


def _create_engine(url: str):
    if url.startswith("sqlite"):
        options = {"connect_args": {"check_same_thread": False}}
        if url in IN_MEMORY_URLS:
            # One shared connection, so every session sees the same in-memory DB.
            options["poolclass"] = StaticPool
        return create_engine(url, **options)
    return create_engine(url, pool_pre_ping=True)


engine = _create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    from app import models  # noqa: F401  (registers the tables)

    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency: one session per request, always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
