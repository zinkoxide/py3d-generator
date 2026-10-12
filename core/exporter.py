"""GLB/OBJ/STL export using trimesh. Validates scene, verifies output file."""

from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np
import trimesh

from .scene import Scene
from .validation import validate_mesh_arrays


@dataclass
class ExportOptions:
    include_hidden: bool = False
    include_ground: bool = False  # ground plane is visual-only; only exported if user opts in
    apply_transforms: bool = True
    export_scale: float = 1.0
    validate: bool = True
    include_materials: bool = True  # colors/PBR factors (GLB); ignored by STL


def _scene_to_trimesh_scene(scene: Scene, opts: ExportOptions) -> trimesh.Scene:
    if opts.export_scale <= 0 or opts.export_scale > 1000:
        raise ValueError(f"Export scale must be in (0,1000], got {opts.export_scale}")
    tscene = trimesh.Scene()
    exported = 0
    for obj in scene.objects:
        if not obj.visible and not opts.include_hidden:
            continue
        is_ground = obj.geom_type == "plane" and obj.name.lower().startswith("ground")
        if is_ground and not opts.include_ground:
            continue
        try:
            if opts.apply_transforms:
                verts = obj.world_vertices() * float(opts.export_scale)
            else:
                verts = np.asarray(obj.base_vertices, dtype=np.float64) * float(opts.export_scale)
            faces = np.asarray(obj.base_faces, dtype=np.int64)
            if opts.validate:
                validate_mesh_arrays(verts, faces, obj.name)
        except Exception as e:
            raise ValueError(f"Object '{obj.name}' failed validation: {e}")
        if verts.shape[0] == 0 or faces.shape[0] == 0:
            continue
        color = np.array(obj.color, dtype=np.uint8 if False else np.float64)
        rgba = np.array([[int(round(c * 255)) for c in obj.color]], dtype=np.uint8)
        try:
            tm = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
            if opts.include_materials:
                if not tm.is_volume and tm.vertices.shape[0] > 0:
                    pass  # planes/rings are legitimately non-volumetric
                tm.visual = trimesh.visual.ColorVisuals(
                    vertex_colors=np.repeat(rgba, len(tm.vertices), axis=0))
                mat = trimesh.visual.material.PBRMaterial(
                    name=f"{obj.name}_mat",
                    baseColorFactor=[float(obj.color[0]), float(obj.color[1]),
                                     float(obj.color[2]), float(obj.color[3])],
                    metallicFactor=float(obj.metallic),
                    roughnessFactor=float(obj.roughness))
                tm.visual.material = mat
        except Exception as e:
            raise ValueError(f"Object '{obj.name}' could not be prepared for export: {e}")
        tscene.add_geometry(tm, node_name=obj.name, geom_name=obj.name)
        exported += 1
    if exported == 0:
        raise ValueError("Nothing to export: scene is empty (or everything is hidden/excluded).")
    return tscene


def export_glb(scene: Scene, path: str, opts: ExportOptions | None = None) -> str:
    opts = opts or ExportOptions()
    tscene = _scene_to_trimesh_scene(scene, opts)
    data = tscene.export(file_type="glb")
    if data is None or len(data) == 0:
        raise ValueError("Exporter produced empty output.")
    with open(path, "wb") as f:
        f.write(data)
    _verify_file(path)
    return path


def export_obj(scene: Scene, path: str, opts: ExportOptions | None = None) -> str:
    """OBJ does not preserve full PBR hierarchy; colors may be approximated.

    Trimesh exports a Scene to OBJ only when a single mesh or with limitations,
    so we concatenate visible meshes into one OBJ (names preserved in groups where possible).
    """
    opts = opts or ExportOptions()
    tscene = _scene_to_trimesh_scene(scene, opts)
    # Combine into single mesh for OBJ (documented limitation)
    combined = trimesh.util.concatenate([g for g in tscene.geometry.values()])
    combined.export(path)
    _verify_file(path)
    return path


def export_stl(scene: Scene, path: str, opts: ExportOptions | None = None) -> str:
    """STL keeps geometry only (no colors/hierarchy) — documented limitation."""
    opts = opts or ExportOptions()
    tscene = _scene_to_trimesh_scene(scene, opts)
    combined = trimesh.util.concatenate([g for g in tscene.geometry.values()])
    combined.export(path)
    _verify_file(path)
    return path


def _verify_file(path: str) -> None:
    if not os.path.isfile(path):
        raise ValueError(f"Export failed: file was not created: {path}")
    size = os.path.getsize(path)
    if size == 0:
        raise ValueError(f"Export failed: file is empty: {path}")
    if path.lower().endswith(".glb") and size < 100:
        raise ValueError(f"Export failed: GLB file suspiciously small ({size} bytes).")
