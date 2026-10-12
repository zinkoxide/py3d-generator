"""Example 4: Small Village — a row of houses with varied colors, heights and details."""
clear_scene()
set_scene_name("SmallVillage")

plane(name="Ground", size=(34, 20), location=(0, 0, 0), color="#7FB069")

wall_colors = ["#E6D5B8", "#F1E4C8", "#E8C07D", "#D9C2A3", "#CDBFA4"]
roof_colors = ["#B0413A", "#8C3B4A", "#355070", "#6D597A", "#9B5DE5"]
door_colors = ["#6F4E37", "#4A3728", "#8B5A2B"]

count = 5
for i in range(count):
    x = i * 6.2 + 1.5
    w = 4.0 + (i % 3) * 0.6          # vary width
    h = 2.4 + (i % 2) * 0.7          # vary wall height
    d = 3.4 + (i % 2) * 0.5          # vary depth
    wall_c = wall_colors[i % len(wall_colors)]
    roof_c = roof_colors[i % len(roof_colors)]

    # foundation + walls + gable roof
    cube(name=f"foundation_{i}", size=(w + 0.3, 0.3, d + 0.3),
         location=(x, 0.15, 0), color="#9A8F86")
    cube(name=f"walls_{i}", size=(w, h, d), location=(x, h / 2 + 0.3, 0), color=wall_c)

    import math
    rise = 1.4 + (i % 2) * 0.5
    run = w / 2 + 0.5
    slope_len = math.sqrt(run * run + rise * rise)
    ang = math.degrees(math.atan2(rise, run))
    y_mid = h + 0.3 + rise / 2
    cube(name=f"roof_{i}_L", size=(slope_len, 0.18, d + 1.0),
         location=(x - run / 2, y_mid, 0), rotation=(0, 0, ang), color=roof_c)
    cube(name=f"roof_{i}_R", size=(slope_len, 0.18, d + 1.0),
         location=(x + run / 2, y_mid, 0), rotation=(0, 0, -ang),
         color=roof_c if i % 2 == 0 else roof_colors[(i + 1) % len(roof_colors)])

    # door + step
    cube(name=f"door_{i}", size=(0.85, 1.7, 0.12),
         location=(x, 0.3 + 0.85, d / 2 - 0.04), color=door_colors[i % len(door_colors)])
    cube(name=f"step_{i}", size=(1.3, 0.16, 0.6),
         location=(x, 0.08, d / 2 + 0.35), color="#A8A29E")

    # windows
    cube(name=f"win_{i}_L", size=(0.8, 0.8, 0.08),
         location=(x - w / 4, h * 0.6, d / 2 - 0.03), color="#8FD3F4", roughness=0.1)
    cube(name=f"win_{i}_R", size=(0.8, 0.8, 0.08),
         location=(x + w / 4, h * 0.6, d / 2 - 0.03), color="#8FD3F4", roughness=0.1)

    # chimney on some houses
    if i % 2 == 0:
        cube(name=f"chimney_{i}", size=(0.6, 1.4, 0.6),
             location=(x + w * 0.25, h + 1.0, 0), color="#8B5A3C")

    # porch columns
    if i % 2 == 1:
        for s in (-1, 1):
            cylinder(name=f"col_{i}_{s}", radius=0.12, height=2.1,
                     location=(x + s * 1.4, 1.35, d / 2 + 0.7),
                     sections=16, color="#F1FAEE")

    # small tree between some houses
    if i % 2 == 0 and i < count - 1:
        tx = x + 3.1
        cylinder(name=f"tree_{i}_trunk", radius=0.16, height=1.8,
                 location=(tx, 0.9, -2.4), sections=12, color="#6F4E37")
        cone(name=f"tree_{i}_leaves", radius=0.9, height=1.8,
             location=(tx, 2.3, -2.4), sections=9, color="#2D6A4F")