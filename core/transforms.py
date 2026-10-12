"""Vector/matrix helpers. Rotations are in degrees at the public API level."""

from __future__ import annotations

import math
import numpy as np


def euler_to_matrix(rotation_deg: tuple[float, float, float]) -> np.ndarray:
    """XYZ euler (degrees) -> 3x3 rotation matrix."""
    rx, ry, rz = (math.radians(float(a)) for a in rotation_deg)
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], dtype=np.float64)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=np.float64)
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], dtype=np.float64)
    return Rz @ Ry @ Rx


def compose_matrix(location, rotation_deg, scale) -> np.ndarray:
    """Build 4x4 transform matrix from location/rotation(deg)/scale."""
    loc = np.asarray(location, dtype=np.float64).reshape(3)
    scl = np.asarray(scale, dtype=np.float64).reshape(3)
    R = euler_to_matrix(tuple(rotation_deg))
    M = np.eye(4, dtype=np.float64)
    M[:3, :3] = R * scl.reshape(1, 3)
    M[:3, 3] = loc
    return M


def apply_transform(vertices: np.ndarray, location, rotation_deg, scale) -> np.ndarray:
    """Apply scale -> rotate -> translate to (N,3) vertices."""
    v = np.asarray(vertices, dtype=np.float64)
    if v.size == 0:
        return v
    s = np.asarray(scale, dtype=np.float64).reshape(3)
    v = v * s.reshape(1, 3)
    R = euler_to_matrix(tuple(rotation_deg))
    v = v @ R.T
    t = np.asarray(location, dtype=np.float64).reshape(3)
    v = v + t.reshape(1, 3)
    return v
