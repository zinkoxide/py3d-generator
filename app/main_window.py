"""Main window: layout, project I/O, execution, undo, import/export, i18n toggle."""

from __future__ import annotations

import ast
import os
import sys
import threading

from PySide6.QtCore import Qt, Signal, QObject, QPoint
from PySide6.QtGui import QUndoStack, QUndoCommand
from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QWidget, QVBoxLayout, QLabel, QStatusBar,
    QFileDialog, QMessageBox, QInputDialog, QDockWidget, QTabWidget,
    QApplication, QPushButton, QTabBar,
)

from app import __version__
from app.i18n import tr, set_language, get_language
from app.code_editor import CodeEditor
from app.viewport import Viewport
from app.object_panel import ObjectPanel
from app.properties_panel import PropertiesPanel
from app.console_panel import ConsolePanel
from app.dialogs import (
    ExportDialog, PreferencesDialog, GeometryInfoDialog,
    ShortcutsDialog, AboutDialog, ApiReferenceDialog,
)
from app.menu_bar import build_menus, build_toolbar
from app.panels import Card
from app.sidebar import Sidebar
from app.display_panel import DisplayPanel
from app.export_panel import ExportPanel
from core.scene import Scene
from core.runner import ExecutionRunner
from core import project_manager as pm
from core import exporter as exp
from core import importer as imp


