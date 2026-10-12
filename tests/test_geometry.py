"""Geometry creation tests: cube/sphere valid, transforms, multi-object, invalid params."""
import numpy as np
import pytest

from core import geometry as G
from core.transforms import apply_transform
from core.validation import validate_mesh_arrays, GeometryError


def test_cube_valid():
    v, f = G.create_cube((1, 1, 1))
    validate_mesh_arrays(v, f, "cube")
    assert v.shape[1] == 3 and f.shape[1] == 3
    assert v.shape[0] == 8 and f.shape[0] == 12


def test_sphere_valid():
    v, f = G.create_sphere(1.0, 1)
    validate_mesh_arrays(v, f, "sphere")
    assert v.shape[0] > 10


def test_transforms_applied():
    v, f = G.create_cube((2, 2, 2))
    moved = apply_transform(v, (5, 0, 0), (0, 0, 0), (1, 1, 1))
    assert moved[:, 0].mean() == pytest.approx(5.0, abs=1e-6)
    scaled = apply_transform(v, (0, 0, 0), (0, 0, 0), (2, 1, 1))
    assert float(np.ptp(scaled[:, 0])) == pytest.approx(4.0, abs=1e-6)


def test_invalid_params():
    with pytest.raises(GeometryError):
        G.create_cube((0, 1, 1))
    with pytest.raises(GeometryError):
        G.create_sphere(-1)
    with pytest.raises(GeometryError):
        G.create_cylinder(0.5, 1.0, sections=2)
    with pytest.raises(GeometryError):
        G.create_torus(0.5, 0.75)
    with pytest.raises(GeometryError):
        G.create_ring(1.0, 0.5, 0.2)
