from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from anxiety_app.ui.widgets.rounded_scroll_area import RoundedScrollArea


class AboutView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("ViewRoot")
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        scroll = RoundedScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName("ScrollContent")
        content.setAutoFillBackground(True)
        content.setAttribute(Qt.WA_StyledBackground, True)
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(12)

        content_layout.addWidget(self._section("Overview", [
            "BreathCheck is a calm, local-first companion for anxiety support.",
            "It combines CBT-style learning, daily tracking, and guided tools.",
        ]))

        content_layout.addWidget(self._section("Core features", [
            "10 learning modules (Module 1 fully implemented).",
            "Daily tracking for mood, anxiety, stress, and notes.",
            "Guided tools: breathing, grounding, thought log, worry time, safe place.",
            "Progress streaks and milestone badges.",
            "Optional AI insights and tool feedback.",
        ]))

        content_layout.addWidget(self._section("Privacy & security", [
            "Your data stays on this device.",
            "Sensitive fields are encrypted locally using a key stored in your system keyring.",
            "No network calls happen unless you enable AI insights or tool feedback.",
        ]))

        content_layout.addWidget(self._section("Keyboard shortcuts", [
            "Ctrl+1 Home",
            "Ctrl+2 Learn",
            "Ctrl+3 Track",
            "Ctrl+4 Insights",
            "Ctrl+5 Progress",
            "Ctrl+6 Tools",
            "Ctrl+7 Contact",
            "Ctrl+8 About",
            "Ctrl+9 Settings",
        ]))

        feedback_card = QFrame()
        feedback_card.setObjectName("Card")
        feedback_layout = QVBoxLayout(feedback_card)
        feedback_title = QLabel("Send Feedback")
        feedback_title.setObjectName("CardTitle")
        feedback_layout.addWidget(feedback_title)
        feedback_layout.addWidget(
            QLabel("Have suggestions or ideas? We’d love to hear from you.")
        )
        feedback_button = QPushButton("Send Feedback")
        feedback_button.setObjectName("AccentButton")
        feedback_button.clicked.connect(self._send_feedback)
        feedback_layout.addWidget(feedback_button, 0, Qt.AlignLeft)
        content_layout.addWidget(feedback_card)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

    def _section(self, title: str, bullets: list[str]) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        header = QLabel(title)
        header.setObjectName("CardTitle")
        layout.addWidget(header)
        for bullet in bullets:
            label = QLabel(f"• {bullet}")
            label.setWordWrap(True)
            layout.addWidget(label)
        return card

    def _send_feedback(self) -> None:
        QMessageBox.information(
            self,
            "Send Feedback",
            "Please send feedback to feedback@breathcheck.app",
        )
