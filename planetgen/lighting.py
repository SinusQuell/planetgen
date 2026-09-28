"""Lighting and atmosphere."""

import math

import numpy as np


def light_direction(azimuth, elevation):
    """Unit vector toward the sun in image space (x right, y down, z toward
    the viewer). azimuth: degrees counterclockwise from the right edge of the
    image. elevation: degrees out of the image plane toward the viewer; 90
    lights the planet head-on, 0 gives a half-lit disc, negative values a
    crescent."""
    az = math.radians(azimuth)
    el = math.radians(elevation)
    return (math.cos(el) * math.cos(az), -math.cos(el) * math.sin(az), math.sin(el))


def apply_lighting(surface, geo, light, shadow=None):
    """Light the surface: soft Lambert diffuse, limb darkening and two
    Blinn-Phong highlights, a tight glint for liquids and a broad sheen for
    everything glossy.

    shadow, if given, scales the sunlight per pixel (1 = fully lit).
    Returns (rgb, diffuse); rgb is (N, 3) in 0..255 and diffuse is the
    sunlight factor, reused to light the clouds.
    """
    nx, ny, nz = geo["nx"], geo["ny"], geo["nz"]
    lx, ly, lz = light

    # Wrap the diffuse term slightly so the day/night line is soft rather
    # than a hard cut.
    wrap = 0.08
    n_dot_l = nx * lx + ny * ly + nz * lz
    diffuse = np.clip((n_dot_l + wrap) / (1.0 + wrap), 0.0, 1.0)
    if shadow is not None:
        diffuse = diffuse * shadow

    # Limb darkening, kept mild so the lit edge still reads as bright
    limb = 0.35 + 0.65 * np.sqrt(nz)
    ambient = 0.03

    # Half vector between the sun and the viewer (who looks down -z)
    hx, hy, hz = lx, ly, lz + 1.0
    h_len = math.sqrt(hx * hx + hy * hy + hz * hz)
    n_dot_h = np.clip((nx * hx + ny * hy + nz * hz) / h_len, 0.0, 1.0)
    glint = np.where(surface.liquid, np.power(n_dot_h, 90.0) * 0.9, 0.0)
    sheen = np.power(n_dot_h, 14.0) * 0.35
    specular = surface.specular * (glint + sheen) * (n_dot_l > 0)
    if shadow is not None:
        specular = specular * shadow

    light_factor = ambient + diffuse * limb
    rgb = surface.color * light_factor[:, None] + (specular * 255.0)[:, None]
    return np.clip(rgb, 0, 255), diffuse


def apply_atmosphere(rgb, geo, traits):
    """Apply Fresnel-based atmospheric rim glow to (N, 3) colors."""
    strength = traits["atmo_strength"]
    if strength <= 0:
        return rgb

    nz = geo["nz"]
    atmo_color = traits["atmo_color"]

    # Fresnel: bright at the limb, transparent at center
    fresnel = np.power(np.clip(1.0 - nz, 0, 1), 3.0) * strength

    fresnel = fresnel[:, None]
    return np.clip(rgb * (1.0 - fresnel) + np.array(atmo_color) * fresnel, 0, 255)


def render_outer_glow(size, radius, traits):
    """Render atmospheric glow outside the planet sphere. Returns RGBA array."""
    strength = traits["atmo_strength"]
    if strength <= 0:
        return None

    cx = cy = size / 2.0
    yy, xx = np.mgrid[0:size, 0:size]
    dx = xx - cx
    dy = yy - cy
    dist = np.sqrt(dx * dx + dy * dy)

    glow_width = radius * 0.12
    glow_mask = (dist > radius) & (dist < radius + glow_width * 3)

    glow = np.zeros((size, size, 4), dtype=np.uint8)
    if not np.any(glow_mask):
        return glow

    falloff = np.exp(-((dist[glow_mask] - radius) / glow_width) ** 2)
    alpha = (falloff * strength * 180).astype(np.uint8)

    ac = traits["atmo_color"]
    glow[glow_mask, 0] = ac[0]
    glow[glow_mask, 1] = ac[1]
    glow[glow_mask, 2] = ac[2]
    glow[glow_mask, 3] = alpha

    return glow
