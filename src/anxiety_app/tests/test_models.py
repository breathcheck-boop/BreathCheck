from __future__ import annotations

from datetime import date
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from anxiety_app.data.db import Base
from anxiety_app.data.models import DailyLog


def test_models_create_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    with Session() as session:
        entry = DailyLog(date=date(2024, 1, 1), mood=5, anxiety=4, trigger="")
        session.add(entry)
        session.commit()

        assert session.query(DailyLog).count() == 1
