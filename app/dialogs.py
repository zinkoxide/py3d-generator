"""Dialogs: export options, preferences, info, shortcuts, about, API reference."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QCheckBox, QDoubleSpinBox,
    QDialogButtonBox, QLabel, QTextBrowser, QSpinBox, QFileDialog, QHBoxLayout,
    QPushButton,
)

from core.exporter import ExportOptions
from core import modeling_api as api


class ExportDialog(QDialog):
    def __init__(self, parent=None, default_name="model", fmt="glb"):
        super().__init__(parent)
        self.setWindowTitle("Export as GLB" if fmt == "glb" else f"Export as {fmt.upper()}")
        self.fmt = fmt
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name_edit = QLineEdit(default_name)
        form.addRow("Output filename (without extension)", self.name_edit)
        dir_row = QHBoxLayout()
        self.dir_edit = QLineEdit()
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)
        dir_row.addWidget(self.dir_edit, 1)
        dir_row.addWidget(browse)
        form.addRow("Output directory", dir_row)
        self.cb_hidden = QCheckBox("Include hidden objects")
        self.cb_ground = QCheckBox("Include ground plane")
        self.cb_transforms = QCheckBox("Apply transformations")
        self.cb_transforms.setChecked(True)
        self.cb_validate = QCheckBox("Validate geometry before export")
        self.cb_validate.setChecked(True)
        self.scale = QDoubleSpinBox()
        self.scale.setRange(0.001, 1000.0)
        self.scale.setValue(1.0)
        form.addRow("Export scale", self.scale)
        layout.addLayout(form)
        layout.addWidget(self.cb_hidden)
        layout.addWidget(self.cb_ground)
        layout.addWidget(self.cb_transforms)
        layout.addWidget(self.cb_validate)
        note = QLabel("GLB preserves geometry, transforms, names, colors, roughness/metallic. "
                      "OBJ needs companion material files; STL keeps geometry only.")
        note.setWordWrap(True)
        layout.addWidget(note)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Output directory")
        if d:
            self.dir_edit.setText(d)

    def options(self) -> ExportOptions:
        return ExportOptions(
            include_hidden=self.cb_hidden.isChecked(),
            include_ground=self.cb_ground.isChecked(),
            apply_transforms=self.cb_transforms.isChecked(),
            export_scale=float(self.scale.value()),
            validate=self.cb_validate.isChecked(),
        )


class PreferencesDialog(QDialog):
    def __init__(self, parent=None, tab_size=4, timeout=20.0):
        super().__init__(parent)
        self.setWindowTitle("Editor Preferences")
        layout = QFormLayout(self)
        self.tab_size = QSpinBox()
        self.tab_size.setRange(2, 8)
        self.tab_size.setValue(int(tab_size))
        layout.addRow("Tab size", self.tab_size)
        self.timeout = QDoubleSpinBox()
        self.timeout.setRange(2, 120)
        self.timeout.setValue(float(timeout))
        layout.addRow("Execution timeout (s)", self.timeout)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)


class GeometryInfoDialog(QDialog):
    def __init__(self, parent=None, stats: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Geometry Information")
        layout = QVBoxLayout(self)
        browser = QTextBrowser()
        stats = stats or {}
        browser.setPlainText(
            f"Objects: {stats.get('objects', 0)}\n"
            f"Vertices: {stats.get('vertices', 0)}\n"
            f"Faces: {stats.get('faces', 0)}")
        layout.addWidget(browser)
        btns = QDialogButtonBox(QDialogButtonBox.Close)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)


class ShortcutsDialog(QDialog):
    TEXT = (
        "Ctrl+N New Project   Ctrl+O Open   Ctrl+S Save   Ctrl+Shift+S Save As\n"
        "F5 / Ctrl+Enter Run Script\nCtrl+Z Undo   Ctrl+Y Redo\nCtrl+F Find\n"
        "Ctrl+Shift+C Copy All Code\n"
        "F Frame Selected   Home Reset Camera   Delete Delete Selected"
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        layout = QVBoxLayout(self)
        b = QTextBrowser()
        b.setPlainText(self.TEXT)
        layout.addWidget(b)


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Py3D Generator")
        layout = QVBoxLayout(self)
        from app import __version__
        layout.addWidget(QLabel(f"Py3D Generator v{__version__}\n"
                                "Code-based 3D model creator.\n"
                                "Geometry: Trimesh/NumPy. Viewport: PyOpenGL. UI: PySide6.\n"
                                "No Blender or Godot required."))


class ApiReferenceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Python API Reference")
        self.resize(560, 480)
        layout = QVBoxLayout(self)
        b = QTextBrowser()
        doc = ["<h3>Primitives (true meshes unless noted)</h3><ul>"]
        for line in [
            "cube(name, size, location, rotation, scale, color) — box() is an alias",
            "sphere(name, radius, location, subdivisions, color) — icosphere() same generator",
            "cylinder(name, radius, height, location, sections, color)",
            "cone(name, radius, height, location, sections, color)",
            "plane(name, size, location, color) — XZ ground plane",
            "torus(name, major_radius, minor_radius, location, color)",
            "capsule(name, radius, height, location, color)",
            "ring(name, inner_radius, outer_radius, height, location, color)",
            "wedge(name, size, location, color) — triangular prism",
            "pyramid(name, size, location, color) — square pyramid",
            "custom_mesh(name, vertices=[(x,y,z)..], faces=[(i,j,k)..]) — raw lists, no numpy needed",
        ]:
            doc.append(f"<li>{line}</li>")
        doc.append("</ul><h3>Scene</h3><ul>")
        for line in [
            "clear_scene(), set_background(color), set_scene_name(name), get_objects()",
            "remove_object(name), duplicate_object(name, new_name)",
            "set_transform(name, location, rotation[deg], scale), set_material(name, color, roughness, metallic)",
            "grid_repeat(...), random_scatter(...) — deterministic with seed=",
            "Conventions: Y-up, rotations in degrees, position= alias of location.",
        ]:
            doc.append(f"<li>{line}</li>")
        doc.append("</ul>")
        b.setHtml("".join(doc))
        layout.addWidget(b)
