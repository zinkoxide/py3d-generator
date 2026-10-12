#!/usr/bin/env bash
# Launch Py3D Generator: activates venv, checks deps, starts the app.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
  echo "No virtual environment found at .venv/"
  echo "Create it with:"
  echo "  python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi
# shellcheck disable=SC1091
source .venv/bin/activate

MISSING="$(python -c "import importlib.util as u; print(' '.join(m for m in ['PySide6','numpy','trimesh','OpenGL'] if u.find_spec(m) is None))")"
if [ -n "$MISSING" ]; then
  echo "Missing dependencies: $MISSING"
  echo "Run: pip install -r requirements.txt"
  exit 1
fi

# System packages hint for Qt/OpenGL on Linux Mint / Ubuntu:
#   sudo apt install libgl1 libegl1 libxkbcommon0 libdbus-1-3

exec python main.py "$@"
