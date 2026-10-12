"""GLB export round-trip: export known model, reopen independently, verify geometry."""
import os

import trimesh

from core import modeling_api as api
from core.scene import Scene
from core.exporter import export_glb, ExportOptions


def _house_scene() -> Scene:
    api._reset_builder()
    api.cube(name="walls", size=(5, 3, 4), location=(0, 2.0, 0), color="#E6D5B8")
    api.pyramid(name="roof", size=(6, 2, 5), location=(0, 3.5, 0), color="#B83A2E")
    return api._builder()


def test_glb_export_and_reopen(tmp_path):
    scene = _house_scene()
    out = str(tmp_path / "house.glb")
    export_glb(scene, out, ExportOptions())
    assert os.path.isfile(out) and os.path.getsize(out) > 100
    # independent load (no app code involved)
    loaded = trimesh.load(out, force="scene")
    assert isinstance(loaded, trimesh.Scene)
    assert len(loaded.geometry) == 2


def test_export_preserves_dimensions_and_positions(tmp_path):
    scene = _house_scene()
    out = str(tmp_path / "house.glb")
    export_glb(scene, out, ExportOptions())
    loaded = trimesh.load(out, force="scene")
    bounds = loaded.bounding_box.bounds  # (2,3) min/max
    # walls span x in [-2.5, 2.5]; roof apex y = 3.5+2 = 5.5
    assert bounds[0][0] <= -2.4 and bounds[1][0] >= 2.4
    assert bounds[1][1] >= 5.4


def test_export_options_respected(tmp_path):
    scene = _house_scene()
    scene.objects[0].visible = False
    out1 = str(tmp_path / "nohidden.glb")
    export_glb(scene, out1, ExportOptions(include_hidden=False))
    l1 = trimesh.load(out1, force="scene")
    assert len(l1.geometry) == 1
    out2 = str(tmp_path / "withhidden.glb")
    export_glb(scene, out2, ExportOptions(include_hidden=True))
    l2 = trimesh.load(out2, force="scene")
    assert len(l2.geometry) == 2


def test_empty_scene_export_fails(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        export_glb(Scene(), str(tmp_path / "empty.glb"), ExportOptions())
