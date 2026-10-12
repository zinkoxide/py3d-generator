"""Example 2: Low-Poly House (default script).

Built from real 3D primitives: foundation, walls, gable roof slopes,
gable triangles, door + steps, windows with frames, chimney with cap,
a porch with columns, bushes, and a small tree.
"""
clear_scene()
set_scene_name("LowPolyHouse")

import math

W, D = 8.0, 6.0        # width (x), depth (z)
H = 3.2                # wall height
R = 2.2                # roof rise
O = 0.6                # roof overhang

# ---- ground ----
plane(name="Ground", size=(W + 10, D + 10), location=(W / 2, 0, D / 2 - 1), color="#7FB069")

# ---- foundation + walls ----
cube(name="foundation", size=(W + 0.4, 0.45, D + 0.4),
     location=(W / 2, 0.22, D / 2), color="#9A8F86")
cube(name="walls", size=(W, H, D),
     location=(W / 2, H / 2 + 0.45, D / 2), color="#E6D5B8")

# ---- gable roof: two sloped slabs + two gable triangles ----
run = W / 2 + O
rise = R
z_eave = H + 0.45
z_ridge = z_eave + rise
slope_len = math.sqrt(run * run + rise * rise) + 0.25
ang = math.degrees(math.atan2(rise, run))
y_mid = (z_ridge + z_eave) / 2

cube(name="roof_L", size=(slope_len, 0.22, D + 2 * O),
     location=((W / 2 - O) / 2, y_mid, D / 2), rotation=(0, 0, ang), color="#B0413A")
cube(name="roof_R", size=(slope_len, 0.22, D + 2 * O),
     location=((W + (W / 2 + O)) / 2, y_mid, D / 2), rotation=(0, 0, -ang), color="#9A3730")

# gable triangles (front/back) — thin mirrored wedges
for z, tag in ((0.0, "front"), (D, "back")):
    wedge(name=f"gable_{tag}_L", size=(W / 2, R, 0.18),
          location=(W / 4, z_eave + R / 2, z), rotation=(0, 180, 0), color="#E6D5B8")
    wedge(name=f"gable_{tag}_R", size=(W / 2, R, 0.18),
          location=(W * 3 / 4, z_eave + R / 2, z), color="#E6D5B8")

# ---- chimney with cap ----
cx, cz = W * 0.74, D * 0.62
roof_z = z_ridge - (abs(cx - W / 2) / (W / 2)) * rise
cube(name="chimney", size=(0.85, 2.0, 0.85),
     location=(cx, roof_z + 0.4, cz), color="#8B5A3C")
cube(name="chimney_cap", size=(1.05, 0.18, 1.05),
     location=(cx, roof_z + 1.45, cz), color="#6D4630")

# ---- door + steps ----
dw, dh = 1.3, 2.3
cube(name="door_frame", size=(dw + 0.25, dh + 0.2, 0.12),
     location=(W / 2, 0.45 + (dh + 0.2) / 2, -0.05), color="#FFFFFF")
cube(name="door", size=(dw, dh, 0.14),
     location=(W / 2, 0.45 + dh / 2, -0.10), color="#6F4E37")
cube(name="door_knob", size=(0.12, 0.12, 0.12),
     location=(W / 2 + 0.45, 0.45 + 1.1, -0.20), color="#D4AF37")
cube(name="step_1", size=(dw + 1.0, 0.18, 0.7),
     location=(W / 2, 0.09, -0.5), color="#A8A29E")
cube(name="step_2", size=(dw + 0.6, 0.18, 0.7),
     location=(W / 2, 0.27, -0.2), color="#BFB7AE")

# ---- windows with frames (front face) ----
for i, wx in enumerate((1.3, W - 1.3 - 1.5)):
    cube(name=f"win_front_{i}_frame", size=(1.7, 1.55, 0.10),
         location=(wx + 0.75, 2.05, -0.03), color="#FFFFFF")
    cube(name=f"win_front_{i}_glass", size=(1.5, 1.35, 0.10),
         location=(wx + 0.75, 2.05, -0.08), color="#8FD3F4", roughness=0.1, metallic=0.2)
    cube(name=f"win_front_{i}_bar", size=(0.07, 1.35, 0.12),
         location=(wx + 0.75, 2.05, -0.10), color="#FFFFFF")
    cube(name=f"win_front_{i}_bar2", size=(1.5, 0.07, 0.12),
         location=(wx + 0.75, 2.05, -0.10), color="#FFFFFF")

# ---- porch roof + columns ----
cube(name="porch_roof", size=(3.0, 0.16, 1.6),
     location=(W / 2, 2.9, -0.7), color="#8B5A3C")
for i, px in enumerate((W / 2 - 1.3, W / 2 + 1.3)):
    cylinder(name=f"column_{i}", radius=0.14, height=2.8, location=(px, 1.4, -0.7),
             sections=24, color="#F1FAEE")

# ---- landscaping ----
for i, (bx, bz, br) in enumerate(((-1.2, 1.0, 0.7), (W + 1.2, 1.2, 0.85), (W + 1.0, D - 0.6, 0.6))):
    icosphere(name=f"bush_{i}", radius=br, location=(bx, br * 0.8, bz),
              subdivisions=1, color="#2D6A4F", roughness=0.6)

cylinder(name="tree_trunk", radius=0.22, height=2.4, location=(-1.8, 1.2, D + 1.2), color="#6F4E37")
cone(name="tree_canopy", radius=1.2, height=2.2, location=(-1.8, 3.0, D + 1.2),
     sections=16, color="#2D6A4F")