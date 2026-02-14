from __future__ import annotations

from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)


class Toast(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self._frame = QFrame(self)
        self._frame.setObjectName("Toast")
        self._frame.setProperty("tone", "info")

        self._label = QLabel("")
        self._label.setObjectName("ToastLabel")
        self._label.setWordWrap(True)

        self._close_button = QPushButton("×")
        self._close_button.setObjectName("ToastClose")
        self._close_button.setFixedSize(24, 24)
        self._close_button.clicked.connect(self._close_toast)

        self._progress = QProgressBar()
        self._progress.setObjectName("ToastProgress")
        self._progress.setRange(0, 100)
        self._progress.setValue(100)
        self._progress.setTextVisible(False)

        content_layout = QVBoxLayout(self._frame)
        content_layout.setContentsMargins(14, 12, 14, 12)
        content_layout.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.addWidget(self._label)
        top_row.addStretch()
        top_row.addWidget(self._close_button)
        content_layout.addLayout(top_row)
        content_layout.addWidget(self._progress)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._frame)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)
        self._tick = QTimer(self)
        self._tick.timeout.connect(self._on_tick)
        self._min_duration_ms = 3000
        self._duration_ms = self._min_duration_ms
        self._remaining_ms = self._min_duration_ms
        self._active_id = 0

    def show_message(self, text: str, tone: str = "info", duration_ms: int = 3200) -> None:
        self._active_id += 1
        active_id = self._active_id
        self._timer.stop()
        self._tick.stop()
        self._frame.setProperty("tone", tone)
        self._frame.setStyleSheet("")
        self._progress.setProperty("tone", tone)
        self._progress.setStyleSheet("")
        self._label.setText(text)
        self._frame.setMinimumWidth(320)
        self.adjustSize()
        self._position()
        self.show()
        self._duration_ms = max(duration_ms, self._min_duration_ms)
        self._remaining_ms = self._duration_ms
        self._progress.setValue(100)
        self._timer.start(self._duration_ms)
        self._tick.start(50)
        self._timer_id = active_id

    def _close_toast(self) -> None:
        self._timer.stop()
        self._tick.stop()
        self.hide()

    def _on_timeout(self) -> None:
        if getattr(self, "_timer_id", None) != self._active_id:
            return
        self._close_toast()

    def _on_tick(self) -> None:
        self._remaining_ms = max(0, self._remaining_ms - 50)
        if self._duration_ms > 0:
            pct = int((self._remaining_ms / self._duration_ms) * 100)
            self._progress.setValue(pct)
        if self._remaining_ms <= 0:
            self._tick.stop()

    def _position(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            cursor_pos = QCursor.pos()
            self.move(cursor_pos + QPoint(12, 12))
            return
        top_left = parent.mapToGlobal(QPoint(0, 0))
        margin = 16
        x = top_left.x() + parent.width() - self.width() - margin
        y = top_left.y() + margin
        self.move(x, y)
