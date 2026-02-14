from __future__ import annotations

from pathlib import Path
from typing import Callable

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def create_engine_and_session(
    db_path: Path,
) -> tuple[Engine, Callable[[], Session]]:
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        echo=False,
        future=True,
    )
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return engine, session_factory


def init_db(engine: Engine) -> None:
    from anxiety_app.data import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_daily_log_columns(engine)
    _ensure_module_progress_columns(engine)


def _ensure_daily_log_columns(engine: Engine) -> None:
    # Lightweight migration for local SQLite databases.
    with engine.begin() as connection:
        result = connection.execute(text("PRAGMA table_info(daily_logs)"))
        columns = {row[1] for row in result.fetchall()}
        if "stress" not in columns:
            connection.execute(text("ALTER TABLE daily_logs ADD COLUMN stress INTEGER DEFAULT 0"))
        connection.execute(
            text("UPDATE daily_logs SET stress = 0 WHERE stress IS NULL")
        )
        if "entry_time" not in columns:
            connection.execute(
                text("ALTER TABLE daily_logs ADD COLUMN entry_time DATETIME")
            )
        connection.execute(
            text(
                "UPDATE daily_logs SET entry_time = created_at "
                "WHERE entry_time IS NULL"
            )
        )


def _ensure_module_progress_columns(engine: Engine) -> None:
    with engine.begin() as connection:
        result = connection.execute(text("PRAGMA table_info(module_progress)"))
        columns = {row[1] for row in result.fetchall()}
        if "completed_at" not in columns:
            connection.execute(
                text("ALTER TABLE module_progress ADD COLUMN completed_at DATETIME")
            )
