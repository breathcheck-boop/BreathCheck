from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QSlider,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)

from anxiety_app.domain.services import (
    LearningService,
    ModuleDataService,
    ToolUsageService,
    UserSettingsService,
)
from anxiety_app.ui.widgets.rounded_scroll_area import RoundedScrollArea
from anxiety_app.ui.widgets.tools_view import BreathingWidget


MODULES = [
    {
        "id": "module_1",
        "title": "Understanding Anxiety",
        "description": "Psychoeducation on anxiety, worry cycles, and baseline tracking.",
    },
    {
        "id": "module_2",
        "title": "Relaxation",
        "description": "Breathing, relaxation skills, and body-based calming.",
    },
    {
        "id": "module_3",
        "title": "Our Thoughts",
        "description": "How thoughts and beliefs shape anxiety patterns.",
    },
    {
        "id": "module_4",
        "title": "Changing Thoughts",
        "description": "Cognitive restructuring and balanced thinking.",
    },
    {
        "id": "module_5",
        "title": "Coping with Worry",
        "description": "Problem solving, worry scheduling, and exposure concepts.",
    },
    {
        "id": "module_6",
        "title": "Lifestyle Factors & Relapse Prevention",
        "description": "Sleep, routines, and maintaining progress.",
    },
]


@dataclass
class FieldConfig:
    key: str
    label: str
    kind: str  # text, multiline, choice, slider, checkboxes
    options: list[str] | None = None
    min_val: int = 0
    max_val: int = 10


@dataclass
class ModuleConfig:
    module_id: str
    intro: str
    lessons: list[tuple[str, str]]
    activity_fields: list[FieldConfig]
    reflection_prompt: str
    summary_points: list[str]
    completion_text: str


