"""Interactive 3D viewport (QOpenGLWidget + PyOpenGL, fixed-function pipeline)."""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QWidget

from core.scene import Scene
from app.camera import Camera
from app.renderer import CachedMesh

try:
    from OpenGL.GL import (
        glClearColor, glClear, glEnable, glDisable, glViewport,
        glMatrixMode, glLoadMatrixd, glLoadIdentity,
        glBegin, glEnd, glVertex3f, glVertex3fv, glColor3f, glColor4f,
        glLineWidth, glPointSize, glPushMatrix, glPopMatrix,
        glTranslatef, glLightfv, glMaterialfv, glMaterialf,
        glNormal3fv, glNormalPointer, glVertexPointer, glDrawElements,
        glPolygonMode, glGetError,
        GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_DEPTH_TEST, GL_LIGHTING,
        GL_LIGHT0, GL_POSITION, GL_AMBIENT, GL_DIFFUSE, GL_SPECULAR,
        GL_COLOR_MATERIAL, GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE,
        GL_NORMALIZE, GL_PROJECTION, GL_MODELVIEW, GL_LINES, GL_QUADS,
        GL_TRIANGLES, GL_FRONT, GL_SHININESS, GL_EMISSION,
        GL_UNSIGNED_INT, GL_FLOAT, GL_DOUBLE, GL_VERTEX_ARRAY,
        GL_NORMAL_ARRAY, GL_FRONT_AND_BACK as _FAB, GL_FILL, GL_LINE,
        GL_BLEND, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
        glShadeModel, GL_SMOOTH, GL_FLAT,
    )
    _GL_OK = True
except Exception:
    _GL_OK = False

from app.i18n import tr


