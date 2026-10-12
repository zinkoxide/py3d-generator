"""Geometry engine: builds trimesh meshes, validates inputs, applies transforms.

All public create_* functions return (vertices, faces) as float64/int64 ndarrays
in LOCAL space (centered at origin). The Scene layer bakes location/rotation/scale.
"""

from __future__ import annotations

import math
import numpy as np
import trimesh

from .validation import GeometryError, validate_mesh_arrays


def _as_mesh(vertices, faces) -> tuple[np.ndarray, np.ndarray]:
    v = np.asarray(vertices, dtype=np.float64)
    f = np.asarray(faces, dtype=np.int64)
    return v, f


def _from_trimesh(tm: trimesh.Trimesh, name: str) -> tuple[np.ndarray, np.ndarray]:
    if tm is None or len(tm.vertices) == 0 or len(tm.faces) == 0:
        raise GeometryError(f"{name}: generated empty geometry")
    v, f = _as_mesh(tm.vertices, tm.faces)
    validate_mesh_arrays(v, f, name)
    return v, f


def _check_positive(name: str, **kwargs) -> None:
    for k, val in kwargs.items():
        try:
            fval = float(val)
        except (TypeError, ValueError):
            raise GeometryError(f"{name}: '{k}' must be a number, got {val!r}")
        if not math.isfinite(fval) or fval <= 0:
            raise GeometryError(f"{name}: '{k}' must be a positive finite number, got {val!r}")


def _check_size_tuple(size, dims: int, name: str) -> tuple:
    if isinstance(size, (int, float)):
        vals = tuple([float(size)] * dims)
    else:
        try:
            vals = tuple(float(x) for x in size)
        except (TypeError, ValueError):
            raise GeometryError(f"{name}: 'size' must be a number or tuple, got {size!r}")
        if len(vals) != dims:
            raise GeometryError(f"{name}: 'size' must have {dims} components, got {size!r}")
    for x in vals:
        if not math.isfinite(x) or x <= 0:
            raise GeometryError(f"{name}: size components must be positive, got {size!r}")
        if x > 1000:
            raise GeometryError(f"{name}: size component too large ({x} > 1000)")
    return vals


def create_cube(size=(1, 1, 1)) -> tuple[np.ndarray, np.ndarray]:
    sx, sy, sz = _check_size_tuple(size, 3, "cube")
    tm = trimesh.creation.box(extents=(sx, sy, sz))
    return _from_trimesh(tm, "cube")


def create_sphere(radius=1.0, subdivisions=2) -> tuple[np.ndarray, np.ndarray]:
    _check_positive("sphere", radius=radius)
    subdivisions = int(subdivisions)
    if not (0 <= subdivisions <= 5):
        raise GeometryError(f"sphere: subdivisions must be 0..5, got {subdivisions!r}")
    tm = trimesh.creation.icosphere(radius=float(radius), subdivisions=subdivisions)
    return _from_trimesh(tm, "sphere")


def create_icosphere(radius=1.0, subdivisions=2) -> tuple[np.ndarray, np.ndarray]:
    return create_sphere(radius=radius, subdivisions=subdivisions)


def create_cylinder(radius=0.5, height=2.0, sections=32) -> tuple[np.ndarray, np.ndarray]:
    _check_positive("cylinder", radius=radius, height=height)
    sections = int(sections)
    if not (3 <= sections <= 256):
        raise GeometryError(f"cylinder: sections must be 3..256, got {sections!r}")
    tm = trimesh.creation.cylinder(radius=float(radius), height=float(height), sections=sections)
    return _from_trimesh(tm, "cylinder")


def create_cone(radius=0.5, height=1.5, sections=32) -> tuple[np.ndarray, np.ndarray]:
    _check_positive("cone", radius=radius, height=height)
    sections = int(sections)
    if not (3 <= sections <= 256):
        raise GeometryError(f"cone: sections must be 3..256, got {sections!r}")
    tm = trimesh.creation.cone(radius=float(radius), height=float(height), sections=sections)
    return _from_trimesh(tm, "cone")


def create_plane(size=(10, 10)) -> tuple[np.ndarray, np.ndarray]:
    sx, sy = _check_size_tuple(size, 2, "plane")
    # Plane in XZ ground orientation (normal +Y) to match viewport ground convention.
    v = np.array([
        [-sx / 2, 0, -sy / 2],
        [sx / 2, 0, -sy / 2],
        [sx / 2, 0, sy / 2],
        [-sx / 2, 0, sy / 2],
    ], dtype=np.float64)
    f = np.array([[0, 2, 1], [0, 3, 2]], dtype=np.int64)
    validate_mesh_arrays(v, f, "plane")
    return v, f


def create_torus(major_radius=1.0, minor_radius=0.25, major_sections=32, minor_sections=16) -> tuple[np.ndarray, np.ndarray]:
    _check_positive("torus", major_radius=major_radius, minor_radius=minor_radius)
    if float(minor_radius) >= float(major_radius):
        raise GeometryError(f"torus: minor_radius ({minor_radius}) must be < major_radius ({major_radius})")
    ms = int(major_sections)
    ns = int(minor_sections)
    if not (3 <= ms <= 128 and 3 <= ns <= 64):
        raise GeometryError("torus: section counts out of range (major 3..128, minor 3..64)")
    tm = trimesh.creation.torus(major_radius=float(major_radius), minor_radius=float(minor_radius))
    return _from_trimesh(tm, "torus")


