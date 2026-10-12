"""Export card: filename, output folder, format, materials toggle, big export button."""

from __future__ import annotations

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QCheckBox, QPushButton,
)

from app.i18n import tr


class ExportPanel(QWidget):
    exportRequested = Signal(str, str, str, bool)  # filename, folder, format, include_materials
    browseRequested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(8)

        # --- file name ---
        self.lbl_file = QLabel(tr("lbl_file"))
        layout.addWidget(self.lbl_file)
        name_row = QHBoxLayout()
        self.name_edit = QLineEdit("house")
        self.name_edit.textChanged.connect(self._sync_ext)
        name_row.addWidget(self.name_edit, 1)
        self.ext_label = QLabel(".glb")
        self.ext_label.setObjectName("DimLabel")
        name_row.addWidget(self.ext_label)
        layout.addLayout(name_row)

        # --- save location ---
        self.lbl_folder = QLabel(tr("lbl_folder"))
        layout.addWidget(self.lbl_folder)
        folder_row = QHBoxLayout()
        self.folder_edit = QLineEdit(os.path.expanduser("~"))
        folder_row.addWidget(self.folder_edit, 1)
        self.browse_btn = QPushButton(tr("btn_browse"))
        self.browse_btn.clicked.connect(
            lambda: self.browseRequested.emit(self.folder_edit.text().strip()))
        folder_row.addWidget(self.browse_btn)
        layout.addLayout(folder_row)

        # --- format ---
        self.lbl_format = QLabel(tr("lbl_format"))
        layout.addWidget(self.lbl_format)
        self.format_combo = QComboBox()
        self.format_combo.addItem(tr("fmt_glb"), "glb")
        self.format_combo.addItem(tr("fmt_obj"), "obj")
        self.format_combo.addItem(tr("fmt_stl"), "stl")
        self.format_combo.currentIndexChanged.connect(self._sync_ext)
        layout.addWidget(self.format_combo)

        # --- materials ---
        self.chk_materials = QCheckBox(tr("chk_materials"))
        self.chk_materials.setChecked(True)
        layout.addWidget(self.chk_materials)

        layout.addStretch(1)

        # --- big export button ---
        self.export_btn = QPushButton(tr("btn_export"))
        self.export_btn.setObjectName("BigExport")
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.clicked.connect(self._emit)
        layout.addWidget(self.export_btn)

    def _sync_ext(self):
        fmt = self.format_combo.currentData() or "glb"
        self.ext_label.setText("." + fmt)
        self.export_btn.setText(tr("btn_export") if fmt == "glb" else tr("btn_export_other"))

    def _emit(self):
        fmt = self.format_combo.currentData() or "glb"
        name = self.name_edit.text().strip() or "model"
        folder = self.folder_edit.text().strip() or os.path.expanduser("~")
        self.exportRequested.emit(name, folder, fmt, self.chk_materials.isChecked())

    def set_project_name(self, name: str):
        base = os.path.splitext(os.path.basename(name or ""))[0]
        if base and base.lower() not in ("untitled", ""):
            self.name_edit.setText(base)

    def retranslate(self):
        self.lbl_file.setText(tr("lbl_file"))
        self.lbl_folder.setText(tr("lbl_folder"))
        self.lbl_format.setText(tr("lbl_format"))
        self.browse_btn.setText(tr("btn_browse"))
        self.chk_materials.setText(tr("chk_materials"))
        cur = self.format_combo.currentData()
        self.format_combo.clear()
        for key in ("fmt_glb", "fmt_obj", "fmt_stl"):
            self.format_combo.addItem(tr(key), key.split("_")[1])
        idx = self.format_combo.findData(cur)
        self.format_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self._sync_ext()