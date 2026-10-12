"""Dark theme (restrained blue accent), readable typography."""

DARK_QSS = """
* { font-family: "Segoe UI", "Noto Sans", "Inter", sans-serif; }
QMainWindow, QWidget { background-color: #1a2230; color: #dbe2ee; }
QMenuBar { background-color: #141b28; color: #dbe2ee; padding: 2px; }
QMenuBar::item:selected { background-color: #223148; }
QMenu { background-color: #1e2839; color: #dbe2ee; border: 1px solid #2c3a52; }
QMenu::item:selected { background-color: #2f6fed; color: white; }
QMenu::item:disabled { color: #5b6b85; }
QToolBar { background-color: #141b28; border: none; spacing: 4px; padding: 4px; }
QToolButton { background-color: transparent; color: #dbe2ee; border-radius: 6px; padding: 6px; }
QToolButton:hover { background-color: #223148; }
QToolButton:disabled { color: #5b6b85; }
QToolButton#RunButton { background-color: #2f6fed; color: white; font-weight: bold; border-radius: 6px; padding: 6px 14px; }
QToolButton#RunButton:hover { background-color: #3d7dff; }
QToolButton#RunButton[running="true"] { background-color: #b3541e; }
QSplitter::handle { background-color: #242f44; }
QPlainTextEdit, QTextEdit, QTreeWidget, QListWidget, QTableWidget {
    background-color: #101724; color: #dbe2ee; border: 1px solid #2c3a52; border-radius: 6px;
    selection-background-color: #2f6fed; selection-color: white;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #101724; color: #dbe2ee; border: 1px solid #2c3a52; border-radius: 6px; padding: 4px;
}
QPushButton { background-color: #223148; color: #dbe2ee; border: 1px solid #2c3a52; border-radius: 6px; padding: 6px 12px; }
QPushButton:hover { background-color: #2c3d5c; }
QPushButton:disabled { color: #5b6b85; }
QPushButton#PrimaryButton { background-color: #2f6fed; color: white; border: none; font-weight: bold; }
QPushButton#PrimaryButton:hover { background-color: #3d7dff; }
QTabWidget::pane { border: 1px solid #2c3a52; border-radius: 6px; }
QTabBar::tab { background-color: #141b28; color: #9fb0c9; padding: 6px 14px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background-color: #223148; color: white; }
QStatusBar { background-color: #141b28; color: #9fb0c9; }
QLabel { color: #dbe2ee; }
QLabel#DimLabel { color: #8fa1bd; }
QGroupBox { border: 1px solid #2c3a52; border-radius: 6px; margin-top: 12px; font-weight: bold; }
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; color: #9fb0c9; }
QCheckBox { color: #dbe2ee; }
QSlider::groove:horizontal { background: #2c3a52; height: 4px; border-radius: 2px; }
QSlider::handle:horizontal { background: #2f6fed; width: 14px; margin: -6px 0; border-radius: 7px; }
QHeaderView::section { background-color: #141b28; color: #9fb0c9; border: none; padding: 4px; }

/* ---- redesigned shell ---- */
QFrame#Card { background-color: #1b2432; border: 1px solid #2c3a52; border-radius: 10px; }
QFrame#Sidebar { background-color: #141b28; border: 1px solid #2c3a52; border-radius: 10px; }
QLabel#CardTitle { color: #dbe2ee; font-size: 13px; font-weight: bold; padding: 2px 2px; }
QPushButton#NavButton { background: transparent; border: none; border-radius: 8px;
    text-align: left; padding: 10px 12px; color: #c3cee0; font-size: 13px; }
QPushButton#NavButton:hover { background-color: #223148; color: #ffffff; }
QPushButton#NavButton:checked { background-color: #2f6fed; color: #ffffff; font-weight: bold; }
QPushButton#FuncButton { background: transparent; border: none; border-radius: 6px;
    text-align: left; padding: 5px 8px; color: #82aaff; font-size: 12px; }
QPushButton#FuncButton:hover { background-color: #223148; color: #ffffff; }
QPushButton#CollapseButton { background: transparent; border: none; color: #9fb0c9;
    font-size: 12px; padding: 2px 6px; }
QPushButton#OverlayButton { background-color: rgba(20, 27, 40, 200); color: #dbe2ee;
    border: 1px solid #2c3a52; border-radius: 8px; font-size: 14px; padding: 4px; }
QPushButton#OverlayButton:hover { background-color: #2f6fed; color: white; }
QPushButton#BigExport { background-color: #2f6fed; color: #ffffff; border: none;
    border-radius: 8px; padding: 12px; font-size: 14px; font-weight: bold; }
QPushButton#BigExport:hover { background-color: #3d7dff; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView { background-color: #1e2839; color: #dbe2ee;
    selection-background-color: #2f6fed; border: 1px solid #2c3a52; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #2c3a52; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #3a4c6d; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
"""


def apply_theme(app) -> None:
    app.setStyleSheet(DARK_QSS)