class Viewport(QOpenGLWidget):
    objectSelected = Signal(object)  # name or None
    glError = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = Scene()
        self.cache: dict[str, CachedMesh] = {}
        self.selected: str | None = None
        self.show_grid = True
        self.show_axes = True
        self.wireframe = "solid"  # solid | wireframe | both
        self.show_ground = True
        self.color_mode = "multi"     # multi | uniform | material
        self.uniform_color = (0.30, 0.60, 1.0, 1.0)
        self.lighting_mode = "basic"  # basic | soft | dramatic
        self.smooth = True
        self.color_mode = "multi"     # multi | uniform | material
        self.uniform_color = (0.30, 0.60, 1.0, 1.0)
        self.lighting_mode = "basic"  # basic | soft | dramatic
        self.smooth = True
        self.camera = Camera()
        self._last_pos: QPoint | None = None
        self._dragging = False
        self._drag_button = None
        self._moved = 0
        self._mvp: np.ndarray | None = None
        self._viewport_size = (1, 1)
        self._gl_failed: str | None = None
        if not _GL_OK:
            self._gl_failed = "PyOpenGL is not available."
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self._build_overlay()

    def _build_overlay(self):
        """Floating view controls in the top-right corner (like the reference UI)."""
        from PySide6.QtWidgets import QPushButton, QHBoxLayout
        from PySide6.QtCore import QSize
        self.overlay = QWidget(self)
        lay = QHBoxLayout(self.overlay)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(4)
        self.overlay.setStyleSheet("background: transparent;")
        specs = [
            ("⛶", "Frame all", lambda: self.frame_object(None)),
            ("⌖", "Frame selected", lambda: self.frame_object(self.selected)),
            ("⟳", "Reset camera", self.reset_camera),
            ("⤢", "Fullscreen viewport", self.toggle_fullscreen),
        ]
        for glyph, tip, slot in specs:
            b = QPushButton(glyph)
            b.setObjectName("OverlayButton")
            b.setToolTip(tip)
            b.setFixedSize(QSize(30, 26))
            b.clicked.connect(slot)
            lay.addWidget(b)
        self.overlay.resize(150, 34)

    def toggle_fullscreen(self):
        """Expand the viewport over the editor, or back."""
        parent = self.parentWidget()
        if parent is None:
            return
        if not getattr(self, "_fs_saved", None):
            self._fs_saved = self.geometry()
            parent.layout().removeWidget(self)
            self.setParent(None)
            window = self.window()
            window.layout().addWidget(self)
            self.show()
            self.raise_()
            self.setGeometry(window.rect())
        else:
            parent.layout().addWidget(self)
            self.setParent(parent)
            self.show()
            self.raise_()
            self.setGeometry(self._fs_saved)
            self._fs_saved = None
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "overlay"):
            self.overlay.move(max(0, self.width() - self.overlay.width() - 10), 10)

    # ---- scene ----
    def set_scene(self, scene: Scene) -> None:
        self.scene = scene
        self.cache = {}
        for o in scene.objects:
            try:
                self.cache[o.name] = CachedMesh(o.world_vertices(), o.world_faces())
            except Exception:
                continue
        if self.selected not in self.cache:
            self.selected = None
        self.update()

    def set_selected(self, name: str | None) -> None:
        self.selected = name
        self.update()

    def reset_camera(self) -> None:
        self.camera.reset()
        self.update()

    def frame_object(self, name: str | None = None) -> None:
        target = name or self.selected
        if target and target in self.cache:
            m = self.cache[target]
            self.camera.frame_bbox(m.bmin.astype(float), m.bmax.astype(float))
        else:
            # frame whole scene
            if not self.cache:
                self.camera.reset()
            else:
                allv = np.concatenate([m.vertices for m in self.cache.values()
                                       if m.vertices.shape[0] > 0], axis=0)
                if allv.shape[0]:
                    self.camera.frame_bbox(allv.min(axis=0).astype(float), allv.max(axis=0).astype(float))
        self.update()

    # ---- GL setup ----
    LIGHT_PRESETS = {
        "basic":    {"amb": 0.35, "dif": 0.90, "spc": 0.40, "pos": [0.6, 1.0, 0.8, 0.0]},
        "soft":     {"amb": 0.58, "dif": 0.62, "spc": 0.12, "pos": [0.3, 1.0, 0.5, 0.0]},
        "dramatic": {"amb": 0.10, "dif": 1.00, "spc": 0.85, "pos": [-0.5, 0.8, 0.6, 0.0]},
    }

    def apply_lighting(self):
        """Apply the selected lighting preset (cheap: a few light calls)."""
        if not _GL_OK:
            return
        p = self.LIGHT_PRESETS.get(self.lighting_mode, self.LIGHT_PRESETS["basic"])
        try:
            glLightfv(GL_LIGHT0, GL_POSITION, p["pos"])
            glLightfv(GL_LIGHT0, GL_AMBIENT, [p["amb"], p["amb"], p["amb"] * 1.1, 1.0])
            glLightfv(GL_LIGHT0, GL_DIFFUSE, [p["dif"], p["dif"], p["dif"], 1.0])
            glLightfv(GL_LIGHT0, GL_SPECULAR, [p["spc"], p["spc"], p["spc"], 1.0])
        except Exception as e:
            self.glError.emit(f"Lighting error: {e}")

    def set_color_mode(self, mode: str, uniform=None):
        if mode in ("multi", "uniform", "material"):
            self.color_mode = mode
        if uniform is not None:
            self.uniform_color = tuple(float(x) for x in uniform)
        self.update()

    def set_lighting(self, mode: str):
        self.lighting_mode = mode if mode in self.LIGHT_PRESETS else "basic"
        self.apply_lighting()
        self.update()

    def set_smooth(self, smooth: bool):
        self.smooth = bool(smooth)
        self.update()

    def _display_color(self, obj):
        """Color used for drawing, per the current color mode."""
        if self.color_mode == "uniform":
            return self.uniform_color
        if self.color_mode == "material":
            # grayscale driven by metallic/roughness so materials read differently
            v = 0.25 + 0.55 * (1.0 - float(obj.metallic)) * (1.0 - 0.4 * float(obj.roughness))
            return (v, v, v * 1.05, 1.0)
        return obj.color

    def initializeGL(self):
        if not _GL_OK:
            self.glError.emit(self._gl_failed or "OpenGL unavailable")
            return
        try:
            bg = self.scene.background
            glClearColor(bg[0], bg[1], bg[2], 1.0)
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_LIGHTING)
            glEnable(GL_LIGHT0)
            glEnable(GL_COLOR_MATERIAL)
            glEnable(GL_NORMALIZE)
            self.apply_lighting()
        except Exception as e:
            self._gl_failed = f"Graphics initialization failed: {e}"
            self.glError.emit(self._gl_failed)

    def resizeGL(self, w: int, h: int):
        if not _GL_OK:
            return
        w = max(1, w)
        h = max(1, h)
        self._viewport_size = (w, h)
        glViewport(0, 0, w, h)

    def paintGL(self):
        if not _GL_OK:
            return
        try:
            bg = self.scene.background
            glClearColor(bg[0], bg[1], bg[2], 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            w, h = self._viewport_size
            aspect = w / max(1, h)
            proj = self.camera.proj_matrix(aspect)
            view = self.camera.view_matrix()
            self._mvp = proj @ view
            # load matrices (column-major for GL)
            glMatrixMode(GL_PROJECTION)
            glLoadMatrixd(proj.T.reshape(-1))
            glMatrixMode(GL_MODELVIEW)
            glLoadMatrixd(view.T.reshape(-1))

            if self.show_ground:
                self._draw_ground()
            if self.show_grid:
                self._draw_grid()
            if self.show_axes:
                self._draw_axes()
            self._draw_objects()
        except Exception as e:
            self.glError.emit(f"Render error: {e}")

        # empty-state overlay handled in paintEvent via QPainter
    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.cache:
            p = QPainter(self)
            p.setPen(QColor("#9fb0c9"))
            p.setFont(QFont("Segoe UI", 11))
            p.drawText(self.rect(), Qt.AlignCenter, tr("viewport_empty"))
            p.end()
        if hasattr(self, "overlay"):
            self.overlay.raise_()

    # ---- drawing ----
    def _draw_ground(self):
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        try:
            from OpenGL.GL import glBlendFunc
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        except Exception:
            pass
        glColor4f(0.35, 0.42, 0.5, 0.35)
        glBegin(GL_QUADS)
        S = 30.0
        glVertex3f(-S, -0.01, -S)
        glVertex3f(S, -0.01, -S)
        glVertex3f(S, -0.01, S)
        glVertex3f(-S, -0.01, S)
        glEnd()
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

    def _draw_grid(self):
        glDisable(GL_LIGHTING)
        glColor3f(0.30, 0.36, 0.46)
        glLineWidth(1.0)
        glBegin(GL_LINES)
        for i in range(-10, 11):
            glVertex3f(float(i), 0.0, -10.0)
            glVertex3f(float(i), 0.0, 10.0)
            glVertex3f(-10.0, 0.0, float(i))
            glVertex3f(10.0, 0.0, float(i))
        glEnd()
        glEnable(GL_LIGHTING)

    def _draw_axes(self):
        glDisable(GL_LIGHTING)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glColor3f(1.0, 0.25, 0.25)
        glVertex3f(0, 0, 0); glVertex3f(2.5, 0, 0)
        glColor3f(0.25, 1.0, 0.35)
        glVertex3f(0, 0, 0); glVertex3f(0, 2.5, 0)
        glColor3f(0.3, 0.55, 1.0)
        glVertex3f(0, 0, 0); glVertex3f(0, 0, 2.5)
        glEnd()
        glEnable(GL_LIGHTING)

    def _draw_objects(self):
        from OpenGL.GL import glEnableClientState, glDisableClientState, glColorMaterial
        for obj in self.scene.objects:
            if not obj.visible:
                continue
            mesh = self.cache.get(obj.name)
            if mesh is None or mesh.vertices.shape[0] == 0:
                continue
            r, g, b, a = self._display_color(obj)
            is_sel = (obj.name == self.selected)
            glColor4f(r, g, b, a)
            try:
                glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [r, g, b, 1.0])
                glMaterialf(GL_FRONT, GL_SHININESS, float(20 + 60 * (1 - obj.roughness)))
                glMaterialfv(GL_FRONT, GL_EMISSION, [0.25, 0.2, 0.0, 1.0] if is_sel else [0, 0, 0, 1.0])
            except Exception:
                pass
            mode = self.wireframe
            if mode == "wireframe":
                glDisable(GL_LIGHTING)
                self._draw_mesh_wire(mesh)
                glEnable(GL_LIGHTING)
            else:
                self._draw_mesh_solid(mesh)
                if mode == "both" or is_sel:
                    glDisable(GL_LIGHTING)
                    if is_sel:
                        glColor3f(1.0, 0.8, 0.2)
                        glLineWidth(2.0)
                    self._draw_mesh_wire(mesh)
                    glLineWidth(1.0)
                    glEnable(GL_LIGHTING)
            try:
                glMaterialfv(GL_FRONT, GL_EMISSION, [0, 0, 0, 1.0])
            except Exception:
                pass
            if is_sel:
                self._draw_bbox(mesh)

    def _draw_mesh_solid(self, mesh: CachedMesh):
        from OpenGL.GL import glEnableClientState as _en, glDisableClientState as _dis
        try:
            glShadeModel(GL_SMOOTH if self.smooth else GL_FLAT)
        except Exception:
            pass
        _en(GL_VERTEX_ARRAY)
        _en(GL_NORMAL_ARRAY)
        try:
            glVertexPointer(3, GL_FLOAT, 0, mesh.vertices)
            glNormalPointer(GL_FLOAT, 0, mesh.normals)
            glDrawElements(GL_TRIANGLES, mesh.faces.size, GL_UNSIGNED_INT, mesh.faces)
        finally:
            _dis(GL_VERTEX_ARRAY)
            _dis(GL_NORMAL_ARRAY)

    def _draw_mesh_wire(self, mesh: CachedMesh):
        from OpenGL.GL import glBegin as _b, glEnd as _e, GL_LINES as _L
        # draw triangle edges via vertex array is complex; use polygon LINE mode re-draw
        from OpenGL.GL import glPolygonMode as _pm
        _pm(GL_FRONT_AND_BACK, GL_LINE)
        self._draw_mesh_solid(mesh)
        _pm(GL_FRONT_AND_BACK, GL_FILL)

    def _draw_bbox(self, mesh: CachedMesh):
        glDisable(GL_LIGHTING)
        glColor3f(1.0, 0.8, 0.2)
        glLineWidth(1.5)
        mn, mx = mesh.bmin, mesh.bmax
        corners = [(x, y, z) for x in (mn[0], mx[0]) for y in (mn[1], mx[1]) for z in (mn[2], mx[2])]
        edges = [(0, 1), (0, 2), (1, 3), (2, 3), (4, 5), (4, 6), (5, 7), (6, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
        glBegin(GL_LINES)
        for a, b in edges:
            glVertex3fv(corners[a])
            glVertex3fv(corners[b])
        glEnd()
        glEnable(GL_LIGHTING)
        glLineWidth(1.0)

    # ---- interaction ----
    def mousePressEvent(self, event):
        self._last_pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        self._drag_button = event.button()
        self._dragging = True
        self._moved = 0
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        if self._dragging and self._last_pos is not None:
            dx = pos.x() - self._last_pos.x()
            dy = pos.y() - self._last_pos.y()
            self._moved += abs(dx) + abs(dy)
            mods = event.modifiers()
            if self._drag_button == Qt.MiddleButton or self._drag_button == Qt.RightButton or (mods & Qt.ShiftModifier):
                self.camera.pan(dx, dy)
            else:
                self.camera.orbit(dx, dy)
            self.update()
        self._last_pos = pos
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging and self._moved < 6 and event.button() == Qt.LeftButton:
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            self._pick(pos.x(), pos.y())
        self._dragging = False
        self._drag_button = None
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self.camera.zoom(0.9 if delta > 0 else 1.1)
        self.update()

    def _pick(self, x: int, y: int):
        if self._mvp is None or not self.cache:
            self.objectSelected.emit(None)
            return
        w, h = self._viewport_size
        best, best_d = None, 40.0
        for name, mesh in self.cache.items():
            obj = next((o for o in self.scene.objects if o.name == name), None)
            if obj is None or not obj.visible:
                continue
            c = ((mesh.bmin + mesh.bmax) / 2.0).astype(float)
            v = self._mvp @ np.array([c[0], c[1], c[2], 1.0])
            if abs(v[3]) < 1e-9:
                continue
            ndc = v[:3] / v[3]
            sx = (ndc[0] * 0.5 + 0.5) * w
            sy = (1.0 - (ndc[1] * 0.5 + 0.5)) * h
            d = ((sx - x) ** 2 + (sy - y) ** 2) ** 0.5
            if d < best_d:
                best, best_d = name, d
        self.selected = best
        self.objectSelected.emit(best)
        self.update()
