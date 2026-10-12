"""Scene validation tests."""
import numpy as np
import pytest

from core.validation import validate_mesh_arrays, GeometryError
from core.scene import Scene, SceneObject


def test_rejects_empty_and_nonfinite():
    with pytest.raises(GeometryError):
        validate_mesh_arrays(np.zeros((0, 3)), np.zeros((0, 3), dtype=int), "empty")
    bad = np.array([[np.nan, 0, 0], [1, 0, 0], [0, 1, 0]])
    with pytest.raises(GeometryError):
        validate_mesh_arrays(bad, np.array([[0, 1, 2]]), "nan")


def test_scene_stats_and_serialization_roundtrip():
    sc = Scene(name="S")
    sc.objects.append(SceneObject(
        name="C", geom_type="cube",
        base_vertices=np.array([[-0.5] * 3, [0.5] * 3], dtype=float),
        base_faces=np.array([[0, 0, 1]], dtype=np.int64)))
    d = sc.to_dict()
    sc2 = Scene.from_dict(d)
    assert sc2.names() == ["C"]
    assert sc2.total_stats()["objects"] == 1
