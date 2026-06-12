from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings
from app.database.migrations import apply_database_migrations


class Base(DeclarativeBase):
    pass


def _connect_args(database_url: str) -> dict[str, bool]:
    return {"check_same_thread": False} if database_url.startswith("sqlite") else {}


engine = create_engine(get_settings().database_url, connect_args=_connect_args(get_settings().database_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.database import models  # noqa: F401
    from app.database.seed import seed_requirements

    Base.metadata.create_all(bind=engine)
    apply_database_migrations(engine)
    db = SessionLocal()
    try:
        seed_requirements(db)
    finally:
        db.close()
