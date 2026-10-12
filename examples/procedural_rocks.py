"""Example 5: Procedural Rocks — deterministic random low-poly rock field.

Uses a fixed random seed (seed=42) so the scene is reproducible across runs.
Each rock is an icosphere deformed by per-vertex random offset, then squashed
with a non-uniform scale and random rotation.
"""
clear_scene()
set_scene_name("ProceduralRocks")

import random
import math

plane(name="Ground", size=(24, 24), location=(0, 0, 0), color="#8D99AE")

palette = ["#6C757D", "#868E96", "#495057", "#ADB5BD", "#CED4DA"]
rng = random.Random(42)

def make_rock(name, radius, jitter, sx, sy, sz, color):
    """Build one irregular low-poly rock from raw vertex/face lists."""
    # unit icosahedron vertices (icosphere subdivisions=0)
    t = (1 + math.sqrt(5)) / 2
    verts = [
        (-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0),
        (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
        (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1),
    ]
    n = math.sqrt(1 + t * t)
    verts = [(x / n, y / n, z / n) for x, y, z in verts]
    faces = [
        (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
        (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
        (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
        (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1),
    ]
    # jitter each vertex outward/inward → irregular silhouette
    deformed = []
    for x, y, z in verts:
        f = 1.0 + rng.uniform(-jitter, jitter)
        deformed.append((x * f * sx, y * f * sy, z * f * sz))
    custom_mesh(name=name, vertices=deformed, faces=faces, color=color, roughness=0.85)

# scattered rock field — deterministic
for i in range(9):
    x = rng.uniform(-8, 8)
    z = rng.uniform(-8, 8)
    r = rng.uniform(0.4, 1.2)
    color = palette[i % len(palette)]
    make_rock(
        name=f"rock_{i}",
        radius=r,
        jitter=rng.uniform(0.15, 0.40),
        sx=r, sy=r * rng.uniform(0.5, 0.8), sz=r * rng.uniform(0.8, 1.1),
        color=color,
    )
    # place and rotate the finished mesh
    set_transform(f"rock_{i}",
                  location=(x, r * 0.45, z),
                  rotation=(rng.uniform(0, 30), rng.uniform(0, 360), rng.uniform(0, 30)))

# a couple of flat stepping stones for scale
for i in range(3):
    cylinder(name=f"stone_{i}", radius=0.35, height=0.06,
             location=(-1.5 + i * 1.5, 0.03, 2.5),
             sections=12, color="#CED4DA", roughness=0.9)