"""Example 0: Showcase — a curated row of all supported primitives.

Each primitive is created as a TRUE mesh (no image fakes), so this is a good
first check that the engine + viewport + GLB export all work.
"""
clear_scene()
set_scene_name("Showcase")
set_background("#1A2230")

# --- ground reference (visual + optional export) ---
plane(name="Ground", size=(26, 14), location=(0, 0, 0), color="#33404F")

# --- primitives, spaced along X ---
cube(name="Cube", size=(1.6, 1.6, 1.6), location=(-8.5, 0.8, 0),
     color="#4C9AFF", roughness=0.35)
icosphere(name="Sphere", radius=0.9, location=(-6.0, 0.9, 0),
          subdivisions=2, color="#E76F51", roughness=0.30)
cylinder(name="Cylinder", radius=0.65, height=1.8, location=(-3.6, 0.9, 0),
         sections=48, color="#2A9D8F", roughness=0.25, metallic=0.1)
cone(name="Cone", radius=0.8, height=1.7, location=(-1.2, 0.85, 0),
     sections=48, color="#E9C46A", roughness=0.35)
torus(name="Torus", major_radius=0.62, minor_radius=0.22,
      location=(1.2, 0.9, 0), rotation=(90, 0, 0), color="#9B5DE5", roughness=0.20, metallic=0.55)
capsule(name="Capsule", radius=0.42, height=1.6, location=(3.6, 0.8, 0),
        color="#00BBF9", roughness=0.25)
ring(name="Ring", inner_radius=0.42, outer_radius=0.85, height=0.3,
     location=(6.0, 0.35, 0), color="#F15BB5", roughness=0.30)
wedge(name="Wedge", size=(1.6, 1.4, 1.6), location=(8.4, 0.7, 0),
      color="#80ED99", roughness=0.40)

# --- custom mesh demo (raw lists, no numpy) ---
# Square pyramid built by hand to show custom_mesh()
pv = [(0, 0, 0), (1.6, 0, 0), (1.6, 0, 1.6), (0, 0, 1.6), (0.8, 1.4, 0.8)]
pf = [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (0, 2, 1), (0, 3, 2)]
custom_mesh(name="Pyramid", vertices=pv, faces=pf, location=(10.8, 0, 0.0),
            color="#F4A261", roughness=0.35)

# --- a small composite model to show object composition ---
# Mini house: body + roof + door + window + chimney
cube(name="house_body", size=(2.2, 1.6, 1.8), location=(-2.0, 0.8, 4.5), color="#E6D5B8")
pyramid(name="house_roof", size=(2.8, 1.3, 2.4), location=(-2.0, 1.6, 4.5), color="#B83A2E")
cube(name="house_door", size=(0.5, 0.9, 0.08), location=(-2.0, 0.45, 3.58), color="#6F4E37")
cube(name="house_window", size=(0.45, 0.45, 0.06), location=(-1.5, 0.95, 3.58), color="#4C9AFF")
cube(name="house_chimney", size=(0.3, 0.9, 0.3), location=(-1.5, 2.4, 4.9), color="#808080")