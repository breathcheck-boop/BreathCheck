from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

from anxiety_app.data.db import create_engine_and_session, init_db
from anxiety_app.domain.services import LearningService, ModuleDataService, TrackingService


def test_tracking_service_create_log(tmp_path: Path) -> None:
    db_path = tmp_path / "tracking.db"
    engine, session_factory = create_engine_and_session(db_path)
    init_db(engine)

    service = TrackingService(session_factory)
    entry, created = service.create_or_update_daily_log(
        date.today(), 6, 4, 5, "", datetime.now(UTC)
    )
    assert entry.id is not None
    assert entry.mood == 6
    assert created is True


def test_learning_service_progress(tmp_path: Path) -> None:
    db_path = tmp_path / "learning.db"
    engine, session_factory = create_engine_and_session(db_path)
    init_db(engine)

    service = LearningService(session_factory)
    entry = service.update_progress("module_1", "UNLOCKED", 30)
    assert entry.progress_percent == 30
    assert service.list_progress()


def test_module_data_service(tmp_path: Path) -> None:
    db_path = tmp_path / "module.db"
    engine, session_factory = create_engine_and_session(db_path)
    init_db(engine)

    service = ModuleDataService(session_factory)
    payload = {
        "reasons_selected": ["Testing"],
        "micro_plan": {"plan_choice": "Test plan", "confidence": 5},
    }
    service.update_module_data("module_1", payload)
    data = service.get_module_data("module_1")
    assert data is not None
    assert data.data["reasons_selected"] == ["Testing"]
    assert data.data["micro_plan"]["confidence"] == 5
