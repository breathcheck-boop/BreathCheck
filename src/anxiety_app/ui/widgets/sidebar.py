from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt5.QtWidgets import QButtonGroup, QLabel, QPushButton, QVBoxLayout, QWidget


class Sidebar(QWidget):
    page_selected = pyqtSignal(int)
    logout_requested = pyqtSignal()

    def __init__(self, pages: list[str]) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(6)

        logo = QLabel()
        logo.setPixmap(self._load_logo_pixmap(64))
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        layout.addSpacing(6)

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)
        for index, label in enumerate(pages):
            button = QPushButton(label)
            button.setCheckable(True)
            button.setObjectName("SidebarButton")
            button.setIcon(self._icon_for_label(label))
            button.setIconSize(QSize(16, 16))
            if index == 0:
                button.setChecked(True)
            self._button_group.addButton(button, index)
            layout.addWidget(button)
        layout.addStretch()
        logout_button = QPushButton("Logout")
        logout_button.setObjectName("SidebarButton")
        logout_button.setIcon(self._icon_for_label("Logout"))
        logout_button.setIconSize(QSize(16, 16))
        logout_button.clicked.connect(self.logout_requested.emit)
        layout.addWidget(logout_button)
        self.setLayout(layout)

        self._button_group.idClicked.connect(self.page_selected.emit)

    def set_current(self, index: int) -> None:
        button = self._button_group.button(index)
        if button:
            button.setChecked(True)

    def _icon_for_label(self, label: str) -> QIcon:
        colors = {
            "Home": "#4B9C7D",
            "Learn": "#2f7f77",
            "Tools": "#5f6f9e",
            "Progress": "#7bb7b1",
            "Support": "#7FAFD4",
            "Settings": "#6a7a7f",
            "Logout": "#c26464",
        }
        color = colors.get(label, "#5aa6a0")
        pixmap = QPixmap(14, 14)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(1, 1, 12, 12)
        painter.end()
        return QIcon(pixmap)

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
        return self._build_logo_pixmap(size)

    def _build_logo_pixmap(self, size: int) -> QPixmap:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor("#5aa6a0"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(6, 6, size - 12, size - 12)
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(18, 18, 10, 10)
        painter.end()
        return pixmap
