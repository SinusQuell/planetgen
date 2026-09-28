"""Main rendering pipeline."""

import random

import numpy as np
from PIL import Image

from .geometry import build_sphere_geometry
from .lighting import apply_atmosphere, apply_lighting, render_outer_glow
from .names import generate_name
from .rings import render_rings
from .surface import generate_clouds, generate_surface
from .types import PLANET_TYPES


def render_planet_image(size=512, seed=None, planet_type=None, rings=None):
    """Render a complete planet image with metadata.

    The same seed (and type, if given) always produces the same planet.
    planet_type and rings override the random choice when not None.
    """
    if seed is None:
        seed = random.randint(0, 999_999)
    rng = random.Random(seed)

    type_pick = rng.choice(list(PLANET_TYPES.keys()))
    planet_type = planet_type or type_pick
    traits = PLANET_TYPES[planet_type]

    name = generate_name(rng)
    temp_range = traits["temperature"]
    temperature = rng.randint(temp_range[0], temp_range[1])
    ring_roll = rng.random() < 0.2
    has_rings = ring_roll if rings is None else rings
    has_moons = rng.randint(0, 5)

    if has_rings:
        radius = rng.randint(int(size * 0.22), int(size * 0.30))
    else:
        radius = rng.randint(int(size * 0.30), int(size * 0.45))

    # 1. Build sphere geometry
    geo = build_sphere_geometry(size, radius)

    # 2. Generate surface colors
    r, g, b = generate_surface(geo, planet_type, seed)

    # 3. Apply lighting
    r, g, b, diffuse = apply_lighting(r, g, b, geo, planet_type)

    # 4. Add clouds (before atmosphere, after lighting)
    if planet_type in ("ocean", "forest", "ice", "desert"):
        cloud_alpha = generate_clouds(geo, seed, diffuse)
        # Blend white clouds over surface
        r = r * (1.0 - cloud_alpha) + 255.0 * cloud_alpha
        g = g * (1.0 - cloud_alpha) + 255.0 * cloud_alpha
        b = b * (1.0 - cloud_alpha) + 255.0 * cloud_alpha

    # 5. Apply atmosphere
    r, g, b = apply_atmosphere(r, g, b, geo, traits)

    # 6. Assemble planet RGBA
    planet_rgba = np.zeros((size, size, 4), dtype=np.uint8)
    mask = geo["mask"]
    planet_rgba[mask, 0] = np.clip(r, 0, 255).astype(np.uint8)
    planet_rgba[mask, 1] = np.clip(g, 0, 255).astype(np.uint8)
    planet_rgba[mask, 2] = np.clip(b, 0, 255).astype(np.uint8)
    planet_rgba[mask, 3] = 255

    # 7. Rings
    if has_rings:
        back_rings, front_rings = render_rings(size, radius, seed)
        final = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        if back_rings is not None:
            final = Image.alpha_composite(final, Image.fromarray(back_rings, "RGBA"))
        final = Image.alpha_composite(final, Image.fromarray(planet_rgba, "RGBA"))
        if front_rings is not None:
            final = Image.alpha_composite(final, Image.fromarray(front_rings, "RGBA"))
    else:
        final = Image.fromarray(planet_rgba, "RGBA")

    # 8. Outer atmospheric glow
    glow = render_outer_glow(size, radius, traits)
    if glow is not None:
        glow_img = Image.fromarray(glow, "RGBA")
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        canvas = Image.alpha_composite(canvas, glow_img)
        canvas = Image.alpha_composite(canvas, final)
        final = canvas

    metadata = {
        "name": name,
        "type": planet_type,
        "temperature": temperature,
        "radius": radius,
        "rings": has_rings,
        "moons": has_moons,
        "atmosphere": traits["atmosphere"],
        "seed": seed,
    }

    return final, metadata
