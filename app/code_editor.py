"""Real Python code editor: highlighting, line numbers, completion, search/replace."""

from __future__ import annotations

import keyword
import re

from PySide6.QtCore import Qt, QRect, Signal, QStringListModel
from PySide6.QtGui import (
    QColor, QFont, QPainter, QSyntaxHighlighter, QTextCharFormat,
    QTextCursor, QKeySequence,
)
from PySide6.QtWidgets import QCompleter, QPlainTextEdit, QWidget

API_WORDS = [
    "cube(", "box(", "sphere(", "icosphere(", "cylinder(", "cone(", "plane(",
    "torus(", "capsule(", "ring(", "wedge(", "pyramid(",
    "custom_mesh(",    "clear_scene()", "set_background(", "set_scene_name(", "get_objects()",
    "remove_object(", "duplicate_object(", "set_transform(", "set_material(",
    "grid_repeat(", "random_scatter(",
    "name=", "size=", "radius=", "height=", "location=", "position=",
    "rotation=", "scale=", "color=", "roughness=", "metallic=",
    "sections=", "subdivisions=", "major_radius=", "minor_radius=",
    "inner_radius=", "outer_radius=",
]


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, doc):
        super().__init__(doc)
        self.rules: list[tuple[re.Pattern, QTextCharFormat]] = []

        def fmt(color, bold=False, italic=False):
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(QFont.Bold)
            if italic:
                f.setFontItalic(True)
            return f

        self.fmt_keyword = fmt("#c792ea", True)
        self.fmt_builtin = fmt("#82aaff")
        self.fmt_string = fmt("#c3e88d")
        self.fmt_number = fmt("#f78c6c")
        self.fmt_comment = fmt("#546e7a", italic=True)
        self.fmt_func = fmt("#ffcb6b")
        self.fmt_error = QTextCharFormat()
        self.fmt_error.setUnderlineColor(QColor("#ff5370"))
        self.fmt_error.setUnderlineStyle(QTextCharFormat.WaveUnderline)

        kw_pat = re.compile(r"\b(" + "|".join(keyword.kwlist) + r")\b")
        self.rules.append((kw_pat, self.fmt_keyword))
        self.rules.append((re.compile(r"\b(print|range|len|for|in|import|from|as)\b"), self.fmt_builtin))
        self.rules.append((re.compile(r'"[^"\n]*"|\'[^\'\n]*\''), self.fmt_string))
        self.rules.append((re.compile(r"\b\d+(\.\d+)?\b"), self.fmt_number))
        self.rules.append((re.compile(r"#[^\n]*"), self.fmt_comment))
        self.rules.append((re.compile(r"\b(cube|box|sphere|icosphere|cylinder|cone|plane|torus|capsule|ring|wedge|pyramid|custom_mesh|clear_scene|set_background|set_scene_name|get_objects|remove_object|duplicate_object|set_transform|set_material|grid_repeat|random_scatter)\b"), self.fmt_func))
        self.error_lines: set[int] = set()

    def set_error_lines(self, lines: set[int]):
        self.error_lines = set(lines)
        self.rehighlight()

    def highlightBlock(self, text: str):
        for pat, fmt in self.rules:
            for m in pat.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)
        if self.currentBlock().blockNumber() + 1 in self.error_lines:
            f = QTextCharFormat()
            f.setBackground(QColor("#4a1f28"))
            self.setFormat(0, len(text), f)


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(self.editor.line_number_width(), 0)

    def paintEvent(self, event):
        self.editor.paint_line_numbers(event)


class CodeEditor(QPlainTextEdit):
    cursorChanged = Signal(int, int)  # line, col
    modifiedChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Python code is always left-to-right, even in an RTL UI
        self.setLayoutDirection(Qt.LeftToRight)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        font = QFont("JetBrains Mono", 11)
        font.setStyleHint(QFont.Monospace)
        font.setFixedPitch(True)
        self.setFont(font)
        self.tab_size = 4
        self.highlighter = PythonHighlighter(self.document())
        self.line_area = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_area_width)
        self.updateRequest.connect(self._update_line_area)
        self.cursorPositionChanged.connect(self._emit_cursor)
        self.textChanged.connect(lambda: self.modifiedChanged.emit(True))
        self._update_line_area_width(0)
        # completion
        self.completer = QCompleter(API_WORDS)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.activated.connect(self._insert_completion)
        self._dirty = False

    # --- line numbers ---
    def line_number_width(self) -> int:
        digits = max(1, len(str(max(1, self.blockCount()))))
        return 8 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_line_area_width(self, _):
        self.setViewportMargins(self.line_number_width(), 0, 0, 0)

    def _update_line_area(self, rect, dy):
        if dy:
            self.line_area.scroll(0, dy)
        else:
            self.line_area.update(0, rect.y(), self.line_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_width(), cr.height()))

    def paint_line_numbers(self, event):
        p = QPainter(self.line_area)
        p.fillRect(event.rect(), QColor("#141b28"))
        block = self.firstVisibleBlock()
        num = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                p.setPen(QColor("#5b6b85") if num != self.textCursor().blockNumber() else QColor("#dbe2ee"))
                p.drawText(0, top, self.line_area.width() - 4, self.fontMetrics().height(),
                           Qt.AlignRight, str(num + 1))
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            num += 1

    def _emit_cursor(self):
        c = self.textCursor()
        self.cursorChanged.emit(c.blockNumber() + 1, c.columnNumber() + 1)

    # --- editing behavior ---
    def keyPressEvent(self, event):
        # completion popup handling
        if self.completer.popup().isVisible() and event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Tab):
            event.ignore()
            return
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self._handle_return()
            return
        if event.key() == Qt.Key_Tab and not (event.modifiers() & Qt.ShiftModifier):
            self.textCursor().insertText(" " * self.tab_size)
            return
        super().keyPressEvent(event)
        # trigger completion after typing 2+ chars of a word
        if event.text().isalnum() or event.text() == "_":
            tc = self.textCursor()
            tc.select(QTextCursor.WordUnderCursor)
            prefix = tc.selectedText()
            if len(prefix) >= 2:
                self.completer.setCompletionPrefix(prefix)
                cr = self.cursorRect()
                cr.setWidth(250)
                self.completer.complete(cr)

    def _handle_return(self):
        cursor = self.textCursor()
        block_text = cursor.block().text()
        indent = re.match(r"[ \t]*", block_text).group(0).replace("\t", " " * self.tab_size)
        extra = " " * self.tab_size if block_text.rstrip().endswith(":") else ""
        cursor.insertText("\n" + indent + extra)

    def _insert_completion(self, text: str):
        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)
        # API words include '(' — insert remainder smartly
        tc.removeSelectedText()
        tc.insertText(text)

    # --- helpers ---
    def set_error_lines(self, lines: set[int]):
        self.highlighter.set_error_lines(lines)

    def clear_errors(self):
        self.highlighter.set_error_lines(set())

    def find_text(self, pattern: str, case_sensitive=False) -> bool:
        from PySide6.QtGui import QTextDocument
        f = QTextDocument.FindFlag(0)
        if case_sensitive:
            f = QTextDocument.FindCaseSensitively
        found = self.find(pattern, f) if pattern else False
        return bool(found)

    def replace_current(self, replacement: str):
        c = self.textCursor()
        if c.hasSelection():
            c.insertText(replacement)

    def set_tab_size(self, n: int):
        self.tab_size = max(2, min(8, int(n)))
