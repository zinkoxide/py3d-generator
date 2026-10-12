"""Properties panel: editable transforms/materials with immediate viewport update."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QDoubleSpinBox, QLineEdit, QPushButton,
    QCheckBox, QSlider, QLabel, QVBoxLayout, QColorDialog,
)

from core.materials import rgba_to_hex


class PropertiesPanel(QWidget):
    transformChanged = Signal(str, dict)   # name, {location, rotation, scale}
    materialChanged = Signal(str, dict)    # name, {color, roughness, metallic}
    visibilityChanged = Signal(str, bool)
    renameRequested = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._name: str | None = None
        self._updating = False
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        self.info = QLabel("No selection")
        self.info.setObjectName("DimLabel")
        root.addWidget(self.info)
        self.warn = QLabel("Manual edit — rerunning the script will discard it.")
        self.warn.setObjectName("DimLabel")
        self.warn.setStyleSheet("color: #ffcb6b;")
        self.warn.setVisible(False)
        self.warn.setWordWrap(True)
        root.addWidget(self.warn)

        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.editingFinished.connect(self._on_rename)
        form.addRow("Name", self.name_edit)
        self.pos = self._vec_row(form, "Position", -1000, 1000)
        self.rot = self._vec_row(form, "Rotation°", -3600, 3600)
        self.scl = self._vec_row(form, "Scale", 0.001, 1000)
        root.addLayout(form)

        self.color_btn = QPushButton("Color")
        self.color_btn.clicked.connect(self._pick_color)
        root.addWidget(self.color_btn)
        self._color = (0.3, 0.6, 1.0, 1.0)

        self.rough = QSlider(Qt.Horizontal)
        self.rough.setRange(0, 100)
        self.rough.valueChanged.connect(self._on_material)
        root.addWidget(QLabel("Roughness"))
        root.addWidget(self.rough)
        self.metal = QSlider(Qt.Horizontal)
        self.metal.setRange(0, 100)
        self.metal.valueChanged.connect(self._on_material)
        root.addWidget(QLabel("Metallic"))
        root.addWidget(self.metal)

        self.visible_cb = QCheckBox("Visible")
        self.visible_cb.toggled.connect(self._on_visible)
        root.addWidget(self.visible_cb)
        self.stats = QLabel("")
        self.stats.setObjectName("DimLabel")
        self.stats.setWordWrap(True)
        root.addWidget(self.stats)
        root.addStretch(1)

    def _vec_row(self, form, label, lo, hi):
        from PySide6.QtWidgets import QHBoxLayout
        boxes = []
        row = QHBoxLayout()
        for _ in range(3):
            sb = QDoubleSpinBox()
            sb.setRange(lo, hi)
            sb.setDecimals(3)
            sb.setSingleStep(0.1)
            sb.valueChanged.connect(self._on_transform)
            row.addWidget(sb)
            boxes.append(sb)
        form.addRow(label, row)
        return boxes

    def set_object(self, obj, manual_edits: bool = False) -> None:
        self._updating = True
        try:
            if obj is None:
                self._name = None
                self.info.setText("No selection")
                self.stats.setText("")
                self.warn.setVisible(False)
                return
            self._name = obj.name
            self.info.setText(f"{obj.geom_type} object")
            self.name_edit.setText(obj.name)
            for box, v in zip(self.pos, obj.location):
                box.setValue(float(v))
            for box, v in zip(self.rot, obj.rotation):
                box.setValue(float(v))
            for box, v in zip(self.scl, obj.scale):
                box.setValue(float(v))
            self._color = tuple(obj.color)
            self.color_btn.setStyleSheet(f"background-color: {rgba_to_hex(obj.color)};")
            self.rough.setValue(int(round(obj.roughness * 100)))
            self.metal.setValue(int(round(obj.metallic * 100)))
            self.visible_cb.setChecked(bool(obj.visible))
            st = obj.stats()
            self.stats.setText(
                f"Type: {obj.geom_type}\nVertices: {st.get('vertices', 0)}  "
                f"Faces: {st.get('faces', 0)}\nSize: {tuple(round(x, 3) for x in st.get('size', (0,0,0)))}")
            self.warn.setVisible(bool(manual_edits))
        finally:
            self._updating = False

    def _on_transform(self):
        if self._updating or not self._name:
            return
        self.transformChanged.emit(self._name, {
            "location": tuple(b.value() for b in self.pos),
            "rotation": tuple(b.value() for b in self.rot),
            "scale": tuple(b.value() for b in self.scl),
        })

    def _on_material(self):
        if self._updating or not self._name:
            return
        self.materialChanged.emit(self._name, {
            "color": self._color,
            "roughness": self.rough.value() / 100.0,
            "metallic": self.metal.value() / 100.0,
        })

    def _on_visible(self, on: bool):
        if self._updating or not self._name:
            return
        self.visibilityChanged.emit(self._name, bool(on))

    def _pick_color(self):
        if not self._name:
            return
        c = QColorDialog.getColor(QColor(*[int(x * 255) for x in self._color[:3]]), self)
        if c.isValid():
            self._color = (c.red() / 255.0, c.green() / 255.0, c.blue() / 255.0, 1.0)
            self.color_btn.setStyleSheet(f"background-color: {c.name()};")
            self._on_material()

    def _on_rename(self):
        if self._updating or not self._name:
            return
        new = self.name_edit.text().strip()
        if new and new != self._name:
            self.renameRequested.emit(self._name, new)
