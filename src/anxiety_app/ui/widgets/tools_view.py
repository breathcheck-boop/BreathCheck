from __future__ import annotations

from datetime import datetime, timezone

from PyQt5.QtCore import QObject, Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from anxiety_app.domain.services import ToolService, ToolUsageService
from anxiety_app.services.tool_feedback_service import ToolFeedbackService
from anxiety_app.ui.widgets.card_widgets import CardFrame, clear_layout
from anxiety_app.ui.widgets.rounded_scroll_area import RoundedScrollArea


class BreathCheckWidget(QFrame):
    session_stopped = pyqtSignal(int)
    session_completed = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Card")
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("BreathCheck")
        title.setObjectName("CardTitle")
        layout.addWidget(title)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        controls.setContentsMargins(0, 0, 0, 0)

        controls.addWidget(QLabel("Pace"))
        self._pace_combo = QComboBox()
        self._pace_combo.setMinimumWidth(170)
        self._pace_combo.setMaximumWidth(220)
        self._pace_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self._pace_combo.setEditable(True)
        self._pace_combo.lineEdit().setReadOnly(True)
        self._pace_combo.lineEdit().setAlignment(Qt.AlignCenter)
        self._pace_combo.addItems(["4-4-4-4", "4-4-6-2", "5-5-5-5"])
        for i in range(self._pace_combo.count()):
            self._pace_combo.setItemData(i, Qt.AlignCenter, Qt.TextAlignmentRole)
        self._pace_combo.currentTextChanged.connect(self._on_pace_changed)
        controls.addWidget(self._pace_combo)

        controls.addWidget(QLabel("Duration"))
        self._duration_combo = QComboBox()
        self._duration_combo.setMinimumWidth(170)
        self._duration_combo.setMaximumWidth(220)
        self._duration_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self._duration_combo.setEditable(True)
        self._duration_combo.lineEdit().setReadOnly(True)
        self._duration_combo.lineEdit().setAlignment(Qt.AlignCenter)
        self._duration_combo.addItems(["Open-ended", "1 min", "2 min", "5 min"])
        for i in range(self._duration_combo.count()):
            self._duration_combo.setItemData(i, Qt.AlignCenter, Qt.TextAlignmentRole)
        self._duration_combo.currentTextChanged.connect(self._on_duration_changed)
        controls.addWidget(self._duration_combo)

        self._phase_label = QLabel("Ready")
        self._phase_label.setObjectName("CardMeta")
        self._phase_label.setAlignment(Qt.AlignCenter)
        self._phase_label.setMinimumWidth(90)
        controls.addWidget(self._phase_label)

        self._elapsed_label = QLabel("00:00")
        self._elapsed_label.setObjectName("CardMeta")
        self._elapsed_label.setAlignment(Qt.AlignCenter)
        self._elapsed_label.setMinimumWidth(64)
        controls.addWidget(self._elapsed_label)

        self._toggle_btn = QPushButton("Start")
        self._toggle_btn.setObjectName("AccentButton")
        self._toggle_btn.clicked.connect(self._toggle)
        controls.addWidget(self._toggle_btn)
        controls.addStretch()
        layout.addLayout(controls)

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

        self._playing = False
        self._elapsed_seconds = 0
        self._phase_elapsed = 0
        self._phase_index = 0
        self._duration_seconds: int | None = None
        self._phases = [
            ("Inhale", 4),
            ("Hold", 4),
            ("Exhale", 4),
            ("Hold", 4),
        ]

        self._on_pace_changed(self._pace_combo.currentText())
        self._on_duration_changed(self._duration_combo.currentText())

    def is_playing(self) -> bool:
        return self._playing

    def current_pace(self) -> str:
        return self._pace_combo.currentText()

    def current_duration_label(self) -> str:
        return self._duration_combo.currentText()

    def reset(self) -> None:
        self._timer.stop()
        self._playing = False
        self._elapsed_seconds = 0
        self._phase_elapsed = 0
        self._phase_index = 0
        self._phase_label.setText("Ready")
        self._elapsed_label.setText("00:00")
        self._toggle_btn.setText("Start")

    def stop_session(self) -> None:
        if self._playing:
            self._stop(manual=True)

    def _on_pace_changed(self, value: str) -> None:
        mapping = {
            "4-4-4-4": [4, 4, 4, 4],
            "4-4-6-2": [4, 4, 6, 2],
            "5-5-5-5": [5, 5, 5, 5],
        }
        values = mapping.get(value, [4, 4, 4, 4])
        self._phases = [
            ("Inhale", values[0]),
            ("Hold", values[1]),
            ("Exhale", values[2]),
            ("Hold", values[3]),
        ]
        self._phase_index = 0
        self._phase_elapsed = 0
        self._update_phase_label()

    def _on_duration_changed(self, value: str) -> None:
        mapping = {
            "Open-ended": None,
            "1 min": 60,
            "2 min": 120,
            "5 min": 300,
        }
        self._duration_seconds = mapping.get(value)

    def _toggle(self) -> None:
        if self._playing:
            self._stop(manual=True)
            return
        self._playing = True
        self._toggle_btn.setText("Pause")
        self._timer.start()

    def _stop(self, manual: bool) -> None:
        self._timer.stop()
        self._playing = False
        self._toggle_btn.setText("Start")

        duration = self._elapsed_seconds
        self._elapsed_seconds = 0
        self._phase_elapsed = 0
        self._phase_index = 0
        self._phase_label.setText("Ready")
        self._elapsed_label.setText("00:00")

        if duration <= 0:
            return
        if manual:
            self.session_stopped.emit(duration)
        else:
            self.session_completed.emit(duration)

    def _update_phase_label(self) -> None:
        phase_name, phase_duration = self._phases[self._phase_index]
        remaining = max(phase_duration - self._phase_elapsed, 0)
        self._phase_label.setText(f"{phase_name} | {remaining}s")

    def _tick(self) -> None:
        self._elapsed_seconds += 1
        self._phase_elapsed += 1

        mins = self._elapsed_seconds // 60
        secs = self._elapsed_seconds % 60
        self._elapsed_label.setText(f"{mins:02d}:{secs:02d}")

        _phase_name, phase_duration = self._phases[self._phase_index]
        if self._phase_elapsed >= phase_duration:
            self._phase_elapsed = 0
            self._phase_index = (self._phase_index + 1) % len(self._phases)
        self._update_phase_label()

        if self._duration_seconds and self._elapsed_seconds >= self._duration_seconds:
            self._stop(manual=False)