def create_capsule(radius=0.5, height=2.0, sections=16) -> tuple[np.ndarray, np.ndarray]:
    _check_positive("capsule", radius=radius, height=height)
    sections = int(sections)
    if not (4 <= sections <= 64):
        raise GeometryError(f"capsule: sections must be 4..64, got {sections!r}")
    try:
        tm = trimesh.creation.capsule(radius=float(radius), height=float(height))
    except Exception:
        # Fallback: cylinder + two spheres manually
        cyl = trimesh.creation.cylinder(radius=float(radius), height=float(height), sections=sections)
        s1 = trimesh.creation.icosphere(radius=float(radius), subdivisions=2)
        s1.apply_translation((0, 0, float(height) / 2))
        s2 = trimesh.creation.icosphere(radius=float(radius), subdivisions=2)
        s2.apply_translation((0, 0, -float(height) / 2))
        tm = trimesh.util.concatenate((cyl, s1, s2))
    return _from_trimesh(tm, "capsule")


def create_ring(inner_radius=0.5, outer_radius=1.0, height=0.2, sections=32) -> tuple[np.ndarray, np.ndarray]:
    _check_positive("ring", inner_radius=inner_radius, outer_radius=outer_radius, height=height)
    if float(inner_radius) >= float(outer_radius):
        raise GeometryError("ring: inner_radius must be < outer_radius")
    sections = int(sections)
    if not (3 <= sections <= 256):
        raise GeometryError(f"ring: sections must be 3..256, got {sections!r}")
    ir, orr, h = float(inner_radius), float(outer_radius), float(height)
    angles = np.linspace(0, 2 * math.pi, sections, endpoint=False)
    verts = []
    for r in (ir, orr):
        for y in (-h / 2, h / 2):
            for a in angles:
                verts.append([r * math.cos(a), y, r * math.sin(a)])
    verts = np.array(verts, dtype=np.float64)
    n = sections
    faces = []
    # top/bottom annulus + inner/outer walls
    base_bot_in, base_top_in = 0, n
    base_bot_out, base_top_out = 2 * n, 3 * n
    for i in range(n):
        j = (i + 1) % n
        faces.append([base_top_in + i, base_top_out + i, base_top_out + j])
        faces.append([base_top_in + i, base_top_out + j, base_top_in + j])
        faces.append([base_bot_in + i, base_bot_out + j, base_bot_out + i])
        faces.append([base_bot_in + i, base_bot_in + j, base_bot_out + j])
        faces.append([base_bot_in + i, base_top_in + j, base_top_in + i])
        faces.append([base_bot_in + i, base_bot_out + i, base_top_in + j])
        faces.append([base_bot_out + i, base_top_out + i, base_top_out + j])
        faces.append([base_bot_out + i, base_top_out + j, base_bot_out + j])
    faces = np.array(faces, dtype=np.int64)
    validate_mesh_arrays(verts, faces, "ring")
    return verts, faces


def create_wedge(size=(1, 1, 1)) -> tuple[np.ndarray, np.ndarray]:
    """Triangular-prism wedge (useful for ramps)."""
    sx, sy, sz = _check_size_tuple(size, 3, "wedge")
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    v = np.array([
        [-hx, -hy, -hz], [hx, -hy, -hz], [hx, -hy, hz], [-hx, -hy, hz],
        [-hx, hy, -hz], [-hx, hy, hz],
    ], dtype=np.float64)
    f = np.array([
        [0, 1, 4], [0, 3, 2], [0, 2, 1], [3, 0, 4], [3, 4, 5],
        [1, 2, 5], [1, 5, 4], [2, 3, 5],
    ], dtype=np.int64)
    validate_mesh_arrays(v, f, "wedge")
    return v, f


def create_pyramid(size=(1, 1, 1)) -> tuple[np.ndarray, np.ndarray]:
    """Square pyramid with base in XZ plane, apex at +Y."""
    sx, sy, sz = _check_size_tuple(size, 3, "pyramid")
    hx, hz = sx / 2, sz / 2
    v = np.array([
        [-hx, 0, -hz], [hx, 0, -hz], [hx, 0, hz], [-hx, 0, hz],
        [0, float(sy), 0],
    ], dtype=np.float64)
    f = np.array([
        [0, 2, 1], [0, 3, 2],
        [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4],
    ], dtype=np.int64)
    validate_mesh_arrays(v, f, "pyramid")
    return v, f


ALIAS_INFO = {
    "box": "alias of cube (true mesh)",
    "icosphere": "true mesh (triangulated sphere)",
    "capsule": "true mesh",
    "ring": "true mesh (flat annulus solid)",
    "wedge": "true mesh (triangular prism)",
    "pyramid": "true mesh (square pyramid)",
    "torus": "true mesh",
    "plane": "true mesh (two triangles)",
}
