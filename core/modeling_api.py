"""Public modeling API injected into user scripts (runs inside worker subprocess).

Conventions:
- location/position: (x, y, z) in world units. Y is up.
- rotation: (rx, ry, rz) in DEGREES.
- scale: (sx, sy, sz) multipliers.
- color: '#RRGGBB' or (r,g,b)/(r,g,b,a).
"""

from __future__ import annotations

import math
import random

from . import geometry as G
from .materials import parse_color
from .scene import Scene, SceneObject
from .validation import GeometryError

MAX_OBJECTS = 500

_builder_scene: Scene | None = None


def _builder() -> Scene:
    global _builder_scene
    if _builder_scene is None:
        _builder_scene = Scene()
    return _builder_scene


def _reset_builder() -> Scene:
    global _builder_scene
    _builder_scene = Scene()
    return _builder_scene


def _unique_name(want: str) -> str:
    sc = _builder()
    existing = set(sc.names())
    if want not in existing:
        return want
    i = 1
    while f"{want}_{i}" in existing:
        i += 1
    return f"{want}_{i}"


def _check_limit():
    if len(_builder().objects) >= MAX_OBJECTS:
        raise GeometryError(f"Object limit reached ({MAX_OBJECTS}). Reduce object count.")


def _norm_vec3(value, field_name: str, default=(0.0, 0.0, 0.0)) -> tuple[float, float, float]:
    if value is None:
        return tuple(float(x) for x in default)
    try:
        vals = tuple(float(x) for x in value)
    except (TypeError, ValueError):
        raise GeometryError(f"'{field_name}' must be a 3-tuple of numbers, got {value!r}")
    if len(vals) != 3:
        raise GeometryError(f"'{field_name}' must have 3 components, got {value!r}")
    for x in vals:
        if not math.isfinite(x) or abs(x) > 10000:
            raise GeometryError(f"'{field_name}' component out of range: {value!r}")
    return vals


def _add_object(name, geom_type, verts, faces, location, rotation, scale, color, roughness=0.6, metallic=0.0) -> str:
    _check_limit()
    sc = _builder()
    final_name = _unique_name(str(name))
    loc = _norm_vec3(location, "location")
    rot = _norm_vec3(rotation, "rotation")
    scl = _norm_vec3(scale, "scale", default=(1.0, 1.0, 1.0))
    for x in scl:
        if x <= 0 or x > 1000:
            raise GeometryError(f"'scale' components must be in (0, 1000], got {scale!r}")
    rgba = parse_color(color)
    for v, label in ((roughness, "roughness"), (metallic, "metallic")):
        fv = float(v)
        if not (0.0 <= fv <= 1.0):
            raise GeometryError(f"'{label}' must be in [0,1], got {v!r}")
    import numpy as np
    obj = SceneObject(
        name=final_name, geom_type=geom_type,
        base_vertices=np.asarray(verts, dtype=float),
        base_faces=np.asarray(faces, dtype=np.int64),
        location=loc, rotation=rot, scale=scl,
        color=rgba, roughness=float(roughness), metallic=float(metallic),
    )
    sc.objects.append(obj)
    return final_name


# ---- Primitive creation ----

def cube(name="Cube", size=(1, 1, 1), location=(0, 0, 0), rotation=(0, 0, 0),
         scale=(1, 1, 1), color="#4C9AFF", roughness=0.6, metallic=0.0, position=None) -> str:
    """Create a box mesh. `position` is accepted as an alias of `location`."""
    if position is not None:
        location = position
    v, f = G.create_cube(size)
    return _add_object(name, "cube", v, f, location, rotation, scale, color, roughness, metallic)


def box(name="Box", size=(1, 1, 1), location=(0, 0, 0), rotation=(0, 0, 0),
        scale=(1, 1, 1), color="#4C9AFF", roughness=0.6, metallic=0.0, position=None) -> str:
    """Alias of cube() — creates a true box mesh."""
    return cube(name=name, size=size, location=location, rotation=rotation,
                scale=scale, color=color, roughness=roughness, metallic=metallic, position=position)


