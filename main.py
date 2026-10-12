"""Py3D Generator entry point."""

from __future__ import annotations

import os
import sys


def check_dependencies() -> list[str]:
    missing = []
    for mod, pkg in (("PySide6", "PySide6"), ("numpy", "numpy"),
                     ("trimesh", "trimesh"), ("OpenGL", "PyOpenGL")):
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)
    return missing


def main() -> int:
    missing = check_dependencies()
    if missing:
        print("Missing dependencies: " + ", ".join(missing), file=sys.stderr)
        print("Run: pip install -r requirements.txt", file=sys.stderr)
        return 1
    # Qt + OpenGL: request desktop GL before creating the app
    try:
        from PySide6.QtCore import Qt, QCoreApplication
        QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    except Exception:
        pass
    from PySide6.QtWidgets import QApplication, QMessageBox
    from app.theme import apply_theme
    from app.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Py3D Generator")
    app.setOrganizationName("Py3DGenerator")
    apply_theme(app)
    try:
        win = MainWindow()
    except Exception as e:
        QMessageBox.critical(None, "Startup failed", f"Could not start Py3D Generator:\n{e}")
        return 1
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
