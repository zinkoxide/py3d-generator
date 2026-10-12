"""Display settings card: color mode, lighting, grid/axes/smooth toggles."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QCheckBox, QHBoxLayout,
)

from app.i18n import tr

COLOR_MODES = ["multi", "uniform", "material"]
LIGHT_MODES = ["basic", "soft", "dramatic"]


class DisplayPanel(QWidget):
    colorModeChanged = Signal(str)
    uniformColorChanged = Signal(object)   # (r,g,b,a)
    lightingChanged = Signal(str)
    gridToggled = Signal(bool)
    axesToggled = Signal(bool)
    smoothToggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(8)

        # --- color mode ---
        self.lbl_color = QLabel(tr("lbl_color"))
        layout.addWidget(self.lbl_color)
        self.color_mode = QComboBox()
        self.color_mode.addItem(tr("color_multi"), "multi")
        self.color_mode.addItem(tr("color_uniform"), "uniform")
        self.color_mode.addItem(tr("color_material"), "material")
        self.color_mode.currentIndexChanged.connect(
            lambda: self.colorModeChanged.emit(self.color_mode.currentData()))
        layout.addWidget(self.color_mode)

        self.uniform_row = QWidget()
        ur = QHBoxLayout(self.uniform_row)
        ur.setContentsMargins(0, 0, 0, 0)
        from PySide6.QtWidgets import QPushButton
        self.uniform_btn = QPushButton(tr("color_uniform"))
        self.uniform_btn.setStyleSheet("background-color: #4C9AFF;")
        self.uniform_btn.clicked.connect(self._pick_uniform)
        ur.addWidget(self.uniform_btn)
        layout.addWidget(self.uniform_row)
        self.uniform_row.setVisible(False)
        self._uniform = (0.30, 0.60, 1.0, 1.0)

        # --- lighting ---
        self.lbl_light = QLabel(tr("lbl_light"))
        layout.addWidget(self.lbl_light)
        self.lighting = QComboBox()
        self.lighting.addItem(tr("light_basic"), "basic")
        self.lighting.addItem(tr("light_soft"), "soft")
        self.lighting.addItem(tr("light_dramatic"), "dramatic")
        self.lighting.currentIndexChanged.connect(
            lambda: self.lightingChanged.emit(self.lighting.currentData()))
        layout.addWidget(self.lighting)

        # --- toggles ---
        self.chk_grid = QCheckBox(tr("chk_grid"))
        self.chk_grid.setChecked(True)
        self.chk_grid.toggled.connect(self.gridToggled.emit)
        layout.addWidget(self.chk_grid)

        self.chk_axes = QCheckBox(tr("chk_axes"))
        self.chk_axes.setChecked(True)
        self.chk_axes.toggled.connect(self.axesToggled.emit)
        layout.addWidget(self.chk_axes)

        self.chk_smooth = QCheckBox(tr("chk_smooth"))
        self.chk_smooth.setChecked(True)
        self.chk_smooth.toggled.connect(self.smoothToggled.emit)
        layout.addWidget(self.chk_smooth)
        layout.addStretch(1)

    def _pick_uniform(self):
        from PySide6.QtGui import QColor
        from PySide6.QtWidgets import QColorDialog
        c = QColorDialog.getColor(QColor(*[int(x * 255) for x in self._uniform[:3]]), self)
        if c.isValid():
            self._uniform = (c.red() / 255.0, c.green() / 255.0, c.blue() / 255.0, 1.0)
            self.uniform_btn.setStyleSheet(f"background-color: {c.name()}; color: #000;")
            self.uniformColorChanged.emit(self._uniform)

    def retranslate(self):
        self.lbl_color.setText(tr("lbl_color"))
        self.lbl_light.setText(tr("lbl_light"))
        self.uniform_btn.setText(tr("color_uniform"))
        for combo, keys in ((self.color_mode, ("color_multi", "color_uniform", "color_material")),
                            (self.lighting, ("light_basic", "light_soft", "light_dramatic"))):
            cur = combo.currentData()
            combo.clear()
            for k in keys:
                combo.addItem(tr(k), k)
            idx = combo.findData(cur)
            combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.chk_grid.setText(tr("chk_grid"))
        self.chk_axes.setText(tr("chk_axes"))
        self.chk_smooth.setText(tr("chk_smooth"))

    def set_uniform_color(self, rgba):
        from app.materials import rgba_to_hex
        self._uniform = tuple(rgba)
        self.uniform_btn.setStyleSheet(f"background-color: {rgba_to_hex(rgba)}; color: #000;")