def sphere(name="Sphere", radius=1.0, location=(0, 0, 0), rotation=(0, 0, 0),
           scale=(1, 1, 1), subdivisions=2, color="#E76F51",
           roughness=0.6, metallic=0.0, position=None) -> str:
    if position is not None:
        location = position
    v, f = G.create_sphere(radius, subdivisions)
    return _add_object(name, "sphere", v, f, location, rotation, scale, color, roughness, metallic)


def icosphere(name="Icosphere", radius=1.0, location=(0, 0, 0), rotation=(0, 0, 0),
              scale=(1, 1, 1), subdivisions=2, color="#E76F51",
              roughness=0.6, metallic=0.0, position=None) -> str:
    """True triangulated sphere mesh (same generator as sphere)."""
    if position is not None:
        location = position
    v, f = G.create_icosphere(radius, subdivisions)
    return _add_object(name, "icosphere", v, f, location, rotation, scale, color, roughness, metallic)


def cylinder(name="Cylinder", radius=0.5, height=2.0, location=(0, 0, 0), rotation=(0, 0, 0),
             scale=(1, 1, 1), sections=32, color="#2A9D8F",
             roughness=0.6, metallic=0.0, position=None) -> str:
    if position is not None:
        location = position
    v, f = G.create_cylinder(radius, height, sections)
    return _add_object(name, "cylinder", v, f, location, rotation, scale, color, roughness, metallic)


def cone(name="Cone", radius=0.5, height=1.5, location=(0, 0, 0), rotation=(0, 0, 0),
         scale=(1, 1, 1), sections=32, color="#E9C46A",
         roughness=0.6, metallic=0.0, position=None) -> str:
    if position is not None:
        location = position
    v, f = G.create_cone(radius, height, sections)
    return _add_object(name, "cone", v, f, location, rotation, scale, color, roughness, metallic)


def plane(name="Plane", size=(10, 10), location=(0, 0, 0), rotation=(0, 0, 0),
          scale=(1, 1, 1), color="#808080", roughness=0.9, metallic=0.0, position=None) -> str:
    if position is not None:
        location = position
    v, f = G.create_plane(size)
    return _add_object(name, "plane", v, f, location, rotation, scale, color, roughness, metallic)


def torus(name="Torus", major_radius=1.0, minor_radius=0.25, location=(0, 0, 0),
          rotation=(0, 0, 0), scale=(1, 1, 1), color="#9B5DE5",
          roughness=0.6, metallic=0.0, position=None) -> str:
    if position is not None:
        location = position
    v, f = G.create_torus(major_radius, minor_radius)
    return _add_object(name, "torus", v, f, location, rotation, scale, color, roughness, metallic)


def capsule(name="Capsule", radius=0.5, height=2.0, location=(0, 0, 0), rotation=(0, 0, 0),
            scale=(1, 1, 1), color="#00BBF9", roughness=0.6, metallic=0.0, position=None) -> str:
    """True capsule mesh."""
    if position is not None:
        location = position
    v, f = G.create_capsule(radius, height)
    return _add_object(name, "capsule", v, f, location, rotation, scale, color, roughness, metallic)


def ring(name="Ring", inner_radius=0.5, outer_radius=1.0, height=0.2, location=(0, 0, 0),
         rotation=(0, 0, 0), scale=(1, 1, 1), sections=32, color="#F15BB5",
         roughness=0.6, metallic=0.0, position=None) -> str:
    """True flat annular solid mesh."""
    if position is not None:
        location = position
    v, f = G.create_ring(inner_radius, outer_radius, height, sections)
    return _add_object(name, "ring", v, f, location, rotation, scale, color, roughness, metallic)


def wedge(name="Wedge", size=(1, 1, 1), location=(0, 0, 0), rotation=(0, 0, 0),
          scale=(1, 1, 1), color="#80ED99", roughness=0.6, metallic=0.0, position=None) -> str:
    """True triangular-prism mesh (ramps)."""
    if position is not None:
        location = position
    v, f = G.create_wedge(size)
    return _add_object(name, "wedge", v, f, location, rotation, scale, color, roughness, metallic)


