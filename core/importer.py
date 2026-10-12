"""Import GLB/GLTF/OBJ/STL into a Scene. Import is decoupled from code execution."""

from __future__ import annotations

import os
import numpy as np
import trimesh

from .materials import parse_color
from .scene import Scene, SceneObject
from .validation import validate_mesh_arrays

SUPPORTED_EXTS = {".glb", ".gltf", ".obj", ".stl"}
MAX_FILE_MB = 100
MAX_VERTS = 500_000


def import_model(path: str) -> Scene:
    if not os.path.isfile(path):
        raise ValueError(f"File not found: {path}")
    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED_EXTS:
        raise ValueError(f"Unsupported format '{ext}'. Supported: GLB, GLTF, OBJ, STL.")
    size_mb = os.path.getsize(path) / (1024 * 1024)
    if size_mb > MAX_FILE_MB:
        raise ValueError(f"File too large ({size_mb:.1f} MB > {MAX_FILE_MB} MB).")
    try:
        loaded = trimesh.load(path, force="scene")
    except Exception as e:
        raise ValueError(f"Could not load {path}: {e}")
    scene = Scene(name=os.path.splitext(os.path.basename(path))[0])
    if isinstance(loaded, trimesh.Scene):
        geoms = list(loaded.geometry.items())
    else:
        geoms = [("mesh", loaded)]
    if not geoms:
        raise ValueError("File contains no geometry.")
    total = 0
    for i, (gname, geom) in enumerate(geoms):
        if not isinstance(geom, trimesh.Trimesh):
            continue
        verts = np.asarray(geom.vertices, dtype=np.float64)
        faces = np.asarray(geom.faces, dtype=np.int64)
        if verts.shape[0] == 0:
            continue
        total += verts.shape[0]
        if total > MAX_VERTS:
            raise ValueError("Model too complex (>500k vertices).")
        try:
            validate_mesh_arrays(verts, faces, str(gname))
        except Exception as e:
            raise ValueError(f"Invalid geometry in '{gname}': {e}")
        color = (0.7, 0.7, 0.75, 1.0)
        try:
            vis = getattr(geom, "visual", None)
            if vis is not None and getattr(vis, "vertex_colors", None) is not None:
                vc = np.asarray(vis.vertex_colors)
                if vc.size:
                    c = vc[0].astype(float)
                    if c.max() > 1.0:
                        c = c / 255.0
                    color = (float(c[0]), float(c[1]), float(c[2]), float(c[3]) if len(c) > 3 else 1.0)
        except Exception:
            pass
        base = os.path.splitext(os.path.basename(path))[0]
        oname = f"{base}_{gname}" if len(geoms) > 1 else base
        scene.objects.append(SceneObject(
            name=oname[:64], geom_type="imported",
            base_vertices=verts, base_faces=faces, color=color))
    if not scene.objects:
        raise ValueError("No supported mesh geometry found in file.")
    return scene
