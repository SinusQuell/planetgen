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


def apply_lighting(r, g, b, geo, planet_type, light):
    """Apply Lambertian diffuse + Blinn-Phong specular + limb darkening.

    Returns (r, g, b, diffuse) where diffuse is the raw diffuse factor for cloud lighting.
    """
    nx, ny, nz = geo["nx"], geo["ny"], geo["nz"]
    lx, ly, lz = light

    # Wrap the diffuse term slightly so the day/night line is soft rather
    # than a hard cut.
    wrap = 0.08
    n_dot_l = nx * lx + ny * ly + nz * lz
    diffuse = np.clip((n_dot_l + wrap) / (1.0 + wrap), 0.0, 1.0)

    # Limb darkening, kept mild so the lit edge still reads as bright
    limb = 0.35 + 0.65 * np.sqrt(nz)

    # Ambient
    ambient = 0.03

    # Specular (Blinn-Phong)
    vx, vy, vz = 0.0, 0.0, 1.0
    hx, hy, hz = lx + vx, ly + vy, lz + vz
    h_len = math.sqrt(hx * hx + hy * hy + hz * hz)
    hx /= h_len
    hy /= h_len
    hz /= h_len

    n_dot_h = np.clip(nx * hx + ny * hy + nz * hz, 0.0, 1.0)
    shininess = 10.0 if planet_type == "gas_giant" else 30.0
    specular = np.power(n_dot_h, shininess) * 0.25 * (n_dot_l > 0)

    # Combine
    light_factor = ambient + diffuse * limb
    r_out = r * light_factor + specular * 255.0
    g_out = g * light_factor + specular * 255.0
    b_out = b * light_factor + specular * 255.0

    return np.clip(r_out, 0, 255), np.clip(g_out, 0, 255), np.clip(b_out, 0, 255), diffuse


def apply_atmosphere(r, g, b, geo, traits):
    """Apply Fresnel-based atmospheric rim glow."""
    strength = traits["atmo_strength"]
    if strength <= 0:
        return r, g, b

    nz = geo["nz"]
    atmo_color = traits["atmo_color"]

    # Fresnel: bright at the limb, transparent at center
    fresnel = np.power(np.clip(1.0 - nz, 0, 1), 3.0) * strength

    ar, ag, ab = float(atmo_color[0]), float(atmo_color[1]), float(atmo_color[2])

    r_out = r * (1.0 - fresnel) + ar * fresnel
    g_out = g * (1.0 - fresnel) + ag * fresnel
    b_out = b * (1.0 - fresnel) + ab * fresnel

    return np.clip(r_out, 0, 255), np.clip(g_out, 0, 255), np.clip(b_out, 0, 255)


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
