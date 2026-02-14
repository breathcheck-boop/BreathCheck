from __future__ import annotations

from datetime import datetime

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QSlider,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QGridLayout,
    QSizePolicy,
)

from anxiety_app.ui.widgets.rounded_scroll_area import RoundedScrollArea
from anxiety_app.domain.services import TrackingService


class TrackView(QWidget):
    log_saved = pyqtSignal(str)

    def __init__(self, tracking_service: TrackingService) -> None:
        super().__init__()
        self.setObjectName("ViewRoot")
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._tracking_service = tracking_service
        self._recent_key: list[tuple[int, str]] = []

        layout = QVBoxLayout()
        layout.setSpacing(10)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)

        form_row = QHBoxLayout()
        sliders_col = QVBoxLayout()
        sliders_col.setSpacing(10)
        form_row.addLayout(sliders_col, 1)

        mood_row = QHBoxLayout()
        mood_icon = self._icon_label("#2f7f77")
        mood_label = QLabel("Mood")
        mood_label.setMinimumWidth(120)
        self._mood_slider = QSlider(Qt.Horizontal)
        self._mood_slider.setRange(0, 10)
        self._mood_slider.setValue(5)
        self._mood_slider.setTickPosition(QSlider.TicksBelow)
        self._mood_slider.setTickInterval(1)
        self._mood_value = QLabel("5")
        self._mood_value.setMinimumWidth(24)
        self._mood_slider.valueChanged.connect(
            lambda value: self._mood_value.setText(str(value))
        )
        mood_row.addWidget(mood_icon)
        mood_row.addWidget(mood_label)
        mood_row.addWidget(self._mood_slider)
        mood_row.addWidget(self._mood_value)
        sliders_col.addLayout(mood_row)

        anxiety_row = QHBoxLayout()
        anxiety_icon = self._icon_label("#d47f7f")
        anxiety_label = QLabel("Anxiety")
        anxiety_label.setMinimumWidth(120)
        self._anxiety_slider = QSlider(Qt.Horizontal)
        self._anxiety_slider.setRange(0, 10)
        self._anxiety_slider.setValue(5)
        self._anxiety_slider.setTickPosition(QSlider.TicksBelow)
        self._anxiety_slider.setTickInterval(1)
        self._anxiety_value = QLabel("5")
        self._anxiety_value.setMinimumWidth(24)
        self._anxiety_slider.valueChanged.connect(
            lambda value: self._anxiety_value.setText(str(value))
        )
        anxiety_row.addWidget(anxiety_icon)
        anxiety_row.addWidget(anxiety_label)
        anxiety_row.addWidget(self._anxiety_slider)
        anxiety_row.addWidget(self._anxiety_value)
        sliders_col.addLayout(anxiety_row)

        stress_row = QHBoxLayout()
        stress_icon = self._icon_label("#5f6f9e")
        stress_label = QLabel("Stress")
        stress_label.setMinimumWidth(120)
        self._stress_slider = QSlider(Qt.Horizontal)
        self._stress_slider.setRange(0, 10)
        self._stress_slider.setValue(5)
        self._stress_slider.setTickPosition(QSlider.TicksBelow)
        self._stress_slider.setTickInterval(1)
        self._stress_value = QLabel("5")
        self._stress_value.setMinimumWidth(24)
        self._stress_slider.valueChanged.connect(
            lambda value: self._stress_value.setText(str(value))
        )
        stress_row.addWidget(stress_icon)
        stress_row.addWidget(stress_label)
        stress_row.addWidget(self._stress_slider)
        stress_row.addWidget(self._stress_value)
        sliders_col.addLayout(stress_row)

        trigger_col = QVBoxLayout()
        trigger_header = QHBoxLayout()
        trigger_icon = self._icon_label("#6a7a7f")
        trigger_label = QLabel("Trigger / Context")
        trigger_header.addWidget(trigger_icon)
        trigger_header.addWidget(trigger_label)
        trigger_header.addStretch()
        self._trigger_input = QTextEdit()
        self._trigger_input.setPlaceholderText("Optional notes")
        self._trigger_input.setMinimumHeight(120)
        trigger_col.addLayout(trigger_header)
        trigger_col.addWidget(self._trigger_input)
        form_row.addLayout(trigger_col, 1)

        card_layout.addLayout(form_row)

        self._save_button = QPushButton("Save entry")
        self._save_button.setObjectName("AccentButton")
        self._save_button.clicked.connect(self._save_entry)
        self._status_label = QLabel("")

        card_layout.addWidget(self._save_button)
        card_layout.addWidget(self._status_label)

        layout.addWidget(card)

        recent_label = QLabel("Recent entries")
        layout.addWidget(recent_label)
        self._entries_area = RoundedScrollArea()
        self._entries_area.setWidgetResizable(True)
        self._entries_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self._entries_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._entries_container = QWidget()
        self._entries_container.setObjectName("ScrollContent")
        self._entries_container.setAutoFillBackground(True)
        self._entries_container.setAttribute(Qt.WA_StyledBackground, True)
        self._entries_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._entries_layout = QGridLayout(self._entries_container)
        self._entries_layout.setSpacing(12)
        self._entries_layout.setAlignment(Qt.AlignTop)
        for col in range(2):
            self._entries_layout.setColumnStretch(col, 1)
        self._entries_area.setWidget(self._entries_container)
        layout.addWidget(self._entries_area, 1)
        self.setLayout(layout)

        self.refresh_recent()

    def _icon_label(self, color: str) -> QLabel:
        size = 12
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, size - 1, size - 1)
        painter.end()
        label = QLabel()
        label.setPixmap(pixmap)
        label.setFixedSize(size, size)
        return label

    def _save_entry(self) -> None:
        entry_time = datetime.now()
        log_date = entry_time.date()
        mood = self._mood_slider.value()
        anxiety = self._anxiety_slider.value()
        stress = self._stress_slider.value()
        trigger = self._trigger_input.toPlainText().strip()
        existing = self._tracking_service.get_daily_log(log_date)
        if existing:
            result = QMessageBox.question(
                self,
                "Update today's entry?",
                "An entry already exists for today. Do you want to update it?",
            )
            if result != QMessageBox.Yes:
                return
        entry, created = self._tracking_service.create_or_update_daily_log(
            log_date, mood, anxiety, stress, trigger, entry_time
        )
        message = "Entry saved." if created else "Entry updated for this date."
        self._status_label.setText(message)
        self._trigger_input.clear()
        self.refresh_recent()
        self.log_saved.emit(message)

    def refresh_recent(self) -> None:
        entries = self._tracking_service.recent_logs(limit=6)
        key = [
            (log.id, log.updated_at.isoformat() if log.updated_at else "")
            for log in entries
        ]
        if key == self._recent_key:
            return
        self._recent_key = key
        self.setUpdatesEnabled(False)
        while self._entries_layout.count():
            item = self._entries_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for index, log in enumerate(entries):
            row = index // 2
            col = index % 2
            self._entries_layout.addWidget(self._build_entry_card(log), row, col)
        self.setUpdatesEnabled(True)

    def _build_entry_card(self, log) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QVBoxLayout(card)
        layout.setSpacing(10)

        time_value = log.entry_time or log.created_at
        time_text = time_value.strftime("%I:%M %p").lstrip("0") if time_value else "--:--"
        date_text = log.date.strftime("%b %d, %Y")
        date_label = QLabel(f"{date_text} • {time_text}")
        date_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(date_label)

        bars_layout = QHBoxLayout()
        bars_layout.setSpacing(10)
        for name, value, object_name in [
            ("Mood", log.mood, "MoodBar"),
            ("Anxiety", log.anxiety, "AnxietyBar"),
            ("Stress", log.stress, "StressBar"),
        ]:
            bar_box = QVBoxLayout()
            bar = QProgressBar()
            bar.setRange(0, 10)
            bar.setValue(value)
            bar.setTextVisible(False)
            bar.setOrientation(Qt.Vertical)
            bar.setObjectName(object_name)
            bar.setFixedSize(18, 80)
            label = QLabel(f"{name} {value}")
            label.setAlignment(Qt.AlignCenter)
            bar_box.addWidget(bar, 0, Qt.AlignCenter)
            bar_box.addWidget(label)
            bars_layout.addLayout(bar_box)
        layout.addLayout(bars_layout)

        notes = QTextEdit()
        notes.setReadOnly(True)
        notes.setMinimumHeight(70)
        notes.setMaximumHeight(90)
        notes.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        notes.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        notes.setText(log.trigger if log.trigger else "Notes: -")
        layout.addWidget(notes)
        return card

    def reset_view(self) -> None:
        self._status_label.clear()
        self._trigger_input.clear()
        self._mood_slider.setValue(5)
        self._anxiety_slider.setValue(5)
        self._stress_slider.setValue(5)
        self.refresh_recent()
