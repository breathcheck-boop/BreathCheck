from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QRadioButton,
    QSlider,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from anxiety_app.domain.services import LearningService, ModuleDataService
from anxiety_app.ui.widgets.card_widgets import CompactCard, clear_layout
from anxiety_app.ui.widgets.rounded_scroll_area import RoundedScrollArea

MODULES = [
    {
        "id": "module_1",
        "title": "Understanding Anxiety",
        "description": "Learn anxiety basics, map your patterns, and build your first coping plan.",
    },
    {
        "id": "module_2",
        "title": "Relaxation",
        "description": "Practice paced breathing and relaxation skills.",
    },
    {
        "id": "module_3",
        "title": "Our Thoughts",
        "description": "Understand thought patterns linked to anxiety.",
    },
    {
        "id": "module_4",
        "title": "Changing Thoughts",
        "description": "Build balanced thoughts with practical challenge steps.",
    },
    {
        "id": "module_5",
        "title": "Coping with Worry",
        "description": "Differentiate worries and practice structured coping.",
    },
    {
        "id": "module_6",
        "title": "Lifestyle Factors & Relapse Prevention",
        "description": "Create a maintenance plan for long-term stability.",
    },
]

STEP_TITLES = [
    "Welcome + Orientation",
    "Anxiety Basics",
    "Fight-or-Flight",
    "Worry Cycle",
    "Helpful Concern vs Unhelpful Worry",
    "Where Anxiety Shows Up",
    "Values -> Goals -> Tiny Habits",
    "Baseline Ratings",
    "Micro-Plan",
    "Completion",
]

STEP_AUDIO_TITLES = [
    "Welcome to BreathCheck",
    "Thoughts, Body, Actions",
    "Body Signals and Fight-or-Flight",
    "Understanding the Worry Cycle",
    "Concern vs Worry",
    "Mapping Anxiety Domains",
    "Values and Tiny Habits",
    "Setting Your Baseline",
    "Build Your Micro-Plan",
    "Module Wrap-Up",
]

STEP_AUDIO_DURATIONS = [
    61,
    66,
    66,
    50,
    50,
    35,
    49,
    90,
    90,
    90,
]

STEP_QUOTES = [
    (
        "The curious paradox is that when I accept myself just as I am, then I can change.",
        "Carl Rogers",
    ),
    (
        "You don't have to control your thoughts. You just have to stop letting them control you.",
        "Dan Millman",
    ),
    (
        "You can't stop the waves, but you can learn to surf.",
        "Jon Kabat-Zinn",
    ),
    (
        "Between stimulus and response there is a space. In that space is our power to choose our response.",
        "Viktor E. Frankl",
    ),
    (
        "Nothing diminishes anxiety faster than action.",
        "Walter Anderson",
    ),
    (
        "Do not anticipate trouble, or worry about what may never happen.",
        "Benjamin Franklin",
    ),
    (
        "When we are no longer able to change a situation, we are challenged to change ourselves.",
        "Viktor E. Frankl",
    ),
    (
        "The greatest weapon against stress is our ability to choose one thought over another.",
        "William James",
    ),
    (
        "Almost everything will work again if you unplug it for a few minutes, including you.",
        "Anne Lamott",
    ),
    (
        "Feelings come and go like clouds in a windy sky. Conscious breathing is my anchor.",
        "Thich Nhat Hanh",
    ),
]

STEP_CONTEXTS = [
    "Set your starting point and clarify why you are here.",
    "Identify which part of anxiety impacts you most right now.",
    "Recognize body signals to improve early awareness.",
    "Map one real worry loop to understand your pattern.",
    "Practice distinguishing action-focused concern from worry looping.",
    "Pinpoint life domains where anxiety shows up most often.",
    "Turn values into practical goals and small weekly actions.",
    "Create baseline ratings for future progress comparison.",
    "Commit to one realistic plan for the next few days.",
    "Consolidate what you learned and lock your next step.",
]

QUIZ_ITEMS = [
    (
        "quiz_1",
        "I have an exam next week, so I'll plan 2 hours of study tonight.",
        "Helpful concern",
    ),
    (
        "quiz_2",
        "What if I fail every exam this year and my whole future is ruined?",
        "Unhelpful worry",
    ),
    (
        "quiz_3",
        "I'll check the deadline and ask my teacher if I'm missing anything.",
        "Helpful concern",
    ),
    (
        "quiz_4",
        "I keep thinking about every possible way this could go wrong, all day.",
        "Unhelpful worry",
    ),
]

DOMAIN_OPTIONS = [
    "Health",
    "Work/School",
    "Money",
    "Relationships",
    "Safety",
    "Future/Identity",
    "Other",
]

PATTERN_OPTIONS = [
    "Overthinking/constant worry",
    "Avoiding tasks/people",
    "Physical symptoms",
    "Sleep problems",
    "Checking/reassurance seeking",
]

VALUE_OPTIONS = [
    "Health",
    "Family",
    "Learning",
    "Stability",
    "Freedom",
    "Creativity",
    "Contribution",
    "Independence",
    "Security",
    "Connection",
    "Other",
]


