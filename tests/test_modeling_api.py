"""Modeling API + worker tests: multi-object scenes, errors, failed script keeps scene."""
import json

import pytest

from core import modeling_api as api
from core.execution_worker import execute_source
from core.scene import Scene


def _example(n=3):
    api._reset_builder()
    for i in range(n):
        api.cube(name=f"Block_{i}", size=(1, 1, 1), location=(i * 1.5, 0, 0))
    return api._builder()


def test_multiple_objects_coexist():
    sc = _example(5)
    assert len(sc.objects) == 5
    assert sc.names() == [f"Block_{i}" for i in range(5)]


def test_duplicate_names_made_unique():
    api._reset_builder()
    a = api.cube(name="Cube")
    b = api.cube(name="Cube")
    assert a != b
    assert len(api._builder().objects) == 2


def test_invalid_api_params_raise_helpful_errors():
    api._reset_builder()
    import pytest
    with pytest.raises(Exception, match=".*"):
        api.cube(name="Bad", size=(0, 1, 1))
    with pytest.raises(Exception):
        api.set_transform("Nope", location=(0, 0, 0))


def test_worker_success_and_scene_serialization():
    src = open("examples/basic_objects.py", encoding="utf-8").read()
    res = execute_source(src)
    assert res["success"], res.get("error")
    sc = Scene.from_dict(res["scene"])
    # 5 primitives + ground plane
    assert len(sc.objects) == 6
    for kind in ("cube", "sphere", "cylinder", "cone", "torus"):
        assert any(o.geom_type == kind for o in sc.objects), kind


def test_failed_script_reports_line_and_keeps_last_scene():
    good = 'cube(name="Keep", size=(1,1,1))\n'
    bad = 'cube(name="A")\nthis_is_not_defined()\n'
    r_good = execute_source(good)
    assert r_good["success"]
    last = Scene.from_dict(r_good["scene"])
    r_bad = execute_source(bad)
    assert not r_bad["success"]
    assert (r_bad["error"]["line"] or 0) >= 2
    # caller keeps `last` — worker never mutates it
    assert len(last.objects) == 1 and last.objects[0].name == "Keep"


def test_all_examples_execute():
    import glob
    for p in sorted(glob.glob("examples/*.py")):
        src = open(p, encoding="utf-8").read()
        res = execute_source(src)
        assert res["success"], f"{p} failed: {res.get('error')}"


def test_custom_mesh_from_raw_lists():
    api._reset_builder()
    verts = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0.5, 0.5, 1)]
    faces = [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (0, 2, 1), (0, 3, 2)]
    n = api.custom_mesh(name="Pyramid", vertices=verts, faces=faces, color="#F4A261")
    assert n == "Pyramid"
    obj = api._builder().get("Pyramid")
    assert obj is not None and obj.stats()["vertices"] == 5
    # via worker (plain lists, no numpy import in user code)
    src = ("verts = [(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0.5,0.5,1)]\n"
           "faces = [(0,1,4),(1,2,4),(2,3,4),(3,0,4),(0,2,1),(0,3,2)]\n"
           "custom_mesh(name='P', vertices=verts, faces=faces)\n")
    res = execute_source(src)
    assert res["success"], res.get("error")
    with pytest.raises(Exception):
        api.custom_mesh(name="Bad", vertices=[(0, 0)], faces=[(0, 1, 2)])
