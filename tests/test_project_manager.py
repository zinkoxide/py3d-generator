"""Project save/load tests + untrusted script is never auto-executed."""
import os

from core import project_manager as pm


def test_save_and_reopen(tmp_path):
    data = pm.new_project_dict(name="Demo", code='cube(name="A")\n')
    path = str(tmp_path / "demo.py3d")
    pm.save_project(path, data)
    assert os.path.isfile(path)
    loaded = pm.load_project(path)
    assert loaded["code"] == 'cube(name="A")\n'
    assert loaded["project_name"] == "Demo"


def test_untrusted_project_not_executed_on_load(tmp_path):
    # load_project must be pure data — it must not exec anything
    evil = 'import os; open("/tmp/py3d_pwned", "w").write("x")\n'
    data = pm.new_project_dict(name="Evil", code=evil)
    path = str(tmp_path / "evil.py3d")
    pm.save_project(path, data)
    if os.path.exists("/tmp/py3d_pwned"):
        os.unlink("/tmp/py3d_pwned")
    loaded = pm.load_project(path)
    assert loaded["code"] == evil
    assert not os.path.exists("/tmp/py3d_pwned")


def test_invalid_project_rejected(tmp_path):
    bad = tmp_path / "bad.py3d"
    bad.write_text("{ not json", encoding="utf-8")
    import pytest
    with pytest.raises(ValueError):
        pm.load_project(str(bad))
