"""Mesh validation utilities."""

from __future__ import annotations

import numpy as np


class GeometryError(ValueError):
    pass


def validate_mesh_arrays(vertices: np.ndarray, faces: np.ndarray, name: str = "mesh") -> None:
    if vertices is None or faces is None:
        raise GeometryError(f"{name}: missing vertices or faces")
    v = np.asarray(vertices)
    f = np.asarray(faces)
    if v.size == 0 or f.size == 0:
        raise GeometryError(f"{name}: empty geometry (no vertices/faces)")
    if v.ndim != 2 or v.shape[1] != 3:
        raise GeometryError(f"{name}: vertices must be (N,3), got shape {v.shape}")
    if f.ndim != 2 or f.shape[1] != 3:
        raise GeometryError(f"{name}: faces must be (M,3), got shape {f.shape}")
    if not np.all(np.isfinite(v)):
        raise GeometryError(f"{name}: vertices contain NaN or infinite values")
    if v.shape[0] > 500_000:
        raise GeometryError(f"{name}: too many vertices ({v.shape[0]} > 500000)")
    if f.shape[0] > 1_000_000:
        raise GeometryError(f"{name}: too many faces ({f.shape[0]} > 1000000)")
    if f.min() < 0 or f.max() >= v.shape[0]:
        raise GeometryError(f"{name}: face indices out of range")
    # degenerate triangles
    v0 = v[f[:, 0]]
    v1 = v[f[:, 1]]
    v2 = v[f[:, 2]]
    cross = np.cross(v1 - v0, v2 - v0)
    area2 = np.linalg.norm(cross, axis=1)
    if np.all(area2 < 1e-12):
        raise GeometryError(f"{name}: all triangles are degenerate")


def mesh_stats(vertices: np.ndarray, faces: np.ndarray) -> dict:
    v = np.asarray(vertices, dtype=np.float64)
    f = np.asarray(faces)
    if v.size == 0:
        return {"vertices": 0, "faces": 0, "bbox_min": (0, 0, 0), "bbox_max": (0, 0, 0), "size": (0, 0, 0)}
    mn = v.min(axis=0)
    mx = v.max(axis=0)
    return {
        "vertices": int(v.shape[0]),
        "faces": int(f.shape[0]),
        "bbox_min": (float(mn[0]), float(mn[1]), float(mn[2])),
        "bbox_max": (float(mx[0]), float(mx[1]), float(mx[2])),
        "size": (float(mx[0] - mn[0]), float(mx[1] - mn[1]), float(mx[2] - mn[2])),
    }
