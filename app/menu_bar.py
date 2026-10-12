"""Menu bar + toolbar builders. All actions route to MainWindow slots."""

from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenuBar, QToolBar

from app.i18n import tr


def build_menus(win) -> QMenuBar:
    mb = QMenuBar(win)

    m_file = mb.addMenu(tr("menu_file"))

    def add(menu, text, slot, shortcut=None, enabled=True):
        a = QAction(text, win)
        if shortcut:
            a.setShortcut(shortcut)
        a.triggered.connect(slot)
        a.setEnabled(enabled)
        menu.addAction(a)
        return a

    win.act_new = add(m_file, tr("file_new"), win.new_project, "Ctrl+N")
    win.act_open = add(m_file, tr("file_open"), win.open_project, "Ctrl+O")
    win.act_save = add(m_file, tr("file_save"), win.save_project, "Ctrl+S")
    win.act_save_as = add(m_file, tr("file_saveas"), win.save_project_as, "Ctrl+Shift+S")
    m_file.addSeparator()
    win.act_import = add(m_file, tr("file_import"), win.import_model)
    win.act_export_glb = add(m_file, tr("file_export_glb"), win.export_glb)
    win.act_export_opts = add(m_file, tr("file_export_opts"), win.export_glb_options)
    win.act_export_obj = add(m_file, tr("file_export_obj"), win.export_obj)
    win.act_export_stl = add(m_file, tr("file_export_stl"), win.export_stl)
    m_file.addSeparator()
    win.recent_menu = m_file.addMenu(tr("file_recent"))
    win.refresh_recent_menu()
    m_file.addSeparator()
    add(m_file, tr("file_exit"), win.close, "Ctrl+Q")

    m_edit = mb.addMenu(tr("menu_edit"))
    win.act_undo = add(m_edit, tr("edit_undo"), win.undo, "Ctrl+Z")
    win.act_redo = add(m_edit, tr("edit_redo"), win.redo, "Ctrl+Y")
    m_edit.addSeparator()
    win.act_cut = add(m_edit, tr("edit_cut"), win.editor_cut, "Ctrl+X")
    win.act_copy = add(m_edit, tr("edit_copy"), win.editor_copy, "Ctrl+C")
    win.act_paste = add(m_edit, tr("edit_paste"), win.editor_paste, "Ctrl+V")
    win.act_select_all = add(m_edit, tr("edit_selectall"), win.editor_select_all, "Ctrl+A")
    m_edit.addSeparator()
    add(m_edit, tr("edit_find"), win.find_dialog, "Ctrl+F")
    add(m_edit, tr("edit_replace"), win.replace_dialog, "Ctrl+H")
    add(m_edit, tr("edit_copyall"), win.copy_all_code, "Ctrl+Shift+C")
    m_edit.addSeparator()
    add(m_edit, tr("edit_prefs"), win.editor_preferences)

    m_view = mb.addMenu(tr("menu_view"))
    add(m_view, tr("view_layout"), win.reset_layout)
    win.act_view_editor = QAction(tr("view_editor"), win, checkable=True,
                                  checked=win.editor_tabs.isVisible())
    win.act_view_editor.toggled.connect(win.toggle_editor)
    m_view.addAction(win.act_view_editor)
    win.act_view_objects = QAction(tr("view_objects"), win, checkable=True,
                                   checked=win.objects.isVisible())
    win.act_view_objects.toggled.connect(win.toggle_objects)
    m_view.addAction(win.act_view_objects)
    win.act_view_console = QAction(tr("view_console"), win, checkable=True,
                                   checked=win.console.isVisible())
    win.act_view_console.toggled.connect(win.toggle_console)
    m_view.addAction(win.act_view_console)
    m_view.addSeparator()
    add(m_view, tr("view_reset_cam"), win.viewport.reset_camera, "Home")
    win.act_grid = QAction(tr("view_grid"), win, checkable=True,
                           checked=win.viewport.show_grid)
    win.act_grid.toggled.connect(win.toggle_grid)
    m_view.addAction(win.act_grid)
    win.act_axes = QAction(tr("view_axes"), win, checkable=True,
                           checked=win.viewport.show_axes)
    win.act_axes.toggled.connect(win.toggle_axes)
    m_view.addAction(win.act_axes)
    disp_menu = m_view.addMenu(tr("view_display"))
    from PySide6.QtGui import QActionGroup
    win.display_group = QActionGroup(win)
    win.display_group.setExclusive(True)
    for mode, label in (("solid", tr("disp_solid")), ("wireframe", tr("disp_wire")),
                        ("both", tr("disp_both"))):
        a = QAction(label, win, checkable=True, checked=(win.viewport.wireframe == mode))
        a.setData(mode)
        a.triggered.connect(lambda checked=False, m=mode: win.set_display_mode(m))
        win.display_group.addAction(a)
        disp_menu.addAction(a)
    win.act_disp_solid = win.display_group.actions()[0]
    win.act_disp_wire = win.display_group.actions()[1]
    win.act_disp_both = win.display_group.actions()[2]
    m_view.addSeparator()
    win.act_lang = QAction(tr("view_lang"), win)
    win.act_lang.triggered.connect(win.toggle_language)
    m_view.addAction(win.act_lang)

    m_tools = mb.addMenu(tr("menu_tools"))
    add(m_tools, tr("tools_validate"), win.validate_code)
    add(m_tools, tr("tools_format"), win.format_code)
    add(m_tools, tr("tools_clear"), win.console.clear)
    add(m_tools, tr("tools_geo"), win.geometry_info)

    m_examples = mb.addMenu(tr("menu_examples"))
    for fname, label_key in (("00_showcase.py", "ex_showcase"),
                             ("basic_objects.py", "ex_basic"),
                             ("low_poly_house.py", "ex_house"),
                             ("simple_tree.py", "ex_tree"),
                             ("small_village.py", "ex_village"),
                             ("procedural_rocks.py", "ex_rocks")):
        add(m_examples, tr(label_key),
            lambda checked=False, f=fname: win.load_example_file(win.example_path(f)))

    m_help = mb.addMenu(tr("menu_help"))
    add(m_help, tr("help_docs"), win.show_docs)
    add(m_help, tr("help_api"), win.show_api_ref)
    add(m_help, tr("help_shortcuts"), win.show_shortcuts)
    add(m_help, tr("help_about"), win.show_about)
    return mb


