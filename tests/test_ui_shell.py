"""Redesigned shell: sidebar, cards, display settings, export panel (headless)."""
import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication


def _win():
    app = QApplication.instance() or QApplication([])
    from app.main_window import MainWindow
    return MainWindow()


def _silence_dialogs(monkeypatch):
    """Modal dialogs would block forever in headless tests."""
    from PySide6.QtWidgets import QMessageBox, QFileDialog, QInputDialog
    for name in ("information", "critical", "warning"):
        monkeypatch.setattr(QMessageBox, name, staticmethod(lambda *a, **k: QMessageBox.Yes))
    monkeypatch.setattr(QMessageBox, "question", staticmethod(lambda *a, **k: QMessageBox.Yes))
    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: ("", "")))
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", staticmethod(lambda *a, **k: ""))
    monkeypatch.setattr(QInputDialog, "getText", staticmethod(lambda *a, **k: ("", True)))


def test_shell_components_exist():
    w = _win()
    for attr in ("sidebar", "vp_card", "disp_card", "el_card", "exp_card",
                 "props_card", "display_panel", "export_panel", "console"):
        assert hasattr(w, attr), attr
    # card titles
    assert w.vp_card.title_label.text()
    assert w.el_card.title_label.text()
    assert w.exp_card.title_label.text()


def test_sidebar_function_click_inserts_snippet():
    w = _win()
    w.editor.clear()
    w._insert_snippet('cube(name="X")')
    assert 'cube(name="X")' in w.editor.toPlainText()


def test_display_settings_drive_viewport():
    w = _win()
    w.display_panel.chk_grid.setChecked(False)
    assert w.viewport.show_grid is False
    w.display_panel.chk_grid.setChecked(True)
    assert w.viewport.show_grid is True

    w.display_panel.chk_axes.setChecked(False)
    assert w.viewport.show_axes is False

    w.display_panel.chk_smooth.setChecked(False)
    assert w.viewport.smooth is False

    w.display_panel.lighting.setCurrentIndex(2)   # dramatic
    assert w.viewport.lighting_mode == "dramatic"

    w.display_panel.color_mode.setCurrentIndex(1)  # uniform
    assert w.viewport.color_mode == "uniform"
    w.display_panel.color_mode.setCurrentIndex(0)  # multi
    assert w.viewport.color_mode == "multi"


def test_console_separates_output_and_errors():
    w = _win()
    w.console.clear()
    w.console.info("hello")
    w.console.error("boom")
    assert "hello" in w.console.out_view.toPlainText()
    assert "hello" not in w.console.err_view.toPlainText()
    assert "boom" in w.console.err_view.toPlainText()
    assert w.console.error_count() == 1


def test_export_panel_writes_glb(monkeypatch):
    _silence_dialogs(monkeypatch)
    w = _win()
    # give the window a real scene (skip confirm dialogs)
    w._confirm_unsaved = lambda: True
    w.load_example_file(w.example_path("simple_tree.py"))
    from core.execution_worker import execute_source
    from core.scene import Scene
    res = execute_source(w.editor.toPlainText())
    w.scene = Scene.from_dict(res["scene"])
    w._refresh_scene_views()

    tmp = tempfile.mkdtemp()
    w.export_panel.name_edit.setText("mytree")
    w.export_panel.folder_edit.setText(tmp)
    w.export_panel.format_combo.setCurrentIndex(0)  # glb
    w.export_panel._emit()

    out = os.path.join(tmp, "mytree.glb")
    assert os.path.isfile(out) and os.path.getsize(out) > 100


def test_language_toggle_updates_cards():
    w = _win()
    w.toggle_language()
    from app.i18n import get_language
    assert get_language() == "ar"
    assert "تصدير" in w.exp_card.title_label.text()
    w.toggle_language()
    assert get_language() == "en"
    assert "Export" in w.exp_card.title_label.text()