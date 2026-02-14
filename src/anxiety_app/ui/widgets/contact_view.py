from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGridLayout,
    QLabel,
    QMessageBox,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from anxiety_app.ui.widgets.card_widgets import CompactCard
from anxiety_app.ui.widgets.rounded_scroll_area import RoundedScrollArea

CONTACTS = [
    ("National Center for Mental Health (NCMH)", "Government mental health facility and services."),
    ("Department of Health – Mental Health Program", "National mental health initiatives and resources."),
    ("Philippine Mental Health Association (PMHA)", "Community-based mental health support."),
    ("Hopeline PH", "Crisis support and referrals."),
    ("Psychological Association of the Philippines (PAP)", "Professional association and referrals."),
    ("MindNation", "Workplace and community mental health support."),
    ("Silakbo", "Peer support and community group."),
    ("In Touch Community Services", "Counseling and support services."),
]


class ContactView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("ViewRoot")
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        note = QLabel(
            "Contact details change over time. Please verify through official websites or channels."
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        scroll = RoundedScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content = QWidget()
        content.setObjectName("ScrollContent")
        content.setAutoFillBackground(True)
        content.setAttribute(Qt.WA_StyledBackground, True)
        content.setMinimumWidth(0)
        content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        content_layout = QGridLayout(content)
        content_layout.setHorizontalSpacing(12)
        content_layout.setVerticalSpacing(12)
        content_layout.setColumnStretch(0, 1)
        content_layout.setColumnStretch(1, 1)
        content_layout.setContentsMargins(12, 12, 12, 12)

        for index, (name, description) in enumerate(CONTACTS):
            card = CompactCard(
                title=name,
                description=description,
                icon_text="Image placeholder",
                minimum_height=320,
                icon_min_height=140,
            )
            card.setMinimumWidth(0)
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            card.title_label.setAlignment(Qt.AlignCenter)
            card.description_label.setAlignment(Qt.AlignCenter)
            button = card.add_button("Contact", lambda _checked=False, org=name: self._open_contact(org))
            button.setObjectName("AccentButton")
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            row = index // 2
            col = index % 2
            content_layout.addWidget(card, row, col)

        content_layout.setRowStretch((len(CONTACTS) + 1) // 2, 1)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

    def _open_contact(self, org: str) -> None:
        QMessageBox.information(
            self,
            "Contact info",
            f"Please search for official contact details for:\n{org}",
        )