def update_menu_texts(win) -> None:
    """Update menu text in place (safer than rebuilding widgets after show)."""
    for attr, key in MENU_TEXT_KEYS.items():
        act = getattr(win, attr, None)
        if act is not None:
            act.setText(tr(key))
    disp_keys = ("disp_solid", "disp_wire", "disp_both")
    for attr, key in (("act_disp_solid", "disp_solid"), ("act_disp_wire", "disp_wire"),
                      ("act_disp_both", "disp_both")):
        act = getattr(win, attr, None)
        if act is not None:
            act.setText(tr(key))


def update_toolbar_texts(win) -> None:
    """Update toolbar button text in place."""
    for attr, key in TOOLBAR_TEXT_KEYS.items():
        btn = getattr(win, attr, None)
        if btn is None:
            continue
        if attr == "tb_run":
            btn.setText(tr("tb_running") if getattr(win, "_running", False) else tr("tb_run"))
        else:
            btn.setText(tr(key))
    combo = getattr(win, "display_combo", None)
    if combo is not None:
        for i, key in enumerate(("disp_solid", "disp_wire", "disp_both")):
            combo.setItemText(i, tr(key))
        combo.setToolTip(tr("view_display"))


MENU_TEXT_KEYS = {
    "act_new": "file_new", "act_open": "file_open", "act_save": "file_save",
    "act_save_as": "file_saveas", "act_import": "file_import",
    "act_export_glb": "file_export_glb", "act_export_opts": "file_export_opts",
    "act_export_obj": "file_export_obj", "act_export_stl": "file_export_stl",
    "act_undo": "edit_undo", "act_redo": "edit_redo", "act_cut": "edit_cut",
    "act_copy": "edit_copy", "act_paste": "edit_paste",
    "act_select_all": "edit_selectall", "act_view_editor": "view_editor",
    "act_view_objects": "view_objects", "act_view_console": "view_console",
    "act_grid": "view_grid", "act_axes": "view_axes", "act_lang": "view_lang",
}

TOOLBAR_TEXT_KEYS = {
    "tb_new": "tb_new", "tb_open": "tb_open", "tb_save": "tb_save",
    "tb_run": "tb_run", "tb_stop": "tb_stop", "tb_reset_cam": "tb_reset_cam",
    "tb_frame": "tb_frame", "tb_grid": "tb_grid", "tb_export": "tb_export",
}


def build_toolbar(win) -> QToolBar:
    from app.i18n import tr as _tr
    tb = QToolBar("Main", win)
    tb.setMovable(False)

    def btn(text, slot, shortcut=None, object_name=None, checkable=False):
        from PySide6.QtWidgets import QToolButton
        b = QToolButton()
        b.setText(text)
        if object_name:
            b.setObjectName(object_name)
        b.setCheckable(checkable)
        b.clicked.connect(slot)
        if shortcut:
            b.setShortcut(shortcut)
        tb.addWidget(b)
        return b

    win.tb_new = btn(_tr("tb_new"), win.new_project)
    win.tb_open = btn(_tr("tb_open"), win.open_project)
    win.tb_save = btn(_tr("tb_save"), win.save_project)
    tb.addSeparator()
    win.tb_run = btn(_tr("tb_run"), win.run_script, "F5", object_name="RunButton")
    win.tb_stop = btn(_tr("tb_stop"), win.stop_script)
    win.tb_stop.setEnabled(False)
    tb.addSeparator()
    win.tb_reset_cam = btn(_tr("tb_reset_cam"), win.viewport.reset_camera)
    win.tb_frame = btn(_tr("tb_frame"), lambda: win.viewport.frame_object(), "F")
    win.tb_grid = btn(_tr("tb_grid"), win.toggle_grid_btn, checkable=True)
    win.tb_grid.setChecked(win.viewport.show_grid)
    from PySide6.QtWidgets import QComboBox
    win.display_combo = QComboBox()
    win.display_combo.addItems([_tr("disp_solid"), _tr("disp_wire"), _tr("disp_both")])
    win.display_combo.setCurrentIndex({"solid": 0, "wireframe": 1, "both": 2}.get(win.viewport.wireframe, 0))
    win.display_combo.currentIndexChanged.connect(
        lambda i: win.set_display_mode(["solid", "wireframe", "both"][i]))
    win.display_combo.setToolTip(_tr("view_display"))
    tb.addWidget(win.display_combo)
    tb.addSeparator()
    win.tb_export = btn(_tr("tb_export"), win.export_glb)
    return tb
