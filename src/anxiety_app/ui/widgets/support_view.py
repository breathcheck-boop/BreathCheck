from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from anxiety_app.domain.services import SupportService
from anxiety_app.ui.widgets.card_widgets import CardFrame, CompactCard, clear_layout
from anxiety_app.ui.widgets.rounded_scroll_area import RoundedScrollArea


class _ContactDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Contact")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name = QLineEdit()
        self.phone = QLineEdit()
        self.note = QLineEdit()
        form.addRow("Name", self.name)
        form.addRow("Phone", self.phone)
        form.addRow("Note", self.note)
        layout.addLayout(form)
        row = QHBoxLayout()
        cancel = QPushButton("Cancel")
        save = QPushButton("Save")
        save.setObjectName("AccentButton")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.accept)
        row.addStretch()
        row.addWidget(cancel)
        row.addWidget(save)
        layout.addLayout(row)


class _ResourceDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Resource")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.title_input = QLineEdit()
        self.contact_input = QLineEdit()
        self.note_input = QLineEdit()
        form.addRow("Title", self.title_input)
        form.addRow("Contact", self.contact_input)
        form.addRow("Note", self.note_input)
        layout.addLayout(form)
        row = QHBoxLayout()
        cancel = QPushButton("Cancel")
        save = QPushButton("Save")
        save.setObjectName("AccentButton")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.accept)
        row.addStretch()
        row.addWidget(cancel)
        row.addWidget(save)
        layout.addLayout(row)


class SupportView(QWidget):
    def __init__(self, support_service: SupportService) -> None:
        super().__init__()
        self.setObjectName("ViewRoot")
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._support_service = support_service

        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = RoundedScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content.setObjectName("ScrollContent")
        content.setAutoFillBackground(True)
        content.setAttribute(Qt.WA_StyledBackground, True)
        content_layout = QVBoxLayout(content)
        content_layout.setAlignment(Qt.AlignTop)
        content_layout.setSpacing(12)

        grid = QGridLayout()
        grid.setSpacing(12)
        grid.addWidget(
            self._build_support_card(
                "Emergency Support",
                "If you feel unsafe, contact local emergency services or a trusted person.",
                "Show Steps",
                self._show_emergency_steps,
            ),
            0,
            0,
        )
        grid.addWidget(
            self._build_support_card(
                "Crisis Hotline",
                "Store your personal crisis contacts for quick reference.",
                "Add Contacts",
                self._add_contact,
            ),
            0,
            1,
        )
        grid.addWidget(
            self._build_support_card(
                "Counseling Services",
                "Save counseling resources you can reach out to.",
                "Add Resource",
                self._add_resource,
            ),
            1,
            0,
        )
        grid.addWidget(
            self._build_support_card(
                "University Mental Health",
                "Store campus support information and contacts.",
                "Add Resource",
                self._add_resource,
            ),
            1,
            1,
        )
        content_layout.addLayout(grid)

        self._contacts_host = QVBoxLayout()
        self._resources_host = QVBoxLayout()

        contacts_card = CardFrame()
        contacts_layout = contacts_card.content_layout
        contacts_title = QLabel("Saved Contacts")
        contacts_title.setObjectName("CardTitle")
        contacts_layout.addWidget(contacts_title)
        contacts_layout.addLayout(self._contacts_host)
        content_layout.addWidget(contacts_card)

        resources_card = CardFrame()
        resources_layout = resources_card.content_layout
        resources_title = QLabel("Saved Resources")
        resources_title.setObjectName("CardTitle")
        resources_layout.addWidget(resources_title)
        resources_layout.addLayout(self._resources_host)
        content_layout.addWidget(resources_card)

        content_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

        self._refresh_lists()

    def _build_support_card(
        self,
        title: str,
        description: str,
        button_text: str,
        callback,
    ) -> QFrame:
        card = CompactCard(title=title, description=description, icon_text="■")
        button = card.add_button(button_text, callback, object_name="AccentButton")
        button.setMinimumHeight(34)
        return card

    def _show_emergency_steps(self) -> None:
        QMessageBox.information(
            self,
            "Emergency Support Steps",
            "1. Move to a safer place if possible.\n"
            "2. Contact local emergency services.\n"
            "3. Reach out to a trusted person immediately.\n"
            "4. Stay with someone until support arrives.",
        )

    def _add_contact(self) -> None:
        dialog = _ContactDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return
        name = dialog.name.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing name", "Please enter a contact name.")
            return
        self._support_service.add_contact(
            name=name,
            phone=dialog.phone.text().strip(),
            note=dialog.note.text().strip(),
        )
        self._refresh_lists()

    def _add_resource(self) -> None:
        dialog = _ResourceDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return
        title = dialog.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Missing title", "Please enter a resource title.")
            return
        self._support_service.add_resource(
            title=title,
            contact=dialog.contact_input.text().strip(),
            note=dialog.note_input.text().strip(),
        )
        self._refresh_lists()

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        clear_layout(layout)

    def _refresh_lists(self) -> None:
        self._clear_layout(self._contacts_host)
        self._clear_layout(self._resources_host)

        contacts = self._support_service.list_contacts()
        if not contacts:
            empty = QLabel("No contacts yet.")
            empty.setObjectName("CardMeta")
            self._contacts_host.addWidget(empty)
        else:
            for entry in contacts:
                row = CardFrame(margins=(10, 8, 10, 8))
                layout = QHBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(8)
                row.content_layout.addLayout(layout)
                label = QLabel(
                    f"{entry.name} | {entry.phone or '-'} | {entry.note or '-'}"
                )
                label.setWordWrap(True)
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(
                    lambda _=False, entry_id=entry.id: self._delete_contact(entry_id)
                )
                layout.addWidget(label)
                layout.addStretch()
                layout.addWidget(delete_btn)
                self._contacts_host.addWidget(row)

        resources = self._support_service.list_resources()
        if not resources:
            empty = QLabel("No resources yet.")
            empty.setObjectName("CardMeta")
            self._resources_host.addWidget(empty)
        else:
            for entry in resources:
                row = CardFrame(margins=(10, 8, 10, 8))
                layout = QHBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(8)
                row.content_layout.addLayout(layout)
                label = QLabel(
                    f"{entry.title} | {entry.contact or '-'} | {entry.note or '-'}"
                )
                label.setWordWrap(True)
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(
                    lambda _=False, entry_id=entry.id: self._delete_resource(entry_id)
                )
                layout.addWidget(label)
                layout.addStretch()
                layout.addWidget(delete_btn)
                self._resources_host.addWidget(row)

    def _delete_contact(self, entry_id: int) -> None:
        self._support_service.delete_contact(entry_id)
        self._refresh_lists()

    def _delete_resource(self, entry_id: int) -> None:
        self._support_service.delete_resource(entry_id)
        self._refresh_lists()
