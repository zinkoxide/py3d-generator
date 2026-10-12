"""Example 1: Basic Objects — cube, sphere, cylinder, cone, torus (classic lineup)."""
clear_scene()
set_scene_name("BasicObjects")

plane(name="Ground", size=(14, 6), location=(0, 0, 0), color="#5A6B7D")

cube(name="Cube", size=(1.6, 1.6, 1.6), location=(-4, 0.8, 0),
     color="#4C9AFF", roughness=0.35)
sphere(name="Sphere", radius=0.9, location=(-2, 0.9, 0),
       subdivisions=3, color="#E76F51", roughness=0.30)
cylinder(name="Cylinder", radius=0.65, height=1.8, location=(0, 0.9, 0),
         sections=48, color="#2A9D8F", roughness=0.25, metallic=0.10)
cone(name="Cone", radius=0.8, height=1.7, location=(2, 0.85, 0),
     sections=48, color="#E9C46A", roughness=0.35)
torus(name="Torus", major_radius=0.62, minor_radius=0.22,
      location=(4, 0.9, 0), rotation=(90, 0, 0), color="#9B5DE5",
      roughness=0.20, metallic=0.55)