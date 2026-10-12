"""Console panel with two tabs: Output (info/warn/stdout) and Errors (error)."""

from __future__ import annotations

from PySide6.QtGui import QColor, QTextCursor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QApplication,
    QTabWidget,
)

from app.i18n import tr


class _LogView(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        f = QFont("JetBrains Mono")
        f.setStyleHint(QFont.Monospace)
        f.setFixedPitch(True)
        self.setFont(f)

    def append_colored(self, msg: str, color: str):
        self.moveCursor(QTextCursor.End)
        self.setTextColor(QColor(color))
        self.insertPlainText(msg.rstrip("\n") + "\n")
        self.moveCursor(QTextCursor.End)


class ConsolePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.out_view = _LogView()
        self.err_view = _LogView()
        self.tabs.addTab(self.out_view, tr("console_out"))
        self.tabs.addTab(self.err_view, tr("console_err"))
        layout.addWidget(self.tabs, 1)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(4, 4, 4, 4)
        self.clear_btn = QPushButton(tr("tools_clear"))
        self.clear_btn.clicked.connect(self.clear)
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.clicked.connect(self.copy)
        btn_row.addWidget(self.clear_btn)
        btn_row.addWidget(self.copy_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

    def retranslate(self):
        self.tabs.setTabText(0, tr("console_out"))
        self.tabs.setTabText(1, tr("console_err"))
        self.clear_btn.setText(tr("tools_clear"))

    def clear(self):
        self.out_view.clear()
        self.err_view.clear()

    def copy(self):
        QApplication.clipboard().setText(self.out_view.toPlainText() + self.err_view.toPlainText())

    def toPlainText(self) -> str:
        return self.out_view.toPlainText() + self.err_view.toPlainText()

    def error_count(self) -> int:
        return len([l for l in self.err_view.toPlainText().splitlines() if l.strip()])

    def info(self, msg: str):
        self.out_view.append_colored(msg, "#7ee787")

    def warn(self, msg: str):
        self.out_view.append_colored(msg, "#ffcb6b")

    def stdout(self, msg: str):
        if msg.strip():
            self.out_view.append_colored(msg, "#9fb0c9")

    def error(self, msg: str):
        self.err_view.append_colored(msg, "#ff7b72")
        self.tabs.setCurrentWidget(self.err_view)