"""Moons orbiting in the planet's equatorial plane."""

import math

import numpy as np
from PIL import Image

from .geometry import build_sphere_geometry, orientation_matrix
from .lighting import apply_lighting
from .surface import generate_surface

# Weighted: mostly rocky, sometimes icy, rarely volcanic like Io
MOON_TYPES = ["barren"] * 6 + ["ice"] * 3 + ["volcanic"]


def place_moons(count, seed, size, planet_radius, orientation, min_orbit):
    """Pick an orbit spot and size for each moon.

    Returns a list of dicts with the moon's pixel center, radius, depth
    (positive = in front of the planet's center) and its own seed and type.
    Moons that would fall outside the image are dropped.
    """
    rng = np.random.RandomState((seed + 3131) & 0x7FFFFFFF)
    # Equator directions in image space (y down)
    east = orientation[:, 0] * np.array([1, -1, 1])
    north_facing = orientation[:, 2] * np.array([1, -1, 1])
    center = size / 2.0

    moons = []
    for i in range(count):
        radius = planet_radius * rng.uniform(0.06, 0.16)
        for _ in range(12):
            orbit = rng.uniform(min_orbit, min_orbit + 1.6)
            angle = rng.uniform(0, 2 * math.pi)
            pos = (math.cos(angle) * east + math.sin(angle) * north_facing) * orbit
            x = center + pos[0] * planet_radius
            y = center + pos[1] * planet_radius
            margin = radius + 2
            inside = margin <= x <= size - margin and margin <= y <= size - margin
            # Skip spots hidden right behind the planet.
            hidden = pos[2] < 0 and math.hypot(pos[0], pos[1]) < 1.0 + radius / planet_radius
            clear = all(math.hypot(x - m["x"], y - m["y"]) > radius + m["radius"] + 2
                        for m in moons)
            if inside and not hidden and clear:
                moons.append({
                    "x": x, "y": y, "radius": radius, "depth": pos[2],
                    "seed": int(rng.randint(0, 1_000_000)),
                    "type": MOON_TYPES[rng.randint(len(MOON_TYPES))],
                })
                break
    return moons


def render_moon(moon, light):
    """Render one moon on its own small transparent tile.

    Returns (image, left, top) for pasting into the full picture.
    """
    radius = moon["radius"]
    tile = int(math.ceil(radius * 2 + 4))
    geo = build_sphere_geometry(tile, radius, orientation_matrix(0, 0, moon["seed"] % 360))
    surface = generate_surface(geo, moon["type"], moon["seed"])
    rgb, _ = apply_lighting(surface, geo, light, relief=min(1.0, radius / 30))

    rgba = np.zeros((tile, tile, 4), dtype=np.uint8)
    rgba[geo["mask"], :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    rgba[geo["mask"], 3] = np.round(geo["coverage"] * 255).astype(np.uint8)

    # The tile's center sits at tile/2; shift so it lands on the moon's spot.
    left = int(round(moon["x"] - tile / 2.0))
    top = int(round(moon["y"] - tile / 2.0))
    return Image.fromarray(rgba, "RGBA"), left, top


def composite_moons(canvas, moons, light):
    """Paste moons onto a canvas the size of the final image."""
    for moon in moons:
        image, left, top = render_moon(moon, light)
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        layer.paste(image, (left, top))
        canvas = Image.alpha_composite(canvas, layer)
    return canvas
