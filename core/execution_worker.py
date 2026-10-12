"""Separate-process execution worker for user scripts.

Trust model (documented limitation):
- User code runs in a CHILD subprocess, not the GUI process, with a timeout,
  restricted builtins, and an import allow-list (math/random only).
- A subprocess alone is NOT a full security boundary: do not run untrusted
  scripts from unknown sources. The GUI never auto-executes project scripts.
- The worker returns a validated JSON scene; the GUI re-validates everything
  before rendering/exporting.

Usage:
    python -m core.execution_worker --source /tmp/script.py --output /tmp/scene.json
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import time
import traceback

ALLOWED_MODULES = {"math", "random"}


def _restricted_import(name, *args, **kwargs):
    base = str(name).split(".")[0]
    if base in ALLOWED_MODULES:
        return _real_import(name, *args, **kwargs)
    raise ImportError(f"Import of module {name!r} is not allowed (allowed: math, random)")


_real_import = __import__


def build_namespace():
    from . import modeling_api as api
    api._reset_builder()
    safe_builtins = {
        "print": print, "range": range, "len": len, "str": str, "int": int,
        "float": float, "bool": bool, "list": list, "dict": dict, "tuple": tuple,
        "set": set, "enumerate": enumerate, "zip": zip, "min": min, "max": max,
        "sum": sum, "abs": abs, "round": round, "sorted": sorted, "reversed": reversed,
        "isinstance": isinstance, "hasattr": hasattr, "getattr": getattr,
        "__import__": _restricted_import,
        "Exception": Exception, "ValueError": ValueError, "TypeError": TypeError,
        "RuntimeError": RuntimeError,
    }
    ns: dict = {"__builtins__": safe_builtins}
    for fn_name in api.PUBLIC_API:
        ns[fn_name] = getattr(api, fn_name)
    return ns, api


def execute_source(source: str, timeout_note: str = "") -> dict:
    started = time.time()
    ns, api = build_namespace()
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = stdout_buf, stderr_buf
    error = None
    try:
        code = compile(source, "<user_script>", "exec")
    except SyntaxError as e:
        error = {"line": e.lineno or 0, "message": f"SyntaxError: {e.msg} (line {e.lineno})"}
        sys.stdout, sys.stderr = old_out, old_err
        return {"success": False, "scene": None, "stdout": stdout_buf.getvalue(),
                "stderr": stderr_buf.getvalue(), "error": error,
                "duration": time.time() - started}
    try:
        exec(code, ns)
    except SystemExit as e:
        error = {"line": 0, "message": f"Script called sys.exit({e.code}) — not allowed."}
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        lineno = 0
        for fr in reversed(tb):
            if fr.filename == "<user_script>":
                lineno = fr.lineno or 0
                break
        error = {"line": lineno, "message": f"{type(e).__name__}: {e}" + (f" (line {lineno})" if lineno else "")}
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    duration = time.time() - started
    if error is not None:
        return {"success": False, "scene": None, "stdout": stdout_buf.getvalue(),
                "stderr": stderr_buf.getvalue() + stderr_buf.getvalue()[:0], "error": error,
                "duration": duration}
    # Serialize scene (cap sizes)
    scene = api._builder()
    if len(scene.objects) > api.MAX_OBJECTS:
        return {"success": False, "scene": None, "stdout": stdout_buf.getvalue(),
                "stderr": "", "error": {"line": 0, "message": "Too many objects generated."},
                "duration": duration}
    total_verts = sum(int(o.base_vertices.shape[0]) for o in scene.objects)
    if total_verts > 1_000_000:
        return {"success": False, "scene": None, "stdout": stdout_buf.getvalue(),
                "stderr": "", "error": {"line": 0, "message": "Geometry too complex (>1M vertices)."},
                "duration": duration}
    return {"success": True, "scene": scene.to_dict(), "stdout": stdout_buf.getvalue(),
            "stderr": "", "error": None, "duration": duration}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    try:
        with open(args.source, "r", encoding="utf-8") as f:
            source = f.read()
    except OSError as e:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump({"success": False, "scene": None, "stdout": "",
                       "stderr": "", "error": {"line": 0, "message": f"Cannot read source: {e}"},
                       "duration": 0.0}, f)
        return 1
    result = execute_source(source)
    try:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f)
    except OSError as e:
        print(f"Cannot write output: {e}", file=sys.stderr)
        return 1
    return 0 if result["success"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
