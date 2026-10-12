"""Example 3: Simple Tree — stylized low-poly tree with layered canopy, rocks and grass."""
clear_scene()
set_scene_name("SimpleTree")

plane(name="Ground", size=(14, 14), location=(0, 0, 0), color="#7FB069")

# --- trunk with a slight lean for organic feel ---
cylinder(name="trunk", radius=0.28, height=2.4, location=(0, 1.2, 0),
         sections=16, color="#6F4E37", roughness=0.85)
cylinder(name="branch_1", radius=0.10, height=1.2, location=(-0.35, 2.5, 0),
         sections=12, rotation=(0, 0, 35), color="#6F4E37", roughness=0.85)
cylinder(name="branch_2", radius=0.10, height=1.2, location=(0.35, 2.8, 0),
         sections=12, rotation=(0, 0, -35), color="#6F4E37", roughness=0.85)

# --- layered low-poly canopy ---
cone(name="leaves_low", radius=1.7, height=1.9, location=(0, 2.9, 0),
     sections=9, color="#2D6A4F", roughness=0.75)
cone(name="leaves_mid", radius=1.35, height=1.7, location=(0, 4.1, 0),
     sections=9, color="#40916C", roughness=0.75)
cone(name="leaves_top", radius=0.9, height=1.5, location=(0, 5.2, 0),
     sections=9, color="#52B788", roughness=0.75)

# --- ground details ---
icosphere(name="rock_1", radius=0.35, location=(1.9, 0.28, 1.1),
          subdivisions=1, color="#8D99AE", roughness=0.9)
icosphere(name="rock_2", radius=0.22, location=(-2.1, 0.18, 1.6),
          subdivisions=1, color="#8D99AE", roughness=0.9)
for i in range(5):
    cone(name=f"grass_{i}", radius=0.10, height=0.45,
         location=(-1.8 + i * 0.9, 0.22, -1.9 + (i % 2) * 0.4),
         sections=5, color="#52B788", roughness=0.9)