MODULE_CONFIGS: dict[str, ModuleConfig] = {
    "module_1": ModuleConfig(
        module_id="module_1",
        intro="Understand the nature of anxiety, how it shows up in body and mind, and set a baseline for tracking.",
        lessons=[
            (
                "Nature of anxiety",
                "Anxiety is a normal survival response that becomes distressing when it stays on too long.",
            ),
            (
                "Fight-or-flight",
                "Your body prepares you to act fast—even when the threat is uncertain or imagined.",
            ),
            (
                "Worry cycle",
                "Thoughts, feelings, body signals, and behaviors can reinforce each other.",
            ),
            (
                "Body–mind link",
                "Physical sensations and anxious thoughts amplify each other in a loop.",
            ),
        ],
        activity_fields=[
            FieldConfig("baseline_anxiety", "Baseline anxiety today (0–10)", "slider"),
            FieldConfig("main_triggers", "Main triggers you notice", "multiline"),
            FieldConfig("body_signals", "Body signals you feel most", "multiline"),
        ],
        reflection_prompt="What is one thing you learned about your anxiety today?",
        summary_points=[
            "You learned the basics of anxiety and the worry cycle.",
            "You identified triggers and body signals.",
            "You recorded a starting baseline for tracking.",
        ],
        completion_text="You’ve completed Module 1. Take a moment to acknowledge your progress.",
    ),
    "module_2": ModuleConfig(
        module_id="module_2",
        intro="Build relaxation skills to calm the body and reduce tension.",
        lessons=[
            ("Physical tension awareness", "Noticing tension is the first step to releasing it."),
            ("Breathing skills", "Slow, steady breathing signals safety to your nervous system."),
            ("Short relaxation", "Brief exercises can reset your stress response in minutes."),
        ],
        activity_fields=[
            FieldConfig("tension_areas", "Where do you feel tension most?", "multiline"),
            FieldConfig(
                "preferred_pace",
                "Preferred breathing pace",
                "choice",
                options=["4-4-6", "4-4-4", "5-5-5"],
            ),
            FieldConfig("after_breathing", "How calm do you feel after breathing? (0–10)", "slider"),
            FieldConfig("relaxation_note", "Which relaxation cue helped most?", "multiline"),
        ],
        reflection_prompt="What helped you feel calmer during relaxation?",
        summary_points=[
            "You identified tension areas.",
            "You practiced guided breathing.",
            "You rated how your body responded.",
        ],
        completion_text="Module 2 complete. You can return to breathing anytime.",
    ),
    "module_3": ModuleConfig(
        module_id="module_3",
        intro="Explore how thoughts, assumptions, and beliefs shape anxiety.",
        lessons=[
            ("Thoughts and anxiety", "Thoughts can trigger emotional and physical responses."),
            ("Cognitive distortions", "Patterns like catastrophizing or mind-reading amplify worry."),
            ("Assumptions", "Quick interpretations often drive anxiety reactions."),
            ("Core beliefs", "Deep beliefs shape how you interpret situations."),
        ],
        activity_fields=[
            FieldConfig("common_distortions", "Distortions you notice", "checkboxes", options=[
                "Catastrophizing", "All-or-nothing", "Mind-reading", "Overgeneralizing", "Should statements",
            ]),
            FieldConfig("example_thought", "Example anxious thought", "multiline"),
            FieldConfig("assumption", "Underlying assumption (if any)", "multiline"),
            FieldConfig("core_belief", "Possible core belief", "multiline"),
        ],
        reflection_prompt="How do your thoughts influence your anxiety?",
        summary_points=[
            "You identified thought patterns.",
            "You captured an example anxious thought.",
        ],
        completion_text="Module 3 complete. Awareness is the first step to change.",
    ),
    "module_4": ModuleConfig(
        module_id="module_4",
        intro="Practice changing anxious thoughts into more balanced alternatives.",
        lessons=[
            ("Cognitive restructuring", "Challenge anxious thoughts with evidence."),
            ("Balanced thinking", "Aim for realistic, compassionate interpretations."),
            ("Re-rating intensity", "Notice how emotion shifts after a balanced thought."),
        ],
        activity_fields=[
            FieldConfig("situation", "Situation", "multiline"),
            FieldConfig("automatic_thought", "Automatic thought", "multiline"),
            FieldConfig("evidence_for", "Evidence for", "multiline"),
            FieldConfig("evidence_against", "Evidence against", "multiline"),
            FieldConfig("balanced_thought", "Balanced thought", "multiline"),
            FieldConfig("emotion_rerate", "Re-rate emotion intensity (0–10)", "slider"),
        ],
        reflection_prompt="What shifts when you practice balanced thinking?",
        summary_points=[
            "You practiced a thought challenge.",
            "You re-rated emotional intensity.",
        ],
        completion_text="Module 4 complete. Keep practicing balanced thinking.",
    ),
    "module_5": ModuleConfig(
        module_id="module_5",
        intro="Learn practical strategies for coping with worry and avoiding avoidance.",
        lessons=[
            ("Internal vs external worries", "Some worries can be solved; others need acceptance."),
            ("Problem-solving", "Structured steps reduce overwhelm."),
            ("Worry scheduling", "Set a time to contain worry loops."),
            ("Avoidance and exposure", "Gradual approach builds confidence."),
        ],
        activity_fields=[
            FieldConfig("worry_type", "Primary worry type", "choice", options=["Internal", "External", "Both"]),
            FieldConfig("problem_steps", "One practical step you can take", "multiline"),
            FieldConfig("worry_time", "Planned worry time (e.g., 6:00 PM)", "text"),
            FieldConfig("avoidance", "One avoided situation to approach gradually", "multiline"),
            FieldConfig("exposure_step", "Small exposure step you can try", "multiline"),
        ],
        reflection_prompt="What feels most doable for coping with worry this week?",
        summary_points=[
            "You identified worry type and a problem-solving step.",
            "You scheduled worry time and noted avoidance targets.",
        ],
        completion_text="Module 5 complete. Small steps build confidence.",
    ),
    "module_6": ModuleConfig(
        module_id="module_6",
        intro="Strengthen lifestyle supports and plan for setbacks.",
        lessons=[
            ("Sleep hygiene", "Consistent routines support emotional balance."),
            ("Nutrition awareness", "Stable energy helps regulate stress."),
            ("Physical activity", "Movement helps regulate stress."),
            ("Mindfulness basics", "Brief awareness practices calm the mind."),
            ("Relapse prevention", "Setbacks are normal—plan for recovery."),
        ],
        activity_fields=[
            FieldConfig("sleep_plan", "One sleep habit to improve", "multiline"),
            FieldConfig("nutrition_plan", "One nutrition habit to support energy", "multiline"),
            FieldConfig("movement_plan", "One movement habit to try", "multiline"),
            FieldConfig("mindfulness_plan", "Brief mindfulness practice to try", "multiline"),
            FieldConfig("safe_place", "Safe place visualization (describe it)", "multiline"),
            FieldConfig("relapse_plan", "Signs of setback + support plan", "multiline"),
            FieldConfig("maintenance_plan", "Maintenance plan for the next month", "multiline"),
        ],
        reflection_prompt="How will you support yourself if anxiety returns?",
        summary_points=[
            "You set lifestyle support habits.",
            "You created a safe place plan and relapse plan.",
            "You outlined a maintenance plan.",
        ],
        completion_text="Module 6 complete. You’ve built a long-term plan.",
    ),
}


