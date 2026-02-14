from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from anxiety_app.domain.services import UserSettingsService


class OnboardingView(QWidget):
    completed = pyqtSignal()

    def __init__(self, user_settings_service: UserSettingsService) -> None:
        super().__init__()
        self.setObjectName("ViewRoot")
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._user_settings_service = user_settings_service

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(48, 48, 48, 48)

        title = QLabel("Welcome to your BreathCheck Journey")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        disclaimer = QLabel(
            "BreathCheck is not a substitute for professional mental health treatment.\n"
            "If you feel unsafe or in crisis, seek immediate professional or emergency help.\n\n"
            "Your responses are confidential.\n"
            "Your data is stored locally on your device."
        )
        disclaimer.setWordWrap(True)
        disclaimer.setAlignment(Qt.AlignCenter)
        layout.addWidget(disclaimer)

        self._ack = QCheckBox("I understand and wish to continue")
        self._ack.setChecked(False)
        self._ack.stateChanged.connect(self._update_state)
        layout.addWidget(self._ack, alignment=Qt.AlignCenter)

        self._continue_button = QPushButton("Continue")
        self._continue_button.setObjectName("AccentButton")
        self._continue_button.setEnabled(False)
        self._continue_button.clicked.connect(self._complete_onboarding)
        layout.addWidget(self._continue_button, alignment=Qt.AlignCenter)

        layout.addStretch()

    def should_show(self) -> bool:
        settings = self._user_settings_service.get_settings()
        self._ack.setChecked(False)
        self._continue_button.setEnabled(False)
        return not settings.onboarding_completed

    def _update_state(self) -> None:
        self._continue_button.setEnabled(self._ack.isChecked())

    def _complete_onboarding(self) -> None:
        if not self._ack.isChecked():
            return
        self._user_settings_service.update_settings({"onboarding_completed": True})
        self.completed.emit()
