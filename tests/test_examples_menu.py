"""Examples menu: one-click load into editor + copy-all to clipboard (offscreen)."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

EXAMPLES = ["00_showcase.py", "basic_objects.py", "low_poly_house.py",
            "simple_tree.py", "small_village.py", "procedural_rocks.py"]


def _win():
    app = QApplication.instance() or QApplication([])
    from app.main_window import MainWindow
    return MainWindow()


def test_example_loads_into_editor():
    w = _win()
    for fname in EXAMPLES:
        path = w.example_path(fname)
        assert os.path.isfile(path), f"missing example: {fname}"
        w.load_example_file(path)
        with open(path, encoding="utf-8") as f:
            assert w.editor.toPlainText() == f.read()
        assert w.project_path is None


def test_copy_all_code_to_clipboard():
    w = _win()
    w.load_example_file(w.example_path("simple_tree.py"))
    w.copy_all_code()
    assert QApplication.clipboard().text() == w.editor.toPlainText()
    assert "trunk" in QApplication.clipboard().text()
