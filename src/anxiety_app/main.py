from __future__ import annotations

import sys
from pathlib import Path

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from anxiety_app.core.config import load_config
from anxiety_app.core.logging_config import setup_logging
from anxiety_app.data.db import create_engine_and_session, init_db
from anxiety_app.domain.services import (
    LearningService,
    ModuleDataService,
    ToolService,
    ToolUsageService,
    UserSettingsService,
    ProgressService,
    SupportService,
)
from anxiety_app.services.ai_client import AIClient
from anxiety_app.services.settings_service import SettingsService
from anxiety_app.services.tool_feedback_service import ToolFeedbackService
from anxiety_app.ui.combobox_centering import install_combobox_centering
from anxiety_app.ui.main_window import MainWindow


def main() -> int:
    config = load_config()
    setup_logging(config.debug)

    app = QApplication(sys.argv)
    app.setApplicationName(config.app_name)
    QCoreApplication.setOrganizationName(config.app_name)
    # Keep a reference so the event filter is not garbage-collected.
    app._combo_centering_filter = install_combobox_centering(app)  # type: ignore[attr-defined]

    icon_base = Path(__file__).resolve().parent / "ui" / "resources"
    icon_path = None
    for ext in (".ico", ".webp", ".png", ".jpg", ".jpeg"):
        candidate = icon_base / f"app_logo{ext}"
        if candidate.exists():
            icon_path = candidate
            break
    if icon_path:
        app.setWindowIcon(QIcon(str(icon_path)))

    engine, session_factory = create_engine_and_session(config.db_path)
    init_db(engine)

    learning_service = LearningService(session_factory)
    module_data_service = ModuleDataService(session_factory)
    tool_service = ToolService(session_factory)
    tool_usage_service = ToolUsageService(session_factory)
    user_settings_service = UserSettingsService(session_factory)
    progress_service = ProgressService(session_factory)
    support_service = SupportService(session_factory)
    ai_client = AIClient(
        config.app_name, api_key_env=config.ai_api_key_env, model_name=config.ai_model
    )
    tool_feedback_service = ToolFeedbackService(ai_client)
    settings_service = SettingsService(session_factory, ai_client)
    style_path = Path(__file__).resolve().parent / "ui" / "style.qss"
    window = MainWindow(
        learning_service=learning_service,
        style_path=style_path,
        app_name=config.app_name,
        module_data_service=module_data_service,
        settings_service=settings_service,
        tool_service=tool_service,
        tool_feedback_service=tool_feedback_service,
        tool_usage_service=tool_usage_service,
        user_settings_service=user_settings_service,
        progress_service=progress_service,
        support_service=support_service,
    )
    if icon_path:
        window.setWindowIcon(QIcon(str(icon_path)))
    window.show()
    window.apply_window_dimensions()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
