"""Main rendering pipeline."""

import numpy as np
from PIL import Image

from .geometry import build_sphere_geometry, orientation_matrix
from .lighting import (
    apply_atmosphere, apply_lighting, atmosphere_color, light_direction, render_outer_glow,
)
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

    # 2. Generate the surface material
    surface = generate_surface(geo, planet_type, seed, spec.temperature, spec.hue,
                               spec.cities)

    # 3. Clouds and the shadows they cast
    light = light_direction(spec.light_azimuth, spec.light_elevation)
    ring_system = RingSystem(seed, spec.ring_inner, spec.ring_outer) if has_rings else None
    ring_shadow = ring_system.shadow_on_planet(geo, geo["pole"], light) if ring_system else 1.0
    clouds = None
    shadow = ring_shadow
    if spec.clouds > 0 and "cloud_color" in traits:
        lx, ly, lz = light
        light_body = orientation.T @ np.array([lx, -ly, lz])
        clouds, cloud_shadow = generate_clouds(geo, seed, spec.clouds, light_body)
        shadow = ring_shadow * (1.0 - cloud_shadow)

    # 4. Light the ground, then lay the clouds over it
    rgb, _ = apply_lighting(surface, geo, light, shadow, spec.relief)
    if clouds is not None:
        rgb = composite_clouds(rgb, geo, light, clouds, traits["cloud_color"], ring_shadow)

    # 5. Apply atmosphere
    air_color = atmosphere_color(traits, surface)
    air = traits["atmo_strength"] * spec.atmosphere_density
    rgb = apply_atmosphere(rgb, geo, light, air_color, air)

    # 6. Assemble planet RGBA
    planet_rgba = np.zeros((size, size, 4), dtype=np.uint8)
    mask = geo["mask"]
    planet_rgba[mask, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
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
    glow = render_outer_glow(size, radius, light, air_color, air)
    if glow is not None:
        final = Image.alpha_composite(_to_image(glow), final)

    return final


def composite_clouds(rgb, geo, light, density, color, shadow):
    """Lay sunlit clouds over the lit ground."""
    nx, ny, nz = geo["nx"], geo["ny"], geo["nz"]
    lx, ly, lz = light
    sun = np.clip((nx * lx + ny * ly + nz * lz + 0.1) / 1.1, 0.0, 1.0) * shadow
    brightness = 0.03 + sun * (0.45 + 0.55 * np.sqrt(nz))
    cloud_rgb = np.asarray(color, dtype=np.float64) * brightness[:, None]
    alpha = (density * 0.95)[:, None]
    return rgb * (1.0 - alpha) + cloud_rgb * alpha


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
