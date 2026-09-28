"""Main rendering pipeline."""

import numpy as np
from PIL import Image

from .geometry import build_sphere_geometry, orientation_matrix
from .lighting import apply_atmosphere, apply_lighting, light_direction, render_outer_glow
from .rings import RingSystem
from .spec import PlanetSpec
from .surface import generate_clouds, generate_surface
from .types import PLANET_TYPES


def render_planet(spec, size=512):
    """Render a PlanetSpec to a square RGBA image."""
    planet_type = spec.type
    traits = PLANET_TYPES[planet_type]
    seed = spec.seed
    has_rings = spec.rings
    radius = max(4, int(round(spec.scale * size)))

    # 1. Build sphere geometry
    orientation = orientation_matrix(spec.tilt, spec.inclination, spec.rotation)
    geo = build_sphere_geometry(size, radius, orientation)

    # 2. Generate surface colors
    r, g, b = generate_surface(geo, planet_type, seed)

    # 3. Apply lighting
    light = light_direction(spec.light_azimuth, spec.light_elevation)
    ring_system = RingSystem(seed, spec.ring_inner, spec.ring_outer) if has_rings else None
    shadow = ring_system.shadow_on_planet(geo, geo["pole"], light) if ring_system else None
    r, g, b, diffuse = apply_lighting(r, g, b, geo, planet_type, light, shadow)

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
    planet_rgba[mask, 3] = np.round(geo["coverage"] * 255).astype(np.uint8)

    # 7. Rings
    if has_rings:
        back_rings, front_rings = ring_system.render(size, radius, geo["pole"], light)
        final = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        if back_rings is not None:
            final = Image.alpha_composite(final, _to_image(back_rings))
        final = Image.alpha_composite(final, Image.fromarray(planet_rgba, "RGBA"))
        if front_rings is not None:
            final = Image.alpha_composite(final, _to_image(front_rings))
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

    return final


def _to_image(rgba):
    """Float RGBA in 0..1 to a PIL image."""
    return Image.fromarray(np.round(np.clip(rgba, 0, 1) * 255).astype(np.uint8), "RGBA")


def render_planet_image(size=512, seed=None, planet_type=None, rings=None, **options):
    """Roll a planet from a seed and render it. Returns (image, metadata).

    planet_type, rings and any other PlanetSpec field override the rolled
    value when given.
    """
    spec = PlanetSpec.random(seed, type=planet_type, rings=rings, **options)
    return render_planet(spec, size), spec.to_dict()