class StreamWorker(QObject):
    token_received = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(
        self,
        feedback_service: ToolFeedbackService,
        tool_name: str,
        payload: dict,
        chunk_size: int = 32,
    ) -> None:
        super().__init__()
        self._feedback_service = feedback_service
        self._tool_name = tool_name
        self._payload = payload
        self._chunk_size = max(20, min(50, chunk_size))
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        buffer = ""
        try:
            for token in self._feedback_service.stream_feedback(self._tool_name, self._payload):
                if self._cancelled:
                    break
                buffer += token
                if len(buffer) >= self._chunk_size:
                    self.token_received.emit(buffer)
                    buffer = ""
            if buffer and not self._cancelled:
                self.token_received.emit(buffer)
            self.finished.emit()
        except Exception as exc:
            self.error.emit(str(exc))
            self.finished.emit()


class ToolsView(QWidget):
    tool_submitted = pyqtSignal(str)
    tool_feedback_ready = pyqtSignal(str)

    def __init__(
        self,
        tool_service: ToolService,
        feedback_service: ToolFeedbackService,
        tool_usage_service: ToolUsageService,
    ) -> None:
        super().__init__()
        self.setObjectName("ViewRoot")
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)

        self._tool_service = tool_service
        self._feedback_service = feedback_service
        self._tool_usage_service = tool_usage_service

        self._stream_thread: QThread | None = None
        self._stream_worker: StreamWorker | None = None
        self._feedback_queue: list[str] = []
        self._stream_finished = False
        self._stream_finalized = False
        self._active_thought_entry_id: int | None = None
        self._active_thought_payload: dict | None = None

        self._feedback_drain_timer = QTimer(self)
        self._feedback_drain_timer.setInterval(65)
        self._feedback_drain_timer.timeout.connect(self._drain_feedback_queue)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        disclaimer = QLabel(
            "These tools are supportive coping strategies and not replacements for professional care. "
            "Everyone is different, and it's okay to experiment to find what helps you."
        )
        disclaimer.setObjectName("CardMeta")
        disclaimer.setWordWrap(True)
        root.addWidget(disclaimer)

        main_column = QVBoxLayout()
        main_column.setSpacing(12)
        main_column.setContentsMargins(0, 0, 0, 0)
        main_column.setAlignment(Qt.AlignTop)
        self._breathing_card = BreathCheckWidget()
        self._breathing_card.session_stopped.connect(self._record_breathing_usage)
        self._breathing_card.session_completed.connect(self._record_breathing_usage)
        self._breathing_card.setMaximumWidth(16777215)

        self._thought_log_card = self._build_thought_log_card()
        self._history_panel = self._build_history_panel()

        main_column.addWidget(self._breathing_card, 0)
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(12)
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setAlignment(Qt.AlignTop)
        bottom_row.addWidget(self._thought_log_card, 2)
        bottom_row.addWidget(self._history_panel, 2)
        main_column.addLayout(bottom_row, 1)
        root.addLayout(main_column, 1)

        self._refresh_history()

    def _build_thought_log_card(self) -> QFrame:
        card = CardFrame()
        layout = card.content_layout

        header = QHBoxLayout()
        header.setSpacing(8)
        title = QLabel("Thought Log")
        title.setObjectName("CardTitle")
        self._history_refresh_btn = QPushButton("Refresh History")
        self._history_refresh_btn.clicked.connect(self._refresh_history)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self._history_refresh_btn)
        layout.addLayout(header)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        situation_label = QLabel("Situation")
        self._situation_input = QTextEdit()
        self._situation_input.setPlaceholderText(
            "What happened? e.g., Team meeting this morning."
        )

        automatic_label = QLabel("Automatic thought")
        self._automatic_input = QTextEdit()
        self._automatic_input.setPlaceholderText(
            "What went through your mind? e.g., 'I will mess this up.'"
        )

        balanced_label = QLabel("Alternative balanced thought")
        self._balanced_input = QTextEdit()
        self._balanced_input.setPlaceholderText(
            "A more balanced view. e.g., 'I can prepare one point at a time.'"
        )

        feedback_label = QLabel("AI Feedback")
        self._feedback_output = QTextEdit()
        self._feedback_output.setReadOnly(True)
        self._feedback_output.setPlaceholderText("Feedback will appear after you save.")

        grid.addWidget(situation_label, 0, 0)
        grid.addWidget(automatic_label, 0, 1)
        grid.addWidget(self._situation_input, 1, 0)
        grid.addWidget(self._automatic_input, 1, 1)
        grid.addWidget(balanced_label, 2, 0)
        grid.addWidget(feedback_label, 2, 1)
        grid.addWidget(self._balanced_input, 3, 0)
        grid.addWidget(self._feedback_output, 3, 1)
        layout.addLayout(grid)

        layout.addWidget(QLabel("Emotion intensity"))
        intensity_note = QLabel("How strong was the emotion before reframing? (0 = none, 10 = highest)")
        intensity_note.setObjectName("CardMeta")
        intensity_note.setWordWrap(True)
        layout.addWidget(intensity_note)
        intensity_row = QHBoxLayout()
        intensity_row.setSpacing(8)
        self._intensity_slider = QSlider(Qt.Horizontal)
        self._intensity_slider.setRange(0, 10)
        self._intensity_slider.setValue(5)
        self._intensity_value = QLabel("5")
        self._intensity_slider.valueChanged.connect(
            lambda value: self._intensity_value.setText(str(value))
        )
        intensity_row.addWidget(self._intensity_slider)
        intensity_row.addWidget(self._intensity_value)
        layout.addLayout(intensity_row)

        layout.addWidget(QLabel("Re-rate emotion"))
        rerate_note = QLabel("After writing a balanced thought, rate the emotion again.")
        rerate_note.setObjectName("CardMeta")
        rerate_note.setWordWrap(True)
        layout.addWidget(rerate_note)
        rerate_row = QHBoxLayout()
        rerate_row.setSpacing(8)
        self._rerate_slider = QSlider(Qt.Horizontal)
        self._rerate_slider.setRange(0, 10)
        self._rerate_slider.setValue(5)
        self._rerate_value = QLabel("5")
        self._rerate_slider.valueChanged.connect(
            lambda value: self._rerate_value.setText(str(value))
        )
        rerate_row.addWidget(self._rerate_slider)
        rerate_row.addWidget(self._rerate_value)
        layout.addLayout(rerate_row)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        self._saved_label = QLabel("")
        self._saved_label.setObjectName("CardMeta")
        save_btn = QPushButton("Save thought log")
        save_btn.setObjectName("AccentButton")
        save_btn.clicked.connect(self._submit_thought_log)
        actions.addWidget(self._saved_label)
        actions.addStretch()
        actions.addWidget(save_btn)
        layout.addLayout(actions)

        return card

    def _build_history_panel(self) -> QFrame:
        panel = CardFrame()
        layout = panel.content_layout

        title = QLabel("Usage History")
        title.setObjectName("CardTitle")
        layout.addWidget(title)

        scroll = RoundedScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        body = QWidget()
        body.setObjectName("ScrollContent")
        body.setAutoFillBackground(True)
        body.setAttribute(Qt.WA_StyledBackground, True)
        self._history_host = QVBoxLayout(body)
        self._history_host.setContentsMargins(8, 8, 8, 8)
        self._history_host.setSpacing(8)
        self._history_host.setAlignment(Qt.AlignTop)

        scroll.setWidget(body)
        layout.addWidget(scroll, 1)
        return panel

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        clear_layout(layout)

    def _format_local_time(self, dt: datetime) -> str:
        value = dt
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone().strftime("%Y-%m-%d %H:%M")

    def _refresh_history(self) -> None:
        self._clear_layout(self._history_host)

        usage_entries = [
            row for row in self._tool_usage_service.list_usage() if row.tool_name == "breathcheck_tool"
        ]
        usage_entries = sorted(usage_entries, key=lambda row: row.used_at, reverse=True)

        breathing_section = CardFrame(margins=(10, 10, 10, 10))
        breathing_layout = breathing_section.content_layout
        breathing_layout.setSpacing(6)
        breathing_title = QLabel("BreathCheck Sessions")
        breathing_title.setObjectName("CardTitle")
        breathing_layout.addWidget(breathing_title)

        if not usage_entries:
            empty = QLabel("No breathing sessions yet.")
            empty.setObjectName("CardMeta")
            breathing_layout.addWidget(empty)
        else:
            for row in usage_entries:
                meta = row.metadata or {}
                duration = int(meta.get("duration_seconds", 0) or 0)
                mins = duration // 60
                secs = duration % 60
                timestamp = self._format_local_time(row.used_at)
                pace = meta.get("pace", "-")
                duration_setting = meta.get("duration_setting", "-")
                line = QLabel(
                    f"{timestamp} | pace: {pace} | duration: {mins:02d}:{secs:02d} | setting: {duration_setting}"
                )
                line.setObjectName("CardMeta")
                line.setWordWrap(True)
                breathing_layout.addWidget(line)

        self._history_host.addWidget(breathing_section)

        thought_entries = [
            row for row in self._tool_service.list_entries() if row.tool_name == "thought_log"
        ]
        thought_entries = sorted(thought_entries, key=lambda row: row.created_at, reverse=True)

        thought_section = CardFrame(margins=(10, 10, 10, 10))
        thought_layout = thought_section.content_layout
        thought_layout.setSpacing(6)
        thought_title = QLabel("Thought Log Entries")
        thought_title.setObjectName("CardTitle")
        thought_layout.addWidget(thought_title)

        if not thought_entries:
            empty = QLabel("No thought log entries yet.")
            empty.setObjectName("CardMeta")
            thought_layout.addWidget(empty)
        else:
            for entry in thought_entries:
                data = entry.data or {}
                intensity = data.get("emotion_intensity", "-")
                timestamp = self._format_local_time(entry.created_at)

                item_card = CardFrame(margins=(8, 8, 8, 8))
                item_layout = item_card.content_layout
                item_layout.setSpacing(6)

                header_btn = QPushButton(
                    f"{timestamp} | intensity: {intensity}"
                )
                header_btn.setCheckable(True)
                item_layout.addWidget(header_btn)

                details = QTextEdit()
                details.setReadOnly(True)
                details.setVisible(False)
                details.setMinimumHeight(110)
                details.setPlainText(
                    "\n".join(
                        [
                            f"Situation: {data.get('situation', '')}",
                            f"Automatic thought: {data.get('automatic_thought', '')}",
                            f"Emotion intensity: {data.get('emotion_intensity', '')}",
                            f"Alternative thought: {data.get('balanced_thought', '')}",
                            f"Re-rate: {data.get('emotion_rerate', '')}",
                            f"AI feedback: {data.get('ai_feedback', '-')}",
                        ]
                    )
                )
                header_btn.toggled.connect(details.setVisible)
                item_layout.addWidget(details)

                thought_layout.addWidget(item_card)

        self._history_host.addWidget(thought_section)

    def _record_breathing_usage(self, duration_seconds: int) -> None:
        if duration_seconds <= 0:
            return
        metadata = {
            "duration_seconds": duration_seconds,
            "pace": self._breathing_card.current_pace(),
            "duration_setting": self._breathing_card.current_duration_label(),
        }
        self._tool_usage_service.record_usage("breathcheck_tool", metadata)
        self._refresh_history()
        self.tool_submitted.emit("BreathCheck tool")

    def _submit_thought_log(self) -> None:
        situation = self._situation_input.toPlainText().strip()
        automatic_thought = self._automatic_input.toPlainText().strip()
        balanced_thought = self._balanced_input.toPlainText().strip()

        if not situation or not automatic_thought:
            self._saved_label.setText("Please fill situation and automatic thought.")
            return

        payload = {
            "situation": situation,
            "automatic_thought": automatic_thought,
            "emotion_intensity": self._intensity_slider.value(),
            "balanced_thought": balanced_thought,
            "emotion_rerate": self._rerate_slider.value(),
            "created_at": datetime.now().astimezone().isoformat(),
        }

        created = self._tool_service.create_entry("thought_log", payload)
        self._active_thought_entry_id = created.id
        self._active_thought_payload = dict(payload)

        self._tool_usage_service.record_usage(
            "thought_log",
            {
                "emotion_intensity": self._intensity_slider.value(),
                "emotion_rerate": self._rerate_slider.value(),
                "has_balanced_thought": bool(balanced_thought),
            },
        )

        self.tool_submitted.emit("Thought log")
        self._saved_label.setText("Saved")
        self._feedback_output.clear()

        self._start_stream_feedback(payload)

    def _clear_thought_log_inputs(self) -> None:
        self._situation_input.clear()
        self._automatic_input.clear()
        self._balanced_input.clear()
        self._intensity_slider.setValue(5)
        self._rerate_slider.setValue(5)

    def _start_stream_feedback(self, payload: dict) -> None:
        self._stop_stream_worker()
        self._feedback_queue = []
        self._stream_finished = False
        self._stream_finalized = False

        if not self._feedback_service.is_configured():
            fallback = self._feedback_service.fallback_feedback("thought_log", payload)
            self._feedback_output.setPlainText(fallback)
            self._finalize_feedback_store(fallback)
            return

        self._stream_thread = QThread(self)
        self._stream_worker = StreamWorker(self._feedback_service, "thought_log", payload)
        self._stream_worker.moveToThread(self._stream_thread)

        self._stream_thread.started.connect(self._stream_worker.run)
        self._stream_worker.token_received.connect(self._queue_feedback_token)
        self._stream_worker.error.connect(self._handle_stream_error)
        self._stream_worker.finished.connect(self._handle_stream_finished)
        self._stream_worker.finished.connect(self._stream_thread.quit)

        self._stream_thread.finished.connect(self._cleanup_stream_worker)
        self._stream_thread.start()

    def _queue_feedback_token(self, token: str) -> None:
        for index in range(0, len(token), 6):
            self._feedback_queue.append(token[index : index + 6])
        if not self._feedback_drain_timer.isActive():
            self._feedback_drain_timer.start()

    def _drain_feedback_queue(self) -> None:
        if self._feedback_queue:
            chunk = self._feedback_queue.pop(0)
            cursor = self._feedback_output.textCursor()
            cursor.movePosition(cursor.End)
            cursor.insertText(chunk)
            self._feedback_output.setTextCursor(cursor)
            self._feedback_output.ensureCursorVisible()
        if not self._feedback_queue and self._stream_finished:
            self._feedback_drain_timer.stop()
            self._finalize_feedback_store(self._feedback_output.toPlainText().strip())

    def _handle_stream_finished(self) -> None:
        self._stream_finished = True
        if not self._feedback_queue:
            self._feedback_drain_timer.stop()
            self._finalize_feedback_store(self._feedback_output.toPlainText().strip())

    def _handle_stream_error(self, message: str) -> None:
        _ = message
        fallback = (
            "Focus on one practical next step and test a balanced thought today. "
            "Small repetitions build confidence."
        )
        self._feedback_queue = []
        self._feedback_drain_timer.stop()
        self._feedback_output.setPlainText(fallback)
        self._stream_finished = True
        self._finalize_feedback_store(fallback)

    def _finalize_feedback_store(self, feedback_text: str) -> None:
        if self._stream_finalized:
            return
        self._stream_finalized = True

        text = feedback_text.strip()
        if not text:
            text = (
                "Focus on one practical next step and test a balanced thought today. "
                "Small repetitions build confidence."
            )
            self._feedback_output.setPlainText(text)

        if self._active_thought_entry_id is not None and self._active_thought_payload is not None:
            payload = dict(self._active_thought_payload)
            payload["ai_feedback"] = text
            self._tool_service.update_entry(self._active_thought_entry_id, payload)

        self._clear_thought_log_inputs()
        self._refresh_history()
        self._saved_label.setText("Saved + feedback ready")
        self.tool_feedback_ready.emit("thought_log")
        self._active_thought_entry_id = None
        self._active_thought_payload = None

    def _cleanup_stream_worker(self) -> None:
        if self._stream_worker is not None:
            self._stream_worker.deleteLater()
        if self._stream_thread is not None:
            self._stream_thread.deleteLater()
        self._stream_worker = None
        self._stream_thread = None

    def _stop_stream_worker(self) -> None:
        if self._stream_worker is not None:
            self._stream_worker.cancel()
        if self._stream_thread is not None and self._stream_thread.isRunning():
            self._stream_thread.quit()
            self._stream_thread.wait(2000)
        self._cleanup_stream_worker()

    def on_leave(self) -> None:
        if self._breathing_card.is_playing():
            self._breathing_card.stop_session()
        self._feedback_drain_timer.stop()
        self._stop_stream_worker()

    def reset_view(self) -> None:
        self._saved_label.setText("")
        self._feedback_output.clear()
        self._clear_thought_log_inputs()
        self._breathing_card.reset()
        self._feedback_queue = []
        self._stream_finished = False
        self._stream_finalized = False
        self._feedback_drain_timer.stop()
        self._stop_stream_worker()
        self._refresh_history()

    def wait_for_workers(self) -> None:
        self._feedback_drain_timer.stop()
        self._stop_stream_worker()