class LearnView(QWidget):
    module_completed = pyqtSignal(str)

    def __init__(
        self,
        learning_service: LearningService,
        module_data_service: ModuleDataService,
        tool_usage_service: ToolUsageService,
        user_settings_service: UserSettingsService,
    ) -> None:
        super().__init__()
        self.setObjectName("ViewRoot")
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._learning_service = learning_service
        self._module_data_service = module_data_service
        self._tool_usage_service = tool_usage_service
        self._user_settings_service = user_settings_service

        self._module_stack = QStackedWidget()
        self._current_module_id: str | None = None
        self._current_step = 0
        self._activity_widgets: dict[str, QWidget] = {}
        self._reflection_widget: QTextEdit | None = None
        self._completion_check: QCheckBox | None = None
        self._breathing_widget: BreathingWidget | None = None

        self._overview_page = self._build_overview()
        self._flow_page = self._build_flow_page()
        self._module_stack.addWidget(self._overview_page)
        self._module_stack.addWidget(self._flow_page)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._module_stack)

        self._refresh_overview()

    def _build_overview(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)

        self._reminder_card = QFrame()
        self._reminder_card.setObjectName("Card")
        reminder_layout = QVBoxLayout(self._reminder_card)
        reminder_title = QLabel("Reminders")
        reminder_title.setObjectName("CardTitle")
        reminder_layout.addWidget(reminder_title)
        self._reminder_label = QLabel("")
        self._reminder_label.setWordWrap(True)
        reminder_layout.addWidget(self._reminder_label)
        self._continue_label = QLabel("")
        self._continue_label.setWordWrap(True)
        self._continue_label.setObjectName("CardMeta")
        reminder_layout.addWidget(self._continue_label)
        layout.addWidget(self._reminder_card)

        scroll = RoundedScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        content = QWidget()
        content.setObjectName("ScrollContent")
        content.setAutoFillBackground(True)
        content.setAttribute(Qt.WA_StyledBackground, True)
        self._overview_grid = QGridLayout(content)
        self._overview_grid.setSpacing(14)
        self._overview_grid.setColumnStretch(0, 1)
        self._overview_grid.setColumnStretch(1, 1)
        self._overview_grid.setContentsMargins(8, 8, 8, 8)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        return container

    def _build_flow_page(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        self._back_to_list = QPushButton("Back to modules")
        self._back_to_list.clicked.connect(self._return_to_overview)
        header_row.addWidget(self._back_to_list)
        header_row.addStretch()
        layout.addLayout(header_row)

        progress_row = QHBoxLayout()
        self._step_label = QLabel("Step 1 of 6")
        self._step_label.setObjectName("CardMeta")
        self._percent_label = QLabel("0%")
        self._percent_label.setObjectName("CardMeta")
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        progress_row.addWidget(self._step_label)
        progress_row.addSpacing(8)
        progress_row.addWidget(self._percent_label)
        progress_row.addStretch()
        progress_row.addWidget(self._progress_bar, 1)
        layout.addLayout(progress_row)

        self._step_stack = QStackedWidget()
        layout.addWidget(self._step_stack, 1)

        nav_row = QHBoxLayout()
        self._back_btn = QPushButton("Back")
        self._back_btn.clicked.connect(self._prev_step)
        self._next_btn = QPushButton("Next")
        self._next_btn.setObjectName("AccentButton")
        self._next_btn.clicked.connect(self._next_step)
        nav_row.addWidget(self._back_btn)
        nav_row.addStretch()
        nav_row.addWidget(self._next_btn)
        layout.addLayout(nav_row)
        return container

    def _refresh_overview(self) -> None:
        self._ensure_progress_rows()
        while self._overview_grid.count():
            item = self._overview_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        progress_map = {
            entry.module_id: entry for entry in self._learning_service.list_progress()
        }
        reminder_text = self._build_reminder_text(progress_map)
        if reminder_text:
            self._reminder_label.setText(reminder_text)
            self._reminder_card.show()
        else:
            self._reminder_card.hide()

        continue_text = self._build_continue_text(progress_map)
        self._continue_label.setText(continue_text)
        for index, module in enumerate(MODULES):
            module_id = module["id"]
            progress = progress_map.get(module_id)
            status = (progress.status if progress else "LOCKED").upper()
            if status == "COMPLETED":
                status = "COMPLETE"

            card = QFrame()
            card.setObjectName("Card")
            card.setProperty("status", status.lower())
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(6)

            title = QLabel(module["title"])
            title.setObjectName("CardTitle")
            title.setWordWrap(True)
            card_layout.addWidget(title)

            desc = QLabel(module["description"])
            desc.setObjectName("CardMeta")
            desc.setWordWrap(True)
            card_layout.addWidget(desc)

            status_label = QLabel(
                "Complete" if status == "COMPLETE" else "Unlocked" if status == "UNLOCKED" else "Locked"
            )
            status_label.setObjectName("CardMeta")
            card_layout.addWidget(status_label)

            open_btn = QPushButton("Open")
            if status == "LOCKED":
                open_btn.setEnabled(False)
                open_btn.setText("Locked")
            else:
                open_btn.clicked.connect(lambda _=False, mid=module_id: self._open_module(mid))
            card_layout.addWidget(open_btn)
            card_layout.addStretch()

            row = index // 2
            col = index % 2
            self._overview_grid.addWidget(card, row, col)

    def _ensure_progress_rows(self) -> None:
        existing = {p.module_id: p for p in self._learning_service.list_progress()}
        for i, module in enumerate(MODULES):
            module_id = module["id"]
            entry = existing.get(module_id)
            if not entry:
                status = "UNLOCKED" if i == 0 else "LOCKED"
                self._learning_service.update_progress(module_id, status, 0)
            else:
                current_status = entry.status.upper()
                if current_status == "COMPLETED":
                    current_status = "COMPLETE"
                # enforce sequential unlocks
                if current_status == "COMPLETE":
                    continue
                if i == 0:
                    if current_status != "UNLOCKED":
                        self._learning_service.update_progress(
                            module_id, "UNLOCKED", entry.progress_percent
                        )
                else:
                    prev = existing.get(MODULES[i - 1]["id"])
                    if prev and prev.status.upper() == "COMPLETE":
                        if current_status == "LOCKED":
                            self._learning_service.update_progress(
                                module_id, "UNLOCKED", entry.progress_percent
                            )
                    else:
                        if current_status != "LOCKED":
                            self._learning_service.update_progress(
                                module_id, "LOCKED", entry.progress_percent
                            )

    def _open_module(self, module_id: str) -> None:
        self._current_module_id = module_id
        self._current_step = 0
        self._build_module_steps(module_id)
        self._load_module_state()
        self._module_stack.setCurrentIndex(1)
        self._update_nav()

    def _return_to_overview(self) -> None:
        self._save_current_step()
        self._module_stack.setCurrentIndex(0)
        self._refresh_overview()

    def _build_module_steps(self, module_id: str) -> None:
        while self._step_stack.count():
            widget = self._step_stack.widget(0)
            self._step_stack.removeWidget(widget)
            widget.deleteLater()
        self._activity_widgets = {}
        self._reflection_widget = None
        self._completion_check = None

        config = MODULE_CONFIGS[module_id]

        # Step 1: Intro
        intro_widget = self._wrap_step(self._text_section("Introduction", config.intro))
        self._step_stack.addWidget(intro_widget)

        # Step 2: Lessons
        lesson_container = QWidget()
        lesson_layout = QVBoxLayout(lesson_container)
        for title, body in config.lessons:
            card = QFrame()
            card.setObjectName("Card")
            layout = QVBoxLayout(card)
            header = QLabel(title)
            header.setObjectName("CardTitle")
            content = QLabel(body)
            content.setWordWrap(True)
            layout.addWidget(header)
            layout.addWidget(content)
            lesson_layout.addWidget(card)
        lesson_layout.addStretch()
        self._step_stack.addWidget(self._wrap_step(lesson_container))

        # Step 3: Activity
        activity_container = QWidget()
        activity_layout = QVBoxLayout(activity_container)
        activity_layout.setSpacing(8)

        self._breathing_widget = None
        if module_id == "module_2":
            breathing = BreathingWidget()
            self._breathing_widget = breathing
            breathing.session_stopped.connect(self._record_breathing_usage)
            breathing.session_completed.connect(self._record_breathing_usage)
            activity_layout.addWidget(breathing)

        for field in config.activity_fields:
            activity_layout.addWidget(QLabel(field.label))
            widget = self._build_field(field)
            activity_layout.addWidget(widget)
            self._activity_widgets[field.key] = widget
        activity_layout.addStretch()
        self._step_stack.addWidget(self._wrap_step(activity_container))

        # Step 4: Reflection
        reflection_container = QWidget()
        reflection_layout = QVBoxLayout(reflection_container)
        reflection_layout.addWidget(QLabel(config.reflection_prompt))
        reflection = QTextEdit()
        reflection.setPlaceholderText("Write a few sentences...")
        reflection_layout.addWidget(reflection)
        self._reflection_widget = reflection
        self._step_stack.addWidget(self._wrap_step(reflection_container))

        # Step 5: Summary
        summary_container = QWidget()
        summary_layout = QVBoxLayout(summary_container)
        for point in config.summary_points:
            label = QLabel(f"• {point}")
            label.setWordWrap(True)
            summary_layout.addWidget(label)
        summary_layout.addStretch()
        self._step_stack.addWidget(self._wrap_step(summary_container))

        # Step 6: Completion
        completion_container = QWidget()
        completion_layout = QVBoxLayout(completion_container)
        completion_label = QLabel(config.completion_text)
        completion_label.setWordWrap(True)
        completion_layout.addWidget(completion_label)
        confirm = QCheckBox("I have completed this module")
        completion_layout.addWidget(confirm)
        self._completion_check = confirm
        completion_layout.addStretch()
        self._step_stack.addWidget(self._wrap_step(completion_container))

    def _wrap_step(self, widget: QWidget) -> QWidget:
        widget.setObjectName("ScrollContent")
        widget.setAutoFillBackground(True)
        widget.setAttribute(Qt.WA_StyledBackground, True)
        scroll = RoundedScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setWidget(widget)
        return scroll

    def _text_section(self, title: str, body: str) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        header = QLabel(title)
        header.setObjectName("CardTitle")
        text = QLabel(body)
        text.setWordWrap(True)
        layout.addWidget(header)
        layout.addWidget(text)
        layout.addStretch()
        return container

    def _build_field(self, field: FieldConfig) -> QWidget:
        if field.kind == "multiline":
            widget = QTextEdit()
            widget.setPlaceholderText("Type here...")
            return widget
        if field.kind == "choice":
            widget = QComboBox()
            widget.addItems(field.options or [])
            return widget
        if field.kind == "checkboxes":
            box = QWidget()
            layout = QVBoxLayout(box)
            for option in field.options or []:
                check = QCheckBox(option)
                layout.addWidget(check)
            return box
        if field.kind == "slider":
            container = QWidget()
            layout = QHBoxLayout(container)
            slider = QSlider(Qt.Horizontal)
            slider.setRange(field.min_val, field.max_val)
            slider.setValue((field.min_val + field.max_val) // 2)
            value_label = QLabel(str(slider.value()))
            slider.valueChanged.connect(lambda v: value_label.setText(str(v)))
            layout.addWidget(slider)
            layout.addWidget(value_label)
            container._slider = slider  # type: ignore[attr-defined]
            return container
        widget = QLineEdit()
        widget.setPlaceholderText("Type here...")
        return widget

    def _load_module_state(self) -> None:
        if not self._current_module_id:
            return
        data = self._module_data_service.get_module_data(self._current_module_id)
        payload = data.data if data else {}
        last_step = int(payload.get("last_step", 0))
        self._current_step = min(max(last_step, 0), 5)
        activity = payload.get("activity", {})
        for key, widget in self._activity_widgets.items():
            if key not in activity:
                continue
            value = activity.get(key)
            if isinstance(widget, QTextEdit):
                widget.setPlainText(value or "")
            elif isinstance(widget, QLineEdit):
                widget.setText(value or "")
            elif isinstance(widget, QComboBox):
                if value in [widget.itemText(i) for i in range(widget.count())]:
                    widget.setCurrentText(value)
            elif hasattr(widget, "_slider"):
                widget._slider.setValue(int(value))  # type: ignore[attr-defined]
            else:
                # checkboxes container
                for i in range(widget.layout().count()):
                    child = widget.layout().itemAt(i).widget()
                    if isinstance(child, QCheckBox):
                        child.setChecked(child.text() in (value or []))
        if self._reflection_widget:
            self._reflection_widget.setPlainText(payload.get("reflection", ""))
        if self._completion_check:
            self._completion_check.setChecked(bool(payload.get("completed", False)))
        self._step_stack.setCurrentIndex(self._current_step)

    def _save_current_step(self) -> None:
        if not self._current_module_id:
            return
        payload: dict[str, Any] = {}
        activity: dict[str, Any] = {}
        for key, widget in self._activity_widgets.items():
            if isinstance(widget, QTextEdit):
                activity[key] = widget.toPlainText().strip()
            elif isinstance(widget, QLineEdit):
                activity[key] = widget.text().strip()
            elif isinstance(widget, QComboBox):
                activity[key] = widget.currentText()
            elif hasattr(widget, "_slider"):
                activity[key] = int(widget._slider.value())  # type: ignore[attr-defined]
            else:
                selections = []
                for i in range(widget.layout().count()):
                    child = widget.layout().itemAt(i).widget()
                    if isinstance(child, QCheckBox) and child.isChecked():
                        selections.append(child.text())
                activity[key] = selections
        payload["activity"] = activity
        payload["reflection"] = self._reflection_widget.toPlainText().strip() if self._reflection_widget else ""
        payload["completed"] = self._completion_check.isChecked() if self._completion_check else False
        payload["last_step"] = self._current_step
        payload["updated_at"] = datetime.now(UTC).isoformat()
        self._module_data_service.update_module_data(self._current_module_id, payload)
        self._update_progress_state()

    def _step_valid(self, step: int) -> bool:
        if step == 2:  # activity
            for key, widget in self._activity_widgets.items():
                if isinstance(widget, QTextEdit) and not widget.toPlainText().strip():
                    return False
                if isinstance(widget, QLineEdit) and not widget.text().strip():
                    return False
                if isinstance(widget, QComboBox) and not widget.currentText().strip():
                    return False
                if hasattr(widget, "_slider"):
                    continue
                if widget.layout() is not None:
                    checks = [
                        widget.layout().itemAt(i).widget()
                        for i in range(widget.layout().count())
                    ]
                    if checks and not any(isinstance(c, QCheckBox) and c.isChecked() for c in checks):
                        return False
        if step == 3 and self._reflection_widget:
            return bool(self._reflection_widget.toPlainText().strip())
        if step == 5 and self._completion_check:
            return self._completion_check.isChecked()
        return True

    def _update_nav(self) -> None:
        self._step_stack.setCurrentIndex(self._current_step)
        self._back_btn.setEnabled(self._current_step > 0)
        if self._current_step == 5:
            self._next_btn.setText("Finish")
        else:
            self._next_btn.setText("Next")
        percent = int(((self._current_step + 1) / 6) * 100)
        self._progress_bar.setValue(percent)
        self._percent_label.setText(f"{percent}%")
        self._step_label.setText(f"Step {self._current_step + 1} of 6")

    def _next_step(self) -> None:
        if not self._step_valid(self._current_step):
            return
        if self._current_step == 2 and self._breathing_widget and self._breathing_widget.is_playing():
            self._breathing_widget.stop_session()
        self._save_current_step()
        if self._current_step == 5:
            self._complete_module()
            return
        self._current_step += 1
        self._update_nav()

    def _prev_step(self) -> None:
        if self._current_step == 2 and self._breathing_widget and self._breathing_widget.is_playing():
            self._breathing_widget.stop_session()
        self._save_current_step()
        if self._current_step > 0:
            self._current_step -= 1
            self._update_nav()

    def _complete_module(self) -> None:
        if not self._current_module_id:
            return
        self._learning_service.update_progress(
            self._current_module_id, "COMPLETE", 100, completed_at=datetime.now(UTC)
        )
        # unlock next module
        ids = [m["id"] for m in MODULES]
        if self._current_module_id in ids:
            idx = ids.index(self._current_module_id)
            if idx + 1 < len(ids):
                next_id = ids[idx + 1]
                progress = self._learning_service.get_progress(next_id)
                if not progress or progress.status != "COMPLETE":
                    self._learning_service.update_progress(next_id, "UNLOCKED", 0)
        self.module_completed.emit(self._current_module_id)
        self._return_to_overview()

    def _record_breathing_usage(self, duration_seconds: int) -> None:
        if duration_seconds <= 0:
            return
        metadata = {"duration_seconds": duration_seconds, "source": "module_2"}
        self._tool_usage_service.record_usage("breathcheck_tool", metadata)

    def _update_progress_state(self) -> None:
        if not self._current_module_id:
            return
        progress = self._learning_service.get_progress(self._current_module_id)
        if progress and progress.status.upper() in {"COMPLETE", "COMPLETED"}:
            return
        percent = int(((self._current_step + 1) / 6) * 100)
        self._learning_service.update_progress(self._current_module_id, "UNLOCKED", percent)

    def _build_reminder_text(self, _progress_map: dict[str, Any]) -> str:
        settings = self._user_settings_service.get_settings()
        if settings.reminder_time.lower() == "off":
            return ""
        reminder_time = settings.reminder_time
        return f"Daily check-in suggestion: take a short check-in {reminder_time.lower()}."

    def _build_continue_text(self, progress_map: dict[str, Any]) -> str:
        for module in MODULES:
            progress = progress_map.get(module["id"])
            if progress and progress.status.upper() == "UNLOCKED" and progress.progress_percent < 100:
                return f"Continue: {module['title']}"
        return ""

    def show_overview(self) -> None:
        self._module_stack.setCurrentIndex(0)
        self._refresh_overview()

    def on_leave(self) -> None:
        if self._breathing_widget and self._breathing_widget.is_playing():
            self._breathing_widget.stop_session()
        self._save_current_step()
        self._module_stack.setCurrentIndex(0)
        self._refresh_overview()

    def reset_view(self) -> None:
        self._module_stack.setCurrentIndex(0)
        self._current_module_id = None
        self._current_step = 0
        self._refresh_overview()
