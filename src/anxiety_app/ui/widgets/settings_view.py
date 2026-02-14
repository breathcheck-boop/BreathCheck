from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from anxiety_app.core.preferences import AppearanceSettings, load_appearance_settings, save_appearance_settings
from anxiety_app.domain.services import UserSettingsService
from anxiety_app.services.settings_service import SettingsService
from anxiety_app.ui.widgets.change_password_dialog import ChangePasswordDialog


class SettingsView(QWidget):
    data_deleted = pyqtSignal()
    logout_requested = pyqtSignal()
    password_changed = pyqtSignal()
    account_deleted = pyqtSignal()
    appearance_changed = pyqtSignal(object)

    def __init__(
        self,
        settings_service: SettingsService,
        user_settings_service: UserSettingsService,
    ) -> None:
        super().__init__()
        self.setObjectName("ViewRoot")
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._settings_service = settings_service
        self._user_settings_service = user_settings_service
        self._loading = True

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        security_card = QFrame()
        security_card.setObjectName("Card")
        security_layout = QVBoxLayout(security_card)
        security_title = QLabel("Security")
        security_title.setObjectName("CardTitle")
        security_layout.addWidget(security_title)
        enabled, message = self._settings_service.encryption_status()
        encryption_label = QLabel(message)
        encryption_label.setWordWrap(True)
        encryption_label.setObjectName("CardMeta" if enabled else "")
        security_layout.addWidget(encryption_label)
        local_label = QLabel("Your data is stored locally on your device.")
        local_label.setObjectName("CardMeta")
        local_label.setWordWrap(True)
        security_layout.addWidget(local_label)
        layout.addWidget(security_card)

        appearance_card = QFrame()
        appearance_card.setObjectName("Card")
        appearance_layout = QVBoxLayout(appearance_card)
        appearance_title = QLabel("Appearance")
        appearance_title.setObjectName("CardTitle")
        appearance_layout.addWidget(appearance_title)

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Theme"))
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Light", "Dark"])
        theme_row.addWidget(self._theme_combo)
        theme_row.addStretch()
        appearance_layout.addLayout(theme_row)

        self._comfort_toggle = QCheckBox("Comfort mode (softer colors)")
        appearance_layout.addWidget(self._comfort_toggle)

        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Font size"))
        self._font_combo = QComboBox()
        self._font_combo.addItems(["Small", "Medium", "Large"])
        font_row.addWidget(self._font_combo)
        font_row.addStretch()
        appearance_layout.addLayout(font_row)

        reminder_row = QHBoxLayout()
        reminder_row.addWidget(QLabel("Reminder preference"))
        self._reminder_combo = QComboBox()
        self._reminder_combo.addItems(["Morning", "Afternoon", "Evening", "Off"])
        reminder_row.addWidget(self._reminder_combo)
        reminder_row.addStretch()
        appearance_layout.addLayout(reminder_row)

        layout.addWidget(appearance_card)

        export_card = QFrame()
        export_card.setObjectName("Card")
        export_layout = QVBoxLayout(export_card)
        export_title = QLabel("Export data")
        export_title.setObjectName("CardTitle")
        export_layout.addWidget(export_title)
        export_row = QHBoxLayout()
        self._export_combo = QComboBox()
        self._export_combo.addItems(["JSON", "CSV"])
        export_row.addWidget(self._export_combo)
        export_button = QPushButton("Export")
        export_button.setObjectName("AccentButton")
        export_button.clicked.connect(self._export_data)
        export_row.addWidget(export_button)
        export_row.addStretch()
        export_layout.addLayout(export_row)
        export_hint = QLabel(
            "Export includes tracker logs, module data, tool entries, and insights."
        )
        export_hint.setObjectName("CardMeta")
        export_hint.setWordWrap(True)
        export_layout.addWidget(export_hint)
        layout.addWidget(export_card)

        account_card = QFrame()
        account_card.setObjectName("Card")
        card_layout = QVBoxLayout(account_card)

        password_button = QPushButton("Change master password")
        password_button.clicked.connect(self._change_password)
        card_layout.addWidget(password_button)

        reset_progress_button = QPushButton("Reset progress")
        reset_progress_button.clicked.connect(self._confirm_reset_progress)
        card_layout.addWidget(reset_progress_button)

        delete_account_button = QPushButton("Delete account")
        delete_account_button.setObjectName("AccentButton")
        delete_account_button.clicked.connect(self._confirm_delete_account)
        card_layout.addWidget(delete_account_button)

        delete_button = QPushButton("Delete all data")
        delete_button.setObjectName("AccentButton")
        delete_button.clicked.connect(self._confirm_delete)
        card_layout.addWidget(delete_button)

        layout.addWidget(account_card)
        layout.addStretch()

        self._load_appearance_settings()
        self._load_user_settings()
        self._loading = False

        self._theme_combo.currentTextChanged.connect(self._emit_appearance_changed)
        self._comfort_toggle.stateChanged.connect(self._emit_appearance_changed)
        self._font_combo.currentTextChanged.connect(self._emit_appearance_changed)
        self._reminder_combo.currentTextChanged.connect(self._emit_appearance_changed)

    def _confirm_delete(self) -> None:
        result = QMessageBox.question(
            self,
            "Delete all data",
            "This will permanently delete all local data. Continue?",
        )
        if result == QMessageBox.Yes:
            self._settings_service.delete_all_data()
            QMessageBox.information(self, "Data deleted", "All data has been removed.")
            self.data_deleted.emit()

    def _change_password(self) -> None:
        dialog = ChangePasswordDialog(self._settings_service.service_name)
        if dialog.exec_() == QDialog.Accepted:
            self.password_changed.emit()

    def _confirm_delete_account(self) -> None:
        result = QMessageBox.question(
            self,
            "Delete account",
            "This will delete all data and remove the master password. Continue?",
        )
        if result == QMessageBox.Yes:
            self._settings_service.delete_account()
            QMessageBox.information(self, "Account deleted", "Account has been removed.")
            self.account_deleted.emit()
            self.data_deleted.emit()
            self.logout_requested.emit()

    def _load_appearance_settings(self) -> None:
        settings = load_appearance_settings()
        self._theme_combo.setCurrentText("Dark" if settings.mode == "dark" else "Light")
        self._comfort_toggle.setChecked(settings.comfort)
        font_text = settings.font_size.capitalize()
        if font_text not in {"Small", "Medium", "Large"}:
            font_text = "Medium"
        self._font_combo.setCurrentText(font_text)

    def _load_user_settings(self) -> None:
        settings = self._user_settings_service.get_settings()
        reminder = settings.reminder_time or "Morning"
        if reminder not in {"Morning", "Afternoon", "Evening", "Off"}:
            reminder = "Morning"
        self._reminder_combo.setCurrentText(reminder)

    def _emit_appearance_changed(self) -> None:
        if self._loading:
            return
        mode = "dark" if self._theme_combo.currentText().lower() == "dark" else "light"
        comfort = self._comfort_toggle.isChecked()
        font_size = self._font_combo.currentText().lower()
        settings = AppearanceSettings(
            mode=mode,
            comfort=comfort,
            font_size=font_size,
            window_size="maximized",
        )
        save_appearance_settings(settings)
        self.appearance_changed.emit(settings)
        self._user_settings_service.update_settings(
            {
                "theme_mode": mode,
                "comfort_mode": comfort,
                "reminder_time": self._reminder_combo.currentText(),
            }
        )

    def _confirm_reset_progress(self) -> None:
        result = QMessageBox.question(
            self,
            "Reset progress",
            "This will reset module progress and module inputs. Continue?",
        )
        if result == QMessageBox.Yes:
            self._settings_service.reset_progress()
            QMessageBox.information(self, "Progress reset", "Progress has been reset.")
            self.data_deleted.emit()


    def _export_data(self) -> None:
        export_format = self._export_combo.currentText().lower()
        suffix = "json" if export_format == "json" else "csv"
        path_str, _filter = QFileDialog.getSaveFileName(
            self,
            "Export data",
            f"breathcheck_export.{suffix}",
            "All Files (*.*)",
        )
        if not path_str:
            return
        try:
            outputs = self._settings_service.export_all_data(export_format, Path(path_str))
            if export_format == "csv" and len(outputs) > 1:
                message = "CSV export created:\n" + "\n".join(str(p) for p in outputs)
            else:
                message = f"Export created: {outputs[0]}"
            QMessageBox.information(self, "Export complete", message)
        except Exception as exc:
            QMessageBox.warning(self, "Export failed", str(exc))
