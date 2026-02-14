from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class CardFrame(QFrame):
    """Shared lightweight card container used across views."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        margins: tuple[int, int, int, int] = (12, 12, 12, 12),
        spacing: int = 8,
        minimum_height: int = 0,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        if minimum_height > 0:
            self.setMinimumHeight(minimum_height)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(*margins)
        self._layout.setSpacing(spacing)

    @property
    def content_layout(self) -> QVBoxLayout:
        return self._layout


class CompactCard(CardFrame):
    """Compact standard card pattern for list/grid items."""

    def __init__(
        self,
        title: str,
        description: str,
        *,
        icon_text: str = "",
        status_text: str = "",
        minimum_height: int = 0,
        icon_min_height: int = 36,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent, minimum_height=minimum_height)

        self.icon_label = QLabel(icon_text)
        self.icon_label.setObjectName("CardMeta")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setMinimumHeight(icon_min_height)
        self.content_layout.addWidget(self.icon_label)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("CardTitle")
        self.title_label.setWordWrap(True)
        self.content_layout.addWidget(self.title_label)

        self.description_label = QLabel(description)
        self.description_label.setObjectName("CardMeta")
        self.description_label.setWordWrap(True)
        self.content_layout.addWidget(self.description_label)

        self.status_label = QLabel(status_text)
        self.status_label.setObjectName("CardMeta")
        self.status_label.setWordWrap(True)
        self.status_label.setVisible(bool(status_text))
        self.content_layout.addWidget(self.status_label)

        self.button_row = QHBoxLayout()
        self.button_row.setSpacing(8)
        self.button_row.setContentsMargins(0, 0, 0, 0)
        self.content_layout.addLayout(self.button_row)

    def set_status_text(self, value: str) -> None:
        self.status_label.setText(value)
        self.status_label.setVisible(bool(value))

    def add_button(
        self,
        text: str,
        callback=None,
        *,
        enabled: bool = True,
        object_name: str | None = None,
    ) -> QPushButton:
        button = QPushButton(text)
        if object_name:
            button.setObjectName(object_name)
        button.setEnabled(enabled)
        if callback is not None:
            button.clicked.connect(callback)
        self.button_row.addWidget(button)
        return button


def clear_layout(layout: QLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        child_layout = item.layout()
        if child_layout is not None:
            clear_layout(child_layout)
        if widget is not None:
            widget.deleteLater()
