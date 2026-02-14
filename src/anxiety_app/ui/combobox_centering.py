from __future__ import annotations

from PyQt5.QtCore import QEvent, QObject, Qt
from PyQt5.QtWidgets import QApplication, QComboBox


class ComboBoxCenteringFilter(QObject):
    """Globally center QComboBox text (selected value + popup items)."""

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if isinstance(obj, QComboBox) and event.type() in {
            QEvent.Polish,
            QEvent.Show,
        }:
            self._apply_to_combo(obj)
        return super().eventFilter(obj, event)

    def _apply_to_combo(self, combo: QComboBox) -> None:
        if not combo.property("_centered_text_ready"):
            combo.setProperty("_centered_text_ready", True)
            model = combo.model()
            if model is not None:
                model.rowsInserted.connect(
                    lambda _parent, first, last, c=combo: self._align_item_range(c, first, last)
                )

        if not combo.isEditable():
            combo.setEditable(True)

        line_edit = combo.lineEdit()
        if line_edit is not None:
            line_edit.setReadOnly(True)
            line_edit.setAlignment(Qt.AlignCenter)

        self._align_all_items(combo)

    @staticmethod
    def _align_item_range(combo: QComboBox, first: int, last: int) -> None:
        for i in range(first, last + 1):
            combo.setItemData(i, Qt.AlignCenter, Qt.TextAlignmentRole)

    @staticmethod
    def _align_all_items(combo: QComboBox) -> None:
        for i in range(combo.count()):
            combo.setItemData(i, Qt.AlignCenter, Qt.TextAlignmentRole)


def install_combobox_centering(app: QApplication) -> ComboBoxCenteringFilter:
    filter_obj = ComboBoxCenteringFilter(app)
    app.installEventFilter(filter_obj)
    for combo in app.findChildren(QComboBox):
        filter_obj._apply_to_combo(combo)
    return filter_obj
