from __future__ import annotations

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from pathlib import Path

from PyQt5.QtGui import QColor, QLinearGradient, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class _HomeCarousel(QWidget):
    def __init__(self, slides: list[tuple[str, str]]) -> None:
        super().__init__()
        self.setObjectName("Card")
        self._slides = slides
        self._index = 0

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self._stack = QStackedWidget()
        for title, body in slides:
            page = QWidget()
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(6, 6, 6, 6)
            page_layout.setSpacing(6)
            title_label = QLabel(title)
            title_label.setObjectName("CardTitle")
            body_label = QLabel(body)
            body_label.setWordWrap(True)
            body_label.setObjectName("CardMeta")
            page_layout.addStretch()
            page_layout.addWidget(title_label, alignment=Qt.AlignCenter)
            page_layout.addWidget(body_label, alignment=Qt.AlignCenter)
            page_layout.addStretch()
            self._stack.addWidget(page)
        layout.addWidget(self._stack)

        nav = QHBoxLayout()
        self._prev_btn = QPushButton("Prev")
        self._prev_btn.clicked.connect(self._prev)
        self._next_btn = QPushButton("Next")
        self._next_btn.setObjectName("AccentButton")
        self._next_btn.clicked.connect(self._next)
        nav.addWidget(self._prev_btn)
        nav.addStretch()

        self._dot_labels: list[QLabel] = []
        for i in range(len(slides)):
            dot = QLabel("●" if i == 0 else "○")
            dot.setObjectName("StepDot")
            self._dot_labels.append(dot)
            nav.addWidget(dot)
        nav.addStretch()
        nav.addWidget(self._next_btn)
        layout.addLayout(nav)

        self._timer = QTimer(self)
        self._timer.setInterval(4500)
        self._timer.timeout.connect(self._next)
        self._timer.start()

    def _next(self) -> None:
        self._index = (self._index + 1) % len(self._slides)
        self._set_index(self._index)

    def _prev(self) -> None:
        self._index = (self._index - 1) % len(self._slides)
        self._set_index(self._index)

    def _set_index(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        for i, dot in enumerate(self._dot_labels):
            dot.setText("●" if i == index else "○")


class HomeView(QWidget):
    start_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("ViewRoot")
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setSpacing(24)
        content_layout.setContentsMargins(0, 0, 0, 0)

        left_col = QWidget()
        left_layout = QVBoxLayout(left_col)
        left_layout.setSpacing(12)

        logo = QLabel()
        logo.setPixmap(self._load_logo_pixmap(220))
        logo.setFixedHeight(220)
        logo.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(logo)

        summary_card = QFrame()
        summary_card.setObjectName("Card")
        summary_layout = QVBoxLayout(summary_card)
        summary_title = QLabel("BreathCheck")
        summary_title.setObjectName("CardTitle")
        summary_layout.addWidget(summary_title)
        summary_text = QLabel(
            "BreathCheck is a self-help CBT-based anxiety program for structured learning, "
            "daily coping practice, and steady progress."
        )
        summary_text.setWordWrap(True)
        summary_layout.addWidget(summary_text)
        left_layout.addWidget(summary_card)

        disclaimer_card = QFrame()
        disclaimer_card.setObjectName("Card")
        disclaimer_layout = QVBoxLayout(disclaimer_card)
        disclaimer_title = QLabel("Important")
        disclaimer_title.setObjectName("CardTitle")
        disclaimer_layout.addWidget(disclaimer_title)
        disclaimer_text = QLabel(
            "BreathCheck is not a substitute for professional care. "
            "If you feel unsafe, seek emergency support. Your data is stored locally on your device."
        )
        disclaimer_text.setWordWrap(True)
        disclaimer_layout.addWidget(disclaimer_text)
        left_layout.addWidget(disclaimer_card)

        start_button = QPushButton("Start")
        start_button.setObjectName("AccentButton")
        start_button.clicked.connect(self.start_requested.emit)
        left_layout.addWidget(start_button, 0, Qt.AlignLeft)
        left_layout.addStretch()

        right_col = QWidget()
        right_layout = QVBoxLayout(right_col)
        right_layout.setSpacing(12)

        slides = [
            ("Learn", "Follow weekly modules step-by-step and complete them in sequence."),
            ("Tools", "Use BreathCheck breathing and Thought Log for quick coping."),
            ("Progress", "Track streaks, milestones, and overall completion."),
            ("Privacy", "Your data stays on your device and is encrypted at rest."),
        ]
        right_layout.addWidget(_HomeCarousel(slides))
        right_layout.addStretch()

        content_layout.addWidget(left_col, 1)
        content_layout.addWidget(right_col, 1)
        layout.addWidget(content, 1)

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
        gradient = QLinearGradient(0, 0, size, size)
        gradient.setColorAt(0.0, QColor("#5aa6a0"))
        gradient.setColorAt(1.0, QColor("#2f7f77"))
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(6, 6, size - 12, size - 12)

        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(26, 26, 12, 12)
        painter.drawEllipse(46, 44, 12, 12)
        painter.end()
        return pixmap