def pyramid(name="Pyramid", size=(1, 1, 1), location=(0, 0, 0), rotation=(0, 0, 0),
            scale=(1, 1, 1), color="#F4A261", roughness=0.6, metallic=0.0, position=None) -> str:
    """True square-pyramid mesh (house roofs)."""
    if position is not None:
        location = position
    v, f = G.create_pyramid(size)
    return _add_object(name, "pyramid", v, f, location, rotation, scale, color, roughness, metallic)


# ---- Custom meshes (bridge for code adapted from the internet) ----

def custom_mesh(name="Custom", vertices=None, faces=None, location=(0, 0, 0),
                rotation=(0, 0, 0), scale=(1, 1, 1), color="#4C9AFF",
                roughness=0.6, metallic=0.0, position=None) -> str:
    """Build a mesh from raw vertex/face lists.

    vertices: iterable of (x, y, z) triples (plain lists/tuples — no numpy needed).
    faces: iterable of (i, j, k) index triples into vertices.
    Useful when adapting algorithms from the internet that compute raw geometry:
    keep their math, then pass the resulting lists here instead of matplotlib.

    Example:
        verts = [(0,0,0), (1,0,0), (1,1,0), (0,1,0), (0.5,0.5,1)]
        faces = [(0,1,4), (1,2,4), (2,3,4), (3,0,4), (0,2,1), (0,3,2)]
        custom_mesh(name="Pyramid", vertices=verts, faces=faces, color="#F4A261")
    """
    import numpy as np
    from .validation import validate_mesh_arrays
    if position is not None:
        location = position
    if vertices is None or faces is None:
        raise GeometryError("custom_mesh: 'vertices' and 'faces' are both required")
    try:
        v = np.asarray(list(vertices), dtype=np.float64)
        f = np.asarray(list(faces), dtype=np.int64)
    except (TypeError, ValueError):
        raise GeometryError("custom_mesh: vertices must be (x,y,z) triples, faces (i,j,k) triples")
    if v.ndim != 2 or v.shape[1] != 3:
        raise GeometryError(f"custom_mesh: vertices must be an (N,3) list, got shape {v.shape}")
    if f.ndim != 2 or f.shape[1] != 3:
        raise GeometryError(f"custom_mesh: faces must be an (M,3) list, got shape {f.shape}")
    validate_mesh_arrays(v, f, str(name))
    return _add_object(name, "custom", v, f, location, rotation, scale, color, roughness, metallic)


# ---- Scene management ----

def clear_scene() -> None:
    _reset_builder()


def set_background(color) -> None:
    rgba = parse_color(color)
    _builder().background = (rgba[0], rgba[1], rgba[2])


def set_scene_name(name) -> None:
    _builder().name = str(name)


def get_objects() -> list[str]:
    return _builder().names()


def remove_object(name) -> bool:
    sc = _builder()
    for i, o in enumerate(sc.objects):
        if o.name == str(name):
            sc.objects.pop(i)
            return True
    raise GeometryError(f"remove_object: no object named {name!r}")


def duplicate_object(name, new_name=None) -> str:
    import copy
    sc = _builder()
    src = next((o for o in sc.objects if o.name == str(name)), None)
    if src is None:
        raise GeometryError(f"duplicate_object: no object named {name!r}")
    _check_limit()
    clone = copy.deepcopy(src)
    clone.name = _unique_name(str(new_name) if new_name else f"{src.name}_copy")
    sc.objects.append(clone)
    return clone.name


def set_transform(name, location=None, rotation=None, scale=None, position=None) -> None:
    sc = _builder()
    obj = next((o for o in sc.objects if o.name == str(name)), None)
    if obj is None:
        raise GeometryError(f"set_transform: no object named {name!r}")
    if position is not None:
        location = position
    if location is not None:
        obj.location = _norm_vec3(location, "location")
    if rotation is not None:
        obj.rotation = _norm_vec3(rotation, "rotation")
    if scale is not None:
        scl = _norm_vec3(scale, "scale", default=(1, 1, 1))
        for x in scl:
            if x <= 0 or x > 1000:
                raise GeometryError(f"'scale' components must be in (0,1000], got {scale!r}")
        obj.scale = scl