class LearnView(QWidget):
    module_completed = pyqtSignal(str)

    def __init__(
        self,
        learning_service: LearningService,
        module_data_service: ModuleDataService,
    ) -> None:
        super().__init__()
        self.setObjectName("ViewRoot")
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._learning_service = learning_service
        self._module_data_service = module_data_service

        self._module1_data: dict[str, Any] = {}
        self._current_step = 0
        self._module1_active = False
        self._module1_ui_ready = False
        self._overview_signature: tuple[tuple[str, str, int], ...] = ()
        self._active_media_step = -1
        self._audio_source_available = False
        self._audio_playing = False
        self._audio_duration_seconds = 0
        self._audio_position_seconds = 0
        self._audio_timer = QTimer(self)
        self._audio_timer.setInterval(1000)
        self._audio_timer.timeout.connect(self._tick_audio)

        self._stack = QStackedWidget()
        self._stack.setObjectName("ViewStack")

        self._overview_page = self._build_modules_page()
        self._module1_page = self._build_module1_page()
        self._module1_overview_page = self._build_module1_overview_page()
        self._module_placeholder_page = self._build_module_placeholder_overview_page()

        self._stack.addWidget(self._overview_page)
        self._stack.addWidget(self._module1_page)
        self._stack.addWidget(self._module1_overview_page)
        self._stack.addWidget(self._module_placeholder_page)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)
        root.addWidget(self._stack)

        self._refresh_overview()

    def show_modules(self) -> None:
        if self._module1_active:
            self._save_current_step()
        self._module1_active = False
        self.stop_audio()
        self._stack.setCurrentIndex(0)
        self._refresh_overview()

    def stop_audio(self) -> None:
        self._audio_timer.stop()
        self._audio_playing = False
        self._audio_position_seconds = 0
        if hasattr(self, "_audio_play_btn"):
            self._audio_play_btn.setText("Play")
        if hasattr(self, "_audio_seek_slider"):
            self._audio_seek_slider.setValue(0)
        self._update_audio_time_label()
        if hasattr(self, "_audio_status_label"):
            if self._audio_source_available:
                self._audio_status_label.setText("Ready")
            else:
                self._audio_status_label.setText("Audio not added yet")

    def reset_module1_state(self) -> None:
        self._module1_data = {}
        self._module1_active = False
        self._current_step = 0
        self.stop_audio()
        self._stack.setCurrentIndex(0)
        self._refresh_overview()

    def reset_module1_to_start(self) -> None:
        self._module1_active = False
        self._current_step = 0
        self.stop_audio()
        self._load_module1_data(force_step=0)

    def _normalize_status(self, status: str | None) -> str:
        if not status:
            return "LOCKED"
        value = status.upper()
        if value == "COMPLETED":
            return "COMPLETE"
        if value == "IN_PROGRESS":
            return "UNLOCKED"
        if value not in {"LOCKED", "UNLOCKED", "COMPLETE"}:
            return "LOCKED"
        return value

    def _ensure_progress_rows(self) -> None:
        existing = {row.module_id: row for row in self._learning_service.list_progress()}
        for index, module in enumerate(MODULES):
            if module["id"] in existing:
                continue
            self._learning_service.update_progress(
                module["id"],
                "UNLOCKED" if index == 0 else "LOCKED",
                0,
            )

        refreshed = {row.module_id: row for row in self._learning_service.list_progress()}
        for index, module in enumerate(MODULES):
            module_id = module["id"]
            row = refreshed.get(module_id)
            if row is None:
                continue
            current_status = self._normalize_status(row.status)
            if index == 0:
                if current_status == "LOCKED":
                    self._learning_service.update_progress(module_id, "UNLOCKED", row.progress_percent)
                continue

            prev = refreshed.get(MODULES[index - 1]["id"])
            prev_complete = bool(prev and self._normalize_status(prev.status) == "COMPLETE")
            if prev_complete and current_status == "LOCKED":
                self._learning_service.update_progress(module_id, "UNLOCKED", row.progress_percent)
            if (not prev_complete) and current_status == "UNLOCKED":
                self._learning_service.update_progress(module_id, "LOCKED", min(row.progress_percent, 99))

    def _build_modules_page(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        scroll = RoundedScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content.setObjectName("ScrollContent")
        content.setAutoFillBackground(True)
        content.setAttribute(Qt.WA_StyledBackground, True)

        self._modules_grid = QGridLayout(content)
        self._modules_grid.setContentsMargins(12, 12, 12, 12)
        self._modules_grid.setHorizontalSpacing(12)
        self._modules_grid.setVerticalSpacing(12)
        self._modules_grid.setColumnStretch(0, 1)
        self._modules_grid.setColumnStretch(1, 1)

        scroll.setWidget(content)
        root.addWidget(scroll)
        return page

    def _refresh_overview(self) -> None:
        self._ensure_progress_rows()

        progress_map = {entry.module_id: entry for entry in self._learning_service.list_progress()}
        signature: list[tuple[str, str, int]] = []
        for module in MODULES:
            progress = progress_map.get(module["id"])
            status = self._normalize_status(progress.status if progress else "LOCKED")
            percent = int(progress.progress_percent) if progress else 0
            signature.append((module["id"], status, percent))

        signature_tuple = tuple(signature)
        if signature_tuple == self._overview_signature and self._modules_grid.count() > 0:
            return

        self._overview_signature = signature_tuple
        clear_layout(self._modules_grid)

        for index, module in enumerate(MODULES):
            module_id = module["id"]
            progress = progress_map.get(module_id)
            status = self._normalize_status(progress.status if progress else "LOCKED")
            percent = int(progress.progress_percent) if progress else 0
            locked = status == "LOCKED"

            status_text = f"Status: {status} | {percent}%"
            if locked:
                status_text = "Complete previous module to unlock"

            card = CompactCard(
                title=f"Module {index + 1} - {module['title']}",
                description=module["description"],
                icon_text="",
                status_text=status_text,
                minimum_height=240,
            )
            card.setProperty("moduleStatus", status.lower())
            overview_btn = card.add_button("Overview", enabled=not locked)
            open_btn = card.add_button("Open", enabled=not locked)
            if module_id == "module_1":
                overview_btn.clicked.connect(self._open_module1_overview)
                open_btn.clicked.connect(self._open_module1)
            else:
                overview_btn.clicked.connect(
                    lambda _=False, module_id=module_id: self._open_module_placeholder(module_id)
                )
                open_btn.clicked.connect(
                    lambda _=False, module_id=module_id: self._open_module_placeholder(module_id)
                )

            self._modules_grid.addWidget(card, index // 2, index % 2)

    def _build_module1_page(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(8)
        back_btn = QPushButton("Back to modules")
        back_btn.clicked.connect(self._back_to_modules)
        self._step_count_label = QLabel("Step 1 of 10")
        self._step_count_label.setObjectName("CardMeta")
        header.addWidget(back_btn)
        header.addStretch()
        header.addWidget(self._step_count_label)
        root.addLayout(header)

        self._step_progress = QProgressBar()
        self._step_progress.setRange(0, 100)
        self._step_progress.setValue(10)
        root.addWidget(self._step_progress)

        split = QHBoxLayout()
        split.setSpacing(12)
        split.setContentsMargins(0, 0, 0, 0)

        self._left_media_panel = QWidget()
        self._left_media_panel.setAutoFillBackground(True)
        self._left_media_panel.setAttribute(Qt.WA_StyledBackground, True)
        left_layout = QVBoxLayout(self._left_media_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        self._media_image_label = QLabel("[Image placeholder]")
        self._media_image_label.setAlignment(Qt.AlignCenter)
        self._media_image_label.setMinimumHeight(180)
        self._media_image_label.setWordWrap(True)
        left_layout.addWidget(self._media_image_label)

        self._audio_title_label = QLabel("")
        self._audio_title_label.setObjectName("CardTitle")
        left_layout.addWidget(self._audio_title_label)

        self._audio_status_label = QLabel("Audio not added yet")
        self._audio_status_label.setObjectName("CardMeta")
        left_layout.addWidget(self._audio_status_label)

        self._audio_play_btn = QPushButton("Play")
        self._audio_play_btn.clicked.connect(self._toggle_audio_for_current_step)
        left_layout.addWidget(self._audio_play_btn)

        self._audio_seek_slider = QSlider(Qt.Horizontal)
        self._audio_seek_slider.setRange(0, 100)
        self._audio_seek_slider.setValue(0)
        self._audio_seek_slider.sliderReleased.connect(self._on_audio_seek_released)
        left_layout.addWidget(self._audio_seek_slider)

        self._audio_time_label = QLabel("00:00 / 00:00")
        self._audio_time_label.setObjectName("CardMeta")
        self._audio_time_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self._audio_time_label)

        self._quote_label = QLabel("")
        self._quote_label.setObjectName("QuoteText")
        self._quote_label.setAlignment(Qt.AlignCenter)
        self._quote_label.setWordWrap(True)
        self._quote_source_label = QLabel("")
        self._quote_source_label.setObjectName("QuoteSource")
        self._quote_source_label.setAlignment(Qt.AlignCenter)
        self._quote_source_label.setWordWrap(True)
        quote_box = QWidget()
        quote_layout = QVBoxLayout(quote_box)
        quote_layout.setContentsMargins(0, 0, 0, 0)
        quote_layout.setSpacing(6)
        quote_layout.addWidget(self._quote_label)
        quote_layout.addWidget(self._quote_source_label)

        left_layout.addStretch()
        left_layout.addWidget(quote_box)
        left_layout.addStretch()

        split.addWidget(self._left_media_panel, 1)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self._steps = QStackedWidget()
        self._steps.addWidget(self._wrap_step(self._build_step1()))
        self._steps.addWidget(self._wrap_step(self._build_step2()))
        self._steps.addWidget(self._wrap_step(self._build_step3()))
        self._steps.addWidget(self._wrap_step(self._build_step4()))
        self._steps.addWidget(self._wrap_step(self._build_step5()))
        self._steps.addWidget(self._wrap_step(self._build_step6()))
        self._steps.addWidget(self._wrap_step(self._build_step7()))
        self._steps.addWidget(self._wrap_step(self._build_step8()))
        self._steps.addWidget(self._wrap_step(self._build_step9()))
        self._steps.addWidget(self._wrap_step(self._build_step10()))
        right_layout.addWidget(self._steps, 1)

        split.addWidget(right_container, 2)
        root.addLayout(split, 1)

        nav = QHBoxLayout()
        nav.setSpacing(8)
        self._prev_btn = QPushButton("Back")
        self._prev_btn.clicked.connect(self._prev_step)
        self._next_btn = QPushButton("Next")
        self._next_btn.setObjectName("AccentButton")
        self._next_btn.clicked.connect(self._next_step)
        nav.addWidget(self._prev_btn)
        nav.addStretch()
        nav.addWidget(self._next_btn)
        root.addLayout(nav)
        self._module1_ui_ready = True
        return page

    def _wrap_step(self, widget: QWidget) -> RoundedScrollArea:
        widget.setObjectName("ScrollContent")
        widget.setAutoFillBackground(True)
        widget.setAttribute(Qt.WA_StyledBackground, True)

        scroll = RoundedScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(widget)
        return scroll

    def _resource_dir(self, kind: str, step_index: int) -> Path:
        return (
            Path(__file__).resolve().parent.parent
            / "resources"
            / "modules"
            / "module_1"
            / kind
            / f"step_{step_index + 1}"
        )

    def _find_resource(self, kind: str, step_index: int) -> Path | None:
        directory = self._resource_dir(kind, step_index)
        if not directory.exists():
            return None
        for ext in (".webp", ".png", ".jpg", ".jpeg", ".bmp", ".mp3", ".ogg", ".wav"):
            for file_path in directory.glob(f"*{ext}"):
                return file_path
        return None

    def _build_step_container(self, step_index: int) -> tuple[QWidget, QVBoxLayout]:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        layout.addWidget(self._card("Purpose", STEP_CONTEXTS[step_index]))
        return widget, layout

    def _format_time(self, seconds: int) -> str:
        value = max(0, int(seconds))
        mins = value // 60
        secs = value % 60
        return f"{mins:02d}:{secs:02d}"

    def _update_audio_time_label(self) -> None:
        if not hasattr(self, "_audio_time_label"):
            return
        total = self._audio_duration_seconds if self._audio_duration_seconds > 0 else 0
        self._audio_time_label.setText(
            f"{self._format_time(self._audio_position_seconds)} / {self._format_time(total)}"
        )

    def _update_left_panel_for_step(self, step_index: int) -> None:
        self.stop_audio()
        self._active_media_step = step_index
        self._audio_duration_seconds = STEP_AUDIO_DURATIONS[step_index]
        self._audio_position_seconds = 0
        self._audio_seek_slider.setRange(0, max(1, self._audio_duration_seconds))
        self._audio_seek_slider.setValue(0)
        self._update_audio_time_label()

        self._audio_title_label.setText(STEP_AUDIO_TITLES[step_index])

        audio_path = self._find_resource("audio", step_index)
        self._audio_source_available = audio_path is not None
        self._audio_play_btn.setEnabled(self._audio_source_available)
        if self._audio_source_available:
            self._audio_status_label.setText("Ready")
        else:
            self._audio_status_label.setText("Audio not added yet")

        image_path = self._find_resource("images", step_index)
        if image_path is not None:
            pixmap = QPixmap(str(image_path))
            if not pixmap.isNull():
                self._media_image_label.setPixmap(
                    pixmap.scaled(380, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                self._media_image_label.setText("")
            else:
                self._media_image_label.setPixmap(QPixmap())
                self._media_image_label.setText("[Image placeholder]")
        else:
            self._media_image_label.setPixmap(QPixmap())
            self._media_image_label.setText("[Image placeholder]")

        quote_text, quote_source = STEP_QUOTES[step_index]
        self._quote_label.setText(f"\"{quote_text}\"")
        self._quote_source_label.setText(f"- {quote_source}")

    def _toggle_audio_for_current_step(self) -> None:
        if not self._audio_source_available:
            return
        if self._audio_playing:
            self.stop_audio()
            return
        self._audio_playing = True
        self._audio_play_btn.setText("Pause")
        self._audio_status_label.setText("Playing")
        self._audio_timer.start()

    def _on_audio_seek_released(self) -> None:
        self._audio_position_seconds = self._audio_seek_slider.value()
        self._update_audio_time_label()

    def _tick_audio(self) -> None:
        if not self._audio_playing:
            return
        self._audio_position_seconds += 1
        if self._audio_position_seconds >= self._audio_duration_seconds:
            self.stop_audio()
            return
        self._audio_seek_slider.setValue(self._audio_position_seconds)
        self._update_audio_time_label()

    def _card(self, title: str, text: str) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card.setAttribute(Qt.WA_StyledBackground, True)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)
        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        body_label = QLabel(text)
        body_label.setObjectName("CardMeta")
        body_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(body_label)
        return card

    def _build_step1(self) -> QWidget:
        widget, layout = self._build_step_container(0)
        layout.addWidget(
            self._card(
                "Lesson",
                "Anxiety is a protective response. This step sets your starting point so the program can stay practical.",
            )
        )
        layout.addWidget(QLabel("Welcome to your BreathCheck Journey"))
        intro = QLabel(
            "BreathCheck is not a substitute for professional mental health care. "
            "If you are in immediate danger, seek emergency support now."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)
        confidential = QLabel(
            "Your data is stored locally on your device."
        )
        confidential.setObjectName("CardMeta")
        confidential.setWordWrap(True)
        layout.addWidget(confidential)

        layout.addWidget(QLabel("What brings you here today? (Select at least one)"))
        reasons_note = QLabel("Tip: Select the options that feel most true this week.")
        reasons_note.setObjectName("CardMeta")
        reasons_note.setWordWrap(True)
        layout.addWidget(reasons_note)
        self._reason_checks: dict[str, QCheckBox] = {}
        for label in [
            "Constant worrying/overthinking",
            "Physical tension/restlessness",
            "Sleep problems related to worry",
            "Avoiding tasks/situations due to anxiety",
            "I want to understand myself better",
            "Other",
        ]:
            checkbox = QCheckBox(label)
            checkbox.stateChanged.connect(self._update_nav)
            self._reason_checks[label] = checkbox
            layout.addWidget(checkbox)

        self._reason_other_input = QLineEdit()
        self._reason_other_input.setPlaceholderText("Other details")
        self._reason_other_input.textChanged.connect(self._update_nav)
        layout.addWidget(self._reason_other_input)
        reason_other_note = QLabel("Example: 'I freeze before presentations' or 'I avoid checking messages.'")
        reason_other_note.setObjectName("CardMeta")
        reason_other_note.setWordWrap(True)
        layout.addWidget(reason_other_note)

        self._step1_validation = QLabel("")
        self._step1_validation.setObjectName("CardMeta")
        layout.addWidget(self._step1_validation)
        layout.addStretch()
        return widget

    def _build_step2(self) -> QWidget:
        widget, layout = self._build_step_container(1)
        layout.addWidget(
            self._card(
                "Lesson",
                "Anxiety often appears through thoughts, body sensations, and behaviors. Naming your strongest area helps target skills.",
            )
        )
        layout.addWidget(self._card("Triangle diagram", "[Placeholder: Thoughts - Body - Actions]"))

        cards_row = QHBoxLayout()
        cards_row.setSpacing(8)
        cards_row.addWidget(
            self._card("Thoughts", "Examples: 'What if I fail?', 'They will judge me'.")
        )
        cards_row.addWidget(
            self._card("Body", "Examples: Tight chest, restlessness, stomach drop.")
        )
        cards_row.addWidget(
            self._card("Actions", "Examples: Avoidance, over-checking, reassurance seeking.")
        )
        layout.addLayout(cards_row)

        layout.addWidget(QLabel("Which part feels strongest lately?"))
        dominant_note = QLabel("Choose one option based on your day-to-day experience.")
        dominant_note.setObjectName("CardMeta")
        dominant_note.setWordWrap(True)
        layout.addWidget(dominant_note)
        self._dominant_buttons: dict[str, QRadioButton] = {}
        self._dominant_group = QButtonGroup(widget)
        for key, text in [
            ("thoughts", "Thoughts"),
            ("body", "Body"),
            ("actions", "Actions"),
            ("not_sure", "Not sure"),
        ]:
            radio = QRadioButton(text)
            radio.toggled.connect(self._update_nav)
            self._dominant_group.addButton(radio)
            self._dominant_buttons[key] = radio
            layout.addWidget(radio)

        self._step2_validation = QLabel("")
        self._step2_validation.setObjectName("CardMeta")
        layout.addWidget(self._step2_validation)
        layout.addStretch()
        return widget

    def _build_step3(self) -> QWidget:
        widget, layout = self._build_step_container(2)
        layout.addWidget(
            self._card(
                "Lesson",
                "Fight-or-flight prepares your body for danger. These signals are uncomfortable but common in anxiety.",
            )
        )

        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self._card("Heart rate", "Pounding chest or racing heartbeat."))
        row.addWidget(self._card("Breathing", "Fast or shallow breaths."))
        row.addWidget(self._card("Muscle tension", "Tight shoulders, jaw, or neck."))
        row.addWidget(self._card("Stomach", "Butterflies or stomach discomfort."))
        layout.addLayout(row)

        layout.addWidget(QLabel("Which body signals have you noticed recently?"))
        signals_note = QLabel("Select all that apply in the past two weeks.")
        signals_note.setObjectName("CardMeta")
        signals_note.setWordWrap(True)
        layout.addWidget(signals_note)
        self._body_signal_checks: dict[str, QCheckBox] = {}
        for label in ["Heart rate", "Breathing", "Tension", "Stomach", "Restlessness"]:
            checkbox = QCheckBox(label)
            checkbox.stateChanged.connect(self._update_nav)
            self._body_signal_checks[label] = checkbox
            layout.addWidget(checkbox)

        self._step3_validation = QLabel("")
        self._step3_validation.setObjectName("CardMeta")
        layout.addWidget(self._step3_validation)
        layout.addStretch()
        return widget

    def _build_step4(self) -> QWidget:
        widget, layout = self._build_step_container(3)
        layout.addWidget(
            self._card(
                "Lesson",
                "A worry cycle links trigger, thought, emotion, and behavior. Mapping one example helps break the loop.",
            )
        )
        layout.addWidget(
            self._card("Worry cycle", "[Placeholder: Trigger -> Thought -> Feeling -> Behavior]")
        )
        cycle_note = QLabel("Use one recent situation to keep this practical.")
        cycle_note.setObjectName("CardMeta")
        cycle_note.setWordWrap(True)
        layout.addWidget(cycle_note)

        layout.addWidget(QLabel("Trigger"))
        self._cycle_trigger_input = QLineEdit()
        self._cycle_trigger_input.setPlaceholderText("Example: Received an email from my manager")
        self._cycle_trigger_input.textChanged.connect(self._update_nav)
        layout.addWidget(self._cycle_trigger_input)
        trigger_note = QLabel("Trigger = what happened right before anxiety rose.")
        trigger_note.setObjectName("CardMeta")
        trigger_note.setWordWrap(True)
        layout.addWidget(trigger_note)

        layout.addWidget(QLabel("Thought"))
        self._cycle_thought_input = QLineEdit()
        self._cycle_thought_input.setPlaceholderText("Example: 'I must have done something wrong'")
        self._cycle_thought_input.textChanged.connect(self._update_nav)
        layout.addWidget(self._cycle_thought_input)
        thought_note = QLabel("Thought = the first interpretation your mind made.")
        thought_note.setObjectName("CardMeta")
        thought_note.setWordWrap(True)
        layout.addWidget(thought_note)

        layout.addWidget(QLabel("Feeling intensity (0-10)"))
        intensity_row = QHBoxLayout()
        self._cycle_intensity_slider = QSlider(Qt.Horizontal)
        self._cycle_intensity_slider.setRange(0, 10)
        self._cycle_intensity_slider.setValue(5)
        self._cycle_intensity_value = QLabel("5")
        self._cycle_intensity_slider.valueChanged.connect(
            lambda value: self._cycle_intensity_value.setText(str(value))
        )
        intensity_row.addWidget(self._cycle_intensity_slider)
        intensity_row.addWidget(self._cycle_intensity_value)
        layout.addLayout(intensity_row)

        layout.addWidget(QLabel("Behavior"))
        self._cycle_behavior_input = QLineEdit()
        self._cycle_behavior_input.setPlaceholderText("Example: Avoided replying and kept re-reading the email")
        self._cycle_behavior_input.textChanged.connect(self._update_nav)
        layout.addWidget(self._cycle_behavior_input)
        behavior_note = QLabel("Behavior = what you did next (including avoidance or checking).")
        behavior_note.setObjectName("CardMeta")
        behavior_note.setWordWrap(True)
        layout.addWidget(behavior_note)

        self._step4_validation = QLabel("")
        self._step4_validation.setObjectName("CardMeta")
        layout.addWidget(self._step4_validation)
        layout.addStretch()
        return widget

    def _build_step5(self) -> QWidget:
        widget, layout = self._build_step_container(4)
        layout.addWidget(
            self._card(
                "Lesson",
                "Helpful concern leads to action. Worry loops keep attention stuck. This quiz builds discrimination skill.",
            )
        )
        layout.addWidget(
            self._card(
                "Rule of thumb",
                "Helpful concern ends with an action. Unhelpful worry loops without resolution.",
            )
        )
        quiz_note = QLabel("Answer all items using your best judgment.")
        quiz_note.setObjectName("CardMeta")
        quiz_note.setWordWrap(True)
        layout.addWidget(quiz_note)

        self._quiz_groups: dict[str, QButtonGroup] = {}
        self._quiz_feedback: dict[str, QLabel] = {}
        for item_id, question, _correct in QUIZ_ITEMS:
            card = QFrame()
            card.setObjectName("Card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 12, 12, 12)
            card_layout.setSpacing(6)
            prompt = QLabel(question)
            prompt.setWordWrap(True)
            card_layout.addWidget(prompt)

            group = QButtonGroup(card)
            helpful = QRadioButton("Helpful concern")
            worry = QRadioButton("Unhelpful worry")
            helpful.toggled.connect(self._update_quiz_feedback)
            worry.toggled.connect(self._update_quiz_feedback)
            group.addButton(helpful)
            group.addButton(worry)
            card_layout.addWidget(helpful)
            card_layout.addWidget(worry)

            feedback = QLabel("")
            feedback.setObjectName("CardMeta")
            feedback.hide()
            card_layout.addWidget(feedback)

            self._quiz_groups[item_id] = group
            self._quiz_feedback[item_id] = feedback
            layout.addWidget(card)

        self._step5_validation = QLabel("")
        self._step5_validation.setObjectName("CardMeta")
        layout.addWidget(self._step5_validation)
        layout.addStretch()
        return widget

    def _build_step6(self) -> QWidget:
        widget, layout = self._build_step_container(5)
        layout.addWidget(
            self._card(
                "Lesson",
                "Anxiety patterns are easier to manage when linked to specific domains and recurring behaviors.",
            )
        )

        layout.addWidget(QLabel("Select domains where anxiety shows up:"))
        domains_note = QLabel("Start with the areas that affect your routine most.")
        domains_note.setObjectName("CardMeta")
        domains_note.setWordWrap(True)
        layout.addWidget(domains_note)
        self._domain_checks: dict[str, QCheckBox] = {}
        for domain in DOMAIN_OPTIONS:
            checkbox = QCheckBox(domain)
            checkbox.stateChanged.connect(self._rebuild_domain_patterns)
            self._domain_checks[domain] = checkbox
            layout.addWidget(checkbox)

        self._domain_other_input = QLineEdit()
        self._domain_other_input.setPlaceholderText("Other domain")
        self._domain_other_input.textChanged.connect(self._update_nav)
        layout.addWidget(self._domain_other_input)
        domain_other_note = QLabel("Example: Parenting, health tests, commuting, or social media.")
        domain_other_note.setObjectName("CardMeta")
        domain_other_note.setWordWrap(True)
        layout.addWidget(domain_other_note)

        self._domain_patterns_host = QVBoxLayout()
        self._domain_patterns_host.setSpacing(8)
        layout.addLayout(self._domain_patterns_host)

        layout.addWidget(QLabel("Optional reflection (1-3 sentences)"))
        self._domains_reflection_input = QTextEdit()
        self._domains_reflection_input.setPlaceholderText(
            "Example: 'When I saw pending tasks, I felt chest tension and avoided starting.'"
        )
        self._domains_reflection_input.textChanged.connect(self._update_nav)
        layout.addWidget(self._domains_reflection_input)

        self._step6_validation = QLabel("")
        self._step6_validation.setObjectName("CardMeta")
        layout.addWidget(self._step6_validation)

        self._domain_pattern_checks: dict[str, dict[str, QCheckBox]] = {}
        layout.addStretch()
        return widget

    def _build_step7(self) -> QWidget:
        widget, layout = self._build_step_container(6)
        layout.addWidget(
            self._card(
                "Lesson",
                "Values give direction during anxiety. Converting values into tiny habits improves follow-through.",
            )
        )

        layout.addWidget(QLabel("Select values (recommended 3-5, minimum 1):"))
        values_note = QLabel("Values are directions. Keep goals specific and realistic.")
        values_note.setObjectName("CardMeta")
        values_note.setWordWrap(True)
        layout.addWidget(values_note)
        self._value_checks: dict[str, QCheckBox] = {}
        for value in VALUE_OPTIONS:
            checkbox = QCheckBox(value)
            checkbox.stateChanged.connect(self._rebuild_value_cards)
            self._value_checks[value] = checkbox
            layout.addWidget(checkbox)

        self._value_other_input = QLineEdit()
        self._value_other_input.setPlaceholderText("Other value")
        self._value_other_input.textChanged.connect(self._update_nav)
        layout.addWidget(self._value_other_input)
        value_other_note = QLabel("Example: Spirituality, service, curiosity, or patience.")
        value_other_note.setObjectName("CardMeta")
        value_other_note.setWordWrap(True)
        layout.addWidget(value_other_note)

        self._value_cards_host = QVBoxLayout()
        self._value_cards_host.setSpacing(8)
        layout.addLayout(self._value_cards_host)

        self._step7_validation = QLabel("")
        self._step7_validation.setObjectName("CardMeta")
        layout.addWidget(self._step7_validation)

        self._value_inputs: dict[str, tuple[QTextEdit, QLineEdit]] = {}
        layout.addStretch()
        return widget

    def _build_step8(self) -> QWidget:
        widget, layout = self._build_step_container(7)
        layout.addWidget(
            self._card(
                "Lesson",
                "Baseline ratings help you compare future check-ins and observe real change over time.",
            )
        )
        baseline_note = QLabel("These ratings become your baseline for later comparison.")
        baseline_note.setObjectName("CardMeta")
        baseline_note.setWordWrap(True)
        layout.addWidget(baseline_note)

        self._baseline_frequency_slider = self._add_slider_row(
            layout,
            "How often did you feel anxious?",
            5,
        )
        self._baseline_intensity_slider = self._add_slider_row(
            layout,
            "Average worry intensity",
            5,
        )
        self._baseline_interference_slider = self._add_slider_row(
            layout,
            "How much did worry interfere?",
            5,
        )
        layout.addStretch()
        return widget

    def _build_step9(self) -> QWidget:
        widget, layout = self._build_step_container(8)
        layout.addWidget(
            self._card(
                "Lesson",
                "A specific, low-friction plan increases the chance of action in the next few days.",
            )
        )

        layout.addWidget(QLabel("Choose one action plan"))
        plan_note = QLabel("Pick one plan you can realistically do this week.")
        plan_note.setObjectName("CardMeta")
        plan_note.setWordWrap(True)
        layout.addWidget(plan_note)
        self._plan_choice_combo = QComboBox()
        self._plan_choice_combo.addItems(
            [
                "Do a daily check-in for 3 days",
                "Label worries as helpful vs unhelpful once per day",
                "Practice 2 minutes of breathing when anxiety > 6",
                "Review my values once this week",
                "Other",
            ]
        )
        self._plan_choice_combo.currentIndexChanged.connect(self._update_nav)
        layout.addWidget(self._plan_choice_combo)

        self._plan_other_input = QLineEdit()
        self._plan_other_input.setPlaceholderText("Other plan")
        self._plan_other_input.textChanged.connect(self._update_nav)
        layout.addWidget(self._plan_other_input)
        plan_other_note = QLabel("Example: 'Write one balanced thought after dinner each day.'")
        plan_other_note.setObjectName("CardMeta")
        plan_other_note.setWordWrap(True)
        layout.addWidget(plan_other_note)

        layout.addWidget(QLabel("Schedule"))
        self._schedule_choice_combo = QComboBox()
        self._schedule_choice_combo.addItems(["Morning", "Afternoon", "Evening", "Specific time"])
        self._schedule_choice_combo.currentIndexChanged.connect(self._update_nav)
        layout.addWidget(self._schedule_choice_combo)

        self._schedule_time_input = QLineEdit()
        self._schedule_time_input.setPlaceholderText("Specific time")
        self._schedule_time_input.textChanged.connect(self._update_nav)
        layout.addWidget(self._schedule_time_input)
        schedule_note = QLabel("Example: '7:30 PM after dinner'.")
        schedule_note.setObjectName("CardMeta")
        schedule_note.setWordWrap(True)
        layout.addWidget(schedule_note)

        self._confidence_slider = self._add_slider_row(layout, "Confidence (0-10)", 5)

        self._step9_validation = QLabel("")
        self._step9_validation.setObjectName("CardMeta")
        layout.addWidget(self._step9_validation)
        layout.addStretch()
        return widget

    def _build_step10(self) -> QWidget:
        widget, layout = self._build_step_container(9)
        layout.addWidget(
            self._card(
                "Lesson",
                "Reviewing key points consolidates learning and prepares you for the next module.",
            )
        )

        layout.addWidget(
            self._card("What you learned", "Anxiety involves thoughts, body signals, and behaviors.")
        )
        layout.addWidget(
            self._card("What you identified", "You mapped patterns and built a baseline.")
        )
        layout.addWidget(
            self._card("What you will try next", "You prepared a practical micro-plan for this week.")
        )
        finish_note = QLabel("Module 1 is ready to complete.")
        finish_note.setObjectName("CardTitle")
        layout.addWidget(finish_note)
        layout.addStretch()
        return widget

    def _add_slider_row(self, layout: QVBoxLayout, title: str, default: int) -> QSlider:
        layout.addWidget(QLabel(title))
        row = QHBoxLayout()
        row.setSpacing(8)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 10)
        slider.setValue(default)
        value = QLabel(str(default))
        slider.valueChanged.connect(lambda v: value.setText(str(v)))
        slider.valueChanged.connect(self._update_nav)
        row.addWidget(slider)
        row.addWidget(value)
        layout.addLayout(row)
        return slider

    def _build_module1_overview_page(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        top = QHBoxLayout()
        top.setSpacing(8)
        back_btn = QPushButton("Back to modules")
        back_btn.clicked.connect(self._back_to_modules)
        self._resume_module_btn = QPushButton("Resume Module")
        self._resume_module_btn.setObjectName("AccentButton")
        self._resume_module_btn.clicked.connect(self._resume_module1)
        top.addWidget(back_btn)
        top.addWidget(self._resume_module_btn)
        top.addStretch()
        root.addLayout(top)

        scroll = RoundedScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        body = QWidget()
        body.setObjectName("ScrollContent")
        body.setAutoFillBackground(True)
        body.setAttribute(Qt.WA_StyledBackground, True)
        self._module1_overview_layout = QVBoxLayout(body)
        self._module1_overview_layout.setContentsMargins(12, 12, 12, 12)
        self._module1_overview_layout.setSpacing(10)
        self._module1_overview_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(body)
        root.addWidget(scroll, 1)
        return page

    def _build_module_placeholder_overview_page(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        back_btn = QPushButton("Back to modules")
        back_btn.clicked.connect(self._back_to_modules)
        root.addWidget(back_btn)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(8)

        self._placeholder_title = QLabel("Module Overview")
        self._placeholder_title.setObjectName("CardTitle")
        self._placeholder_status = QLabel("Status: LOCKED")
        self._placeholder_status.setObjectName("CardMeta")
        self._placeholder_progress = QLabel("Progress: 0%")
        self._placeholder_progress.setObjectName("CardMeta")
        self._placeholder_content = QLabel("No module inputs yet.")
        self._placeholder_content.setObjectName("CardMeta")

        card_layout.addWidget(self._placeholder_title)
        card_layout.addWidget(self._placeholder_status)
        card_layout.addWidget(self._placeholder_progress)
        card_layout.addWidget(self._placeholder_content)
        root.addWidget(card)
        root.addStretch()
        return page

    def _open_module1(self) -> None:
        self._module1_active = True
        self._load_module1_data(force_step=None)
        self._stack.setCurrentIndex(1)
        self._update_nav()

    def _open_module1_overview(self) -> None:
        self._load_module1_data(force_step=None)
        self._render_module1_overview()
        self._stack.setCurrentIndex(2)

    def _open_module_placeholder(self, module_id: str) -> None:
        progress = self._learning_service.get_progress(module_id)
        status = self._normalize_status(progress.status if progress else "LOCKED")
        percent = int(progress.progress_percent) if progress else 0
        module_title = next((m["title"] for m in MODULES if m["id"] == module_id), module_id)

        self._placeholder_title.setText(module_title)
        self._placeholder_status.setText(f"Status: {status}")
        self._placeholder_progress.setText(f"Progress: {percent}%")
        self._placeholder_content.setText("No module inputs yet.")
        self._stack.setCurrentIndex(3)

    def _resume_module1(self) -> None:
        resume_step = int(self._module1_data.get("last_step_index", 0) or 0)
        resume_step = max(0, min(9, resume_step))
        self._module1_active = True
        self._load_module1_data(force_step=resume_step)
        self._stack.setCurrentIndex(1)

    def _back_to_modules(self) -> None:
        if self._module1_active:
            self._save_current_step()
        self._module1_active = False
        self.show_modules()

    def _update_quiz_feedback(self) -> None:
        for item_id, _question, correct in QUIZ_ITEMS:
            selected = ""
            for button in self._quiz_groups[item_id].buttons():
                if button.isChecked():
                    selected = button.text()
                    break
            label = self._quiz_feedback[item_id]
            _ = selected
            _ = correct
            label.setText("")
        self._update_nav()

    def _rebuild_domain_patterns(self) -> None:
        while self._domain_patterns_host.count():
            item = self._domain_patterns_host.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._domain_pattern_checks = {}
        for domain, checkbox in self._domain_checks.items():
            if not checkbox.isChecked():
                continue
            card = QFrame()
            card.setObjectName("Card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 12, 12, 12)
            card_layout.setSpacing(6)
            card_layout.addWidget(QLabel(f"Patterns for {domain}"))

            self._domain_pattern_checks[domain] = {}
            for pattern in PATTERN_OPTIONS:
                pattern_check = QCheckBox(pattern)
                pattern_check.stateChanged.connect(self._update_nav)
                self._domain_pattern_checks[domain][pattern] = pattern_check
                card_layout.addWidget(pattern_check)

            self._domain_patterns_host.addWidget(card)
        self._update_nav()

    def _rebuild_value_cards(self) -> None:
        while self._value_cards_host.count():
            item = self._value_cards_host.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._value_inputs = {}
        for value, checkbox in self._value_checks.items():
            if not checkbox.isChecked():
                continue

            card = QFrame()
            card.setObjectName("Card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 12, 12, 12)
            card_layout.setSpacing(6)
            card_layout.addWidget(QLabel(f"Value: {value}"))

            card_layout.addWidget(QLabel("Goal"))
            goal_input = QTextEdit()
            goal_input.setPlaceholderText(
                "If anxiety were less in the way, how would life look here?"
            )
            goal_input.textChanged.connect(self._update_nav)
            card_layout.addWidget(goal_input)

            card_layout.addWidget(QLabel("Tiny habit"))
            habit_input = QLineEdit()
            habit_input.setPlaceholderText("One small action this week")
            habit_input.textChanged.connect(self._update_nav)
            card_layout.addWidget(habit_input)

            helper = QLabel("Example: Keep this practical and specific.")
            helper.setObjectName("CardMeta")
            card_layout.addWidget(helper)

            self._value_inputs[value] = (goal_input, habit_input)
            self._value_cards_host.addWidget(card)
        self._update_nav()

    def _is_step_valid(self, step: int) -> bool:
        if step == 0:
            valid = any(cb.isChecked() for cb in self._reason_checks.values())
            self._step1_validation.setText("" if valid else "Select at least one reason.")
            return valid

        if step == 1:
            valid = any(rb.isChecked() for rb in self._dominant_buttons.values())
            self._step2_validation.setText("" if valid else "Choose one dominant area.")
            return valid

        if step == 2:
            valid = any(cb.isChecked() for cb in self._body_signal_checks.values())
            self._step3_validation.setText("" if valid else "Select at least one body signal.")
            return valid

        if step == 3:
            valid = bool(
                self._cycle_trigger_input.text().strip()
                and self._cycle_thought_input.text().strip()
                and self._cycle_behavior_input.text().strip()
            )
            self._step4_validation.setText("" if valid else "Complete trigger, thought, and behavior.")
            return valid

        if step == 4:
            valid = all(any(btn.isChecked() for btn in group.buttons()) for group in self._quiz_groups.values())
            self._step5_validation.setText("" if valid else "Answer all quiz items.")
            return valid

        if step == 5:
            selected_domains = [name for name, cb in self._domain_checks.items() if cb.isChecked()]
            if not selected_domains:
                self._step6_validation.setText("Select at least one domain.")
                return False
            for domain in selected_domains:
                checks = self._domain_pattern_checks.get(domain, {})
                if checks and not any(cb.isChecked() for cb in checks.values()):
                    self._step6_validation.setText("Select at least one pattern per chosen domain.")
                    return False
            self._step6_validation.setText("")
            return True

        if step == 6:
            selected_values = [name for name, cb in self._value_checks.items() if cb.isChecked()]
            if not selected_values:
                self._step7_validation.setText("Select at least one value.")
                return False
            for value in selected_values:
                pair = self._value_inputs.get(value)
                if pair is None:
                    self._step7_validation.setText("Add goal and tiny habit for each selected value.")
                    return False
                goal, habit = pair
                if not goal.toPlainText().strip() or not habit.text().strip():
                    self._step7_validation.setText("Add goal and tiny habit for each selected value.")
                    return False
            if self._value_checks["Other"].isChecked() and not self._value_other_input.text().strip():
                self._step7_validation.setText("Fill in the Other value name.")
                return False
            self._step7_validation.setText("")
            return True

        if step == 8:
            if self._plan_choice_combo.currentText() == "Other" and not self._plan_other_input.text().strip():
                self._step9_validation.setText("Enter your custom plan.")
                return False
            if self._schedule_choice_combo.currentText() == "Specific time" and not self._schedule_time_input.text().strip():
                self._step9_validation.setText("Enter a specific time.")
                return False
            self._step9_validation.setText("")
            return True

        return True

    def _update_nav(self) -> None:
        if not self._module1_ui_ready:
            return
        if self._active_media_step != self._current_step:
            self._update_left_panel_for_step(self._current_step)
        self._steps.setCurrentIndex(self._current_step)
        self._prev_btn.setEnabled(self._current_step > 0)
        self._step_count_label.setText(f"Step {self._current_step + 1} of 10")
        self._step_progress.setValue(int(((self._current_step + 1) / 10) * 100))

        self._plan_other_input.setVisible(self._plan_choice_combo.currentText() == "Other")
        self._schedule_time_input.setVisible(self._schedule_choice_combo.currentText() == "Specific time")

        if self._current_step == 9:
            self._next_btn.setText("Finish")
            self._next_btn.setEnabled(True)
        else:
            self._next_btn.setText("Next")
            self._next_btn.setEnabled(self._is_step_valid(self._current_step))

    def _prev_step(self) -> None:
        if self._current_step <= 0:
            return
        self._save_current_step()
        self._current_step -= 1
        self._update_nav()

    def _next_step(self) -> None:
        if self._current_step < 9 and not self._is_step_valid(self._current_step):
            self._update_nav()
            return

        self._save_current_step()
        if self._current_step == 9:
            self._finish_module1()
            return
        self._current_step += 1
        self._update_nav()

    def _update_module_progress(self) -> None:
        current = self._learning_service.get_progress("module_1")
        if current and self._normalize_status(current.status) == "COMPLETE":
            return
        percent = int(((self._current_step + 1) / 10) * 100)
        self._learning_service.update_progress("module_1", "UNLOCKED", percent)

    def _save_current_step(self) -> None:
        self._module1_data.update(self._collect_step_payload(self._current_step))
        self._module1_data["last_step_index"] = self._current_step
        self._module_data_service.update_module_data("module_1", self._module1_data)
        self._update_module_progress()

    def _collect_step_payload(self, step: int) -> dict[str, Any]:
        if step == 0:
            return {
                "reasons_selected": [name for name, cb in self._reason_checks.items() if cb.isChecked()],
                "reason_other_text": self._reason_other_input.text().strip(),
            }

        if step == 1:
            dominant = ""
            for key, radio in self._dominant_buttons.items():
                if radio.isChecked():
                    dominant = key
                    break
            return {"dominant_component": dominant}

        if step == 2:
            return {
                "body_signals_selected": [name for name, cb in self._body_signal_checks.items() if cb.isChecked()]
            }

        if step == 3:
            return {
                "worry_cycle_example": {
                    "trigger": self._cycle_trigger_input.text().strip(),
                    "thought": self._cycle_thought_input.text().strip(),
                    "feeling_intensity": self._cycle_intensity_slider.value(),
                    "behavior": self._cycle_behavior_input.text().strip(),
                }
            }

        if step == 4:
            results = []
            for item_id, _question, correct in QUIZ_ITEMS:
                choice = ""
                for button in self._quiz_groups[item_id].buttons():
                    if button.isChecked():
                        choice = button.text()
                        break
                results.append(
                    {
                        "item_id": item_id,
                        "user_choice": choice,
                        "is_correct": choice == correct,
                    }
                )
            return {"worry_quiz_results": results}

        if step == 5:
            selected_domains = []
            domain_patterns: dict[str, list[str]] = {}
            for domain, checkbox in self._domain_checks.items():
                if not checkbox.isChecked():
                    continue
                saved_name = domain
                if domain == "Other":
                    saved_name = self._domain_other_input.text().strip() or "Other"
                selected_domains.append(saved_name)
                checks = self._domain_pattern_checks.get(domain, {})
                domain_patterns[saved_name] = [
                    name for name, cb in checks.items() if cb.isChecked()
                ]

            return {
                "domains_selected": selected_domains,
                "domain_patterns": domain_patterns,
                "domain_other_text": self._domain_other_input.text().strip(),
                "recent_example_text": self._domains_reflection_input.toPlainText().strip(),
            }

        if step == 6:
            values_selected: list[str] = []
            values_goals: list[dict[str, str]] = []
            for value, checkbox in self._value_checks.items():
                if not checkbox.isChecked():
                    continue
                saved_name = value
                if value == "Other":
                    saved_name = self._value_other_input.text().strip() or "Other"
                values_selected.append(saved_name)

                goal_input, habit_input = self._value_inputs.get(value, (None, None))
                values_goals.append(
                    {
                        "value_name": saved_name,
                        "goal_text": goal_input.toPlainText().strip() if goal_input else "",
                        "tiny_habit_text": habit_input.text().strip() if habit_input else "",
                    }
                )

            return {
                "values_selected": values_selected,
                "other_value_text": self._value_other_input.text().strip(),
                "values_goals": values_goals,
            }

        if step == 7:
            return {
                "baseline_frequency": self._baseline_frequency_slider.value(),
                "baseline_worry_intensity": self._baseline_intensity_slider.value(),
                "baseline_interference": self._baseline_interference_slider.value(),
            }

        if step == 8:
            return {
                "micro_plan": {
                    "plan_choice": self._plan_choice_combo.currentText(),
                    "plan_other_text": self._plan_other_input.text().strip(),
                    "schedule_choice": self._schedule_choice_combo.currentText(),
                    "schedule_time_text": self._schedule_time_input.text().strip(),
                    "confidence": self._confidence_slider.value(),
                }
            }

        return {}

    def _load_module1_data(self, force_step: int | None) -> None:
        saved = self._module_data_service.get_module_data("module_1")
        self._module1_data = dict(saved.data) if saved else {}
        if force_step is not None:
            self._current_step = force_step
        else:
            self._current_step = int(self._module1_data.get("last_step_index", 0) or 0)
        self._current_step = max(0, min(9, self._current_step))
        self._apply_module1_data()
        self._update_nav()

    def _apply_module1_data(self) -> None:
        reasons = set(self._module1_data.get("reasons_selected", []))
        for name, checkbox in self._reason_checks.items():
            checkbox.setChecked(name in reasons)
        self._reason_other_input.setText(self._module1_data.get("reason_other_text", ""))

        dominant = self._module1_data.get("dominant_component", "")
        for key, radio in self._dominant_buttons.items():
            radio.setChecked(key == dominant)

        signals = set(self._module1_data.get("body_signals_selected", []))
        for name, checkbox in self._body_signal_checks.items():
            checkbox.setChecked(name in signals)

        cycle = self._module1_data.get("worry_cycle_example", {})
        self._cycle_trigger_input.setText(cycle.get("trigger", ""))
        self._cycle_thought_input.setText(cycle.get("thought", ""))
        self._cycle_intensity_slider.setValue(int(cycle.get("feeling_intensity", 5)))
        self._cycle_behavior_input.setText(cycle.get("behavior", ""))

        quiz_map = {item.get("item_id"): item for item in self._module1_data.get("worry_quiz_results", [])}
        for item_id, _question, _correct in QUIZ_ITEMS:
            selected = quiz_map.get(item_id, {}).get("user_choice", "")
            for button in self._quiz_groups[item_id].buttons():
                button.setChecked(button.text() == selected)
        self._update_quiz_feedback()

        selected_domains = self._module1_data.get("domains_selected", [])
        other_domain = self._module1_data.get("domain_other_text", "")
        self._domain_other_input.setText(other_domain)

        for domain, checkbox in self._domain_checks.items():
            if domain == "Other":
                has_other = bool(other_domain)
                if not has_other:
                    has_other = any(name not in DOMAIN_OPTIONS for name in selected_domains)
                checkbox.setChecked(has_other)
            else:
                checkbox.setChecked(domain in selected_domains)

        self._rebuild_domain_patterns()
        saved_patterns = self._module1_data.get("domain_patterns", {})
        for domain, checks in self._domain_pattern_checks.items():
            key = domain
            if domain == "Other":
                key = other_domain or "Other"
            selected = set(saved_patterns.get(key, []))
            for pattern, checkbox in checks.items():
                checkbox.setChecked(pattern in selected)
        self._domains_reflection_input.setPlainText(self._module1_data.get("recent_example_text", ""))

        selected_values = self._module1_data.get("values_selected", [])
        other_value = self._module1_data.get("other_value_text", "")
        self._value_other_input.setText(other_value)
        for value, checkbox in self._value_checks.items():
            if value == "Other":
                checkbox.setChecked(bool(other_value) or "Other" in selected_values)
            else:
                checkbox.setChecked(value in selected_values)

        self._rebuild_value_cards()
        goals_map = {
            row.get("value_name", ""): row
            for row in self._module1_data.get("values_goals", [])
        }
        for value, pair in self._value_inputs.items():
            key = value if value != "Other" else (other_value or "Other")
            goal_input, habit_input = pair
            goal_input.setPlainText(goals_map.get(key, {}).get("goal_text", ""))
            habit_input.setText(goals_map.get(key, {}).get("tiny_habit_text", ""))

        self._baseline_frequency_slider.setValue(int(self._module1_data.get("baseline_frequency", 5)))
        self._baseline_intensity_slider.setValue(int(self._module1_data.get("baseline_worry_intensity", 5)))
        self._baseline_interference_slider.setValue(int(self._module1_data.get("baseline_interference", 5)))

        micro_plan = self._module1_data.get("micro_plan", {})
        if micro_plan:
            plan_index = self._plan_choice_combo.findText(micro_plan.get("plan_choice", ""))
            if plan_index >= 0:
                self._plan_choice_combo.setCurrentIndex(plan_index)
            schedule_index = self._schedule_choice_combo.findText(micro_plan.get("schedule_choice", ""))
            if schedule_index >= 0:
                self._schedule_choice_combo.setCurrentIndex(schedule_index)
            self._plan_other_input.setText(micro_plan.get("plan_other_text", ""))
            self._schedule_time_input.setText(micro_plan.get("schedule_time_text", ""))
            self._confidence_slider.setValue(int(micro_plan.get("confidence", 5)))

    def _finish_module1(self) -> None:
        self._save_current_step()
        self._module1_data["last_step_index"] = 9
        self._module_data_service.update_module_data("module_1", self._module1_data)
        self._learning_service.update_progress(
            "module_1",
            "COMPLETE",
            100,
            completed_at=datetime.now(UTC),
        )

        module2_progress = self._learning_service.get_progress("module_2")
        if module2_progress and self._normalize_status(module2_progress.status) == "LOCKED":
            self._learning_service.update_progress("module_2", "UNLOCKED", 0)

        self.module_completed.emit("module_1")
        self._back_to_modules()

    def _render_module1_overview(self) -> None:
        while self._module1_overview_layout.count():
            item = self._module1_overview_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        def add_card(title: str, body: str) -> None:
            card = QFrame()
            card.setObjectName("Card")
            card.setAttribute(Qt.WA_StyledBackground, True)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 12, 12, 12)
            card_layout.setSpacing(6)
            title_label = QLabel(title)
            title_label.setObjectName("CardTitle")
            body_label = QLabel(body if body.strip() else "-")
            body_label.setObjectName("CardMeta")
            body_label.setWordWrap(True)
            card_layout.addWidget(title_label)
            card_layout.addWidget(body_label)
            self._module1_overview_layout.addWidget(card)

        reasons = ", ".join(self._module1_data.get("reasons_selected", []))
        if self._module1_data.get("reason_other_text"):
            reasons = f"{reasons}\nOther: {self._module1_data.get('reason_other_text')}" if reasons else f"Other: {self._module1_data.get('reason_other_text')}"
        add_card("Step 1 - Reasons", reasons)

        add_card("Step 2 - Dominant Component", self._module1_data.get("dominant_component", ""))

        add_card(
            "Step 3 - Body Signals",
            ", ".join(self._module1_data.get("body_signals_selected", [])),
        )

        cycle = self._module1_data.get("worry_cycle_example", {})
        cycle_text = (
            f"Trigger: {cycle.get('trigger', '')}\n"
            f"Thought: {cycle.get('thought', '')}\n"
            f"Feeling intensity: {cycle.get('feeling_intensity', '')}\n"
            f"Behavior: {cycle.get('behavior', '')}"
        )
        add_card("Step 4 - Worry Cycle Example", cycle_text)

        quiz_lines = []
        quiz_lookup = {
            row.get("item_id", ""): row for row in self._module1_data.get("worry_quiz_results", [])
        }
        for index, (item_id, question, correct_answer) in enumerate(QUIZ_ITEMS, start=1):
            preview = question if len(question) <= 64 else f"{question[:61]}..."
            row = quiz_lookup.get(item_id, {})
            choice = str(row.get("user_choice", "")).strip()
            if not choice:
                result = "Not answered"
                choice = "-"
            else:
                is_correct = row.get("is_correct")
                if isinstance(is_correct, bool):
                    result = "Correct" if is_correct else "Wrong"
                else:
                    result = "Correct" if choice == correct_answer else "Wrong"
            quiz_lines.append(f"{index}. {preview} -> {choice} ({result})")
        add_card("Step 5 - Concern vs Worry Quiz", "\n".join(quiz_lines))

        domains = self._module1_data.get("domains_selected", [])
        patterns = self._module1_data.get("domain_patterns", {})
        domains_text_parts = [f"Domains: {', '.join(domains)}"]
        for domain, values in patterns.items():
            domains_text_parts.append(f"{domain}: {', '.join(values)}")
        reflection = self._module1_data.get("recent_example_text", "")
        if reflection:
            domains_text_parts.append(f"Reflection: {reflection}")
        add_card("Step 6 - Domains and Patterns", "\n".join(domains_text_parts))

        values_lines = [f"Values: {', '.join(self._module1_data.get('values_selected', []))}"]
        for row in self._module1_data.get("values_goals", []):
            values_lines.append(
                f"{row.get('value_name', '')} -> Goal: {row.get('goal_text', '')} | Habit: {row.get('tiny_habit_text', '')}"
            )
        add_card("Step 7 - Values, Goals, Habits", "\n".join(values_lines))

        add_card(
            "Step 8 - Baseline Ratings",
            (
                f"Frequency: {self._module1_data.get('baseline_frequency', '-')}\n"
                f"Worry intensity: {self._module1_data.get('baseline_worry_intensity', '-')}\n"
                f"Interference: {self._module1_data.get('baseline_interference', '-')}"
            ),
        )

        micro_plan = self._module1_data.get("micro_plan", {})
        add_card(
            "Step 9 - Micro-Plan",
            (
                f"Plan: {micro_plan.get('plan_choice', '')}\n"
                f"Other: {micro_plan.get('plan_other_text', '')}\n"
                f"Schedule: {micro_plan.get('schedule_choice', '')}\n"
                f"Specific time: {micro_plan.get('schedule_time_text', '')}\n"
                f"Confidence: {micro_plan.get('confidence', '')}"
            ),
        )

        status = self._learning_service.get_progress("module_1")
        status_label = self._normalize_status(status.status if status else "LOCKED")
        add_card("Step 10 - Completion", f"Module status: {status_label}")
