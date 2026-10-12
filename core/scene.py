"""Internal scene representation (UI process side + shared serialization)."""

from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np

from .transforms import apply_transform
from .validation import mesh_stats


@dataclass
class SceneObject:
    name: str
    geom_type: str = "cube"
    base_vertices: np.ndarray = field(default_factory=lambda: np.zeros((0, 3)))
    base_faces: np.ndarray = field(default_factory=lambda: np.zeros((0, 3), dtype=np.int64))
    location: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0)  # degrees
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0)
    color: tuple[float, float, float, float] = (0.3, 0.6, 1.0, 1.0)
    roughness: float = 0.6
    metallic: float = 0.0
    visible: bool = True
    locked: bool = False

    def world_vertices(self) -> np.ndarray:
        return apply_transform(
            np.asarray(self.base_vertices, dtype=np.float64),
            self.location, self.rotation, self.scale,
        )

    def world_faces(self) -> np.ndarray:
        return np.asarray(self.base_faces, dtype=np.int64)

    def stats(self) -> dict:
        try:
            return mesh_stats(self.world_vertices(), self.world_faces())
        except Exception:
            return {"vertices": 0, "faces": 0, "bbox_min": (0, 0, 0), "bbox_max": (0, 0, 0), "size": (0, 0, 0)}

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "geom_type": self.geom_type,
            "base_vertices": np.asarray(self.base_vertices, dtype=np.float64).tolist(),
            "base_faces": np.asarray(self.base_faces, dtype=np.int64).tolist(),
            "location": [float(x) for x in self.location],
            "rotation": [float(x) for x in self.rotation],
            "scale": [float(x) for x in self.scale],
            "color": [float(x) for x in self.color],
            "roughness": float(self.roughness),
            "metallic": float(self.metallic),
            "visible": bool(self.visible),
            "locked": bool(self.locked),
        }

    @staticmethod
    def from_dict(d: dict) -> "SceneObject":
        return SceneObject(
            name=str(d["name"]),
            geom_type=str(d.get("geom_type", "cube")),
            base_vertices=np.asarray(d.get("base_vertices", []), dtype=np.float64).reshape(-1, 3),
            base_faces=np.asarray(d.get("base_faces", []), dtype=np.int64).reshape(-1, 3),
            location=tuple(float(x) for x in d.get("location", (0, 0, 0))),
            rotation=tuple(float(x) for x in d.get("rotation", (0, 0, 0))),
            scale=tuple(float(x) for x in d.get("scale", (1, 1, 1))),
            color=tuple(float(x) for x in d.get("color", (0.3, 0.6, 1.0, 1.0))),
            roughness=float(d.get("roughness", 0.6)),
            metallic=float(d.get("metallic", 0.0)),
            visible=bool(d.get("visible", True)),
            locked=bool(d.get("locked", False)),
        )


@dataclass
class Scene:
    name: str = "Scene"
    background: tuple[float, float, float] = (0.12, 0.14, 0.18)
    objects: list[SceneObject] = field(default_factory=list)

    def get(self, name: str) -> SceneObject | None:
        for o in self.objects:
            if o.name == name:
                return o
        return None

    def names(self) -> list[str]:
        return [o.name for o in self.objects]

    def total_stats(self) -> dict:
        tv = sum(o.stats().get("vertices", 0) for o in self.objects if o.visible)
        tf = sum(o.stats().get("faces", 0) for o in self.objects if o.visible)
        return {"objects": len(self.objects), "vertices": tv, "faces": tf}

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "background": [float(x) for x in self.background],
            "objects": [o.to_dict() for o in self.objects],
        }

    @staticmethod
    def from_dict(d: dict) -> "Scene":
        sc = Scene(name=str(d.get("name", "Scene")))
        bg = d.get("background", (0.12, 0.14, 0.18))
        try:
            sc.background = (float(bg[0]), float(bg[1]), float(bg[2]))
        except Exception:
            pass
        for od in d.get("objects", []):
            try:
                sc.objects.append(SceneObject.from_dict(od))
            except Exception:
                continue
        return sc
