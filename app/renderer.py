"""CPU-side mesh cache: world vertices, computed normals, bounding boxes."""

from __future__ import annotations

import numpy as np


def compute_vertex_normals(verts: np.ndarray, faces: np.ndarray) -> np.ndarray:
    n = np.zeros_like(verts, dtype=np.float64)
    if verts.shape[0] == 0 or faces.shape[0] == 0:
        return n
    v0 = verts[faces[:, 0]]
    v1 = verts[faces[:, 1]]
    v2 = verts[faces[:, 2]]
    fn = np.cross(v1 - v0, v2 - v0)
    lens = np.linalg.norm(fn, axis=1, keepdims=True)
    lens[lens < 1e-12] = 1.0
    fn = fn / lens
    for i in range(3):
        np.add.at(n, faces[:, i], fn)
    lens = np.linalg.norm(n, axis=1, keepdims=True)
    lens[lens < 1e-12] = 1.0
    return n / lens


class CachedMesh:
    def __init__(self, vertices: np.ndarray, faces: np.ndarray):
        self.vertices = np.ascontiguousarray(np.asarray(vertices, dtype=np.float32))
        self.faces = np.ascontiguousarray(np.asarray(faces, dtype=np.uint32))
        nv = compute_vertex_normals(np.asarray(vertices, dtype=np.float64),
                                    np.asarray(faces, dtype=np.int64))
        self.normals = np.ascontiguousarray(nv.astype(np.float32))
        if self.vertices.shape[0]:
            self.bmin = self.vertices.min(axis=0)
            self.bmax = self.vertices.max(axis=0)
        else:
            self.bmin = np.zeros(3, dtype=np.float32)
            self.bmax = np.zeros(3, dtype=np.float32)
