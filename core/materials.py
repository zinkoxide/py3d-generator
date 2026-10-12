"""Material helpers: color parsing and material record."""

from __future__ import annotations

from dataclasses import dataclass


def parse_color(value) -> tuple[float, float, float, float]:
    """Parse '#RRGGBB', '#RRGGBBAA', (r,g,b) or (r,g,b,a) into 0..1 RGBA floats."""
    if isinstance(value, (tuple, list)):
        if len(value) == 3:
            r, g, b = value
            a = 1.0
        elif len(value) == 4:
            r, g, b, a = value
        else:
            raise ValueError(f"Color tuple must have 3 or 4 components, got {value!r}")
        comps = []
        for c in (r, g, b, a):
            f = float(c)
            if f > 1.0:  # allow 0..255 ints
                f = f / 255.0
            if not (0.0 <= f <= 1.0):
                raise ValueError(f"Color component out of range: {c!r}")
            comps.append(f)
        return (comps[0], comps[1], comps[2], comps[3])
    if isinstance(value, str):
        s = value.strip()
        if s.startswith("#"):
            s = s[1:]
        if len(s) == 6:
            s += "FF"
        if len(s) != 8:
            raise ValueError(f"Color string must be '#RRGGBB' or '#RRGGBBAA', got {value!r}")
        try:
            r = int(s[0:2], 16) / 255.0
            g = int(s[2:4], 16) / 255.0
            b = int(s[4:6], 16) / 255.0
            a = int(s[6:8], 16) / 255.0
        except ValueError:
            raise ValueError(f"Invalid hex color: {value!r}")
        return (r, g, b, a)
    raise TypeError(f"Unsupported color type: {type(value).__name__} ({value!r})")


def rgba_to_hex(rgba) -> str:
    r, g, b, _a = rgba
    return "#{:02X}{:02X}{:02X}".format(int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


@dataclass
class Material:
    color: tuple[float, float, float, float] = (0.3, 0.6, 1.0, 1.0)
    roughness: float = 0.6
    metallic: float = 0.0

    def validated(self) -> "Material":
        r, g, b, a = (float(x) for x in self.color)
        for v in (r, g, b, a):
            if not (0.0 <= v <= 1.0):
                raise ValueError(f"Material color component out of range: {self.color!r}")
        rough = float(self.roughness)
        metal = float(self.metallic)
        if not (0.0 <= rough <= 1.0):
            raise ValueError(f"roughness must be in [0,1], got {self.roughness!r}")
        if not (0.0 <= metal <= 1.0):
            raise ValueError(f"metallic must be in [0,1], got {self.metallic!r}")
        return Material(color=(r, g, b, a), roughness=rough, metallic=metal)
