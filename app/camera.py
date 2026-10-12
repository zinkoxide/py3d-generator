"""Orbit camera: yaw/pitch/distance/target with perspective matrices."""

from __future__ import annotations

import math
import numpy as np


class Camera:
    def __init__(self):
        self.target = np.array([0.0, 1.0, 0.0], dtype=np.float64)
        self.distance = 14.0
        self.yaw = 45.0    # degrees around Y
        self.pitch = 22.0  # degrees above horizon
        self.fov = 45.0
        self.near = 0.1
        self.far = 500.0

    def reset(self) -> None:
        self.__init__()

    def orbit(self, dx: float, dy: float) -> None:
        self.yaw -= dx * 0.4
        self.pitch += dy * 0.4
        self.pitch = max(-85.0, min(85.0, self.pitch))

    def pan(self, dx: float, dy: float) -> None:
        s = self.distance / 600.0
        yaw_r = math.radians(self.yaw)
        right = np.array([math.cos(yaw_r), 0.0, -math.sin(yaw_r)])
        up = np.array([0.0, 1.0, 0.0])
        # screen-right drag moves scene with cursor
        self.target -= right * dx * s
        self.target += up * dy * s

    def zoom(self, factor: float) -> None:
        self.distance = max(1.0, min(200.0, self.distance * factor))

    def position(self) -> np.ndarray:
        yr, pr = math.radians(self.yaw), math.radians(self.pitch)
        x = self.distance * math.cos(pr) * math.sin(yr)
        y = self.distance * math.sin(pr)
        z = self.distance * math.cos(pr) * math.cos(yr)
        return self.target + np.array([x, y, z])

    def view_matrix(self) -> np.ndarray:
        eye = self.position()
        center = self.target
        up = np.array([0.0, 1.0, 0.0])
        f = center - eye
        f = f / (np.linalg.norm(f) + 1e-12)
        s = np.cross(f, up)
        n = np.linalg.norm(s)
        s = s / (n + 1e-12) if n > 1e-9 else np.array([1.0, 0.0, 0.0])
        u = np.cross(s, f)
        M = np.eye(4)
        M[0, :3] = s
        M[1, :3] = u
        M[2, :3] = -f
        M[:3, 3] = -M[:3, :3] @ eye
        return M

    def proj_matrix(self, aspect: float) -> np.ndarray:
        f = 1.0 / math.tan(math.radians(self.fov) / 2.0)
        M = np.zeros((4, 4))
        M[0, 0] = f / aspect
        M[1, 1] = f
        M[2, 2] = (self.far + self.near) / (self.near - self.far)
        M[2, 3] = (2 * self.far * self.near) / (self.near - self.far)
        M[3, 2] = -1.0
        return M

    def frame_bbox(self, bmin: np.ndarray, bmax: np.ndarray) -> None:
        center = (np.asarray(bmin) + np.asarray(bmax)) / 2.0
        size = float(np.linalg.norm(np.asarray(bmax) - np.asarray(bmin)))
        self.target = center
        self.distance = max(3.0, min(200.0, size * 1.6 + 3.0))