def default_script() -> str:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(here, "examples", "low_poly_house.py")
    try:
        with open(p, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return 'cube(name="Cube", size=(1, 1, 1))\n'


class _Bridge(QObject):
    finished = Signal(object)


class SnapshotCommand(QUndoCommand):
    def __init__(self, win, label, before: dict, after: dict):
        super().__init__(label)
        self.win = win
        self.before = before
        self.after = after

    def _apply(self, d: dict):
        self.win.scene = Scene.from_dict(d)
        self.win._refresh_scene_views()
        self.win._mark_dirty(True)
        self.win._manual_edits = True

    def undo(self):
        self._apply(self.before)

    def redo(self):
        self._apply(self.after)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("app_title"))
        self.resize(1400, 850)
        self._settings_org = "Py3DGenerator"
        self._settings_app = "Py3DGenerator"
        self.scene = Scene(name="Scene")
        self.project_path: str | None = None
        self.project_name = "Untitled"
        self._dirty = False
        self._manual_edits = False
        self.timeout = 20.0
        self.undo_stack = QUndoStack(self)
        self.runner = ExecutionRunner(timeout=self.timeout)
        self._bridge = _Bridge()
        self._bridge.finished.connect(self._on_execution_finished)
        self._running = False
        self._run_thread: threading.Thread | None = None

        # ---------- left sidebar: navigation + available functions ----------
        self.sidebar = Sidebar()
        self.sidebar.functionClicked.connect(self._insert_snippet)
        self.sidebar.navSelected.connect(self._on_nav)
        self.sidebar.setObjectName("SidebarFrame")

        # ---------- center: editor (tab + plus button) over console ----------
        self.editor = CodeEditor()
        self.editor.setPlainText(default_script())
        self.editor.textChanged.connect(lambda: self._mark_dirty(True))
        self.editor.cursorChanged.connect(self._on_cursor)
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setMovable(True)
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.addTab(self.editor, self.project_name + ".py")
        self.editor_tabs.tabBar().setTabButton(0, QTabBar.RightSide, self._make_plus_button())
        self.console = ConsolePanel()

        self.center = QWidget()
        center_layout = QVBoxLayout(self.center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(6)
        center_layout.addWidget(self.editor_tabs, 4)
        center_layout.addWidget(self.console, 2)

        # ---------- viewport card ----------
        self.viewport = Viewport()
        self.viewport.objectSelected.connect(self._on_viewport_select)
        self.viewport.glError.connect(self._on_gl_error)
        self.vp_card = Card(tr("vp_title"), show_close=True)
        self.vp_card.body.setContentsMargins(0, 0, 0, 0)
        self.vp_card.add_widget(self.viewport)
        self.vp_card.closed.connect(self._hide_viewport)

        # ---------- right column: display settings + elements ----------
        self.display_panel = DisplayPanel()
        self.disp_card = Card(tr("disp_title"))
        self.disp_card.add_widget(self.display_panel)
        self.display_panel.colorModeChanged.connect(self._on_color_mode)
        self.display_panel.uniformColorChanged.connect(
            lambda rgba: self.viewport.set_color_mode("uniform", rgba))
        self.display_panel.lightingChanged.connect(self.viewport.set_lighting)
        self.display_panel.gridToggled.connect(self._on_grid_check)
        self.display_panel.axesToggled.connect(self._on_axes_check)
        self.display_panel.smoothToggled.connect(self.viewport.set_smooth)

        self.objects = ObjectPanel()
        self.el_card = Card(tr("elements_title"), collapsible=True)
        self.el_card.add_widget(self.objects)

        self.right = QWidget()
        right_layout = QVBoxLayout(self.right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)
        right_layout.addWidget(self.disp_card, 0)
        right_layout.addWidget(self.el_card, 1)
        self.el_card.setMinimumHeight(170)

        # ---------- bottom-right: export card ----------
        self.export_panel = ExportPanel()
        self.export_panel.browseRequested.connect(self._browse_export_folder)
        self.export_panel.exportRequested.connect(self._export_from_panel)
        self.exp_card = Card(tr("export_title"))
        self.exp_card.add_widget(self.export_panel)

        self.props = PropertiesPanel()
        self.props.transformChanged.connect(self._on_transform_edited)
        self.props.materialChanged.connect(self._on_material_edited)
        self.props.visibilityChanged.connect(self._on_visibility)
        self.props.renameRequested.connect(self.rename_object)
        self.props_card = Card(tr("properties"), collapsible=True, show_close=True)
        self.props_card.add_widget(self.props)
        self.props_card.set_collapsed(True)   # secondary panel — start folded

        self.export_row = QWidget()
        export_row_layout = QVBoxLayout(self.export_row)
        export_row_layout.setContentsMargins(0, 0, 0, 0)
        export_row_layout.addWidget(self.exp_card)
        export_row_layout.addWidget(self.props_card)

        self.right_split = QSplitter(Qt.Vertical)
        self.right_split.addWidget(self.right)
        self.right_split.addWidget(self.export_row)
        self.right_split.setSizes([420, 380])

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.center)
        splitter.addWidget(self.vp_card)
        splitter.addWidget(self.right_split)
        splitter.setSizes([230, 470, 480, 330])
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 4)
        self.setCentralWidget(splitter)
        self._splitter = splitter
        self._center = self.center
        self._right_split = self.right_split

        # object panel signals
        self.objects.selectionChanged.connect(self._on_object_select)
        self.objects.visibilityToggled.connect(self._on_visibility)
        self.objects.deleteRequested.connect(self.delete_object)
        self.objects.duplicateRequested.connect(self.duplicate_object)
        self.objects.renameRequested.connect(self.rename_object)
        self.objects.focusRequested.connect(lambda n: self.viewport.frame_object(n))

        status = QStatusBar()
        self.setStatusBar(status)
        self.status_dot = QLabel("● " + tr("ready"))
        self.status_dot.setStyleSheet("color: #4ade80;")
        self.cursor_label = QLabel("Ln 1, Col 1")
        self.dirty_label = QLabel("")
        self.scene_label = QLabel("0 objects")
        self.py_label = QLabel(f"Python {sys.version_info.major}.{sys.version_info.minor}")
        status.addWidget(self.status_dot)
        status.addWidget(self.cursor_label)
        status.addWidget(self.dirty_label)
        status.addPermanentWidget(self.scene_label)
        status.addPermanentWidget(self.py_label)

        self.setMenuBar(build_menus(self))
        self._toolbar = build_toolbar(self)
        self.addToolBar(self._toolbar)

        self._refresh_scene_views()
        self.console.info(tr("ready_msg"))
        self._update_undo_actions()

    # ---- status/helpers ----
    def _make_plus_button(self):
        btn = QPushButton("+")
        btn.setObjectName("CollapseButton")
        btn.setToolTip(tr("nav_examples"))
        btn.setFixedSize(22, 22)
        btn.clicked.connect(lambda: self._show_examples_menu(btn))
        return btn

    def _show_examples_menu(self, anchor):
        from PySide6.QtWidgets import QMenu
        m = QMenu(self)
        for fname, key in (("00_showcase.py", "ex_showcase"), ("basic_objects.py", "ex_basic"),
                           ("low_poly_house.py", "ex_house"), ("simple_tree.py", "ex_tree"),
                           ("small_village.py", "ex_village"), ("procedural_rocks.py", "ex_rocks")):
            m.addAction(tr(key), lambda checked=False, f=fname: self.load_example_file(self.example_path(f)))
        m.exec(anchor.mapToGlobal(QPoint(0, anchor.height())))

    def _insert_snippet(self, snippet: str):
        """Insert a function template at the cursor position."""
        cur = self.editor.textCursor()
        cur.insertText(snippet)
        self.editor.setFocus()
        self.console.info(tr("btn_insert"))

    def _on_nav(self, key: str):
        if key == "editor":
            self.editor.setFocus()
        elif key == "projects":
            self.open_project()
            self.sidebar.set_nav_checked("editor")
        elif key == "examples":
            m = self.menuBar().actions()
            for a in m:
                if a.text().replace("&", "") in ("Examples", "أمثلة"):
                    a.menu().exec(self.sidebar.mapToGlobal(QPoint(180, 120)))
                    break
        elif key == "settings":
            self.editor_preferences()
            self.sidebar.set_nav_checked("editor")
        elif key == "about":
            self.show_about()
            self.sidebar.set_nav_checked("editor")

    def _hide_viewport(self):
        self.vp_card.setVisible(False)

    def _on_grid_check(self, on: bool):
        self.viewport.show_grid = bool(on)
        self.act_grid.setChecked(bool(on))
        self.tb_grid.setChecked(bool(on))
        self.viewport.update()

    def _on_axes_check(self, on: bool):
        self.viewport.show_axes = bool(on)
        self.act_axes.setChecked(bool(on))
        self.viewport.update()

    def _on_color_mode(self, mode: str):
        self.viewport.set_color_mode(mode)
        self.display_panel.uniform_row.setVisible(mode == "uniform")

    def _browse_export_folder(self, current: str):
        d = QFileDialog.getExistingDirectory(self, tr("lbl_folder"), current or os.path.expanduser("~"))
        if d:
            self.export_panel.folder_edit.setText(d)

    def _export_from_panel(self, name: str, folder: str, fmt: str, include_materials: bool):
        if not self.scene.objects:
            QMessageBox.information(self, tr("export_title"), "Nothing to export — generate a model first.")
            return
        try:
            os.makedirs(folder, exist_ok=True)
        except OSError as e:
            QMessageBox.critical(self, tr("export_title"), str(e))
            return
        base = os.path.splitext(name)[0] or "model"
        path = os.path.join(folder, base + "." + fmt)
        if os.path.exists(path):
            if QMessageBox.question(self, tr("export_title"),
                                    f"Overwrite existing file?\n{path}") != QMessageBox.Yes:
                return
        # include_materials only matters for formats that support it
        opts = exp.ExportOptions(include_materials=include_materials)
        self._export_with(fmt, opts, path)

    def _on_cursor(self, line, col):
        self.cursor_label.setText(f"Ln {line}, Col {col}")

    def _mark_dirty(self, dirty: bool):
        self._dirty = dirty
        self.dirty_label.setText("● unsaved" if dirty else "")
        base = self.project_name + (" *" if dirty else "")
        self.editor_tabs.setTabText(0, os.path.basename(self.project_path) if self.project_path else base + ".py")

    def _refresh_scene_views(self):
        self.viewport.set_scene(self.scene)
        sel = self.viewport.selected
        self.objects.set_scene(self.scene, sel)
        obj = self.scene.get(sel) if sel else None
        self.props.set_object(obj, self._manual_edits)
        st = self.scene.total_stats()
        self.scene_label.setText(f"{st['objects']} objects · {st['vertices']} verts · {st['faces']} faces")

    def _snapshot(self) -> dict:
        return self.scene.to_dict()

    def _push_snapshot(self, label: str, before: dict):
        after = self._snapshot()
        self.undo_stack.push(SnapshotCommand(self, label, before, after))
        self._update_undo_actions()

    def _update_undo_actions(self):
        self.act_undo.setEnabled(self.undo_stack.canUndo())
        self.act_redo.setEnabled(self.undo_stack.canRedo())

    # ---- selection ----
    def _on_viewport_select(self, name):
        self.objects.set_scene(self.scene, name)
        self.props.set_object(self.scene.get(name) if name else None, self._manual_edits)

    def _on_object_select(self, name):
        self.viewport.set_selected(name)
        self.props.set_object(self.scene.get(name) if name else None, self._manual_edits)

    # ---- project ----
    def _confirm_unsaved(self) -> bool:
        if not self._dirty:
            return True
        r = QMessageBox.question(self, "Unsaved changes",
                                 "You have unsaved changes. Continue without saving?",
                                 QMessageBox.Yes | QMessageBox.No)
        return r == QMessageBox.Yes

    def new_project(self):
        if not self._confirm_unsaved():
            return
        self.editor.setPlainText(default_script())
        self.scene = Scene()
        self.project_path = None
        self.project_name = "Untitled"
        self._manual_edits = False
        self.undo_stack.clear()
        self._refresh_scene_views()
        self._mark_dirty(False)
        self.console.info("New project created.")

    def open_project(self):
        if not self._confirm_unsaved():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Open Project", os.path.expanduser("~"), "*.py3d")
        if not path:
            return
        try:
            data = pm.load_project(path)
        except ValueError as e:
            QMessageBox.critical(self, "Open failed", str(e))
            return
        # NEVER auto-execute embedded code (trust model)
        self.editor.setPlainText(data.get("code", ""))
        self.editor.clear_errors()
        self.project_path = path
        self.project_name = data.get("project_name", "Untitled")
        vp = data.get("viewport", {})
        self.viewport.show_grid = bool(vp.get("grid", True))
        self.viewport.show_axes = bool(vp.get("axes", True))
        self.timeout = float(data.get("execution", {}).get("timeout", 20.0))
        self.runner.timeout = self.timeout
        self.scene = Scene()
        self._manual_edits = False
        self.undo_stack.clear()
        self._refresh_scene_views()
        self._mark_dirty(False)
        self._add_recent(path)
        self.console.warn("Project opened. Code was NOT executed automatically — press Run to generate.")

    def _collect_project(self) -> dict:
        return {
            "project_name": self.project_name,
            "code": self.editor.toPlainText(),
            "scene_settings": {"background": list(self.scene.background)},
            "execution": {"timeout": self.timeout},
            "viewport": {"grid": self.viewport.show_grid, "axes": self.viewport.show_axes,
                         "wireframe": self.viewport.wireframe},
        }

    def save_project(self):
        if self.project_path:
            pm.save_project(self.project_path, self._collect_project())
            self._mark_dirty(False)
            self.console.info(f"Saved: {self.project_path}")
        else:
            self.save_project_as()

    def save_project_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Project", os.path.expanduser("~"), "*.py3d")
        if not path:
            return
        self.project_path = pm.save_project(path, self._collect_project())
        self.project_name = os.path.splitext(os.path.basename(self.project_path))[0]
        self._mark_dirty(False)
        self._add_recent(self.project_path)
        self.console.info(f"Saved: {self.project_path}")

    def _add_recent(self, path: str):
        from PySide6.QtCore import QSettings
        s = QSettings(self._settings_org, self._settings_app)
        rec = s.value("recent", [])
        if not isinstance(rec, list):
            rec = [rec] if rec else []
        rec = [p for p in rec if p != path]
        rec.insert(0, path)
        s.setValue("recent", rec[:8])
        self.refresh_recent_menu()

    def refresh_recent_menu(self):
        if not hasattr(self, "recent_menu"):
            return
        from PySide6.QtCore import QSettings
        self.recent_menu.clear()
        s = QSettings(self._settings_org, self._settings_app)
        rec = s.value("recent", []) or []
        if not rec:
            a = self.recent_menu.addAction("(empty)")
            a.setEnabled(False)
            return
        for p in rec:
            self.recent_menu.addAction(p, lambda checked=False, pp=p: self._open_recent(pp))

    def _open_recent(self, path: str):
        if not self._confirm_unsaved():
            return
        try:
            data = pm.load_project(path)
        except ValueError as e:
            QMessageBox.critical(self, "Open failed", str(e))
            return
        self.editor.setPlainText(data.get("code", ""))
        self.project_path = path
        self.project_name = data.get("project_name", "Untitled")
        self.scene = Scene()
        self._manual_edits = False
        self.undo_stack.clear()
        self._refresh_scene_views()
        self._mark_dirty(False)
        self.console.warn("Project opened. Code was NOT executed automatically.")

    # ---- execution ----
    def run_script(self):
        if self._running:
            return
        if self._manual_edits:
            r = QMessageBox.warning(self, "Discard manual edits?",
                                    "You edited objects manually. Running the script will replace the "
                                    "scene and discard those edits. Continue?",
                                    QMessageBox.Yes | QMessageBox.No)
            if r != QMessageBox.Yes:
                return
        source = self.editor.toPlainText()
        if not source.strip():
            QMessageBox.information(self, "Nothing to run", "The editor is empty.")
            return
        self._running = True
        self.tb_run.setProperty("running", True)
        self.tb_run.style().unpolish(self.tb_run)
        self.tb_run.style().polish(self.tb_run)
        self.tb_run.setText(tr("tb_running"))
        self.tb_stop.setEnabled(True)
        self.editor.clear_errors()
        self.console.info("Starting model generation…")
        self.runner.timeout = self.timeout
        self._run_thread = threading.Thread(target=self._run_worker, args=(source,), daemon=True)
        self._run_thread.start()

    def _run_worker(self, source: str):
        result = self.runner.run(source)
        self._bridge.finished.emit(result)

    def _on_execution_finished(self, result):
        self._running = False
        self.tb_run.setProperty("running", False)
        self.tb_run.style().unpolish(self.tb_run)
        self.tb_run.style().polish(self.tb_run)
        self.tb_run.setText(tr("tb_run"))
        self.tb_stop.setEnabled(False)
        if result.stdout:
            self.console.stdout(result.stdout)
        if result.cancelled:
            self.console.warn("Execution stopped by user. Last valid scene kept.")
            return
        if result.timed_out:
            self.console.error(f"Execution timed out after {self.timeout:g}s. Last valid scene kept.")
            QMessageBox.warning(self, "Timed out", f"Execution timed out after {self.timeout:g}s.")
            return
        if not result.success or result.scene is None:
            err = result.error or {"line": 0, "message": "Unknown error"}
            line = int(err.get("line", 0) or 0)
            msg = str(err.get("message", "Error"))
            self.console.error(msg)
            if line > 0:
                self.editor.set_error_lines({line})
                cursor = self.editor.textCursor()
                block = self.editor.document().findBlockByNumber(line - 1)
                if block.isValid():
                    cursor.setPosition(block.position())
                    self.editor.setTextCursor(cursor)
            else:
                self.editor.clear_errors()
            self.console.warn("Failed script did not corrupt the last valid scene.")
            return
        # success → replace scene (execution mode: replace/regenerate)
        try:
            new_scene = Scene.from_dict(result.scene)
        except Exception as e:
            self.console.error(f"Worker returned invalid scene: {e}")
            return
        self.scene = new_scene
        self.viewport.selected = None
        self._manual_edits = False
        self.undo_stack.clear()  # execution replaces scene; undo history reset (documented)
        self._update_undo_actions()
        self._refresh_scene_views()
        self._mark_dirty(True)
        st = self.scene.total_stats()
        self.console.info(f"Model generated successfully! Objects: {st['objects']}, "
                          f"Vertices: {st['vertices']}, Faces: {st['faces']}, "
                          f"Time: {result.duration:.2f}s. Ready for export.")

    def stop_script(self):
        self.runner.stop()
        self.console.warn("Stopping… (will report if the process cannot stop immediately)")

    # ---- object ops (undoable) ----
    def delete_object(self, name: str):
        obj = self.scene.get(name)
        if obj is None:
            return
        if obj.locked:
            QMessageBox.information(self, "Locked", f"Object '{name}' is locked.")
            return
        before = self._snapshot()
        self.scene.objects = [o for o in self.scene.objects if o.name != name]
        if self.viewport.selected == name:
            self.viewport.selected = None
        self._push_snapshot(f"Delete {name}", before)
        self._refresh_scene_views()
        self.console.info(f"Deleted '{name}'.")

    def duplicate_object(self, name: str):
        import copy
        src = self.scene.get(name)
        if src is None:
            return
        before = self._snapshot()
        clone = copy.deepcopy(src)
        base = f"{name}_copy"
        existing = set(self.scene.names())
        new_name = base
        i = 1
        while new_name in existing:
            i += 1
            new_name = f"{base}_{i}"
        clone.name = new_name
        clone.location = (clone.location[0] + 1.0, clone.location[1], clone.location[2])
        self.scene.objects.append(clone)
        self._push_snapshot(f"Duplicate {name}", before)
        self._refresh_scene_views()

    def rename_object(self, old: str, new: str):
        if self.scene.get(new) is not None:
            QMessageBox.warning(self, "Rename", f"An object named '{new}' already exists.")
            return
        obj = self.scene.get(old)
        if obj is None:
            return
        before = self._snapshot()
        obj.name = new
        if self.viewport.selected == old:
            self.viewport.selected = new
        self._push_snapshot(f"Rename {old}", before)
        self._refresh_scene_views()

    def _on_visibility(self, name: str, visible: bool):
        obj = self.scene.get(name)
        if obj is None:
            return
        before = self._snapshot()
        obj.visible = bool(visible)
        self._push_snapshot(f"Visibility {name}", before)
        self._refresh_scene_views()

    def _on_transform_edited(self, name: str, values: dict):
        obj = self.scene.get(name)
        if obj is None:
            return
        before = self._snapshot()
        try:
            obj.location = tuple(float(x) for x in values["location"])
            obj.rotation = tuple(float(x) for x in values["rotation"])
            obj.scale = tuple(max(0.001, float(x)) for x in values["scale"])
        except (ValueError, TypeError, KeyError):
            return
        # apply without pushing every keystroke? push coalesced: use snapshot push each change is noisy
        # but acceptable; mark manual edits
        self._manual_edits = True
        self.undo_stack.push(SnapshotCommand(self, f"Transform {name}", before, self._snapshot()))
        self._update_undo_actions()
        self._refresh_scene_views()
        self.props.set_object(obj, True)

    def _on_material_edited(self, name: str, values: dict):
        obj = self.scene.get(name)
        if obj is None:
            return
        before = self._snapshot()
        try:
            obj.color = tuple(float(x) for x in values["color"])
            obj.roughness = float(values["roughness"])
            obj.metallic = float(values["metallic"])
        except (ValueError, TypeError, KeyError):
            return
        self._manual_edits = True
        self.undo_stack.push(SnapshotCommand(self, f"Material {name}", before, self._snapshot()))
        self._update_undo_actions()
        self._refresh_scene_views()
        self.props.set_object(obj, True)

    def undo(self):
        self.undo_stack.undo()
        self._update_undo_actions()

    def redo(self):
        self.undo_stack.redo()
        self._update_undo_actions()

    # ---- examples ----
    @staticmethod
    def example_path(filename: str) -> str:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(root, "examples", filename)

    def load_example_file(self, path: str):
        """Load an example script into the editor (one click, no typing)."""
        if not self._confirm_unsaved():
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
        except OSError as e:
            QMessageBox.critical(self, "Example failed", f"Could not load example:\n{e}")
            return
        # Example code ships with the app, but still never auto-run it.
        self.editor.setPlainText(code)
        self.editor.clear_errors()
        self.project_path = None
        self.project_name = os.path.splitext(os.path.basename(path))[0]
        self.scene = Scene()
        self.viewport.selected = None
        self._manual_edits = False
        self.undo_stack.clear()
        self._update_undo_actions()
        self._refresh_scene_views()
        self._mark_dirty(False)
        self.console.info(f"Example '{self.project_name}' {tr('ex_loaded')}")

    # ---- editor slots ----
    def copy_all_code(self):
        QApplication.clipboard().setText(self.editor.toPlainText())
        self.console.info("Entire script copied to clipboard.")

    def editor_cut(self):
        self.editor.cut()

    def editor_copy(self):
        self.editor.copy()

    def editor_paste(self):
        self.editor.paste()

    def editor_select_all(self):
        self.editor.selectAll()

    def find_dialog(self):
        text, ok = QInputDialog.getText(self, "Find", "Find:")
        if ok and text:
            if not self.editor.find_text(text):
                QMessageBox.information(self, "Find", f"'{text}' not found.")

    def replace_dialog(self):
        find, ok = QInputDialog.getText(self, "Replace", "Find:")
        if not (ok and find):
            return
        rep, ok = QInputDialog.getText(self, "Replace", f"Replace '{find}' with:")
        if not ok:
            return
        count = 0
        self.editor.moveCursor(self.editor.textCursor().Start)
        while self.editor.find_text(find):
            self.editor.replace_current(rep)
            count += 1
            if count > 10000:
                break
        QMessageBox.information(self, "Replace", f"Replaced {count} occurrence(s).")

    def editor_preferences(self):
        d = PreferencesDialog(self, tab_size=self.editor.tab_size, timeout=self.timeout)
        if d.exec():
            self.editor.set_tab_size(d.tab_size.value())
            self.timeout = float(d.timeout.value())
            self.runner.timeout = self.timeout
            self._mark_dirty(True)

    def validate_code(self):
        try:
            ast.parse(self.editor.toPlainText())
        except SyntaxError as e:
            self.console.error(f"SyntaxError: {e.msg} (line {e.lineno})")
            self.editor.set_error_lines({e.lineno or 1})
            return
        self.editor.clear_errors()
        self.console.info("Code validation passed (syntax OK).")

    def format_code(self):
        text = self.editor.toPlainText()
        try:
            import black  # optional
            text = black.format_str(text, mode=black.Mode())
            self.editor.setPlainText(text)
            self.console.info("Formatted with black.")
        except ImportError:
            lines = [ln.expandtabs(self.editor.tab_size).rstrip() for ln in text.splitlines()]
            self.editor.setPlainText("\n".join(lines) + ("\n" if text.endswith("\n") else ""))
            self.console.info("Formatted (basic: tabs expanded, trailing whitespace removed).")

    # ---- view slots ----
    def reset_layout(self):
        self.sidebar.setVisible(True)
        self.vp_card.setVisible(True)
        self._right_split.setVisible(True)
        self.console.setVisible(True)
        self.act_view_editor.setChecked(True)
        self.act_view_objects.setChecked(True)
        self.act_view_console.setChecked(True)
        self._splitter.setSizes([230, 470, 480, 330])

    def toggle_editor(self, on: bool):
        self.editor_tabs.setVisible(on)

    def toggle_objects(self, on: bool):
        self.objects.setVisible(on)

    def toggle_console(self, on: bool):
        self.console.setVisible(on)

    def toggle_grid(self, on: bool = None):
        state = (not self.viewport.show_grid) if on is None else bool(on)
        if isinstance(on, bool):
            state = on
        self.viewport.show_grid = state
        self.act_grid.setChecked(state)
        self.tb_grid.setChecked(state)
        self.viewport.update()

    def toggle_grid_btn(self):
        self.toggle_grid(self.tb_grid.isChecked())

    def toggle_axes(self, on: bool):
        self.viewport.show_axes = bool(on)
        self.viewport.update()

    def set_display_mode(self, mode: str):
        """Set viewport display mode: 'solid' | 'wireframe' | 'both'."""
        if mode not in ("solid", "wireframe", "both"):
            return
        self.viewport.wireframe = mode
        idx = {"solid": 0, "wireframe": 1, "both": 2}[mode]
        if hasattr(self, "display_combo") and self.display_combo.currentIndex() != idx:
            self.display_combo.setCurrentIndex(idx)
        for attr in ("act_disp_solid", "act_disp_wire", "act_disp_both"):
            act = getattr(self, attr, None)
            if act is not None and not act.isChecked():
                want = {"act_disp_solid": "solid", "act_disp_wire": "wireframe",
                        "act_disp_both": "both"}[attr] == mode
                if want:
                    act.setChecked(True)
        self.viewport.update()

    def toggle_wireframe(self, on: bool):
        # Kept for compatibility: checkbox-style callers map to solid/wireframe.
        self.set_display_mode("wireframe" if on else "solid")

    def toggle_language(self):
        set_language("ar" if get_language() == "en" else "en")
        self._retranslate_ui()

    def _retranslate_ui(self):
        """Update all visible text in place for the active language (safe after show)."""
        from app.menu_bar import update_menu_texts, update_toolbar_texts
        lang = get_language()
        self.setWindowTitle(tr("app_title"))
        self.setLayoutDirection(Qt.RightToLeft if lang == "ar" else Qt.LeftToRight)
        # code + logs stay left-to-right in Arabic mode
        self.editor.setLayoutDirection(Qt.LeftToRight)
        self.console.setLayoutDirection(Qt.LeftToRight)
        update_menu_texts(self)
        update_toolbar_texts(self)
        self.vp_card.set_title(tr("vp_title"))
        self.disp_card.set_title(tr("disp_title"))
        self.el_card.set_title(tr("elements_title"))
        self.exp_card.set_title(tr("export_title"))
        self.props_card.set_title(tr("properties"))
        self.display_panel.retranslate()
        self.export_panel.retranslate()
        self.console.retranslate()
        self.sidebar.retranslate()
        self.status_dot.setText("\u25cf " + tr("ready"))
        self._update_undo_actions()
        self.console.info(f"{tr('language')}: {lang.upper()}")

    # ---- tools/help ----
    def geometry_info(self):
        GeometryInfoDialog(self, self.scene.total_stats()).exec()

    def show_docs(self):
        QMessageBox.information(
            self, "Documentation",
            "Workflow: 1) Write Python using the API (see API Reference). "
            "2) Press Run (F5). 3) Orbit: left-drag; Pan: right/middle-drag or Shift+drag; "
            "Zoom: wheel. 4) Edit properties (manual edits diverge from code). "
            "5) Export GLB. Projects (.py3d) never auto-run code on open.")

    def show_api_ref(self):
        ApiReferenceDialog(self).exec()

    def show_shortcuts(self):
        ShortcutsDialog(self).exec()

    def show_about(self):
        AboutDialog(self).exec()

    def _on_gl_error(self, msg: str):
        self.console.error(msg)

    # ---- import/export ----
    def _export_with(self, fmt: str, opts: exp.ExportOptions | None = None, path: str | None = None):
        try:
            if fmt == "glb":
                exp.export_glb(self.scene, path, opts)
            elif fmt == "obj":
                exp.export_obj(self.scene, path, opts)
            elif fmt == "stl":
                exp.export_stl(self.scene, path, opts)
        except ValueError as e:
            QMessageBox.critical(self, "Export failed", str(e))
            self.console.error(f"Export failed: {e}")
            return
        self.console.info(f"Exported {fmt.upper()}: {path}")
        QMessageBox.information(self, "Export complete", f"Exported:\n{path}")

    def export_glb(self):
        d = QFileDialog.getSaveFileName(self, "Export as GLB", os.path.expanduser("~/model.glb"), "*.glb")
        if not d[0]:
            return
        path = d[0] if d[0].endswith(".glb") else d[0] + ".glb"
        if os.path.exists(path):
            if QMessageBox.question(self, "Overwrite?", f"Overwrite existing file?\n{path}") != QMessageBox.Yes:
                return
        self._export_with("glb", exp.ExportOptions(), path)

    def export_glb_options(self):
        dlg = ExportDialog(self, default_name=self.project_name)
        if not dlg.exec():
            return
        directory = dlg.dir_edit.text().strip() or os.path.expanduser("~")
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, dlg.name_edit.text().strip() or "model") + ".glb"
        if os.path.exists(path):
            if QMessageBox.question(self, "Overwrite?", f"Overwrite existing file?\n{path}") != QMessageBox.Yes:
                return
        self._export_with("glb", dlg.options(), path)

    def export_obj(self):
        d = QFileDialog.getSaveFileName(self, "Export as OBJ", os.path.expanduser("~/model.obj"), "*.obj")
        if not d[0]:
            return
        path = d[0] if d[0].endswith(".obj") else d[0] + ".obj"
        if os.path.exists(path):
            if QMessageBox.question(self, "Overwrite?", f"Overwrite?\n{path}") != QMessageBox.Yes:
                return
        self.console.warn("OBJ limitation: materials/hierarchy approximated; companion .mtl may be written.")
        self._export_with("obj", exp.ExportOptions(), path)

    def export_stl(self):
        d = QFileDialog.getSaveFileName(self, "Export as STL", os.path.expanduser("~/model.stl"), "*.stl")
        if not d[0]:
            return
        path = d[0] if d[0].endswith(".stl") else d[0] + ".stl"
        if os.path.exists(path):
            if QMessageBox.question(self, "Overwrite?", f"Overwrite?\n{path}") != QMessageBox.Yes:
                return
        self.console.warn("STL limitation: geometry only, no colors/hierarchy.")
        self._export_with("stl", exp.ExportOptions(), path)

    def import_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import 3D Model", os.path.expanduser("~"),
            "3D models (*.glb *.gltf *.obj *.stl)")
        if not path:
            return
        try:
            imported = imp.import_model(path)
        except ValueError as e:
            QMessageBox.critical(self, "Import failed", str(e))
            self.console.error(f"Import failed: {e}")
            return
        before = self._snapshot()
        existing = set(self.scene.names())
        for o in imported.objects:
            name = o.name
            i = 1
            while name in existing:
                i += 1
                name = f"{o.name}_{i}"
            o.name = name
            existing.add(name)
            self.scene.objects.append(o)
        self._push_snapshot(f"Import {os.path.basename(path)}", before)
        self._manual_edits = True  # imported models have no Python source representation
        self._refresh_scene_views()
        self.console.warn(f"Imported {len(imported.objects)} object(s) from {path}. "
                          "Note: imports cannot be converted back to Python code.")

    # ---- keyboard ----
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            n = self.viewport.selected or self.objects.selected_name()
            if n:
                self.delete_object(n)
                return
        if event.key() == Qt.Key_F5 or (event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_Return):
            self.run_script()
            return
        if event.key() == Qt.Key_F:
            self.viewport.frame_object()
            return
        if event.key() == Qt.Key_Home:
            self.viewport.reset_camera()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        if self._running:
            self.runner.stop()
        if not self._confirm_unsaved():
            event.ignore()
            return
        event.accept()
