"""Native .py3d project format (versioned JSON). Never auto-executes code on open."""

from __future__ import annotations

import json
import os

from app import __version__ as APP_VERSION

PROJECT_EXT = ".py3d"
FORMAT_VERSION = 1


def new_project_dict(name="Untitled", code="") -> dict:
    return {
        "format": "py3d-project",
        "format_version": FORMAT_VERSION,
        "app_version": APP_VERSION,
        "project_name": name,
        "code": code,
        "scene_settings": {"background": [0.12, 0.14, 0.18]},
        "execution": {"timeout": 20.0},
        "viewport": {"grid": True, "axes": True, "wireframe": False},
    }


def save_project(path: str, data: dict) -> str:
    if not path.endswith(PROJECT_EXT):
        path += PROJECT_EXT
    data = dict(data)
    data["format"] = "py3d-project"
    data["format_version"] = FORMAT_VERSION
    data["app_version"] = APP_VERSION
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def load_project(path: str) -> dict:
    if not os.path.isfile(path):
        raise ValueError(f"Project file not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"Invalid project file: {e}")
    if not isinstance(data, dict) or data.get("format") != "py3d-project":
        raise ValueError("Not a Py3D Generator project file.")
    if int(data.get("format_version", 0)) > FORMAT_VERSION:
        raise ValueError("Project was saved with a newer app version. Please update.")
    data.setdefault("code", "")
    data.setdefault("project_name", os.path.splitext(os.path.basename(path))[0])
    return data