def set_material(name, color=None, roughness=None, metallic=None) -> None:
    sc = _builder()
    obj = next((o for o in sc.objects if o.name == str(name)), None)
    if obj is None:
        raise GeometryError(f"set_material: no object named {name!r}")
    if color is not None:
        obj.color = parse_color(color)
    if roughness is not None:
        r = float(roughness)
        if not (0.0 <= r <= 1.0):
            raise GeometryError(f"'roughness' must be in [0,1], got {roughness!r}")
        obj.roughness = r
    if metallic is not None:
        m = float(metallic)
        if not (0.0 <= m <= 1.0):
            raise GeometryError(f"'metallic' must be in [0,1], got {metallic!r}")
        obj.metallic = m


# ---- Procedural helpers ----

def grid_repeat(base_name="Cube", kind="cube", count=(3, 1, 3), spacing=(2.0, 0.0, 2.0),
                size=(1, 1, 1), palette=None, seed=0, **kwargs) -> list[str]:
    """Repeat an object kind in a 3D grid. Returns created names."""
    rng = random.Random(seed)
    nx, ny, nz = (int(count[0]), int(count[1]), int(count[2])) if not isinstance(count, int) else (int(count), 1, 1)
    sx, sy, sz = (float(spacing[0]), float(spacing[1]), float(spacing[2]))
    fn = {"cube": cube, "box": box, "sphere": sphere, "cylinder": cylinder,
          "cone": cone, "torus": torus, "capsule": capsule, "ring": ring,
          "wedge": wedge, "pyramid": pyramid, "plane": plane, "icosphere": icosphere}.get(kind, cube)
    names = []
    i = 0
    for ix in range(nx):
        for iy in range(ny):
            for iz in range(nz):
                color = kwargs.get("color", "#4C9AFF")
                if palette:
                    color = rng.choice(list(palette))
                loc = (ix * sx, iy * sy, iz * sz)
                kw = dict(kwargs)
                kw["color"] = color
                if kind in ("cube", "box", "wedge", "pyramid"):
                    kw.setdefault("size", size)
                n = fn(name=f"{base_name}_{i}", location=loc, **kw)
                names.append(n)
                i += 1
    return names


def random_scatter(kind="cube", count=10, bounds=((-5, 5), (0, 3), (-5, 5)),
                   palette=None, seed=0, **kwargs) -> list[str]:
    """Scatter objects randomly inside bounds ((xmin,xmax),(ymin,ymax),(zmin,zmax))."""
    rng = random.Random(seed)
    (xa, xb), (ya, yb), (za, zb) = bounds
    fn = {"cube": cube, "box": box, "sphere": sphere, "cylinder": cylinder,
          "cone": cone, "torus": torus, "capsule": capsule, "ring": ring,
          "wedge": wedge, "pyramid": pyramid, "plane": plane, "icosphere": icosphere}.get(kind, cube)
    names = []
    for i in range(int(count)):
        color = kwargs.get("color", "#4C9AFF")
        if palette:
            color = rng.choice(list(palette))
        loc = (rng.uniform(xa, xb), rng.uniform(ya, yb), rng.uniform(za, zb))
        kw = dict(kwargs)
        kw["color"] = color
        n = fn(name=f"{kind}_{i}", location=loc, **kw)
        names.append(n)
    return names


PUBLIC_API = [
    "cube", "box", "sphere", "icosphere", "cylinder", "cone", "plane",
    "torus", "capsule", "ring", "wedge", "pyramid",
    "custom_mesh",
    "clear_scene", "set_background", "set_scene_name", "get_objects",
    "remove_object", "duplicate_object", "set_transform", "set_material",
    "grid_repeat", "random_scatter",
]
