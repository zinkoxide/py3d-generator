# Py3D Generator — Code-Based 3D Model Creator

Standalone desktop app (Linux Mint compatible) to create, preview, edit, and export
3D models with simple Python code. No Blender or Godot required.

## Features
- UI shell modeled after the reference design: left nav sidebar (Editor/Projects/Examples/Settings/About) with a clickable **Available Functions** list (inserts a snippet at the cursor), a bordered code editor tab (`+` button), a titled 3D preview card, and right-hand cards for **Display Settings**, **Elements**, **Export Model** and **Properties**
- Display settings are live: color mode (multi / single / by material), lighting (basic / soft / dramatic), grid, axes, smooth shading
- Python code editor (highlighting, line numbers, completion, find/replace, error lines)
- Primitives: cube/box, sphere/icosphere, cylinder, cone, plane, torus, capsule, ring, wedge, pyramid
- `custom_mesh(vertices, faces)` for raw vertex lists (adapting internet algorithms without numpy/matplotlib)
- Scene API: clear/remove/duplicate/transform/material + `grid_repeat`, `random_scatter` (seeded)
- Interactive PyOpenGL viewport: orbit/pan/zoom, grid, axes, ground, selection, solid/wireframe/solid+wireframe
- Object hierarchy + properties (transforms/materials update viewport immediately)
- Out-of-process execution with timeout + Stop button; errors show line numbers
- Native `.py3d` projects (JSON, versioned; never auto-run code on open)
- Examples menu (one click loads any of the 5 examples into the editor) + Copy All Code (Ctrl+Shift+C)
- GLB export with options (verified round-trip), plus OBJ/STL; basic GLB/GLTF/OBJ/STL import
- Undo/redo for object edits (script execution replaces scene and resets undo — documented)
- EN/AR UI strings with live switching (View → Switch Language; menus/toolbar/tabs/headers translate instantly, RTL layout in Arabic)

## Trust & safety model
User scripts run in a **child subprocess** with restricted builtins and an import
allow-list (`math`, `random` only), plus object-count/vertex/time limits. A subprocess
alone is **not** a full sandbox — do not run scripts from untrusted sources. Projects
never execute embedded code on open; press Run explicitly.

## Install (Linux Mint)
```bash
cd ~/Projects/py3d-generator
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
# or
./run.sh
```
System packages for Qt/OpenGL if needed:
```bash
sudo apt install libgl1 libegl1 libxkbcommon0 libdbus-1-3
```

## API quick reference
- `cube(name, size, location, rotation[deg], color)` — `box` is an alias
- `sphere/icosphere(radius, subdivisions)`, `cylinder(radius, height, sections)`
- `cone`, `plane(size)` (XZ ground), `torus(major_radius, minor_radius)`
- `capsule`, `ring(inner/outer_radius, height)`, `wedge(size)`, `pyramid(size)`
- `custom_mesh(name, vertices=[(x,y,z)..], faces=[(i,j,k)..])` — raw lists for adapted algorithms
- `clear_scene, set_background, set_scene_name, get_objects, remove_object,`
  `duplicate_object, set_transform, set_material, grid_repeat, random_scatter`
- Y-up; `position=` accepted as alias of `location=`; rotations in degrees.

## Export notes
- GLB: geometry, transforms, names, colors, roughness/metallic preserved.
- OBJ: materials/hierarchy approximated (may write `.mtl`).
- STL: geometry only.
- Hidden objects excluded by default; ground plane excluded unless opted in.

## Tests
```bash
source .venv/bin/activate
pytest -q
```
