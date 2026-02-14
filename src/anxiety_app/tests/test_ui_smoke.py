from __future__ import annotations

import os
from pathlib import Path

from PyQt5.QtWidgets import QApplication

from anxiety_app.data.db import create_engine_and_session, init_db
from anxiety_app.domain.services import (
    LearningService,
    ModuleDataService,
    ProgressService,
    SupportService,
    ToolService,
    ToolUsageService,
    UserSettingsService,
)
from anxiety_app.services.ai_client import AIClient
from anxiety_app.services.settings_service import SettingsService
from anxiety_app.services.tool_feedback_service import ToolFeedbackService
from anxiety_app.ui.main_window import MainWindow
from anxiety_app.ui.widgets.learn_view import LearnView


def test_main_window_smoke(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])

    db_path = tmp_path / "ui.db"
    engine, session_factory = create_engine_and_session(db_path)
    init_db(engine)

    learning_service = LearningService(session_factory)
    module_data_service = ModuleDataService(session_factory)
    tool_service = ToolService(session_factory)
    tool_usage_service = ToolUsageService(session_factory)
    user_settings_service = UserSettingsService(session_factory)
    progress_service = ProgressService(session_factory)
    support_service = SupportService(session_factory)
    settings_service = SettingsService(session_factory, AIClient("test"))
    tool_feedback_service = ToolFeedbackService(AIClient("test"))

    style_path = Path(__file__).resolve().parent.parent / "ui" / "style.qss"
    window = MainWindow(
        learning_service=learning_service,
        style_path=style_path,
        app_name="AnxietyApp",
        module_data_service=module_data_service,
        settings_service=settings_service,
        tool_service=tool_service,
        tool_feedback_service=tool_feedback_service,
        tool_usage_service=tool_usage_service,
        user_settings_service=user_settings_service,
        progress_service=progress_service,
        support_service=support_service,
    )
    window.show()
    app.processEvents()


def test_learn_view_module1_opens(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])

    db_path = tmp_path / "learn.db"
    engine, session_factory = create_engine_and_session(db_path)
    init_db(engine)

    learning_service = LearningService(session_factory)
    module_data_service = ModuleDataService(session_factory)
    learn_view = LearnView(learning_service, module_data_service)
    learn_view.show()
    learn_view._open_module1()
    app.processEvents()
