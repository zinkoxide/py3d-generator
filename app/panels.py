"""Titled card container used across the redesigned shell."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton


class Card(QFrame):
    """Panel with a bold title header, optional close button and collapsible body.

    Matches the reference UI: rounded card, title row, scrollable body.
    """

    closed = Signal()

    def __init__(self, title: str, parent=None, collapsible: bool = False,
                 show_close: bool = False):
        super().__init__(parent)
        self.setObjectName("Card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 8, 10, 10)
        outer.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(4)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("CardTitle")
        header.addWidget(self.title_label)
        header.addStretch(1)
        self.chevron = None
        if collapsible:
            self.chevron = QPushButton("⌄")
            self.chevron.setObjectName("CollapseButton")
            self.chevron.setFixedWidth(22)
            self.chevron.clicked.connect(self.toggle_collapsed)
            header.addWidget(self.chevron)
        self.close_btn = None
        if show_close:
            self.close_btn = QPushButton("✕")
            self.close_btn.setObjectName("CollapseButton")
            self.close_btn.setFixedWidth(22)
            self.close_btn.clicked.connect(self.closed.emit)
            header.addWidget(self.close_btn)
        outer.addLayout(header)

        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(6)
        outer.addLayout(self.body, 1)
        self._collapsed = False

    def set_title(self, text: str) -> None:
        self.title_label.setText(text)

    def add_widget(self, w) -> None:
        self.body.addWidget(w)

    def toggle_collapsed(self) -> None:
        self.set_collapsed(not self._collapsed)

    def set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = collapsed
        # Hide every widget in the body layout except the header.
        for i in range(self.body.count()):
            item = self.body.itemAt(i)
            w = item.widget()
            if w is not None:
                w.setVisible(not collapsed)
        if self.chevron is not None:
            self.chevron.setText("⌃" if collapsed else "⌄")