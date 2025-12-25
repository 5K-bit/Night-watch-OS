from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from nightwatch.settings import DB_PATH


class Base(DeclarativeBase):
    pass


_engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False, class_=Session)


def init_db() -> None:
    # Import models so metadata is populated before create_all()
    from nightwatch import models  # noqa: F401

    Base.metadata.create_all(bind=_engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

