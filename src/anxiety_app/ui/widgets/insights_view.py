from __future__ import annotations

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from anxiety_app.ui.widgets.rounded_scroll_area import RoundedScrollArea

from anxiety_app.domain.entities import DailyLogEntity
from anxiety_app.domain.services import TrackingService
from anxiety_app.services.insights_service import InsightsService


class InsightsWorker(QThread):
    insights_ready = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, insights_service: InsightsService) -> None:
        super().__init__()
        self._insights_service = insights_service

    def run(self) -> None:
        try:
            insight = self._insights_service.generate()
            self.insights_ready.emit(insight.summary_text)
        except Exception as exc:  # pragma: no cover - UI fallback
            self.error.emit(str(exc))


class InsightsView(QWidget):
    def __init__(
        self, insights_service: InsightsService, tracking_service: TrackingService
    ) -> None:
        super().__init__()
        self.setObjectName("ViewRoot")
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._insights_service = insights_service
        self._tracking_service = tracking_service
        self._worker: InsightsWorker | None = None
        self._logs: list[DailyLogEntity] = []

        layout = QVBoxLayout()
        layout.setSpacing(10)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Chart filter"))
        self._filter_combo = QComboBox()
        self._filter_combo.addItems(["All", "Anxiety", "Mood", "Stress"])
        self._filter_combo.currentTextChanged.connect(self._update_chart)
        filter_row.addWidget(self._filter_combo)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        self._chart = TrendChart()
        self._chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._chart_scroll = RoundedScrollArea()
        self._chart_scroll.setWidgetResizable(True)
        self._chart_scroll.setFrameShape(QFrame.NoFrame)
        self._chart_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._chart_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._chart_scroll.setWidget(self._chart)
        layout.addWidget(self._chart_scroll, 1)

        self._insights_text = QTextEdit()
        self._insights_text.setReadOnly(True)
        self._insights_text.setPlaceholderText("Generate insights to see analysis.")
        self._insights_text.setMinimumHeight(380)
        self._insights_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self._insights_text, 1)

        self._generate_button = QPushButton("Generate insights")
        self._generate_button.setObjectName("AccentButton")
        self._generate_button.clicked.connect(self._start_generation)
        layout.addWidget(self._generate_button)
        layout.addStretch()
        self.setLayout(layout)

        cached = self._insights_service.latest_cached()
        if cached:
            self._insights_text.setText(self._clean_insight_text(cached.summary_text))
        self._refresh_logs()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._sync_chart_size()

    def _start_generation(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        self._generate_button.setEnabled(False)
        self._insights_text.setText("Generating insights...")
        self._worker = InsightsWorker(self._insights_service)
        self._worker.insights_ready.connect(self._on_insights_ready)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_insights_ready(self, text: str) -> None:
        self._insights_text.setText(self._clean_insight_text(text))
        self._finalize_worker()

    def _on_error(self, message: str) -> None:
        self._insights_text.setText(f"Unable to generate insights: {message}")
        self._finalize_worker()

    def _finalize_worker(self) -> None:
        if self._worker:
            self._worker.wait(2000)
            self._worker.deleteLater()
            self._worker = None
        self._generate_button.setEnabled(True)

    def _clean_insight_text(self, text: str) -> str:
        cleaned = text.replace("**", "").replace("*", "").strip()
        for label in ["Modules:", "Tracking:", "Tools:"]:
            cleaned = cleaned.replace(label, f"\n{label}\n")
        cleaned = "\n".join(line.strip() for line in cleaned.splitlines()).strip()
        return cleaned

    def _refresh_logs(self) -> None:
        self._logs = list(reversed(self._tracking_service.recent_logs(limit=30)))
        self._update_chart()

    def refresh_view(self) -> None:
        self._refresh_logs()

    def wait_for_worker(self, timeout_ms: int = 3000) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.wait(timeout_ms)
            if self._worker.isRunning():
                self._worker.terminate()
                self._worker.wait(1000)

    def _update_chart(self) -> None:
        metric = self._filter_combo.currentText().lower()
        self._chart.set_data(self._logs, metric)
        self._sync_chart_size()

    def _sync_chart_size(self) -> None:
        viewport = self._chart_scroll.viewport()
        if viewport is None:
            return
        target_width = max(self._chart.computed_min_width(), viewport.width())
        target_height = max(0, viewport.height())
        self._chart.setMinimumWidth(target_width)
        self._chart.setMinimumHeight(target_height)
        self._chart.setMaximumHeight(target_height)

    def reset_view(self) -> None:
        self._insights_text.clear()
        self._logs = []
        self._filter_combo.setCurrentIndex(0)
        self._chart.set_data([], "all")


class TrendChart(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(0)
        self._logs: list[DailyLogEntity] = []
        self._metric = "all"
        self._pixels_per_day = 48
        self._computed_min_width = 520
        self._cache_pixmap: QPixmap | None = None
        self._cache_key: tuple | None = None

    def set_data(self, logs: list[DailyLogEntity], metric: str) -> None:
        self._logs = logs
        self._metric = metric
        self._cache_pixmap = None
        self._cache_key = None
        if logs:
            start_date = min(log.date for log in logs)
            end_date = max(log.date for log in logs)
            start_date = start_date.fromordinal(start_date.toordinal() - 1)
            end_date = end_date.fromordinal(end_date.toordinal() + 1)
            total_days = max((end_date - start_date).days, 1)
            min_width = 200 + (total_days * self._pixels_per_day)
            self._computed_min_width = max(520, min_width)
            self.setMinimumWidth(self._computed_min_width)
        else:
            self._computed_min_width = 520
            self.setMinimumWidth(self._computed_min_width)
        self.update()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._cache_pixmap = None
        self._cache_key = None

    def computed_min_width(self) -> int:
        return self._computed_min_width

    def paintEvent(self, event) -> None:  # type: ignore[override]
        super().paintEvent(event)
        cache_key = self._cache_key_for_current_state()
        if self._cache_pixmap and cache_key == self._cache_key:
            painter = QPainter(self)
            painter.drawPixmap(0, 0, self._cache_pixmap)
            painter.end()
            return

        pixmap = QPixmap(self.size())
        pixmap.fill(self.palette().base().color())
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self._logs:
            painter.setPen(self.palette().text().color())
            painter.drawText(self.rect(), Qt.AlignCenter, "No data yet")
            painter.end()
            self._cache_pixmap = pixmap
            self._cache_key = cache_key
            painter = QPainter(self)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            return

        metrics = ["anxiety", "mood", "stress"]
        if self._metric != "all":
            metrics = [self._metric]

        max_value = 10
        left = 36
        right = 24
        top = 16
        bottom = 56
        width = self.width() - left - right
        height = self.height() - top - bottom
        count = len(self._logs)
        start_date = min(log.date for log in self._logs)
        end_date = max(log.date for log in self._logs)
        total_days = max((end_date - start_date).days, 1)

        colors = {
            "anxiety": QColor("#d47f7f"),
            "mood": QColor("#2f7f77"),
            "stress": QColor("#5f6f9e"),
        }

        axis_pen = QPen(QColor("#5a6b72"), 1)
        painter.setPen(axis_pen)
        painter.drawLine(left, top, left, top + height)
        painter.drawLine(left, top + height, left + width, top + height)

        painter.setPen(QColor("#5a6b72"))
        for tick in range(1, 11):
            y = top + height - (tick / max_value) * height
            painter.drawLine(left - 4, int(y), left, int(y))
            painter.drawText(6, int(y) + 4, str(tick))

        label_indices = max(count // 5, 1)
        used_labels = set()
        for idx, log in enumerate(self._logs):
            if idx % label_indices != 0 and idx != count - 1:
                continue
            x = left + width * (
                (log.date - start_date).days / float(total_days)
            )
            label = log.date.strftime("%m/%d")
            if label in used_labels:
                continue
            used_labels.add(label)
            text_width = 40
            x = min(max(x, left + text_width / 2), left + width - text_width / 2)
            painter.drawLine(int(x), top + height, int(x), top + height + 4)
            painter.drawText(int(x) - 18, top + height + 20, label)

        for metric in metrics:
            pen = QPen(colors.get(metric, QColor("#5aa6a0")), 2)
            painter.setPen(pen)
            points = []
            for index, log in enumerate(self._logs):
                value = getattr(log, metric, 0)
                x = left + width * (
                    (log.date - start_date).days / float(total_days)
                )
                y = top + height - (value / max_value) * height
                points.append((x, y))
            for i in range(len(points) - 1):
                painter.drawLine(
                    int(points[i][0]),
                    int(points[i][1]),
                    int(points[i + 1][0]),
                    int(points[i + 1][1]),
                )
            for point in points:
                painter.drawEllipse(int(point[0]) - 2, int(point[1]) - 2, 4, 4)

        if self._metric == "all":
            legend_y = top + 8
            legend_x = left + 100
            for metric in ["mood", "stress", "anxiety"]:
                color = colors.get(metric, QColor("#5aa6a0"))
                painter.setPen(QPen(color, 3))
                painter.drawLine(legend_x, legend_y, legend_x + 18, legend_y)
                painter.setPen(QColor("#445056"))
                painter.drawText(legend_x + 24, legend_y + 4, metric.capitalize())
                legend_x += 90

        painter.end()
        self._cache_pixmap = pixmap
        self._cache_key = cache_key
        painter = QPainter(self)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

    def _cache_key_for_current_state(self) -> tuple:
        log_key = tuple(
            (log.date.toordinal(), log.mood, log.anxiety, log.stress)
            for log in self._logs
        )
        return (self.width(), self.height(), self._metric, log_key)
