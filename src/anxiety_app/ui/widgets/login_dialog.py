from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from anxiety_app.core.security import (
    get_master_password_hash,
    set_master_password,
    verify_master_password,
)


class MasterPasswordDialog(QDialog):
    def __init__(self, service_name: str) -> None:
        super().__init__()
        self._service_name = service_name
        self.setWindowTitle("Master Password")
        self.setModal(True)
        self.setFixedWidth(420)

        self._has_password = bool(get_master_password_hash(service_name))
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addStretch()

        title = QLabel(
            "Create a master password"
            if not self._has_password
            else "Enter master password"
        )
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self._password_input = QLineEdit()
        self._password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel("Password"))
        layout.addWidget(self._password_input)

        self._confirm_input: QLineEdit | None = None
        if not self._has_password:
            self._confirm_input = QLineEdit()
            self._confirm_input.setEchoMode(QLineEdit.Password)
            layout.addWidget(QLabel("Confirm password"))
            layout.addWidget(self._confirm_input)

        self._status = QLabel("")
        self._status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._status)

        button_row = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        submit = QPushButton("Confirm")
        submit.setObjectName("AccentButton")
        submit.clicked.connect(self._handle_submit)
        button_row.addStretch()
        button_row.addWidget(cancel)
        button_row.addWidget(submit)
        layout.addLayout(button_row)
        layout.addStretch()

        self._password_input.returnPressed.connect(self._handle_submit)
        if self._confirm_input:
            self._confirm_input.returnPressed.connect(self._handle_submit)


    def _handle_submit(self) -> None:
        password = self._password_input.text().strip()
        if not password:
            self._status.setText("Please enter a password.")
            return
        if not self._has_password:
            confirm = self._confirm_input.text().strip() if self._confirm_input else ""
            if password != confirm:
                self._status.setText("Passwords do not match.")
                return
            set_master_password(self._service_name, password)
            self.accept()
            return

        if verify_master_password(self._service_name, password):
            self.accept()
        else:
            self._status.setText("Incorrect password.")
