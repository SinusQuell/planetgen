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


# Height field units to slope. Terrain heights span about -1..1, which taken
# literally would be mountains as tall as the planet.
RELIEF_SCALE = 0.05


def bumped_normals(geo, height, relief):
    """Tilt the sphere normals by the slope of the height field.

    The slope is taken in screen space, which is cheap and good enough away
    from the very edge; pixels next to the rim keep their plain normals.
    """
    nx, ny, nz = geo["nx"], geo["ny"], geo["nz"]
    if relief <= 0:
        return nx, ny, nz

    mask = geo["mask"]
    field = np.zeros(mask.shape)
    field[mask] = height
    grad_y, grad_x = np.gradient(field)

    interior = mask.copy()
    interior[1:, :] &= mask[:-1, :]
    interior[:-1, :] &= mask[1:, :]
    interior[:, 1:] &= mask[:, :-1]
    interior[:, :-1] &= mask[:, 1:]
    keep = interior[mask]

    # Per pixel slope to per planet radius slope, then undo the
    # foreshortening toward the limb (which is what the nz factor does).
    scale = geo["radius"] * relief * RELIEF_SCALE * nz * keep
    gx = grad_x[mask] * scale
    gy = grad_y[mask] * scale

    # Remove the part of the slope along the normal, then tilt away from it.
    along = gx * nx + gy * ny
    bx = nx - (gx - along * nx)
    by = ny - (gy - along * ny)
    bz = nz + along * nz
    length = np.sqrt(bx * bx + by * by + bz * bz)
    return bx / length, by / length, bz / length


def apply_lighting(surface, geo, light, shadow=None, relief=1.0):
    """Light the surface: soft Lambert diffuse, limb darkening and two
    Blinn-Phong highlights, a tight glint for liquids and a broad sheen for
    everything glossy.

    shadow, if given, scales the sunlight per pixel (1 = fully lit).
    relief scales how strongly terrain height shades the surface.
    Returns (rgb, diffuse); rgb is (N, 3) in 0..255 and diffuse is the
    sunlight factor, reused to light the clouds.
    """
    nx, ny, nz = bumped_normals(geo, surface.height, relief)
    lx, ly, lz = light

    # Wrap the diffuse term slightly so the day/night line is soft rather
    # than a hard cut.
    wrap = 0.08
    n_dot_l = nx * lx + ny * ly + nz * lz
    diffuse = np.clip((n_dot_l + wrap) / (1.0 + wrap), 0.0, 1.0)
    if shadow is not None:
        diffuse = diffuse * shadow

    # Limb darkening follows the smooth sphere, not the bumps. Kept mild so
    # the lit edge still reads as bright.
    limb = 0.35 + 0.65 * np.sqrt(geo["nz"])
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
    if surface.emission is not None:
        # Glow shows most where the sun is not already washing it out.
        rgb = rgb + surface.emission * (1.0 - 0.6 * diffuse)[:, None]
    return np.clip(rgb, 0, 255), diffuse


def atmosphere_color(traits, surface):
    """Color of the scattered light. Gas giants are mostly atmosphere, so
    theirs leans toward the planet's own colors."""
    base = np.array(traits["atmo_color"], dtype=np.float64)
    if traits.get("banded"):
        own = surface.color.mean(axis=0)
        own = own / max(own.max(), 1.0) * 235.0
        return base * 0.25 + own * 0.75
    return base


def apply_atmosphere(rgb, geo, light, color, strength):
    """Add sunlit haze toward the limb of (N, 3) colors, with a warm sunset
    band along the day/night line when the air is thick."""
    if strength <= 0:
        return rgb

    nx, ny, nz = geo["nx"], geo["ny"], geo["nz"]
    lx, ly, lz = light
    n_dot_l = nx * lx + ny * ly + nz * lz
    daylight = np.clip((n_dot_l + 0.3) / 1.3, 0.0, 1.0)

    rim = np.power(np.clip(1.0 - nz, 0.0, 1.0), 2.2)
    haze = (0.12 + rim) * strength * daylight
    haze = np.clip(haze, 0.0, 0.9)[:, None]
    # Screen blend: haze brightens dark ground a lot and bright ground a little.
    out = rgb + (np.asarray(color) - rgb * np.asarray(color) / 255.0) * haze

    sunset = np.exp(-(n_dot_l / 0.12) ** 2) * np.clip(strength - 0.3, 0.0, 1.0) * 0.6
    sunset_color = np.array([255.0, 120.0, 60.0])
    out = out + sunset_color * (sunset * (0.3 + 0.7 * rim))[:, None]
    return np.clip(out, 0, 255)


def render_outer_glow(size, radius, light, color, strength):
    """Halo of lit air just outside the planet's edge, as float RGBA in 0..1.

    It is brightest on the sunlit side. With the sun behind the planet,
    light scattering forward through the air lights up the whole rim.
    """
    if strength <= 0:
        return None

    cx = cy = size / 2.0
    yy, xx = np.mgrid[0:size, 0:size]
    dx = xx + 0.5 - cx
    dy = yy + 0.5 - cy
    dist = np.sqrt(dx * dx + dy * dy)

    # Halo thickness, in planet radii
    thickness = 0.04 + 0.06 * min(strength, 1.5)
    height = (dist - radius) / radius
    region = (height > -0.02) & (height < thickness * 5)
    glow = np.zeros((size, size, 4))
    if not np.any(region):
        return None

    h = np.maximum(height[region], 0.0)
    falloff = np.exp(-h / thickness)

    lx, ly, lz = light
    limb_dot_l = (dx[region] * lx + dy[region] * ly) / np.maximum(dist[region], 1e-6)
    lit = np.clip((limb_dot_l + 0.3) / 1.3, 0.0, 1.0) ** 1.5
    backlit = max(-lz, 0.0) ** 2 * 0.9

    intensity = falloff * min(strength, 1.5) * (lit + backlit)
    glow[region, :3] = np.asarray(color) / 255.0
    glow[region, 3] = np.clip(intensity * 2.2, 0.0, 1.0)
    return glow
