"""Object hierarchy panel: tree/list with visibility, selection, lock + operations."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QMenu, QInputDialog, QMessageBox, QLabel,
)

from core.scene import Scene


def QColorIcon(hex_color: str) -> QIcon:
    """Small solid-color square icon used as the object color swatch."""
    pix = QPixmap(12, 12)
    pix.fill(QColor(hex_color))
    return QIcon(pix)


class ObjectPanel(QWidget):
    selectionChanged = Signal(object)
    visibilityToggled = Signal(str, bool)
    deleteRequested = Signal(str)
    duplicateRequested = Signal(str)
    renameRequested = Signal(str, str)
    focusRequested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Type", "Verts"])
        self.tree.setColumnWidth(0, 110)
        self.tree.setColumnWidth(1, 62)
        self.tree.setColumnWidth(2, 44)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tree.setTextElideMode(Qt.ElideRight)
        self.tree.setIconSize(self.tree.iconSize() * 0.9)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.itemChanged.connect(self._on_item_changed)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self.tree, 1)
        btn_row = QHBoxLayout()
        for label, slot in (("Focus", self._focus_sel), ("Dupl.", self._dup_sel), ("Del", self._del_sel)):
            b = QPushButton(label)
            b.clicked.connect(slot)
            btn_row.addWidget(b)
        layout.addLayout(btn_row)
        self._scene: Scene | None = None
        self._loading = False

    def set_scene(self, scene: Scene, selected: str | None = None) -> None:
        self._loading = True
        try:
            self._scene = scene
            self.tree.clear()
            for o in scene.objects:
                item = QTreeWidgetItem([o.name, o.geom_type, str(o.stats().get("vertices", 0))])
                item.setData(0, Qt.UserRole, o.name)
                item.setCheckState(0, Qt.Checked if o.visible else Qt.Unchecked)
                # color swatch like the reference UI
                from core.materials import rgba_to_hex
                item.setIcon(0, QColorIcon(rgba_to_hex(o.color)))
                if o.locked:
                    item.setForeground(0, Qt.gray)
                if o.name == selected:
                    item.setSelected(True)
                self.tree.addTopLevelItem(item)
        finally:
            self._loading = False

    def selected_name(self) -> str | None:
        items = self.tree.selectedItems()
        if items:
            return items[0].data(0, Qt.UserRole)
        return None

    def _on_item_clicked(self, item, col):
        name = item.data(0, Qt.UserRole)
        if col == 0 and item.checkState(0) is not None:
            pass
        self.selectionChanged.emit(name)

    def on_item_changed_checkbox(self, item, col):
        pass

    def _on_item_changed(self, item, col):
        if self._loading or col != 0:
            return
        name = item.data(0, Qt.UserRole)
        if self._scene is None:
            return
        obj = self._scene.get(name)
        if obj is None:
            return
        visible = item.checkState(0) == Qt.Checked
        if visible != obj.visible:
            self.visibilityToggled.emit(name, visible)

    def _on_item_double_clicked(self, item, col):
        if col == 0:
            self._rename(item.data(0, Qt.UserRole))

    def _on_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if item is None:
            return
        name = item.data(0, Qt.UserRole)
        menu = QMenu(self)
        for label, fn in (("Focus camera (F)", lambda: self.focusRequested.emit(name)),
                          ("Rename", lambda: self._rename(name)),
                          ("Duplicate", lambda: self.duplicateRequested.emit(name)),
                          ("Delete (Del)", lambda: self.deleteRequested.emit(name)),
                          ("Toggle visibility", lambda: self.visibilityToggled.emit(
                              name, item.checkState(0) != Qt.Checked))):
            menu.addAction(label, fn)
        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _rename(self, old: str):
        text, ok = QInputDialog.getText(self, "Rename object", "New name:", text=old)
        if ok and text.strip() and text.strip() != old:
            self.renameRequested.emit(old, text.strip())

    def _focus_sel(self):
        n = self.selected_name()
        if n:
            self.focusRequested.emit(n)

    def _dup_sel(self):
        n = self.selected_name()
        if n:
            self.duplicateRequested.emit(n)

    def _del_sel(self):
        n = self.selected_name()
        if n:
            self.deleteRequested.emit(n)
