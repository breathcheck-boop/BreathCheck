from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QScrollArea


class RoundedScrollArea(QScrollArea):
    def __init__(self, radius: int = 12) -> None:
        super().__init__()
        _ = radius
        self.setFrameShape(QFrame.NoFrame)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        viewport = self.viewport()
        if viewport is not None:
            viewport.setAttribute(Qt.WA_StyledBackground, True)
            viewport.setAutoFillBackground(True)
