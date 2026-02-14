from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QShortcut,
    QSizePolicy,
    QStackedWidget,
    QWidget,
)

from anxiety_app.domain.services import (
    LearningService,
    ModuleDataService,
    ProgressService,
    SupportService,
    ToolService,
    ToolUsageService,
    UserSettingsService,
)
from anxiety_app.services.settings_service import SettingsService
from anxiety_app.services.tool_feedback_service import ToolFeedbackService
from anxiety_app.ui.widgets.login_view import LoginView
from anxiety_app.ui.widgets.learn_view import LearnView
from anxiety_app.ui.widgets.onboarding_view import OnboardingView
from anxiety_app.ui.widgets.progress_view import ProgressView
from anxiety_app.ui.widgets.settings_view import SettingsView
from anxiety_app.ui.widgets.sidebar import Sidebar
from anxiety_app.ui.widgets.toast import Toast
from anxiety_app.ui.widgets.support_view import SupportView
from anxiety_app.ui.widgets.tools_view import ToolsView
from anxiety_app.core.preferences import load_appearance_settings, AppearanceSettings
from anxiety_app.ui.theme import apply_theme


class MainWindow(QMainWindow):
    def __init__(
        self,
        learning_service: LearningService,
        style_path: Path,
        app_name: str,
        module_data_service: ModuleDataService,
        settings_service: SettingsService,
        tool_service: ToolService,
        tool_feedback_service: ToolFeedbackService,
        tool_usage_service: ToolUsageService,
        user_settings_service: UserSettingsService,
        progress_service: ProgressService,
        support_service: SupportService,
    ) -> None:
        super().__init__()
        self.setWindowTitle(app_name)
        self.setWindowFlags(
            Qt.Window
            | Qt.CustomizeWindowHint
            | Qt.WindowTitleHint
            | Qt.WindowCloseButtonHint
        )
        self._style_path = style_path

        self._stacked = QStackedWidget()
        self._stacked.setAutoFillBackground(True)
        self._stacked.setAttribute(Qt.WA_StyledBackground, True)
        self._stacked.setContentsMargins(0, 0, 0, 0)
        self._learn_view = LearnView(learning_service, module_data_service)
        self._tools_view = ToolsView(tool_service, tool_feedback_service, tool_usage_service)
        self._progress_view = ProgressView(progress_service)
        self._support_view = SupportView(support_service)
        self._settings_view = SettingsView(settings_service, user_settings_service)
        self._toast = Toast(self)

        self._stacked.addWidget(self._learn_view)
        self._stacked.addWidget(self._tools_view)
        self._stacked.addWidget(self._progress_view)
        self._stacked.addWidget(self._support_view)
        self._stacked.addWidget(self._settings_view)

        self._sidebar = Sidebar(["Learn", "Tools", "Progress", "Support", "Settings"])
        self._sidebar.setFixedWidth(180)
        self._sidebar.page_selected.connect(self._stacked.setCurrentIndex)
        self._sidebar.logout_requested.connect(self._handle_logout)
        self._stacked.currentChanged.connect(self._handle_page_changed)
        self._settings_view.data_deleted.connect(self._handle_data_deleted)
        self._settings_view.logout_requested.connect(self._handle_logout)
        self._settings_view.password_changed.connect(
            lambda: self._show_toast("Master password updated.", "success")
        )
        self._settings_view.appearance_changed.connect(self._apply_appearance)
        self._settings_view.account_deleted.connect(
            lambda: self._show_toast("Account deleted.", "error")
        )
        self._learn_view.module_completed.connect(self._handle_module_completed)
        self._progress_view.milestone_achieved.connect(self._handle_milestone_achieved)
        self._tools_view.tool_submitted.connect(self._handle_tool_submitted)
        self._tools_view.tool_feedback_ready.connect(self._handle_tool_feedback_ready)
        self._current_index = 0
        self._progress_dirty = True
        self._init_shortcuts()

        self._appearance = load_appearance_settings()
        apply_theme(QApplication.instance(), self._style_path, self._appearance)
        self._apply_window_dimensions(self._appearance)

        app_container = QWidget()
        app_container.setObjectName("AppRoot")
        app_container.setAutoFillBackground(True)
        app_container.setAttribute(Qt.WA_StyledBackground, True)
        layout = QHBoxLayout(app_container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.addWidget(self._sidebar)
        layout.addWidget(self._stacked)
        app_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._login_view = LoginView(app_name)
        self._login_view.login_success.connect(self._handle_login_success)
        self._login_view.cancel_requested.connect(self.close)
        self._onboarding_view = OnboardingView(user_settings_service)
        self._onboarding_view.completed.connect(self._show_app)

        self._root_stack = QStackedWidget()
        self._root_stack.addWidget(self._login_view)
        self._root_stack.addWidget(self._onboarding_view)
        self._root_stack.addWidget(app_container)
        self._root_stack.setCurrentIndex(0)
        self.setCentralWidget(self._root_stack)



    def _init_shortcuts(self) -> None:
        mappings = [
            ("Ctrl+1", 0),
            ("Ctrl+2", 1),
            ("Ctrl+3", 2),
            ("Ctrl+4", 3),
            ("Ctrl+5", 4),
        ]
        self._shortcuts: list[QShortcut] = []
        for key, index in mappings:
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(lambda index=index: self._set_home_target(index))
            self._shortcuts.append(shortcut)

    def _apply_appearance(self, appearance) -> None:
        self._appearance = appearance
        apply_theme(QApplication.instance(), self._style_path, self._appearance)
        self._apply_window_dimensions(self._appearance)

    def apply_window_dimensions(self) -> None:
        self._apply_window_dimensions(self._appearance)

    def _apply_window_dimensions(self, appearance: AppearanceSettings) -> None:
        _ = appearance
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            self.setGeometry(geom)
            self.setFixedSize(geom.size())
        else:
            self.setFixedSize(self.size())

    def _handle_data_deleted(self) -> None:
        self._learn_view.reset_module1_state()
        self._progress_view.reset_view()
        self._tools_view.reset_view()
        self._progress_dirty = False
        self._set_home_target(0)
        self._login_view.refresh_state()
        self._show_toast("All data deleted.", "error")

    def _handle_module_completed(self, module_id: str) -> None:
        label = module_id.replace("_", " ").title()
        if self._current_index == 2:
            self._progress_view.refresh()
        else:
            self._progress_dirty = True
        self._show_toast(f"{label} completed.", "success")

    def _handle_milestone_achieved(self, title: str) -> None:
        self._show_toast(f"Milestone achieved: {title}", "success")

    def _handle_tool_submitted(self, title: str) -> None:
        if self._current_index == 2:
            self._progress_view.refresh()
        else:
            self._progress_dirty = True
        self._show_toast(f"Tool submitted: {title}", "success")

    def _handle_tool_feedback_ready(self, tool_name: str) -> None:
        label = tool_name.replace("_", " ").title()
        self._show_toast(f"Feedback ready: {label}", "info")

    def _show_toast(self, message: str, tone: str = "info") -> None:
        self._toast.show_message(message, tone)

    def _handle_logout(self) -> None:
        self._login_view.refresh_state()
        self._root_stack.setCurrentIndex(0)

    def _handle_login_success(self) -> None:
        if self._onboarding_view.should_show():
            self._root_stack.setCurrentIndex(1)
        else:
            self._show_app()

    def _show_app(self) -> None:
        self._root_stack.setCurrentIndex(2)
        self._set_home_target(0)

    def _set_home_target(self, index: int) -> None:
        self._stacked.setCurrentIndex(index)
        self._sidebar.set_current(index)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._tools_view.wait_for_workers()
        super().closeEvent(event)

    def _handle_page_changed(self, index: int) -> None:
        if self._current_index == 0 and index != 0:
            self._learn_view.stop_audio()
            self._learn_view.show_modules()
        if self._current_index == 1 and index != 1:
            self._tools_view.on_leave()
        if index == 2 and self._progress_dirty:
            self._progress_view.refresh()
            self._progress_dirty = False
        self._sidebar.set_current(index)
        self._current_index = index
