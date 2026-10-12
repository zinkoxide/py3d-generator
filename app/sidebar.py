"""Left sidebar: app navigation + clickable list of available modeling functions."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QLabel, QSizePolicy,
)

from app.i18n import tr

# (function signature, description i18n key, color swatch, snippet)
FUNCTIONS = [
    ("cube()", "fn_cube", "#4C9AFF", 'cube(name="MyCube", size=(1, 1, 1), location=(0, 0, 0))'),
    ("box()", "fn_box", "#4C9AFF", 'box(name="MyBox", size=(1, 1, 1))'),
    ("sphere()", "fn_sphere", "#E76F51", 'sphere(name="MySphere", radius=1, location=(0, 1, 0), subdivisions=2)'),
    ("icosphere()", "fn_icosphere", "#E76F51", 'icosphere(name="Ball", radius=0.8, subdivisions=1)'),
    ("cylinder()", "fn_cylinder", "#2A9D8F", 'cylinder(name="MyCylinder", radius=0.5, height=2, location=(0, 1, 0))'),
    ("cone()", "fn_cone", "#E9C46A", 'cone(name="MyCone", radius=0.6, height=1.5, location=(0, 0.75, 0))'),
    ("plane()", "fn_plane", "#808080", 'plane(name="Ground", size=(10, 10))'),
    ("torus()", "fn_torus", "#9B5DE5", 'torus(name="MyTorus", major_radius=1, minor_radius=0.25, location=(0, 1, 0))'),
    ("capsule()", "fn_capsule", "#00BBF9", 'capsule(name="MyCapsule", radius=0.5, height=2)'),
    ("ring()", "fn_ring", "#F15BB5", 'ring(name="MyRing", inner_radius=0.5, outer_radius=1, height=0.2)'),
    ("wedge()", "fn_wedge", "#80ED99", 'wedge(name="MyWedge", size=(1, 1, 1))'),
    ("pyramid()", "fn_pyramid", "#F4A261", 'pyramid(name="MyPyramid", size=(1, 1, 1), location=(0, 0.5, 0))'),
    ("custom_mesh()", "fn_custom", "#8D99AE", 'custom_mesh(name="Mesh", vertices=[(0,0,0)], faces=[(0,0,0)])'),
    ("clear_scene()", "fn_clear", "#ff7b72", 'clear_scene()'),
    ("set_transform()", "fn_transform", "#c792ea", 'set_transform("Name", location=(1, 0, 0), rotation=(0, 45, 0), scale=(1, 1, 1))'),
    ("set_material()", "fn_material", "#c3e88d", 'set_material("Name", color="#4C9AFF", roughness=0.5, metallic=0.0)'),
    ("duplicate_object()", "fn_duplicate", "#82aaff", 'duplicate_object("Name", "Name_copy")'),
    ("remove_object()", "fn_remove", "#ff7b72", 'remove_object("Name")'),
    ("grid_repeat()", "fn_grid", "#2A9D8F", 'grid_repeat(base_name="Block", kind="cube", count=(3,1,3), spacing=(2,0,2))'),
    ("random_scatter()", "fn_scatter", "#E9C46A", 'random_scatter(kind="cube", count=10, seed=1)'),
]


class _Swatch(QFrame):
    def __init__(self, color: str):
        super().__init__()
        self.setFixedSize(9, 9)
        self.setStyleSheet(
            f"background-color: {color}; border-radius: 4px; border: 1px solid #2c3a52;")


class Sidebar(QFrame):
    """Navigation (Editor/Projects/Examples/Settings/About) + function list."""

    functionClicked = Signal(str)
    navSelected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setMinimumWidth(190)
        self.setMaximumWidth(320)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(4)

        self.nav_buttons: dict[str, QPushButton] = {}
        nav_items = [
            ("editor", "</>", tr("nav_editor")),
            ("projects", "▤", tr("nav_projects")),
            ("examples", "◇", tr("nav_examples")),
            ("settings", "⚙", tr("nav_settings")),
            ("about", "ⓘ", tr("nav_about")),
        ]
        for key, icon, label in nav_items:
            b = QPushButton(f"  {icon}    {label}")
            b.setObjectName("NavButton")
            b.setCheckable(True)
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            b.clicked.connect(lambda checked=False, k=key: self._on_nav(k))
            self.nav_buttons[key] = b
            layout.addWidget(b)
        self.nav_buttons["editor"].setChecked(True)

        layout.addSpacing(8)

        # --- available functions ---
        self.fun_header = QLabel(tr("nav_functions"))
        self.fun_header.setObjectName("CardTitle")
        layout.addWidget(self.fun_header)

        self.hint = QLabel(tr("btn_insert"))
        self.hint.setObjectName("DimLabel")
        self.hint.setWordWrap(True)
        layout.addWidget(self.hint)

        self.func_list = QWidget()
        self.func_layout = QVBoxLayout(self.func_list)
        self.func_layout.setContentsMargins(0, 0, 0, 0)
        self.func_layout.setSpacing(1)
        self._func_buttons: list[QPushButton] = []
        self._functions_hidden = False
        for sig, desc_key, color, snippet in FUNCTIONS:
            # NOTE: use an explicit container widget — nested layouts don't adopt
            # their child widgets reliably in this PySide6 build.
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(6)
            sw = _Swatch(color)
            rl.addWidget(sw)
            b = QPushButton(f"{sig}  {tr(desc_key)}")
            b.setObjectName("FuncButton")
            b.setToolTip(snippet)
            b.clicked.connect(lambda checked=False, s=snippet: self.functionClicked.emit(s))
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            rl.addWidget(b, 1)
            self.func_layout.addWidget(row)
            self._func_buttons.append(b)
        self.func_layout.addStretch(1)
        layout.addWidget(self.func_list, 1)

    def retranslate(self):
        """Refresh all sidebar labels for the active language."""
        labels = [
            ("editor", "</>", tr("nav_editor")),
            ("projects", "▤", tr("nav_projects")),
            ("examples", "◇", tr("nav_examples")),
            ("settings", "⚙", tr("nav_settings")),
            ("about", "ⓘ", tr("nav_about")),
        ]
        for key, icon, label in labels:
            b = self.nav_buttons.get(key)
            if b is not None:
                b.setText(f"  {icon}    {label}")
        self.fun_header.setText(tr("nav_functions") + ("  ⌃" if self._functions_hidden else "  ⌄"))
        self.hint.setText(tr("btn_insert"))
        for btn, (sig, desc_key, _c, _sn) in zip(self._func_buttons, FUNCTIONS):
            btn.setText(f"{sig}  {tr(desc_key)}")

    def _on_nav(self, key: str) -> None:
        for k, b in self.nav_buttons.items():
            b.setChecked(k == key)
        self.navSelected.emit(key)

    def set_nav_checked(self, key: str) -> None:
        for k, b in self.nav_buttons.items():
            b.setChecked(k == key)

    def set_functions_collapsed(self, collapsed: bool) -> None:
        self._functions_hidden = collapsed
        self.func_list.setVisible(not collapsed)
        self.hint.setVisible(not collapsed)
        self.fun_header.setText(tr("nav_functions") + ("  ⌃" if collapsed else "  ⌄"))