from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from nightwatch.backup import ensure_daily_backup
from nightwatch.config import get_settings
from nightwatch.migrate import apply_migrations


class Base(DeclarativeBase):
    pass


_settings = get_settings()
_engine = create_engine(
    f"sqlite:///{_settings.db_path}",
    connect_args={"check_same_thread": False, "timeout": 5},
    pool_pre_ping=True,
)


@event.listens_for(_engine, "connect")
def _configure_sqlite(dbapi_connection, _connection_record) -> None:
    """Apply reliability settings to every SQLite connection."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=5000")
    finally:
        cursor.close()


SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False, class_=Session)


def init_db() -> None:
    # Apply versioned SQL migrations first; models assume the schema exists.
    apply_migrations(get_settings().db_path)
    # Daily backup (no-op if already created today).
    ensure_daily_backup(get_settings().db_path, get_settings().backups_dir)


def get_engine() -> Engine:
    """Return the configured engine for health checks and integrations."""
    return _engine


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
