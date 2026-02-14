from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from anxiety_app.domain.entities import MilestoneStatus
from anxiety_app.domain.services import ProgressService
from anxiety_app.ui.widgets.learn_view import MODULES
from anxiety_app.ui.widgets.card_widgets import CardFrame, clear_layout
from anxiety_app.ui.widgets.rounded_scroll_area import RoundedScrollArea


class ProgressView(QWidget):
    milestone_achieved = pyqtSignal(str)

    def __init__(self, progress_service: ProgressService) -> None:
        super().__init__()
        self.setObjectName("ViewRoot")
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._progress_service = progress_service
        self._completed_milestones: set[str] = set()
        self._milestones_initialized = False
        self._milestone_pixmaps: dict[int, QPixmap | None] = {}
        self._last_milestone_state: list[tuple[str, str, bool, bool, str]] = []

        layout = QVBoxLayout()
        layout.setSpacing(10)

        summary_card = CardFrame()
        summary_layout = summary_card.content_layout

        summary_layout.addWidget(QLabel("Program completion"))
        self._completion_bar = QProgressBar()
        self._completion_label = QLabel("0/6 modules complete")
        self._completion_label.setObjectName("CardMeta")
        summary_layout.addWidget(self._completion_bar)
        summary_layout.addWidget(self._completion_label)

        summary_layout.addWidget(QLabel("Weekly engagement"))
        self._weekly_bar = QProgressBar()
        self._weekly_bar.setRange(0, 7)
        self._engagement_label = QLabel("Active days: 0/7")
        self._engagement_label.setObjectName("CardMeta")
        summary_layout.addWidget(self._weekly_bar)
        summary_layout.addWidget(self._engagement_label)

        summary_layout.addWidget(QLabel("Streak"))
        self._streak_label = QLabel("Streak: 0 days")
        self._streak_label.setObjectName("CardMeta")
        summary_layout.addWidget(self._streak_label)

        summary_layout.addWidget(QLabel("Tool usage"))
        self._tool_usage_label = QLabel("BreathCheck sessions: 0 · Thought logs: 0")
        self._tool_usage_label.setObjectName("CardMeta")
        summary_layout.addWidget(self._tool_usage_label)

        layout.addWidget(summary_card)

        achievements_label = QLabel("Milestones")
        achievements_label.setObjectName("CardTitle")
        layout.addWidget(achievements_label)

        self._achievements_widget = QWidget()
        self._achievements_widget.setObjectName("ScrollContent")
        self._achievements_widget.setAutoFillBackground(True)
        self._achievements_widget.setAttribute(Qt.WA_StyledBackground, True)
        self._achievements_container = QGridLayout(self._achievements_widget)
        self._achievements_container.setHorizontalSpacing(14)
        self._achievements_container.setVerticalSpacing(14)

        self._achievements_scroll = RoundedScrollArea()
        self._achievements_scroll.setWidgetResizable(True)
        self._achievements_scroll.setFrameShape(QFrame.NoFrame)
        self._achievements_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self._achievements_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._achievements_scroll.setWidget(self._achievements_widget)
        layout.addWidget(self._achievements_scroll, 1)

        self.setLayout(layout)
        self.refresh()

    def refresh(self) -> None:
        module_ids = [module["id"] for module in MODULES]
        completion = self._progress_service.program_completion(module_ids)
        engagement = self._progress_service.engagement_summary()
        usage = self._progress_service.tool_usage_summary()

        self._completion_bar.setValue(completion.percent_complete)
        self._completion_label.setText(
            f"{completion.completed_modules}/{completion.total_modules} modules complete • {completion.percent_complete}%"
        )
        self._weekly_bar.setValue(engagement.active_days)
        self._engagement_label.setText(f"Active days: {engagement.active_days}/7")
        self._streak_label.setText(f"Streak: {engagement.streak_days} days")
        self._tool_usage_label.setText(
            f"BreathCheck sessions: {usage.breathcheck_sessions} · "
            f"Thought logs: {usage.thought_log_entries}"
        )

        milestones = self._progress_service.milestone_statuses(module_ids)
        items = [
            (
                m.title,
                m.description,
                m.achieved,
                m.locked,
                m.completed_at.isoformat() if m.completed_at else "",
            )
            for m in milestones
        ]
        if items != self._last_milestone_state:
            self._last_milestone_state = list(items)
            self._render_achievements(milestones)

    def reset_view(self) -> None:
        self.refresh()

    def _render_achievements(self, items: list[MilestoneStatus]) -> None:
        self._achievements_widget.setUpdatesEnabled(False)
        completed_now = {item.title for item in items if item.achieved}
        if not self._milestones_initialized:
            self._completed_milestones = completed_now
            self._milestones_initialized = True
        else:
            newly_completed = completed_now - self._completed_milestones
            self._completed_milestones = completed_now
            for title in newly_completed:
                self.milestone_achieved.emit(title)

        clear_layout(self._achievements_container)

        for index, item in enumerate(items):
            card = CardFrame(minimum_height=180)
            card.setProperty("milestone", "completed" if item.achieved else "pending")
            card_layout = card.content_layout
            card_layout.setSpacing(6)

            icon = QLabel("")
            icon.setAlignment(Qt.AlignCenter)
            icon.setMinimumHeight(56)
            pixmap = self._load_milestone_pixmap(index + 1)
            if pixmap:
                icon.setPixmap(pixmap)
            else:
                icon.setText("Badge")

            title_label = QLabel(item.title)
            title_label.setObjectName("CardTitle")
            title_label.setAlignment(Qt.AlignCenter)

            desc = QLabel(item.description)
            desc.setObjectName("CardMeta")
            desc.setWordWrap(True)
            desc.setAlignment(Qt.AlignCenter)
            state = "Locked" if item.locked else ("Complete" if item.achieved else "Unlocked")
            state_label = QLabel(f"Status: {state}")
            state_label.setObjectName("CardMeta")
            state_label.setAlignment(Qt.AlignCenter)
            completed_label = QLabel(
                f"Completed: {item.completed_at.strftime('%Y-%m-%d')}"
                if item.completed_at
                else "Completed: -"
            )
            completed_label.setObjectName("CardMeta")
            completed_label.setAlignment(Qt.AlignCenter)

            card_layout.addWidget(icon)
            card_layout.addWidget(title_label)
            card_layout.addWidget(desc)
            card_layout.addWidget(state_label)
            card_layout.addWidget(completed_label)

            row = index // 2
            col = index % 2
            self._achievements_container.addWidget(card, row, col)

        placeholder = CardFrame()
        placeholder_layout = placeholder.content_layout
        placeholder_label = QLabel("More milestones coming soon.")
        placeholder_label.setObjectName("CardMeta")
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet("font-weight: 600;")
        placeholder_layout.addWidget(placeholder_label)
        row = len(items) // 2
        col = len(items) % 2
        self._achievements_container.addWidget(placeholder, row, col)

        self._achievements_widget.setUpdatesEnabled(True)

    def _load_milestone_pixmap(self, index: int) -> QPixmap | None:
        if index in self._milestone_pixmaps:
            return self._milestone_pixmaps[index]
        base = Path(__file__).resolve().parent.parent / "resources" / "milestones"
        for ext in (".webp", ".png", ".jpg", ".jpeg"):
            path = base / f"{index}{ext}"
            if not path.exists():
                continue
            pixmap = QPixmap(str(path))
            if pixmap.isNull():
                continue
            scaled = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._milestone_pixmaps[index] = scaled
            return scaled
        self._milestone_pixmaps[index] = None
        return None
