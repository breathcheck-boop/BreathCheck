from __future__ import annotations

from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from anxiety_app.core.security import set_master_password, verify_master_password


class ChangePasswordDialog(QDialog):
    def __init__(self, service_name: str) -> None:
        super().__init__()
        self._service_name = service_name
        self.setWindowTitle("Change Master Password")
        self.setModal(True)

        layout = QVBoxLayout(self)
        title = QLabel("Change master password")
        title.setObjectName("Title")
        layout.addWidget(title)

        form = QFormLayout()
        self._current_input = QLineEdit()
        self._current_input.setEchoMode(QLineEdit.Password)
        self._new_input = QLineEdit()
        self._new_input.setEchoMode(QLineEdit.Password)
        self._confirm_input = QLineEdit()
        self._confirm_input.setEchoMode(QLineEdit.Password)

        form.addRow("Current", self._current_input)
        form.addRow("New", self._new_input)
        form.addRow("Confirm", self._confirm_input)
        layout.addLayout(form)

        self._status = QLabel("")
        layout.addWidget(self._status)

        submit = QPushButton("Update password")
        submit.setObjectName("AccentButton")
        submit.clicked.connect(self._handle_submit)
        layout.addWidget(submit)

    def _handle_submit(self) -> None:
        current = self._current_input.text().strip()
        new = self._new_input.text().strip()
        confirm = self._confirm_input.text().strip()
        if not current or not new:
            self._status.setText("Please fill out all fields.")
            return
        if new != confirm:
            self._status.setText("New passwords do not match.")
            return
        if not verify_master_password(self._service_name, current):
            self._status.setText("Current password is incorrect.")
            return
        set_master_password(self._service_name, new)
        self.accept()
