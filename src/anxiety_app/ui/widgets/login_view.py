from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QVBoxLayout,
    QWidget,
)

from anxiety_app.core.security import (
    get_master_password_hash,
    set_master_password,
    verify_master_password,
)


class LoginView(QWidget):
    login_success = pyqtSignal()
    cancel_requested = pyqtSignal()

    def __init__(self, service_name: str) -> None:
        super().__init__()
        self.setObjectName("ViewRoot")
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._service_name = service_name

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.addStretch()

        logo = QLabel()
        logo.setPixmap(self._load_logo_pixmap(140))
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        slogan = QLabel("Track your breath. Steady your mind.")
        slogan.setObjectName("CardMeta")
        slogan.setAlignment(Qt.AlignCenter)
        layout.addWidget(slogan)

        self._title = QLabel("")
        self._title.setObjectName("Title")
        self._title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._title)

        layout.addWidget(QLabel("Password"))
        self._password_input = QLineEdit()
        self._password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self._password_input)

        self._confirm_label = QLabel("Confirm password")
        self._confirm_input = QLineEdit()
        self._confirm_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self._confirm_label)
        layout.addWidget(self._confirm_input)

        self._show_password = QCheckBox("Show password")
        self._show_password.stateChanged.connect(self._toggle_password_visibility)
        layout.addWidget(self._show_password)

        self._status = QLabel("")
        self._status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._status)

        button_row = QHBoxLayout()
        cancel = QPushButton("Exit")
        cancel.clicked.connect(self.cancel_requested.emit)
        submit = QPushButton("Confirm")
        submit.setObjectName("AccentButton")
        submit.clicked.connect(self._handle_submit)
        button_row.addStretch()
        button_row.addWidget(cancel)
        button_row.addWidget(submit)
        layout.addLayout(button_row)
        layout.addStretch()

        self._password_input.returnPressed.connect(self._handle_submit)
        self._confirm_input.returnPressed.connect(self._handle_submit)

        self.refresh_state()

    def refresh_state(self) -> None:
        self._has_password = bool(get_master_password_hash(self._service_name))
        if self._has_password:
            self._title.setText("Enter master password")
            self._confirm_label.hide()
            self._confirm_input.hide()
        else:
            self._title.setText("Create a master password")
            self._confirm_label.show()
            self._confirm_input.show()
        self._password_input.clear()
        self._confirm_input.clear()
        self._status.clear()
        self._show_password.setChecked(False)
        self._toggle_password_visibility()
        self._password_input.setFocus()

    def _handle_submit(self) -> None:
        password = self._password_input.text().strip()
        if not password:
            self._status.setText("Please enter a password.")
            return
        if not self._has_password:
            confirm = self._confirm_input.text().strip()
            if password != confirm:
                self._status.setText("Passwords do not match.")
                return
            set_master_password(self._service_name, password)
            self.login_success.emit()
            return
        if verify_master_password(self._service_name, password):
            self.login_success.emit()
        else:
            self._status.setText("Incorrect password.")

    def _toggle_password_visibility(self) -> None:
        mode = QLineEdit.Normal if self._show_password.isChecked() else QLineEdit.Password
        self._password_input.setEchoMode(mode)
        self._confirm_input.setEchoMode(mode)

    def _logo_path(self) -> Path:
        base = Path(__file__).resolve().parent.parent / "resources"
        for ext in (".webp", ".png", ".jpg", ".jpeg"):
            path = base / f"app_logo{ext}"
            if path.exists():
                return path
        return base / "app_logo.png"

    def _load_logo_pixmap(self, size: int) -> QPixmap:
        path = self._logo_path()
        if path.exists():
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                return pixmap.scaled(
                    size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
        return QPixmap()
